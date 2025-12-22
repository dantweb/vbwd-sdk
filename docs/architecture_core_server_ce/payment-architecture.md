# Payment Architecture

**Event-Driven Payment Platform with Plugin System**

---

## Overview

The payment system is designed as an event-driven, provider-agnostic platform. Following the established domain event pattern:

- **Routes** trigger payment domain events
- **EventDispatcher** dispatches events to registered handlers
- **Event Handlers** use services for business logic implementation
- **Payment Plugins** provide provider-specific integration
- **SDK Adapters** wrap provider APIs with idempotency checks

This architecture enables:
- Decoupled payment flow via domain events
- Easy addition of new payment providers without core changes
- Consistent payment handling regardless of provider
- Clean separation between routes, events, handlers, services, and SDK adapters
- Idempotent API calls preventing duplicate charges/refunds

---

## Event-Driven Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌─────────────────┐     ┌──────────────────────────┐  │
│  │              │     │                 │     │                          │  │
│  │    Routes    │────▶│  Domain Events  │────▶│    EventDispatcher       │  │
│  │  (Triggers)  │     │   (Emitted)     │     │     (Dispatches)         │  │
│  │              │     │                 │     │                          │  │
│  └──────────────┘     └─────────────────┘     └───────────┬──────────────┘  │
│                                                           │                  │
│                                                           ▼                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         EVENT HANDLERS                                  │ │
│  │                    (Orchestrate Business Logic)                         │ │
│  │                                                                         │ │
│  │   ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐   │ │
│  │   │ PaymentInitiated│  │ PaymentCompleted │  │ PaymentFailed       │   │ │
│  │   │ Handler         │  │ Handler          │  │ Handler             │   │ │
│  │   └────────┬────────┘  └────────┬─────────┘  └──────────┬──────────┘   │ │
│  │            │                    │                       │               │ │
│  └────────────┼────────────────────┼───────────────────────┼───────────────┘ │
│               │                    │                       │                  │
│               ▼                    ▼                       ▼                  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                          SERVICES LAYER                                 │  │
│  │                      (Business Logic Implementation)                    │  │
│  │                                                                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │  │
│  │  │ Invoice     │  │ Subscription│  │ User        │  │ Notification  │  │  │
│  │  │ Service     │  │ Service     │  │ Service     │  │ Service       │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│                                    ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         PLUGIN LAYER                                    │  │
│  │                   (Payment Provider Plugins)                            │  │
│  │                                                                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │  │
│  │  │  Stripe  │  │  PayPal  │  │  Klarna  │  │  Manual/Invoice      │   │  │
│  │  │  Plugin  │  │  Plugin  │  │  Plugin  │  │  Plugin              │   │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────────────────┘   │  │
│  │       │             │             │                                    │  │
│  └───────┼─────────────┼─────────────┼────────────────────────────────────┘  │
│          │             │             │                                       │
│          ▼             ▼             ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                      SDK ADAPTER LAYER                                  │  │
│  │            (Provider SDK Wrappers with Idempotency)                     │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │                    IdempotencyService                            │   │  │
│  │  │     (Check/Store idempotency keys to prevent duplicate calls)    │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │ StripeSDK    │  │ PayPalSDK    │  │ KlarnaSDK    │                  │  │
│  │  │ Adapter      │  │ Adapter      │  │ Adapter      │                  │  │
│  │  │              │  │              │  │              │                  │  │
│  │  │ - HTTP Client│  │ - REST API   │  │ - HTTP Client│                  │  │
│  │  │ - Auth       │  │ - OAuth2     │  │ - Auth       │                  │  │
│  │  │ - Retries    │  │ - Retries    │  │ - Retries    │                  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Event System Core Components

The event system provides a sophisticated, priority-based event handling mechanism. Based on proven patterns from enterprise payment solutions, it supports:

- **Priority-based handler execution** (higher priority executes first)
- **Event propagation control** (handlers can stop propagation)
- **Request-scoped context** (shared data across handlers)
- **Lazy handler initialization** (prevents circular dependencies)
- **Event chaining** (handlers can emit subsequent events)

### Event Interface

```python
"""Event system interfaces - src/events/interfaces.py"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


class EventInterface(ABC):
    """
    Base interface for all events.

    All domain events must implement this interface.
    """
    pass


@dataclass
class Event(EventInterface):
    """
    Base event class with common properties.
    """
    name: str = ""
    propagation_stopped: bool = field(default=False, repr=False)

    def stop_propagation(self) -> None:
        """Stop event from being processed by remaining handlers."""
        self.propagation_stopped = True

    def is_propagation_stopped(self) -> bool:
        """Check if propagation was stopped."""
        return self.propagation_stopped


@dataclass
class DomainEvent(Event):
    """
    Domain event with metadata for tracking and debugging.
    """
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, key: str, value: Any) -> 'DomainEvent':
        """Add metadata and return self for chaining."""
        self.metadata[key] = value
        return self
```

### Event Context

Event context provides request-scoped data caching, preventing multiple database queries during event processing.

```python
"""Event context - src/events/context.py"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class EventContext:
    """
    Request-scoped context for event handlers.

    Caches data that multiple handlers need access to,
    preventing redundant database queries.

    Usage:
        context = EventContext()
        context.set('basket', basket_data)
        context.set('user', user_data)

        # In handlers:
        basket = event.context.get('basket')
        user = event.context.get('user')
    """
    _data: Dict[str, Any] = field(default_factory=dict)

    # Common cached entities
    _user_id: Optional[UUID] = None
    _invoice_id: Optional[UUID] = None
    _subscription_id: Optional[UUID] = None

    def set(self, key: str, value: Any) -> None:
        """Store value in context."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve value from context."""
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if key exists in context."""
        return key in self._data

    def all(self) -> Dict[str, Any]:
        """Get all context data."""
        return self._data.copy()

    # Convenience properties for common entities
    @property
    def user_id(self) -> Optional[UUID]:
        return self._user_id

    @user_id.setter
    def user_id(self, value: UUID) -> None:
        self._user_id = value

    @property
    def invoice_id(self) -> Optional[UUID]:
        return self._invoice_id

    @invoice_id.setter
    def invoice_id(self, value: UUID) -> None:
        self._invoice_id = value

    @property
    def subscription_id(self) -> Optional[UUID]:
        return self._subscription_id

    @subscription_id.setter
    def subscription_id(self, value: UUID) -> None:
        self._subscription_id = value

    # Convenience getters
    def get_basket(self) -> Optional[Dict]:
        """Get cached basket data."""
        return self.get('basket')

    def get_user(self) -> Optional[Dict]:
        """Get cached user data."""
        return self.get('user')

    def get_tarif_plan(self) -> Optional[Dict]:
        """Get cached tarif plan data."""
        return self.get('tarif_plan')
```

### Handler Interface

```python
"""Handler interface - src/events/handler.py"""
from abc import ABC, abstractmethod
from typing import Type
from dataclasses import dataclass


class HandlerPriority:
    """Handler priority constants."""
    HIGHEST = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    LOWEST = 0


@dataclass
class EventResult:
    """
    Result returned by event handlers.
    """
    success: bool
    data: dict = None
    error: str = None

    @classmethod
    def success_result(cls, data: dict = None) -> 'EventResult':
        return cls(success=True, data=data or {})

    @classmethod
    def error_result(cls, error: str) -> 'EventResult':
        return cls(success=False, error=error)


class IEventHandler(ABC):
    """
    Interface for event handlers.

    Handlers implement business logic triggered by domain events.
    Each handler should:
    1. Handle ONE specific event type
    2. Use services for business logic (not implement it directly)
    3. Optionally emit subsequent events for downstream processing

    Example:
        class PaymentCapturedHandler(IEventHandler):
            def __init__(self, invoice_service, subscription_service):
                self.invoice_service = invoice_service
                self.subscription_service = subscription_service

            @staticmethod
            def get_handled_event_class() -> str:
                return 'payment.captured'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.NORMAL

            def can_handle(self, event) -> bool:
                return isinstance(event, PaymentCapturedEvent)

            def handle(self, event: PaymentCapturedEvent) -> EventResult:
                # Use services for business logic
                self.invoice_service.mark_paid(event.invoice_id)
                self.subscription_service.activate(event.subscription_id)
                return EventResult.success_result()
    """

    @staticmethod
    @abstractmethod
    def get_handled_event_class() -> str:
        """
        Return the event name this handler processes.

        Used for registration without instantiating the handler.
        """
        pass

    @staticmethod
    def get_priority() -> int:
        """
        Return handler priority (higher executes first).

        Default is NORMAL (50). Override for specific ordering needs.
        """
        return HandlerPriority.NORMAL

    @abstractmethod
    def can_handle(self, event: EventInterface) -> bool:
        """
        Check if this handler can process the given event.

        Typically checks isinstance() for the expected event type.
        """
        pass

    @abstractmethod
    def handle(self, event: EventInterface) -> EventResult:
        """
        Process the event and return result.

        Should use injected services for business logic.
        Can emit subsequent events via dispatcher if needed.
        """
        pass
```

### Abstract Base Handler

```python
"""Base handler with common dependencies - src/events/base_handler.py"""
from typing import Optional
import logging

from src.events.handler import IEventHandler, EventResult, HandlerPriority
from src.events.interfaces import EventInterface
from src.repositories.base import BaseRepository


logger = logging.getLogger(__name__)


class AbstractHandler(IEventHandler):
    """
    Abstract base handler with common dependencies.

    Provides:
    - Event dispatcher for emitting subsequent events
    - Logger for debugging
    - Common error handling pattern

    Subclasses must implement:
    - get_handled_event_class()
    - can_handle()
    - handle()
    """

    def __init__(
        self,
        event_dispatcher: Optional['EventDispatcher'] = None,
    ):
        self._dispatcher = event_dispatcher
        self._logger = logging.getLogger(self.__class__.__name__)

    def emit(self, event: EventInterface) -> Optional[EventResult]:
        """
        Emit a subsequent event.

        Allows handlers to trigger downstream processing.
        """
        if self._dispatcher:
            return self._dispatcher.dispatch(event)
        return None

    def log_info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self._logger.info(message, extra=kwargs)

    def log_error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self._logger.error(message, extra=kwargs)

    def handle_with_error_logging(
        self,
        event: EventInterface,
        handler_func,
    ) -> EventResult:
        """
        Wrapper that logs errors and returns error result.
        """
        try:
            return handler_func(event)
        except Exception as e:
            self.log_error(
                f"Handler error: {e}",
                event_name=event.name if hasattr(event, 'name') else 'unknown',
                handler=self.__class__.__name__,
            )
            return EventResult.error_result(str(e))
```

### Event Dispatcher

```python
"""Event dispatcher - src/events/dispatcher.py"""
from typing import Dict, List, Callable, Optional, Type
from dataclasses import dataclass, field
import logging

from src.events.interfaces import EventInterface, DomainEvent
from src.events.handler import IEventHandler, EventResult


logger = logging.getLogger(__name__)


@dataclass
class RegisteredHandler:
    """Handler registration entry."""
    handler: IEventHandler
    priority: int


class EventDispatcher:
    """
    Event dispatcher with priority-based execution.

    Features:
    - Priority-based handler ordering (higher first)
    - Event propagation control
    - Multiple handlers per event type
    - Combined results from all handlers
    - Lazy handler initialization support

    Usage:
        dispatcher = EventDispatcher()

        # Register handlers
        dispatcher.register('payment.captured', PaymentCapturedHandler(...))
        dispatcher.register('payment.captured', NotificationHandler(...), priority=25)

        # Dispatch event
        event = PaymentCapturedEvent(...)
        result = dispatcher.dispatch(event)
    """

    def __init__(self):
        self._handlers: Dict[str, List[RegisteredHandler]] = {}
        self._initialized = False

    def register(
        self,
        event_name: str,
        handler: IEventHandler,
        priority: Optional[int] = None,
    ) -> None:
        """
        Register handler for event type.

        Args:
            event_name: Event name to listen for
            handler: Handler instance
            priority: Optional priority override (default: handler's get_priority())
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []

        actual_priority = priority if priority is not None else handler.get_priority()

        self._handlers[event_name].append(
            RegisteredHandler(handler=handler, priority=actual_priority)
        )

        # Sort by priority (descending - higher first)
        self._handlers[event_name].sort(key=lambda h: h.priority, reverse=True)

        logger.debug(
            f"Registered handler {handler.__class__.__name__} "
            f"for '{event_name}' with priority {actual_priority}"
        )

    def unregister(self, event_name: str, handler: IEventHandler) -> None:
        """Remove handler from event."""
        if event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name]
                if h.handler is not handler
            ]

    def dispatch(self, event: EventInterface) -> EventResult:
        """
        Dispatch event to all registered handlers.

        Handlers execute in priority order (highest first).
        If any handler stops propagation, remaining handlers are skipped.

        Args:
            event: Event to dispatch

        Returns:
            Combined EventResult from all handlers
        """
        event_name = getattr(event, 'name', event.__class__.__name__)
        handlers = self._handlers.get(event_name, [])

        if not handlers:
            logger.debug(f"No handlers registered for '{event_name}'")
            return EventResult.success_result()

        logger.info(
            f"Dispatching '{event_name}' to {len(handlers)} handler(s)"
        )

        results = []

        for registered in handlers:
            handler = registered.handler

            # Check if handler can process this event
            if not handler.can_handle(event):
                continue

            try:
                result = handler.handle(event)
                results.append(result)

                if not result.success:
                    logger.warning(
                        f"Handler {handler.__class__.__name__} "
                        f"failed: {result.error}"
                    )

            except Exception as e:
                logger.exception(
                    f"Handler {handler.__class__.__name__} "
                    f"raised exception: {e}"
                )
                results.append(EventResult.error_result(str(e)))

            # Check for propagation stop
            if hasattr(event, 'is_propagation_stopped') and event.is_propagation_stopped():
                logger.debug(
                    f"Propagation stopped by {handler.__class__.__name__}"
                )
                break

        # Combine results
        return self._combine_results(results)

    def _combine_results(self, results: List[EventResult]) -> EventResult:
        """Combine multiple handler results into one."""
        if not results:
            return EventResult.success_result()

        # If any failed, return first failure
        for result in results:
            if not result.success:
                return result

        # Merge all data
        combined_data = {}
        for result in results:
            if result.data:
                combined_data.update(result.data)

        return EventResult.success_result(combined_data)

    def get_handlers(self, event_name: str) -> List[IEventHandler]:
        """Get all handlers for event type."""
        return [h.handler for h in self._handlers.get(event_name, [])]


class EventListenerProvider:
    """
    Provider for lazy handler initialization.

    Prevents circular dependencies by deferring handler
    instantiation until first use.

    Usage:
        provider = EventListenerProvider()
        provider.add_handler_class('payment.captured', PaymentCapturedHandler)

        # Later, when dispatcher needs handlers:
        handlers = provider.get_handlers_for_event('payment.captured', container)
    """

    def __init__(self):
        self._handler_classes: Dict[str, List[tuple]] = {}
        self._initialized_handlers: Dict[str, List[IEventHandler]] = {}

    def add_handler_class(
        self,
        event_name: str,
        handler_class: Type[IEventHandler],
        priority: Optional[int] = None,
    ) -> None:
        """Register handler class for lazy initialization."""
        if event_name not in self._handler_classes:
            self._handler_classes[event_name] = []

        self._handler_classes[event_name].append((handler_class, priority))

    def get_handlers_for_event(
        self,
        event_name: str,
        container,  # DI container
    ) -> List[tuple]:
        """
        Get initialized handlers for event.

        Initializes handlers on first access using DI container.
        """
        if event_name not in self._initialized_handlers:
            self._initialized_handlers[event_name] = []

            for handler_class, priority in self._handler_classes.get(event_name, []):
                # Resolve handler from DI container
                handler = container.get(handler_class)
                actual_priority = priority or handler.get_priority()
                self._initialized_handlers[event_name].append((handler, actual_priority))

        return self._initialized_handlers[event_name]
```

---

## Domain Events

### Payment Events

```python
"""Payment domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from src.events.domain import DomainEvent


@dataclass
class CheckoutInitiatedEvent(DomainEvent):
    """Event: User initiated checkout process."""

    user_id: UUID = None
    tarif_plan_id: UUID = None
    payment_method: str = None  # card, invoice, wallet, bnpl
    provider: str = None  # stripe, paypal, manual
    currency: str = None
    country: str = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'checkout.initiated'


@dataclass
class PaymentIntentCreatedEvent(DomainEvent):
    """Event: Payment intent was created with provider."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None
    provider_reference: str = None
    amount: Decimal = None
    currency: str = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'payment.intent_created'


@dataclass
class PaymentAuthorizedEvent(DomainEvent):
    """Event: Payment was authorized (before capture)."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None
    provider_reference: str = None
    amount: Decimal = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'payment.authorized'


@dataclass
class PaymentCapturedEvent(DomainEvent):
    """Event: Payment was captured successfully."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None
    provider_reference: str = None
    amount: Decimal = None
    currency: str = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'payment.captured'


@dataclass
class PaymentFailedEvent(DomainEvent):
    """Event: Payment failed."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None
    error_code: str = None
    error_message: str = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'payment.failed'


@dataclass
class PaymentRefundedEvent(DomainEvent):
    """Event: Payment was refunded."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None
    refund_id: str = None
    amount: Decimal = None
    reason: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'payment.refunded'


@dataclass
class WebhookReceivedEvent(DomainEvent):
    """Event: Webhook received from payment provider."""

    provider: str = None
    event_type: str = None  # Provider's event type
    payload: dict = None
    signature_valid: bool = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'webhook.received'


@dataclass
class CheckoutCompletedEvent(DomainEvent):
    """Event: Checkout session completed successfully."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'checkout.completed'


@dataclass
class CheckoutExpiredEvent(DomainEvent):
    """Event: Checkout session expired."""

    invoice_id: UUID = None
    subscription_id: UUID = None
    user_id: UUID = None
    provider: str = None

    def __post_init__(self):
        super().__post_init__()
        self.name = 'checkout.expired'
```

---

## Event Handlers

### Handler Pattern

All payment handlers implement `IEventHandler` interface and use services for business logic.

```python
"""Payment event handlers."""
from src.events.domain import IEventHandler, DomainEvent, EventResult
from src.events.payment_events import (
    CheckoutInitiatedEvent,
    PaymentCapturedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
    WebhookReceivedEvent,
)


class CheckoutInitiatedHandler(IEventHandler):
    """
    Handler for checkout initiation.

    Creates invoice, subscription, and payment intent.
    """

    def __init__(
        self,
        invoice_service,
        subscription_service,
        payment_service,
        plugin_registry,
    ):
        self.invoice_service = invoice_service
        self.subscription_service = subscription_service
        self.payment_service = payment_service
        self.plugin_registry = plugin_registry

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, CheckoutInitiatedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle checkout initiation.

        1. Create pending subscription
        2. Create invoice with tax calculation
        3. Get payment plugin
        4. Create payment intent/checkout session
        """
        if not isinstance(event, CheckoutInitiatedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # 1. Create subscription (PENDING status)
            subscription = self.subscription_service.create_subscription(
                user_id=event.user_id,
                tarif_plan_id=event.tarif_plan_id,
            )

            # 2. Create invoice
            invoice = self.invoice_service.create_invoice(
                user_id=event.user_id,
                subscription_id=subscription.id,
                tarif_plan_id=event.tarif_plan_id,
                currency=event.currency,
                country=event.country,
            )

            # 3. Get payment plugin
            plugin = self.plugin_registry.get_plugin(event.provider)
            if not plugin:
                return EventResult.error_result(
                    f"Payment provider not available: {event.provider}"
                )

            # 4. Create payment intent
            checkout_result = self.payment_service.create_checkout(
                plugin=plugin,
                invoice=invoice,
                payment_method=event.payment_method,
            )

            return EventResult.success_result({
                "subscription_id": str(subscription.id),
                "invoice_id": str(invoice.id),
                "checkout_url": checkout_result.checkout_url,
                "requires_redirect": checkout_result.requires_redirect,
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class PaymentCapturedHandler(IEventHandler):
    """
    Handler for successful payment capture.

    Activates subscription, marks invoice paid, sends confirmation.
    """

    def __init__(
        self,
        invoice_service,
        subscription_service,
        user_service,
        notification_service=None,
    ):
        self.invoice_service = invoice_service
        self.subscription_service = subscription_service
        self.user_service = user_service
        self.notification_service = notification_service

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, PaymentCapturedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle payment capture.

        1. Mark invoice as paid
        2. Activate subscription
        3. Activate user if pending
        4. Send confirmation notification
        """
        if not isinstance(event, PaymentCapturedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # 1. Mark invoice paid
            self.invoice_service.mark_paid(
                invoice_id=event.invoice_id,
                payment_ref=event.provider_reference,
                provider=event.provider,
            )

            # 2. Activate subscription
            self.subscription_service.activate_subscription(event.subscription_id)

            # 3. Activate user if pending
            user = self.user_service.get_user(event.user_id)
            if user and user.status.value == "pending":
                self.user_service.update_user_status(event.user_id, "active")

            # 4. Send confirmation
            if self.notification_service:
                self.notification_service.send_payment_confirmation(
                    user_id=event.user_id,
                    invoice_id=event.invoice_id,
                )

            return EventResult.success_result({
                "invoice_id": str(event.invoice_id),
                "subscription_activated": True,
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class PaymentFailedHandler(IEventHandler):
    """
    Handler for failed payments.

    Updates invoice status, notifies user.
    """

    def __init__(
        self,
        invoice_service,
        notification_service=None,
    ):
        self.invoice_service = invoice_service
        self.notification_service = notification_service

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, PaymentFailedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle payment failure.

        1. Mark invoice as failed
        2. Send failure notification
        3. Log for retry workflow
        """
        if not isinstance(event, PaymentFailedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # 1. Mark invoice failed
            self.invoice_service.mark_failed(
                invoice_id=event.invoice_id,
                error=event.error_message,
            )

            # 2. Notify user
            if self.notification_service:
                self.notification_service.send_payment_failed(
                    user_id=event.user_id,
                    invoice_id=event.invoice_id,
                    error=event.error_message,
                )

            return EventResult.success_result({
                "invoice_id": str(event.invoice_id),
                "handled": True,
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class WebhookReceivedHandler(IEventHandler):
    """
    Handler for incoming webhooks.

    Parses provider webhook and emits appropriate domain event.
    """

    def __init__(
        self,
        plugin_registry,
        event_dispatcher,
    ):
        self.plugin_registry = plugin_registry
        self.event_dispatcher = event_dispatcher

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, WebhookReceivedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle webhook reception.

        1. Get plugin for provider
        2. Parse webhook to normalized event
        3. Emit appropriate domain event
        """
        if not isinstance(event, WebhookReceivedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # 1. Get plugin
            plugin = self.plugin_registry.get_plugin(event.provider)
            if not plugin:
                return EventResult.error_result(f"Unknown provider: {event.provider}")

            # 2. Parse webhook
            normalized = plugin.parse_webhook_event(event.payload)

            # 3. Emit domain event based on normalized type
            domain_event = self._create_domain_event(normalized, event.provider)
            if domain_event:
                result = self.event_dispatcher.emit(domain_event)
                return result

            return EventResult.success_result({"acknowledged": True})

        except Exception as e:
            return EventResult.error_result(str(e))

    def _create_domain_event(self, normalized, provider):
        """Map normalized webhook event to domain event."""
        event_map = {
            "payment.captured": PaymentCapturedEvent,
            "payment.failed": PaymentFailedEvent,
            "payment.refunded": PaymentRefundedEvent,
        }

        event_class = event_map.get(normalized.type)
        if not event_class:
            return None

        return event_class(
            invoice_id=normalized.invoice_id,
            subscription_id=normalized.subscription_id,
            user_id=normalized.user_id,
            provider=provider,
            provider_reference=normalized.payment_intent_id,
        )


class PaymentRefundedHandler(IEventHandler):
    """
    Handler for payment refunds.

    Updates invoice, cancels subscription access.
    """

    def __init__(
        self,
        invoice_service,
        subscription_service,
        notification_service=None,
    ):
        self.invoice_service = invoice_service
        self.subscription_service = subscription_service
        self.notification_service = notification_service

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, PaymentRefundedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle payment refund.

        1. Mark invoice as refunded
        2. Cancel subscription
        3. Notify user
        """
        if not isinstance(event, PaymentRefundedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # 1. Mark refunded
            self.invoice_service.mark_refunded(
                invoice_id=event.invoice_id,
                refund_id=event.refund_id,
            )

            # 2. Cancel subscription
            if event.subscription_id:
                self.subscription_service.cancel_subscription(
                    subscription_id=event.subscription_id,
                    reason=event.reason or "Payment refunded",
                )

            # 3. Notify
            if self.notification_service:
                self.notification_service.send_refund_confirmation(
                    user_id=event.user_id,
                    invoice_id=event.invoice_id,
                    amount=event.amount,
                )

            return EventResult.success_result({
                "invoice_id": str(event.invoice_id),
                "refunded": True,
            })

        except Exception as e:
            return EventResult.error_result(str(e))
```

---

## Routes (Event Triggers)

Routes are thin - they validate input, emit events, and return responses.

```python
"""Payment routes - event triggers."""
from flask import Blueprint, request, jsonify, g
from src.middleware.auth import require_auth
from src.events.domain import DomainEventDispatcher
from src.events.payment_events import (
    CheckoutInitiatedEvent,
    WebhookReceivedEvent,
)


payment_bp = Blueprint('payment', __name__, url_prefix='/api/v1/payment')


@payment_bp.route('/checkout', methods=['POST'])
@require_auth
def initiate_checkout():
    """
    Initiate checkout process.

    Emits CheckoutInitiatedEvent for handler to process.
    """
    data = request.get_json()

    # Validate required fields
    required = ['tarif_plan_id', 'payment_method', 'currency']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    # Create and emit event
    event = CheckoutInitiatedEvent(
        user_id=g.user_id,
        tarif_plan_id=data['tarif_plan_id'],
        payment_method=data['payment_method'],
        provider=data.get('provider'),  # Optional, handler selects default
        currency=data['currency'],
        country=data.get('country', 'DE'),
    )

    dispatcher = DomainEventDispatcher()
    result = dispatcher.emit(event)

    if result.success:
        return jsonify(result.data), 200
    else:
        return jsonify({'error': result.error}), 400


@payment_bp.route('/webhook/<provider>', methods=['POST'])
def handle_webhook(provider: str):
    """
    Handle incoming webhook from payment provider.

    Emits WebhookReceivedEvent for handler to process.
    """
    # Get raw payload for signature verification
    raw_payload = request.get_data()
    payload = request.get_json()
    signature = request.headers.get('X-Signature', '')

    # Verify signature via plugin
    from src.plugins.registry import PaymentPluginRegistry
    plugin = PaymentPluginRegistry.get_plugin(provider)

    if not plugin:
        return jsonify({'error': 'Unknown provider'}), 400

    signature_valid = plugin.verify_webhook_signature(raw_payload, signature)
    if not signature_valid:
        return jsonify({'error': 'Invalid signature'}), 401

    # Emit event
    event = WebhookReceivedEvent(
        provider=provider,
        event_type=payload.get('type', ''),
        payload=payload,
        signature_valid=True,
    )

    dispatcher = DomainEventDispatcher()
    result = dispatcher.emit(event)

    # Always return 200 to acknowledge receipt
    return jsonify({'received': True}), 200


@payment_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """
    Get available payment methods for context.

    No event needed - simple query operation.
    """
    currency = request.args.get('currency', 'EUR')
    country = request.args.get('country', 'DE')

    from src.services.payment_service import PaymentService
    payment_service = PaymentService()

    methods = payment_service.get_available_methods(
        currency=currency,
        country=country,
    )

    return jsonify({'methods': methods}), 200
```

---

## Handler Registration

Handlers are registered with the dispatcher at application startup.

```python
"""Payment handler registration."""
from src.events.domain import DomainEventDispatcher
from src.handlers.payment_handlers import (
    CheckoutInitiatedHandler,
    PaymentCapturedHandler,
    PaymentFailedHandler,
    PaymentRefundedHandler,
    WebhookReceivedHandler,
)
from src.services.invoice_service import InvoiceService
from src.services.subscription_service import SubscriptionService
from src.services.user_service import UserService
from src.services.payment_service import PaymentService
from src.services.notification_service import NotificationService
from src.plugins.registry import PaymentPluginRegistry


def register_payment_handlers(dispatcher: DomainEventDispatcher):
    """Register all payment event handlers."""

    # Initialize services
    invoice_service = InvoiceService()
    subscription_service = SubscriptionService()
    user_service = UserService()
    payment_service = PaymentService()
    notification_service = NotificationService()
    plugin_registry = PaymentPluginRegistry()

    # Checkout initiated handler
    checkout_handler = CheckoutInitiatedHandler(
        invoice_service=invoice_service,
        subscription_service=subscription_service,
        payment_service=payment_service,
        plugin_registry=plugin_registry,
    )
    dispatcher.register('checkout.initiated', checkout_handler)

    # Payment captured handler
    captured_handler = PaymentCapturedHandler(
        invoice_service=invoice_service,
        subscription_service=subscription_service,
        user_service=user_service,
        notification_service=notification_service,
    )
    dispatcher.register('payment.captured', captured_handler)

    # Payment failed handler
    failed_handler = PaymentFailedHandler(
        invoice_service=invoice_service,
        notification_service=notification_service,
    )
    dispatcher.register('payment.failed', failed_handler)

    # Payment refunded handler
    refunded_handler = PaymentRefundedHandler(
        invoice_service=invoice_service,
        subscription_service=subscription_service,
        notification_service=notification_service,
    )
    dispatcher.register('payment.refunded', refunded_handler)

    # Webhook received handler
    webhook_handler = WebhookReceivedHandler(
        plugin_registry=plugin_registry,
        event_dispatcher=dispatcher,
    )
    dispatcher.register('webhook.received', webhook_handler)
```

---

## Services Layer

Services contain the actual business logic. They are called by handlers.

### PaymentService

```python
"""Payment service - business logic for payment operations."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from src.plugins.base import IPaymentProviderAdapter


@dataclass
class CheckoutResult:
    """Result of checkout creation."""
    checkout_url: Optional[str]
    requires_redirect: bool
    payment_intent_id: Optional[str]
    provider: str


class PaymentService:
    """
    Payment service for payment operations.

    Contains business logic called by event handlers.
    """

    def __init__(self, plugin_registry=None, tax_service=None):
        self._plugin_registry = plugin_registry
        self._tax_service = tax_service

    def get_available_methods(
        self,
        currency: str,
        country: str,
    ) -> List[dict]:
        """Get available payment methods for context."""
        methods = []

        # Card payment
        methods.append({
            'type': 'card',
            'display_name': 'Credit/Debit Card',
            'providers': ['stripe', 'paypal'],
            'requires_redirect': True,
        })

        # Invoice/Manual
        methods.append({
            'type': 'invoice',
            'display_name': 'Pay by Invoice',
            'providers': ['manual'],
            'requires_redirect': False,
        })

        # BNPL for supported countries
        bnpl_countries = ['DE', 'AT', 'NL', 'SE', 'US']
        if country in bnpl_countries:
            methods.append({
                'type': 'bnpl',
                'display_name': 'Buy Now, Pay Later',
                'providers': ['klarna'],
                'requires_redirect': True,
            })

        return methods

    def create_checkout(
        self,
        plugin: IPaymentProviderAdapter,
        invoice,
        payment_method: str,
        success_url: str = None,
        cancel_url: str = None,
    ) -> CheckoutResult:
        """
        Create checkout session with provider.

        Args:
            plugin: Payment provider plugin
            invoice: Invoice to pay
            payment_method: Payment method type
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel

        Returns:
            CheckoutResult with checkout URL
        """
        if payment_method == 'invoice':
            # Invoice payment - no redirect needed
            return CheckoutResult(
                checkout_url=None,
                requires_redirect=False,
                payment_intent_id=None,
                provider=plugin.provider_name,
            )

        # Create checkout session with provider
        session = plugin.create_checkout_session(
            amount=invoice.gross_amount,
            currency=invoice.currency,
            success_url=success_url or f"/checkout/success?invoice={invoice.id}",
            cancel_url=cancel_url or f"/checkout/cancel?invoice={invoice.id}",
            metadata={
                'invoice_id': str(invoice.id),
                'user_id': str(invoice.user_id),
                'subscription_id': str(invoice.subscription_id),
            },
        )

        return CheckoutResult(
            checkout_url=session.checkout_url,
            requires_redirect=True,
            payment_intent_id=session.id,
            provider=plugin.provider_name,
        )

    def process_refund(
        self,
        plugin: IPaymentProviderAdapter,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ):
        """Process refund through provider."""
        return plugin.refund_payment(
            payment_intent_id=payment_intent_id,
            amount=amount,
            reason=reason,
        )
```

---

## Plugin System

### Plugin Interface

```python
"""Payment provider plugin interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from decimal import Decimal
from dataclasses import dataclass


class PaymentStatus:
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class PaymentIntent:
    """Provider-agnostic payment intent."""
    id: str
    provider: str
    provider_reference: str
    amount: Decimal
    currency: str
    status: str
    metadata: dict


@dataclass
class CheckoutSession:
    """Provider-agnostic checkout session."""
    id: str
    provider: str
    checkout_url: str
    expires_at: Optional[str]
    metadata: dict


@dataclass
class WebhookEvent:
    """Normalized webhook event."""
    id: str
    type: str  # payment.captured, payment.failed, etc.
    provider: str
    payment_intent_id: Optional[str]
    invoice_id: Optional[str]
    subscription_id: Optional[str]
    user_id: Optional[str]
    data: dict


class IPaymentProviderAdapter(ABC):
    """
    Payment provider adapter interface.

    All payment provider plugins must implement this interface.
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

    @abstractmethod
    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
    ) -> CheckoutSession:
        """Create hosted checkout session."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify webhook authenticity."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """Parse provider webhook into normalized event."""
        pass

    @abstractmethod
    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ):
        """Refund a captured payment."""
        pass

    @abstractmethod
    def get_payment_status(self, payment_intent_id: str) -> PaymentIntent:
        """Get current payment status."""
        pass
```

### Plugin Registry

```python
"""Payment plugin registry."""
from typing import Dict, Type, Optional, List
from src.plugins.base import IPaymentProviderAdapter


class PaymentPluginRegistry:
    """
    Registry for payment provider plugins.

    Manages plugin registration and instantiation.
    """

    _plugins: Dict[str, Type[IPaymentProviderAdapter]] = {}
    _instances: Dict[str, IPaymentProviderAdapter] = {}

    @classmethod
    def register(cls, provider_name: str):
        """Decorator to register a payment plugin."""
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
    def get_default_provider(cls, payment_method: str) -> Optional[str]:
        """Get default provider for payment method."""
        defaults = {
            'card': 'stripe',
            'invoice': 'manual',
            'wallet': 'paypal',
            'bnpl': 'klarna',
        }
        return defaults.get(payment_method)
```

---

## SDK Adapter Layer

The SDK Adapter Layer provides a unified abstraction for interacting with different payment provider SDKs. Each adapter wraps provider-specific SDK calls and includes built-in idempotency checking to prevent duplicate requests.

### Layer Responsibilities

| Component | Purpose |
|-----------|---------|
| `ISDKAdapter` | Common interface for all provider SDKs |
| `IdempotencyService` | Check/store idempotency keys in Redis |
| `BaseSDKAdapter` | Common HTTP client, retries, error handling |
| `StripeSDKAdapter` | Stripe API wrapper |
| `PayPalSDKAdapter` | PayPal REST API wrapper |
| `KlarnaSDKAdapter` | Klarna API wrapper |

### Idempotency Service

Prevents duplicate API calls by storing idempotency keys with their responses.

```python
"""Idempotency service for SDK requests."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any
from uuid import UUID
import hashlib
import json
import redis


@dataclass
class IdempotencyRecord:
    """Record of an idempotent request."""
    key: str
    provider: str
    operation: str
    request_hash: str
    response_data: Optional[dict]
    status: str  # pending, completed, failed
    created_at: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict:
        return {
            'key': self.key,
            'provider': self.provider,
            'operation': self.operation,
            'request_hash': self.request_hash,
            'response_data': self.response_data,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'IdempotencyRecord':
        return cls(
            key=data['key'],
            provider=data['provider'],
            operation=data['operation'],
            request_hash=data['request_hash'],
            response_data=data.get('response_data'),
            status=data['status'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
        )


class IdempotencyService:
    """
    Service for managing idempotency of SDK requests.

    Uses Redis for distributed storage with automatic expiration.
    Prevents duplicate payment operations across retries and failures.
    """

    # Default TTL for idempotency keys (24 hours)
    DEFAULT_TTL_HOURS = 24

    # Redis key prefix
    KEY_PREFIX = "idempotency:"

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def generate_key(
        self,
        provider: str,
        operation: str,
        invoice_id: UUID,
        **extra_params,
    ) -> str:
        """
        Generate idempotency key from operation parameters.

        Args:
            provider: Payment provider name
            operation: Operation type (create_checkout, capture, refund)
            invoice_id: Invoice being processed
            **extra_params: Additional parameters to include in key

        Returns:
            Unique idempotency key
        """
        # Create deterministic key from parameters
        key_data = {
            'provider': provider,
            'operation': operation,
            'invoice_id': str(invoice_id),
            **{k: str(v) for k, v in extra_params.items()},
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]

        return f"{provider}:{operation}:{key_hash}"

    def check_idempotency(self, key: str) -> Optional[IdempotencyRecord]:
        """
        Check if request was already processed.

        Args:
            key: Idempotency key

        Returns:
            IdempotencyRecord if found and not expired, None otherwise
        """
        redis_key = f"{self.KEY_PREFIX}{key}"
        data = self._redis.get(redis_key)

        if not data:
            return None

        record = IdempotencyRecord.from_dict(json.loads(data))

        if record.is_expired():
            self._redis.delete(redis_key)
            return None

        return record

    def start_request(
        self,
        key: str,
        provider: str,
        operation: str,
        request_data: dict,
        ttl_hours: int = None,
    ) -> bool:
        """
        Mark request as in-progress (pending).

        Uses Redis SETNX for atomic check-and-set.

        Args:
            key: Idempotency key
            provider: Provider name
            operation: Operation type
            request_data: Request parameters for hash
            ttl_hours: Time to live in hours

        Returns:
            True if request started, False if already exists
        """
        redis_key = f"{self.KEY_PREFIX}{key}"
        ttl = ttl_hours or self.DEFAULT_TTL_HOURS

        record = IdempotencyRecord(
            key=key,
            provider=provider,
            operation=operation,
            request_hash=hashlib.sha256(
                json.dumps(request_data, sort_keys=True).encode()
            ).hexdigest(),
            response_data=None,
            status='pending',
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=ttl),
        )

        # Atomic set-if-not-exists
        success = self._redis.setnx(redis_key, json.dumps(record.to_dict()))

        if success:
            # Set expiration
            self._redis.expire(redis_key, int(ttl * 3600))

        return success

    def complete_request(
        self,
        key: str,
        response_data: dict,
        status: str = 'completed',
    ) -> None:
        """
        Mark request as completed with response.

        Args:
            key: Idempotency key
            response_data: Response to cache
            status: Final status (completed, failed)
        """
        redis_key = f"{self.KEY_PREFIX}{key}"
        data = self._redis.get(redis_key)

        if not data:
            return

        record = IdempotencyRecord.from_dict(json.loads(data))
        record.response_data = response_data
        record.status = status

        # Update with remaining TTL
        ttl = self._redis.ttl(redis_key)
        self._redis.setex(redis_key, ttl, json.dumps(record.to_dict()))

    def delete_key(self, key: str) -> None:
        """Delete idempotency key (for cleanup or retry)."""
        redis_key = f"{self.KEY_PREFIX}{key}"
        self._redis.delete(redis_key)

    def is_duplicate(self, key: str, request_data: dict) -> tuple[bool, Optional[dict]]:
        """
        Check if this is a duplicate request.

        Args:
            key: Idempotency key
            request_data: Current request parameters

        Returns:
            Tuple of (is_duplicate, cached_response)
            - If duplicate with completed status: (True, response_data)
            - If duplicate with pending status: (True, None)
            - If not duplicate: (False, None)
        """
        record = self.check_idempotency(key)

        if not record:
            return False, None

        # Verify request hash matches
        current_hash = hashlib.sha256(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()

        if current_hash != record.request_hash:
            # Same key but different parameters - this is an error
            raise ValueError(
                f"Idempotency key collision: same key '{key}' "
                f"but different request parameters"
            )

        if record.status == 'completed':
            return True, record.response_data
        elif record.status == 'failed':
            # Allow retry of failed requests
            self.delete_key(key)
            return False, None
        else:
            # Still pending - return duplicate signal
            return True, None
```

### SDK Adapter Interface

```python
"""SDK Adapter interface for payment providers."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class SDKResponse:
    """Standardized SDK response."""
    success: bool
    provider: str
    operation: str
    data: Dict[str, Any]
    error: Optional[str] = None
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None


@dataclass
class SDKConfig:
    """SDK configuration."""
    api_key: str
    api_secret: Optional[str] = None
    sandbox: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class ISDKAdapter(ABC):
    """
    Interface for payment provider SDK adapters.

    All SDK adapters must implement this interface.
    Handles low-level API communication with idempotency support.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: dict,
        idempotency_key: str,
    ) -> SDKResponse:
        """Create payment intent with provider."""
        pass

    @abstractmethod
    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
        idempotency_key: str,
        line_items: Optional[list] = None,
    ) -> SDKResponse:
        """Create hosted checkout session."""
        pass

    @abstractmethod
    def capture_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal],
        idempotency_key: str,
    ) -> SDKResponse:
        """Capture authorized payment."""
        pass

    @abstractmethod
    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal],
        reason: Optional[str],
        idempotency_key: str,
    ) -> SDKResponse:
        """Refund captured payment."""
        pass

    @abstractmethod
    def get_payment(self, payment_intent_id: str) -> SDKResponse:
        """Get payment details."""
        pass

    @abstractmethod
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify webhook signature."""
        pass
```

### Base SDK Adapter

```python
"""Base SDK adapter with common functionality."""
import time
import logging
from typing import Optional, Callable
from decimal import Decimal
import httpx

from src.sdk.interface import ISDKAdapter, SDKResponse, SDKConfig
from src.services.idempotency_service import IdempotencyService


logger = logging.getLogger(__name__)


class BaseSDKAdapter(ISDKAdapter):
    """
    Base SDK adapter with common functionality.

    Provides:
    - HTTP client with retries
    - Idempotency checking
    - Error handling and logging
    - Response normalization
    """

    def __init__(
        self,
        config: SDKConfig,
        idempotency_service: IdempotencyService,
    ):
        self._config = config
        self._idempotency = idempotency_service
        self._http_client = self._create_http_client()

    def _create_http_client(self) -> httpx.Client:
        """Create configured HTTP client."""
        return httpx.Client(
            timeout=self._config.timeout,
            headers=self._get_default_headers(),
        )

    def _get_default_headers(self) -> dict:
        """Get default headers. Override in subclasses."""
        return {
            'Content-Type': 'application/json',
            'User-Agent': f'VBWD-SDK/1.0 ({self.provider_name})',
        }

    def _get_base_url(self) -> str:
        """Get API base URL. Override in subclasses."""
        raise NotImplementedError

    def _execute_with_idempotency(
        self,
        operation: str,
        idempotency_key: str,
        request_data: dict,
        execute_fn: Callable[[], SDKResponse],
    ) -> SDKResponse:
        """
        Execute operation with idempotency checking.

        Args:
            operation: Operation name for logging
            idempotency_key: Key for idempotency
            request_data: Request parameters
            execute_fn: Function to execute if not duplicate

        Returns:
            SDKResponse (cached or fresh)
        """
        # Check for duplicate
        is_dup, cached = self._idempotency.is_duplicate(idempotency_key, request_data)

        if is_dup and cached:
            logger.info(f"Idempotent response for {operation}: {idempotency_key}")
            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation=operation,
                data=cached,
                idempotency_key=idempotency_key,
            )

        if is_dup and not cached:
            # Request still pending - wait and retry
            logger.warning(f"Duplicate pending request for {operation}: {idempotency_key}")
            time.sleep(2)
            return self._execute_with_idempotency(
                operation, idempotency_key, request_data, execute_fn
            )

        # Start new request
        if not self._idempotency.start_request(
            key=idempotency_key,
            provider=self.provider_name,
            operation=operation,
            request_data=request_data,
        ):
            # Race condition - another process started
            return self._execute_with_idempotency(
                operation, idempotency_key, request_data, execute_fn
            )

        try:
            # Execute with retries
            response = self._execute_with_retries(execute_fn)

            # Cache successful response
            if response.success:
                self._idempotency.complete_request(
                    key=idempotency_key,
                    response_data=response.data,
                    status='completed',
                )
            else:
                self._idempotency.complete_request(
                    key=idempotency_key,
                    response_data={'error': response.error},
                    status='failed',
                )

            response.idempotency_key = idempotency_key
            return response

        except Exception as e:
            self._idempotency.complete_request(
                key=idempotency_key,
                response_data={'error': str(e)},
                status='failed',
            )
            raise

    def _execute_with_retries(
        self,
        execute_fn: Callable[[], SDKResponse],
    ) -> SDKResponse:
        """Execute function with retry logic."""
        last_error = None

        for attempt in range(self._config.max_retries):
            try:
                return execute_fn()
            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    return SDKResponse(
                        success=False,
                        provider=self.provider_name,
                        operation='unknown',
                        data={},
                        error=str(e),
                        error_code=str(e.response.status_code),
                        raw_response=e.response.json() if e.response.content else None,
                    )
                last_error = e
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e

            # Wait before retry with exponential backoff
            if attempt < self._config.max_retries - 1:
                delay = self._config.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Retry {attempt + 1}/{self._config.max_retries} "
                    f"after {delay}s: {last_error}"
                )
                time.sleep(delay)

        # All retries failed
        return SDKResponse(
            success=False,
            provider=self.provider_name,
            operation='unknown',
            data={},
            error=f"All retries failed: {last_error}",
            error_code='RETRY_EXHAUSTED',
        )
```

### Stripe SDK Adapter

```python
"""Stripe SDK adapter."""
from typing import Optional
from decimal import Decimal
import stripe

from src.sdk.base import BaseSDKAdapter, SDKResponse, SDKConfig
from src.services.idempotency_service import IdempotencyService


class StripeSDKAdapter(BaseSDKAdapter):
    """
    Stripe SDK adapter.

    Wraps Stripe Python SDK with idempotency support.
    """

    def __init__(
        self,
        config: SDKConfig,
        idempotency_service: IdempotencyService,
    ):
        super().__init__(config, idempotency_service)
        stripe.api_key = config.api_key

    @property
    def provider_name(self) -> str:
        return 'stripe'

    def _get_base_url(self) -> str:
        return 'https://api.stripe.com/v1'

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: dict,
        idempotency_key: str,
    ) -> SDKResponse:
        """Create Stripe PaymentIntent."""
        request_data = {
            'amount': int(amount * 100),  # Stripe uses cents
            'currency': currency.lower(),
            'metadata': metadata,
        }

        def execute():
            intent = stripe.PaymentIntent.create(
                amount=request_data['amount'],
                currency=request_data['currency'],
                metadata=request_data['metadata'],
                idempotency_key=idempotency_key,  # Stripe native idempotency
            )
            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='create_payment_intent',
                data={
                    'id': intent.id,
                    'client_secret': intent.client_secret,
                    'status': intent.status,
                    'amount': intent.amount,
                    'currency': intent.currency,
                },
                raw_response=dict(intent),
            )

        return self._execute_with_idempotency(
            operation='create_payment_intent',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
        idempotency_key: str,
        line_items: Optional[list] = None,
    ) -> SDKResponse:
        """Create Stripe Checkout Session."""
        request_data = {
            'amount': int(amount * 100),
            'currency': currency.lower(),
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': metadata,
        }

        def execute():
            session = stripe.checkout.Session.create(
                mode='payment',
                line_items=line_items or [{
                    'price_data': {
                        'currency': request_data['currency'],
                        'unit_amount': request_data['amount'],
                        'product_data': {
                            'name': 'Subscription',
                        },
                    },
                    'quantity': 1,
                }],
                success_url=request_data['success_url'],
                cancel_url=request_data['cancel_url'],
                metadata=request_data['metadata'],
                idempotency_key=idempotency_key,
            )
            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='create_checkout_session',
                data={
                    'id': session.id,
                    'url': session.url,
                    'status': session.status,
                    'expires_at': session.expires_at,
                },
                raw_response=dict(session),
            )

        return self._execute_with_idempotency(
            operation='create_checkout_session',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def capture_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal],
        idempotency_key: str,
    ) -> SDKResponse:
        """Capture Stripe PaymentIntent."""
        request_data = {
            'payment_intent_id': payment_intent_id,
            'amount': int(amount * 100) if amount else None,
        }

        def execute():
            capture_params = {}
            if request_data['amount']:
                capture_params['amount_to_capture'] = request_data['amount']

            intent = stripe.PaymentIntent.capture(
                payment_intent_id,
                idempotency_key=idempotency_key,
                **capture_params,
            )
            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='capture_payment',
                data={
                    'id': intent.id,
                    'status': intent.status,
                    'amount_captured': intent.amount_received,
                },
                raw_response=dict(intent),
            )

        return self._execute_with_idempotency(
            operation='capture_payment',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal],
        reason: Optional[str],
        idempotency_key: str,
    ) -> SDKResponse:
        """Refund Stripe payment."""
        request_data = {
            'payment_intent': payment_intent_id,
            'amount': int(amount * 100) if amount else None,
            'reason': reason,
        }

        def execute():
            refund_params = {'payment_intent': payment_intent_id}
            if request_data['amount']:
                refund_params['amount'] = request_data['amount']
            if request_data['reason']:
                refund_params['reason'] = request_data['reason']

            refund = stripe.Refund.create(
                idempotency_key=idempotency_key,
                **refund_params,
            )
            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='refund_payment',
                data={
                    'id': refund.id,
                    'status': refund.status,
                    'amount': refund.amount,
                },
                raw_response=dict(refund),
            )

        return self._execute_with_idempotency(
            operation='refund_payment',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def get_payment(self, payment_intent_id: str) -> SDKResponse:
        """Get Stripe PaymentIntent."""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='get_payment',
                data={
                    'id': intent.id,
                    'status': intent.status,
                    'amount': intent.amount,
                    'currency': intent.currency,
                },
                raw_response=dict(intent),
            )
        except stripe.error.StripeError as e:
            return SDKResponse(
                success=False,
                provider=self.provider_name,
                operation='get_payment',
                data={},
                error=str(e),
                error_code=e.code if hasattr(e, 'code') else None,
            )

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify Stripe webhook signature."""
        try:
            stripe.Webhook.construct_event(payload, signature, secret)
            return True
        except stripe.error.SignatureVerificationError:
            return False
```

### PayPal SDK Adapter

```python
"""PayPal SDK adapter."""
from typing import Optional
from decimal import Decimal
import httpx

from src.sdk.base import BaseSDKAdapter, SDKResponse, SDKConfig
from src.services.idempotency_service import IdempotencyService


class PayPalSDKAdapter(BaseSDKAdapter):
    """
    PayPal SDK adapter.

    Uses PayPal REST API with OAuth2 authentication.
    """

    def __init__(
        self,
        config: SDKConfig,
        idempotency_service: IdempotencyService,
    ):
        super().__init__(config, idempotency_service)
        self._access_token = None
        self._token_expires_at = None

    @property
    def provider_name(self) -> str:
        return 'paypal'

    def _get_base_url(self) -> str:
        if self._config.sandbox:
            return 'https://api-m.sandbox.paypal.com'
        return 'https://api-m.paypal.com'

    def _get_access_token(self) -> str:
        """Get OAuth2 access token (with caching)."""
        import time

        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at - 60:
                return self._access_token

        response = self._http_client.post(
            f"{self._get_base_url()}/v1/oauth2/token",
            auth=(self._config.api_key, self._config.api_secret),
            data={'grant_type': 'client_credentials'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data['access_token']
        self._token_expires_at = time.time() + data['expires_in']

        return self._access_token

    def _get_auth_headers(self) -> dict:
        """Get headers with authorization."""
        return {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json',
        }

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: dict,
        idempotency_key: str,
    ) -> SDKResponse:
        """Create PayPal Order."""
        request_data = {
            'amount': str(amount),
            'currency': currency.upper(),
            'metadata': metadata,
        }

        def execute():
            response = self._http_client.post(
                f"{self._get_base_url()}/v2/checkout/orders",
                headers={
                    **self._get_auth_headers(),
                    'PayPal-Request-Id': idempotency_key,
                },
                json={
                    'intent': 'CAPTURE',
                    'purchase_units': [{
                        'amount': {
                            'currency_code': request_data['currency'],
                            'value': request_data['amount'],
                        },
                        'custom_id': metadata.get('invoice_id', ''),
                    }],
                },
            )
            response.raise_for_status()
            data = response.json()

            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='create_payment_intent',
                data={
                    'id': data['id'],
                    'status': data['status'],
                    'links': {
                        link['rel']: link['href']
                        for link in data.get('links', [])
                    },
                },
                raw_response=data,
            )

        return self._execute_with_idempotency(
            operation='create_payment_intent',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
        idempotency_key: str,
        line_items: Optional[list] = None,
    ) -> SDKResponse:
        """Create PayPal Order with approval URL."""
        request_data = {
            'amount': str(amount),
            'currency': currency.upper(),
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': metadata,
        }

        def execute():
            response = self._http_client.post(
                f"{self._get_base_url()}/v2/checkout/orders",
                headers={
                    **self._get_auth_headers(),
                    'PayPal-Request-Id': idempotency_key,
                },
                json={
                    'intent': 'CAPTURE',
                    'purchase_units': [{
                        'amount': {
                            'currency_code': request_data['currency'],
                            'value': request_data['amount'],
                        },
                        'custom_id': metadata.get('invoice_id', ''),
                    }],
                    'payment_source': {
                        'paypal': {
                            'experience_context': {
                                'return_url': request_data['success_url'],
                                'cancel_url': request_data['cancel_url'],
                            },
                        },
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            # Find approval URL
            approval_url = None
            for link in data.get('links', []):
                if link['rel'] == 'payer-action':
                    approval_url = link['href']
                    break

            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='create_checkout_session',
                data={
                    'id': data['id'],
                    'url': approval_url,
                    'status': data['status'],
                },
                raw_response=data,
            )

        return self._execute_with_idempotency(
            operation='create_checkout_session',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def capture_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal],
        idempotency_key: str,
    ) -> SDKResponse:
        """Capture PayPal Order."""
        request_data = {
            'order_id': payment_intent_id,
            'amount': str(amount) if amount else None,
        }

        def execute():
            response = self._http_client.post(
                f"{self._get_base_url()}/v2/checkout/orders/{payment_intent_id}/capture",
                headers={
                    **self._get_auth_headers(),
                    'PayPal-Request-Id': idempotency_key,
                },
            )
            response.raise_for_status()
            data = response.json()

            capture = data['purchase_units'][0]['payments']['captures'][0]

            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='capture_payment',
                data={
                    'id': data['id'],
                    'status': data['status'],
                    'capture_id': capture['id'],
                    'amount': capture['amount']['value'],
                },
                raw_response=data,
            )

        return self._execute_with_idempotency(
            operation='capture_payment',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal],
        reason: Optional[str],
        idempotency_key: str,
    ) -> SDKResponse:
        """Refund PayPal capture."""
        request_data = {
            'capture_id': payment_intent_id,
            'amount': str(amount) if amount else None,
            'reason': reason,
        }

        def execute():
            refund_body = {}
            if request_data['amount']:
                # Get capture to find currency
                capture_resp = self._http_client.get(
                    f"{self._get_base_url()}/v2/payments/captures/{payment_intent_id}",
                    headers=self._get_auth_headers(),
                )
                capture = capture_resp.json()
                refund_body['amount'] = {
                    'value': request_data['amount'],
                    'currency_code': capture['amount']['currency_code'],
                }
            if request_data['reason']:
                refund_body['note_to_payer'] = request_data['reason']

            response = self._http_client.post(
                f"{self._get_base_url()}/v2/payments/captures/{payment_intent_id}/refund",
                headers={
                    **self._get_auth_headers(),
                    'PayPal-Request-Id': idempotency_key,
                },
                json=refund_body if refund_body else None,
            )
            response.raise_for_status()
            data = response.json()

            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='refund_payment',
                data={
                    'id': data['id'],
                    'status': data['status'],
                    'amount': data['amount']['value'] if 'amount' in data else None,
                },
                raw_response=data,
            )

        return self._execute_with_idempotency(
            operation='refund_payment',
            idempotency_key=idempotency_key,
            request_data=request_data,
            execute_fn=execute,
        )

    def get_payment(self, payment_intent_id: str) -> SDKResponse:
        """Get PayPal Order."""
        try:
            response = self._http_client.get(
                f"{self._get_base_url()}/v2/checkout/orders/{payment_intent_id}",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data = response.json()

            return SDKResponse(
                success=True,
                provider=self.provider_name,
                operation='get_payment',
                data={
                    'id': data['id'],
                    'status': data['status'],
                    'amount': data['purchase_units'][0]['amount']['value'],
                    'currency': data['purchase_units'][0]['amount']['currency_code'],
                },
                raw_response=data,
            )
        except httpx.HTTPStatusError as e:
            return SDKResponse(
                success=False,
                provider=self.provider_name,
                operation='get_payment',
                data={},
                error=str(e),
                error_code=str(e.response.status_code),
            )

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify PayPal webhook signature."""
        # PayPal webhook verification requires calling their API
        # This is a simplified version
        try:
            response = self._http_client.post(
                f"{self._get_base_url()}/v1/notifications/verify-webhook-signature",
                headers=self._get_auth_headers(),
                json={
                    'webhook_id': secret,
                    'webhook_event': payload.decode() if isinstance(payload, bytes) else payload,
                },
            )
            data = response.json()
            return data.get('verification_status') == 'SUCCESS'
        except Exception:
            return False
```

### SDK Adapter Registry

```python
"""SDK adapter registry and factory."""
from typing import Dict, Type, Optional
import redis

from src.sdk.interface import ISDKAdapter, SDKConfig
from src.sdk.stripe_adapter import StripeSDKAdapter
from src.sdk.paypal_adapter import PayPalSDKAdapter
from src.services.idempotency_service import IdempotencyService


class SDKAdapterRegistry:
    """
    Registry for SDK adapters.

    Creates and caches SDK adapter instances.
    """

    _adapters: Dict[str, Type[ISDKAdapter]] = {
        'stripe': StripeSDKAdapter,
        'paypal': PayPalSDKAdapter,
    }
    _instances: Dict[str, ISDKAdapter] = {}
    _idempotency_service: Optional[IdempotencyService] = None

    @classmethod
    def initialize(cls, redis_url: str) -> None:
        """Initialize registry with Redis connection."""
        redis_client = redis.from_url(redis_url)
        cls._idempotency_service = IdempotencyService(redis_client)

    @classmethod
    def register(cls, provider: str, adapter_class: Type[ISDKAdapter]) -> None:
        """Register new SDK adapter."""
        cls._adapters[provider] = adapter_class

    @classmethod
    def get_adapter(
        cls,
        provider: str,
        config: SDKConfig,
    ) -> Optional[ISDKAdapter]:
        """Get SDK adapter instance."""
        if provider not in cls._adapters:
            return None

        cache_key = f"{provider}:{config.api_key[:8]}"

        if cache_key not in cls._instances:
            if not cls._idempotency_service:
                raise RuntimeError("SDKAdapterRegistry not initialized")

            adapter_class = cls._adapters[provider]
            cls._instances[cache_key] = adapter_class(
                config=config,
                idempotency_service=cls._idempotency_service,
            )

        return cls._instances[cache_key]
```

### Plugin Integration with SDK Adapter

Plugins use SDK adapters for provider communication:

```python
"""Stripe plugin using SDK adapter."""
from typing import Optional, List
from decimal import Decimal

from src.plugins.base import IPaymentProviderAdapter, CheckoutSession, WebhookEvent
from src.sdk.registry import SDKAdapterRegistry, SDKConfig
from src.services.idempotency_service import IdempotencyService


class StripePlugin(IPaymentProviderAdapter):
    """
    Stripe payment provider plugin.

    Uses StripeSDKAdapter for API communication.
    """

    def __init__(self, api_key: str, webhook_secret: str, sandbox: bool = True):
        self._webhook_secret = webhook_secret
        self._config = SDKConfig(
            api_key=api_key,
            sandbox=sandbox,
        )
        self._sdk = SDKAdapterRegistry.get_adapter('stripe', self._config)

    @property
    def provider_name(self) -> str:
        return 'stripe'

    @property
    def supported_payment_methods(self) -> List[str]:
        return ['card', 'wallet']

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
    ) -> CheckoutSession:
        """Create Stripe checkout session via SDK adapter."""
        # Generate idempotency key
        idempotency_key = self._sdk._idempotency.generate_key(
            provider='stripe',
            operation='create_checkout_session',
            invoice_id=metadata.get('invoice_id'),
        )

        # Call SDK adapter
        response = self._sdk.create_checkout_session(
            amount=amount,
            currency=currency,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

        if not response.success:
            raise Exception(response.error)

        return CheckoutSession(
            id=response.data['id'],
            provider=self.provider_name,
            checkout_url=response.data['url'],
            expires_at=response.data.get('expires_at'),
            metadata=metadata,
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify Stripe webhook via SDK adapter."""
        return self._sdk.verify_webhook(payload, signature, self._webhook_secret)

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """Parse Stripe webhook payload."""
        event_type = payload.get('type', '')
        data = payload.get('data', {}).get('object', {})

        # Map Stripe event types to normalized types
        type_map = {
            'checkout.session.completed': 'payment.captured',
            'payment_intent.succeeded': 'payment.captured',
            'payment_intent.payment_failed': 'payment.failed',
            'charge.refunded': 'payment.refunded',
        }

        return WebhookEvent(
            id=payload.get('id'),
            type=type_map.get(event_type, event_type),
            provider=self.provider_name,
            payment_intent_id=data.get('payment_intent') or data.get('id'),
            invoice_id=data.get('metadata', {}).get('invoice_id'),
            subscription_id=data.get('metadata', {}).get('subscription_id'),
            user_id=data.get('metadata', {}).get('user_id'),
            data=data,
        )

    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ):
        """Refund via SDK adapter."""
        idempotency_key = self._sdk._idempotency.generate_key(
            provider='stripe',
            operation='refund',
            invoice_id=payment_intent_id,  # Use payment ID as reference
        )

        return self._sdk.refund_payment(
            payment_intent_id=payment_intent_id,
            amount=amount,
            reason=reason,
            idempotency_key=idempotency_key,
        )

    def get_payment_status(self, payment_intent_id: str):
        """Get payment status via SDK adapter."""
        return self._sdk.get_payment(payment_intent_id)
```

---

## Webhook System

The webhook system provides a base infrastructure for receiving and processing webhooks from payment providers. It's designed to be extended by payment modules (Stripe, PayPal, Klarna, etc.).

### Webhook Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEBHOOK FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  External Provider (Stripe/PayPal/Klarna)                                   │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Webhook Endpoint                                  │    │
│  │              POST /api/v1/webhooks/{provider}                       │    │
│  │                                                                      │    │
│  │  1. Extract raw payload and headers                                 │    │
│  │  2. Get provider's webhook handler                                  │    │
│  │  3. Delegate to handler                                             │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   WebhookService                                     │    │
│  │                                                                      │    │
│  │  1. Check idempotency (prevent duplicate processing)                │    │
│  │  2. Store raw webhook for audit                                     │    │
│  │  3. Dispatch to provider handler                                    │    │
│  │  4. Update webhook status                                           │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              Provider Webhook Handlers (Extensible)                  │    │
│  │                                                                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │   Stripe    │  │   PayPal    │  │   Klarna    │                  │    │
│  │  │   Handler   │  │   Handler   │  │   Handler   │                  │    │
│  │  │             │  │             │  │             │                  │    │
│  │  │ - Verify    │  │ - Verify    │  │ - Verify    │                  │    │
│  │  │ - Parse     │  │ - Parse     │  │ - Parse     │                  │    │
│  │  │ - Normalize │  │ - Normalize │  │ - Normalize │                  │    │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │    │
│  │         │                │                │                          │    │
│  └─────────┼────────────────┼────────────────┼──────────────────────────┘    │
│            │                │                │                               │
│            └────────────────┼────────────────┘                               │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   Domain Event Dispatcher                            │    │
│  │                                                                      │    │
│  │  Emits normalized domain events:                                    │    │
│  │  - PaymentCapturedEvent                                             │    │
│  │  - PaymentFailedEvent                                               │    │
│  │  - PaymentRefundedEvent                                             │    │
│  │  - SubscriptionRenewedEvent                                         │    │
│  │  - etc.                                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Webhook Database Model

The `Webhook` model is stored with other models in `src/models/` and managed via Alembic migrations.

```python
"""Webhook model - src/models/webhook.py"""
from datetime import datetime
from typing import Optional
from uuid import UUID
import enum

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Enum as SQLEnum,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class WebhookStatus(enum.Enum):
    """Webhook processing status."""
    RECEIVED = "received"      # Just received, not processed
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"    # Successfully processed
    FAILED = "failed"          # Processing failed
    IGNORED = "ignored"        # Event type not handled


class Webhook(BaseModel):
    """
    Persistent record of received webhook.

    Stored for audit trail, debugging, and retry capability.
    """
    __tablename__ = 'webhooks'

    # Provider identification
    provider = Column(String(50), nullable=False, index=True)
    event_id = Column(String(255), nullable=False)  # Provider's event ID
    event_type = Column(String(100), nullable=False, index=True)

    # Raw data storage
    payload = Column(JSONB, nullable=False, default={})
    headers = Column(JSONB, nullable=False, default={})
    signature = Column(Text, nullable=True)

    # Processing status
    status = Column(
        SQLEnum(WebhookStatus),
        nullable=False,
        default=WebhookStatus.RECEIVED,
        index=True
    )
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    processed_at = Column(DateTime, nullable=True)

    # Linked resources (populated after parsing)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey('invoices.id'), nullable=True)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    invoice = relationship('Invoice', back_populates='webhooks')
    subscription = relationship('Subscription', back_populates='webhooks')
    user = relationship('User', back_populates='webhooks')

    # Composite index for idempotency lookup
    __table_args__ = (
        Index('ix_webhooks_provider_event_id', 'provider', 'event_id', unique=True),
        Index('ix_webhooks_status_retry', 'status', 'retry_count'),
    )

    def can_retry(self) -> bool:
        """Check if webhook can be retried."""
        return (
            self.status == WebhookStatus.FAILED
            and self.retry_count < self.max_retries
        )

    def mark_processing(self) -> None:
        """Mark webhook as being processed."""
        self.status = WebhookStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark webhook as successfully processed."""
        self.status = WebhookStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark webhook as failed with error message."""
        self.status = WebhookStatus.FAILED
        self.error_message = error
        self.retry_count += 1

    def mark_ignored(self, reason: str = None) -> None:
        """Mark webhook as ignored (unhandled event type)."""
        self.status = WebhookStatus.IGNORED
        self.error_message = reason

    def __repr__(self):
        return f"<Webhook {self.provider}:{self.event_id} [{self.status.value}]>"
```

### Alembic Migration

```python
"""Add webhook table

Revision ID: add_webhook_table
Revises: e3bb91853ab7
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_webhook_table'
down_revision = 'e3bb91853ab7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'webhooks',
        # Base columns (from BaseModel)
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Provider identification
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),

        # Raw data
        sa.Column('payload', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('headers', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('signature', sa.Text(), nullable=True),

        # Processing status
        sa.Column('status', sa.Enum('RECEIVED', 'PROCESSING', 'COMPLETED', 'FAILED', 'IGNORED', name='webhookstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('processed_at', sa.DateTime(), nullable=True),

        # Foreign keys
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Constraints
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Indexes
    op.create_index('ix_webhooks_provider', 'webhooks', ['provider'])
    op.create_index('ix_webhooks_event_type', 'webhooks', ['event_type'])
    op.create_index('ix_webhooks_status', 'webhooks', ['status'])
    op.create_index('ix_webhooks_provider_event_id', 'webhooks', ['provider', 'event_id'], unique=True)
    op.create_index('ix_webhooks_status_retry', 'webhooks', ['status', 'retry_count'])
    op.create_index('ix_webhooks_created_at', 'webhooks', ['created_at'])


def downgrade() -> None:
    op.drop_table('webhooks')
    op.execute('DROP TYPE IF EXISTS webhookstatus')
```

### Webhook Repository

```python
"""Webhook repository - src/repositories/webhook_repository.py"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import and_

from src.models.webhook import Webhook, WebhookStatus
from src.repositories.base import BaseRepository


class WebhookRepository(BaseRepository[Webhook]):
    """Repository for Webhook entities."""

    def __init__(self, session):
        super().__init__(Webhook, session)

    def find_by_event_id(self, provider: str, event_id: str) -> Optional[Webhook]:
        """Find webhook by provider and event ID."""
        return self._session.query(Webhook).filter(
            and_(
                Webhook.provider == provider,
                Webhook.event_id == event_id,
            )
        ).first()

    def find_by_provider(
        self,
        provider: str,
        status: Optional[WebhookStatus] = None,
        limit: int = 100,
    ) -> List[Webhook]:
        """Find webhooks by provider with optional status filter."""
        query = self._session.query(Webhook).filter(
            Webhook.provider == provider
        )
        if status:
            query = query.filter(Webhook.status == status)
        return query.order_by(Webhook.created_at.desc()).limit(limit).all()

    def find_failed_retryable(
        self,
        provider: Optional[str] = None,
        limit: int = 100,
    ) -> List[Webhook]:
        """Find failed webhooks that can be retried."""
        query = self._session.query(Webhook).filter(
            and_(
                Webhook.status == WebhookStatus.FAILED,
                Webhook.retry_count < Webhook.max_retries,
            )
        )
        if provider:
            query = query.filter(Webhook.provider == provider)
        return query.order_by(Webhook.created_at.asc()).limit(limit).all()

    def find_stuck_processing(
        self,
        older_than_minutes: int = 30,
    ) -> List[Webhook]:
        """Find webhooks stuck in PROCESSING status."""
        threshold = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        return self._session.query(Webhook).filter(
            and_(
                Webhook.status == WebhookStatus.PROCESSING,
                Webhook.updated_at < threshold,
            )
        ).all()

    def count_by_status(self, provider: Optional[str] = None) -> dict:
        """Get count of webhooks grouped by status."""
        from sqlalchemy import func

        query = self._session.query(
            Webhook.status,
            func.count(Webhook.id).label('count')
        )
        if provider:
            query = query.filter(Webhook.provider == provider)
        results = query.group_by(Webhook.status).all()

        return {status.value: count for status, count in results}

    def cleanup_old_completed(self, days: int = 30) -> int:
        """Delete completed webhooks older than N days."""
        threshold = datetime.utcnow() - timedelta(days=days)
        result = self._session.query(Webhook).filter(
            and_(
                Webhook.status == WebhookStatus.COMPLETED,
                Webhook.created_at < threshold,
            )
        ).delete()
        self._session.commit()
        return result
```

### Normalized Webhook Event (DTO)

The `NormalizedWebhookEvent` is a data transfer object (not persisted), used for passing parsed webhook data between components.

```python
"""Webhook DTOs - src/webhooks/dto.py"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class NormalizedWebhookEvent:
    """
    Provider-agnostic webhook event.

    All provider-specific webhooks are normalized to this format
    before being converted to domain events.
    """
    # Event identification
    event_id: str                    # Provider's event ID
    event_type: str                  # Normalized event type
    provider: str                    # Provider name

    # Timestamps
    timestamp: datetime              # When event occurred
    received_at: datetime            # When we received it

    # Payment context
    payment_intent_id: Optional[str] = None
    checkout_session_id: Optional[str] = None
    charge_id: Optional[str] = None
    refund_id: Optional[str] = None

    # Business context (from metadata)
    invoice_id: Optional[UUID] = None
    subscription_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    # Financial data
    amount: Optional[int] = None     # Amount in smallest currency unit
    currency: Optional[str] = None

    # Status and errors
    status: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None

    # Raw data for debugging
    raw_data: Dict[str, Any] = field(default_factory=dict)


# Normalized event types
class WebhookEventType:
    """Standard webhook event types across all providers."""
    # Payment events
    PAYMENT_CREATED = "payment.created"
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_CANCELLED = "payment.cancelled"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_PARTIALLY_REFUNDED = "payment.partially_refunded"
    PAYMENT_DISPUTED = "payment.disputed"

    # Checkout events
    CHECKOUT_COMPLETED = "checkout.completed"
    CHECKOUT_EXPIRED = "checkout.expired"

    # Subscription events (for recurring)
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "subscription.expired"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
```

### Webhook Handler Interface

```python
"""Base webhook handler interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class WebhookVerificationResult:
    """Result of webhook signature verification."""
    valid: bool
    error: Optional[str] = None


@dataclass
class WebhookProcessingResult:
    """Result of webhook processing."""
    success: bool
    event_type: Optional[str] = None
    domain_event_emitted: bool = False
    error: Optional[str] = None
    should_retry: bool = False


class IWebhookHandler(ABC):
    """
    Interface for provider-specific webhook handlers.

    Each payment provider must implement this interface.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (stripe, paypal, klarna)."""
        pass

    @property
    @abstractmethod
    def supported_events(self) -> List[str]:
        """List of provider event types this handler supports."""
        pass

    @abstractmethod
    def verify_signature(
        self,
        payload: bytes,
        headers: dict,
        secret: str,
    ) -> WebhookVerificationResult:
        """
        Verify webhook signature.

        Args:
            payload: Raw request body
            headers: Request headers
            secret: Webhook signing secret

        Returns:
            Verification result with validity and error
        """
        pass

    @abstractmethod
    def parse_event(
        self,
        payload: dict,
        headers: dict,
    ) -> NormalizedWebhookEvent:
        """
        Parse provider webhook into normalized event.

        Args:
            payload: Parsed JSON payload
            headers: Request headers

        Returns:
            NormalizedWebhookEvent
        """
        pass

    @abstractmethod
    def get_event_id(self, payload: dict) -> str:
        """Extract provider's event ID for idempotency."""
        pass

    @abstractmethod
    def get_event_type(self, payload: dict) -> str:
        """Extract provider's event type."""
        pass

    def should_process(self, event_type: str) -> bool:
        """Check if this event type should be processed."""
        return event_type in self.supported_events
```

### Webhook Service

```python
"""Webhook service - core webhook processing logic."""
import logging
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime

from src.webhooks.models import (
    WebhookRecord,
    WebhookStatus,
    NormalizedWebhookEvent,
    WebhookEventType,
)
from src.webhooks.handlers.base import (
    IWebhookHandler,
    WebhookProcessingResult,
)
from src.webhooks.repository import WebhookRepository
from src.events.domain import DomainEventDispatcher
from src.events.payment_events import (
    PaymentCapturedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
    CheckoutCompletedEvent,
)
from src.services.idempotency_service import IdempotencyService


logger = logging.getLogger(__name__)


class WebhookService:
    """
    Core webhook processing service.

    Handles:
    - Webhook storage and audit trail
    - Idempotency checking
    - Delegation to provider handlers
    - Domain event emission
    - Retry logic
    """

    def __init__(
        self,
        repository: WebhookRepository,
        idempotency_service: IdempotencyService,
        event_dispatcher: DomainEventDispatcher,
    ):
        self._repository = repository
        self._idempotency = idempotency_service
        self._dispatcher = event_dispatcher
        self._handlers: Dict[str, IWebhookHandler] = {}

    def register_handler(self, handler: IWebhookHandler) -> None:
        """Register a provider webhook handler."""
        self._handlers[handler.provider_name] = handler
        logger.info(f"Registered webhook handler for {handler.provider_name}")

    def get_handler(self, provider: str) -> Optional[IWebhookHandler]:
        """Get handler for provider."""
        return self._handlers.get(provider)

    def process_webhook(
        self,
        provider: str,
        payload: bytes,
        headers: dict,
        secret: str,
    ) -> WebhookProcessingResult:
        """
        Process incoming webhook.

        Args:
            provider: Provider name (stripe, paypal, etc.)
            payload: Raw request body
            headers: Request headers
            secret: Webhook signing secret

        Returns:
            Processing result
        """
        handler = self.get_handler(provider)
        if not handler:
            logger.error(f"No webhook handler for provider: {provider}")
            return WebhookProcessingResult(
                success=False,
                error=f"Unknown provider: {provider}",
            )

        # Parse payload
        try:
            import json
            payload_dict = json.loads(payload)
        except json.JSONDecodeError as e:
            return WebhookProcessingResult(
                success=False,
                error=f"Invalid JSON payload: {e}",
            )

        # Extract event ID for idempotency
        event_id = handler.get_event_id(payload_dict)
        event_type = handler.get_event_type(payload_dict)

        # Check idempotency
        idempotency_key = f"webhook:{provider}:{event_id}"
        is_dup, cached = self._idempotency.is_duplicate(idempotency_key, {})
        if is_dup:
            logger.info(f"Duplicate webhook ignored: {idempotency_key}")
            return WebhookProcessingResult(
                success=True,
                event_type=event_type,
                error="Duplicate webhook",
            )

        # Create webhook record
        record = WebhookRecord(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload=payload_dict,
            headers=dict(headers),
            signature=headers.get('stripe-signature') or headers.get('paypal-transmission-sig'),
        )

        # Store for audit
        self._repository.save(record)

        # Mark as processing
        self._idempotency.start_request(
            key=idempotency_key,
            provider=provider,
            operation='webhook',
            request_data={'event_id': event_id},
        )

        try:
            # Verify signature
            verification = handler.verify_signature(payload, headers, secret)
            if not verification.valid:
                record.mark_failed(f"Signature verification failed: {verification.error}")
                self._repository.save(record)
                self._idempotency.complete_request(idempotency_key, {'error': verification.error}, 'failed')
                return WebhookProcessingResult(
                    success=False,
                    error=verification.error,
                )

            # Check if event type should be processed
            if not handler.should_process(event_type):
                record.mark_ignored(f"Event type not handled: {event_type}")
                self._repository.save(record)
                self._idempotency.complete_request(idempotency_key, {'ignored': True}, 'completed')
                return WebhookProcessingResult(
                    success=True,
                    event_type=event_type,
                )

            # Parse to normalized event
            record.mark_processing()
            self._repository.save(record)

            normalized = handler.parse_event(payload_dict, headers)

            # Update record with business context
            record.invoice_id = normalized.invoice_id
            record.subscription_id = normalized.subscription_id
            record.user_id = normalized.user_id

            # Emit domain event
            domain_event = self._create_domain_event(normalized)
            if domain_event:
                result = self._dispatcher.emit(domain_event)
                if not result.success:
                    record.mark_failed(result.error)
                    self._repository.save(record)
                    self._idempotency.complete_request(idempotency_key, {'error': result.error}, 'failed')
                    return WebhookProcessingResult(
                        success=False,
                        event_type=event_type,
                        error=result.error,
                        should_retry=True,
                    )

            # Mark completed
            record.mark_completed()
            self._repository.save(record)
            self._idempotency.complete_request(idempotency_key, {'processed': True}, 'completed')

            return WebhookProcessingResult(
                success=True,
                event_type=event_type,
                domain_event_emitted=domain_event is not None,
            )

        except Exception as e:
            logger.exception(f"Webhook processing error: {e}")
            record.mark_failed(str(e))
            self._repository.save(record)
            self._idempotency.complete_request(idempotency_key, {'error': str(e)}, 'failed')
            return WebhookProcessingResult(
                success=False,
                event_type=event_type,
                error=str(e),
                should_retry=record.can_retry(),
            )

    def _create_domain_event(self, normalized: NormalizedWebhookEvent):
        """Map normalized webhook event to domain event."""
        event_map = {
            WebhookEventType.PAYMENT_CAPTURED: PaymentCapturedEvent,
            WebhookEventType.CHECKOUT_COMPLETED: PaymentCapturedEvent,
            WebhookEventType.PAYMENT_FAILED: PaymentFailedEvent,
            WebhookEventType.PAYMENT_REFUNDED: PaymentRefundedEvent,
        }

        event_class = event_map.get(normalized.event_type)
        if not event_class:
            logger.debug(f"No domain event for webhook type: {normalized.event_type}")
            return None

        # Build event based on type
        if event_class == PaymentCapturedEvent:
            return PaymentCapturedEvent(
                invoice_id=normalized.invoice_id,
                subscription_id=normalized.subscription_id,
                user_id=normalized.user_id,
                provider=normalized.provider,
                provider_reference=normalized.payment_intent_id or normalized.checkout_session_id,
                amount=normalized.amount,
                currency=normalized.currency,
            )
        elif event_class == PaymentFailedEvent:
            return PaymentFailedEvent(
                invoice_id=normalized.invoice_id,
                subscription_id=normalized.subscription_id,
                user_id=normalized.user_id,
                provider=normalized.provider,
                error_code=normalized.failure_code,
                error_message=normalized.failure_message,
            )
        elif event_class == PaymentRefundedEvent:
            return PaymentRefundedEvent(
                invoice_id=normalized.invoice_id,
                subscription_id=normalized.subscription_id,
                user_id=normalized.user_id,
                provider=normalized.provider,
                refund_id=normalized.refund_id,
                amount=normalized.amount,
            )

        return None

    def retry_failed_webhooks(self, provider: str = None) -> int:
        """
        Retry failed webhooks.

        Args:
            provider: Optional provider filter

        Returns:
            Number of webhooks retried
        """
        failed = self._repository.find_failed_retryable(provider=provider)
        retried = 0

        for record in failed:
            # Clear idempotency to allow retry
            idempotency_key = f"webhook:{record.provider}:{record.event_id}"
            self._idempotency.delete_key(idempotency_key)

            # Get secret from config
            from src.config.payment_config import get_webhook_secret
            secret = get_webhook_secret(record.provider)

            # Reprocess
            import json
            result = self.process_webhook(
                provider=record.provider,
                payload=json.dumps(record.payload).encode(),
                headers=record.headers,
                secret=secret,
            )

            if result.success:
                retried += 1
                logger.info(f"Retried webhook successfully: {record.event_id}")

        return retried
```

### Stripe Webhook Handler

```python
"""Stripe webhook handler."""
import stripe
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.webhooks.handlers.base import (
    IWebhookHandler,
    WebhookVerificationResult,
)
from src.webhooks.models import NormalizedWebhookEvent, WebhookEventType


class StripeWebhookHandler(IWebhookHandler):
    """
    Stripe webhook handler.

    Handles verification, parsing, and normalization of Stripe webhooks.
    """

    # Stripe events we care about
    SUPPORTED_EVENTS = [
        'checkout.session.completed',
        'checkout.session.expired',
        'payment_intent.succeeded',
        'payment_intent.payment_failed',
        'payment_intent.canceled',
        'charge.refunded',
        'charge.dispute.created',
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
        'invoice.paid',
        'invoice.payment_failed',
    ]

    @property
    def provider_name(self) -> str:
        return 'stripe'

    @property
    def supported_events(self) -> List[str]:
        return self.SUPPORTED_EVENTS

    def verify_signature(
        self,
        payload: bytes,
        headers: dict,
        secret: str,
    ) -> WebhookVerificationResult:
        """Verify Stripe webhook signature."""
        signature = headers.get('stripe-signature', '')

        try:
            stripe.Webhook.construct_event(payload, signature, secret)
            return WebhookVerificationResult(valid=True)
        except stripe.error.SignatureVerificationError as e:
            return WebhookVerificationResult(valid=False, error=str(e))
        except Exception as e:
            return WebhookVerificationResult(valid=False, error=f"Unexpected error: {e}")

    def get_event_id(self, payload: dict) -> str:
        """Extract Stripe event ID."""
        return payload.get('id', '')

    def get_event_type(self, payload: dict) -> str:
        """Extract Stripe event type."""
        return payload.get('type', '')

    def parse_event(
        self,
        payload: dict,
        headers: dict,
    ) -> NormalizedWebhookEvent:
        """Parse Stripe webhook to normalized event."""
        event_type = payload.get('type', '')
        data = payload.get('data', {}).get('object', {})

        # Map Stripe event types to normalized types
        normalized_type = self._map_event_type(event_type)

        # Extract metadata
        metadata = data.get('metadata', {})

        # Parse UUIDs from metadata
        invoice_id = self._parse_uuid(metadata.get('invoice_id'))
        subscription_id = self._parse_uuid(metadata.get('subscription_id'))
        user_id = self._parse_uuid(metadata.get('user_id'))

        # Extract payment identifiers
        payment_intent_id = None
        checkout_session_id = None
        charge_id = None
        refund_id = None

        if event_type.startswith('checkout.session'):
            checkout_session_id = data.get('id')
            payment_intent_id = data.get('payment_intent')
        elif event_type.startswith('payment_intent'):
            payment_intent_id = data.get('id')
        elif event_type.startswith('charge'):
            charge_id = data.get('id')
            payment_intent_id = data.get('payment_intent')
            if 'refunds' in data and data['refunds'].get('data'):
                refund_id = data['refunds']['data'][0].get('id')

        # Extract amount
        amount = data.get('amount') or data.get('amount_total')
        currency = data.get('currency', '').upper()

        # Extract failure info
        failure_code = None
        failure_message = None
        if 'last_payment_error' in data:
            error = data['last_payment_error']
            failure_code = error.get('code')
            failure_message = error.get('message')

        return NormalizedWebhookEvent(
            event_id=payload.get('id'),
            event_type=normalized_type,
            provider=self.provider_name,
            timestamp=datetime.fromtimestamp(payload.get('created', 0)),
            received_at=datetime.utcnow(),
            payment_intent_id=payment_intent_id,
            checkout_session_id=checkout_session_id,
            charge_id=charge_id,
            refund_id=refund_id,
            invoice_id=invoice_id,
            subscription_id=subscription_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=data.get('status'),
            failure_code=failure_code,
            failure_message=failure_message,
            raw_data=data,
        )

    def _map_event_type(self, stripe_type: str) -> str:
        """Map Stripe event type to normalized type."""
        mapping = {
            'checkout.session.completed': WebhookEventType.CHECKOUT_COMPLETED,
            'checkout.session.expired': WebhookEventType.CHECKOUT_EXPIRED,
            'payment_intent.succeeded': WebhookEventType.PAYMENT_CAPTURED,
            'payment_intent.payment_failed': WebhookEventType.PAYMENT_FAILED,
            'payment_intent.canceled': WebhookEventType.PAYMENT_CANCELLED,
            'charge.refunded': WebhookEventType.PAYMENT_REFUNDED,
            'charge.dispute.created': WebhookEventType.PAYMENT_DISPUTED,
            'customer.subscription.created': WebhookEventType.SUBSCRIPTION_CREATED,
            'customer.subscription.deleted': WebhookEventType.SUBSCRIPTION_CANCELLED,
            'invoice.paid': WebhookEventType.SUBSCRIPTION_RENEWED,
            'invoice.payment_failed': WebhookEventType.PAYMENT_FAILED,
        }
        return mapping.get(stripe_type, stripe_type)

    def _parse_uuid(self, value: Optional[str]) -> Optional[UUID]:
        """Parse UUID string, return None if invalid."""
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, TypeError):
            return None
```

### PayPal Webhook Handler

```python
"""PayPal webhook handler."""
import httpx
import hashlib
import base64
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.webhooks.handlers.base import (
    IWebhookHandler,
    WebhookVerificationResult,
)
from src.webhooks.models import NormalizedWebhookEvent, WebhookEventType


class PayPalWebhookHandler(IWebhookHandler):
    """
    PayPal webhook handler.

    Handles verification, parsing, and normalization of PayPal webhooks.
    """

    SUPPORTED_EVENTS = [
        'CHECKOUT.ORDER.APPROVED',
        'CHECKOUT.ORDER.COMPLETED',
        'PAYMENT.CAPTURE.COMPLETED',
        'PAYMENT.CAPTURE.DENIED',
        'PAYMENT.CAPTURE.REFUNDED',
        'PAYMENT.CAPTURE.REVERSED',
        'BILLING.SUBSCRIPTION.ACTIVATED',
        'BILLING.SUBSCRIPTION.CANCELLED',
        'BILLING.SUBSCRIPTION.EXPIRED',
        'BILLING.SUBSCRIPTION.PAYMENT.FAILED',
    ]

    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self._client_id = client_id
        self._client_secret = client_secret
        self._sandbox = sandbox
        self._base_url = (
            'https://api-m.sandbox.paypal.com' if sandbox
            else 'https://api-m.paypal.com'
        )

    @property
    def provider_name(self) -> str:
        return 'paypal'

    @property
    def supported_events(self) -> List[str]:
        return self.SUPPORTED_EVENTS

    def verify_signature(
        self,
        payload: bytes,
        headers: dict,
        secret: str,  # This is the webhook_id for PayPal
    ) -> WebhookVerificationResult:
        """
        Verify PayPal webhook signature.

        PayPal requires calling their API to verify webhooks.
        """
        try:
            # Get access token
            token = self._get_access_token()

            # Build verification request
            verification_data = {
                'auth_algo': headers.get('paypal-auth-algo'),
                'cert_url': headers.get('paypal-cert-url'),
                'transmission_id': headers.get('paypal-transmission-id'),
                'transmission_sig': headers.get('paypal-transmission-sig'),
                'transmission_time': headers.get('paypal-transmission-time'),
                'webhook_id': secret,
                'webhook_event': payload.decode() if isinstance(payload, bytes) else payload,
            }

            # Call PayPal verification endpoint
            response = httpx.post(
                f"{self._base_url}/v1/notifications/verify-webhook-signature",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                json=verification_data,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('verification_status') == 'SUCCESS':
                    return WebhookVerificationResult(valid=True)
                return WebhookVerificationResult(
                    valid=False,
                    error=f"Verification failed: {result.get('verification_status')}"
                )

            return WebhookVerificationResult(
                valid=False,
                error=f"Verification API error: {response.status_code}"
            )

        except Exception as e:
            return WebhookVerificationResult(valid=False, error=str(e))

    def _get_access_token(self) -> str:
        """Get PayPal OAuth access token."""
        response = httpx.post(
            f"{self._base_url}/v1/oauth2/token",
            auth=(self._client_id, self._client_secret),
            data={'grant_type': 'client_credentials'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()['access_token']

    def get_event_id(self, payload: dict) -> str:
        """Extract PayPal event ID."""
        return payload.get('id', '')

    def get_event_type(self, payload: dict) -> str:
        """Extract PayPal event type."""
        return payload.get('event_type', '')

    def parse_event(
        self,
        payload: dict,
        headers: dict,
    ) -> NormalizedWebhookEvent:
        """Parse PayPal webhook to normalized event."""
        event_type = payload.get('event_type', '')
        resource = payload.get('resource', {})

        # Map PayPal event types to normalized types
        normalized_type = self._map_event_type(event_type)

        # Extract identifiers
        order_id = None
        capture_id = None
        refund_id = None

        if 'ORDER' in event_type:
            order_id = resource.get('id')
        elif 'CAPTURE' in event_type:
            capture_id = resource.get('id')
            if event_type == 'PAYMENT.CAPTURE.REFUNDED':
                # Refund info in supplementary_data
                refund_id = resource.get('supplementary_data', {}).get('refund_id')

        # Extract metadata from custom_id
        custom_id = self._extract_custom_id(resource)
        invoice_id, subscription_id, user_id = self._parse_custom_id(custom_id)

        # Extract amount
        amount_obj = resource.get('amount', {})
        amount = None
        currency = None
        if amount_obj:
            try:
                amount = int(float(amount_obj.get('value', 0)) * 100)
                currency = amount_obj.get('currency_code', '').upper()
            except (ValueError, TypeError):
                pass

        # Extract failure info
        failure_code = None
        failure_message = None
        if 'DENIED' in event_type or 'FAILED' in event_type:
            failure_code = resource.get('status_details', {}).get('reason')
            failure_message = resource.get('message')

        return NormalizedWebhookEvent(
            event_id=payload.get('id'),
            event_type=normalized_type,
            provider=self.provider_name,
            timestamp=datetime.fromisoformat(
                payload.get('create_time', '').replace('Z', '+00:00')
            ) if payload.get('create_time') else datetime.utcnow(),
            received_at=datetime.utcnow(),
            payment_intent_id=order_id,
            checkout_session_id=order_id,
            charge_id=capture_id,
            refund_id=refund_id,
            invoice_id=invoice_id,
            subscription_id=subscription_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=resource.get('status'),
            failure_code=failure_code,
            failure_message=failure_message,
            raw_data=resource,
        )

    def _map_event_type(self, paypal_type: str) -> str:
        """Map PayPal event type to normalized type."""
        mapping = {
            'CHECKOUT.ORDER.APPROVED': WebhookEventType.PAYMENT_AUTHORIZED,
            'CHECKOUT.ORDER.COMPLETED': WebhookEventType.CHECKOUT_COMPLETED,
            'PAYMENT.CAPTURE.COMPLETED': WebhookEventType.PAYMENT_CAPTURED,
            'PAYMENT.CAPTURE.DENIED': WebhookEventType.PAYMENT_FAILED,
            'PAYMENT.CAPTURE.REFUNDED': WebhookEventType.PAYMENT_REFUNDED,
            'PAYMENT.CAPTURE.REVERSED': WebhookEventType.PAYMENT_REFUNDED,
            'BILLING.SUBSCRIPTION.ACTIVATED': WebhookEventType.SUBSCRIPTION_CREATED,
            'BILLING.SUBSCRIPTION.CANCELLED': WebhookEventType.SUBSCRIPTION_CANCELLED,
            'BILLING.SUBSCRIPTION.EXPIRED': WebhookEventType.SUBSCRIPTION_EXPIRED,
            'BILLING.SUBSCRIPTION.PAYMENT.FAILED': WebhookEventType.PAYMENT_FAILED,
        }
        return mapping.get(paypal_type, paypal_type)

    def _extract_custom_id(self, resource: dict) -> Optional[str]:
        """Extract custom_id from various PayPal resource structures."""
        # Direct custom_id
        if 'custom_id' in resource:
            return resource['custom_id']

        # In purchase_units
        purchase_units = resource.get('purchase_units', [])
        if purchase_units:
            return purchase_units[0].get('custom_id')

        return None

    def _parse_custom_id(self, custom_id: Optional[str]):
        """
        Parse custom_id containing our metadata.

        Expected format: "inv:{invoice_id}|sub:{subscription_id}|usr:{user_id}"
        """
        invoice_id = None
        subscription_id = None
        user_id = None

        if not custom_id:
            return invoice_id, subscription_id, user_id

        try:
            parts = custom_id.split('|')
            for part in parts:
                if part.startswith('inv:'):
                    invoice_id = UUID(part[4:])
                elif part.startswith('sub:'):
                    subscription_id = UUID(part[4:])
                elif part.startswith('usr:'):
                    user_id = UUID(part[4:])
        except (ValueError, TypeError):
            pass

        return invoice_id, subscription_id, user_id
```

### Webhook Routes

```python
"""Webhook routes."""
from flask import Blueprint, request, jsonify, current_app
import logging

from src.webhooks.service import WebhookService
from src.config.payment_config import get_webhook_secret


logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhooks', __name__, url_prefix='/api/v1/webhooks')


@webhook_bp.route('/<provider>', methods=['POST'])
def handle_webhook(provider: str):
    """
    Generic webhook endpoint for all providers.

    POST /api/v1/webhooks/stripe
    POST /api/v1/webhooks/paypal
    POST /api/v1/webhooks/klarna
    """
    # Get raw payload
    payload = request.get_data()

    # Get headers
    headers = dict(request.headers)

    # Get webhook secret for provider
    secret = get_webhook_secret(provider)
    if not secret:
        logger.error(f"No webhook secret configured for {provider}")
        return jsonify({'error': 'Provider not configured'}), 400

    # Get webhook service
    webhook_service: WebhookService = current_app.extensions['webhook_service']

    # Process webhook
    result = webhook_service.process_webhook(
        provider=provider,
        payload=payload,
        headers=headers,
        secret=secret,
    )

    # Always return 200 to acknowledge receipt
    # (Providers will retry if they get non-2xx)
    if result.success:
        return jsonify({
            'received': True,
            'event_type': result.event_type,
        }), 200
    else:
        # Log error but still return 200 to prevent retry spam
        # (We handle retries internally)
        logger.error(f"Webhook processing error: {result.error}")
        return jsonify({
            'received': True,
            'error': result.error,
        }), 200


@webhook_bp.route('/retry/<provider>', methods=['POST'])
def retry_webhooks(provider: str):
    """
    Retry failed webhooks for a provider.

    POST /api/v1/webhooks/retry/stripe

    Admin only endpoint.
    """
    from src.middleware.auth import require_admin

    @require_admin
    def _retry():
        webhook_service: WebhookService = current_app.extensions['webhook_service']
        count = webhook_service.retry_failed_webhooks(provider=provider)
        return jsonify({
            'retried': count,
            'provider': provider,
        }), 200

    return _retry()


@webhook_bp.route('/status/<event_id>', methods=['GET'])
def webhook_status(event_id: str):
    """
    Get webhook processing status.

    GET /api/v1/webhooks/status/{event_id}

    Admin only endpoint.
    """
    from src.middleware.auth import require_admin

    @require_admin
    def _status():
        webhook_service: WebhookService = current_app.extensions['webhook_service']
        record = webhook_service._repository.find_by_event_id(event_id)

        if not record:
            return jsonify({'error': 'Webhook not found'}), 404

        return jsonify({
            'id': str(record.id),
            'provider': record.provider,
            'event_id': record.event_id,
            'event_type': record.event_type,
            'status': record.status.value,
            'error': record.error_message,
            'retry_count': record.retry_count,
            'created_at': record.created_at.isoformat(),
            'processed_at': record.processed_at.isoformat() if record.processed_at else None,
        }), 200

    return _status()
```

### Webhook Handler Registration

```python
"""Webhook system initialization."""
from src.webhooks.service import WebhookService
from src.webhooks.repository import WebhookRepository
from src.webhooks.handlers.stripe import StripeWebhookHandler
from src.webhooks.handlers.paypal import PayPalWebhookHandler
from src.services.idempotency_service import IdempotencyService
from src.events.domain import DomainEventDispatcher
from src.config.payment_config import PaymentConfig


def init_webhook_service(
    idempotency_service: IdempotencyService,
    event_dispatcher: DomainEventDispatcher,
    config: PaymentConfig,
) -> WebhookService:
    """
    Initialize webhook service with all handlers.

    Call during app startup.
    """
    repository = WebhookRepository()

    service = WebhookService(
        repository=repository,
        idempotency_service=idempotency_service,
        event_dispatcher=event_dispatcher,
    )

    # Register Stripe handler
    if config.stripe_enabled:
        stripe_handler = StripeWebhookHandler()
        service.register_handler(stripe_handler)

    # Register PayPal handler
    if config.paypal_enabled:
        paypal_handler = PayPalWebhookHandler(
            client_id=config.paypal_client_id,
            client_secret=config.paypal_client_secret,
            sandbox=config.paypal_sandbox,
        )
        service.register_handler(paypal_handler)

    # Register additional handlers as needed
    # service.register_handler(KlarnaWebhookHandler(...))

    return service


def register_webhook_blueprint(app, webhook_service: WebhookService):
    """Register webhook routes with Flask app."""
    from src.webhooks.routes import webhook_bp

    # Store service in app extensions
    app.extensions['webhook_service'] = webhook_service

    # Register blueprint
    app.register_blueprint(webhook_bp)
```

---

## File Structure

```
python/api/src/
├── events/
│   ├── __init__.py
│   ├── core/                   # Event System Core (NEW)
│   │   ├── __init__.py
│   │   ├── interfaces.py       # EventInterface, EventResult
│   │   ├── base.py             # Event base class
│   │   ├── domain.py           # DomainEvent with metadata
│   │   ├── context.py          # EventContext (request-scoped cache)
│   │   ├── handler.py          # IEventHandler, HandlerPriority
│   │   ├── base_handler.py     # AbstractHandler
│   │   ├── dispatcher.py       # EventDispatcher (priority-based)
│   │   └── provider.py         # EventListenerProvider (lazy init)
│   │
│   ├── subscription_events.py  # Subscription domain events
│   ├── payment_events.py       # Payment domain events (NEW)
│   └── user_events.py          # User domain events
│
├── handlers/
│   ├── __init__.py
│   ├── subscription_handlers.py
│   ├── payment_handlers.py    # Payment event handlers (NEW)
│   └── user_handlers.py
│
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── subscriptions.py
│   ├── tarif_plans.py
│   └── payment.py             # Payment routes (NEW)
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   ├── subscription_service.py
│   ├── tarif_plan_service.py
│   ├── invoice_service.py     # Invoice business logic
│   ├── payment_service.py     # Payment business logic (NEW)
│   ├── notification_service.py
│   └── idempotency_service.py # Idempotency key management (NEW)
│
├── plugins/
│   ├── __init__.py
│   ├── base.py                # IPaymentProviderAdapter
│   ├── registry.py            # PaymentPluginRegistry
│   ├── mock_plugin.py         # Mock for testing
│   ├── stripe/                # Stripe plugin
│   │   ├── __init__.py
│   │   └── plugin.py          # StripePlugin (uses SDK adapter)
│   ├── paypal/                # PayPal plugin
│   │   ├── __init__.py
│   │   └── plugin.py          # PayPalPlugin (uses SDK adapter)
│   └── manual/                # Manual/Invoice plugin
│       ├── __init__.py
│       └── plugin.py
│
├── sdk/                       # SDK Adapter Layer (NEW)
│   ├── __init__.py
│   ├── interface.py           # ISDKAdapter, SDKResponse, SDKConfig
│   ├── base.py                # BaseSDKAdapter (HTTP, retries, idempotency)
│   ├── registry.py            # SDKAdapterRegistry
│   ├── stripe_adapter.py      # StripeSDKAdapter
│   ├── paypal_adapter.py      # PayPalSDKAdapter
│   └── klarna_adapter.py      # KlarnaSDKAdapter
│
├── models/
│   ├── __init__.py
│   ├── base.py                # BaseModel (UUID, version, timestamps)
│   ├── user.py                # User, UserDetails
│   ├── subscription.py        # Subscription
│   ├── tarif_plan.py          # TarifPlan
│   ├── price.py               # Price
│   ├── currency.py            # Currency
│   ├── tax.py                 # Tax, TaxRate
│   ├── invoice.py             # Invoice
│   └── webhook.py             # Webhook model (NEW)
│
├── repositories/
│   ├── __init__.py
│   ├── base.py                # BaseRepository[T]
│   ├── user_repository.py
│   ├── subscription_repository.py
│   ├── tarif_plan_repository.py
│   ├── invoice_repository.py
│   └── webhook_repository.py  # WebhookRepository (NEW)
│
├── webhooks/                  # Webhook System (NEW)
│   ├── __init__.py
│   ├── dto.py                 # NormalizedWebhookEvent, WebhookEventType
│   ├── service.py             # WebhookService (core processing)
│   ├── routes.py              # Webhook endpoints
│   ├── init.py                # Initialization & registration
│   └── handlers/              # Provider-specific handlers
│       ├── __init__.py
│       ├── base.py            # IWebhookHandler interface
│       ├── stripe.py          # StripeWebhookHandler
│       ├── paypal.py          # PayPalWebhookHandler
│       └── klarna.py          # KlarnaWebhookHandler
│
├── migrations/                # Alembic migrations
│   ├── versions/
│   │   ├── e3bb91853ab7_initial.py
│   │   └── add_webhook_table.py  # Webhook migration (NEW)
│   ├── env.py
│   └── alembic.ini
│
└── config/
    └── payment_config.py      # Payment configuration
```

---

## Event Flow Examples

### Checkout Flow

```
User clicks "Subscribe"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /api/v1/payment/checkout                               │
│   → Validates input                                         │
│   → Emits CheckoutInitiatedEvent                           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ DomainEventDispatcher.emit(CheckoutInitiatedEvent)          │
│   → Routes to CheckoutInitiatedHandler                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ CheckoutInitiatedHandler.handle()                           │
│   → SubscriptionService.create_subscription()               │
│   → InvoiceService.create_invoice()                         │
│   → PaymentService.create_checkout()                        │
│   → Returns checkout_url                                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
User redirected to payment provider
```

### Webhook Flow

```
Payment provider sends webhook
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /api/v1/payment/webhook/stripe                         │
│   → Verifies signature via plugin                           │
│   → Emits WebhookReceivedEvent                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ WebhookReceivedHandler.handle()                             │
│   → Plugin.parse_webhook_event()                            │
│   → Creates PaymentCapturedEvent                           │
│   → Emits to dispatcher                                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ PaymentCapturedHandler.handle()                             │
│   → InvoiceService.mark_paid()                             │
│   → SubscriptionService.activate_subscription()            │
│   → UserService.update_user_status()                       │
│   → NotificationService.send_confirmation()                │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

This event-driven payment architecture provides:

1. **Clear Separation of Concerns**
   - Routes: Input validation, event emission
   - Events: Domain event definitions
   - Handlers: Event orchestration, service coordination
   - Services: Business logic implementation
   - Plugins: Provider-specific integration
   - SDK Adapters: Low-level provider API communication
   - Webhook Handlers: Provider-specific webhook processing

2. **Consistent Pattern**
   - Same pattern as existing subscription/user events
   - All handlers implement `IEventHandler`
   - All events extend `DomainEvent`
   - Unified `EventResult` for responses
   - All SDK adapters implement `ISDKAdapter`
   - All webhook handlers implement `IWebhookHandler`

3. **Extensibility**
   - New payment providers via plugins + SDK adapters + webhook handlers
   - New event types without core changes
   - Multiple handlers per event supported
   - SDK adapters and webhook handlers can be registered dynamically

4. **Idempotency & Reliability**
   - Redis-backed idempotency keys prevent duplicate API calls
   - Automatic retry with exponential backoff
   - Request hash verification prevents key collisions
   - Cached responses returned for completed operations
   - Failed requests can be retried after cleanup
   - Webhook deduplication via event ID

5. **Webhook System**
   - Generic endpoint: `POST /api/v1/webhooks/{provider}`
   - Signature verification per provider
   - Event normalization to standard format
   - Audit trail with `WebhookRecord` persistence
   - Failed webhook retry mechanism
   - Admin endpoints for status and manual retry

6. **Testability**
   - Handlers easily unit tested with mock services
   - Events are simple data objects
   - Services tested independently
   - SDK adapters testable with mock idempotency service
   - Webhook handlers testable with mock payloads

See also:
- `src/events/domain.py` - Base event system
- `src/handlers/subscription_handlers.py` - Existing handler pattern
- `docs/architecture_core_server_ce/plugin-system.md` - Plugin architecture
