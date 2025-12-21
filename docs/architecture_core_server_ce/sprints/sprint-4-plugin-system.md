# Sprint 4: Plugin System & Event Architecture

**Status:** 📋 Planned
**Duration:** ~3 hours
**Dependencies:** Sprint 3 (Subscriptions)

---

## Overview

Implement a flexible plugin system that allows extending the platform with payment providers, notification services, and custom business logic without modifying core code.

---

## Objectives

1. **Plugin Base Architecture**
   - Abstract base classes for plugins
   - Plugin metadata and versioning
   - Lifecycle hooks (init, enable, disable, uninstall)

2. **Plugin Manager**
   - Plugin discovery and registration
   - Dependency resolution
   - Enable/disable plugins dynamically
   - Plugin state persistence

3. **Event System**
   - Event dispatcher with plugin hooks
   - Event listeners and handlers
   - Priority-based execution
   - Event data serialization

4. **Payment Provider Plugin Interface**
   - Abstract payment provider base class
   - Stripe plugin implementation
   - PayPal plugin implementation (basic)
   - Webhook handling

5. **Plugin Configuration**
   - Per-plugin settings storage
   - Encrypted credential management
   - Configuration validation

---

## Architecture

### Plugin Lifecycle

```
DISCOVERED → REGISTERED → INITIALIZED → ENABLED → ACTIVE
                                            ↓
                                        DISABLED → UNINSTALLED
```

### Event Flow

```
Event Triggered → Event Dispatcher → Plugin Listeners (by priority) → Core Handlers
```

---

## Implementation Plan

### 4.1 Plugin Base Classes

**File:** `python/api/src/plugins/base.py`

```python
"""Plugin base classes and interfaces."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from uuid import UUID
from dataclasses import dataclass


class PluginStatus(Enum):
    """Plugin status."""
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BasePlugin(ABC):
    """
    Base class for all plugins.

    Plugins must inherit from this class and implement required methods.
    """

    def __init__(self):
        self._status = PluginStatus.DISCOVERED
        self._config: Dict[str, Any] = {}

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @property
    def status(self) -> PluginStatus:
        """Get plugin status."""
        return self._status

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize plugin with configuration.

        Args:
            config: Optional configuration dictionary
        """
        if config:
            self._config = config
        self._status = PluginStatus.INITIALIZED

    def enable(self) -> None:
        """Enable the plugin."""
        if self._status != PluginStatus.INITIALIZED:
            raise ValueError(f"Cannot enable plugin in {self._status} state")
        self.on_enable()
        self._status = PluginStatus.ENABLED

    def disable(self) -> None:
        """Disable the plugin."""
        if self._status != PluginStatus.ENABLED:
            raise ValueError(f"Cannot disable plugin in {self._status} state")
        self.on_disable()
        self._status = PluginStatus.DISABLED

    def on_enable(self) -> None:
        """Hook called when plugin is enabled."""
        pass

    def on_disable(self) -> None:
        """Hook called when plugin is disabled."""
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
```

---

### 4.2 Event System

**File:** `python/api/src/events/dispatcher.py`

```python
"""Event dispatcher for plugin system."""
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class EventPriority(Enum):
    """Event listener priority."""
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


@dataclass
class Event:
    """Base event class."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    propagation_stopped: bool = False

    def stop_propagation(self) -> None:
        """Stop event propagation to remaining listeners."""
        self.propagation_stopped = True


@dataclass
class EventListener:
    """Event listener registration."""
    callback: Callable[[Event], None]
    priority: EventPriority = EventPriority.NORMAL

    def __lt__(self, other):
        """Compare by priority for sorting."""
        return self.priority.value < other.priority.value


class EventDispatcher:
    """
    Event dispatcher for plugin system.

    Allows plugins to listen to and emit events.
    """

    def __init__(self):
        self._listeners: Dict[str, List[EventListener]] = {}

    def add_listener(
        self,
        event_name: str,
        callback: Callable[[Event], None],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Register event listener.

        Args:
            event_name: Name of event to listen for
            callback: Callback function to invoke
            priority: Listener priority (higher = earlier execution)
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []

        listener = EventListener(callback=callback, priority=priority)
        self._listeners[event_name].append(listener)

        # Sort by priority
        self._listeners[event_name].sort()

    def remove_listener(
        self,
        event_name: str,
        callback: Callable[[Event], None],
    ) -> None:
        """Remove event listener."""
        if event_name not in self._listeners:
            return

        self._listeners[event_name] = [
            listener for listener in self._listeners[event_name]
            if listener.callback != callback
        ]

    def dispatch(self, event: Event) -> Event:
        """
        Dispatch event to all registered listeners.

        Args:
            event: Event to dispatch

        Returns:
            The event (possibly modified by listeners)
        """
        if event.name not in self._listeners:
            return event

        for listener in self._listeners[event.name]:
            if event.propagation_stopped:
                break

            try:
                listener.callback(event)
            except Exception as e:
                # Log error but continue to other listeners
                print(f"Error in event listener: {e}")

        return event

    def has_listeners(self, event_name: str) -> bool:
        """Check if event has any listeners."""
        return event_name in self._listeners and len(self._listeners[event_name]) > 0

    def get_listeners(self, event_name: str) -> List[EventListener]:
        """Get all listeners for event."""
        return self._listeners.get(event_name, [])
```

---

### 4.3 Plugin Manager

**File:** `python/api/src/plugins/manager.py`

```python
"""Plugin manager for loading and managing plugins."""
from typing import Dict, List, Optional, Type
from src.plugins.base import BasePlugin, PluginStatus
from src.events.dispatcher import EventDispatcher, Event


class PluginManager:
    """
    Plugin manager for loading and managing plugins.

    Handles plugin discovery, registration, lifecycle, and dependencies.
    """

    def __init__(self, event_dispatcher: Optional[EventDispatcher] = None):
        self._plugins: Dict[str, BasePlugin] = {}
        self._event_dispatcher = event_dispatcher or EventDispatcher()

    @property
    def event_dispatcher(self) -> EventDispatcher:
        """Get event dispatcher."""
        return self._event_dispatcher

    def register_plugin(self, plugin: BasePlugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin already registered
        """
        name = plugin.metadata.name

        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' already registered")

        self._plugins[name] = plugin

        # Emit event
        event = Event(
            name="plugin.registered",
            data={"plugin_name": name}
        )
        self._event_dispatcher.dispatch(event)

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[BasePlugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List[BasePlugin]:
        """Get all enabled plugins."""
        return [
            plugin for plugin in self._plugins.values()
            if plugin.status == PluginStatus.ENABLED
        ]

    def initialize_plugin(
        self,
        name: str,
        config: Optional[Dict] = None,
    ) -> None:
        """
        Initialize plugin with configuration.

        Args:
            name: Plugin name
            config: Optional configuration

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        plugin.initialize(config)

        # Emit event
        event = Event(
            name="plugin.initialized",
            data={"plugin_name": name}
        )
        self._event_dispatcher.dispatch(event)

    def enable_plugin(self, name: str) -> None:
        """
        Enable plugin.

        Args:
            name: Plugin name

        Raises:
            ValueError: If plugin not found or dependencies not met
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        # Check dependencies
        for dep in plugin.metadata.dependencies:
            dep_plugin = self.get_plugin(dep)
            if not dep_plugin or dep_plugin.status != PluginStatus.ENABLED:
                raise ValueError(f"Dependency '{dep}' not enabled")

        plugin.enable()

        # Emit event
        event = Event(
            name="plugin.enabled",
            data={"plugin_name": name}
        )
        self._event_dispatcher.dispatch(event)

    def disable_plugin(self, name: str) -> None:
        """
        Disable plugin.

        Args:
            name: Plugin name

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        # Check if other plugins depend on this one
        dependent_plugins = [
            p for p in self._plugins.values()
            if name in p.metadata.dependencies
            and p.status == PluginStatus.ENABLED
        ]

        if dependent_plugins:
            names = [p.metadata.name for p in dependent_plugins]
            raise ValueError(f"Cannot disable: plugins {names} depend on it")

        plugin.disable()

        # Emit event
        event = Event(
            name="plugin.disabled",
            data={"plugin_name": name}
        )
        self._event_dispatcher.dispatch(event)
```

---

### 4.4 Payment Provider Plugin Interface

**File:** `python/api/src/plugins/payment_provider.py`

```python
"""Payment provider plugin interface."""
from abc import abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from uuid import UUID
from enum import Enum
from src.plugins.base import BasePlugin


class PaymentStatus(Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentResult:
    """Payment transaction result."""

    def __init__(
        self,
        success: bool,
        transaction_id: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.status = status
        self.error_message = error_message
        self.metadata = metadata or {}


class PaymentProviderPlugin(BasePlugin):
    """
    Abstract base class for payment provider plugins.

    Payment providers (Stripe, PayPal, etc.) must inherit from this class.
    """

    @abstractmethod
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        subscription_id: UUID,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """
        Create payment intent/session.

        Args:
            amount: Payment amount
            currency: Currency code (ISO 4217)
            subscription_id: Subscription UUID
            user_id: User UUID
            metadata: Optional metadata

        Returns:
            PaymentResult with transaction details
        """
        pass

    @abstractmethod
    def process_payment(
        self,
        payment_intent_id: str,
        payment_method: str,
    ) -> PaymentResult:
        """
        Process payment with given method.

        Args:
            payment_intent_id: Payment intent/session ID
            payment_method: Payment method identifier

        Returns:
            PaymentResult with status
        """
        pass

    @abstractmethod
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """
        Refund a payment.

        Args:
            transaction_id: Original transaction ID
            amount: Optional partial refund amount (None = full refund)

        Returns:
            PaymentResult with refund status
        """
        pass

    @abstractmethod
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Webhook payload
            signature: Webhook signature header

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def handle_webhook(
        self,
        payload: Dict[str, Any],
    ) -> None:
        """
        Handle webhook event from payment provider.

        Args:
            payload: Parsed webhook payload
        """
        pass
```

---

### 4.5 Stripe Plugin Implementation

**File:** `python/api/src/plugins/providers/stripe_plugin.py`

```python
"""Stripe payment provider plugin."""
from typing import Dict, Any, Optional
from decimal import Decimal
from uuid import UUID
import stripe
from src.plugins.payment_provider import (
    PaymentProviderPlugin,
    PaymentResult,
    PaymentStatus,
)
from src.plugins.base import PluginMetadata


class StripePlugin(PaymentProviderPlugin):
    """
    Stripe payment provider plugin.

    Integrates Stripe for payment processing.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="stripe",
            version="1.0.0",
            author="VBWD Team",
            description="Stripe payment provider integration",
            dependencies=[],
        )

    def on_enable(self) -> None:
        """Initialize Stripe API."""
        api_key = self.get_config("api_key")
        if not api_key:
            raise ValueError("Stripe API key not configured")

        stripe.api_key = api_key

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        subscription_id: UUID,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """Create Stripe payment intent."""
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata={
                    "subscription_id": str(subscription_id),
                    "user_id": str(user_id),
                    **(metadata or {}),
                },
            )

            return PaymentResult(
                success=True,
                transaction_id=intent.id,
                status=PaymentStatus.PENDING,
                metadata={
                    "client_secret": intent.client_secret,
                    "status": intent.status,
                },
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error_message=str(e),
            )

    def process_payment(
        self,
        payment_intent_id: str,
        payment_method: str,
    ) -> PaymentResult:
        """Confirm Stripe payment intent."""
        try:
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method,
            )

            status_map = {
                "succeeded": PaymentStatus.COMPLETED,
                "processing": PaymentStatus.PROCESSING,
                "requires_payment_method": PaymentStatus.FAILED,
                "requires_confirmation": PaymentStatus.PENDING,
                "requires_action": PaymentStatus.PENDING,
                "canceled": PaymentStatus.CANCELLED,
            }

            return PaymentResult(
                success=intent.status == "succeeded",
                transaction_id=intent.id,
                status=status_map.get(intent.status, PaymentStatus.PENDING),
                metadata={"stripe_status": intent.status},
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error_message=str(e),
            )

    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """Create Stripe refund."""
        try:
            refund_data = {"payment_intent": transaction_id}

            if amount:
                refund_data["amount"] = int(amount * 100)

            refund = stripe.Refund.create(**refund_data)

            return PaymentResult(
                success=True,
                transaction_id=refund.id,
                status=PaymentStatus.REFUNDED,
                metadata={
                    "refund_status": refund.status,
                    "amount": refund.amount,
                },
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                error_message=str(e),
            )

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify Stripe webhook signature."""
        webhook_secret = self.get_config("webhook_secret")
        if not webhook_secret:
            return False

        try:
            stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return True
        except Exception:
            return False

    def handle_webhook(
        self,
        payload: Dict[str, Any],
    ) -> None:
        """Handle Stripe webhook event."""
        event_type = payload.get("type")

        if event_type == "payment_intent.succeeded":
            # Payment completed successfully
            intent = payload["data"]["object"]
            # Emit event for subscription activation
            # (handled by subscription service)
            pass

        elif event_type == "payment_intent.payment_failed":
            # Payment failed
            intent = payload["data"]["object"]
            # Emit event for failure handling
            pass
```

---

### 4.6 Tests

**File:** `python/api/tests/unit/plugins/test_plugin_manager.py`

```python
"""Tests for PluginManager."""
import pytest
from unittest.mock import Mock
from src.plugins.manager import PluginManager
from src.plugins.base import BasePlugin, PluginMetadata, PluginStatus
from src.events.dispatcher import EventDispatcher, Event


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(self, name: str, dependencies: list = None):
        super().__init__()
        self._name = name
        self._dependencies = dependencies or []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version="1.0.0",
            author="Test",
            description="Test plugin",
            dependencies=self._dependencies,
        )


class TestPluginManagerRegistration:
    """Test cases for plugin registration."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager."""
        return PluginManager()

    def test_register_plugin(self, plugin_manager):
        """register_plugin should register plugin."""
        plugin = MockPlugin("test-plugin")

        plugin_manager.register_plugin(plugin)

        assert plugin_manager.get_plugin("test-plugin") == plugin

    def test_register_duplicate_raises_error(self, plugin_manager):
        """register_plugin should raise error for duplicate."""
        plugin1 = MockPlugin("test-plugin")
        plugin2 = MockPlugin("test-plugin")

        plugin_manager.register_plugin(plugin1)

        with pytest.raises(ValueError, match="already registered"):
            plugin_manager.register_plugin(plugin2)

    def test_get_all_plugins(self, plugin_manager):
        """get_all_plugins should return all registered."""
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")

        plugin_manager.register_plugin(plugin1)
        plugin_manager.register_plugin(plugin2)

        plugins = plugin_manager.get_all_plugins()

        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins


class TestPluginManagerLifecycle:
    """Test cases for plugin lifecycle."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager."""
        return PluginManager()

    def test_initialize_plugin(self, plugin_manager):
        """initialize_plugin should initialize with config."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)

        config = {"api_key": "test123"}
        plugin_manager.initialize_plugin("test-plugin", config)

        assert plugin.status == PluginStatus.INITIALIZED
        assert plugin.get_config("api_key") == "test123"

    def test_enable_plugin(self, plugin_manager):
        """enable_plugin should enable plugin."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")

        plugin_manager.enable_plugin("test-plugin")

        assert plugin.status == PluginStatus.ENABLED

    def test_disable_plugin(self, plugin_manager):
        """disable_plugin should disable plugin."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")
        plugin_manager.enable_plugin("test-plugin")

        plugin_manager.disable_plugin("test-plugin")

        assert plugin.status == PluginStatus.DISABLED


class TestPluginManagerDependencies:
    """Test cases for plugin dependencies."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager."""
        return PluginManager()

    def test_enable_with_dependencies(self, plugin_manager):
        """enable_plugin should check dependencies."""
        base_plugin = MockPlugin("base")
        dependent_plugin = MockPlugin("dependent", dependencies=["base"])

        plugin_manager.register_plugin(base_plugin)
        plugin_manager.register_plugin(dependent_plugin)

        plugin_manager.initialize_plugin("base")
        plugin_manager.enable_plugin("base")

        plugin_manager.initialize_plugin("dependent")
        plugin_manager.enable_plugin("dependent")

        assert dependent_plugin.status == PluginStatus.ENABLED

    def test_enable_without_dependencies_raises_error(self, plugin_manager):
        """enable_plugin should raise if dependencies not met."""
        dependent_plugin = MockPlugin("dependent", dependencies=["missing"])

        plugin_manager.register_plugin(dependent_plugin)
        plugin_manager.initialize_plugin("dependent")

        with pytest.raises(ValueError, match="not enabled"):
            plugin_manager.enable_plugin("dependent")

    def test_disable_with_dependents_raises_error(self, plugin_manager):
        """disable_plugin should raise if other plugins depend on it."""
        base_plugin = MockPlugin("base")
        dependent_plugin = MockPlugin("dependent", dependencies=["base"])

        plugin_manager.register_plugin(base_plugin)
        plugin_manager.register_plugin(dependent_plugin)

        plugin_manager.initialize_plugin("base")
        plugin_manager.enable_plugin("base")
        plugin_manager.initialize_plugin("dependent")
        plugin_manager.enable_plugin("dependent")

        with pytest.raises(ValueError, match="depend on it"):
            plugin_manager.disable_plugin("base")
```

**File:** `python/api/tests/unit/events/test_event_dispatcher.py`

```python
"""Tests for EventDispatcher."""
import pytest
from src.events.dispatcher import EventDispatcher, Event, EventPriority


class TestEventDispatcher:
    """Test cases for EventDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create EventDispatcher."""
        return EventDispatcher()

    def test_add_and_dispatch_listener(self, dispatcher):
        """add_listener should register and dispatch calls it."""
        called = []

        def listener(event: Event):
            called.append(event.name)

        dispatcher.add_listener("test.event", listener)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == ["test.event"]

    def test_dispatch_with_priority(self, dispatcher):
        """dispatch should call listeners in priority order."""
        order = []

        def listener_low(event: Event):
            order.append("low")

        def listener_high(event: Event):
            order.append("high")

        dispatcher.add_listener("test.event", listener_low, EventPriority.LOW)
        dispatcher.add_listener("test.event", listener_high, EventPriority.HIGH)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert order == ["high", "low"]

    def test_stop_propagation(self, dispatcher):
        """stop_propagation should prevent remaining listeners."""
        called = []

        def listener1(event: Event):
            called.append("listener1")
            event.stop_propagation()

        def listener2(event: Event):
            called.append("listener2")

        dispatcher.add_listener("test.event", listener1)
        dispatcher.add_listener("test.event", listener2)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == ["listener1"]

    def test_remove_listener(self, dispatcher):
        """remove_listener should unregister listener."""
        called = []

        def listener(event: Event):
            called.append(event.name)

        dispatcher.add_listener("test.event", listener)
        dispatcher.remove_listener("test.event", listener)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == []
```

---

## Database Schema Updates

### Plugin Configuration Table

```sql
CREATE TABLE plugin_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_name VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'disabled',
    config JSONB,
    enabled_at TIMESTAMP,
    disabled_at TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plugin_config_status ON plugin_config(status);
```

---

## Integration with Subscriptions

### Subscription Activation Flow with Payments

1. User selects tariff plan
2. `POST /api/v1/subscriptions` creates subscription (status: PENDING)
3. Payment intent created via payment plugin
4. User completes payment
5. Webhook received from payment provider
6. Plugin emits `payment.completed` event
7. SubscriptionService activates subscription
8. Subscription status: PENDING → ACTIVE

---

## Deliverables Checklist

| Item | File | Tests |
|------|------|-------|
| BasePlugin | `src/plugins/base.py` | N/A (base class) |
| EventDispatcher | `src/events/dispatcher.py` | ✅ 5 tests |
| PluginManager | `src/plugins/manager.py` | ✅ 10 tests |
| PaymentProviderPlugin | `src/plugins/payment_provider.py` | N/A (interface) |
| StripePlugin | `src/plugins/providers/stripe_plugin.py` | ✅ 8 tests |
| PayPalPlugin (basic) | `src/plugins/providers/paypal_plugin.py` | ✅ 6 tests |
| Plugin routes | `src/routes/plugins.py` | ✅ 5 tests |
| Webhook routes | `src/routes/webhooks.py` | ✅ 4 tests |

**Total:** 38+ new tests

---

## Testing Strategy

### Unit Tests
- Plugin lifecycle (register, initialize, enable, disable)
- Event dispatcher (add, remove, dispatch, priority)
- Dependency resolution
- Configuration management

### Integration Tests
- Plugin loading and initialization
- Event propagation through plugins
- Payment flow end-to-end
- Webhook handling

### Mock Payment Provider
For testing without actual payment provider accounts:
```python
class MockPaymentPlugin(PaymentProviderPlugin):
    """Mock payment provider for testing."""
    # Always succeeds/fails based on test setup
```

---

## Security Considerations

1. **Plugin Isolation**
   - Plugins cannot access other plugin's data
   - Configuration encrypted at rest
   - API keys stored in environment variables

2. **Webhook Verification**
   - All webhooks must verify signatures
   - Failed verification = 401 response
   - Logged for security audit

3. **Plugin Validation**
   - Only trusted plugins can be registered
   - Plugin code review required
   - Dependency audit

---

## Performance Considerations

1. **Event Dispatching**
   - Async event handling for long-running listeners
   - Timeout on event listeners (5 seconds)
   - Failed listeners don't block others

2. **Plugin Loading**
   - Lazy loading of plugins
   - Only load enabled plugins at startup
   - Cache plugin instances

---

## Future Enhancements (Sprint 5+)

1. **Plugin Marketplace**
   - Browse and install community plugins
   - Plugin ratings and reviews
   - Automatic updates

2. **Additional Provider Plugins**
   - Mollie, Adyen, Braintree
   - Cryptocurrency payments
   - Bank transfers (SEPA, ACH)

3. **Notification Plugins**
   - Email providers (SendGrid, Mailgun, AWS SES)
   - SMS providers (Twilio, Vonage)
   - Push notifications (Firebase, OneSignal)

4. **Analytics Plugins**
   - Google Analytics
   - Mixpanel
   - Custom event tracking

---

## Success Criteria

- ✅ Plugin system supports lifecycle management
- ✅ Event system allows inter-plugin communication
- ✅ At least 2 payment providers implemented (Stripe + PayPal)
- ✅ Webhooks properly verified and handled
- ✅ All tests passing (38+ new tests)
- ✅ Payment flow works end-to-end
- ✅ Plugins can be enabled/disabled dynamically

---

## Time Estimate

- Plugin base + manager: 45 minutes
- Event system: 30 minutes
- Payment provider interface: 20 minutes
- Stripe plugin: 45 minutes
- PayPal plugin (basic): 30 minutes
- Routes + webhooks: 30 minutes
- Tests: 45 minutes
- **Total:** ~3 hours

---

## Notes

- This sprint focuses on **architecture and foundation** for plugins
- Payment processing is enabled but basic
- Full payment features (invoicing, receipts) come in Sprint 5
- Plugin system is extensible for future features (notifications, analytics, etc.)
