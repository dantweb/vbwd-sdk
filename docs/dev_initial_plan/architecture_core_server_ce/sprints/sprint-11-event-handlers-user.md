# Sprint 11: Event Handlers for User State Management

**Goal:** Implement event-driven architecture for user state changes with EventDispatcher and domain event handlers.

**Prerequisites:** Sprint 2 complete (AuthService, UserService, user routes)

---

## Objectives

- [ ] EventDispatcher infrastructure
- [ ] Domain event base classes
- [ ] User state change events
- [ ] UserStatusUpdateHandler implementation
- [ ] Event handler registration system
- [ ] Integration with existing user routes
- [ ] Comprehensive unit and integration tests (95%+ coverage)

---

## Tasks

### 11.1 Event System Infrastructure

**TDD Steps:**

#### Step 1: Write failing tests for EventDispatcher

**File:** `python/api/tests/unit/events/test_event_dispatcher.py`

```python
"""Tests for EventDispatcher."""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


class TestEventDispatcher:
    """Test cases for EventDispatcher."""

    def test_register_adds_handler(self):
        """register should add handler for event type."""
        from src.events import EventDispatcher, IEventHandler

        dispatcher = EventDispatcher()
        mock_handler = Mock(spec=IEventHandler)

        dispatcher.register('test.event', mock_handler)

        assert dispatcher.has_handler('test.event')

    def test_emit_calls_handler(self):
        """emit should call registered handler."""
        from src.events import EventDispatcher, Event, IEventHandler, EventResult

        dispatcher = EventDispatcher()
        mock_handler = Mock(spec=IEventHandler)
        mock_handler.can_handle.return_value = True
        mock_handler.handle.return_value = EventResult.success({'user_id': 1})

        dispatcher.register('test.event', mock_handler)

        event = Event(name='test.event', timestamp=datetime.utcnow())
        result = dispatcher.emit(event)

        assert result.success
        mock_handler.handle.assert_called_once_with(event)

    def test_emit_calls_multiple_handlers(self):
        """emit should call all registered handlers for an event."""
        from src.events import EventDispatcher, Event, IEventHandler, EventResult

        dispatcher = EventDispatcher()
        handler1 = Mock(spec=IEventHandler)
        handler1.can_handle.return_value = True
        handler1.handle.return_value = EventResult.success()

        handler2 = Mock(spec=IEventHandler)
        handler2.can_handle.return_value = True
        handler2.handle.return_value = EventResult.success()

        dispatcher.register('test.event', handler1)
        dispatcher.register('test.event', handler2)

        event = Event(name='test.event', timestamp=datetime.utcnow())
        result = dispatcher.emit(event)

        handler1.handle.assert_called_once()
        handler2.handle.assert_called_once()

    def test_emit_returns_no_handler_result_if_no_handlers(self):
        """emit should return no_handler result if no handlers registered."""
        from src.events import EventDispatcher, Event

        dispatcher = EventDispatcher()
        event = Event(name='unknown.event', timestamp=datetime.utcnow())

        result = dispatcher.emit(event)

        assert not result.success
        assert result.error_type == 'no_handler'

    def test_emit_handles_handler_exceptions(self):
        """emit should catch and log handler exceptions."""
        from src.events import EventDispatcher, Event, IEventHandler, EventResult

        dispatcher = EventDispatcher()
        mock_handler = Mock(spec=IEventHandler)
        mock_handler.can_handle.return_value = True
        mock_handler.handle.side_effect = Exception("Handler error")

        dispatcher.register('test.event', mock_handler)

        event = Event(name='test.event', timestamp=datetime.utcnow())
        result = dispatcher.emit(event)

        assert not result.success
        assert "Handler error" in result.error


class TestEventResult:
    """Test cases for EventResult."""

    def test_success_creates_successful_result(self):
        """success should create result with success=True."""
        from src.events import EventResult

        result = EventResult.success({'user_id': 1})

        assert result.success
        assert result.data == {'user_id': 1}
        assert result.error is None

    def test_error_creates_failed_result(self):
        """error should create result with success=False."""
        from src.events import EventResult

        result = EventResult.error('Something went wrong')

        assert not result.success
        assert result.error == 'Something went wrong'
        assert result.data is None

    def test_no_handler_creates_no_handler_result(self):
        """no_handler should create result with no_handler error type."""
        from src.events import EventResult

        result = EventResult.no_handler()

        assert not result.success
        assert result.error_type == 'no_handler'

    def test_combine_merges_multiple_results(self):
        """combine should merge multiple results."""
        from src.events import EventResult

        result1 = EventResult.success({'count': 1})
        result2 = EventResult.success({'count': 2})

        combined = EventResult.combine([result1, result2])

        assert combined.success
        # Combined data should be a list of results
        assert isinstance(combined.data, list)

    def test_combine_fails_if_any_result_fails(self):
        """combine should fail if any result fails."""
        from src.events import EventResult

        result1 = EventResult.success({'count': 1})
        result2 = EventResult.error('Failed')

        combined = EventResult.combine([result1, result2])

        assert not combined.success
```

#### Step 2: Implement EventDispatcher

**File:** `python/api/src/events/__init__.py`

```python
"""Event system package."""
from .base import Event, EventResult, IEventHandler
from .dispatcher import EventDispatcher

__all__ = [
    'Event',
    'EventResult',
    'IEventHandler',
    'EventDispatcher',
]
```

**File:** `python/api/src/events/base.py`

```python
"""Base classes for event system."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod


@dataclass
class Event:
    """
    Base event class.

    All domain events should inherit from this class.
    Events are immutable data structures that represent something that happened.
    """

    name: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure timestamp is set."""
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class EventResult:
    """
    Result of event handling.

    Encapsulates success/failure status and optional data or error.
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

    @classmethod
    def success(cls, data: Any = None) -> 'EventResult':
        """Create successful result."""
        return cls(success=True, data=data)

    @classmethod
    def error(cls, error: str, error_type: str = 'handler_error') -> 'EventResult':
        """Create failed result."""
        return cls(success=False, error=error, error_type=error_type)

    @classmethod
    def no_handler(cls) -> 'EventResult':
        """Create no handler result."""
        return cls(
            success=False,
            error='No handler registered for event',
            error_type='no_handler'
        )

    @classmethod
    def combine(cls, results: List['EventResult']) -> 'EventResult':
        """
        Combine multiple results.

        Returns success if all results succeeded, failure otherwise.
        """
        if not results:
            return cls.success()

        # If any failed, return combined failure
        failed = [r for r in results if not r.success]
        if failed:
            errors = [r.error for r in failed if r.error]
            return cls.error('; '.join(errors))

        # All succeeded, combine data
        data = [r.data for r in results if r.data is not None]
        return cls.success(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'error_type': self.error_type
        }


class IEventHandler(ABC):
    """
    Interface for event handlers.

    All event handlers must implement this interface (LSP).
    """

    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """
        Check if this handler can handle the given event.

        Args:
            event: The event to check.

        Returns:
            True if this handler can handle the event.
        """
        pass

    @abstractmethod
    def handle(self, event: Event) -> EventResult:
        """
        Handle the event.

        Args:
            event: The event to handle.

        Returns:
            EventResult indicating success or failure.
        """
        pass
```

**File:** `python/api/src/events/dispatcher.py`

```python
"""Event dispatcher implementation."""
import logging
from typing import Dict, List
from .base import Event, EventResult, IEventHandler

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Event dispatcher for domain events.

    Routes events to registered handlers using the Observer pattern.
    Follows SOLID principles:
    - SRP: Only responsible for event dispatching
    - OCP: Can add new handlers without modifying dispatcher
    - LSP: All handlers implement IEventHandler interface
    - DI: Handlers are registered/injected
    """

    def __init__(self):
        """Initialize event dispatcher."""
        self._handlers: Dict[str, List[IEventHandler]] = {}

    def register(self, event_type: str, handler: IEventHandler) -> None:
        """
        Register a handler for an event type.

        Args:
            event_type: The event name (e.g., 'user.status.update_requested').
            handler: The handler implementing IEventHandler.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__class__.__name__} for {event_type}")

    def has_handler(self, event_type: str) -> bool:
        """
        Check if any handlers are registered for an event type.

        Args:
            event_type: The event name to check.

        Returns:
            True if at least one handler is registered.
        """
        return event_type in self._handlers and len(self._handlers[event_type]) > 0

    def emit(self, event: Event) -> EventResult:
        """
        Emit an event to all registered handlers.

        Args:
            event: The event to emit.

        Returns:
            Combined EventResult from all handlers.
        """
        handlers = self._handlers.get(event.name, [])

        if not handlers:
            logger.warning(f"No handlers registered for event: {event.name}")
            return EventResult.no_handler()

        results: List[EventResult] = []

        for handler in handlers:
            try:
                # Check if handler can handle this event
                if not handler.can_handle(event):
                    continue

                logger.debug(f"Dispatching {event.name} to {handler.__class__.__name__}")

                # Handle event
                result = handler.handle(event)
                results.append(result)

                if not result.success:
                    logger.warning(
                        f"Handler {handler.__class__.__name__} failed: {result.error}"
                    )

            except Exception as e:
                logger.error(
                    f"Exception in handler {handler.__class__.__name__}: {str(e)}",
                    exc_info=True
                )
                results.append(EventResult.error(str(e)))

        # Combine all results
        return EventResult.combine(results)

    def clear(self, event_type: Optional[str] = None) -> None:
        """
        Clear registered handlers.

        Args:
            event_type: If provided, clear only handlers for this event type.
                       If None, clear all handlers.
        """
        if event_type:
            self._handlers.pop(event_type, None)
        else:
            self._handlers.clear()
```

---

### 11.2 User State Change Events

**File:** `python/api/src/events/user_events.py`

```python
"""User domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .base import Event


@dataclass
class UserStatusUpdateRequestedEvent(Event):
    """
    Event: Admin requested user status update.

    This is a command event that triggers the status update handler.
    """

    user_id: int
    status: str
    admin_id: int
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'user.status.update_requested'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class UserStatusUpdatedEvent(Event):
    """
    Event: User status was updated.

    This is a domain event that notifies other parts of the system
    that a user's status has changed.
    """

    user_id: int
    old_status: str
    new_status: str
    admin_id: int
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'user.status.updated'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class UserCreatedEvent(Event):
    """Event: New user was created."""

    user_id: int
    email: str
    role: str

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'user.created'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class UserDeletedEvent(Event):
    """Event: User was deleted."""

    user_id: int
    admin_id: int
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        self.name = 'user.deleted'
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
```

---

### 11.3 UserStatusUpdateHandler

**File:** `python/api/tests/unit/handlers/test_user_status_handler.py`

```python
"""Tests for UserStatusUpdateHandler."""
import pytest
from unittest.mock import Mock
from datetime import datetime


class TestUserStatusUpdateHandler:
    """Test cases for UserStatusUpdateHandler."""

    def test_can_handle_returns_true_for_user_status_update_requested(self):
        """can_handle should return True for user.status.update_requested."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import UserStatusUpdateRequestedEvent

        mock_user_service = Mock()
        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = UserStatusUpdateRequestedEvent(
            user_id=1,
            status='suspended',
            admin_id=1,
            timestamp=datetime.utcnow()
        )

        assert handler.can_handle(event)

    def test_can_handle_returns_false_for_other_events(self):
        """can_handle should return False for other events."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import Event

        mock_user_service = Mock()
        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = Event(name='other.event', timestamp=datetime.utcnow())

        assert not handler.can_handle(event)

    def test_handle_updates_user_status(self):
        """handle should update user status via UserService."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import UserStatusUpdateRequestedEvent, EventResult
        from src.models import User, UserStatus

        mock_user_service = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.status = UserStatus.ACTIVE
        mock_user_service.get_by_id.return_value = mock_user

        updated_user = Mock(spec=User)
        updated_user.id = 1
        updated_user.status = UserStatus.SUSPENDED
        mock_user_service.update_status.return_value = updated_user

        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = UserStatusUpdateRequestedEvent(
            user_id=1,
            status='suspended',
            admin_id=1,
            timestamp=datetime.utcnow()
        )

        result = handler.handle(event)

        assert result.success
        mock_user_service.update_status.assert_called_once_with(1, 'suspended')

    def test_handle_logs_action_to_audit_service(self):
        """handle should log action to AuditService."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import UserStatusUpdateRequestedEvent
        from src.models import User, UserStatus

        mock_user_service = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.status = UserStatus.ACTIVE
        mock_user_service.get_by_id.return_value = mock_user

        updated_user = Mock(spec=User)
        updated_user.id = 1
        updated_user.status = UserStatus.SUSPENDED
        mock_user_service.update_status.return_value = updated_user

        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = UserStatusUpdateRequestedEvent(
            user_id=1,
            status='suspended',
            admin_id=1,
            timestamp=datetime.utcnow()
        )

        handler.handle(event)

        mock_audit_service.log_action.assert_called_once()
        call_args = mock_audit_service.log_action.call_args
        assert call_args[1]['admin_id'] == 1
        assert call_args[1]['action'] == 'user_status_update'
        assert call_args[1]['resource_type'] == 'user'
        assert call_args[1]['resource_id'] == 1

    def test_handle_sends_notification_for_suspension(self):
        """handle should send notification when user is suspended."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import UserStatusUpdateRequestedEvent
        from src.models import User, UserStatus

        mock_user_service = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.status = UserStatus.ACTIVE
        mock_user_service.get_by_id.return_value = mock_user

        updated_user = Mock(spec=User)
        updated_user.id = 1
        updated_user.status = UserStatus.SUSPENDED
        mock_user_service.update_status.return_value = updated_user

        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = UserStatusUpdateRequestedEvent(
            user_id=1,
            status='suspended',
            admin_id=1,
            timestamp=datetime.utcnow()
        )

        handler.handle(event)

        mock_notification_service.notify_user.assert_called_once_with(
            user_id=1,
            template='account_suspended'
        )

    def test_handle_emits_user_status_updated_event(self):
        """handle should emit UserStatusUpdatedEvent after update."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import UserStatusUpdateRequestedEvent, UserStatusUpdatedEvent
        from src.models import User, UserStatus

        mock_user_service = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.status = UserStatus.ACTIVE
        mock_user_service.get_by_id.return_value = mock_user

        updated_user = Mock(spec=User)
        updated_user.id = 1
        updated_user.status = UserStatus.SUSPENDED
        mock_user_service.update_status.return_value = updated_user

        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = UserStatusUpdateRequestedEvent(
            user_id=1,
            status='suspended',
            admin_id=1,
            timestamp=datetime.utcnow()
        )

        handler.handle(event)

        # Check that dispatcher.emit was called with UserStatusUpdatedEvent
        mock_dispatcher.emit.assert_called_once()
        emitted_event = mock_dispatcher.emit.call_args[0][0]
        assert isinstance(emitted_event, UserStatusUpdatedEvent)
        assert emitted_event.user_id == 1
        assert emitted_event.old_status == UserStatus.ACTIVE
        assert emitted_event.new_status == UserStatus.SUSPENDED

    def test_handle_returns_error_if_user_not_found(self):
        """handle should return error if user not found."""
        from src.handlers import UserStatusUpdateHandler
        from src.events import UserStatusUpdateRequestedEvent

        mock_user_service = Mock()
        mock_user_service.get_by_id.return_value = None

        mock_audit_service = Mock()
        mock_notification_service = Mock()
        mock_dispatcher = Mock()

        handler = UserStatusUpdateHandler(
            mock_user_service,
            mock_audit_service,
            mock_notification_service,
            mock_dispatcher
        )

        event = UserStatusUpdateRequestedEvent(
            user_id=999,
            status='suspended',
            admin_id=1,
            timestamp=datetime.utcnow()
        )

        result = handler.handle(event)

        assert not result.success
        assert 'not found' in result.error.lower()
```

**File:** `python/api/src/handlers/__init__.py`

```python
"""Event handlers package."""
from .user_status_handler import UserStatusUpdateHandler

__all__ = [
    'UserStatusUpdateHandler',
]
```

**File:** `python/api/src/handlers/user_status_handler.py`

```python
"""Handler for user status update events."""
import logging
from typing import TYPE_CHECKING
from src.events.base import IEventHandler, Event, EventResult
from src.events.user_events import UserStatusUpdateRequestedEvent, UserStatusUpdatedEvent
from src.models import UserStatus

if TYPE_CHECKING:
    from src.interfaces import IUserService, IAuditService, INotificationService
    from src.events import EventDispatcher

logger = logging.getLogger(__name__)


class UserStatusUpdateHandler(IEventHandler):
    """
    Handler for user status update requests.

    Responsibilities (SRP):
    - Update user status via UserService
    - Log action via AuditService
    - Send notifications via NotificationService
    - Emit UserStatusUpdatedEvent

    Dependencies injected via constructor (DI).
    """

    def __init__(
        self,
        user_service: 'IUserService',
        audit_service: 'IAuditService',
        notification_service: 'INotificationService',
        event_dispatcher: 'EventDispatcher'
    ):
        """
        Initialize handler with dependencies.

        Args:
            user_service: Service for user operations.
            audit_service: Service for audit logging.
            notification_service: Service for notifications.
            event_dispatcher: Event dispatcher for emitting result events.
        """
        self._user_service = user_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: Event) -> bool:
        """
        Check if this handler can handle the event.

        Args:
            event: The event to check.

        Returns:
            True if event is UserStatusUpdateRequestedEvent.
        """
        return event.name == 'user.status.update_requested'

    def handle(self, event: UserStatusUpdateRequestedEvent) -> EventResult:
        """
        Handle user status update request.

        Flow:
        1. Load current user
        2. Update status
        3. Log action to audit
        4. Send notification if suspended
        5. Emit UserStatusUpdatedEvent
        6. Return result

        Args:
            event: The user status update requested event.

        Returns:
            EventResult indicating success or failure.
        """
        logger.info(f"Handling user status update: user_id={event.user_id}, status={event.status}")

        try:
            # 1. Load current user
            user = self._user_service.get_by_id(event.user_id)
            if not user:
                return EventResult.error(f"User {event.user_id} not found")

            old_status = user.status

            # 2. Update status
            updated_user = self._user_service.update_status(event.user_id, event.status)

            # 3. Log action to audit
            self._audit_service.log_action(
                admin_id=event.admin_id,
                action='user_status_update',
                resource_type='user',
                resource_id=event.user_id,
                old_value=old_status,
                new_value=event.status,
                reason=event.reason
            )

            # 4. Send notification if suspended
            if event.status == UserStatus.SUSPENDED:
                self._notification_service.notify_user(
                    user_id=event.user_id,
                    template='account_suspended'
                )

            # 5. Emit result event
            result_event = UserStatusUpdatedEvent(
                user_id=event.user_id,
                old_status=old_status,
                new_status=event.status,
                admin_id=event.admin_id,
                reason=event.reason,
                timestamp=event.timestamp
            )
            self._event_dispatcher.emit(result_event)

            # 6. Return success
            logger.info(f"User status updated successfully: user_id={event.user_id}")
            return EventResult.success(updated_user.to_dict())

        except Exception as e:
            logger.error(f"Error updating user status: {str(e)}", exc_info=True)
            return EventResult.error(str(e))
```

---

### 11.4 Integration with User Routes

**File:** `python/api/src/routes/admin/users.py` (updated)

```python
"""Admin user management routes with event-driven architecture."""
from flask import Blueprint, request, jsonify, g
from dependency_injector.wiring import inject, Provide
from marshmallow import ValidationError
from src.container import Container
from src.interfaces import IUserService
from src.middleware.auth import require_auth, require_admin
from src.schemas.auth import UserSchema
from src.events import EventDispatcher, UserStatusUpdateRequestedEvent
from datetime import datetime

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")

user_schema = UserSchema()


@admin_users_bp.route("/<int:user_id>/status", methods=["PUT"])
@require_auth
@require_admin
@inject
def update_user_status(
    user_id: int,
    event_dispatcher: EventDispatcher = Provide[Container.event_dispatcher],
):
    """
    Update user status (event-driven).

    PUT /api/v1/admin/users/:id/status
    Authorization: Bearer <admin-token>
    {
        "status": "suspended",
        "reason": "Policy violation"
    }
    """
    # Parse request
    data = request.get_json()
    status = data.get('status')
    reason = data.get('reason')

    if not status:
        return jsonify({'error': 'Status required'}), 400

    # Validate status
    valid_statuses = ['active', 'suspended', 'pending', 'deleted']
    if status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    # Create and emit event
    event = UserStatusUpdateRequestedEvent(
        user_id=user_id,
        status=status,
        admin_id=g.user_id,
        reason=reason,
        timestamp=datetime.utcnow()
    )

    result = event_dispatcher.emit(event)

    # Return result
    if result.success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(result.to_dict()), 400


@admin_users_bp.route("/<int:user_id>", methods=["DELETE"])
@require_auth
@require_admin
@inject
def delete_user(
    user_id: int,
    event_dispatcher: EventDispatcher = Provide[Container.event_dispatcher],
):
    """
    Delete user (event-driven).

    DELETE /api/v1/admin/users/:id
    Authorization: Bearer <admin-token>
    {
        "reason": "User requested account deletion"
    }
    """
    from src.events import UserDeletedEvent

    data = request.get_json() or {}
    reason = data.get('reason')

    # Create and emit event
    event = UserStatusUpdateRequestedEvent(
        user_id=user_id,
        status='deleted',
        admin_id=g.user_id,
        reason=reason,
        timestamp=datetime.utcnow()
    )

    result = event_dispatcher.emit(event)

    if result.success:
        # Also emit UserDeletedEvent for other listeners
        deleted_event = UserDeletedEvent(
            user_id=user_id,
            admin_id=g.user_id,
            reason=reason,
            timestamp=datetime.utcnow()
        )
        event_dispatcher.emit(deleted_event)

        return jsonify(result.to_dict()), 200
    else:
        return jsonify(result.to_dict()), 400
```

---

### 11.5 Event Handler Registration

**File:** `python/api/src/container.py` (updated)

```python
"""Dependency injection container."""
from dependency_injector import containers, providers
from src.events import EventDispatcher
from src.handlers import UserStatusUpdateHandler


class Container(containers.DeclarativeContainer):
    """Application DI container."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.routes.auth",
            "src.routes.user",
            "src.routes.admin.users",
        ]
    )

    # Configuration
    config = providers.Configuration()

    # Database
    db = providers.Singleton(
        # ... database setup
    )

    # Repositories
    user_repository = providers.Factory(
        # ... user repository
    )

    # Services
    auth_service = providers.Factory(
        # ... auth service
    )

    user_service = providers.Factory(
        # ... user service
    )

    audit_service = providers.Factory(
        # ... audit service
    )

    notification_service = providers.Factory(
        # ... notification service
    )

    # Event System
    event_dispatcher = providers.Singleton(
        EventDispatcher
    )

    # Event Handlers
    user_status_update_handler = providers.Factory(
        UserStatusUpdateHandler,
        user_service=user_service,
        audit_service=audit_service,
        notification_service=notification_service,
        event_dispatcher=event_dispatcher
    )


def configure_event_handlers(container: Container) -> None:
    """
    Register all event handlers with the dispatcher.

    This should be called during application initialization.
    """
    dispatcher = container.event_dispatcher()

    # Register user handlers
    dispatcher.register(
        'user.status.update_requested',
        container.user_status_update_handler()
    )

    # More handlers will be registered here in future sprints
```

**File:** `python/api/src/app.py` (updated)

```python
"""Flask application factory."""
from flask import Flask
from src.container import Container, configure_event_handlers
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.admin.users import admin_users_bp


def create_app(config=None):
    """Create Flask application."""
    app = Flask(__name__)

    # Load config
    if config:
        app.config.from_mapping(config)

    # Setup DI container
    container = Container()
    container.config.from_dict(app.config)
    app.container = container

    # Configure event handlers
    configure_event_handlers(container)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(user_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_users_bp, url_prefix='/api/v1')

    return app
```

---

## Verification Checklist

```bash
# Run event system tests
docker-compose run --rm python pytest tests/unit/events/ -v

# Run handler tests
docker-compose run --rm python pytest tests/unit/handlers/ -v

# Run integration tests
docker-compose run --rm python pytest tests/integration/test_user_status_events.py -v

# Run all Sprint 11 tests
docker-compose run --rm python pytest tests/unit/events/ tests/unit/handlers/ -v

# Test event-driven route manually
docker-compose up -d

# Login as admin
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass"}'

# Update user status (event-driven)
curl -X PUT http://localhost:5000/api/v1/admin/users/2/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"status": "suspended", "reason": "Policy violation"}'
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| EventDispatcher | [ ] | Core event routing |
| Event base classes | [ ] | Event, EventResult, IEventHandler |
| User domain events | [ ] | UserStatusUpdateRequestedEvent, UserStatusUpdatedEvent |
| UserStatusUpdateHandler | [ ] | Event handler with DI |
| Event handler registration | [ ] | configure_event_handlers() |
| Updated admin routes | [ ] | Event-driven user status endpoint |
| Unit tests | [ ] | 95%+ coverage |
| Integration tests | [ ] | End-to-end event flow |

---

## Benefits of Event-Driven Architecture

**Decoupling:**
- Routes only emit events, don't call services directly
- Handlers don't know about HTTP layer
- Easy to add new handlers without modifying existing code (OCP)

**Auditability:**
- All state changes go through events
- Complete audit trail with timestamps
- Easy to track who did what when

**Testability:**
- Mock EventDispatcher in route tests
- Test handlers independently with mocked services
- No need for complex integration tests

**Extensibility:**
- Add analytics handler to track user suspensions
- Add webhook handler to notify external systems
- Add caching handler to invalidate caches
- All without modifying existing handlers (OCP)

**SOLID Principles:**
- **SRP:** Each handler has one responsibility
- **OCP:** Add new handlers without modifying dispatcher
- **LSP:** All handlers implement IEventHandler interface
- **ISP:** Focused interfaces (IEventHandler, IUserService, etc.)
- **DI:** All dependencies injected via constructor

---

## Next Sprint

[Sprint 12: Event Handlers for Subscriptions & Invoices](./sprint-12-event-handlers-subscriptions.md) - Event-driven subscription lifecycle management.
