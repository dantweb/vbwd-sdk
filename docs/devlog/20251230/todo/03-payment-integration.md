# Sprint 3: Payment Integration (Plugin Architecture)

**Priority:** HIGH
**Duration:** 2-3 days
**Focus:** Plugin-based payment provider system with Stripe as first implementation

> **Core Requirements:** See [sprint-plan.md](./sprint-plan.md) for mandatory TDD-first, SOLID, DI, Clean Code, and No Over-Engineering requirements.

---

## Architecture Overview

Payment providers are implemented as **plugins** with **event-driven lifecycle**:

### Plugin Benefits
- Multiple payment providers (Stripe, PayPal, Paddle, etc.)
- Easy addition of new providers without core changes
- Provider switching per tenant (if multi-tenant)
- Testing with mock providers

### Event-Driven Plugin Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PLUGIN LIFECYCLE EVENTS                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Registration      Initialization        Operation          Shutdown    │
│       │                  │                   │                  │       │
│       ▼                  ▼                   ▼                  ▼       │
│  ┌─────────┐       ┌──────────┐       ┌──────────┐       ┌─────────┐   │
│  │Register │ ───▶  │Initialize│ ───▶  │ Payment  │ ───▶  │Shutdown │   │
│  │ Plugin  │       │  Plugin  │       │Operations│       │ Plugin  │   │
│  └────┬────┘       └────┬─────┘       └────┬─────┘       └────┬────┘   │
│       │                  │                  │                  │        │
│       ▼                  ▼                  ▼                  ▼        │
│  PluginRegistered  PluginInitialized  PaymentCreated    PluginStopped  │
│  Event             Event              PaymentSucceeded  Event          │
│                                       PaymentFailed                     │
│                                       SubscriptionCreated               │
│                                       RefundProcessed                   │
│                                       etc.                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Payment Flow (Event-Driven)

```
User Request → PaymentService → Plugin.createPayment() → EventDispatcher
                    ↓                                          ↓
                Database                              PaymentCreatedEvent
                                                              ↓
                                                    PaymentEventHandler
                                                    (email, webhook, etc.)
```

### File Structure

```
src/plugins/
  base.py                 # Base plugin class with lifecycle
  registry.py             # Event-driven plugin registry
  events.py               # Plugin lifecycle events
  payments/
    __init__.py
    base.py               # PaymentProviderPlugin interface
    events.py             # Payment-specific events
    providers/
      stripe/
        __init__.py
        provider.py       # StripePaymentProvider
      mock/
        provider.py       # MockPaymentProvider
```

---

## 3.0 Plugin Lifecycle Events

### Events Definition

**File:** `src/plugins/events.py`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from src.services.events.base import Event

@dataclass
class PluginRegisteredEvent(Event):
    """Emitted when a plugin is registered."""
    plugin_name: str
    plugin_version: str
    plugin_type: str  # "payment", "notification", etc.

@dataclass
class PluginInitializedEvent(Event):
    """Emitted when a plugin is initialized and ready."""
    plugin_name: str
    plugin_type: str
    config_keys: list  # Which config keys were used (not values!)

@dataclass
class PluginErrorEvent(Event):
    """Emitted when a plugin encounters an error."""
    plugin_name: str
    plugin_type: str
    error: str
    error_type: str  # "initialization", "operation", "shutdown"

@dataclass
class PluginStoppedEvent(Event):
    """Emitted when a plugin is stopped/unregistered."""
    plugin_name: str
    plugin_type: str
    reason: str  # "shutdown", "replaced", "error"
```

**File:** `src/plugins/payments/events.py`
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from src.services.events.base import Event

# Payment Events
@dataclass
class PaymentCreatedEvent(Event):
    """Emitted when a payment intent is created."""
    payment_id: str
    provider: str
    amount: int
    currency: str
    customer_id: str
    user_id: str

@dataclass
class PaymentSucceededEvent(Event):
    """Emitted when a payment succeeds."""
    payment_id: str
    provider: str
    amount: int
    currency: str
    customer_id: str
    user_id: str

@dataclass
class PaymentFailedEvent(Event):
    """Emitted when a payment fails."""
    payment_id: str
    provider: str
    error: str
    customer_id: str
    user_id: str

# Subscription Events
@dataclass
class SubscriptionCreatedEvent(Event):
    """Emitted when a subscription is created."""
    subscription_id: str
    provider: str
    plan_id: str
    customer_id: str
    user_id: str

@dataclass
class SubscriptionUpdatedEvent(Event):
    """Emitted when a subscription is modified."""
    subscription_id: str
    provider: str
    old_plan_id: Optional[str]
    new_plan_id: str
    user_id: str

@dataclass
class SubscriptionCancelledEvent(Event):
    """Emitted when a subscription is cancelled."""
    subscription_id: str
    provider: str
    cancel_at_period_end: bool
    user_id: str

# Refund Events
@dataclass
class RefundProcessedEvent(Event):
    """Emitted when a refund is processed."""
    refund_id: str
    payment_id: str
    provider: str
    amount: int
    user_id: str

# Invoice Events
@dataclass
class InvoicePaidEvent(Event):
    """Emitted when an invoice is paid."""
    invoice_id: str
    provider: str
    amount: int
    user_id: str

@dataclass
class InvoicePaymentFailedEvent(Event):
    """Emitted when invoice payment fails."""
    invoice_id: str
    provider: str
    error: str
    user_id: str
```

---

## 3.1 Payment Plugin Base Interface

### Problem
Need a standard interface all payment plugins must implement.

### Requirements
- Abstract payment provider interface
- Plugin registration system
- Provider factory
- Configuration validation

### TDD Tests First

**File:** `tests/unit/plugins/payments/test_plugin_registry.py`
```python
class TestPaymentPluginRegistry:
    def test_register_plugin_adds_to_registry(self):
        """Plugin registration stores provider."""
        pass

    def test_get_provider_returns_registered_plugin(self):
        """Can retrieve registered provider by name."""
        pass

    def test_get_unknown_provider_raises_error(self):
        """Unknown provider name raises PluginNotFoundError."""
        pass

    def test_list_providers_returns_all_registered(self):
        """List returns all registered provider names."""
        pass

    def test_provider_validates_config_on_init(self):
        """Provider validates required config on initialization."""
        pass
```

### Implementation

**File:** `src/plugins/payments/base.py`
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

@dataclass
class PaymentResult:
    success: bool
    payment_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    client_secret: Optional[str] = None  # For frontend confirmation
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CustomerResult:
    success: bool
    customer_id: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None

@dataclass
class SubscriptionResult:
    success: bool
    subscription_id: Optional[str] = None
    status: Optional[str] = None
    current_period_end: Optional[int] = None
    error: Optional[str] = None

@dataclass
class RefundResult:
    success: bool
    refund_id: Optional[str] = None
    amount: Optional[int] = None
    error: Optional[str] = None

@dataclass
class InvoiceResult:
    success: bool
    invoice_id: Optional[str] = None
    pdf_url: Optional[str] = None
    amount: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None


class PaymentProviderPlugin(ABC):
    """Abstract base class for payment provider plugins."""

    # Plugin metadata
    PLUGIN_NAME: str = ""
    PLUGIN_VERSION: str = "1.0.0"
    REQUIRED_CONFIG: List[str] = []

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate required configuration is present."""
        missing = [key for key in self.REQUIRED_CONFIG if key not in self.config]
        if missing:
            raise ValueError(f"Missing required config for {self.PLUGIN_NAME}: {missing}")

    # Customer Management
    @abstractmethod
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> CustomerResult:
        """Create a customer in the payment provider."""
        pass

    @abstractmethod
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Retrieve customer details."""
        pass

    @abstractmethod
    def update_customer(self, customer_id: str, **kwargs) -> CustomerResult:
        """Update customer details."""
        pass

    # Payment Methods
    @abstractmethod
    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        """Attach a payment method to a customer."""
        pass

    @abstractmethod
    def list_payment_methods(self, customer_id: str) -> List[Dict]:
        """List customer's payment methods."""
        pass

    @abstractmethod
    def set_default_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        """Set default payment method for customer."""
        pass

    # One-time Payments
    @abstractmethod
    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        customer_id: str,
        metadata: Optional[Dict] = None
    ) -> PaymentResult:
        """Create a payment intent for one-time payment."""
        pass

    @abstractmethod
    def confirm_payment(self, payment_id: str) -> PaymentResult:
        """Confirm/capture a payment."""
        pass

    @abstractmethod
    def cancel_payment(self, payment_id: str) -> PaymentResult:
        """Cancel a pending payment."""
        pass

    # Subscriptions
    @abstractmethod
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0,
        metadata: Optional[Dict] = None
    ) -> SubscriptionResult:
        """Create a subscription."""
        pass

    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Get subscription details."""
        pass

    @abstractmethod
    def update_subscription(self, subscription_id: str, price_id: str) -> SubscriptionResult:
        """Update subscription (change plan)."""
        pass

    @abstractmethod
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> SubscriptionResult:
        """Cancel a subscription."""
        pass

    @abstractmethod
    def reactivate_subscription(self, subscription_id: str) -> SubscriptionResult:
        """Reactivate a cancelled subscription."""
        pass

    # Refunds
    @abstractmethod
    def create_refund(self, payment_id: str, amount: Optional[int] = None, reason: Optional[str] = None) -> RefundResult:
        """Create a refund."""
        pass

    # Invoices
    @abstractmethod
    def get_invoice(self, invoice_id: str) -> InvoiceResult:
        """Get invoice details."""
        pass

    @abstractmethod
    def list_invoices(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """List customer invoices."""
        pass

    # Webhooks
    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Verify webhook signature and return parsed event."""
        pass

    @abstractmethod
    def get_webhook_handlers(self) -> Dict[str, callable]:
        """Return mapping of event types to handler methods."""
        pass


class WebhookHandler(ABC):
    """Abstract base for webhook handlers."""

    @abstractmethod
    def handle(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle a webhook event."""
        pass
```

**File:** `src/plugins/payments/registry.py`
```python
from typing import Dict, Type, List, Optional
from .base import PaymentProviderPlugin
from src.plugins.events import (
    PluginRegisteredEvent,
    PluginInitializedEvent,
    PluginErrorEvent,
    PluginStoppedEvent,
)
from src.services.events.dispatcher import EventDispatcher

class PluginNotFoundError(Exception):
    """Raised when requested plugin is not found."""
    pass

class PaymentPluginRegistry:
    """Event-driven registry for payment provider plugins."""

    _instance = None
    _providers: Dict[str, Type[PaymentProviderPlugin]] = {}
    _instances: Dict[str, PaymentProviderPlugin] = {}
    _event_dispatcher: Optional[EventDispatcher] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_event_dispatcher(cls, dispatcher: EventDispatcher) -> None:
        """Set event dispatcher for lifecycle events."""
        cls._event_dispatcher = dispatcher

    @classmethod
    def register(cls, provider_class: Type[PaymentProviderPlugin]) -> None:
        """Register a payment provider plugin and emit event."""
        name = provider_class.PLUGIN_NAME
        if not name:
            raise ValueError("Plugin must have PLUGIN_NAME defined")

        cls._providers[name] = provider_class

        # Emit registration event
        if cls._event_dispatcher:
            cls._event_dispatcher.dispatch(
                PluginRegisteredEvent(
                    plugin_name=name,
                    plugin_version=provider_class.PLUGIN_VERSION,
                    plugin_type="payment"
                )
            )

    @classmethod
    def get_provider(cls, name: str, config: Optional[Dict] = None) -> PaymentProviderPlugin:
        """Get/initialize a payment provider and emit events."""
        if name not in cls._providers:
            raise PluginNotFoundError(
                f"Payment provider '{name}' not found. Available: {list(cls._providers.keys())}"
            )

        # Return cached instance if exists
        if name in cls._instances:
            return cls._instances[name]

        # Initialize new instance
        if config is None:
            raise ValueError(f"Config required for first initialization of '{name}'")

        try:
            instance = cls._providers[name](config)
            cls._instances[name] = instance

            # Emit initialization event
            if cls._event_dispatcher:
                cls._event_dispatcher.dispatch(
                    PluginInitializedEvent(
                        plugin_name=name,
                        plugin_type="payment",
                        config_keys=list(config.keys())  # Keys only, not values!
                    )
                )

            return instance

        except Exception as e:
            # Emit error event
            if cls._event_dispatcher:
                cls._event_dispatcher.dispatch(
                    PluginErrorEvent(
                        plugin_name=name,
                        plugin_type="payment",
                        error=str(e),
                        error_type="initialization"
                    )
                )
            raise

    @classmethod
    def stop_provider(cls, name: str, reason: str = "shutdown") -> None:
        """Stop and remove a provider instance."""
        if name in cls._instances:
            del cls._instances[name]

            if cls._event_dispatcher:
                cls._event_dispatcher.dispatch(
                    PluginStoppedEvent(
                        plugin_name=name,
                        plugin_type="payment",
                        reason=reason
                    )
                )

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)."""
        cls._providers.clear()
        cls._instances.clear()


def register_payment_plugin(cls: Type[PaymentProviderPlugin]) -> Type[PaymentProviderPlugin]:
    """Decorator to register a payment plugin."""
    PaymentPluginRegistry.register(cls)
    return cls
```

---

## 3.2 Stripe Plugin Implementation

### Problem
Need Stripe as the first concrete payment plugin.

### Requirements
- Implement all PaymentProviderPlugin methods
- Stripe SDK integration
- Webhook signature verification
- Event handlers

### TDD Tests First

**File:** `tests/unit/plugins/payments/providers/test_stripe_provider.py`
```python
class TestStripePlugin:
    def test_plugin_name_is_stripe(self):
        """Plugin identifies as 'stripe'."""
        pass

    def test_create_customer_calls_stripe_api(self):
        """Customer creation uses Stripe API."""
        pass

    def test_create_payment_intent_returns_client_secret(self):
        """Payment intent includes client secret."""
        pass

    def test_create_subscription_with_trial(self):
        """Subscription with trial period."""
        pass

    def test_verify_webhook_signature_valid(self):
        """Valid signature passes verification."""
        pass

    def test_verify_webhook_signature_invalid_raises(self):
        """Invalid signature raises error."""
        pass

    def test_webhook_handlers_registered(self):
        """All webhook event handlers are registered."""
        pass
```

### Implementation

**File:** `src/plugins/payments/providers/stripe/__init__.py`
```python
from .provider import StripePaymentProvider
from .webhook import StripeWebhookHandler

__all__ = ["StripePaymentProvider", "StripeWebhookHandler"]
```

**File:** `src/plugins/payments/providers/stripe/provider.py`
```python
import stripe
from typing import Optional, Dict, Any, List
from src.plugins.payments.base import (
    PaymentProviderPlugin,
    PaymentResult,
    PaymentStatus,
    CustomerResult,
    SubscriptionResult,
    RefundResult,
    InvoiceResult,
)
from src.plugins.payments.registry import register_payment_plugin


@register_payment_plugin
class StripePaymentProvider(PaymentProviderPlugin):
    """Stripe payment provider plugin."""

    PLUGIN_NAME = "stripe"
    PLUGIN_VERSION = "1.0.0"
    REQUIRED_CONFIG = ["api_key", "webhook_secret"]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        stripe.api_key = config["api_key"]
        self.webhook_secret = config["webhook_secret"]

    # Customer Management
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> CustomerResult:
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={**(metadata or {}), "source": "vbwd"}
            )
            return CustomerResult(
                success=True,
                customer_id=customer.id,
                provider=self.PLUGIN_NAME
            )
        except stripe.error.StripeError as e:
            return CustomerResult(success=False, error=str(e))

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError:
            return None

    def update_customer(self, customer_id: str, **kwargs) -> CustomerResult:
        try:
            stripe.Customer.modify(customer_id, **kwargs)
            return CustomerResult(success=True, customer_id=customer_id)
        except stripe.error.StripeError as e:
            return CustomerResult(success=False, error=str(e))

    # Payment Methods
    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        try:
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            return True
        except stripe.error.StripeError:
            return False

    def list_payment_methods(self, customer_id: str) -> List[Dict]:
        try:
            methods = stripe.PaymentMethod.list(customer=customer_id, type="card")
            return list(methods.data)
        except stripe.error.StripeError:
            return []

    def set_default_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        try:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            return True
        except stripe.error.StripeError:
            return False

    # One-time Payments
    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        customer_id: str,
        metadata: Optional[Dict] = None
    ) -> PaymentResult:
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            return PaymentResult(
                success=True,
                payment_id=intent.id,
                client_secret=intent.client_secret,
                status=self._map_status(intent.status)
            )
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, error=str(e))

    def confirm_payment(self, payment_id: str) -> PaymentResult:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_id)
            return PaymentResult(
                success=intent.status == "succeeded",
                payment_id=intent.id,
                status=self._map_status(intent.status)
            )
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, error=str(e))

    def cancel_payment(self, payment_id: str) -> PaymentResult:
        try:
            intent = stripe.PaymentIntent.cancel(payment_id)
            return PaymentResult(
                success=True,
                payment_id=intent.id,
                status=PaymentStatus.CANCELLED
            )
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, error=str(e))

    # Subscriptions
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0,
        metadata: Optional[Dict] = None
    ) -> SubscriptionResult:
        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {},
            }
            if trial_days > 0:
                params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**params)
            return SubscriptionResult(
                success=True,
                subscription_id=subscription.id,
                status=subscription.status,
                current_period_end=subscription.current_period_end
            )
        except stripe.error.StripeError as e:
            return SubscriptionResult(success=False, error=str(e))

    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError:
            return None

    def update_subscription(self, subscription_id: str, price_id: str) -> SubscriptionResult:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": price_id,
                }],
                proration_behavior="create_prorations"
            )
            return SubscriptionResult(success=True, subscription_id=subscription_id)
        except stripe.error.StripeError as e:
            return SubscriptionResult(success=False, error=str(e))

    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> SubscriptionResult:
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            return SubscriptionResult(
                success=True,
                subscription_id=subscription.id,
                status=subscription.status
            )
        except stripe.error.StripeError as e:
            return SubscriptionResult(success=False, error=str(e))

    def reactivate_subscription(self, subscription_id: str) -> SubscriptionResult:
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return SubscriptionResult(
                success=True,
                subscription_id=subscription.id,
                status=subscription.status
            )
        except stripe.error.StripeError as e:
            return SubscriptionResult(success=False, error=str(e))

    # Refunds
    def create_refund(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> RefundResult:
        try:
            params = {"payment_intent": payment_id}
            if amount:
                params["amount"] = amount
            if reason:
                params["reason"] = reason

            refund = stripe.Refund.create(**params)
            return RefundResult(
                success=True,
                refund_id=refund.id,
                amount=refund.amount
            )
        except stripe.error.StripeError as e:
            return RefundResult(success=False, error=str(e))

    # Invoices
    def get_invoice(self, invoice_id: str) -> InvoiceResult:
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return InvoiceResult(
                success=True,
                invoice_id=invoice.id,
                pdf_url=invoice.invoice_pdf,
                amount=invoice.total,
                status=invoice.status
            )
        except stripe.error.StripeError as e:
            return InvoiceResult(success=False, error=str(e))

    def list_invoices(self, customer_id: str, limit: int = 10) -> List[Dict]:
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return list(invoices.data)
        except stripe.error.StripeError:
            return []

    # Webhooks
    def verify_webhook_signature(self, payload: bytes, signature: str) -> Dict[str, Any]:
        return stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )

    def get_webhook_handlers(self) -> Dict[str, callable]:
        return {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
        }

    def _handle_payment_succeeded(self, data: Dict) -> None:
        pass  # Implement with event dispatcher

    def _handle_payment_failed(self, data: Dict) -> None:
        pass

    def _handle_subscription_created(self, data: Dict) -> None:
        pass

    def _handle_subscription_updated(self, data: Dict) -> None:
        pass

    def _handle_subscription_deleted(self, data: Dict) -> None:
        pass

    def _handle_invoice_paid(self, data: Dict) -> None:
        pass

    def _handle_invoice_payment_failed(self, data: Dict) -> None:
        pass

    def _map_status(self, stripe_status: str) -> PaymentStatus:
        mapping = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "processing": PaymentStatus.PROCESSING,
            "succeeded": PaymentStatus.SUCCEEDED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return mapping.get(stripe_status, PaymentStatus.PENDING)
```

**File:** `src/plugins/payments/providers/stripe/webhook.py`
```python
from typing import Dict, Any
from src.plugins.payments.base import WebhookHandler
from src.services.events.dispatcher import EventDispatcher
from src.services.payment.events import (
    PaymentSucceededEvent,
    PaymentFailedEvent,
    SubscriptionCreatedEvent,
    SubscriptionUpdatedEvent,
    SubscriptionCancelledEvent,
)


class StripeWebhookHandler(WebhookHandler):
    """Stripe-specific webhook handler."""

    def __init__(self, event_dispatcher: EventDispatcher):
        self.event_dispatcher = event_dispatcher

    def handle(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Route event to appropriate handler."""
        handlers = {
            "payment_intent.succeeded": self._on_payment_succeeded,
            "payment_intent.payment_failed": self._on_payment_failed,
            "customer.subscription.created": self._on_subscription_created,
            "customer.subscription.updated": self._on_subscription_updated,
            "customer.subscription.deleted": self._on_subscription_deleted,
            "invoice.paid": self._on_invoice_paid,
            "invoice.payment_failed": self._on_invoice_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)

    def _on_payment_succeeded(self, data: Dict) -> None:
        self.event_dispatcher.dispatch(
            PaymentSucceededEvent(
                payment_id=data["id"],
                amount=data["amount"],
                customer_id=data["customer"],
                provider="stripe"
            )
        )

    def _on_payment_failed(self, data: Dict) -> None:
        self.event_dispatcher.dispatch(
            PaymentFailedEvent(
                payment_id=data["id"],
                error=data.get("last_payment_error", {}).get("message"),
                customer_id=data["customer"],
                provider="stripe"
            )
        )

    def _on_subscription_created(self, data: Dict) -> None:
        self.event_dispatcher.dispatch(
            SubscriptionCreatedEvent(
                subscription_id=data["id"],
                customer_id=data["customer"],
                plan_id=data["items"]["data"][0]["price"]["id"],
                provider="stripe"
            )
        )

    def _on_subscription_updated(self, data: Dict) -> None:
        self.event_dispatcher.dispatch(
            SubscriptionUpdatedEvent(
                subscription_id=data["id"],
                status=data["status"],
                cancel_at_period_end=data.get("cancel_at_period_end", False),
                provider="stripe"
            )
        )

    def _on_subscription_deleted(self, data: Dict) -> None:
        self.event_dispatcher.dispatch(
            SubscriptionCancelledEvent(
                subscription_id=data["id"],
                customer_id=data["customer"],
                provider="stripe"
            )
        )

    def _on_invoice_paid(self, data: Dict) -> None:
        pass  # Dispatch invoice event

    def _on_invoice_failed(self, data: Dict) -> None:
        pass  # Dispatch invoice failure event
```

---

## 3.3 Mock Provider for Testing

### Requirements
- In-memory mock provider
- Predictable responses for testing
- State tracking

### Implementation

**File:** `src/plugins/payments/providers/mock/provider.py`
```python
from typing import Optional, Dict, Any, List
import uuid
from src.plugins.payments.base import (
    PaymentProviderPlugin,
    PaymentResult,
    PaymentStatus,
    CustomerResult,
    SubscriptionResult,
    RefundResult,
    InvoiceResult,
)
from src.plugins.payments.registry import register_payment_plugin


@register_payment_plugin
class MockPaymentProvider(PaymentProviderPlugin):
    """Mock payment provider for testing."""

    PLUGIN_NAME = "mock"
    PLUGIN_VERSION = "1.0.0"
    REQUIRED_CONFIG = []

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.customers: Dict[str, Dict] = {}
        self.payments: Dict[str, Dict] = {}
        self.subscriptions: Dict[str, Dict] = {}
        self.invoices: Dict[str, Dict] = {}

    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> CustomerResult:
        customer_id = f"mock_cus_{uuid.uuid4().hex[:8]}"
        self.customers[customer_id] = {"email": email, "name": name, "metadata": metadata}
        return CustomerResult(success=True, customer_id=customer_id, provider=self.PLUGIN_NAME)

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        return self.customers.get(customer_id)

    def update_customer(self, customer_id: str, **kwargs) -> CustomerResult:
        if customer_id in self.customers:
            self.customers[customer_id].update(kwargs)
            return CustomerResult(success=True, customer_id=customer_id)
        return CustomerResult(success=False, error="Customer not found")

    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        return customer_id in self.customers

    def list_payment_methods(self, customer_id: str) -> List[Dict]:
        return [{"id": "mock_pm_123", "type": "card", "card": {"last4": "4242"}}]

    def set_default_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        return True

    def create_payment_intent(self, amount: int, currency: str, customer_id: str, metadata: Optional[Dict] = None) -> PaymentResult:
        payment_id = f"mock_pi_{uuid.uuid4().hex[:8]}"
        self.payments[payment_id] = {
            "amount": amount,
            "currency": currency,
            "customer": customer_id,
            "status": "succeeded"
        }
        return PaymentResult(
            success=True,
            payment_id=payment_id,
            client_secret=f"{payment_id}_secret",
            status=PaymentStatus.SUCCEEDED
        )

    def confirm_payment(self, payment_id: str) -> PaymentResult:
        if payment_id in self.payments:
            return PaymentResult(success=True, payment_id=payment_id, status=PaymentStatus.SUCCEEDED)
        return PaymentResult(success=False, error="Payment not found")

    def cancel_payment(self, payment_id: str) -> PaymentResult:
        if payment_id in self.payments:
            self.payments[payment_id]["status"] = "cancelled"
            return PaymentResult(success=True, payment_id=payment_id, status=PaymentStatus.CANCELLED)
        return PaymentResult(success=False, error="Payment not found")

    def create_subscription(self, customer_id: str, price_id: str, trial_days: int = 0, metadata: Optional[Dict] = None) -> SubscriptionResult:
        sub_id = f"mock_sub_{uuid.uuid4().hex[:8]}"
        self.subscriptions[sub_id] = {
            "customer": customer_id,
            "price": price_id,
            "status": "active",
            "trial_days": trial_days
        }
        return SubscriptionResult(success=True, subscription_id=sub_id, status="active")

    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        return self.subscriptions.get(subscription_id)

    def update_subscription(self, subscription_id: str, price_id: str) -> SubscriptionResult:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["price"] = price_id
            return SubscriptionResult(success=True, subscription_id=subscription_id)
        return SubscriptionResult(success=False, error="Subscription not found")

    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> SubscriptionResult:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["status"] = "cancelled" if immediately else "active"
            return SubscriptionResult(success=True, subscription_id=subscription_id, status="cancelled")
        return SubscriptionResult(success=False, error="Subscription not found")

    def reactivate_subscription(self, subscription_id: str) -> SubscriptionResult:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["status"] = "active"
            return SubscriptionResult(success=True, subscription_id=subscription_id, status="active")
        return SubscriptionResult(success=False, error="Subscription not found")

    def create_refund(self, payment_id: str, amount: Optional[int] = None, reason: Optional[str] = None) -> RefundResult:
        return RefundResult(success=True, refund_id=f"mock_re_{uuid.uuid4().hex[:8]}", amount=amount)

    def get_invoice(self, invoice_id: str) -> InvoiceResult:
        return InvoiceResult(success=True, invoice_id=invoice_id, pdf_url="/mock/invoice.pdf", amount=1000, status="paid")

    def list_invoices(self, customer_id: str, limit: int = 10) -> List[Dict]:
        return []

    def verify_webhook_signature(self, payload: bytes, signature: str) -> Dict[str, Any]:
        import json
        return json.loads(payload)

    def get_webhook_handlers(self) -> Dict[str, callable]:
        return {}
```

---

## 3.4 Payment Service (Plugin Consumer)

### Requirements
- Use registered plugins
- Handle provider switching
- Sync with local database

### Implementation

**File:** `src/services/payment_service.py`
```python
from typing import Optional
from src.plugins.payments.registry import PaymentPluginRegistry
from src.plugins.payments.base import PaymentProviderPlugin
from src.repositories.payment_repository import PaymentRepository
from src.repositories.user_repository import UserRepository

class PaymentService:
    """Service layer that uses payment plugins."""

    def __init__(
        self,
        payment_repo: PaymentRepository,
        user_repo: UserRepository,
        provider_name: str = "stripe"
    ):
        self.payment_repo = payment_repo
        self.user_repo = user_repo
        self.provider_name = provider_name

    @property
    def provider(self) -> PaymentProviderPlugin:
        """Get the configured payment provider."""
        return PaymentPluginRegistry.get_provider(self.provider_name)

    def create_checkout_session(self, user_id: str, plan_id: str):
        """Create checkout session for plan purchase."""
        user = self.user_repo.get_by_id(user_id)

        # Ensure customer exists in payment provider
        if not user.payment_customer_id:
            result = self.provider.create_customer(user.email, user.name)
            if result.success:
                user.payment_customer_id = result.customer_id
                self.user_repo.update(user)

        # Create payment intent or subscription
        # ... implementation

    def process_webhook(self, payload: bytes, signature: str):
        """Process incoming webhook."""
        event = self.provider.verify_webhook_signature(payload, signature)
        handlers = self.provider.get_webhook_handlers()

        handler = handlers.get(event["type"])
        if handler:
            handler(event["data"]["object"])
```

---

## 3.5 Webhook Routes

**File:** `src/routes/webhooks.py`
```python
from flask import Blueprint, request, current_app, jsonify
from src.plugins.payments.registry import PaymentPluginRegistry

webhooks_bp = Blueprint("webhooks", __name__)

@webhooks_bp.route("/payments/<provider>", methods=["POST"])
def payment_webhook(provider: str):
    """Generic webhook endpoint for any payment provider."""
    payload = request.get_data()
    signature = request.headers.get("Stripe-Signature") or request.headers.get("X-Webhook-Signature", "")

    try:
        payment_provider = PaymentPluginRegistry.get_provider(provider)
        event = payment_provider.verify_webhook_signature(payload, signature)

        # Get webhook handler
        webhook_handler = current_app.container.get_webhook_handler(provider)
        webhook_handler.handle(event["type"], event["data"]["object"])

        return "", 200
    except Exception as e:
        current_app.logger.error(f"Webhook error for {provider}: {e}")
        return jsonify({"error": str(e)}), 400
```

---

## Environment Variables

```bash
# Payment Plugins
PAYMENT_PROVIDER=stripe  # Default provider

# Stripe Plugin Config
STRIPE_API_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# PayPal Plugin Config (future)
# PAYPAL_CLIENT_ID=...
# PAYPAL_CLIENT_SECRET=...
```

---

## Checklist

### 3.0 Plugin Lifecycle Events
- [ ] Tests for plugin lifecycle events
- [ ] PluginRegisteredEvent defined
- [ ] PluginInitializedEvent defined
- [ ] PluginErrorEvent defined
- [ ] PluginStoppedEvent defined
- [ ] Payment-specific events defined (PaymentCreated, PaymentSucceeded, etc.)
- [ ] Registry emits events on register/init/stop

### 3.1 Plugin Base Interface
- [ ] Tests for PaymentPluginRegistry (event-driven)
- [ ] PaymentProviderPlugin abstract class
- [ ] Plugin registration decorator
- [ ] Config validation
- [ ] Event dispatcher integration
- [ ] All tests pass

### 3.2 Stripe Plugin
- [ ] Tests for StripePaymentProvider
- [ ] All interface methods implemented
- [ ] Emits events on operations
- [ ] Stripe SDK integration
- [ ] All tests pass

### 3.3 Mock Provider
- [ ] MockPaymentProvider implemented
- [ ] Emits events like real provider
- [ ] State tracking works

### 3.4 Payment Service
- [ ] Service uses plugin registry
- [ ] Provider switching works
- [ ] Emits business events (PaymentCreated, etc.)
- [ ] Database sync works

### 3.5 Webhook Routes
- [ ] Generic webhook endpoint
- [ ] Provider routing works
- [ ] Signature verification
- [ ] Converts webhook to domain events
- [ ] All tests pass

### 3.6 Payment Event Handlers
- [ ] PaymentEventHandler implemented
- [ ] Handles PaymentSucceededEvent (update subscription, send receipt)
- [ ] Handles PaymentFailedEvent (notify user, retry logic)
- [ ] Handles SubscriptionCreatedEvent (welcome email)
- [ ] Handlers registered with EventDispatcher

---

## Adding New Payment Providers

To add a new provider (e.g., PayPal):

1. Create `src/plugins/payments/providers/paypal/__init__.py`
2. Implement `PayPalPaymentProvider(PaymentProviderPlugin)`
3. Use `@register_payment_plugin` decorator
4. Implement all abstract methods
5. Add config variables
6. Provider is automatically available

```python
@register_payment_plugin
class PayPalPaymentProvider(PaymentProviderPlugin):
    PLUGIN_NAME = "paypal"
    PLUGIN_VERSION = "1.0.0"
    REQUIRED_CONFIG = ["client_id", "client_secret"]
    # ... implement methods
```

---

## Verification Commands

```bash
# Run plugin tests
docker-compose --profile test run --rm test pytest tests/unit/plugins/payments/ -v

# List registered providers
docker-compose exec api python -c "from src.plugins.payments.registry import PaymentPluginRegistry; print(PaymentPluginRegistry.list_providers())"

# Test webhook endpoint
curl -X POST http://localhost:5000/webhooks/payments/stripe \
  -H "Stripe-Signature: test" \
  -d '{"type": "test"}'
```
