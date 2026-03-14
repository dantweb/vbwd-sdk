# Plugin System Architecture

**General-Purpose Plugin Framework for Extensible Components**

---

## Overview

The plugin system provides a unified framework for extending the platform with modular components. Any system feature can be implemented as a plugin, enabling:

- Modular, decoupled architecture
- Easy addition of new functionality
- Third-party integrations without core changes
- Feature flags and gradual rollouts
- Testing with mock implementations

---

## Plugin System Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION CORE                              │
│                    (Flask App, DI Container)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    PLUGIN MANAGER                               │ │
│  │            (Discovery, Loading, Lifecycle)                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    PLUGIN REGISTRY                              │ │
│  │          (Registration, Lookup, Dependencies)                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│         ┌──────────────────────┼──────────────────────┐             │
│         ▼                      ▼                      ▼             │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       │
│  │  COMPONENT  │       │  COMPONENT  │       │  COMPONENT  │       │
│  │   Payment   │       │   Email     │       │  Analytics  │       │
│  │   Plugins   │       │   Plugins   │       │   Plugins   │       │
│  └─────────────┘       └─────────────┘       └─────────────┘       │
│         │                      │                      │             │
│         ▼                      ▼                      ▼             │
│  ┌───────────┐         ┌───────────┐         ┌───────────┐         │
│  │ Stripe    │         │ SendGrid  │         │ Mixpanel  │         │
│  │ PayPal    │         │ Mailgun   │         │ Segment   │         │
│  │ Manual    │         │ SMTP      │         │ Internal  │         │
│  └───────────┘         └───────────┘         └───────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Plugin Interface

```python
"""Base plugin interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class PluginState(Enum):
    """Plugin lifecycle states."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class IPlugin(ABC):
    """
    Base interface for all plugins.

    All plugins must implement this interface.
    Component-specific plugins extend this with additional methods.
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
    def component(self) -> str:
        """Component this plugin belongs to (payment, email, etc.)."""
        pass

    @property
    def dependencies(self) -> List[str]:
        """List of plugin names this plugin depends on."""
        return []

    @property
    def priority(self) -> int:
        """Loading priority (higher = loaded first)."""
        return 0

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        Called once when plugin is loaded.

        Args:
            config: Plugin-specific configuration
        """
        pass

    @abstractmethod
    def activate(self) -> None:
        """
        Activate plugin.

        Called when plugin should start handling requests.
        """
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """
        Deactivate plugin.

        Called when plugin should stop handling requests.
        Cleanup resources here.
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        Check plugin health.

        Returns:
            Health status with details
        """
        return {"status": "healthy"}
```

### Plugin Metadata

```python
"""Plugin metadata for discovery."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PluginMetadata:
    """
    Plugin metadata for registration and discovery.

    Can be defined in plugin class or plugin.yaml file.
    """

    name: str
    version: str
    component: str
    description: str = ""
    author: str = ""
    homepage: str = ""

    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)

    # Capabilities
    provides: List[str] = field(default_factory=list)  # What this plugin provides
    requires: List[str] = field(default_factory=list)  # What it requires from others

    # Configuration schema
    config_schema: Dict[str, Any] = field(default_factory=dict)

    # Feature flags
    experimental: bool = False
    deprecated: bool = False


# Example metadata
STRIPE_PLUGIN_METADATA = PluginMetadata(
    name="stripe",
    version="1.0.0",
    component="payment",
    description="Stripe payment provider integration",
    author="VBWD Team",
    provides=["payment.card", "payment.wallet"],
    config_schema={
        "api_key": {"type": "string", "required": True, "secret": True},
        "webhook_secret": {"type": "string", "required": True, "secret": True},
        "sandbox": {"type": "boolean", "default": False},
    },
)
```

### Plugin Manager

```python
"""Plugin manager for lifecycle management."""
from typing import Dict, List, Optional, Type
from pathlib import Path
import importlib
import yaml


class PluginManager:
    """
    Manages plugin lifecycle.

    - Discovery: Finds plugins in configured paths
    - Loading: Imports and instantiates plugins
    - Initialization: Configures plugins
    - Activation: Enables plugins for use
    - Deactivation: Disables plugins cleanly
    """

    def __init__(self, app_config: dict):
        self._config = app_config
        self._plugins: Dict[str, IPlugin] = {}
        self._states: Dict[str, PluginState] = {}
        self._registry = PluginRegistry()

    def discover_plugins(self, paths: List[str]) -> List[PluginMetadata]:
        """
        Discover plugins in given paths.

        Looks for:
        - Python packages with plugin.yaml
        - Python modules with PLUGIN_METADATA
        """
        discovered = []

        for path in paths:
            plugin_path = Path(path)
            if not plugin_path.exists():
                continue

            # Check for plugin.yaml
            yaml_path = plugin_path / "plugin.yaml"
            if yaml_path.exists():
                with open(yaml_path) as f:
                    meta_dict = yaml.safe_load(f)
                    discovered.append(PluginMetadata(**meta_dict))
                continue

            # Check for Python module with metadata
            init_path = plugin_path / "__init__.py"
            if init_path.exists():
                module = importlib.import_module(path.replace("/", "."))
                if hasattr(module, "PLUGIN_METADATA"):
                    discovered.append(module.PLUGIN_METADATA)

        return discovered

    def load_plugin(self, name: str, plugin_class: Type[IPlugin]) -> None:
        """Load a plugin class."""
        if name in self._plugins:
            raise ValueError(f"Plugin already loaded: {name}")

        plugin = plugin_class()
        self._plugins[name] = plugin
        self._states[name] = PluginState.LOADED
        self._registry.register(plugin)

    def initialize_plugin(self, name: str) -> None:
        """Initialize a loaded plugin."""
        if name not in self._plugins:
            raise ValueError(f"Plugin not loaded: {name}")

        plugin = self._plugins[name]
        config = self._config.get("plugins", {}).get(name, {})

        # Check dependencies
        for dep in plugin.dependencies:
            if dep not in self._plugins:
                raise ValueError(f"Missing dependency: {dep}")
            if self._states[dep] != PluginState.INITIALIZED:
                self.initialize_plugin(dep)

        plugin.initialize(config)
        self._states[name] = PluginState.INITIALIZED

    def activate_plugin(self, name: str) -> None:
        """Activate an initialized plugin."""
        if self._states.get(name) != PluginState.INITIALIZED:
            self.initialize_plugin(name)

        self._plugins[name].activate()
        self._states[name] = PluginState.ACTIVE

    def deactivate_plugin(self, name: str) -> None:
        """Deactivate an active plugin."""
        if self._states.get(name) != PluginState.ACTIVE:
            return

        self._plugins[name].deactivate()
        self._states[name] = PluginState.DISABLED

    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_plugins_by_component(self, component: str) -> List[IPlugin]:
        """Get all plugins for a component."""
        return [
            p for p in self._plugins.values()
            if p.component == component and self._states[p.name] == PluginState.ACTIVE
        ]

    def load_all(self) -> None:
        """Load and activate all configured plugins."""
        plugin_configs = self._config.get("plugins", {})

        for name, config in plugin_configs.items():
            if config.get("enabled", True):
                self.activate_plugin(name)

    def health_check(self) -> Dict[str, Any]:
        """Check health of all plugins."""
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = {
                    "state": self._states[name].value,
                    "health": plugin.health_check(),
                }
            except Exception as e:
                results[name] = {
                    "state": PluginState.ERROR.value,
                    "error": str(e),
                }
        return results
```

### Plugin Registry

```python
"""Plugin registry for lookup and dependencies."""
from typing import Dict, List, Optional, Callable, Any


class PluginRegistry:
    """
    Registry for plugin lookup and capability matching.

    Provides:
    - Name-based lookup
    - Component-based lookup
    - Capability-based lookup
    - Hook registration
    """

    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._by_component: Dict[str, List[IPlugin]] = {}
        self._by_capability: Dict[str, List[IPlugin]] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, plugin: IPlugin) -> None:
        """Register a plugin."""
        self._plugins[plugin.name] = plugin

        # Index by component
        if plugin.component not in self._by_component:
            self._by_component[plugin.component] = []
        self._by_component[plugin.component].append(plugin)

        # Index by capabilities (from metadata)
        if hasattr(plugin, "metadata"):
            for capability in plugin.metadata.provides:
                if capability not in self._by_capability:
                    self._by_capability[capability] = []
                self._by_capability[capability].append(plugin)

    def get(self, name: str) -> Optional[IPlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_by_component(self, component: str) -> List[IPlugin]:
        """Get all plugins for a component."""
        return self._by_component.get(component, [])

    def get_by_capability(self, capability: str) -> List[IPlugin]:
        """Get plugins that provide a capability."""
        return self._by_capability.get(capability, [])

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a callback for a hook."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger all callbacks for a hook."""
        results = []
        for callback in self._hooks.get(hook_name, []):
            results.append(callback(*args, **kwargs))
        return results
```

---

## Component Architecture

Components are logical groupings of related plugins with shared interfaces.

### Component Interface

```python
"""Component base class."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IComponent(ABC):
    """
    Base interface for components.

    Components group related plugins and provide
    a unified API for the application.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Component name."""
        pass

    @property
    @abstractmethod
    def plugin_interface(self) -> type:
        """Interface that plugins must implement."""
        pass

    @abstractmethod
    def get_default_plugin(self) -> str:
        """Get default plugin name for this component."""
        pass

    @abstractmethod
    def select_plugin(self, context: Dict[str, Any]) -> str:
        """
        Select best plugin for given context.

        Args:
            context: Request context (country, currency, etc.)

        Returns:
            Plugin name to use
        """
        pass
```

### Available Components

| Component | Purpose | Plugin Interface |
|-----------|---------|------------------|
| `payment` | Payment processing | `IPaymentProviderAdapter` |
| `email` | Email delivery | `IEmailProviderAdapter` |
| `storage` | File storage | `IStorageProviderAdapter` |
| `analytics` | Event tracking | `IAnalyticsProviderAdapter` |
| `notification` | Push notifications | `INotificationProviderAdapter` |
| `auth` | External auth providers | `IAuthProviderAdapter` |

---

## Payment Component

Payment is implemented as a component with the plugin system.

### Payment Component Class

```python
"""Payment component implementation."""
from typing import Dict, Any, List
from src.plugins.base import IComponent
from src.payment.interfaces import IPaymentProviderAdapter


class PaymentComponent(IComponent):
    """
    Payment processing component.

    Manages payment provider plugins and routes
    requests to appropriate providers.
    """

    def __init__(self, plugin_manager: PluginManager, config: dict):
        self._plugin_manager = plugin_manager
        self._config = config
        self._method_providers = config.get("method_providers", {})
        self._default_provider = config.get("default_provider", "stripe")

    @property
    def name(self) -> str:
        return "payment"

    @property
    def plugin_interface(self) -> type:
        return IPaymentProviderAdapter

    def get_default_plugin(self) -> str:
        return self._default_provider

    def select_plugin(self, context: Dict[str, Any]) -> str:
        """
        Select payment provider based on context.

        Selection criteria:
        1. Explicit provider in context
        2. Provider for payment method
        3. Provider for country/currency
        4. Default provider
        """
        # Explicit provider
        if "provider" in context:
            return context["provider"]

        # Payment method preference
        method = context.get("payment_method")
        if method and method in self._method_providers:
            return self._method_providers[method]

        # Country/currency routing
        country = context.get("country")
        currency = context.get("currency")
        if country and currency:
            routing = self._config.get("routing", {})
            route_key = f"{country}_{currency}"
            if route_key in routing:
                return routing[route_key]

        return self._default_provider

    def get_provider(self, name: str) -> IPaymentProviderAdapter:
        """Get payment provider plugin."""
        plugin = self._plugin_manager.get_plugin(name)
        if not plugin or not isinstance(plugin, IPaymentProviderAdapter):
            raise ValueError(f"Payment provider not found: {name}")
        return plugin

    def get_providers_for_method(
        self,
        method: str,
        currency: str,
        country: str,
    ) -> List[IPaymentProviderAdapter]:
        """Get all providers that support a payment method."""
        providers = []
        for plugin in self._plugin_manager.get_plugins_by_component("payment"):
            if isinstance(plugin, IPaymentProviderAdapter):
                if method in plugin.supported_payment_methods:
                    providers.append(plugin)
        return providers
```

### Payment Plugin Base

```python
"""Base class for payment plugins."""
from abc import abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal
from src.plugins.base import IPlugin, PluginMetadata
from src.payment.interfaces import (
    IPaymentProviderAdapter,
    PaymentIntent,
    CheckoutSession,
    WebhookEvent,
    RefundResult,
    PaymentStatus,
)


class PaymentPlugin(IPlugin, IPaymentProviderAdapter):
    """
    Base class for payment provider plugins.

    Combines IPlugin lifecycle with IPaymentProviderAdapter functionality.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._client = None  # SDK client

    @property
    def component(self) -> str:
        return "payment"

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        pass

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with configuration."""
        self._config = config
        self._validate_config()
        self._init_client()

    def _validate_config(self) -> None:
        """Validate configuration against schema."""
        schema = self.metadata.config_schema
        for key, spec in schema.items():
            if spec.get("required") and key not in self._config:
                raise ValueError(f"Missing required config: {key}")

    @abstractmethod
    def _init_client(self) -> None:
        """Initialize SDK client. Implement in subclass."""
        pass

    def activate(self) -> None:
        """Activate plugin."""
        pass  # Default: no-op

    def deactivate(self) -> None:
        """Deactivate plugin."""
        self._client = None
```

---

## Example Plugins

### Stripe Payment Plugin

```python
"""Stripe payment plugin."""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from src.payment.plugins.base import PaymentPlugin, PluginMetadata
from src.payment.interfaces import (
    PaymentIntent,
    CheckoutSession,
    WebhookEvent,
    RefundResult,
    PaymentStatus,
)
from src.payment.sdk.stripe_sdk import StripeSDKClient


METADATA = PluginMetadata(
    name="stripe",
    version="1.0.0",
    component="payment",
    description="Stripe payment provider",
    provides=["payment.card", "payment.wallet", "payment.sepa"],
    config_schema={
        "api_key": {"type": "string", "required": True, "secret": True},
        "webhook_secret": {"type": "string", "required": True, "secret": True},
    },
)


class StripePlugin(PaymentPlugin):
    """
    Stripe payment provider plugin.

    Supports:
    - Card payments
    - Wallet payments (Apple Pay, Google Pay)
    - SEPA Direct Debit
    """

    @property
    def metadata(self) -> PluginMetadata:
        return METADATA

    @property
    def provider_name(self) -> str:
        return "stripe"

    @property
    def supported_payment_methods(self) -> List[str]:
        return ["card", "wallet", "sepa"]

    @property
    def supports_webhooks(self) -> bool:
        return True

    def _init_client(self) -> None:
        self._client = StripeSDKClient(
            api_key=self._config["api_key"],
        )

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: dict,
    ) -> PaymentIntent:
        """Create Stripe PaymentIntent."""
        result = self._client.create_payment_intent(
            amount=int(amount * 100),  # Stripe uses cents
            currency=currency.lower(),
            metadata=metadata,
        )

        return PaymentIntent(
            id=f"stripe_{result['id']}",
            provider="stripe",
            provider_reference=result["id"],
            amount=amount,
            currency=currency,
            status=self._map_status(result["status"]),
            metadata=metadata,
        )

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
        line_items: Optional[List[dict]] = None,
    ) -> CheckoutSession:
        """Create Stripe Checkout Session."""
        result = self._client.create_checkout_session(
            amount=int(amount * 100),
            currency=currency.lower(),
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )

        return CheckoutSession(
            id=f"stripe_{result['id']}",
            provider="stripe",
            checkout_url=result["url"],
            expires_at=None,
            metadata=metadata,
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """Verify Stripe webhook signature."""
        return self._client.verify_webhook(
            payload=payload,
            signature=signature,
            secret=self._config["webhook_secret"],
        )

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """Parse Stripe webhook to normalized event."""
        event_type = payload.get("type", "")
        data = payload.get("data", {}).get("object", {})

        type_mapping = {
            "checkout.session.completed": "checkout.completed",
            "checkout.session.expired": "checkout.expired",
            "payment_intent.succeeded": "payment.captured",
            "payment_intent.payment_failed": "payment.failed",
            "charge.refunded": "payment.refunded",
        }

        return WebhookEvent(
            id=payload.get("id"),
            type=type_mapping.get(event_type, event_type),
            provider="stripe",
            payment_intent_id=data.get("payment_intent"),
            invoice_id=int(data.get("metadata", {}).get("invoice_id", 0)) or None,
            data=data,
            raw_payload=payload,
        )

    def _map_status(self, stripe_status: str) -> PaymentStatus:
        """Map Stripe status to PaymentStatus."""
        mapping = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "processing": PaymentStatus.PENDING,
            "succeeded": PaymentStatus.CAPTURED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return mapping.get(stripe_status, PaymentStatus.PENDING)

    # ... implement remaining IPaymentProviderAdapter methods ...
```

### Manual Invoice Plugin

```python
"""Manual/Invoice payment plugin."""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from src.payment.plugins.base import PaymentPlugin, PluginMetadata
from src.payment.interfaces import (
    PaymentIntent,
    CheckoutSession,
    WebhookEvent,
    RefundResult,
    PaymentStatus,
)


METADATA = PluginMetadata(
    name="manual",
    version="1.0.0",
    component="payment",
    description="Manual/Invoice payment (pay later)",
    provides=["payment.invoice", "payment.bank_transfer"],
    config_schema={
        "invoice_due_days": {"type": "integer", "default": 14},
        "bank_details": {"type": "object", "required": False},
    },
)


class ManualPaymentPlugin(PaymentPlugin):
    """
    Manual payment plugin for invoice/pay-later flows.

    No external provider - payments marked manually by admin.
    Used for:
    - Pay by invoice
    - Bank transfer
    - Manual payments
    """

    @property
    def metadata(self) -> PluginMetadata:
        return METADATA

    @property
    def provider_name(self) -> str:
        return "manual"

    @property
    def supported_payment_methods(self) -> List[str]:
        return ["invoice", "bank_transfer"]

    @property
    def supports_webhooks(self) -> bool:
        return False  # No external webhooks

    def _init_client(self) -> None:
        # No external client needed
        pass

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: dict,
    ) -> PaymentIntent:
        """Create manual payment intent."""
        intent_id = str(uuid.uuid4())
        due_days = self._config.get("invoice_due_days", 14)

        return PaymentIntent(
            id=f"manual_{intent_id}",
            provider="manual",
            provider_reference=intent_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            metadata={
                **metadata,
                "due_date": (datetime.utcnow() + timedelta(days=due_days)).isoformat(),
                "bank_details": self._config.get("bank_details"),
            },
        )

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
        Create 'checkout' for manual payment.

        Returns a URL to invoice display page (not external provider).
        """
        session_id = str(uuid.uuid4())

        # URL to internal invoice page
        invoice_url = f"/invoice/{metadata.get('invoice_id')}?session={session_id}"

        return CheckoutSession(
            id=f"manual_{session_id}",
            provider="manual",
            checkout_url=invoice_url,
            expires_at=datetime.utcnow() + timedelta(
                days=self._config.get("invoice_due_days", 14)
            ),
            metadata=metadata,
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """Manual plugin doesn't use webhooks."""
        return False

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """Manual plugin doesn't receive webhooks."""
        raise NotImplementedError("Manual plugin doesn't support webhooks")

    def get_payment_status(self, payment_intent_id: str) -> PaymentIntent:
        """
        Get payment status.

        For manual payments, status is tracked in database.
        This would query the invoice status.
        """
        # In real implementation, query invoice from database
        raise NotImplementedError("Query invoice status from database")

    def capture_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentIntent:
        """Manual payments don't need capture."""
        raise NotImplementedError("Manual payments are captured via admin")

    def cancel_payment(self, payment_intent_id: str) -> PaymentIntent:
        """Cancel manual payment."""
        # Update invoice status to cancelled
        raise NotImplementedError("Cancel via admin interface")

    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> RefundResult:
        """Manual refunds handled externally."""
        raise NotImplementedError("Manual refunds processed externally")

    def health_check(self) -> Dict[str, Any]:
        """Manual plugin is always healthy."""
        return {
            "status": "healthy",
            "message": "Manual payment plugin active",
        }
```

---

## Configuration

### Plugin Configuration

```yaml
# config/plugins.yaml

plugins:
  # Payment plugins
  stripe:
    enabled: true
    api_key: ${STRIPE_API_KEY}
    webhook_secret: ${STRIPE_WEBHOOK_SECRET}

  paypal:
    enabled: true
    client_id: ${PAYPAL_CLIENT_ID}
    client_secret: ${PAYPAL_CLIENT_SECRET}
    sandbox: true

  manual:
    enabled: true
    invoice_due_days: 14
    bank_details:
      bank_name: "Example Bank"
      iban: "DE89 3704 0044 0532 0130 00"
      bic: "COBADEFFXXX"

  klarna:
    enabled: false  # Enable when needed

  # Email plugins
  sendgrid:
    enabled: true
    api_key: ${SENDGRID_API_KEY}

  # Analytics plugins
  mixpanel:
    enabled: false

# Component configuration
components:
  payment:
    default_provider: stripe
    method_providers:
      card: stripe
      invoice: manual
      wallet: paypal
    routing:
      DE_EUR: stripe
      US_USD: stripe
```

---

## Directory Structure

```
python/api/src/
├── plugins/                    # Plugin framework
│   ├── __init__.py
│   ├── base.py                 # IPlugin, PluginMetadata
│   ├── manager.py              # PluginManager
│   ├── registry.py             # PluginRegistry
│   └── component.py            # IComponent base
│
├── components/                 # Component implementations
│   ├── __init__.py
│   ├── payment/                # Payment component
│   │   ├── __init__.py
│   │   ├── component.py        # PaymentComponent
│   │   ├── interfaces.py       # IPaymentProviderAdapter
│   │   ├── types.py            # PaymentIntent, etc.
│   │   ├── methods/            # Payment methods
│   │   │   ├── card.py
│   │   │   ├── invoice.py
│   │   │   └── bnpl.py
│   │   └── plugins/            # Payment plugins
│   │       ├── base.py
│   │       ├── stripe/
│   │       ├── paypal/
│   │       └── manual/
│   │
│   ├── email/                  # Email component
│   │   ├── component.py
│   │   └── plugins/
│   │       ├── sendgrid/
│   │       └── smtp/
│   │
│   └── analytics/              # Analytics component
│       ├── component.py
│       └── plugins/
│           └── mixpanel/
```

---

## Summary

The plugin system provides:

1. **General Framework** - Any feature can be a plugin
2. **Component Abstraction** - Logical grouping with shared interfaces
3. **Lifecycle Management** - Load, initialize, activate, deactivate
4. **Dependency Resolution** - Plugins can depend on others
5. **Capability Discovery** - Find plugins by what they provide
6. **Configuration Driven** - Enable/disable via config
7. **Health Monitoring** - Built-in health checks

Payment is just one component built on this framework, demonstrating how to build provider-agnostic systems with pluggable backends.
