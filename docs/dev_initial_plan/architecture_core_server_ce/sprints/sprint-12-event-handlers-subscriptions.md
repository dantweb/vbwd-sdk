# Sprint 12: Event Handlers for Subscriptions & Invoices

**Goal:** Implement event-driven architecture for subscription lifecycle and invoice management with domain event handlers.

**Prerequisites:** Sprint 3 complete (subscriptions), Sprint 4 complete (payments), Sprint 11 complete (event infrastructure)

---

## Objectives

- [ ] Subscription domain events
- [ ] Invoice domain events
- [ ] SubscriptionCancelHandler implementation
- [ ] SubscriptionPaymentFailedHandler implementation
- [ ] InvoiceRefundHandler implementation
- [ ] InvoiceVoidHandler implementation
- [ ] Integration with existing subscription/invoice routes
- [ ] Webhook event handlers for Stripe/PayPal
- [ ] Comprehensive unit and integration tests (95%+ coverage)

---

## Tasks

### 12.1 Subscription Domain Events

**File:** `python/api/src/events/subscription_events.py`

```python
"""Subscription domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal
from .base import Event


@dataclass
class SubscriptionCancelRequestedEvent(Event):
    """Event: Admin or user requested subscription cancellation."""

    subscription_id: int
    user_id: int
    admin_id: Optional[int] = None  # None if user-initiated
    reason: Optional[str] = None
    immediate: bool = False  # Cancel immediately or at period end
    refund_amount: Optional[Decimal] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'subscription.cancel_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class SubscriptionCancelledEvent(Event):
    """Event: Subscription was cancelled."""

    subscription_id: int
    user_id: int
    plan_id: int
    cancellation_type: str  # 'immediate' or 'end_of_period'
    cancelled_at: datetime
    ends_at: datetime
    refund_amount: Optional[Decimal] = None
    admin_id: Optional[int] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'subscription.cancelled'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class SubscriptionPaymentFailedEvent(Event):
    """Event: Subscription payment failed."""

    subscription_id: int
    user_id: int
    invoice_id: int
    amount: Decimal
    currency: str
    failure_reason: str
    retry_count: int
    next_retry_at: Optional[datetime] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'subscription.payment.failed'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class SubscriptionPaymentSucceededEvent(Event):
    """Event: Subscription payment succeeded."""

    subscription_id: int
    user_id: int
    invoice_id: int
    amount: Decimal
    currency: str
    payment_provider: str
    provider_payment_id: str

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'subscription.payment.succeeded'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class SubscriptionReactivatedEvent(Event):
    """Event: Subscription was reactivated."""

    subscription_id: int
    user_id: int
    plan_id: int
    admin_id: int
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'subscription.reactivated'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class SubscriptionExpiredEvent(Event):
    """Event: Subscription expired."""

    subscription_id: int
    user_id: int
    plan_id: int
    expired_at: datetime

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'subscription.expired'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
```

---

### 12.2 Invoice Domain Events

**File:** `python/api/src/events/invoice_events.py`

```python
"""Invoice domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal
from .base import Event


@dataclass
class InvoiceCreatedEvent(Event):
    """Event: Invoice was created."""

    invoice_id: int
    user_id: int
    subscription_id: Optional[int] = None
    amount: Decimal = Decimal('0')
    currency: str = 'USD'
    due_date: Optional[datetime] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.created'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoicePaidEvent(Event):
    """Event: Invoice was paid."""

    invoice_id: int
    user_id: int
    amount: Decimal
    currency: str
    payment_provider: str
    provider_payment_id: str
    paid_at: datetime

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.paid'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoiceVoidRequestedEvent(Event):
    """Event: Admin requested to void an invoice."""

    invoice_id: int
    admin_id: int
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.void_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoiceVoidedEvent(Event):
    """Event: Invoice was voided."""

    invoice_id: int
    user_id: int
    amount: Decimal
    admin_id: int
    reason: Optional[str] = None
    voided_at: datetime

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.voided'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoiceRefundRequestedEvent(Event):
    """Event: Admin requested refund."""

    payment_id: int
    invoice_id: int
    amount: Decimal
    admin_id: int
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.refund_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoiceRefundProcessingEvent(Event):
    """Event: Refund is being processed with payment provider."""

    payment_id: int
    invoice_id: int
    amount: Decimal
    payment_provider: str

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.refund.processing'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoiceRefundCompletedEvent(Event):
    """Event: Refund was completed successfully."""

    payment_id: int
    invoice_id: int
    user_id: int
    amount: Decimal
    currency: str
    provider_refund_id: str
    admin_id: int
    completed_at: datetime

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.refund.completed'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class InvoiceRefundFailedEvent(Event):
    """Event: Refund failed."""

    payment_id: int
    invoice_id: int
    amount: Decimal
    error: str
    admin_id: int

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'invoice.refund.failed'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
```

---

### 12.3 SubscriptionCancelHandler

**File:** `python/api/tests/unit/handlers/test_subscription_cancel_handler.py`

```python
"""Tests for SubscriptionCancelHandler."""
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from decimal import Decimal


class TestSubscriptionCancelHandler:
    """Test cases for SubscriptionCancelHandler."""

    def test_can_handle_subscription_cancel_requested(self):
        """can_handle should return True for subscription.cancel_requested."""
        from src.handlers import SubscriptionCancelHandler
        from src.events import SubscriptionCancelRequestedEvent

        mock_subscription_service = Mock()
        mock_payment_service = Mock()
        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = SubscriptionCancelHandler(
            mock_subscription_service,
            mock_payment_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = SubscriptionCancelRequestedEvent(
            subscription_id=1,
            user_id=1,
            admin_id=1,
            reason='Test',
            timestamp=datetime.utcnow()
        )

        assert handler.can_handle(event)

    def test_handle_cancels_subscription_immediately(self):
        """handle should cancel subscription immediately if requested."""
        from src.handlers import SubscriptionCancelHandler
        from src.events import SubscriptionCancelRequestedEvent
        from src.models import Subscription, SubscriptionStatus

        mock_subscription_service = Mock()
        mock_sub = Mock(spec=Subscription)
        mock_sub.id = 1
        mock_sub.user_id = 1
        mock_sub.status = SubscriptionStatus.ACTIVE
        mock_subscription_service.get_by_id.return_value = mock_sub
        mock_subscription_service.cancel.return_value = mock_sub

        mock_payment_service = Mock()
        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = SubscriptionCancelHandler(
            mock_subscription_service,
            mock_payment_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = SubscriptionCancelRequestedEvent(
            subscription_id=1,
            user_id=1,
            admin_id=1,
            immediate=True,
            reason='Immediate cancellation',
            timestamp=datetime.utcnow()
        )

        result = handler.handle(event)

        assert result.success
        mock_subscription_service.cancel.assert_called_once_with(
            subscription_id=1,
            immediate=True
        )

    def test_handle_processes_refund_if_amount_provided(self):
        """handle should process refund if refund_amount provided."""
        from src.handlers import SubscriptionCancelHandler
        from src.events import SubscriptionCancelRequestedEvent
        from src.models import Subscription, SubscriptionStatus

        mock_subscription_service = Mock()
        mock_sub = Mock(spec=Subscription)
        mock_sub.id = 1
        mock_sub.user_id = 1
        mock_sub.status = SubscriptionStatus.ACTIVE
        mock_subscription_service.get_by_id.return_value = mock_sub
        mock_subscription_service.cancel.return_value = mock_sub

        mock_payment_service = Mock()
        mock_payment_service.find_last_payment_for_subscription.return_value = Mock(id=100)

        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = SubscriptionCancelHandler(
            mock_subscription_service,
            mock_payment_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = SubscriptionCancelRequestedEvent(
            subscription_id=1,
            user_id=1,
            admin_id=1,
            immediate=True,
            refund_amount=Decimal('50.00'),
            reason='Cancellation with refund',
            timestamp=datetime.utcnow()
        )

        result = handler.handle(event)

        assert result.success
        # Should emit InvoiceRefundRequestedEvent
        mock_dispatcher.emit.assert_called()

    def test_handle_sends_notification_to_user(self):
        """handle should send notification to user."""
        from src.handlers import SubscriptionCancelHandler
        from src.events import SubscriptionCancelRequestedEvent
        from src.models import Subscription, SubscriptionStatus

        mock_subscription_service = Mock()
        mock_sub = Mock(spec=Subscription)
        mock_sub.id = 1
        mock_sub.user_id = 1
        mock_sub.status = SubscriptionStatus.ACTIVE
        mock_subscription_service.get_by_id.return_value = mock_sub
        mock_subscription_service.cancel.return_value = mock_sub

        mock_payment_service = Mock()
        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = SubscriptionCancelHandler(
            mock_subscription_service,
            mock_payment_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = SubscriptionCancelRequestedEvent(
            subscription_id=1,
            user_id=1,
            immediate=True,
            timestamp=datetime.utcnow()
        )

        handler.handle(event)

        mock_notification_service.notify_user.assert_called_once_with(
            user_id=1,
            template='subscription_cancelled'
        )
```

**File:** `python/api/src/handlers/subscription_cancel_handler.py`

```python
"""Handler for subscription cancellation events."""
import logging
from typing import TYPE_CHECKING
from src.events.base import IEventHandler, Event, EventResult
from src.events.subscription_events import (
    SubscriptionCancelRequestedEvent,
    SubscriptionCancelledEvent
)
from src.events.invoice_events import InvoiceRefundRequestedEvent

if TYPE_CHECKING:
    from src.interfaces import (
        ISubscriptionService,
        IPaymentService,
        IAuditService,
        INotificationService
    )
    from src.events import EventDispatcher

logger = logging.getLogger(__name__)


class SubscriptionCancelHandler(IEventHandler):
    """
    Handler for subscription cancellation requests.

    Responsibilities (SRP):
    - Cancel subscription via SubscriptionService
    - Process refund if requested
    - Log action via AuditService
    - Send notification to user
    - Emit SubscriptionCancelledEvent
    """

    def __init__(
        self,
        subscription_service: 'ISubscriptionService',
        payment_service: 'IPaymentService',
        audit_service: 'IAuditService',
        notification_service: 'INotificationService',
        event_dispatcher: 'EventDispatcher'
    ):
        """Initialize handler with dependencies (DI)."""
        self._subscription_service = subscription_service
        self._payment_service = payment_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the event."""
        return event.name == 'subscription.cancel_requested'

    def handle(self, event: SubscriptionCancelRequestedEvent) -> EventResult:
        """
        Handle subscription cancellation.

        Flow:
        1. Load subscription
        2. Cancel subscription (immediate or end of period)
        3. Process refund if requested
        4. Log action to audit
        5. Send notification to user
        6. Emit SubscriptionCancelledEvent
        """
        logger.info(f"Handling subscription cancellation: sub_id={event.subscription_id}")

        try:
            # 1. Load subscription
            subscription = self._subscription_service.get_by_id(event.subscription_id)
            if not subscription:
                return EventResult.error(f"Subscription {event.subscription_id} not found")

            # 2. Cancel subscription
            cancelled_subscription = self._subscription_service.cancel(
                subscription_id=event.subscription_id,
                immediate=event.immediate
            )

            # 3. Process refund if requested
            if event.refund_amount and event.refund_amount > 0:
                # Find the last payment for this subscription
                payment = self._payment_service.find_last_payment_for_subscription(
                    event.subscription_id
                )

                if payment:
                    # Emit refund request event
                    refund_event = InvoiceRefundRequestedEvent(
                        payment_id=payment.id,
                        invoice_id=payment.invoice_id,
                        amount=event.refund_amount,
                        admin_id=event.admin_id or event.user_id,
                        reason=f"Subscription {event.subscription_id} cancellation refund",
                        timestamp=event.timestamp
                    )
                    self._event_dispatcher.emit(refund_event)

            # 4. Log action
            self._audit_service.log_action(
                admin_id=event.admin_id or event.user_id,
                action='subscription_cancelled',
                resource_type='subscription',
                resource_id=event.subscription_id,
                old_value=str(subscription.status),
                new_value='cancelled',
                reason=event.reason
            )

            # 5. Send notification
            self._notification_service.notify_user(
                user_id=event.user_id,
                template='subscription_cancelled',
                context={
                    'subscription_id': event.subscription_id,
                    'plan_name': subscription.plan.name,
                    'cancellation_type': 'immediate' if event.immediate else 'end_of_period',
                    'refund_amount': str(event.refund_amount) if event.refund_amount else None
                }
            )

            # 6. Emit result event
            result_event = SubscriptionCancelledEvent(
                subscription_id=event.subscription_id,
                user_id=event.user_id,
                plan_id=subscription.plan_id,
                cancellation_type='immediate' if event.immediate else 'end_of_period',
                cancelled_at=cancelled_subscription.cancelled_at,
                ends_at=cancelled_subscription.ends_at,
                refund_amount=event.refund_amount,
                admin_id=event.admin_id,
                reason=event.reason,
                timestamp=event.timestamp
            )
            self._event_dispatcher.emit(result_event)

            logger.info(f"Subscription cancelled successfully: sub_id={event.subscription_id}")
            return EventResult.success(cancelled_subscription.to_dict())

        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}", exc_info=True)
            return EventResult.error(str(e))
```

---

### 12.4 InvoiceRefundHandler

**File:** `python/api/src/handlers/invoice_refund_handler.py`

```python
"""Handler for invoice refund events."""
import logging
from typing import TYPE_CHECKING
from src.events.base import IEventHandler, Event, EventResult
from src.events.invoice_events import (
    InvoiceRefundRequestedEvent,
    InvoiceRefundProcessingEvent,
    InvoiceRefundCompletedEvent,
    InvoiceRefundFailedEvent
)

if TYPE_CHECKING:
    from src.interfaces import (
        IPaymentService,
        IInvoiceService,
        IAuditService,
        INotificationService
    )
    from src.events import EventDispatcher

logger = logging.getLogger(__name__)


class InvoiceRefundHandler(IEventHandler):
    """
    Handler for invoice refund requests.

    Responsibilities (SRP):
    - Process refund via PaymentService
    - Update invoice status via InvoiceService
    - Log action via AuditService
    - Send notification to user
    - Emit InvoiceRefundCompletedEvent or InvoiceRefundFailedEvent
    """

    def __init__(
        self,
        payment_service: 'IPaymentService',
        invoice_service: 'IInvoiceService',
        audit_service: 'IAuditService',
        notification_service: 'INotificationService',
        event_dispatcher: 'EventDispatcher'
    ):
        """Initialize handler with dependencies (DI)."""
        self._payment_service = payment_service
        self._invoice_service = invoice_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the event."""
        return event.name == 'invoice.refund_requested'

    def handle(self, event: InvoiceRefundRequestedEvent) -> EventResult:
        """
        Handle invoice refund request.

        Flow:
        1. Load payment and invoice
        2. Emit InvoiceRefundProcessingEvent
        3. Process refund with payment provider (Stripe/PayPal)
        4. Update invoice status
        5. Log action to audit
        6. Send notification to user
        7. Emit InvoiceRefundCompletedEvent or InvoiceRefundFailedEvent
        """
        logger.info(f"Handling refund request: payment_id={event.payment_id}, amount={event.amount}")

        try:
            # 1. Load payment and invoice
            payment = self._payment_service.get_by_id(event.payment_id)
            if not payment:
                return EventResult.error(f"Payment {event.payment_id} not found")

            invoice = self._invoice_service.get_by_id(event.invoice_id)
            if not invoice:
                return EventResult.error(f"Invoice {event.invoice_id} not found")

            # 2. Emit processing event
            processing_event = InvoiceRefundProcessingEvent(
                payment_id=event.payment_id,
                invoice_id=event.invoice_id,
                amount=event.amount,
                payment_provider=payment.payment_provider,
                timestamp=event.timestamp
            )
            self._event_dispatcher.emit(processing_event)

            # 3. Process refund with payment provider
            try:
                refund_result = self._payment_service.process_refund(
                    payment_id=event.payment_id,
                    amount=event.amount,
                    reason=event.reason
                )
            except Exception as refund_error:
                # Emit failure event
                failure_event = InvoiceRefundFailedEvent(
                    payment_id=event.payment_id,
                    invoice_id=event.invoice_id,
                    amount=event.amount,
                    error=str(refund_error),
                    admin_id=event.admin_id,
                    timestamp=event.timestamp
                )
                self._event_dispatcher.emit(failure_event)
                return EventResult.error(f"Refund failed: {str(refund_error)}")

            # 4. Update invoice status
            self._invoice_service.mark_as_refunded(
                invoice_id=event.invoice_id,
                refund_amount=event.amount
            )

            # 5. Log action
            self._audit_service.log_action(
                admin_id=event.admin_id,
                action='invoice_refunded',
                resource_type='invoice',
                resource_id=event.invoice_id,
                old_value=str(invoice.status),
                new_value='refunded',
                reason=event.reason,
                metadata={
                    'payment_id': event.payment_id,
                    'refund_amount': str(event.amount),
                    'provider_refund_id': refund_result.provider_refund_id
                }
            )

            # 6. Send notification
            self._notification_service.notify_user(
                user_id=invoice.user_id,
                template='refund_processed',
                context={
                    'invoice_id': event.invoice_id,
                    'amount': str(event.amount),
                    'currency': invoice.currency
                }
            )

            # 7. Emit success event
            success_event = InvoiceRefundCompletedEvent(
                payment_id=event.payment_id,
                invoice_id=event.invoice_id,
                user_id=invoice.user_id,
                amount=event.amount,
                currency=invoice.currency,
                provider_refund_id=refund_result.provider_refund_id,
                admin_id=event.admin_id,
                completed_at=refund_result.completed_at,
                timestamp=event.timestamp
            )
            self._event_dispatcher.emit(success_event)

            logger.info(f"Refund processed successfully: payment_id={event.payment_id}")
            return EventResult.success({
                'payment_id': event.payment_id,
                'invoice_id': event.invoice_id,
                'refund_amount': str(event.amount),
                'provider_refund_id': refund_result.provider_refund_id
            })

        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}", exc_info=True)
            return EventResult.error(str(e))
```

---

### 12.5 Integration with Subscription Routes

**File:** `python/api/src/routes/admin/subscriptions.py` (updated)

```python
"""Admin subscription management routes with event-driven architecture."""
from flask import Blueprint, request, jsonify, g
from dependency_injector.wiring import inject, Provide
from datetime import datetime
from decimal import Decimal
from src.container import Container
from src.middleware.auth import require_auth, require_admin
from src.events import (
    EventDispatcher,
    SubscriptionCancelRequestedEvent,
    InvoiceRefundRequestedEvent
)

admin_subscriptions_bp = Blueprint(
    "admin_subscriptions",
    __name__,
    url_prefix="/admin/subscriptions"
)


@admin_subscriptions_bp.route("/<int:subscription_id>/cancel", methods=["POST"])
@require_auth
@require_admin
@inject
def cancel_subscription(
    subscription_id: int,
    event_dispatcher: EventDispatcher = Provide[Container.event_dispatcher],
):
    """
    Cancel subscription (event-driven).

    POST /api/v1/admin/subscriptions/:id/cancel
    Authorization: Bearer <admin-token>
    {
        "immediate": true,
        "refund_amount": "50.00",
        "reason": "Customer request"
    }
    """
    data = request.get_json() or {}
    immediate = data.get('immediate', False)
    refund_amount = data.get('refund_amount')
    reason = data.get('reason')

    # Parse refund amount
    if refund_amount:
        try:
            refund_amount = Decimal(str(refund_amount))
        except:
            return jsonify({'error': 'Invalid refund amount'}), 400

    # Create and emit event
    event = SubscriptionCancelRequestedEvent(
        subscription_id=subscription_id,
        user_id=0,  # Will be loaded from subscription
        admin_id=g.user_id,
        immediate=immediate,
        refund_amount=refund_amount,
        reason=reason,
        timestamp=datetime.utcnow()
    )

    result = event_dispatcher.emit(event)

    if result.success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(result.to_dict()), 400


@admin_subscriptions_bp.route("/<int:subscription_id>/refund", methods=["POST"])
@require_auth
@require_admin
@inject
def refund_subscription_payment(
    subscription_id: int,
    event_dispatcher: EventDispatcher = Provide[Container.event_dispatcher],
):
    """
    Refund subscription payment (event-driven).

    POST /api/v1/admin/subscriptions/:id/refund
    Authorization: Bearer <admin-token>
    {
        "payment_id": 123,
        "amount": "50.00",
        "reason": "Customer complaint"
    }
    """
    data = request.get_json()
    payment_id = data.get('payment_id')
    amount = data.get('amount')
    reason = data.get('reason')

    if not payment_id or not amount:
        return jsonify({'error': 'payment_id and amount required'}), 400

    # Parse amount
    try:
        amount = Decimal(str(amount))
    except:
        return jsonify({'error': 'Invalid amount'}), 400

    # Create and emit event
    event = InvoiceRefundRequestedEvent(
        payment_id=payment_id,
        invoice_id=0,  # Will be loaded from payment
        amount=amount,
        admin_id=g.user_id,
        reason=reason,
        timestamp=datetime.utcnow()
    )

    result = event_dispatcher.emit(event)

    if result.success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(result.to_dict()), 400
```

---

### 12.6 Event Handler Registration

**File:** `python/api/src/container.py` (updated)

```python
"""Dependency injection container (updated)."""
from dependency_injector import containers, providers
from src.events import EventDispatcher
from src.handlers import (
    UserStatusUpdateHandler,
    SubscriptionCancelHandler,
    InvoiceRefundHandler
)


class Container(containers.DeclarativeContainer):
    """Application DI container."""

    # ... previous configuration ...

    # Subscription/Payment Services
    subscription_service = providers.Factory(
        # ... subscription service
    )

    payment_service = providers.Factory(
        # ... payment service
    )

    invoice_service = providers.Factory(
        # ... invoice service
    )

    # Event Handlers
    subscription_cancel_handler = providers.Factory(
        SubscriptionCancelHandler,
        subscription_service=subscription_service,
        payment_service=payment_service,
        audit_service=audit_service,
        notification_service=notification_service,
        event_dispatcher=event_dispatcher
    )

    invoice_refund_handler = providers.Factory(
        InvoiceRefundHandler,
        payment_service=payment_service,
        invoice_service=invoice_service,
        audit_service=audit_service,
        notification_service=notification_service,
        event_dispatcher=event_dispatcher
    )


def configure_event_handlers(container: Container) -> None:
    """Register all event handlers with the dispatcher."""
    dispatcher = container.event_dispatcher()

    # User handlers (from Sprint 11)
    dispatcher.register(
        'user.status.update_requested',
        container.user_status_update_handler()
    )

    # Subscription handlers
    dispatcher.register(
        'subscription.cancel_requested',
        container.subscription_cancel_handler()
    )

    # Invoice handlers
    dispatcher.register(
        'invoice.refund_requested',
        container.invoice_refund_handler()
    )
```

---

## Verification Checklist

```bash
# Run subscription event tests
docker-compose run --rm python pytest tests/unit/handlers/test_subscription*.py -v

# Run invoice event tests
docker-compose run --rm python pytest tests/unit/handlers/test_invoice*.py -v

# Run integration tests
docker-compose run --rm python pytest tests/integration/test_subscription_events.py -v

# Test event-driven cancellation
curl -X POST http://localhost:5000/api/v1/admin/subscriptions/1/cancel \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"immediate": true, "refund_amount": "50.00", "reason": "Customer request"}'

# Test event-driven refund
curl -X POST http://localhost:5000/api/v1/admin/subscriptions/1/refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"payment_id": 123, "amount": "50.00", "reason": "Service issue"}'
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Subscription domain events | [ ] | 6 events for subscription lifecycle |
| Invoice domain events | [ ] | 7 events for invoice/refund lifecycle |
| SubscriptionCancelHandler | [ ] | Event handler with DI |
| InvoiceRefundHandler | [ ] | Event handler with DI |
| Updated admin routes | [ ] | Event-driven endpoints |
| Event handler registration | [ ] | configure_event_handlers() |
| Unit tests | [ ] | 95%+ coverage |
| Integration tests | [ ] | End-to-end event flow |

---

## Event Flow Examples

### Subscription Cancellation Flow

```
Admin clicks "Cancel Subscription"
  ↓
Frontend emits API request
  ↓
Route creates SubscriptionCancelRequestedEvent
  ↓
EventDispatcher → SubscriptionCancelHandler
  ↓
Handler:
  1. Cancels subscription via SubscriptionService
  2. Emits InvoiceRefundRequestedEvent (if refund)
  3. Logs to AuditService
  4. Sends notification to user
  5. Emits SubscriptionCancelledEvent
  ↓
Multiple listeners react:
  - AnalyticsHandler tracks cancellation
  - WebhookHandler notifies external systems
  - EmailHandler sends confirmation email
```

### Invoice Refund Flow

```
Admin clicks "Process Refund"
  ↓
Route creates InvoiceRefundRequestedEvent
  ↓
EventDispatcher → InvoiceRefundHandler
  ↓
Handler:
  1. Emits InvoiceRefundProcessingEvent
  2. Calls PaymentService.process_refund()
     → Stripe/PayPal API call
  3. Updates invoice status
  4. Logs to AuditService
  5. Sends notification to user
  6. Emits InvoiceRefundCompletedEvent
  ↓
Multiple listeners react:
  - AnalyticsHandler tracks refund metrics
  - AccountingHandler updates revenue
  - WebhookHandler notifies external systems
```

---

## Next Sprint

[Sprint 13: Event Handlers for Tickets & Bookings](./sprint-13-event-handlers-tickets-bookings.md) - Event-driven ticket and booking management.
