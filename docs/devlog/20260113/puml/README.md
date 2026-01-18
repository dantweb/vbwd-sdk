# Checkout Architecture Diagrams

This folder contains PlantUML diagrams explaining the checkout flow, event system, and payment plugin architecture.

## Key Architecture Principles

### 1. Payment-First Activation

**Nothing is active until payment is confirmed.**

| Entity | Initial Status | After Payment |
|--------|---------------|---------------|
| Subscription | `pending` | `active` |
| Token Bundle | `pending` | tokens credited to balance |
| Add-on | `pending` | `active` |

### 2. Event-Driven Architecture

**Routes emit events, NOT call services directly.**

```
Route (emit event) → EventDispatcher → EventHandler → Service → Repository → DB
```

### 3. Invoice Line Items

An invoice can contain multiple items:
- Subscription
- Token bundles
- Add-ons

All remain pending until invoice is paid.

## Event Flow

```
1. POST /user/checkout
   └─→ CheckoutRequestedEvent
       └─→ CheckoutHandler
           ├─ Create subscription (PENDING)
           ├─ Create token purchases (PENDING)
           ├─ Create add-on subscriptions (PENDING)
           └─ Create invoice with line items

2. POST /webhooks/:provider (or admin marks paid)
   └─→ PaymentCapturedEvent
       └─→ PaymentCapturedHandler
           ├─ Mark invoice PAID
           ├─ Activate subscription
           ├─ Credit tokens to user balance
           └─ Activate add-ons
```

## Diagrams Overview

### 1. Checkout Flow (`01-checkout-flow.puml`)

**Sequence diagram** showing the complete user journey with payment-first activation.

**Key Points:**
- Checkout creates ALL items as PENDING
- User completes payment via provider
- PaymentCapturedEvent triggers activation
- Tokens credited, subscription & add-ons activated

### 2. Event System (`02-checkout-event-system.puml`)

**Component diagram** showing command vs domain events.

**Events:**
- `CheckoutRequestedEvent` - Creates pending items
- `PaymentCapturedEvent` - Activates items
- `SubscriptionActivatedEvent` - Subscription became active
- `TokensCreditedEvent` - Tokens added to balance
- `AddOnActivatedEvent` - Add-on became active

### 3. Payment Plugin Architecture (`03-payment-plugin-architecture.puml`)

**Component diagram** showing how payment providers integrate with the event system.

**Flow:**
1. Webhook route receives payment notification
2. PaymentService verifies with provider
3. PaymentCapturedEvent emitted
4. Handler activates all items

**Plugins:**
- StripePlugin → StripeProvider
- PayPalPlugin → PayPalProvider
- ManualPaymentPlugin → ManualProvider (default)

### 4. Checkout with Payment Plugins (`04-checkout-with-payment-plugins.puml`)

**Sequence diagram** showing complete flow with different payment providers.

**Flows:**
1. **Stripe** - Card form → PaymentIntent → webhook → activate
2. **PayPal** - Redirect → approval → webhook → activate
3. **Manual** - Invoice → bank transfer → admin marks paid → activate

### 5. Component Diagram (`05-checkout-component-diagram.puml`)

**Architecture overview** showing all components and their relationships.

**Layers:**
- Routes emit events (NOT call services)
- Event System dispatches to handlers
- Handlers call services
- Services use repositories

### 6. State Diagram (`06-checkout-state-diagram.puml`)

**State machines** for:
- User checkout journey
- Subscription lifecycle (pending → active → cancelled/expired)
- Token bundle purchase lifecycle (pending → completed)
- Add-on subscription lifecycle (pending → active)
- Invoice lifecycle (pending → paid/failed/refunded)

## Rendering Diagrams

### Using PlantUML CLI
```bash
# Install PlantUML
brew install plantuml  # macOS
apt install plantuml   # Ubuntu

# Render single file
plantuml 01-checkout-flow.puml

# Render all files
plantuml *.puml
```

### Using VS Code
Install "PlantUML" extension, then:
- Open `.puml` file
- Press `Alt+D` to preview
- Right-click → "Export Current Diagram"

### Using Online Editor
Copy content to https://www.plantuml.com/plantuml/uml/

## Architecture Decisions

### 1. Why Payment-First?

| Approach | Problem |
|----------|---------|
| Activate immediately | User has access without paying |
| Activate on payment | Clean state, no rollback needed |

**Benefits:**
- No partial states to manage
- Simple refund flow (deactivate)
- Clear audit trail

### 2. Why Event-Driven?

```python
# Route emits event (NOT calls service)
@user_bp.route("/checkout", methods=["POST"])
def checkout():
    event = CheckoutRequestedEvent(...)
    result = dispatcher.emit(event)
    return jsonify(result.data), 201

# Handler does the work
class CheckoutHandler(IEventHandler):
    def handle(self, event):
        subscription = self._subscription_service.create(status=PENDING)
        invoice = self._invoice_service.create(...)
        return EventResult.success_result({...})
```

**Benefits:**
- Loose coupling
- Easy to add side effects (email, webhooks)
- Event log for audit

### 3. Plugin-Based Payment Providers

```python
# Register providers via plugins
registry.register("stripe", StripeProvider())
registry.register("paypal", PayPalProvider())
registry.register("manual", ManualProvider())  # Default

# Easy to add new providers
registry.register("crypto", CryptoProvider())
```

### 4. Manual Payment as Default

Without payment gateway:
- Invoice created with "pending" status
- User pays via bank transfer
- Admin marks invoice as paid
- PaymentCapturedEvent triggers activation

## Related Files

- Sprint plan: `../todo/01-user-checkout.md`
- Event system: `vbwd-backend/src/events/`
- Handlers: `vbwd-backend/src/handlers/`
- Plugins: `vbwd-backend/src/plugins/`
