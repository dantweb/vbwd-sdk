# Backend Sprint: Booking System

**Duration:** 2 weeks
**Goal:** Implement room booking system with timeslot management
**Dependencies:** Core authentication, payment system

---

## Objectives

- [ ] Create database models (Room, Timeslot, Booking)
- [ ] Implement booking business logic
- [ ] Create user API endpoints
- [ ] Create admin API endpoints
- [ ] Implement cancellation & refund logic
- [ ] Add notification system integration
- [ ] Write comprehensive tests (95%+ coverage)

---

## Tasks

### 1. Database Models

**File:** `python/api/src/models/room.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from src.models.base import Base

class Room(Base):
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

    def to_dict(self):
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
```

**File:** `python/api/src/models/timeslot.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Decimal, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class Timeslot(Base):
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

    def to_dict(self):
        return {
            'id': self.id,
            'roomId': self.room_id,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'isAvailable': self.is_available,
            'price': float(self.price) if self.price else None,
            'maxBookings': self.max_bookings,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }
```

**File:** `python/api/src/models/booking.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Decimal, Text, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class Booking(Base):
    __tablename__ = 'bookings'
    __table_args__ = (
        Index('idx_user_bookings', 'user_id', 'status'),
        Index('idx_timeslot', 'timeslot_id'),
        Index('idx_status', 'status', 'created_at'),
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
        Enum('pending', 'paid', 'refunded', name='payment_status_enum'),
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

    def to_dict(self, include_relations=False):
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
```

### 2. Business Logic Service

**File:** `python/api/src/services/booking_service.py`

```python
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from src.models.booking import Booking
from src.models.timeslot import Timeslot
from src.models.room import Room

class BookingService:
    """Business logic for booking management"""

    @staticmethod
    def get_available_timeslots(
        db: Session,
        room_id: int,
        date: datetime,
        duration_minutes: int = 30
    ) -> List[Timeslot]:
        """Get available timeslots for a room on a specific date"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return db.query(Timeslot).filter(
            Timeslot.room_id == room_id,
            Timeslot.start_time >= start_of_day,
            Timeslot.start_time < end_of_day,
            Timeslot.is_available == True
        ).order_by(Timeslot.start_time).all()

    @staticmethod
    def create_booking(
        db: Session,
        user_id: int,
        timeslot_id: int,
        room_id: int,
        notes: Optional[str] = None
    ) -> Booking:
        """Create a new booking"""
        # Check timeslot availability
        timeslot = db.query(Timeslot).filter(Timeslot.id == timeslot_id).first()
        if not timeslot:
            raise ValueError("Timeslot not found")

        if not timeslot.is_available:
            raise ValueError("Timeslot is not available")

        # Check room exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Room not found")

        # Create booking
        booking = Booking(
            user_id=user_id,
            timeslot_id=timeslot_id,
            room_id=room_id,
            price=timeslot.price,
            status='pending',
            payment_status='pending',
            notes=notes
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def confirm_booking(db: Session, booking_id: int, payment_id: str) -> Booking:
        """Confirm booking after successful payment"""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise ValueError("Booking not found")

        if booking.status != 'pending':
            raise ValueError(f"Cannot confirm booking with status: {booking.status}")

        # Update booking
        booking.status = 'confirmed'
        booking.payment_status = 'paid'
        booking.payment_id = payment_id

        # Mark timeslot as unavailable
        timeslot = db.query(Timeslot).filter(Timeslot.id == booking.timeslot_id).first()
        if timeslot:
            timeslot.is_available = False

        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def cancel_booking(
        db: Session,
        booking_id: int,
        cancelled_by_user: bool = True
    ) -> Dict:
        """Cancel booking and calculate refund"""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise ValueError("Booking not found")

        if booking.status not in ['pending', 'confirmed']:
            raise ValueError(f"Cannot cancel booking with status: {booking.status}")

        # Calculate refund amount
        refund_amount = BookingService._calculate_refund(booking)

        # Update booking
        booking.status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()

        if refund_amount > 0:
            booking.payment_status = 'refunded'

        # Release timeslot
        timeslot = db.query(Timeslot).filter(Timeslot.id == booking.timeslot_id).first()
        if timeslot:
            timeslot.is_available = True

        db.commit()
        db.refresh(booking)

        return {
            'booking': booking,
            'refund_amount': float(refund_amount)
        }

    @staticmethod
    def _calculate_refund(booking: Booking) -> Decimal:
        """Calculate refund based on cancellation policy"""
        if booking.payment_status != 'paid':
            return 0

        # Get hours before appointment
        now = datetime.utcnow()
        hours_before = (booking.timeslot.start_time - now).total_seconds() / 3600

        # Refund policy
        if hours_before >= 24:
            return booking.price  # 100% refund
        elif hours_before >= 6:
            return booking.price * 0.5  # 50% refund
        else:
            return 0  # No refund

    @staticmethod
    def generate_timeslots(
        db: Session,
        room_id: int,
        start_date: datetime,
        end_date: datetime,
        slot_duration_minutes: int = 30,
        working_hours: Dict[str, str] = None
    ) -> List[Timeslot]:
        """Generate timeslots for a room"""
        if working_hours is None:
            working_hours = {'start': '09:00', 'end': '17:00'}

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Room not found")

        timeslots = []
        current_date = start_date

        while current_date < end_date:
            # Parse working hours
            start_hour, start_minute = map(int, working_hours['start'].split(':'))
            end_hour, end_minute = map(int, working_hours['end'].split(':'))

            slot_start = current_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            day_end = current_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

            while slot_start < day_end:
                slot_end = slot_start + timedelta(minutes=slot_duration_minutes)

                timeslot = Timeslot(
                    room_id=room_id,
                    start_time=slot_start,
                    end_time=slot_end,
                    is_available=True,
                    price=room.hourly_rate * (slot_duration_minutes / 60) if room.hourly_rate else 0,
                    max_bookings=1
                )

                timeslots.append(timeslot)
                slot_start = slot_end

            current_date += timedelta(days=1)

        db.add_all(timeslots)
        db.commit()

        return timeslots
```

### 3. API Routes

**File:** `python/api/src/routes/bookings.py`

```python
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from src.services.booking_service import BookingService
from src.services.auth_service import require_auth, get_current_user
from src.database import get_db

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/v1/bookings')

@bookings_bp.route('/rooms', methods=['GET'])
def list_rooms():
    """List available rooms"""
    db = get_db()
    rooms = db.query(Room).filter(Room.is_active == True).all()
    return jsonify([room.to_dict() for room in rooms]), 200

@bookings_bp.route('/rooms/<int:room_id>/timeslots', methods=['GET'])
def get_room_timeslots(room_id: int):
    """Get available timeslots for a room"""
    db = get_db()
    date_str = request.args.get('date')
    duration = int(request.args.get('duration', 30))

    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    timeslots = BookingService.get_available_timeslots(db, room_id, date, duration)
    return jsonify([ts.to_dict() for ts in timeslots]), 200

@bookings_bp.route('', methods=['POST'])
@require_auth
def create_booking():
    """Create new booking"""
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    try:
        booking = BookingService.create_booking(
            db,
            user_id=user.id,
            timeslot_id=data['timeslotId'],
            room_id=data['roomId'],
            notes=data.get('notes')
        )

        # TODO: Initiate payment flow

        return jsonify(booking.to_dict(include_relations=True)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bookings_bp.route('', methods=['GET'])
@require_auth
def list_user_bookings():
    """List user's bookings"""
    db = get_db()
    user = get_current_user()

    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))

    query = db.query(Booking).filter(Booking.user_id == user.id)

    if status:
        query = query.filter(Booking.status == status)

    bookings = query.order_by(Booking.created_at.desc()) \
                    .offset((page - 1) * limit) \
                    .limit(limit) \
                    .all()

    return jsonify([b.to_dict(include_relations=True) for b in bookings]), 200

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
@require_auth
def get_booking(booking_id: int):
    """Get booking details"""
    db = get_db()
    user = get_current_user()

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    return jsonify(booking.to_dict(include_relations=True)), 200

@bookings_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@require_auth
def cancel_booking(booking_id: int):
    """Cancel booking"""
    db = get_db()
    user = get_current_user()

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    try:
        result = BookingService.cancel_booking(db, booking_id)

        # TODO: Process refund if refund_amount > 0

        return jsonify({
            'booking': result['booking'].to_dict(include_relations=True),
            'refundAmount': result['refund_amount']
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

### 4. Admin Routes

**File:** `python/api/src/routes/admin/bookings.py`

```python
from flask import Blueprint, request, jsonify
from src.services.booking_service import BookingService
from src.services.auth_service import require_admin
from src.database import get_db

admin_bookings_bp = Blueprint('admin_bookings', __name__, url_prefix='/api/v1/admin')

@admin_bookings_bp.route('/rooms', methods=['POST'])
@require_admin
def create_room():
    """Create new room"""
    db = get_db()
    data = request.get_json()

    room = Room(
        name=data['name'],
        description=data.get('description'),
        capacity=data.get('capacity', 1),
        room_type=data['roomType'],
        hourly_rate=data.get('hourlyRate'),
        is_active=data.get('isActive', True),
        metadata=data.get('metadata')
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return jsonify(room.to_dict()), 201

@admin_bookings_bp.route('/timeslots/generate', methods=['POST'])
@require_admin
def generate_timeslots():
    """Generate timeslots for a room"""
    db = get_db()
    data = request.get_json()

    try:
        start_date = datetime.fromisoformat(data['startDate'])
        end_date = datetime.fromisoformat(data['endDate'])

        timeslots = BookingService.generate_timeslots(
            db,
            room_id=data['roomId'],
            start_date=start_date,
            end_date=end_date,
            slot_duration_minutes=data.get('slotDuration', 30),
            working_hours=data.get('workingHours')
        )

        return jsonify({
            'message': f'Generated {len(timeslots)} timeslots',
            'count': len(timeslots)
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@admin_bookings_bp.route('/bookings', methods=['GET'])
@require_admin
def list_all_bookings():
    """List all bookings (admin)"""
    db = get_db()

    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))

    query = db.query(Booking)

    if status:
        query = query.filter(Booking.status == status)

    bookings = query.order_by(Booking.created_at.desc()) \
                    .offset((page - 1) * limit) \
                    .limit(limit) \
                    .all()

    return jsonify([b.to_dict(include_relations=True) for b in bookings]), 200
```

---

## Testing

### Unit Tests

**File:** `python/api/tests/unit/test_booking_service.py`

```python
import pytest
from datetime import datetime, timedelta
from src.services.booking_service import BookingService
from src.models.booking import Booking
from src.models.room import Room
from src.models.timeslot import Timeslot

def test_create_booking(db_session, test_user, test_room, test_timeslot):
    booking = BookingService.create_booking(
        db_session,
        user_id=test_user.id,
        timeslot_id=test_timeslot.id,
        room_id=test_room.id,
        notes="Test booking"
    )

    assert booking.id is not None
    assert booking.status == 'pending'
    assert booking.payment_status == 'pending'

def test_calculate_refund_full(test_booking):
    # 48 hours before
    test_booking.timeslot.start_time = datetime.utcnow() + timedelta(hours=48)
    refund = BookingService._calculate_refund(test_booking)
    assert refund == test_booking.price

def test_calculate_refund_half(test_booking):
    # 12 hours before
    test_booking.timeslot.start_time = datetime.utcnow() + timedelta(hours=12)
    refund = BookingService._calculate_refund(test_booking)
    assert refund == test_booking.price * 0.5

def test_calculate_refund_none(test_booking):
    # 2 hours before
    test_booking.timeslot.start_time = datetime.utcnow() + timedelta(hours=2)
    refund = BookingService._calculate_refund(test_booking)
    assert refund == 0
```

---

## Definition of Done

- [x] Database models created and migrated
- [x] Business logic service implemented
- [x] User API endpoints implemented
- [x] Admin API endpoints implemented
- [x] Cancellation & refund logic working
- [x] Unit tests with 95%+ coverage
- [x] Integration tests
- [x] API documentation
- [x] Ready for frontend integration

---

## Next Sprint

[Backend Sprint: Ticket System](./sprint-ticket-system.md)
