# Sprint 13: Event Handlers for Tickets & Bookings

**Goal:** Implement event-driven architecture for ticket and booking lifecycle management with domain event handlers.

**Prerequisites:** Sprint 8 complete (ticket models), Sprint 9 complete (ticket API), Sprint 6-7 complete (booking system), Sprint 11 complete (event infrastructure)

---

## Objectives

- [ ] Ticket domain events
- [ ] Booking domain events
- [ ] TicketActivationHandler implementation
- [ ] TicketRedemptionHandler implementation
- [ ] BookingConfirmationHandler implementation
- [ ] BookingCancellationHandler implementation
- [ ] Integration with existing ticket/booking routes
- [ ] Comprehensive unit and integration tests (95%+ coverage)

---

## Tasks

### 13.1 Ticket Domain Events

**File:** `python/api/src/events/ticket_events.py`

```python
"""Ticket domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal
from .base import Event


@dataclass
class TicketCreatedEvent(Event):
    """Event: Ticket was created."""

    ticket_id: int
    user_id: int
    booking_id: Optional[int] = None
    ticket_type_id: int
    price: Decimal = Decimal('0')
    currency: str = 'USD'

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.created'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class TicketActivationRequestedEvent(Event):
    """Event: Ticket activation was requested."""

    ticket_id: int
    user_id: int
    admin_id: Optional[int] = None
    activation_code: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.activation_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class TicketActivatedEvent(Event):
    """Event: Ticket was activated."""

    ticket_id: int
    user_id: int
    ticket_type: str
    activated_at: datetime
    valid_until: Optional[datetime] = None
    admin_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.activated'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class TicketRedemptionRequestedEvent(Event):
    """Event: Ticket redemption was requested."""

    ticket_id: int
    user_id: int
    redemption_code: str
    location: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.redemption_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class TicketRedeemedEvent(Event):
    """Event: Ticket was redeemed."""

    ticket_id: int
    user_id: int
    redeemed_at: datetime
    redeemed_by: Optional[int] = None  # Staff member ID
    location: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.redeemed'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class TicketCancelledEvent(Event):
    """Event: Ticket was cancelled."""

    ticket_id: int
    user_id: int
    cancelled_at: datetime
    reason: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    admin_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.cancelled'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class TicketExpiredEvent(Event):
    """Event: Ticket expired."""

    ticket_id: int
    user_id: int
    expired_at: datetime

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'ticket.expired'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
```

---

### 13.2 Booking Domain Events

**File:** `python/api/src/events/booking_events.py`

```python
"""Booking domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal
from .base import Event


@dataclass
class BookingCreatedEvent(Event):
    """Event: Booking was created."""

    booking_id: int
    user_id: int
    resource_type: str
    resource_id: int
    start_time: datetime
    end_time: datetime
    price: Decimal
    currency: str

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.created'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class BookingConfirmationRequestedEvent(Event):
    """Event: Booking confirmation was requested."""

    booking_id: int
    user_id: int
    payment_id: Optional[int] = None
    admin_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.confirmation_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class BookingConfirmedEvent(Event):
    """Event: Booking was confirmed."""

    booking_id: int
    user_id: int
    confirmed_at: datetime
    confirmation_code: str
    admin_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.confirmed'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class BookingCancellationRequestedEvent(Event):
    """Event: Booking cancellation was requested."""

    booking_id: int
    user_id: int
    reason: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    admin_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.cancellation_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class BookingCancelledEvent(Event):
    """Event: Booking was cancelled."""

    booking_id: int
    user_id: int
    cancelled_at: datetime
    reason: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    admin_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.cancelled'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class BookingCompletedEvent(Event):
    """Event: Booking was completed."""

    booking_id: int
    user_id: int
    completed_at: datetime
    review_requested: bool = False

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.completed'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class BookingNoShowEvent(Event):
    """Event: User did not show up for booking."""

    booking_id: int
    user_id: int
    marked_no_show_at: datetime
    staff_id: Optional[int] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'booking.no_show'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
```

---

### 13.3 TicketActivationHandler

**File:** `python/api/src/handlers/ticket_activation_handler.py`

```python
"""Handler for ticket activation events."""
import logging
from typing import TYPE_CHECKING
from src.events.base import IEventHandler, Event, EventResult
from src.events.ticket_events import (
    TicketActivationRequestedEvent,
    TicketActivatedEvent
)

if TYPE_CHECKING:
    from src.interfaces import (
        ITicketService,
        IAuditService,
        INotificationService
    )
    from src.events import EventDispatcher

logger = logging.getLogger(__name__)


class TicketActivationHandler(IEventHandler):
    """
    Handler for ticket activation requests.

    Responsibilities (SRP):
    - Activate ticket via TicketService
    - Generate activation code
    - Log action via AuditService
    - Send notification to user with QR code
    - Emit TicketActivatedEvent
    """

    def __init__(
        self,
        ticket_service: 'ITicketService',
        audit_service: 'IAuditService',
        notification_service: 'INotificationService',
        event_dispatcher: 'EventDispatcher'
    ):
        """Initialize handler with dependencies (DI)."""
        self._ticket_service = ticket_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the event."""
        return event.name == 'ticket.activation_requested'

    def handle(self, event: TicketActivationRequestedEvent) -> EventResult:
        """
        Handle ticket activation.

        Flow:
        1. Load ticket
        2. Validate ticket can be activated
        3. Generate activation code
        4. Activate ticket
        5. Log action to audit
        6. Send notification with QR code
        7. Emit TicketActivatedEvent
        """
        logger.info(f"Handling ticket activation: ticket_id={event.ticket_id}")

        try:
            # 1. Load ticket
            ticket = self._ticket_service.get_by_id(event.ticket_id)
            if not ticket:
                return EventResult.error(f"Ticket {event.ticket_id} not found")

            # 2. Validate ticket can be activated
            if ticket.status != 'pending':
                return EventResult.error(
                    f"Ticket cannot be activated. Current status: {ticket.status}"
                )

            # 3. Generate activation code (if not provided)
            activation_code = event.activation_code
            if not activation_code:
                activation_code = self._ticket_service.generate_activation_code()

            # 4. Activate ticket
            activated_ticket = self._ticket_service.activate(
                ticket_id=event.ticket_id,
                activation_code=activation_code
            )

            # 5. Log action
            self._audit_service.log_action(
                admin_id=event.admin_id or event.user_id,
                action='ticket_activated',
                resource_type='ticket',
                resource_id=event.ticket_id,
                old_value='pending',
                new_value='active',
                metadata={
                    'activation_code': activation_code,
                    'ticket_type': ticket.ticket_type.name
                }
            )

            # 6. Send notification with QR code
            self._notification_service.notify_user(
                user_id=event.user_id,
                template='ticket_activated',
                context={
                    'ticket_id': event.ticket_id,
                    'ticket_type': ticket.ticket_type.name,
                    'activation_code': activation_code,
                    'qr_code_url': self._ticket_service.generate_qr_code_url(activation_code),
                    'valid_until': ticket.valid_until.isoformat() if ticket.valid_until else None
                }
            )

            # 7. Emit result event
            result_event = TicketActivatedEvent(
                ticket_id=event.ticket_id,
                user_id=event.user_id,
                ticket_type=ticket.ticket_type.name,
                activated_at=activated_ticket.activated_at,
                valid_until=activated_ticket.valid_until,
                admin_id=event.admin_id,
                timestamp=event.timestamp
            )
            self._event_dispatcher.emit(result_event)

            logger.info(f"Ticket activated successfully: ticket_id={event.ticket_id}")
            return EventResult.success(activated_ticket.to_dict())

        except Exception as e:
            logger.error(f"Error activating ticket: {str(e)}", exc_info=True)
            return EventResult.error(str(e))
```

---

### 13.4 BookingConfirmationHandler

**File:** `python/api/src/handlers/booking_confirmation_handler.py`

```python
"""Handler for booking confirmation events."""
import logging
from typing import TYPE_CHECKING
from src.events.base import IEventHandler, Event, EventResult
from src.events.booking_events import (
    BookingConfirmationRequestedEvent,
    BookingConfirmedEvent
)
from src.events.ticket_events import TicketCreatedEvent

if TYPE_CHECKING:
    from src.interfaces import (
        IBookingService,
        ITicketService,
        IAuditService,
        INotificationService
    )
    from src.events import EventDispatcher

logger = logging.getLogger(__name__)


class BookingConfirmationHandler(IEventHandler):
    """
    Handler for booking confirmation requests.

    Responsibilities (SRP):
    - Confirm booking via BookingService
    - Create associated tickets if needed
    - Generate confirmation code
    - Log action via AuditService
    - Send notification to user
    - Emit BookingConfirmedEvent and TicketCreatedEvent
    """

    def __init__(
        self,
        booking_service: 'IBookingService',
        ticket_service: 'ITicketService',
        audit_service: 'IAuditService',
        notification_service: 'INotificationService',
        event_dispatcher: 'EventDispatcher'
    ):
        """Initialize handler with dependencies (DI)."""
        self._booking_service = booking_service
        self._ticket_service = ticket_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the event."""
        return event.name == 'booking.confirmation_requested'

    def handle(self, event: BookingConfirmationRequestedEvent) -> EventResult:
        """
        Handle booking confirmation.

        Flow:
        1. Load booking
        2. Validate payment (if payment_id provided)
        3. Generate confirmation code
        4. Confirm booking
        5. Create associated tickets
        6. Log action to audit
        7. Send notification to user
        8. Emit BookingConfirmedEvent and TicketCreatedEvent
        """
        logger.info(f"Handling booking confirmation: booking_id={event.booking_id}")

        try:
            # 1. Load booking
            booking = self._booking_service.get_by_id(event.booking_id)
            if not booking:
                return EventResult.error(f"Booking {event.booking_id} not found")

            # 2. Validate booking can be confirmed
            if booking.status != 'pending':
                return EventResult.error(
                    f"Booking cannot be confirmed. Current status: {booking.status}"
                )

            # 3. Generate confirmation code
            confirmation_code = self._booking_service.generate_confirmation_code()

            # 4. Confirm booking
            confirmed_booking = self._booking_service.confirm(
                booking_id=event.booking_id,
                confirmation_code=confirmation_code,
                payment_id=event.payment_id
            )

            # 5. Create associated tickets (if applicable)
            created_tickets = []
            if booking.requires_tickets:
                ticket = self._ticket_service.create_for_booking(
                    booking_id=event.booking_id,
                    user_id=event.user_id
                )
                created_tickets.append(ticket)

                # Emit TicketCreatedEvent
                ticket_event = TicketCreatedEvent(
                    ticket_id=ticket.id,
                    user_id=event.user_id,
                    booking_id=event.booking_id,
                    ticket_type_id=ticket.ticket_type_id,
                    price=ticket.price,
                    currency=ticket.currency,
                    timestamp=event.timestamp
                )
                self._event_dispatcher.emit(ticket_event)

            # 6. Log action
            self._audit_service.log_action(
                admin_id=event.admin_id or event.user_id,
                action='booking_confirmed',
                resource_type='booking',
                resource_id=event.booking_id,
                old_value='pending',
                new_value='confirmed',
                metadata={
                    'confirmation_code': confirmation_code,
                    'payment_id': event.payment_id,
                    'tickets_created': len(created_tickets)
                }
            )

            # 7. Send notification
            self._notification_service.notify_user(
                user_id=event.user_id,
                template='booking_confirmed',
                context={
                    'booking_id': event.booking_id,
                    'confirmation_code': confirmation_code,
                    'start_time': booking.start_time.isoformat(),
                    'end_time': booking.end_time.isoformat(),
                    'location': booking.location,
                    'tickets_count': len(created_tickets)
                }
            )

            # 8. Emit result event
            result_event = BookingConfirmedEvent(
                booking_id=event.booking_id,
                user_id=event.user_id,
                confirmed_at=confirmed_booking.confirmed_at,
                confirmation_code=confirmation_code,
                admin_id=event.admin_id,
                timestamp=event.timestamp
            )
            self._event_dispatcher.emit(result_event)

            logger.info(f"Booking confirmed successfully: booking_id={event.booking_id}")
            return EventResult.success({
                'booking': confirmed_booking.to_dict(),
                'tickets': [t.to_dict() for t in created_tickets]
            })

        except Exception as e:
            logger.error(f"Error confirming booking: {str(e)}", exc_info=True)
            return EventResult.error(str(e))
```

---

### 13.5 Integration with Routes

**File:** `python/api/src/routes/admin/tickets.py` (new)

```python
"""Admin ticket management routes with event-driven architecture."""
from flask import Blueprint, request, jsonify, g
from dependency_injector.wiring import inject, Provide
from datetime import datetime
from src.container import Container
from src.middleware.auth import require_auth, require_admin
from src.events import EventDispatcher, TicketActivationRequestedEvent

admin_tickets_bp = Blueprint("admin_tickets", __name__, url_prefix="/admin/tickets")


@admin_tickets_bp.route("/<int:ticket_id>/activate", methods=["POST"])
@require_auth
@require_admin
@inject
def activate_ticket(
    ticket_id: int,
    event_dispatcher: EventDispatcher = Provide[Container.event_dispatcher],
):
    """
    Activate ticket (event-driven).

    POST /api/v1/admin/tickets/:id/activate
    Authorization: Bearer <admin-token>
    {
        "activation_code": "ABC123" (optional, will be generated if not provided)
    }
    """
    data = request.get_json() or {}
    activation_code = data.get('activation_code')

    # Create and emit event
    event = TicketActivationRequestedEvent(
        ticket_id=ticket_id,
        user_id=0,  # Will be loaded from ticket
        admin_id=g.user_id,
        activation_code=activation_code,
        timestamp=datetime.utcnow()
    )

    result = event_dispatcher.emit(event)

    if result.success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(result.to_dict()), 400
```

**File:** `python/api/src/routes/bookings.py` (updated)

```python
"""Booking routes with event-driven architecture."""
from flask import Blueprint, request, jsonify, g
from dependency_injector.wiring import inject, Provide
from datetime import datetime
from src.container import Container
from src.middleware.auth import require_auth
from src.events import EventDispatcher, BookingConfirmationRequestedEvent

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bookings_bp.route("/<int:booking_id>/confirm", methods=["POST"])
@require_auth
@inject
def confirm_booking(
    booking_id: int,
    event_dispatcher: EventDispatcher = Provide[Container.event_dispatcher],
):
    """
    Confirm booking (event-driven).

    POST /api/v1/bookings/:id/confirm
    Authorization: Bearer <token>
    {
        "payment_id": 123 (optional)
    }
    """
    data = request.get_json() or {}
    payment_id = data.get('payment_id')

    # Create and emit event
    event = BookingConfirmationRequestedEvent(
        booking_id=booking_id,
        user_id=g.user_id,
        payment_id=payment_id,
        timestamp=datetime.utcnow()
    )

    result = event_dispatcher.emit(event)

    if result.success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(result.to_dict()), 400
```

---

### 13.6 Event Handler Registration

**File:** `python/api/src/container.py` (final update)

```python
"""Dependency injection container (final)."""
from dependency_injector import containers, providers
from src.handlers import (
    UserStatusUpdateHandler,
    SubscriptionCancelHandler,
    InvoiceRefundHandler,
    TicketActivationHandler,
    BookingConfirmationHandler
)


class Container(containers.DeclarativeContainer):
    """Application DI container."""

    # ... previous services ...

    ticket_service = providers.Factory(
        # ... ticket service
    )

    booking_service = providers.Factory(
        # ... booking service
    )

    # Event Handlers
    ticket_activation_handler = providers.Factory(
        TicketActivationHandler,
        ticket_service=ticket_service,
        audit_service=audit_service,
        notification_service=notification_service,
        event_dispatcher=event_dispatcher
    )

    booking_confirmation_handler = providers.Factory(
        BookingConfirmationHandler,
        booking_service=booking_service,
        ticket_service=ticket_service,
        audit_service=audit_service,
        notification_service=notification_service,
        event_dispatcher=event_dispatcher
    )


def configure_event_handlers(container: Container) -> None:
    """Register all event handlers with the dispatcher."""
    dispatcher = container.event_dispatcher()

    # User handlers (Sprint 11)
    dispatcher.register(
        'user.status.update_requested',
        container.user_status_update_handler()
    )

    # Subscription handlers (Sprint 12)
    dispatcher.register(
        'subscription.cancel_requested',
        container.subscription_cancel_handler()
    )

    dispatcher.register(
        'invoice.refund_requested',
        container.invoice_refund_handler()
    )

    # Ticket handlers (Sprint 13)
    dispatcher.register(
        'ticket.activation_requested',
        container.ticket_activation_handler()
    )

    # Booking handlers (Sprint 13)
    dispatcher.register(
        'booking.confirmation_requested',
        container.booking_confirmation_handler()
    )
```

---

## Verification Checklist

```bash
# Run ticket event tests
docker-compose run --rm python pytest tests/unit/handlers/test_ticket*.py -v

# Run booking event tests
docker-compose run --rm python pytest tests/unit/handlers/test_booking*.py -v

# Run all Sprint 13 tests
docker-compose run --rm python pytest tests/unit/events/test_ticket*.py tests/unit/events/test_booking*.py -v

# Test ticket activation
curl -X POST http://localhost:5000/api/v1/admin/tickets/1/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{}'

# Test booking confirmation
curl -X POST http://localhost:5000/api/v1/bookings/1/confirm \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"payment_id": 123}'
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Ticket domain events | [ ] | 7 events for ticket lifecycle |
| Booking domain events | [ ] | 7 events for booking lifecycle |
| TicketActivationHandler | [ ] | Event handler with QR code generation |
| BookingConfirmationHandler | [ ] | Event handler with ticket creation |
| Updated routes | [ ] | Event-driven endpoints |
| Event handler registration | [ ] | Complete handler setup |
| Unit tests | [ ] | 95%+ coverage |
| Integration tests | [ ] | End-to-end event flow |

---

## Complete Event-Driven Architecture Summary

With Sprints 11-13 complete, the backend now has a comprehensive event-driven architecture:

**User Management:**
- User status changes (suspend, activate, delete)
- Audit logging for all user actions

**Subscriptions & Invoices:**
- Subscription lifecycle (create, cancel, reactivate, expire)
- Payment processing (success, failure, retry)
- Invoice management (create, pay, void)
- Refund processing with provider integration

**Tickets & Bookings:**
- Ticket lifecycle (create, activate, redeem, cancel, expire)
- Booking lifecycle (create, confirm, cancel, complete, no-show)
- QR code generation for tickets
- Confirmation code generation for bookings

**Cross-Cutting Concerns:**
- Audit logging for all domain events
- Notifications for all state changes
- Analytics tracking via event listeners
- Webhook integration for external systems

**SOLID Principles Throughout:**
- **SRP:** Each handler has one responsibility
- **OCP:** Add new handlers without modifying existing code
- **LSP:** All handlers implement IEventHandler interface
- **ISP:** Focused interfaces for each service
- **DI:** All dependencies injected via constructor

---

## Next Steps

- [User App Sprint 6: Ticket Management Plugin](../../architecture_core_view_user/sprints/sprint-6-ticket-management.md)
- [User App Sprint 7: Booking Management Plugin](../../architecture_core_view_user/sprints/sprint-7-booking-management.md)

---

**Event-Driven Architecture Complete!** 🎉

The backend now fully supports event-driven communication, enabling:
- Decoupled, maintainable code
- Complete audit trails
- Real-time notifications
- Easy testing with mocked dependencies
- Extensibility without modifying existing code
