# Sprint 03: Backend Checkout Implementation

**Date:** 2026-01-13
**Priority:** High
**Type:** Backend Implementation
**Section:** User Checkout Flow
**Prerequisite:** Sprint 02 (Backend Integration Tests)
**Blocks:** Sprint 04 (Payment Capture)

## Goal

Implement the checkout backend that creates PENDING subscriptions, token purchases, add-on subscriptions, and invoices with line items.

**All items are PENDING until payment is captured.**

## Architecture

```
POST /user/checkout → CheckoutRequestedEvent → CheckoutHandler → Services → DB
```

## Tasks

### Task 3.1: Create Data Models

**Files:**
- `vbwd-backend/src/models/token_bundle.py`
- `vbwd-backend/src/models/addon.py`
- `vbwd-backend/src/models/invoice_line_item.py`

```python
# token_bundle.py
from dataclasses import dataclass
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from enum import Enum

class PurchaseStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"

@dataclass
class TokenBundle:
    id: UUID
    name: str
    token_amount: int
    price: Decimal
    is_active: bool = True

@dataclass
class TokenBundlePurchase:
    id: UUID
    user_id: UUID
    bundle_id: UUID
    status: PurchaseStatus
    tokens_credited: bool = False
    created_at: datetime = None
    completed_at: datetime = None
```

```python
# addon.py
@dataclass
class AddOn:
    id: UUID
    name: str
    description: str
    price: Decimal
    billing_period: str  # monthly, yearly, one_time
    is_active: bool = True

@dataclass
class AddOnSubscription:
    id: UUID
    user_id: UUID
    add_on_id: UUID
    subscription_id: UUID  # parent subscription
    status: SubscriptionStatus
    starts_at: datetime = None
    expires_at: datetime = None
```

```python
# invoice_line_item.py
class LineItemType(str, Enum):
    SUBSCRIPTION = "subscription"
    TOKEN_BUNDLE = "token_bundle"
    ADD_ON = "add_on"

@dataclass
class InvoiceLineItem:
    id: UUID
    invoice_id: UUID
    item_type: LineItemType
    item_id: UUID
    description: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
```

---

### Task 3.2: Create Database Migrations

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose exec api flask db migrate -m "Add token bundles, addons, invoice line items"
docker-compose exec api flask db upgrade
```

**Tables to create:**
- `token_bundles`
- `token_bundle_purchases`
- `addons`
- `addon_subscriptions`
- `invoice_line_items`

---

### Task 3.3: Create Repositories

**Files:**
- `vbwd-backend/src/repositories/token_bundle_repository.py`
- `vbwd-backend/src/repositories/addon_repository.py`

```python
# token_bundle_repository.py
class TokenBundleRepository:
    def __init__(self, session):
        self._session = session

    def get_by_id(self, bundle_id: UUID) -> Optional[TokenBundle]:
        ...

    def get_active(self) -> List[TokenBundle]:
        ...

    def save_purchase(self, purchase: TokenBundlePurchase) -> TokenBundlePurchase:
        ...

    def get_purchase_by_id(self, purchase_id: UUID) -> Optional[TokenBundlePurchase]:
        ...
```

---

### Task 3.4: Create Checkout Events

**File:** `vbwd-backend/src/events/checkout_events.py`

```python
from dataclasses import dataclass, field
from typing import List
from uuid import UUID
from src.events.base import DomainEvent

@dataclass
class CheckoutRequestedEvent(DomainEvent):
    """Command event: User requested checkout."""
    user_id: UUID
    plan_id: UUID
    token_bundle_ids: List[UUID] = field(default_factory=list)
    add_on_ids: List[UUID] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.name = "checkout.requested"
```

---

### Task 3.5: Create Checkout Handler

**File:** `vbwd-backend/src/handlers/checkout_handlers.py`

```python
class CheckoutHandler(IEventHandler):
    """Handler for checkout requests. Creates all items as PENDING."""

    def __init__(
        self,
        subscription_service: SubscriptionService,
        token_bundle_service: TokenBundleService,
        add_on_service: AddOnService,
        invoice_service: InvoiceService,
        event_dispatcher: EventDispatcher
    ):
        self._subscription_service = subscription_service
        self._token_bundle_service = token_bundle_service
        self._add_on_service = add_on_service
        self._invoice_service = invoice_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: DomainEvent) -> bool:
        return event.name == "checkout.requested"

    def handle(self, event: CheckoutRequestedEvent) -> EventResult:
        try:
            line_items = []

            # 1. Create PENDING subscription
            subscription = self._subscription_service.create_subscription(
                user_id=event.user_id,
                plan_id=event.plan_id,
                status=SubscriptionStatus.PENDING
            )
            line_items.append({
                "type": "subscription",
                "item_id": subscription.id,
                "description": subscription.plan.name,
                "price": subscription.plan.price
            })

            # 2. Create PENDING token bundle purchases
            bundle_purchases = []
            for bundle_id in event.token_bundle_ids:
                purchase = self._token_bundle_service.create_purchase(
                    user_id=event.user_id,
                    bundle_id=bundle_id,
                    status=PurchaseStatus.PENDING
                )
                bundle_purchases.append(purchase)
                line_items.append({
                    "type": "token_bundle",
                    "item_id": purchase.id,
                    "description": purchase.bundle.name,
                    "price": purchase.bundle.price
                })

            # 3. Create PENDING add-on subscriptions
            addon_subscriptions = []
            for addon_id in event.add_on_ids:
                addon_sub = self._add_on_service.create_subscription(
                    user_id=event.user_id,
                    add_on_id=addon_id,
                    parent_subscription_id=subscription.id,
                    status=SubscriptionStatus.PENDING
                )
                addon_subscriptions.append(addon_sub)
                line_items.append({
                    "type": "add_on",
                    "item_id": addon_sub.id,
                    "description": addon_sub.add_on.name,
                    "price": addon_sub.add_on.price
                })

            # 4. Create invoice with all line items
            invoice = self._invoice_service.create_invoice(
                user_id=event.user_id,
                line_items=line_items
            )

            # 5. Emit domain events
            self._event_dispatcher.emit("subscription:created", {
                "subscription_id": str(subscription.id),
                "status": "pending"
            })
            self._event_dispatcher.emit("invoice:created", {
                "invoice_id": str(invoice.id),
                "total": str(invoice.total_amount)
            })

            return EventResult.success_result({
                "subscription": subscription.to_dict(),
                "invoice": invoice.to_dict(),
                "token_bundles": [p.to_dict() for p in bundle_purchases],
                "add_ons": [a.to_dict() for a in addon_subscriptions],
                "message": "Checkout created. Awaiting payment."
            })

        except Exception as e:
            return EventResult.error_result(str(e))
```

---

### Task 3.6: Create Services

**Files:**
- `vbwd-backend/src/services/token_bundle_service.py`
- `vbwd-backend/src/services/addon_service.py`

```python
# token_bundle_service.py
class TokenBundleService:
    def __init__(self, bundle_repo: TokenBundleRepository):
        self._bundle_repo = bundle_repo

    def get_by_id(self, bundle_id: UUID) -> TokenBundle:
        bundle = self._bundle_repo.get_by_id(bundle_id)
        if not bundle or not bundle.is_active:
            raise ValueError("Token bundle not found or inactive")
        return bundle

    def create_purchase(
        self,
        user_id: UUID,
        bundle_id: UUID,
        status: PurchaseStatus
    ) -> TokenBundlePurchase:
        bundle = self.get_by_id(bundle_id)
        purchase = TokenBundlePurchase(
            id=uuid4(),
            user_id=user_id,
            bundle_id=bundle_id,
            status=status,
            tokens_credited=False,
            created_at=datetime.utcnow()
        )
        return self._bundle_repo.save_purchase(purchase)
```

---

### Task 3.7: Create Checkout Route

**File:** `vbwd-backend/src/routes/user.py`

```python
@user_bp.route("/checkout", methods=["POST"])
@require_auth
def checkout():
    """
    Create checkout with subscription and optional items.
    All items created as PENDING until payment is confirmed.
    """
    user_id = g.user_id
    data = request.get_json() or {}

    plan_id = data.get("plan_id")
    if not plan_id:
        return jsonify({"error": "plan_id is required"}), 400

    token_bundle_ids = data.get("token_bundle_ids", [])
    add_on_ids = data.get("add_on_ids", [])

    try:
        event = CheckoutRequestedEvent(
            user_id=UUID(user_id),
            plan_id=UUID(plan_id),
            token_bundle_ids=[UUID(id) for id in token_bundle_ids],
            add_on_ids=[UUID(id) for id in add_on_ids]
        )

        dispatcher = current_app.container.event_dispatcher()
        result = dispatcher.emit(event)

        if result.success:
            return jsonify({
                "subscription": result.data.get("subscription"),
                "invoice": result.data.get("invoice"),
                "token_bundles": result.data.get("token_bundles"),
                "add_ons": result.data.get("add_ons"),
                "message": "Checkout created. Awaiting payment.",
                "next_step": "Complete payment to activate subscription."
            }), 201
        else:
            return jsonify({"error": result.error}), 400

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

### Task 3.8: Register Handler in DI Container

**File:** `vbwd-backend/src/app.py`

```python
def _register_event_handlers(app: Flask, container) -> None:
    dispatcher = container.event_dispatcher()

    # Checkout handler
    checkout_handler = CheckoutHandler(
        subscription_service=container.subscription_service(),
        token_bundle_service=container.token_bundle_service(),
        add_on_service=container.add_on_service(),
        invoice_service=container.invoice_service(),
        event_dispatcher=dispatcher
    )
    dispatcher.register("checkout.requested", checkout_handler)
```

---

### Task 3.9: Run Tests (Should PASS)

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run checkout tests
docker-compose run --rm test pytest tests/integration/test_checkout*.py -v

# All tests from Sprint 02 should now PASS
```

---

## Build & Test Commands

**IMPORTANT:** Always rebuild and run tests after making changes.

### Rebuild Backend
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Rebuild and restart services
make up-build
```

### Run Tests with Pre-Commit Script
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run all quality checks (lint + unit + integration)
./bin/pre-commit-check.sh

# Quick check (skip integration tests)
./bin/pre-commit-check.sh --quick

# Only run specific checks
./bin/pre-commit-check.sh --lint        # Static analysis only (black, flake8, mypy)
./bin/pre-commit-check.sh --unit        # Unit tests only
./bin/pre-commit-check.sh --integration # Integration tests only
```

---

## Definition of Done

- [ ] Token bundle model created
- [ ] Add-on model created
- [ ] Invoice line item model created
- [ ] Database migrations created and applied
- [ ] Repositories created
- [ ] CheckoutRequestedEvent created
- [ ] CheckoutHandler implemented
- [ ] TokenBundleService created
- [ ] AddOnService created
- [ ] Checkout route implemented
- [ ] Handler registered in DI
- [ ] All Sprint 02 tests PASS
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 3.1 Data Models | ⏳ Pending | |
| 3.2 Migrations | ⏳ Pending | |
| 3.3 Repositories | ⏳ Pending | |
| 3.4 Checkout Events | ⏳ Pending | |
| 3.5 Checkout Handler | ⏳ Pending | |
| 3.6 Services | ⏳ Pending | |
| 3.7 Checkout Route | ⏳ Pending | |
| 3.8 Register Handler | ⏳ Pending | |
| 3.9 Run Tests | ⏳ Pending | Should PASS |

---

## Next Sprint

After this sprint, proceed to:
- **Sprint 04:** Backend Payment Capture Implementation
