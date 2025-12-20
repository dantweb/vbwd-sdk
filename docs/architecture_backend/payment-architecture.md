# Payment Architecture

**Provider-Agnostic Payment Platform with Plugin System**

---

## Overview

The payment system is designed as a provider-agnostic platform where payment-specific code exists as plugins/module extensions. This architecture enables:

- Easy addition of new payment providers without core changes
- Consistent payment flow regardless of provider
- Support for diverse payment methods (card, invoice, wallet, etc.)
- Clean separation between business logic and provider SDKs

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                             │
│                    (Routes, Controllers, DTOs)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    PAYMENT SERVICE LAYER                        │ │
│  │            (Provider-Agnostic Business Logic)                   │ │
│  │                                                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │ │
│  │  │ Checkout    │  │ Invoice     │  │ Subscription            │ │ │
│  │  │ Orchestrator│  │ Service     │  │ Billing Service         │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                 PAYMENT METHOD ABSTRACTION                      │ │
│  │              (Payment Method Strategy Layer)                    │ │
│  │                                                                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │ │
│  │  │ Card     │  │ Invoice  │  │ Wallet   │  │ Bank Transfer │  │ │
│  │  │ Payment  │  │ (Pay     │  │ Payment  │  │ Payment       │  │ │
│  │  │ Method   │  │ Later)   │  │ Method   │  │ Method        │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   PROVIDER ADAPTER LAYER                        │ │
│  │            (Unified Interface for All Providers)                │ │
│  │                                                                 │ │
│  │    IPaymentProviderAdapter                                      │ │
│  │    ├── create_payment_intent()                                  │ │
│  │    ├── capture_payment()                                        │ │
│  │    ├── refund_payment()                                         │ │
│  │    ├── create_checkout_session()                                │ │
│  │    ├── verify_webhook()                                         │ │
│  │    └── get_payment_status()                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      PLUGIN SYSTEM                              │ │
│  │                (Payment Provider Plugins)                       │ │
│  │                                                                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │  Stripe  │  │  PayPal  │  │  Klarna  │  │  Manual/     │   │ │
│  │  │  Plugin  │  │  Plugin  │  │  Plugin  │  │  Invoice     │   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      SDK ADAPTER LAYER                          │ │
│  │            (Provider SDK Wrappers/Clients)                      │ │
│  │                                                                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │ Stripe   │  │ PayPal   │  │ Klarna   │  │    N/A       │   │ │
│  │  │ SDK      │  │ REST API │  │ SDK      │  │  (internal)  │   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

### 1. Payment Service Layer (Business Logic)

Provider-agnostic orchestration of payment flows. Contains no provider-specific code.

| Component | Responsibility |
|-----------|----------------|
| `CheckoutOrchestrator` | Orchestrates complete checkout flow |
| `InvoiceService` | Invoice creation, tax calculation, status management |
| `SubscriptionBillingService` | Recurring billing, renewals, upgrades |
| `RefundService` | Refund processing and validation |
| `PaymentEventHandler` | Processes normalized payment events |

### 2. Payment Method Abstraction

Strategy pattern for different payment methods. Each method knows which providers support it.

| Method | Description | Supported Providers |
|--------|-------------|---------------------|
| `CardPayment` | Credit/debit card payments | Stripe, PayPal, Adyen |
| `InvoicePayment` | Pay later / manual invoice | Manual, Klarna |
| `WalletPayment` | Digital wallets | PayPal, Apple Pay, Google Pay |
| `BankTransfer` | Direct bank transfers | SEPA, Wire |
| `BuyNowPayLater` | Installment payments | Klarna, Affirm |

### 3. Provider Adapter Layer

Unified interface that all provider plugins must implement. Normalizes provider differences.

### 4. Plugin System

Self-contained provider implementations. Each plugin:
- Implements `IPaymentProviderAdapter`
- Handles provider-specific webhook parsing
- Maps provider events to normalized events
- Manages provider configuration

### 5. SDK Adapter Layer

Thin wrappers around provider SDKs. Handles:
- HTTP client configuration
- Authentication
- Request/response serialization
- Error handling and retries

---

## Core Interfaces

### IPaymentProviderAdapter

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    """Normalized payment status."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


@dataclass
class PaymentIntent:
    """Provider-agnostic payment intent."""
    id: str
    provider: str
    provider_reference: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    metadata: dict


@dataclass
class CheckoutSession:
    """Provider-agnostic checkout session."""
    id: str
    provider: str
    checkout_url: str
    expires_at: Optional[datetime]
    metadata: dict


@dataclass
class WebhookEvent:
    """Normalized webhook event."""
    id: str
    type: str  # payment.completed, payment.failed, etc.
    provider: str
    payment_intent_id: Optional[str]
    invoice_id: Optional[int]
    data: dict
    raw_payload: dict


@dataclass
class RefundResult:
    """Refund operation result."""
    id: str
    provider: str
    provider_reference: str
    amount: Decimal
    status: str


class IPaymentProviderAdapter(ABC):
    """
    Payment provider adapter interface.

    All payment provider plugins must implement this interface.
    Follows Liskov Substitution Principle - any implementation
    must be substitutable without changing behavior.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier."""
        pass

    @property
    @abstractmethod
    def supported_payment_methods(self) -> List[str]:
        """List of supported payment methods."""
        pass

    @property
    @abstractmethod
    def supports_webhooks(self) -> bool:
        """Whether provider supports webhooks."""
        pass

    @abstractmethod
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: dict,
    ) -> PaymentIntent:
        """
        Create a payment intent/order.

        Args:
            amount: Payment amount
            currency: ISO 4217 currency code
            payment_method: Payment method type
            metadata: Application metadata (invoice_id, user_id, etc.)

        Returns:
            PaymentIntent with provider reference
        """
        pass

    @abstractmethod
    def capture_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentIntent:
        """
        Capture authorized payment.

        Args:
            payment_intent_id: Payment intent to capture
            amount: Optional partial capture amount

        Returns:
            Updated PaymentIntent
        """
        pass

    @abstractmethod
    def cancel_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Cancel/void a payment intent."""
        pass

    @abstractmethod
    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> RefundResult:
        """
        Refund a captured payment.

        Args:
            payment_intent_id: Payment to refund
            amount: Optional partial refund amount
            reason: Refund reason

        Returns:
            RefundResult with status
        """
        pass

    @abstractmethod
    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
        line_items: Optional[List[dict]] = None,
    ) -> CheckoutSession:
        """
        Create hosted checkout session.

        Args:
            amount: Total amount
            currency: ISO 4217 currency code
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            metadata: Application metadata
            line_items: Optional itemized line items

        Returns:
            CheckoutSession with checkout URL
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify webhook authenticity.

        Args:
            payload: Raw webhook payload
            signature: Signature from headers
            timestamp: Optional timestamp for replay protection

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """
        Parse provider webhook into normalized event.

        Args:
            payload: Webhook JSON payload

        Returns:
            Normalized WebhookEvent
        """
        pass

    @abstractmethod
    def get_payment_status(self, payment_intent_id: str) -> PaymentIntent:
        """
        Get current payment status.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            PaymentIntent with current status
        """
        pass
```

### IPaymentMethod

```python
class IPaymentMethod(ABC):
    """
    Payment method interface.

    Represents a payment method type (card, invoice, wallet).
    Knows which providers support it.
    """

    @property
    @abstractmethod
    def method_type(self) -> str:
        """Payment method identifier (card, invoice, wallet)."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""
        pass

    @property
    @abstractmethod
    def requires_redirect(self) -> bool:
        """Whether this method requires redirect to provider."""
        pass

    @property
    @abstractmethod
    def supports_recurring(self) -> bool:
        """Whether this method supports recurring payments."""
        pass

    @abstractmethod
    def get_compatible_providers(
        self,
        currency: str,
        country: str,
    ) -> List[str]:
        """
        Get providers that support this method for given context.

        Args:
            currency: Payment currency
            country: Customer country

        Returns:
            List of compatible provider names
        """
        pass

    @abstractmethod
    def validate_payment_details(self, details: dict) -> List[str]:
        """
        Validate payment method specific details.

        Args:
            details: Payment details (varies by method)

        Returns:
            List of validation errors (empty if valid)
        """
        pass
```

---

## Plugin System

### Plugin Structure

```
python/api/src/
├── payment/
│   ├── __init__.py
│   ├── interfaces.py           # Core interfaces
│   ├── types.py                # Shared types/dataclasses
│   ├── exceptions.py           # Payment exceptions
│   │
│   ├── methods/                # Payment methods
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── card.py
│   │   ├── invoice.py
│   │   ├── wallet.py
│   │   └── bank_transfer.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── checkout_orchestrator.py
│   │   ├── payment_processor.py
│   │   ├── refund_service.py
│   │   └── webhook_handler.py
│   │
│   ├── plugins/                # Provider plugins
│   │   ├── __init__.py
│   │   ├── base.py             # Base plugin class
│   │   ├── registry.py         # Plugin registry
│   │   │
│   │   ├── stripe/             # Stripe plugin
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py
│   │   │   ├── sdk_client.py
│   │   │   ├── webhook_parser.py
│   │   │   └── config.py
│   │   │
│   │   ├── paypal/             # PayPal plugin
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py
│   │   │   ├── sdk_client.py
│   │   │   ├── webhook_parser.py
│   │   │   └── config.py
│   │   │
│   │   ├── manual/             # Manual/Invoice plugin
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py
│   │   │   └── config.py
│   │   │
│   │   └── klarna/             # Klarna plugin (example)
│   │       ├── __init__.py
│   │       ├── adapter.py
│   │       ├── sdk_client.py
│   │       └── config.py
│   │
│   └── sdk/                    # SDK adapters
│       ├── __init__.py
│       ├── stripe_sdk.py
│       ├── paypal_sdk.py
│       └── http_client.py
```

### Plugin Registry

```python
"""Payment plugin registry."""
from typing import Dict, Type, Optional, List
from src.payment.interfaces import IPaymentProviderAdapter


class PaymentPluginRegistry:
    """
    Registry for payment provider plugins.

    Manages plugin registration, discovery, and instantiation.
    """

    _plugins: Dict[str, Type[IPaymentProviderAdapter]] = {}
    _instances: Dict[str, IPaymentProviderAdapter] = {}

    @classmethod
    def register(cls, provider_name: str):
        """
        Decorator to register a payment plugin.

        Usage:
            @PaymentPluginRegistry.register("stripe")
            class StripeAdapter(IPaymentProviderAdapter):
                ...
        """
        def decorator(plugin_class: Type[IPaymentProviderAdapter]):
            cls._plugins[provider_name] = plugin_class
            return plugin_class
        return decorator

    @classmethod
    def get_plugin(cls, provider_name: str) -> Optional[IPaymentProviderAdapter]:
        """Get instantiated plugin by name."""
        if provider_name not in cls._instances:
            if provider_name not in cls._plugins:
                return None
            cls._instances[provider_name] = cls._plugins[provider_name]()
        return cls._instances[provider_name]

    @classmethod
    def get_all_plugins(cls) -> List[IPaymentProviderAdapter]:
        """Get all registered plugins."""
        return [cls.get_plugin(name) for name in cls._plugins.keys()]

    @classmethod
    def get_plugins_for_method(
        cls,
        method_type: str,
        currency: str,
        country: str,
    ) -> List[IPaymentProviderAdapter]:
        """Get plugins that support a payment method in context."""
        compatible = []
        for plugin in cls.get_all_plugins():
            if method_type in plugin.supported_payment_methods:
                # Additional filtering by currency/country can be done here
                compatible.append(plugin)
        return compatible

    @classmethod
    def load_plugins(cls, config: dict) -> None:
        """
        Load and configure plugins from configuration.

        Args:
            config: Plugin configuration dict
        """
        for provider_name, provider_config in config.items():
            if not provider_config.get("enabled", True):
                continue

            plugin_class = cls._plugins.get(provider_name)
            if plugin_class:
                cls._instances[provider_name] = plugin_class(**provider_config)
```

### Base Plugin Implementation

```python
"""Base payment plugin implementation."""
from abc import ABC
from typing import Optional, List
from decimal import Decimal
from src.payment.interfaces import (
    IPaymentProviderAdapter,
    PaymentIntent,
    CheckoutSession,
    WebhookEvent,
    RefundResult,
    PaymentStatus,
)
from src.payment.exceptions import PaymentProviderError


class BasePaymentPlugin(IPaymentProviderAdapter, ABC):
    """
    Base class for payment provider plugins.

    Provides common functionality and helper methods.
    Subclasses implement provider-specific logic.
    """

    def __init__(self, **config):
        """Initialize plugin with configuration."""
        self._config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate plugin configuration. Override in subclasses."""
        pass

    def _create_payment_intent_record(
        self,
        provider_reference: str,
        amount: Decimal,
        currency: str,
        status: PaymentStatus,
        metadata: dict,
    ) -> PaymentIntent:
        """Helper to create PaymentIntent dataclass."""
        return PaymentIntent(
            id=f"{self.provider_name}_{provider_reference}",
            provider=self.provider_name,
            provider_reference=provider_reference,
            amount=amount,
            currency=currency,
            status=status,
            metadata=metadata,
        )

    def _normalize_status(self, provider_status: str) -> PaymentStatus:
        """
        Normalize provider-specific status to PaymentStatus.

        Override in subclasses with provider-specific mapping.
        """
        raise NotImplementedError

    def _normalize_webhook_type(self, provider_event_type: str) -> str:
        """
        Normalize provider event type to standard type.

        Standard types:
        - payment.pending
        - payment.authorized
        - payment.captured
        - payment.failed
        - payment.cancelled
        - payment.refunded
        - checkout.completed
        - checkout.expired
        """
        raise NotImplementedError
```

---

## Payment Methods

### Card Payment Method

```python
"""Card payment method."""
from typing import List
from src.payment.interfaces import IPaymentMethod


class CardPaymentMethod(IPaymentMethod):
    """
    Credit/debit card payment method.

    Supports most payment providers.
    """

    @property
    def method_type(self) -> str:
        return "card"

    @property
    def display_name(self) -> str:
        return "Credit/Debit Card"

    @property
    def requires_redirect(self) -> bool:
        return True  # For 3DS

    @property
    def supports_recurring(self) -> bool:
        return True

    def get_compatible_providers(
        self,
        currency: str,
        country: str,
    ) -> List[str]:
        # Most providers support cards globally
        return ["stripe", "paypal", "adyen"]

    def validate_payment_details(self, details: dict) -> List[str]:
        # Card details handled by provider (PCI compliance)
        return []
```

### Invoice Payment Method (Pay Later)

```python
"""Invoice/Pay Later payment method."""
from typing import List
from src.payment.interfaces import IPaymentMethod


class InvoicePaymentMethod(IPaymentMethod):
    """
    Invoice-based payment (pay later).

    Creates invoice for manual payment via bank transfer
    or other offline methods.
    """

    @property
    def method_type(self) -> str:
        return "invoice"

    @property
    def display_name(self) -> str:
        return "Pay by Invoice"

    @property
    def requires_redirect(self) -> bool:
        return False

    @property
    def supports_recurring(self) -> bool:
        return False  # Each period needs new invoice

    def get_compatible_providers(
        self,
        currency: str,
        country: str,
    ) -> List[str]:
        # Manual provider always available
        # Klarna for B2C in supported countries
        providers = ["manual"]

        klarna_countries = ["DE", "AT", "NL", "SE", "NO", "FI", "DK"]
        if country in klarna_countries:
            providers.append("klarna")

        return providers

    def validate_payment_details(self, details: dict) -> List[str]:
        errors = []

        # Invoice requires billing address
        if not details.get("billing_address"):
            errors.append("Billing address required for invoice payment")

        return errors
```

### Buy Now Pay Later Method

```python
"""Buy Now Pay Later payment method."""
from typing import List
from src.payment.interfaces import IPaymentMethod


class BuyNowPayLaterMethod(IPaymentMethod):
    """
    Buy Now Pay Later (installments).

    Supported by Klarna, Affirm, Afterpay.
    """

    @property
    def method_type(self) -> str:
        return "bnpl"

    @property
    def display_name(self) -> str:
        return "Buy Now, Pay Later"

    @property
    def requires_redirect(self) -> bool:
        return True

    @property
    def supports_recurring(self) -> bool:
        return False

    def get_compatible_providers(
        self,
        currency: str,
        country: str,
    ) -> List[str]:
        providers = []

        # Klarna
        klarna_countries = ["DE", "AT", "NL", "SE", "NO", "FI", "DK", "US", "UK"]
        if country in klarna_countries:
            providers.append("klarna")

        # Affirm (US only)
        if country == "US" and currency == "USD":
            providers.append("affirm")

        return providers

    def validate_payment_details(self, details: dict) -> List[str]:
        errors = []

        # BNPL requires full customer details for credit check
        required = ["first_name", "last_name", "email", "billing_address"]
        for field in required:
            if not details.get(field):
                errors.append(f"{field} required for BNPL")

        return errors
```

---

## Checkout Orchestrator

```python
"""Provider-agnostic checkout orchestrator."""
from typing import Optional, List
from decimal import Decimal
from dataclasses import dataclass
from src.payment.interfaces import IPaymentProviderAdapter, CheckoutSession
from src.payment.plugins.registry import PaymentPluginRegistry
from src.payment.methods.base import IPaymentMethod


@dataclass
class CheckoutRequest:
    """Checkout request data."""
    user_id: int
    tarif_plan_id: int
    payment_method: str  # card, invoice, bnpl
    provider: Optional[str]  # Optional specific provider
    currency: str
    country: str
    billing_details: dict
    success_url: str
    cancel_url: str


@dataclass
class CheckoutResult:
    """Checkout result."""
    success: bool
    invoice_id: Optional[int]
    checkout_url: Optional[str]
    requires_redirect: bool
    provider: str
    error: Optional[str]


class CheckoutOrchestrator:
    """
    Orchestrates checkout flow across payment methods and providers.

    Provider-agnostic - delegates to appropriate plugin.
    """

    def __init__(
        self,
        invoice_service: "InvoiceService",
        subscription_service: "SubscriptionService",
        tax_service: "TaxService",
        payment_methods: dict[str, IPaymentMethod],
    ):
        self._invoice_service = invoice_service
        self._subscription_service = subscription_service
        self._tax_service = tax_service
        self._payment_methods = payment_methods

    def get_available_methods(
        self,
        currency: str,
        country: str,
    ) -> List[dict]:
        """
        Get available payment methods for context.

        Returns list of methods with their compatible providers.
        """
        available = []

        for method_type, method in self._payment_methods.items():
            providers = method.get_compatible_providers(currency, country)
            if providers:
                available.append({
                    "type": method_type,
                    "display_name": method.display_name,
                    "requires_redirect": method.requires_redirect,
                    "supports_recurring": method.supports_recurring,
                    "providers": providers,
                })

        return available

    def create_checkout(self, request: CheckoutRequest) -> CheckoutResult:
        """
        Create checkout session.

        1. Validate payment method
        2. Select provider
        3. Create invoice
        4. Create subscription (inactive)
        5. Create provider checkout session
        """
        # Get payment method
        method = self._payment_methods.get(request.payment_method)
        if not method:
            return CheckoutResult(
                success=False,
                error=f"Unknown payment method: {request.payment_method}",
            )

        # Validate payment details
        errors = method.validate_payment_details(request.billing_details)
        if errors:
            return CheckoutResult(
                success=False,
                error="; ".join(errors),
            )

        # Select provider
        provider_name = request.provider
        if not provider_name:
            compatible = method.get_compatible_providers(
                request.currency, request.country
            )
            if not compatible:
                return CheckoutResult(
                    success=False,
                    error=f"No providers available for {request.payment_method}",
                )
            provider_name = compatible[0]  # Default to first

        # Get provider plugin
        provider = PaymentPluginRegistry.get_plugin(provider_name)
        if not provider:
            return CheckoutResult(
                success=False,
                error=f"Provider not configured: {provider_name}",
            )

        # Create subscription (inactive)
        subscription = self._subscription_service.create_subscription(
            user_id=request.user_id,
            tarif_plan_id=request.tarif_plan_id,
        )

        # Create invoice
        invoice = self._invoice_service.create_invoice(
            user_id=request.user_id,
            tarif_plan_id=request.tarif_plan_id,
            subscription_id=subscription.id,
            country_code=request.country,
            currency_code=request.currency,
        )

        # Handle based on method type
        if request.payment_method == "invoice":
            # Invoice payment - no redirect needed
            return CheckoutResult(
                success=True,
                invoice_id=invoice.id,
                checkout_url=None,
                requires_redirect=False,
                provider=provider_name,
                error=None,
            )

        # Create provider checkout session
        try:
            session = provider.create_checkout_session(
                amount=invoice.amount,
                currency=invoice.currency,
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                metadata={
                    "invoice_id": invoice.id,
                    "user_id": request.user_id,
                    "subscription_id": subscription.id,
                },
            )

            return CheckoutResult(
                success=True,
                invoice_id=invoice.id,
                checkout_url=session.checkout_url,
                requires_redirect=True,
                provider=provider_name,
                error=None,
            )

        except Exception as e:
            # Cleanup on failure
            self._invoice_service.mark_cancelled(invoice.id)
            return CheckoutResult(
                success=False,
                error=str(e),
            )
```

---

## Webhook Handler

```python
"""Provider-agnostic webhook handler."""
from typing import Optional
from src.payment.interfaces import WebhookEvent, PaymentStatus
from src.payment.plugins.registry import PaymentPluginRegistry


class PaymentWebhookHandler:
    """
    Handles webhooks from all payment providers.

    Normalizes events and triggers appropriate actions.
    """

    def __init__(
        self,
        invoice_service: "InvoiceService",
        subscription_service: "SubscriptionService",
        user_service: "UserService",
        email_service: Optional["EmailService"] = None,
    ):
        self._invoice_service = invoice_service
        self._subscription_service = subscription_service
        self._user_service = user_service
        self._email_service = email_service

    def handle_webhook(
        self,
        provider: str,
        payload: dict,
        signature: str,
        raw_payload: bytes,
    ) -> bool:
        """
        Handle incoming webhook.

        1. Get provider plugin
        2. Verify signature
        3. Parse to normalized event
        4. Route to handler
        """
        plugin = PaymentPluginRegistry.get_plugin(provider)
        if not plugin:
            return False

        # Verify signature
        if plugin.supports_webhooks:
            if not plugin.verify_webhook_signature(raw_payload, signature):
                return False

        # Parse event
        event = plugin.parse_webhook_event(payload)

        # Route to handler
        return self._route_event(event)

    def _route_event(self, event: WebhookEvent) -> bool:
        """Route normalized event to appropriate handler."""
        handlers = {
            "payment.captured": self._handle_payment_captured,
            "payment.authorized": self._handle_payment_authorized,
            "payment.failed": self._handle_payment_failed,
            "payment.refunded": self._handle_payment_refunded,
            "checkout.completed": self._handle_checkout_completed,
            "checkout.expired": self._handle_checkout_expired,
        }

        handler = handlers.get(event.type)
        if handler:
            return handler(event)

        # Unknown event type - log and ignore
        return True

    def _handle_payment_captured(self, event: WebhookEvent) -> bool:
        """Handle successful payment capture."""
        if not event.invoice_id:
            return False

        # Mark invoice paid
        from src.models import PaymentMethod
        method_map = {
            "stripe": PaymentMethod.STRIPE,
            "paypal": PaymentMethod.PAYPAL,
            "manual": PaymentMethod.MANUAL,
        }

        self._invoice_service.mark_paid(
            invoice_id=event.invoice_id,
            payment_ref=event.payment_intent_id,
            payment_method=method_map.get(event.provider, PaymentMethod.MANUAL),
        )

        # Get invoice for subscription activation
        invoice = self._invoice_service._invoice_repo.find_by_id(event.invoice_id)
        if invoice and invoice.subscription_id:
            self._subscription_service.activate_subscription(invoice.subscription_id)

        # Activate user if pending
        if invoice:
            user = self._user_service.get_user(invoice.user_id)
            if user and user.status.value == "pending":
                from src.models import UserStatus
                self._user_service.update_user_status(invoice.user_id, UserStatus.ACTIVE)

        # Send confirmation email
        if self._email_service and invoice:
            self._email_service.send_payment_confirmation(invoice)

        return True

    def _handle_payment_failed(self, event: WebhookEvent) -> bool:
        """Handle failed payment."""
        if event.invoice_id:
            self._invoice_service.mark_cancelled(event.invoice_id)
        return True

    def _handle_checkout_completed(self, event: WebhookEvent) -> bool:
        """Handle checkout session completion."""
        # Same as payment captured for redirect flows
        return self._handle_payment_captured(event)

    def _handle_checkout_expired(self, event: WebhookEvent) -> bool:
        """Handle expired checkout session."""
        if event.invoice_id:
            self._invoice_service.mark_expired(event.invoice_id)
        return True

    def _handle_payment_authorized(self, event: WebhookEvent) -> bool:
        """Handle payment authorization (before capture)."""
        # Log for manual capture workflows
        return True

    def _handle_payment_refunded(self, event: WebhookEvent) -> bool:
        """Handle payment refund."""
        if event.invoice_id:
            # Update invoice status
            self._invoice_service.mark_refunded(event.invoice_id)
        return True
```

---

## Configuration Example

```python
# config.py

PAYMENT_CONFIG = {
    # Default provider for each method
    "default_providers": {
        "card": "stripe",
        "invoice": "manual",
        "bnpl": "klarna",
    },

    # Provider configurations
    "providers": {
        "stripe": {
            "enabled": True,
            "api_key": "${STRIPE_API_KEY}",
            "webhook_secret": "${STRIPE_WEBHOOK_SECRET}",
            "supported_methods": ["card", "wallet"],
        },
        "paypal": {
            "enabled": True,
            "client_id": "${PAYPAL_CLIENT_ID}",
            "client_secret": "${PAYPAL_CLIENT_SECRET}",
            "sandbox": True,
            "webhook_id": "${PAYPAL_WEBHOOK_ID}",
            "supported_methods": ["card", "wallet"],
        },
        "manual": {
            "enabled": True,
            "invoice_due_days": 14,
            "supported_methods": ["invoice", "bank_transfer"],
        },
        "klarna": {
            "enabled": False,  # Enable when configured
            "api_key": "${KLARNA_API_KEY}",
            "api_secret": "${KLARNA_API_SECRET}",
            "supported_methods": ["invoice", "bnpl"],
            "supported_countries": ["DE", "AT", "NL", "SE"],
        },
    },
}
```

---

## Summary

This architecture provides:

1. **Complete Provider Agnosticism** - Business logic never touches provider-specific code
2. **Plugin System** - New providers added as self-contained plugins
3. **Payment Method Abstraction** - Different payment types handled uniformly
4. **SDK Adapter Layer** - Clean separation between plugins and SDK clients
5. **Normalized Events** - Webhooks converted to standard event types
6. **Easy Extension** - Add new methods or providers without core changes

See also:
- `puml/payment-architecture.puml` - Architecture diagram
- `sprints/sprint-4-payments.md` - Implementation details
