# Sprint 6: Booking System - Database Models & Services

**Goal:** Implement database models and core services for the booking system
**Dependencies:** Sprint 1 (Data Layer), Sprint 2 (Auth), Sprint 4 (Payments)

---

## Objectives

- [ ] Create Room, Timeslot, Booking database models
- [ ] Create BookingReminder model for notifications
- [ ] Implement BookingService with business logic
- [ ] Implement TimeslotGeneratorService
- [ ] Create database migrations
- [ ] Write comprehensive unit tests (95%+ coverage)

---

## Database Models

### 1. Room Model

**File:** `python/api/src/models/room.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, Enum, JSON, DateTime
from sqlalchemy.orm import relationship
from src.models.base import Base

class RoomType(str, Enum):
    OFFICE = 'office'
    CONSULTATION = 'consultation'
    MEETING = 'meeting'
    TREATMENT = 'treatment'

class Room(Base):
    """
    Room entity for booking appointments.

    Represents a physical or virtual space that can be reserved.
    Examples: consultation room, meeting room, treatment room.
    """
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    capacity = Column(Integer, default=1)
    room_type = Column(
        Enum('office', 'consultation', 'meeting', 'treatment', name='room_type_enum'),
        nullable=False
    )
    hourly_rate = Column(Decimal(10, 2))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    timeslots = relationship('Timeslot', back_populates='room', cascade='all, delete-orphan')
    bookings = relationship('Booking', back_populates='room')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'capacity': self.capacity,
            'roomType': self.room_type,
            'hourlyRate': float(self.hourly_rate) if self.hourly_rate else None,
            'isActive': self.is_active,
            'metadata': self.metadata,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}', type='{self.room_type}')>"
```

### 2. Timeslot Model

**File:** `python/api/src/models/timeslot.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Decimal, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class Timeslot(Base):
    """
    Timeslot entity representing a bookable time period.

    Discrete time blocks within a room's schedule.
    Auto-generated based on working hours configuration.
    """
    __tablename__ = 'timeslots'
    __table_args__ = (
        Index('idx_room_time', 'room_id', 'start_time', 'end_time'),
        Index('idx_availability', 'is_available', 'start_time'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)
    price = Column(Decimal(10, 2))
    max_bookings = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    room = relationship('Room', back_populates='timeslots')
    bookings = relationship('Booking', back_populates='timeslot')

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def is_past(self) -> bool:
        """Check if timeslot has passed"""
        return datetime.utcnow() > self.end_time

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'roomId': self.room_id,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'isAvailable': self.is_available,
            'price': float(self.price) if self.price else None,
            'maxBookings': self.max_bookings,
            'durationMinutes': self.duration_minutes,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Timeslot(id={self.id}, room={self.room_id}, start='{self.start_time}')>"
```

### 3. Booking Model

**File:** `python/api/src/models/booking.py`

```python
from datetime import datetime
from decimal import Decimal as DecimalType
from sqlalchemy import Column, Integer, String, ForeignKey, Decimal, Text, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class BookingStatus:
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'

class PaymentStatus:
    PENDING = 'pending'
    PAID = 'paid'
    REFUNDED = 'refunded'

class Booking(Base):
    """
    Booking entity representing a user's reservation.

    Links a user to a specific timeslot and room.
    Tracks payment status and booking lifecycle.
    """
    __tablename__ = 'bookings'
    __table_args__ = (
        Index('idx_user_bookings', 'user_id', 'status'),
        Index('idx_timeslot', 'timeslot_id'),
        Index('idx_status', 'status', 'created_at'),
        Index('idx_payment', 'payment_status', 'payment_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    timeslot_id = Column(Integer, ForeignKey('timeslots.id', ondelete='RESTRICT'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='RESTRICT'), nullable=False)
    status = Column(
        Enum('pending', 'confirmed', 'cancelled', 'completed', 'no_show', name='booking_status_enum'),
        default='pending'
    )
    booking_type = Column(String(50))
    price = Column(Decimal(10, 2), nullable=False)
    payment_status = Column(
        Enum('pending', 'paid', 'refunded', name='booking_payment_status_enum'),
        default='pending'
    )
    payment_id = Column(String(255))
    notes = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='bookings')
    timeslot = relationship('Timeslot', back_populates='bookings')
    room = relationship('Room', back_populates='bookings')
    reminders = relationship('BookingReminder', back_populates='booking', cascade='all, delete-orphan')

    @property
    def is_cancellable(self) -> bool:
        """Check if booking can be cancelled"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]

    @property
    def is_modifiable(self) -> bool:
        """Check if booking can be modified"""
        return self.status == BookingStatus.CONFIRMED and not self.timeslot.is_past

    def to_dict(self, include_relations: bool = False) -> dict:
        result = {
            'id': self.id,
            'userId': self.user_id,
            'timeslotId': self.timeslot_id,
            'roomId': self.room_id,
            'status': self.status,
            'bookingType': self.booking_type,
            'price': float(self.price),
            'paymentStatus': self.payment_status,
            'paymentId': self.payment_id,
            'notes': self.notes,
            'metadata': self.metadata,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'cancelledAt': self.cancelled_at.isoformat() if self.cancelled_at else None,
        }

        if include_relations:
            if self.room:
                result['room'] = self.room.to_dict()
            if self.timeslot:
                result['timeslot'] = self.timeslot.to_dict()

        return result

    def __repr__(self):
        return f"<Booking(id={self.id}, user={self.user_id}, status='{self.status}')>"
```

### 4. BookingReminder Model

**File:** `python/api/src/models/booking_reminder.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class ReminderType:
    EMAIL_24H = 'email_24h'
    EMAIL_1H = 'email_1h'
    SMS = 'sms'

class ReminderStatus:
    PENDING = 'pending'
    SENT = 'sent'
    CANCELLED = 'cancelled'
    FAILED = 'failed'

class BookingReminder(Base):
    """
    Reminder entity for booking notifications.

    Tracks scheduled reminders and their delivery status.
    """
    __tablename__ = 'booking_reminders'
    __table_args__ = (
        Index('idx_scheduled', 'status', 'scheduled_at'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    reminder_type = Column(
        Enum('email_24h', 'email_1h', 'sms', name='reminder_type_enum'),
        nullable=False
    )
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(
        Enum('pending', 'sent', 'cancelled', 'failed', name='reminder_status_enum'),
        default='pending'
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    booking = relationship('Booking', back_populates='reminders')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'bookingId': self.booking_id,
            'reminderType': self.reminder_type,
            'scheduledAt': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sentAt': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<BookingReminder(id={self.id}, booking={self.booking_id}, type='{self.reminder_type}')>"
```

---

## Services

### 5. BookingService

**File:** `python/api/src/services/booking_service.py`

```python
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from src.models.booking import Booking, BookingStatus, PaymentStatus
from src.models.timeslot import Timeslot
from src.models.room import Room
from src.models.booking_reminder import BookingReminder, ReminderType, ReminderStatus

class BookingError(Exception):
    """Custom exception for booking operations"""
    pass

class BookingService:
    """
    Business logic for booking management.

    Handles booking creation, confirmation, cancellation,
    rescheduling, and refund calculations.
    """

    # Refund policy constants
    FULL_REFUND_HOURS = 24
    PARTIAL_REFUND_HOURS = 6
    PARTIAL_REFUND_PERCENTAGE = 0.5

    @staticmethod
    def get_available_timeslots(
        db: Session,
        room_id: int,
        date: datetime,
        duration_minutes: int = 30
    ) -> List[Timeslot]:
        """
        Get available timeslots for a room on a specific date.

        Args:
            db: Database session
            room_id: Room identifier
            date: Target date
            duration_minutes: Minimum slot duration

        Returns:
            List of available timeslots
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return db.query(Timeslot).filter(
            Timeslot.room_id == room_id,
            Timeslot.start_time >= start_of_day,
            Timeslot.start_time < end_of_day,
            Timeslot.is_available == True,
            Timeslot.start_time > datetime.utcnow()  # Only future slots
        ).order_by(Timeslot.start_time).all()

    @staticmethod
    def create_booking(
        db: Session,
        user_id: int,
        timeslot_id: int,
        room_id: int,
        notes: Optional[str] = None,
        booking_type: Optional[str] = None
    ) -> Booking:
        """
        Create a new pending booking.

        Args:
            db: Database session
            user_id: User making the booking
            timeslot_id: Timeslot to reserve
            room_id: Room being booked
            notes: Optional booking notes
            booking_type: Optional category/type

        Returns:
            Created booking

        Raises:
            BookingError: If timeslot unavailable or room not found
        """
        # Validate timeslot
        timeslot = db.query(Timeslot).filter(Timeslot.id == timeslot_id).first()
        if not timeslot:
            raise BookingError("Timeslot not found")

        if not timeslot.is_available:
            raise BookingError("Timeslot is not available")

        if timeslot.is_past:
            raise BookingError("Cannot book past timeslots")

        # Validate room
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise BookingError("Room not found")

        if not room.is_active:
            raise BookingError("Room is not active")

        # Verify timeslot belongs to room
        if timeslot.room_id != room_id:
            raise BookingError("Timeslot does not belong to specified room")

        # Create booking
        booking = Booking(
            user_id=user_id,
            timeslot_id=timeslot_id,
            room_id=room_id,
            price=timeslot.price or Decimal('0.00'),
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            booking_type=booking_type,
            notes=notes
        )

        # Temporarily reserve timeslot
        timeslot.is_available = False

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def confirm_booking(
        db: Session,
        booking_id: int,
        payment_id: str
    ) -> Booking:
        """
        Confirm booking after successful payment.

        Args:
            db: Database session
            booking_id: Booking to confirm
            payment_id: Payment reference

        Returns:
            Confirmed booking
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise BookingError("Booking not found")

        if booking.status != BookingStatus.PENDING:
            raise BookingError(f"Cannot confirm booking with status: {booking.status}")

        # Update booking
        booking.status = BookingStatus.CONFIRMED
        booking.payment_status = PaymentStatus.PAID
        booking.payment_id = payment_id

        # Schedule reminders
        BookingService._schedule_reminders(db, booking)

        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def cancel_booking(
        db: Session,
        booking_id: int,
        cancelled_by_admin: bool = False
    ) -> Dict:
        """
        Cancel booking and calculate refund.

        Args:
            db: Database session
            booking_id: Booking to cancel
            cancelled_by_admin: Whether cancelled by admin

        Returns:
            Dict with booking and refund_amount
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise BookingError("Booking not found")

        if not booking.is_cancellable:
            raise BookingError(f"Cannot cancel booking with status: {booking.status}")

        # Calculate refund
        refund_amount = BookingService._calculate_refund(booking)

        # Update booking
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()

        if refund_amount > 0:
            booking.payment_status = PaymentStatus.REFUNDED

        # Release timeslot
        timeslot = db.query(Timeslot).filter(Timeslot.id == booking.timeslot_id).first()
        if timeslot:
            timeslot.is_available = True

        # Cancel pending reminders
        db.query(BookingReminder).filter(
            BookingReminder.booking_id == booking_id,
            BookingReminder.status == ReminderStatus.PENDING
        ).update({'status': ReminderStatus.CANCELLED})

        db.commit()
        db.refresh(booking)

        return {
            'booking': booking,
            'refund_amount': float(refund_amount)
        }

    @staticmethod
    def reschedule_booking(
        db: Session,
        booking_id: int,
        new_timeslot_id: int
    ) -> Booking:
        """
        Reschedule booking to a new timeslot.

        Args:
            db: Database session
            booking_id: Booking to reschedule
            new_timeslot_id: New timeslot

        Returns:
            Updated booking
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise BookingError("Booking not found")

        if not booking.is_modifiable:
            raise BookingError("Booking cannot be rescheduled")

        new_timeslot = db.query(Timeslot).filter(Timeslot.id == new_timeslot_id).first()
        if not new_timeslot:
            raise BookingError("New timeslot not found")

        if not new_timeslot.is_available:
            raise BookingError("New timeslot is not available")

        if new_timeslot.room_id != booking.room_id:
            raise BookingError("New timeslot must be in the same room")

        # Release old timeslot
        old_timeslot = db.query(Timeslot).filter(Timeslot.id == booking.timeslot_id).first()
        if old_timeslot:
            old_timeslot.is_available = True

        # Reserve new timeslot
        new_timeslot.is_available = False

        # Update booking
        booking.timeslot_id = new_timeslot_id
        booking.price = new_timeslot.price or booking.price

        # Reschedule reminders
        db.query(BookingReminder).filter(
            BookingReminder.booking_id == booking_id,
            BookingReminder.status == ReminderStatus.PENDING
        ).delete()
        BookingService._schedule_reminders(db, booking)

        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def complete_booking(db: Session, booking_id: int) -> Booking:
        """Mark booking as completed"""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise BookingError("Booking not found")

        if booking.status != BookingStatus.CONFIRMED:
            raise BookingError(f"Cannot complete booking with status: {booking.status}")

        booking.status = BookingStatus.COMPLETED
        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def mark_no_show(db: Session, booking_id: int) -> Booking:
        """Mark booking as no-show"""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise BookingError("Booking not found")

        if booking.status != BookingStatus.CONFIRMED:
            raise BookingError(f"Cannot mark no-show for booking with status: {booking.status}")

        booking.status = BookingStatus.NO_SHOW
        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def _calculate_refund(booking: Booking) -> Decimal:
        """
        Calculate refund based on cancellation policy.

        Policy:
        - 24+ hours before: 100% refund
        - 6-24 hours before: 50% refund
        - Less than 6 hours: No refund
        """
        if booking.payment_status != PaymentStatus.PAID:
            return Decimal('0.00')

        now = datetime.utcnow()
        hours_before = (booking.timeslot.start_time - now).total_seconds() / 3600

        if hours_before >= BookingService.FULL_REFUND_HOURS:
            return booking.price
        elif hours_before >= BookingService.PARTIAL_REFUND_HOURS:
            return booking.price * Decimal(str(BookingService.PARTIAL_REFUND_PERCENTAGE))
        else:
            return Decimal('0.00')

    @staticmethod
    def _schedule_reminders(db: Session, booking: Booking) -> None:
        """Schedule email reminders for confirmed booking"""
        appointment_time = booking.timeslot.start_time

        # 24-hour reminder
        reminder_24h = BookingReminder(
            booking_id=booking.id,
            reminder_type=ReminderType.EMAIL_24H,
            scheduled_at=appointment_time - timedelta(hours=24),
            status=ReminderStatus.PENDING
        )

        # 1-hour reminder
        reminder_1h = BookingReminder(
            booking_id=booking.id,
            reminder_type=ReminderType.EMAIL_1H,
            scheduled_at=appointment_time - timedelta(hours=1),
            status=ReminderStatus.PENDING
        )

        db.add_all([reminder_24h, reminder_1h])
```

### 6. TimeslotGeneratorService

**File:** `python/api/src/services/timeslot_generator_service.py`

```python
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models.timeslot import Timeslot
from src.models.room import Room

class TimeslotGeneratorService:
    """
    Service for generating timeslots based on working hours configuration.
    """

    @staticmethod
    def generate_timeslots(
        db: Session,
        room_id: int,
        start_date: datetime,
        end_date: datetime,
        slot_duration_minutes: int = 30,
        working_hours: Optional[Dict[str, str]] = None,
        excluded_dates: Optional[List[datetime]] = None,
        price_override: Optional[Decimal] = None
    ) -> List[Timeslot]:
        """
        Generate timeslots for a room over a date range.

        Args:
            db: Database session
            room_id: Room to generate slots for
            start_date: Start of generation range
            end_date: End of generation range
            slot_duration_minutes: Duration of each slot
            working_hours: Dict with 'start' and 'end' times (e.g., {'start': '09:00', 'end': '17:00'})
            excluded_dates: List of dates to skip (holidays, etc.)
            price_override: Override room's hourly rate for price calculation

        Returns:
            List of created timeslots
        """
        if working_hours is None:
            working_hours = {'start': '09:00', 'end': '17:00'}

        if excluded_dates is None:
            excluded_dates = []

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Room not found")

        # Calculate price per slot
        hourly_rate = price_override or room.hourly_rate or Decimal('0.00')
        slot_price = hourly_rate * Decimal(slot_duration_minutes) / Decimal('60')

        timeslots = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        while current_date < end_date:
            # Skip weekends (optional, can be configurable)
            if current_date.weekday() < 5 and current_date not in excluded_dates:
                # Parse working hours
                start_hour, start_minute = map(int, working_hours['start'].split(':'))
                end_hour, end_minute = map(int, working_hours['end'].split(':'))

                slot_start = current_date.replace(
                    hour=start_hour, minute=start_minute, second=0, microsecond=0
                )
                day_end = current_date.replace(
                    hour=end_hour, minute=end_minute, second=0, microsecond=0
                )

                while slot_start + timedelta(minutes=slot_duration_minutes) <= day_end:
                    slot_end = slot_start + timedelta(minutes=slot_duration_minutes)

                    # Check for existing timeslot
                    existing = db.query(Timeslot).filter(
                        Timeslot.room_id == room_id,
                        Timeslot.start_time == slot_start
                    ).first()

                    if not existing:
                        timeslot = Timeslot(
                            room_id=room_id,
                            start_time=slot_start,
                            end_time=slot_end,
                            is_available=True,
                            price=slot_price,
                            max_bookings=1
                        )
                        timeslots.append(timeslot)

                    slot_start = slot_end

            current_date += timedelta(days=1)

        if timeslots:
            db.add_all(timeslots)
            db.commit()

        return timeslots

    @staticmethod
    def generate_custom_timeslots(
        db: Session,
        room_id: int,
        slots: List[Dict]
    ) -> List[Timeslot]:
        """
        Generate custom timeslots from a list of definitions.

        Args:
            db: Database session
            room_id: Room identifier
            slots: List of dicts with 'start_time', 'end_time', 'price'

        Returns:
            List of created timeslots
        """
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Room not found")

        timeslots = []
        for slot_def in slots:
            timeslot = Timeslot(
                room_id=room_id,
                start_time=slot_def['start_time'],
                end_time=slot_def['end_time'],
                is_available=True,
                price=slot_def.get('price', room.hourly_rate),
                max_bookings=slot_def.get('max_bookings', 1)
            )
            timeslots.append(timeslot)

        if timeslots:
            db.add_all(timeslots)
            db.commit()

        return timeslots
```

---

## Database Migration

**File:** `python/api/migrations/versions/xxx_add_booking_tables.py`

```python
"""Add booking system tables

Revision ID: xxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('capacity', sa.Integer(), default=1),
        sa.Column('room_type', sa.Enum('office', 'consultation', 'meeting', 'treatment', name='room_type_enum'), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create timeslots table
    op.create_table(
        'timeslots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('is_available', sa.Boolean(), default=True),
        sa.Column('price', sa.Numeric(10, 2)),
        sa.Column('max_bookings', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('idx_room_time', 'timeslots', ['room_id', 'start_time', 'end_time'])
    op.create_index('idx_availability', 'timeslots', ['is_available', 'start_time'])

    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timeslot_id', sa.Integer(), sa.ForeignKey('timeslots.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('rooms.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'cancelled', 'completed', 'no_show', name='booking_status_enum'), default='pending'),
        sa.Column('booking_type', sa.String(50)),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('payment_status', sa.Enum('pending', 'paid', 'refunded', name='booking_payment_status_enum'), default='pending'),
        sa.Column('payment_id', sa.String(255)),
        sa.Column('notes', sa.Text()),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('cancelled_at', sa.DateTime()),
    )
    op.create_index('idx_user_bookings', 'bookings', ['user_id', 'status'])
    op.create_index('idx_timeslot', 'bookings', ['timeslot_id'])
    op.create_index('idx_status', 'bookings', ['status', 'created_at'])
    op.create_index('idx_payment', 'bookings', ['payment_status', 'payment_id'])

    # Create booking_reminders table
    op.create_table(
        'booking_reminders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('booking_id', sa.Integer(), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reminder_type', sa.Enum('email_24h', 'email_1h', 'sms', name='reminder_type_enum'), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime()),
        sa.Column('status', sa.Enum('pending', 'sent', 'cancelled', 'failed', name='reminder_status_enum'), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('idx_scheduled', 'booking_reminders', ['status', 'scheduled_at'])

def downgrade():
    op.drop_table('booking_reminders')
    op.drop_table('bookings')
    op.drop_table('timeslots')
    op.drop_table('rooms')
```

---

## Unit Tests

**File:** `python/api/tests/unit/test_booking_service.py`

```python
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from src.services.booking_service import BookingService, BookingError
from src.models.booking import BookingStatus, PaymentStatus

class TestBookingService:
    """Test suite for BookingService"""

    def test_create_booking_success(self, db_session, test_user, test_room, test_timeslot):
        """Test successful booking creation"""
        booking = BookingService.create_booking(
            db_session,
            user_id=test_user.id,
            timeslot_id=test_timeslot.id,
            room_id=test_room.id,
            notes="Test booking"
        )

        assert booking.id is not None
        assert booking.status == BookingStatus.PENDING
        assert booking.payment_status == PaymentStatus.PENDING
        assert booking.user_id == test_user.id

    def test_create_booking_unavailable_timeslot(self, db_session, test_user, test_room, unavailable_timeslot):
        """Test booking creation fails for unavailable timeslot"""
        with pytest.raises(BookingError, match="not available"):
            BookingService.create_booking(
                db_session,
                user_id=test_user.id,
                timeslot_id=unavailable_timeslot.id,
                room_id=test_room.id
            )

    def test_confirm_booking(self, db_session, pending_booking):
        """Test booking confirmation"""
        booking = BookingService.confirm_booking(
            db_session,
            booking_id=pending_booking.id,
            payment_id="PAY-12345"
        )

        assert booking.status == BookingStatus.CONFIRMED
        assert booking.payment_status == PaymentStatus.PAID
        assert booking.payment_id == "PAY-12345"

    def test_cancel_booking_full_refund(self, db_session, confirmed_booking):
        """Test cancellation with full refund (24+ hours before)"""
        confirmed_booking.timeslot.start_time = datetime.utcnow() + timedelta(hours=48)
        confirmed_booking.payment_status = PaymentStatus.PAID

        result = BookingService.cancel_booking(db_session, confirmed_booking.id)

        assert result['booking'].status == BookingStatus.CANCELLED
        assert result['refund_amount'] == float(confirmed_booking.price)

    def test_cancel_booking_partial_refund(self, db_session, confirmed_booking):
        """Test cancellation with 50% refund (6-24 hours before)"""
        confirmed_booking.timeslot.start_time = datetime.utcnow() + timedelta(hours=12)
        confirmed_booking.payment_status = PaymentStatus.PAID

        result = BookingService.cancel_booking(db_session, confirmed_booking.id)

        assert result['refund_amount'] == float(confirmed_booking.price) * 0.5

    def test_cancel_booking_no_refund(self, db_session, confirmed_booking):
        """Test cancellation with no refund (<6 hours before)"""
        confirmed_booking.timeslot.start_time = datetime.utcnow() + timedelta(hours=2)
        confirmed_booking.payment_status = PaymentStatus.PAID

        result = BookingService.cancel_booking(db_session, confirmed_booking.id)

        assert result['refund_amount'] == 0

    def test_reschedule_booking(self, db_session, confirmed_booking, available_timeslot):
        """Test booking rescheduling"""
        old_timeslot_id = confirmed_booking.timeslot_id

        booking = BookingService.reschedule_booking(
            db_session,
            booking_id=confirmed_booking.id,
            new_timeslot_id=available_timeslot.id
        )

        assert booking.timeslot_id == available_timeslot.id
        assert booking.timeslot_id != old_timeslot_id
```

---

## Definition of Done

- [ ] All database models created with proper relationships
- [ ] Database migrations tested and working
- [ ] BookingService with all CRUD operations
- [ ] TimeslotGeneratorService for batch slot creation
- [ ] Refund calculation logic implemented
- [ ] Reminder scheduling implemented
- [ ] Unit tests with 95%+ coverage
- [ ] Integration tests for database operations
- [ ] Code reviewed and approved

---

## Related Documentation

- [Booking Data Model](../puml/booking-data-model.puml)
- [Booking Flow](../puml/booking-flow.puml)
- [Booking Lifecycle](../puml/booking-lifecycle.puml)

---

## Next Sprint

[Sprint 7: Booking System - API Routes](./sprint-7-booking-api.md)
