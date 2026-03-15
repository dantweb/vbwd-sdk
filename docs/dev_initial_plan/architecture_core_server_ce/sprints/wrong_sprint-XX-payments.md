# Sprint 4: Invoicing & Plugin-Based Payment System

**Goal:** Implement invoice management, provider-agnostic payment system with plugin architecture, and checkout flow.

**Prerequisites:** Sprint 3 complete (subscriptions and tariff plans)

**Related Documentation:**
- [Payment Architecture](../payment-architecture.md) - Provider-agnostic payment platform design
- [Plugin System](../plugin-system.md) - General-purpose plugin framework

---

## Objectives

- [ ] General-purpose plugin system (IPlugin, PluginManager, PluginRegistry)
- [ ] **Plugin lifecycle**: Singletons (thread-safe, connection pooling)
- [ ] **EventDispatcher** with sequential handler execution (replaces EventBus)
- [ ] **Idempotency key middleware** (prevent duplicate payments)
- [ ] Payment component built on plugin system
- [ ] InvoiceService with tax breakdown
- [ ] PaymentProviderAdapter interface and implementations
- [ ] Payment method abstractions (Card, Invoice/PayLater)
- [ ] CheckoutOrchestrator (provider-agnostic)
- [ ] Stripe plugin implementation
- [ ] ManualPayment plugin (pay invoice later)
- [ ] Checkout and invoice routes

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│   (Checkout Routes, Webhook Routes, Invoice Routes)              │
├─────────────────────────────────────────────────────────────────┤
│                   Payment Service Layer                          │
│   (CheckoutOrchestrator, WebhookHandler, RefundService)          │
│   Provider-agnostic business logic                               │
├─────────────────────────────────────────────────────────────────┤
│                 Payment Method Abstraction                       │
│   (CardPayment, InvoicePayment, WalletPayment)                  │
│   Strategy pattern for payment types                             │
├─────────────────────────────────────────────────────────────────┤
│                  Provider Adapter Layer                          │
│   (IPaymentProviderAdapter, PluginRegistry)                      │
├─────────────────────────────────────────────────────────────────┤
│                      Plugin System                               │
│   (StripePlugin, PayPalPlugin, ManualPaymentPlugin)              │
├─────────────────────────────────────────────────────────────────┤
│                    SDK Adapter Layer                             │
│   (StripeSDKClient, PayPalRESTClient)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tasks

### 4.0 Plugin System Foundation

**TDD Steps:**

#### Step 1: Write failing tests for plugin interfaces

**File:** `python/api/tests/unit/plugins/test_plugin_system.py`

```python
"""Tests for plugin system."""
import pytest
from unittest.mock import Mock


class TestPluginInterface:
    """Test cases for IPlugin interface."""

    def test_plugin_has_required_attributes(self):
        """Plugin must have name, version, and description."""
        from src.plugins import IPlugin

        class TestPlugin(IPlugin):
            @property
            def name(self) -> str:
                return "test-plugin"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Test plugin"

            def initialize(self, config: dict) -> None:
                pass

            def activate(self) -> None:
                pass

            def deactivate(self) -> None:
                pass

        plugin = TestPlugin()
        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Test plugin"

    def test_plugin_lifecycle_methods(self):
        """Plugin lifecycle: initialize -> activate -> deactivate."""
        from src.plugins import IPlugin

        lifecycle_calls = []

        class LifecyclePlugin(IPlugin):
            @property
            def name(self) -> str:
                return "lifecycle-plugin"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Lifecycle test"

            def initialize(self, config: dict) -> None:
                lifecycle_calls.append("initialize")

            def activate(self) -> None:
                lifecycle_calls.append("activate")

            def deactivate(self) -> None:
                lifecycle_calls.append("deactivate")

        plugin = LifecyclePlugin()
        plugin.initialize({})
        plugin.activate()
        plugin.deactivate()

        assert lifecycle_calls == ["initialize", "activate", "deactivate"]


class TestPluginManager:
    """Test cases for PluginManager."""

    def test_register_plugin(self):
        """PluginManager should register plugins."""
        from src.plugins import PluginManager, IPlugin

        mock_plugin = Mock(spec=IPlugin)
        mock_plugin.name = "test"

        manager = PluginManager()
        manager.register(mock_plugin)

        assert "test" in manager.plugins

    def test_get_plugin_by_name(self):
        """PluginManager should retrieve plugins by name."""
        from src.plugins import PluginManager, IPlugin

        mock_plugin = Mock(spec=IPlugin)
        mock_plugin.name = "my-plugin"

        manager = PluginManager()
        manager.register(mock_plugin)

        result = manager.get("my-plugin")
        assert result == mock_plugin

    def test_activate_all_plugins(self):
        """PluginManager should activate all registered plugins."""
        from src.plugins import PluginManager, IPlugin

        mock_plugin1 = Mock(spec=IPlugin)
        mock_plugin1.name = "plugin1"
        mock_plugin2 = Mock(spec=IPlugin)
        mock_plugin2.name = "plugin2"

        manager = PluginManager()
        manager.register(mock_plugin1)
        manager.register(mock_plugin2)
        manager.activate_all()

        mock_plugin1.activate.assert_called_once()
        mock_plugin2.activate.assert_called_once()


class TestPluginRegistry:
    """Test cases for PluginRegistry."""

    def test_find_plugins_by_capability(self):
        """Registry should find plugins by capability."""
        from src.plugins import PluginRegistry, IPlugin

        mock_plugin = Mock(spec=IPlugin)
        mock_plugin.name = "payment-plugin"
        mock_plugin.capabilities = ["payment", "checkout"]

        registry = PluginRegistry()
        registry.register(mock_plugin)

        results = registry.find_by_capability("payment")
        assert mock_plugin in results
```

#### Step 2: Implement plugin interfaces

**File:** `python/api/src/plugins/__init__.py`

```python
"""Plugin system exports."""
from .interfaces import IPlugin, IComponent
from .manager import PluginManager
from .registry import PluginRegistry

__all__ = ["IPlugin", "IComponent", "PluginManager", "PluginRegistry"]
```

**File:** `python/api/src/plugins/interfaces.py`

```python
"""Plugin system interfaces."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class IPlugin(ABC):
    """
    Base plugin interface.

    All plugins must implement this interface for lifecycle management.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semver)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""
        pass

    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this plugin provides."""
        return []

    @property
    def dependencies(self) -> List[str]:
        """List of plugin names this plugin depends on."""
        return []

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        Called once during plugin loading.
        """
        pass

    @abstractmethod
    def activate(self) -> None:
        """
        Activate the plugin.

        Called when plugin becomes active.
        """
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """
        Deactivate the plugin.

        Called when plugin is being disabled.
        """
        pass


class IComponent(ABC):
    """
    Component interface for plugin-provided functionality.

    Plugins can register multiple components.
    """

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Type of component (e.g., 'payment', 'notification')."""
        pass

    @property
    @abstractmethod
    def component_id(self) -> str:
        """Unique component identifier."""
        pass
```

**File:** `python/api/src/plugins/manager.py`

```python
"""Plugin manager implementation."""
from typing import Dict, Optional, List
from .interfaces import IPlugin


class PluginManager:
    """
    Manages plugin lifecycle.

    Handles registration, initialization, activation, and deactivation.
    """

    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._active: Dict[str, bool] = {}

    @property
    def plugins(self) -> Dict[str, IPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def register(self, plugin: IPlugin) -> None:
        """Register a plugin."""
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' already registered")
        self._plugins[plugin.name] = plugin
        self._active[plugin.name] = False

    def get(self, name: str) -> Optional[IPlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def initialize_all(self, configs: Dict[str, dict] = None) -> None:
        """Initialize all plugins with their configs."""
        configs = configs or {}
        for name, plugin in self._plugins.items():
            config = configs.get(name, {})
            plugin.initialize(config)

    def activate_all(self) -> None:
        """Activate all registered plugins."""
        # Sort by dependencies
        sorted_plugins = self._sort_by_dependencies()
        for name in sorted_plugins:
            self._plugins[name].activate()
            self._active[name] = True

    def deactivate_all(self) -> None:
        """Deactivate all active plugins."""
        # Reverse order for deactivation
        sorted_plugins = self._sort_by_dependencies()
        for name in reversed(sorted_plugins):
            if self._active.get(name):
                self._plugins[name].deactivate()
                self._active[name] = False

    def _sort_by_dependencies(self) -> List[str]:
        """Topologically sort plugins by dependencies."""
        visited = set()
        result = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            plugin = self._plugins.get(name)
            if plugin:
                for dep in plugin.dependencies:
                    visit(dep)
            result.append(name)

        for name in self._plugins:
            visit(name)

        return result
```

**File:** `python/api/src/plugins/registry.py`

```python
"""Plugin registry for component lookup."""
from typing import Dict, List, Optional, Type
from .interfaces import IPlugin, IComponent


class PluginRegistry:
    """
    Registry for plugin and component lookup.

    Provides capability-based discovery.
    """

    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._components: Dict[str, Dict[str, IComponent]] = {}

    def register(self, plugin: IPlugin) -> None:
        """Register a plugin."""
        self._plugins[plugin.name] = plugin

    def register_component(
        self,
        component_type: str,
        component_id: str,
        component: IComponent,
    ) -> None:
        """Register a component."""
        if component_type not in self._components:
            self._components[component_type] = {}
        self._components[component_type][component_id] = component

    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_component(
        self,
        component_type: str,
        component_id: str,
    ) -> Optional[IComponent]:
        """Get component by type and ID."""
        type_components = self._components.get(component_type, {})
        return type_components.get(component_id)

    def find_by_capability(self, capability: str) -> List[IPlugin]:
        """Find all plugins with a given capability."""
        return [
            plugin for plugin in self._plugins.values()
            if capability in plugin.capabilities
        ]

    def get_components_by_type(self, component_type: str) -> List[IComponent]:
        """Get all components of a given type."""
        return list(self._components.get(component_type, {}).values())
```

---

### 4.0.1 Plugin Lifecycle: Singletons and Thread Safety

**CRITICAL**: Payment plugins are registered as **singletons** (one instance shared across all requests) for connection pooling and efficiency.

#### Requirements:

1. **Thread-Safe Implementation**: Plugins must be stateless or use thread-safe state management
2. **Connection Pooling**: External API clients (Stripe, PayPal) handle concurrency internally
3. **No Mutable Shared State**: Instance variables should be immutable or protected

**File:** `python/api/src/container.py`

```python
"""Dependency injection container with singleton plugins."""
from dependency_injector import containers, providers
from src.plugins import PluginManager
from src.plugins.payment import StripePlugin, PayPalPlugin, ManualPaymentPlugin


class Container(containers.DeclarativeContainer):
    """DI container for application services."""

    config = providers.Configuration()

    # Plugin Manager (singleton)
    plugin_manager = providers.Singleton(PluginManager)

    # Payment Plugins (singletons - thread-safe)
    stripe_plugin = providers.Singleton(
        StripePlugin,
        api_key=config.stripe.api_key,
    )

    paypal_plugin = providers.Singleton(
        PayPalPlugin,
        client_id=config.paypal.client_id,
        client_secret=config.paypal.client_secret,
    )

    manual_payment_plugin = providers.Singleton(
        ManualPaymentPlugin,
    )
```

**Plugin Thread-Safety Example:**

**File:** `python/api/src/plugins/payment/stripe_plugin.py`

```python
"""Stripe payment plugin (thread-safe singleton)."""
import stripe
from typing import Dict, Any
from src.plugins import IPlugin
from src.plugins.payment import IPaymentProviderAdapter


class StripePlugin(IPlugin, IPaymentProviderAdapter):
    """
    Stripe payment plugin.

    Thread-safe singleton - Stripe client handles concurrency internally.
    """

    def __init__(self, api_key: str):
        """
        Initialize Stripe plugin.

        Args:
            api_key: Stripe API key (immutable)
        """
        # Immutable configuration (thread-safe)
        self._api_key = api_key

        # Stripe client is thread-safe
        self._client = stripe.StripeClient(api_key=api_key)

    @property
    def name(self) -> str:
        return "stripe"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Stripe payment provider"

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize (no mutable state)."""
        pass

    def activate(self) -> None:
        """Activate plugin."""
        pass

    def deactivate(self) -> None:
        """Deactivate plugin."""
        pass

    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create payment intent (thread-safe).

        No mutable instance state - safe for concurrent calls.
        """
        # Thread-safe: Stripe client handles concurrency
        payment_intent = self._client.payment_intents.create(
            amount=amount,
            currency=currency,
            metadata=metadata,
        )
        return payment_intent
```

---

### 4.0.2 Idempotency Key Middleware

**CRITICAL**: Payment operations require idempotency keys to prevent duplicate charges when requests are retried.

**File:** `python/api/src/middleware/idempotency.py`

```python
"""Idempotency key middleware for payment operations."""
from functools import wraps
from flask import request, jsonify, g
from src.utils.redis_client import redis_client
import json
import logging

logger = logging.getLogger(__name__)


def require_idempotency_key(f):
    """
    Decorator requiring Idempotency-Key header for payment operations.

    Usage:
        @app.route('/api/subscriptions/<int:id>/activate', methods=['POST'])
        @require_idempotency_key
        def activate_subscription(id):
            # Your logic here
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for idempotency key
        idempotency_key = request.headers.get('Idempotency-Key')

        if not idempotency_key:
            return jsonify({
                "error": "Missing Idempotency-Key header",
                "message": "Payment operations require an Idempotency-Key header"
            }), 400

        # Check if we've seen this key before
        cached_response = redis_client.get_idempotency_key(idempotency_key)

        if cached_response:
            # Return cached response
            logger.info(f"Idempotency key hit: {idempotency_key}")
            return jsonify(json.loads(cached_response)), 200

        # Store key in request context for later caching
        g.idempotency_key = idempotency_key

        # Execute the function
        response = f(*args, **kwargs)

        # Cache successful response (only 2xx status codes)
        if isinstance(response, tuple):
            data, status_code = response
        else:
            data = response
            status_code = 200

        if 200 <= status_code < 300:
            redis_client.set_idempotency_key(
                idempotency_key,
                json.dumps(data.get_json() if hasattr(data, 'get_json') else data),
                ttl=86400,  # 24 hours
            )
            logger.info(f"Cached response for idempotency key: {idempotency_key}")

        return response

    return decorated_function
```

**Usage in Routes:**

**File:** `python/api/src/routes/subscriptions.py`

```python
"""Subscription routes with idempotency."""
from flask import Blueprint, request, jsonify
from src.middleware.idempotency import require_idempotency_key
from src.services import SubscriptionService

bp = Blueprint('subscriptions', __name__)


@bp.route('/api/subscriptions/<int:subscription_id>/activate', methods=['POST'])
@require_idempotency_key  # Prevents duplicate activation
def activate_subscription(subscription_id: int):
    """
    Activate subscription with payment.

    Requires: Idempotency-Key header
    """
    subscription_service = get_service(SubscriptionService)

    try:
        result = subscription_service.activate(subscription_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route('/api/invoices/<int:invoice_id>/pay', methods=['POST'])
@require_idempotency_key  # Prevents double payment
def pay_invoice(invoice_id: int):
    """
    Pay invoice.

    Requires: Idempotency-Key header
    """
    invoice_service = get_service(InvoiceService)

    payment_method = request.json.get('payment_method')

    try:
        result = invoice_service.process_payment(
            invoice_id=invoice_id,
            payment_method=payment_method,
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
```

**Test Idempotency:**

**File:** `python/api/tests/integration/test_idempotency.py`

```python
"""Tests for idempotency middleware."""
import pytest
from flask import Flask
import json


class TestIdempotencyMiddleware:
    """Test idempotency key handling."""

    def test_missing_idempotency_key_returns_400(self, client):
        """Missing idempotency key should return 400."""
        response = client.post('/api/subscriptions/1/activate')

        assert response.status_code == 400
        data = response.get_json()
        assert 'Idempotency-Key' in data['error']

    def test_duplicate_request_returns_cached_response(self, client):
        """Duplicate requests with same key return cached response."""
        headers = {'Idempotency-Key': 'test-key-123'}

        # First request
        response1 = client.post(
            '/api/subscriptions/1/activate',
            headers=headers,
            json={'payment_method': 'stripe'},
        )
        assert response1.status_code == 200
        data1 = response1.get_json()

        # Second request (should return cached)
        response2 = client.post(
            '/api/subscriptions/1/activate',
            headers=headers,
            json={'payment_method': 'stripe'},
        )
        assert response2.status_code == 200
        data2 = response2.get_json()

        # Responses should be identical
        assert data1 == data2

    def test_different_keys_execute_independently(self, client):
        """Different idempotency keys execute independently."""
        response1 = client.post(
            '/api/subscriptions/1/activate',
            headers={'Idempotency-Key': 'key-1'},
            json={'payment_method': 'stripe'},
        )

        response2 = client.post(
            '/api/subscriptions/2/activate',
            headers={'Idempotency-Key': 'key-2'},
            json={'payment_method': 'stripe'},
        )

        # Both should execute successfully
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_failed_requests_not_cached(self, client):
        """Failed requests (4xx/5xx) should not be cached."""
        headers = {'Idempotency-Key': 'fail-key-123'}

        # First request (fails)
        response1 = client.post(
            '/api/subscriptions/999/activate',  # Non-existent
            headers=headers,
        )
        assert response1.status_code == 404

        # Second request should also execute (not cached)
        response2 = client.post(
            '/api/subscriptions/999/activate',
            headers=headers,
        )
        assert response2.status_code == 404
```

---

### 4.1 InvoiceService Implementation

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/services/test_invoice_service.py`

```python
"""Tests for InvoiceService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, timedelta


class TestInvoiceServiceCreate:
    """Test cases for creating invoices."""

    def test_create_invoice_generates_number(self):
        """create_invoice should generate unique invoice number."""
        from src.services import InvoiceService
        from src.models import UserInvoice, TarifPlan, BillingPeriod, InvoiceStatus

        mock_invoice_repo = Mock()
        mock_plan_repo = Mock()
        mock_tax_service = Mock()

        plan = TarifPlan(
            id=1, name="Pro", price=Decimal("29.99"),
            currency="EUR", billing_period=BillingPeriod.MONTHLY,
        )
        mock_plan_repo.find_by_id.return_value = plan
        mock_tax_service.get_tax_breakdown.return_value = {
            "net_amount": Decimal("29.99"),
            "tax_amount": Decimal("5.70"),
            "gross_amount": Decimal("35.69"),
            "tax_rate": Decimal("19.0"),
            "tax_code": "VAT_DE",
        }
        mock_invoice_repo.save.return_value = UserInvoice(
            id=1,
            invoice_number="INV-20231201-ABC123",
            amount=Decimal("35.69"),
        )

        service = InvoiceService(
            invoice_repo=mock_invoice_repo,
            tarif_plan_repo=mock_plan_repo,
            tax_service=mock_tax_service,
        )
        result = service.create_invoice(
            user_id=1,
            tarif_plan_id=1,
            country_code="DE",
        )

        assert result.invoice_number.startswith("INV-")
        mock_invoice_repo.save.assert_called_once()

    def test_create_invoice_includes_tax(self):
        """create_invoice should include tax breakdown."""
        from src.services import InvoiceService
        from src.models import UserInvoice, TarifPlan, BillingPeriod

        mock_invoice_repo = Mock()
        mock_plan_repo = Mock()
        mock_tax_service = Mock()

        plan = TarifPlan(id=1, price=Decimal("100.00"), currency="EUR")
        mock_plan_repo.find_by_id.return_value = plan
        mock_tax_service.get_tax_breakdown.return_value = {
            "net_amount": Decimal("100.00"),
            "tax_amount": Decimal("19.00"),
            "gross_amount": Decimal("119.00"),
            "tax_rate": Decimal("19.0"),
            "tax_code": "VAT_DE",
        }

        captured_invoice = None
        def capture_save(inv):
            nonlocal captured_invoice
            captured_invoice = inv
            inv.id = 1
            return inv
        mock_invoice_repo.save.side_effect = capture_save

        service = InvoiceService(
            invoice_repo=mock_invoice_repo,
            tarif_plan_repo=mock_plan_repo,
            tax_service=mock_tax_service,
        )
        service.create_invoice(user_id=1, tarif_plan_id=1, country_code="DE")

        assert captured_invoice.amount == Decimal("119.00")
        assert captured_invoice.tax_amount == Decimal("19.00")


class TestInvoiceServiceMarkPaid:
    """Test cases for marking invoices paid."""

    def test_mark_paid_updates_status(self):
        """mark_paid should update invoice status and payment info."""
        from src.services import InvoiceService
        from src.models import UserInvoice, InvoiceStatus, PaymentMethod

        mock_invoice_repo = Mock()
        invoice = UserInvoice(
            id=1,
            user_id=1,
            tarif_plan_id=1,
            invoice_number="INV-001",
            amount=Decimal("29.99"),
            status=InvoiceStatus.INVOICED,
        )
        mock_invoice_repo.find_by_id.return_value = invoice
        mock_invoice_repo.save.return_value = invoice

        service = InvoiceService(invoice_repo=mock_invoice_repo)
        result = service.mark_paid(
            invoice_id=1,
            payment_ref="PAY-123",
            payment_method=PaymentMethod.STRIPE,
        )

        assert result.status == InvoiceStatus.PAID
        assert result.payment_ref == "PAY-123"
        assert result.paid_at is not None


class TestInvoiceServiceExpire:
    """Test cases for expiring invoices."""

    def test_expire_pending_invoices(self):
        """expire_pending_invoices should mark old invoices as expired."""
        from src.services import InvoiceService
        from src.models import UserInvoice, InvoiceStatus

        mock_invoice_repo = Mock()
        old_invoices = [
            UserInvoice(id=1, status=InvoiceStatus.INVOICED),
            UserInvoice(id=2, status=InvoiceStatus.INVOICED),
        ]
        mock_invoice_repo.find_pending_expired.return_value = old_invoices

        service = InvoiceService(invoice_repo=mock_invoice_repo)
        count = service.expire_pending_invoices()

        assert count == 2
        assert mock_invoice_repo.save.call_count == 2
```

#### Step 2: Implement to pass

**File:** `python/api/src/services/invoice_service.py`

```python
"""Invoice service implementation."""
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List
from src.interfaces import IInvoiceService
from src.models import UserInvoice, InvoiceStatus, PaymentMethod


class InvoiceService(IInvoiceService):
    """
    Invoice management service.

    Handles invoice creation, payment tracking, and tax calculations.
    """

    INVOICE_EXPIRY_DAYS = 7

    def __init__(
        self,
        invoice_repo: "IInvoiceRepository",
        tarif_plan_repo: Optional["ITarifPlanRepository"] = None,
        tax_service: Optional["TaxService"] = None,
        currency_service: Optional["CurrencyService"] = None,
    ):
        self._invoice_repo = invoice_repo
        self._tarif_plan_repo = tarif_plan_repo
        self._tax_service = tax_service
        self._currency_service = currency_service

    def create_invoice(
        self,
        user_id: int,
        tarif_plan_id: int,
        subscription_id: Optional[int] = None,
        country_code: Optional[str] = None,
        currency_code: str = "EUR",
    ) -> UserInvoice:
        """
        Create new invoice with tax calculation.

        Args:
            user_id: User ID.
            tarif_plan_id: Tariff plan ID.
            subscription_id: Optional subscription ID.
            country_code: Country for tax calculation.
            currency_code: Currency for the invoice.

        Returns:
            Created invoice.
        """
        # Get plan
        plan = self._tarif_plan_repo.find_by_id(tarif_plan_id)
        if not plan:
            raise ValueError(f"Tariff plan {tarif_plan_id} not found")

        # Get price in currency
        net_amount = plan.price
        if self._currency_service and currency_code != plan.currency:
            net_amount = self._currency_service.convert(
                plan.price, plan.currency, currency_code
            )

        # Calculate tax
        tax_amount = Decimal("0.00")
        tax_code = None
        tax_rate = Decimal("0.00")

        if self._tax_service and country_code:
            breakdown = self._tax_service.get_tax_breakdown(net_amount, country_code)
            tax_amount = breakdown["tax_amount"]
            tax_code = breakdown.get("tax_code")
            tax_rate = breakdown.get("tax_rate", Decimal("0.00"))
            gross_amount = breakdown["gross_amount"]
        else:
            gross_amount = net_amount

        # Create invoice
        invoice = UserInvoice(
            user_id=user_id,
            tarif_plan_id=tarif_plan_id,
            subscription_id=subscription_id,
            invoice_number=UserInvoice.generate_invoice_number(),
            amount=gross_amount,
            net_amount=net_amount,
            tax_amount=tax_amount,
            tax_code=tax_code,
            tax_rate=tax_rate,
            currency=currency_code,
            status=InvoiceStatus.INVOICED,
            invoiced_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.INVOICE_EXPIRY_DAYS),
        )

        return self._invoice_repo.save(invoice)

    def mark_paid(
        self,
        invoice_id: int,
        payment_ref: str,
        payment_method: PaymentMethod,
    ) -> UserInvoice:
        """Mark invoice as paid."""
        invoice = self._invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status != InvoiceStatus.INVOICED:
            raise ValueError(f"Invoice {invoice_id} is not payable (status: {invoice.status})")

        invoice.mark_paid(payment_ref, payment_method)
        return self._invoice_repo.save(invoice)

    def mark_expired(self, invoice_id: int) -> UserInvoice:
        """Mark invoice as expired."""
        invoice = self._invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        invoice.mark_expired()
        return self._invoice_repo.save(invoice)

    def mark_cancelled(self, invoice_id: int) -> UserInvoice:
        """Mark invoice as cancelled."""
        invoice = self._invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        invoice.mark_cancelled()
        return self._invoice_repo.save(invoice)

    def get_user_invoices(self, user_id: int) -> List[UserInvoice]:
        """Get all invoices for user."""
        return self._invoice_repo.find_by_user_id(user_id)

    def get_invoice_by_number(self, invoice_number: str) -> Optional[UserInvoice]:
        """Get invoice by invoice number."""
        return self._invoice_repo.find_by_invoice_number(invoice_number)

    def expire_pending_invoices(self) -> int:
        """
        Expire invoices past their deadline.

        Returns count of expired invoices.
        Should be run periodically.
        """
        expired = self._invoice_repo.find_pending_expired()
        count = 0

        for invoice in expired:
            invoice.mark_expired()
            self._invoice_repo.save(invoice)
            count += 1

        return count
```

---

### 4.2 Payment Provider Adapter Interface

**TDD Steps:**

#### Step 1: Write failing tests for payment adapter

**File:** `python/api/tests/unit/payment/test_payment_adapter.py`

```python
"""Tests for payment provider adapter interface."""
import pytest
from unittest.mock import Mock
from decimal import Decimal


class TestPaymentProviderAdapter:
    """Test cases for IPaymentProviderAdapter."""

    def test_adapter_implements_required_methods(self):
        """Adapter must implement all required methods."""
        from src.payment import IPaymentProviderAdapter

        class TestAdapter(IPaymentProviderAdapter):
            @property
            def provider_name(self) -> str:
                return "test"

            @property
            def supported_payment_methods(self) -> list:
                return ["card"]

            def create_checkout_session(self, **kwargs):
                return {"session_id": "123", "checkout_url": "http://test.com"}

            def capture_payment(self, payment_id: str):
                return {"success": True}

            def refund_payment(self, payment_id: str, amount=None):
                return {"refund_id": "ref-123"}

            def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
                return True

            def parse_webhook_event(self, payload: dict):
                return {"type": "payment.completed"}

            def get_payment_status(self, payment_id: str):
                return "completed"

        adapter = TestAdapter()
        assert adapter.provider_name == "test"
        assert "card" in adapter.supported_payment_methods


class TestPaymentIntent:
    """Test cases for normalized PaymentIntent."""

    def test_payment_intent_structure(self):
        """PaymentIntent should have normalized structure."""
        from src.payment import PaymentIntent, PaymentStatus

        intent = PaymentIntent(
            id="pi_123",
            provider="stripe",
            amount=Decimal("29.99"),
            currency="EUR",
            status=PaymentStatus.PENDING,
            invoice_id=1,
        )

        assert intent.id == "pi_123"
        assert intent.provider == "stripe"
        assert intent.status == PaymentStatus.PENDING
```

#### Step 2: Implement payment adapter interface

**File:** `python/api/src/payment/__init__.py`

```python
"""Payment system exports."""
from .interfaces import (
    IPaymentProviderAdapter,
    IPaymentMethod,
    PaymentIntent,
    PaymentStatus,
    CheckoutSession,
    WebhookEvent,
)
from .methods import CardPayment, InvoicePayment
from .registry import PaymentProviderRegistry

__all__ = [
    "IPaymentProviderAdapter",
    "IPaymentMethod",
    "PaymentIntent",
    "PaymentStatus",
    "CheckoutSession",
    "WebhookEvent",
    "CardPayment",
    "InvoicePayment",
    "PaymentProviderRegistry",
]
```

**File:** `python/api/src/payment/interfaces.py`

```python
"""Payment system interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class PaymentStatus(Enum):
    """Normalized payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class PaymentIntent:
    """Normalized payment intent."""
    id: str
    provider: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    invoice_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CheckoutSession:
    """Checkout session for redirect-based payments."""
    session_id: str
    checkout_url: str
    provider: str
    expires_at: Optional[datetime] = None


@dataclass
class WebhookEvent:
    """Normalized webhook event."""
    id: str
    type: str
    provider: str
    invoice_id: Optional[int]
    payment_intent_id: Optional[str]
    data: Dict[str, Any]


class IPaymentProviderAdapter(ABC):
    """
    Interface for payment provider adapters.

    All payment plugins must implement this interface.
    Provider-specific logic is encapsulated here.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier."""
        pass

    @property
    @abstractmethod
    def supported_payment_methods(self) -> List[str]:
        """List of supported payment method types."""
        pass

    @abstractmethod
    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        invoice_id: int,
        success_url: str,
        cancel_url: str,
        payment_method: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckoutSession:
        """Create a checkout session for redirect-based payment."""
        pass

    @abstractmethod
    def capture_payment(self, payment_id: str) -> PaymentIntent:
        """Capture an authorized payment."""
        pass

    @abstractmethod
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Refund a payment (full or partial)."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify webhook signature."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse webhook payload into normalized event."""
        pass

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get current payment status."""
        pass


class IPaymentMethod(ABC):
    """
    Interface for payment method strategies.

    Defines payment method behavior independent of provider.
    """

    @property
    @abstractmethod
    def method_type(self) -> str:
        """Payment method type identifier."""
        pass

    @property
    @abstractmethod
    def requires_redirect(self) -> bool:
        """Whether this method requires redirect to external site."""
        pass

    @property
    @abstractmethod
    def supports_recurring(self) -> bool:
        """Whether this method supports recurring payments."""
        pass

    @abstractmethod
    def get_compatible_providers(self) -> List[str]:
        """Get list of provider names that support this method."""
        pass

    @abstractmethod
    def validate_payment_details(self, details: Dict[str, Any]) -> bool:
        """Validate payment details for this method."""
        pass
```

---

### 4.3 Payment Method Implementations

**File:** `python/api/src/payment/methods.py`

```python
"""Payment method implementations."""
from typing import List, Dict, Any
from .interfaces import IPaymentMethod


class CardPayment(IPaymentMethod):
    """Credit/debit card payment method."""

    @property
    def method_type(self) -> str:
        return "card"

    @property
    def requires_redirect(self) -> bool:
        return True  # Redirect to Stripe/PayPal checkout

    @property
    def supports_recurring(self) -> bool:
        return True

    def get_compatible_providers(self) -> List[str]:
        return ["stripe", "paypal"]

    def validate_payment_details(self, details: Dict[str, Any]) -> bool:
        # Card details validated by provider
        return True


class InvoicePayment(IPaymentMethod):
    """Pay by invoice (pay later) method."""

    @property
    def method_type(self) -> str:
        return "invoice"

    @property
    def requires_redirect(self) -> bool:
        return False  # No redirect, invoice sent

    @property
    def supports_recurring(self) -> bool:
        return False  # One-time payment per invoice

    def get_compatible_providers(self) -> List[str]:
        return ["manual"]

    def validate_payment_details(self, details: Dict[str, Any]) -> bool:
        # Require billing address for invoice
        required = ["billing_name", "billing_address"]
        return all(key in details for key in required)


class WalletPayment(IPaymentMethod):
    """Digital wallet payment (PayPal, Apple Pay)."""

    @property
    def method_type(self) -> str:
        return "wallet"

    @property
    def requires_redirect(self) -> bool:
        return True

    @property
    def supports_recurring(self) -> bool:
        return True

    def get_compatible_providers(self) -> List[str]:
        return ["paypal"]

    def validate_payment_details(self, details: Dict[str, Any]) -> bool:
        return True
```

---

### 4.4 Stripe Plugin Implementation

**File:** `python/api/tests/unit/plugins/test_stripe_plugin.py`

```python
"""Tests for Stripe payment plugin."""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal


class TestStripePlugin:
    """Test cases for StripePlugin."""

    def test_plugin_properties(self):
        """StripePlugin should have correct properties."""
        from src.plugins.payment import StripePlugin

        plugin = StripePlugin()

        assert plugin.name == "stripe"
        assert "payment" in plugin.capabilities
        assert "card" in plugin.adapter.supported_payment_methods

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_create):
        """StripePlugin should create Stripe checkout session."""
        from src.plugins.payment import StripePlugin

        mock_create.return_value = Mock(
            id="cs_123",
            url="https://checkout.stripe.com/cs_123",
        )

        plugin = StripePlugin()
        plugin.initialize({"api_key": "sk_test_xxx", "webhook_secret": "whsec_xxx"})
        plugin.activate()

        session = plugin.adapter.create_checkout_session(
            amount=Decimal("29.99"),
            currency="EUR",
            invoice_id=1,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            payment_method="card",
        )

        assert session.session_id == "cs_123"
        assert "stripe.com" in session.checkout_url
```

#### Step 2: Implement Stripe plugin

**File:** `python/api/src/plugins/payment/__init__.py`

```python
"""Payment plugins exports."""
from .stripe_plugin import StripePlugin
from .manual_plugin import ManualPaymentPlugin

__all__ = ["StripePlugin", "ManualPaymentPlugin"]
```

**File:** `python/api/src/plugins/payment/stripe_plugin.py`

```python
"""Stripe payment plugin."""
import stripe
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.plugins import IPlugin
from src.payment import (
    IPaymentProviderAdapter,
    PaymentIntent,
    PaymentStatus,
    CheckoutSession,
    WebhookEvent,
)


class StripeAdapter(IPaymentProviderAdapter):
    """Stripe SDK adapter."""

    def __init__(self):
        self._api_key: Optional[str] = None
        self._webhook_secret: Optional[str] = None

    def configure(self, api_key: str, webhook_secret: str) -> None:
        """Configure Stripe SDK."""
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        stripe.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "stripe"

    @property
    def supported_payment_methods(self) -> List[str]:
        return ["card", "sepa_debit"]

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        invoice_id: int,
        success_url: str,
        cancel_url: str,
        payment_method: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckoutSession:
        """Create Stripe Checkout Session."""
        amount_cents = int(amount * 100)

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=[payment_method],
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": amount_cents,
                    "product_data": {"name": "Subscription"},
                },
                "quantity": 1,
            }],
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
            metadata={"invoice_id": str(invoice_id), **(metadata or {})},
        )

        return CheckoutSession(
            session_id=session.id,
            checkout_url=session.url,
            provider="stripe",
        )

    def capture_payment(self, payment_id: str) -> PaymentIntent:
        """Capture a Stripe payment intent."""
        intent = stripe.PaymentIntent.capture(payment_id)
        return PaymentIntent(
            id=intent.id,
            provider="stripe",
            amount=Decimal(intent.amount) / 100,
            currency=intent.currency.upper(),
            status=self._map_status(intent.status),
        )

    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Refund a Stripe payment."""
        params = {"payment_intent": payment_id}
        if amount:
            params["amount"] = int(amount * 100)

        refund = stripe.Refund.create(**params)
        return {"refund_id": refund.id, "status": refund.status}

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify Stripe webhook signature."""
        try:
            stripe.Webhook.construct_event(
                payload,
                signature,
                self._webhook_secret,
            )
            return True
        except stripe.error.SignatureVerificationError:
            return False

    def parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse Stripe webhook into normalized event."""
        event_type = payload.get("type", "")
        data = payload.get("data", {}).get("object", {})

        # Map Stripe events
        type_mapping = {
            "checkout.session.completed": "payment.completed",
            "checkout.session.expired": "payment.expired",
            "payment_intent.payment_failed": "payment.failed",
        }

        invoice_id = None
        metadata = data.get("metadata", {})
        if "invoice_id" in metadata:
            invoice_id = int(metadata["invoice_id"])

        return WebhookEvent(
            id=payload.get("id", ""),
            type=type_mapping.get(event_type, event_type),
            provider="stripe",
            invoice_id=invoice_id,
            payment_intent_id=data.get("payment_intent"),
            data=payload,
        )

    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get Stripe payment status."""
        intent = stripe.PaymentIntent.retrieve(payment_id)
        return self._map_status(intent.status)

    def _map_status(self, stripe_status: str) -> PaymentStatus:
        """Map Stripe status to normalized status."""
        mapping = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PROCESSING,
            "processing": PaymentStatus.PROCESSING,
            "succeeded": PaymentStatus.COMPLETED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return mapping.get(stripe_status, PaymentStatus.PENDING)


class StripePlugin(IPlugin):
    """
    Stripe payment plugin.

    Provides Stripe payment integration through the plugin system.
    """

    def __init__(self):
        self._adapter = StripeAdapter()
        self._config: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "stripe"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Stripe payment provider integration"

    @property
    def capabilities(self) -> List[str]:
        return ["payment", "checkout", "webhooks", "refunds"]

    @property
    def adapter(self) -> StripeAdapter:
        """Get the payment adapter."""
        return self._adapter

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with Stripe credentials."""
        self._config = config
        api_key = config.get("api_key", "")
        webhook_secret = config.get("webhook_secret", "")
        self._adapter.configure(api_key, webhook_secret)

    def activate(self) -> None:
        """Activate the plugin."""
        pass

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        pass
```

---

### 4.5 Manual Payment Plugin (Pay Invoice Later)

**File:** `python/api/tests/unit/plugins/test_manual_plugin.py`

```python
"""Tests for Manual Payment plugin."""
import pytest
from decimal import Decimal


class TestManualPaymentPlugin:
    """Test cases for ManualPaymentPlugin."""

    def test_plugin_properties(self):
        """ManualPaymentPlugin should have correct properties."""
        from src.plugins.payment import ManualPaymentPlugin

        plugin = ManualPaymentPlugin()

        assert plugin.name == "manual"
        assert "payment" in plugin.capabilities
        assert "invoice" in plugin.adapter.supported_payment_methods

    def test_create_invoice_session(self):
        """ManualPaymentPlugin should create invoice without redirect."""
        from src.plugins.payment import ManualPaymentPlugin

        plugin = ManualPaymentPlugin()
        plugin.initialize({})
        plugin.activate()

        session = plugin.adapter.create_checkout_session(
            amount=Decimal("99.00"),
            currency="EUR",
            invoice_id=1,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            payment_method="invoice",
        )

        # No redirect for invoice payment
        assert session.checkout_url is None or session.checkout_url == ""
        assert session.session_id.startswith("INV-")
```

**File:** `python/api/src/plugins/payment/manual_plugin.py`

```python
"""Manual payment plugin for invoice/pay-later flows."""
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from src.plugins import IPlugin
from src.payment import (
    IPaymentProviderAdapter,
    PaymentIntent,
    PaymentStatus,
    CheckoutSession,
    WebhookEvent,
)


class ManualPaymentAdapter(IPaymentProviderAdapter):
    """
    Manual payment adapter for invoice-based payments.

    Supports "pay later" flow where invoice is sent and
    payment is recorded manually when received.
    """

    @property
    def provider_name(self) -> str:
        return "manual"

    @property
    def supported_payment_methods(self) -> List[str]:
        return ["invoice", "bank_transfer"]

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        invoice_id: int,
        success_url: str,
        cancel_url: str,
        payment_method: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckoutSession:
        """
        Create invoice session (no redirect).

        For manual payments, no external checkout is needed.
        Invoice is sent directly to customer.
        """
        session_id = f"INV-{invoice_id}-{uuid.uuid4().hex[:8]}"

        return CheckoutSession(
            session_id=session_id,
            checkout_url="",  # No redirect
            provider="manual",
        )

    def capture_payment(self, payment_id: str) -> PaymentIntent:
        """
        Record manual payment capture.

        Called when admin confirms payment was received.
        """
        return PaymentIntent(
            id=payment_id,
            provider="manual",
            amount=Decimal("0"),  # Amount from invoice
            currency="EUR",
            status=PaymentStatus.COMPLETED,
        )

    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Record manual refund."""
        return {
            "refund_id": f"REF-{payment_id}",
            "status": "completed",
        }

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Manual payments don't use webhooks."""
        return True

    def parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse internal event (admin action)."""
        return WebhookEvent(
            id=payload.get("id", ""),
            type=payload.get("type", "payment.manual"),
            provider="manual",
            invoice_id=payload.get("invoice_id"),
            payment_intent_id=payload.get("payment_id"),
            data=payload,
        )

    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get payment status from invoice."""
        # Status comes from invoice record
        return PaymentStatus.PENDING


class ManualPaymentPlugin(IPlugin):
    """
    Manual payment plugin.

    Provides invoice-based and bank transfer payment support.
    Useful for B2B scenarios or pay-later flows.
    """

    def __init__(self):
        self._adapter = ManualPaymentAdapter()

    @property
    def name(self) -> str:
        return "manual"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Manual payment provider (invoice, bank transfer)"

    @property
    def capabilities(self) -> List[str]:
        return ["payment", "invoice"]

    @property
    def adapter(self) -> ManualPaymentAdapter:
        """Get the payment adapter."""
        return self._adapter

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin."""
        pass

    def activate(self) -> None:
        """Activate the plugin."""
        pass

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        pass
```

---

### 4.6 Event-Driven Architecture with EventDispatcher

**IMPORTANT**: Sprint 4 uses EventDispatcher with **sequential execution** (handlers execute one by one in registration order). This ensures predictable ordering and easier debugging for payment-critical events.

The payment system uses an event-driven architecture where services react to domain events through handlers.

**File:** `python/api/src/events/__init__.py`

```python
"""Event system exports."""
from .dispatcher import EventDispatcher
from .interfaces import DomainEvent, IEventHandler
from .payment_events import (
    PaymentCompletedEvent,
    PaymentFailedEvent,
    InvoiceCreatedEvent,
    SubscriptionActivatedEvent,
)

__all__ = [
    "EventDispatcher",
    "DomainEvent",
    "IEventHandler",
    "PaymentCompletedEvent",
    "PaymentFailedEvent",
    "InvoiceCreatedEvent",
    "SubscriptionActivatedEvent",
]
```

**File:** `python/api/src/events/interfaces.py`

```python
"""Event system interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Type
import uuid


@dataclass
class DomainEvent(ABC):
    """
    Base domain event.

    All domain events should inherit from this class.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    @abstractmethod
    def event_name(self) -> str:
        """Event name identifier."""
        pass


class IEventHandler(ABC):
    """
    Event handler interface.

    Handlers execute sequentially in registration order.
    """

    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """
        Handle the event synchronously.

        Args:
            event: The domain event to handle.
        """
        pass

    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the event.

        Args:
            event: The domain event to check.

        Returns:
            True if handler can process this event.
        """
        pass
```

**File:** `python/api/src/events/dispatcher.py`

```python
"""Event dispatcher with sequential execution."""
from typing import Dict, List, Type
from .interfaces import DomainEvent, IEventHandler
import logging

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Event dispatcher with sequential handler execution.

    Handlers execute one by one in registration order for
    predictable behavior and easier debugging.
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[IEventHandler]] = {}

    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: IEventHandler,
    ) -> None:
        """
        Subscribe handler to event type.

        Args:
            event_type: Domain event class
            handler: Event handler instance
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(
            f"Registered handler {handler.__class__.__name__} "
            f"for event {event_type.__name__}"
        )

    def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch event to all subscribed handlers sequentially.

        Handlers execute in registration order.
        If a handler raises an exception, execution stops.

        Args:
            event: Domain event to dispatch
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        logger.info(
            f"Dispatching {event_type.__name__} to {len(handlers)} handler(s)"
        )

        for handler in handlers:
            if handler.can_handle(event):
                try:
                    logger.debug(
                        f"Executing handler {handler.__class__.__name__}"
                    )
                    handler.handle(event)
                except Exception as e:
                    logger.error(
                        f"Handler {handler.__class__.__name__} failed: {e}",
                        exc_info=True,
                    )
                    # Stop on first failure for payment-critical events
                    raise

    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: IEventHandler,
    ) -> None:
        """Unsubscribe handler from event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def clear(self) -> None:
        """Clear all subscriptions (for testing)."""
        self._handlers.clear()
```

**File:** `python/api/src/events/payment_events.py`

```python
"""Payment-related events."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from .interfaces import IEvent


@dataclass
class PaymentCompletedEvent(IEvent):
    """Fired when payment is successfully completed."""
    invoice_id: int = 0
    user_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "EUR"
    provider: str = ""
    payment_ref: str = ""

    @property
    def event_type(self) -> str:
        return "payment.completed"


@dataclass
class PaymentFailedEvent(IEvent):
    """Fired when payment fails."""
    invoice_id: int = 0
    user_id: int = 0
    error: str = ""
    provider: str = ""

    @property
    def event_type(self) -> str:
        return "payment.failed"


@dataclass
class InvoiceCreatedEvent(IEvent):
    """Fired when invoice is created."""
    invoice_id: int = 0
    user_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "EUR"

    @property
    def event_type(self) -> str:
        return "invoice.created"


@dataclass
class SubscriptionActivatedEvent(IEvent):
    """Fired when subscription is activated."""
    subscription_id: int = 0
    user_id: int = 0
    tarif_plan_id: int = 0

    @property
    def event_type(self) -> str:
        return "subscription.activated"


@dataclass
class UserCreditsDepletedEvent(IEvent):
    """Fired when user runs out of credits."""
    user_id: int = 0
    remaining_credits: int = 0

    @property
    def event_type(self) -> str:
        return "user.credits_depleted"
```

**File:** `python/api/src/events/handlers/payment_handlers.py`

```python
"""Payment event handlers."""
from typing import List
from src.events import IEvent, IEventHandler, PaymentCompletedEvent
from src.services import InvoiceService, SubscriptionService, UserService


class PaymentCompletedHandler(IEventHandler):
    """
    Handles payment.completed events.

    Activates subscription and updates user status.
    """

    def __init__(
        self,
        invoice_service: InvoiceService,
        subscription_service: SubscriptionService,
        user_service: UserService,
        email_gateway=None,
    ):
        self._invoice_service = invoice_service
        self._subscription_service = subscription_service
        self._user_service = user_service
        self._email_gateway = email_gateway

    @property
    def handles(self) -> List[str]:
        return ["payment.completed"]

    async def handle(self, event: IEvent) -> None:
        """Handle payment completed event."""
        if not isinstance(event, PaymentCompletedEvent):
            return

        # Mark invoice as paid
        invoice = self._invoice_service.mark_paid(
            invoice_id=event.invoice_id,
            payment_ref=event.payment_ref,
            payment_method=event.provider,
        )

        # Activate subscription
        if invoice.subscription_id:
            self._subscription_service.activate_subscription(
                invoice.subscription_id
            )

        # Send confirmation email
        if self._email_gateway:
            user = self._user_service.get_user(event.user_id)
            await self._email_gateway.send_payment_confirmation(
                to_email=user.email,
                invoice_number=invoice.invoice_number,
                amount=event.amount,
                currency=event.currency,
            )


class UserCreditsDepletedHandler(IEventHandler):
    """
    Handles user.credits_depleted events.

    Sends notification and optionally suspends account.
    """

    def __init__(self, user_service: UserService, notification_service=None):
        self._user_service = user_service
        self._notification_service = notification_service

    @property
    def handles(self) -> List[str]:
        return ["user.credits_depleted"]

    async def handle(self, event: IEvent) -> None:
        """Handle credits depleted event."""
        # Send notification to user
        if self._notification_service:
            await self._notification_service.send(
                user_id=event.user_id,
                message="Your credits have been depleted. Please renew your subscription.",
            )
```

---

### 4.7 CheckoutOrchestrator (Provider-Agnostic)

**File:** `python/api/src/services/checkout_orchestrator.py`

```python
"""Checkout orchestration service (provider-agnostic)."""
from decimal import Decimal
from typing import Optional, Dict, Any
from src.plugins import PluginRegistry
from src.payment import (
    IPaymentProviderAdapter,
    IPaymentMethod,
    CheckoutSession,
    PaymentProviderRegistry,
)
from src.events import EventBus, InvoiceCreatedEvent


class CheckoutOrchestrator:
    """
    Provider-agnostic checkout orchestration.

    Coordinates invoice creation and payment session creation
    through the plugin system. Publishes events for downstream handlers.
    """

    def __init__(
        self,
        invoice_service: "IInvoiceService",
        subscription_service: "ISubscriptionService",
        payment_registry: PaymentProviderRegistry,
        event_bus: EventBus,
        base_url: str = "http://localhost:5000",
    ):
        self._invoice_service = invoice_service
        self._subscription_service = subscription_service
        self._payment_registry = payment_registry
        self._event_bus = event_bus
        self._base_url = base_url

    def create_checkout(
        self,
        user_id: int,
        tarif_plan_id: int,
        payment_method_type: str,
        provider_name: Optional[str] = None,
        country_code: Optional[str] = None,
        currency_code: str = "EUR",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckoutSession:
        """
        Create checkout session using plugin system.

        1. Resolves payment method and provider
        2. Creates inactive subscription
        3. Creates invoice with tax
        4. Publishes InvoiceCreatedEvent
        5. Creates payment session via provider adapter
        6. Returns checkout session
        """
        # Get payment method
        payment_method = self._payment_registry.get_payment_method(
            payment_method_type
        )
        if not payment_method:
            raise ValueError(f"Unknown payment method: {payment_method_type}")

        # Auto-select provider if not specified
        if not provider_name:
            compatible = payment_method.get_compatible_providers()
            if not compatible:
                raise ValueError(
                    f"No providers support {payment_method_type}"
                )
            provider_name = compatible[0]

        # Get provider adapter
        adapter = self._payment_registry.get_provider(provider_name)
        if not adapter:
            raise ValueError(f"Provider not registered: {provider_name}")

        # Validate provider supports method
        if payment_method_type not in adapter.supported_payment_methods:
            raise ValueError(
                f"Provider {provider_name} doesn't support {payment_method_type}"
            )

        # Create subscription (inactive)
        subscription = self._subscription_service.create_subscription(
            user_id=user_id,
            tarif_plan_id=tarif_plan_id,
        )

        # Create invoice
        invoice = self._invoice_service.create_invoice(
            user_id=user_id,
            tarif_plan_id=tarif_plan_id,
            subscription_id=subscription.id,
            country_code=country_code,
            currency_code=currency_code,
        )

        # Publish invoice created event
        self._event_bus.publish_sync(InvoiceCreatedEvent(
            invoice_id=invoice.id,
            user_id=user_id,
            amount=invoice.amount,
            currency=invoice.currency,
        ))

        # Create payment session
        success_url = f"{self._base_url}/api/v1/checkout/success"
        cancel_url = f"{self._base_url}/api/v1/checkout/cancel"

        session = adapter.create_checkout_session(
            amount=invoice.amount,
            currency=invoice.currency,
            invoice_id=invoice.id,
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method=payment_method_type,
            metadata=metadata,
        )

        return session

    def get_available_payment_methods(self) -> Dict[str, list]:
        """Get all available payment methods grouped by provider."""
        result = {}
        for provider_name, adapter in self._payment_registry.providers.items():
            result[provider_name] = adapter.supported_payment_methods
        return result
```

---

### 4.8 Payment Webhook Handler (Event-Driven)

**File:** `python/api/src/services/payment_webhook_handler.py`

```python
"""Payment webhook handler (event-driven)."""
from typing import Dict, Any
from src.plugins import PluginRegistry
from src.payment import PaymentProviderRegistry, WebhookEvent
from src.events import (
    EventBus,
    PaymentCompletedEvent,
    PaymentFailedEvent,
)


class PaymentWebhookHandler:
    """
    Provider-agnostic webhook handler.

    Converts provider webhooks to domain events.
    Event handlers process business logic.
    """

    def __init__(
        self,
        payment_registry: PaymentProviderRegistry,
        invoice_repo: "IInvoiceRepository",
        event_bus: EventBus,
    ):
        self._payment_registry = payment_registry
        self._invoice_repo = invoice_repo
        self._event_bus = event_bus

    def handle_webhook(
        self,
        provider_name: str,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Handle incoming webhook.

        1. Get provider adapter
        2. Verify signature
        3. Parse to normalized event
        4. Publish domain event
        """
        adapter = self._payment_registry.get_provider(provider_name)
        if not adapter:
            return False

        # Verify signature
        if not adapter.verify_webhook_signature(payload, signature):
            return False

        # Parse to provider-agnostic event
        payload_dict = self._parse_payload(payload)
        webhook_event = adapter.parse_webhook_event(payload_dict)

        # Convert to domain event and publish
        domain_event = self._to_domain_event(webhook_event)
        if domain_event:
            self._event_bus.publish_sync(domain_event)

        return True

    def _to_domain_event(self, webhook_event: WebhookEvent):
        """Convert webhook event to domain event."""
        if webhook_event.type == "payment.completed":
            invoice = self._invoice_repo.find_by_id(webhook_event.invoice_id)
            if not invoice:
                return None

            return PaymentCompletedEvent(
                invoice_id=webhook_event.invoice_id,
                user_id=invoice.user_id,
                amount=invoice.amount,
                currency=invoice.currency,
                provider=webhook_event.provider,
                payment_ref=webhook_event.payment_intent_id or "",
            )

        elif webhook_event.type == "payment.failed":
            invoice = self._invoice_repo.find_by_id(webhook_event.invoice_id)
            if not invoice:
                return None

            return PaymentFailedEvent(
                invoice_id=webhook_event.invoice_id,
                user_id=invoice.user_id,
                provider=webhook_event.provider,
                error=webhook_event.data.get("error", "Payment failed"),
            )

        return None

    def _parse_payload(self, payload: bytes) -> Dict[str, Any]:
        """Parse webhook payload bytes to dict."""
        import json
        return json.loads(payload.decode("utf-8"))
```

---

### 4.9 Payment Provider Registry

**File:** `python/api/src/payment/registry.py`

```python
"""Payment provider registry."""
from typing import Dict, Optional, List
from .interfaces import IPaymentProviderAdapter, IPaymentMethod


class PaymentProviderRegistry:
    """
    Registry for payment providers and methods.

    Central registry for provider adapters and payment methods.
    """

    def __init__(self):
        self._providers: Dict[str, IPaymentProviderAdapter] = {}
        self._methods: Dict[str, IPaymentMethod] = {}

    @property
    def providers(self) -> Dict[str, IPaymentProviderAdapter]:
        """Get all registered providers."""
        return self._providers.copy()

    def register_provider(self, adapter: IPaymentProviderAdapter) -> None:
        """Register a payment provider adapter."""
        self._providers[adapter.provider_name] = adapter

    def register_payment_method(self, method: IPaymentMethod) -> None:
        """Register a payment method."""
        self._methods[method.method_type] = method

    def get_provider(self, name: str) -> Optional[IPaymentProviderAdapter]:
        """Get provider adapter by name."""
        return self._providers.get(name)

    def get_payment_method(self, method_type: str) -> Optional[IPaymentMethod]:
        """Get payment method by type."""
        return self._methods.get(method_type)

    def get_providers_for_method(self, method_type: str) -> List[str]:
        """Get all providers that support a payment method."""
        method = self._methods.get(method_type)
        if not method:
            return []
        return [
            name for name, adapter in self._providers.items()
            if method_type in adapter.supported_payment_methods
        ]
```

---

### 4.5 Checkout Routes

**File:** `python/api/src/routes/checkout.py`

```python
"""Checkout routes."""
from flask import Blueprint, request, jsonify, g, redirect
from dependency_injector.wiring import inject, Provide
from marshmallow import Schema, fields, validate, ValidationError
from src.container import Container
from src.middleware.auth import require_auth

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


class CreateCheckoutSchema(Schema):
    """Schema for checkout creation request."""
    tarif_plan_id = fields.Int(required=True)
    payment_method = fields.Str(
        required=True,
        validate=validate.OneOf(["paypal", "stripe"]),
    )
    country_code = fields.Str(validate=validate.Length(equal=2))
    currency_code = fields.Str(validate=validate.Length(equal=3))


create_schema = CreateCheckoutSchema()


@checkout_bp.route("/create", methods=["POST"])
@require_auth
@inject
def create_checkout(
    payment_service=Provide[Container.payment_service],
):
    """
    Create checkout session.

    POST /api/v1/checkout/create
    Authorization: Bearer <token>
    {
        "tarif_plan_id": 1,
        "payment_method": "stripe",
        "country_code": "DE",
        "currency_code": "EUR"
    }
    """
    try:
        data = create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    try:
        session = payment_service.create_checkout(
            user_id=g.user_id,
            tarif_plan_id=data["tarif_plan_id"],
            payment_method=data["payment_method"],
            country_code=data.get("country_code"),
            currency_code=data.get("currency_code", "EUR"),
        )

        return jsonify({
            "checkout_url": session.checkout_url,
            "session_id": session.session_id,
            "invoice_id": session.invoice_id,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@checkout_bp.route("/success", methods=["GET"])
def checkout_success():
    """
    Payment success callback.

    GET /api/v1/checkout/success?session_id=xxx
    """
    # In production, verify the session and show success page
    return jsonify({
        "status": "success",
        "message": "Payment completed successfully",
    }), 200


@checkout_bp.route("/cancel", methods=["GET"])
def checkout_cancel():
    """
    Payment cancelled callback.

    GET /api/v1/checkout/cancel
    """
    return jsonify({
        "status": "cancelled",
        "message": "Payment was cancelled",
    }), 200


@checkout_bp.route("/confirm", methods=["POST"])
@require_auth
@inject
def confirm_payment(
    payment_service=Provide[Container.payment_service],
):
    """
    Confirm payment status.

    POST /api/v1/checkout/confirm
    {
        "invoice_id": 123
    }
    """
    invoice_id = request.json.get("invoice_id")
    if not invoice_id:
        return jsonify({"error": "invoice_id required"}), 400

    is_paid = payment_service.verify_payment(invoice_id)

    return jsonify({
        "paid": is_paid,
    }), 200
```

---

### 4.6 Invoice Routes

**File:** `python/api/src/routes/invoices.py`

```python
"""Invoice routes."""
from flask import Blueprint, jsonify, g
from dependency_injector.wiring import inject, Provide
from src.container import Container
from src.middleware.auth import require_auth

invoices_bp = Blueprint("invoices", __name__, url_prefix="/user/invoices")


@invoices_bp.route("", methods=["GET"])
@require_auth
@inject
def list_invoices(
    invoice_service=Provide[Container.invoice_service],
):
    """
    List user's invoices.

    GET /api/v1/user/invoices
    Authorization: Bearer <token>
    """
    invoices = invoice_service.get_user_invoices(g.user_id)

    return jsonify({
        "invoices": [inv.to_dict() for inv in invoices],
    }), 200


@invoices_bp.route("/<invoice_number>", methods=["GET"])
@require_auth
@inject
def get_invoice(
    invoice_number: str,
    invoice_service=Provide[Container.invoice_service],
):
    """
    Get single invoice by number.

    GET /api/v1/user/invoices/INV-20231201-ABC123
    Authorization: Bearer <token>
    """
    invoice = invoice_service.get_invoice_by_number(invoice_number)

    if not invoice or invoice.user_id != g.user_id:
        return jsonify({"error": "Invoice not found"}), 404

    return jsonify(invoice.to_dict()), 200
```

---

## Verification Checklist

```bash
# Run plugin system tests
docker-compose run --rm python pytest tests/unit/plugins/ -v

# Run payment adapter tests
docker-compose run --rm python pytest tests/unit/payment/ -v

# Run invoice service tests
docker-compose run --rm python pytest tests/unit/services/test_invoice_service.py -v

# Run event handler tests
docker-compose run --rm python pytest tests/unit/events/ -v

# Test checkout flow (with mock providers in test env)
docker-compose run --rm python pytest tests/integration/test_checkout_flow.py -v
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Plugin System | [ ] | IPlugin, PluginManager, PluginRegistry |
| Payment Interfaces | [ ] | IPaymentProviderAdapter, IPaymentMethod |
| Payment Methods | [ ] | CardPayment, InvoicePayment, WalletPayment |
| StripePlugin | [ ] | Full Stripe integration |
| ManualPaymentPlugin | [ ] | Invoice/pay-later support |
| PaymentProviderRegistry | [ ] | Provider lookup |
| InvoiceService | [ ] | With tax breakdown |
| CheckoutOrchestrator | [ ] | Provider-agnostic checkout |
| PaymentWebhookHandler | [ ] | Event-driven webhook processing |
| Event System | [ ] | EventBus, IEvent, IEventHandler |
| Payment Events | [ ] | PaymentCompleted, PaymentFailed, etc. |
| Event Handlers | [ ] | PaymentCompletedHandler, etc. |
| Checkout routes | [ ] | /create, /confirm |
| Invoice routes | [ ] | List, get |

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     Event-Driven Flow                             │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  Webhook Route  │
                    └────────┬────────┘
                             │ (raw payload)
                             ▼
                    ┌─────────────────┐
                    │ WebhookHandler  │
                    └────────┬────────┘
                             │ (verify, parse)
                             ▼
              ┌──────────────────────────────┐
              │   PaymentCompletedEvent      │
              │   PaymentFailedEvent         │
              └──────────────┬───────────────┘
                             │ (publish)
                             ▼
                    ┌─────────────────┐
                    │    EventBus     │
                    └────────┬────────┘
                             │ (dispatch)
                    ┌────────┼────────┐
                    ▼        ▼        ▼
            ┌───────────┐ ┌───────┐ ┌───────────┐
            │ Invoice   │ │ Sub   │ │  Email    │
            │ Handler   │ │Handler│ │  Handler  │
            └───────────┘ └───────┘ └───────────┘
                    │        │            │
                    ▼        ▼            ▼
            ┌───────────┐ ┌───────┐ ┌───────────┐
            │ Invoice   │ │ Sub   │ │  Email    │
            │ Service   │ │Service│ │  Gateway  │
            └───────────┘ └───────┘ └───────────┘
```

---

## Next Sprint

[Sprint 5: Admin & Webhooks](./sprint-5-admin-webhooks.md) - Admin API and background jobs.
