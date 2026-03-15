# Sprint 7: Booking System - API Routes

**Goal:** Implement user and admin API endpoints for booking management
**Dependencies:** Sprint 6 (Booking Models & Services)

---

## Objectives

- [ ] Create user booking API endpoints
- [ ] Create admin booking management endpoints
- [ ] Implement room browsing endpoints
- [ ] Add payment integration hooks
- [ ] Implement WebSocket notifications for booking updates
- [ ] Write integration tests
- [ ] Create API documentation

---

## API Routes

### 1. User Booking Routes

**File:** `python/api/src/routes/bookings.py`

```python
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy.orm import Session
from src.services.booking_service import BookingService, BookingError
from src.services.auth_service import require_auth, get_current_user
from src.database import get_db
from src.models.room import Room
from src.models.booking import Booking

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/v1/bookings')


@bookings_bp.route('/rooms', methods=['GET'])
def list_rooms():
    """
    List available rooms with optional filtering.

    Query Parameters:
        - type: Filter by room type (office, consultation, meeting, treatment)
        - active: Filter by active status (default: true)
        - page: Page number (default: 1)
        - limit: Items per page (default: 25)

    Returns:
        200: List of rooms
    """
    db = get_db()

    room_type = request.args.get('type')
    active_only = request.args.get('active', 'true').lower() == 'true'
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 25)), 100)

    query = db.query(Room)

    if active_only:
        query = query.filter(Room.is_active == True)

    if room_type:
        query = query.filter(Room.room_type == room_type)

    total = query.count()
    rooms = query.order_by(Room.name) \
                 .offset((page - 1) * limit) \
                 .limit(limit) \
                 .all()

    return jsonify({
        'items': [room.to_dict() for room in rooms],
        'total': total,
        'page': page,
        'limit': limit,
        'pages': (total + limit - 1) // limit
    }), 200


@bookings_bp.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id: int):
    """
    Get room details.

    Returns:
        200: Room details
        404: Room not found
    """
    db = get_db()
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        return jsonify({'error': 'Room not found'}), 404

    return jsonify(room.to_dict()), 200


@bookings_bp.route('/rooms/<int:room_id>/timeslots', methods=['GET'])
def get_room_timeslots(room_id: int):
    """
    Get available timeslots for a room on a specific date.

    Query Parameters:
        - date: Target date (ISO format, required)
        - duration: Minimum slot duration in minutes (default: 30)

    Returns:
        200: List of available timeslots
        400: Invalid date format
        404: Room not found
    """
    db = get_db()

    # Validate room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    date_str = request.args.get('date')
    duration = int(request.args.get('duration', 30))

    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400

    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO 8601'}), 400

    timeslots = BookingService.get_available_timeslots(db, room_id, date, duration)

    return jsonify({
        'room': room.to_dict(),
        'date': date_str,
        'timeslots': [ts.to_dict() for ts in timeslots]
    }), 200


@bookings_bp.route('', methods=['POST'])
@require_auth
def create_booking():
    """
    Create a new booking.

    Request Body:
        - timeslotId: int (required)
        - roomId: int (required)
        - notes: string (optional)
        - bookingType: string (optional)

    Returns:
        201: Booking created with payment URL
        400: Validation error
        401: Unauthorized
    """
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    # Validate required fields
    if not data.get('timeslotId') or not data.get('roomId'):
        return jsonify({'error': 'timeslotId and roomId are required'}), 400

    try:
        booking = BookingService.create_booking(
            db,
            user_id=user.id,
            timeslot_id=data['timeslotId'],
            room_id=data['roomId'],
            notes=data.get('notes'),
            booking_type=data.get('bookingType')
        )

        # TODO: Create payment session and return checkout URL
        # checkout_url = payment_service.create_checkout(booking)

        return jsonify({
            'booking': booking.to_dict(include_relations=True),
            'checkoutUrl': None,  # Will be set by payment integration
            'message': 'Booking created. Complete payment to confirm.'
        }), 201

    except BookingError as e:
        return jsonify({'error': str(e)}), 400


@bookings_bp.route('', methods=['GET'])
@require_auth
def list_user_bookings():
    """
    List current user's bookings.

    Query Parameters:
        - status: Filter by status
        - from_date: Filter from date
        - to_date: Filter to date
        - page: Page number (default: 1)
        - limit: Items per page (default: 25)

    Returns:
        200: List of bookings
    """
    db = get_db()
    user = get_current_user()

    status = request.args.get('status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 25)), 100)

    query = db.query(Booking).filter(Booking.user_id == user.id)

    if status:
        query = query.filter(Booking.status == status)

    if from_date:
        query = query.join(Booking.timeslot).filter(
            Timeslot.start_time >= datetime.fromisoformat(from_date)
        )

    if to_date:
        query = query.join(Booking.timeslot).filter(
            Timeslot.start_time <= datetime.fromisoformat(to_date)
        )

    total = query.count()
    bookings = query.order_by(Booking.created_at.desc()) \
                    .offset((page - 1) * limit) \
                    .limit(limit) \
                    .all()

    return jsonify({
        'items': [b.to_dict(include_relations=True) for b in bookings],
        'total': total,
        'page': page,
        'limit': limit
    }), 200


@bookings_bp.route('/<int:booking_id>', methods=['GET'])
@require_auth
def get_booking(booking_id: int):
    """
    Get booking details.

    Returns:
        200: Booking details
        403: Not owner of booking
        404: Booking not found
    """
    db = get_db()
    user = get_current_user()

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if booking.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify(booking.to_dict(include_relations=True)), 200


@bookings_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@require_auth
def cancel_booking(booking_id: int):
    """
    Cancel a booking.

    Returns:
        200: Cancellation result with refund amount
        400: Cannot cancel
        403: Not owner of booking
        404: Booking not found
    """
    db = get_db()
    user = get_current_user()

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if booking.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    try:
        result = BookingService.cancel_booking(db, booking_id)

        # TODO: Process refund if refund_amount > 0
        # if result['refund_amount'] > 0:
        #     payment_service.process_refund(booking, result['refund_amount'])

        return jsonify({
            'booking': result['booking'].to_dict(include_relations=True),
            'refundAmount': result['refund_amount'],
            'message': 'Booking cancelled successfully'
        }), 200

    except BookingError as e:
        return jsonify({'error': str(e)}), 400


@bookings_bp.route('/<int:booking_id>/reschedule', methods=['PUT'])
@require_auth
def reschedule_booking(booking_id: int):
    """
    Reschedule booking to a new timeslot.

    Request Body:
        - newTimeslotId: int (required)

    Returns:
        200: Updated booking
        400: Cannot reschedule
        403: Not owner of booking
        404: Booking not found
    """
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    if booking.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    if not data.get('newTimeslotId'):
        return jsonify({'error': 'newTimeslotId is required'}), 400

    try:
        updated_booking = BookingService.reschedule_booking(
            db,
            booking_id=booking_id,
            new_timeslot_id=data['newTimeslotId']
        )

        return jsonify({
            'booking': updated_booking.to_dict(include_relations=True),
            'message': 'Booking rescheduled successfully'
        }), 200

    except BookingError as e:
        return jsonify({'error': str(e)}), 400
```

### 2. Admin Booking Routes

**File:** `python/api/src/routes/admin/bookings.py`

```python
from flask import Blueprint, request, jsonify
from datetime import datetime
from src.services.booking_service import BookingService, BookingError
from src.services.timeslot_generator_service import TimeslotGeneratorService
from src.services.auth_service import require_admin
from src.database import get_db
from src.models.room import Room
from src.models.booking import Booking

admin_bookings_bp = Blueprint('admin_bookings', __name__, url_prefix='/api/v1/admin')


# ==================
# ROOM MANAGEMENT
# ==================

@admin_bookings_bp.route('/rooms', methods=['POST'])
@require_admin
def create_room():
    """Create a new room"""
    db = get_db()
    data = request.get_json()

    required_fields = ['name', 'roomType']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

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


@admin_bookings_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@require_admin
def update_room(room_id: int):
    """Update room details"""
    db = get_db()
    data = request.get_json()

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Update allowed fields
    updateable_fields = ['name', 'description', 'capacity', 'roomType',
                         'hourlyRate', 'isActive', 'metadata']
    field_mapping = {
        'roomType': 'room_type',
        'hourlyRate': 'hourly_rate',
        'isActive': 'is_active'
    }

    for field in updateable_fields:
        if field in data:
            attr_name = field_mapping.get(field, field)
            setattr(room, attr_name, data[field])

    db.commit()
    db.refresh(room)

    return jsonify(room.to_dict()), 200


@admin_bookings_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@require_admin
def delete_room(room_id: int):
    """Delete a room (soft delete by deactivating)"""
    db = get_db()

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Soft delete - just deactivate
    room.is_active = False
    db.commit()

    return jsonify({'message': 'Room deactivated'}), 200


# ==================
# TIMESLOT MANAGEMENT
# ==================

@admin_bookings_bp.route('/timeslots/generate', methods=['POST'])
@require_admin
def generate_timeslots():
    """
    Generate timeslots for a room.

    Request Body:
        - roomId: int (required)
        - startDate: ISO date (required)
        - endDate: ISO date (required)
        - slotDuration: int minutes (default: 30)
        - workingHours: {start: "09:00", end: "17:00"}
        - excludedDates: list of ISO dates
    """
    db = get_db()
    data = request.get_json()

    required_fields = ['roomId', 'startDate', 'endDate']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    try:
        start_date = datetime.fromisoformat(data['startDate'])
        end_date = datetime.fromisoformat(data['endDate'])

        excluded_dates = None
        if data.get('excludedDates'):
            excluded_dates = [datetime.fromisoformat(d) for d in data['excludedDates']]

        timeslots = TimeslotGeneratorService.generate_timeslots(
            db,
            room_id=data['roomId'],
            start_date=start_date,
            end_date=end_date,
            slot_duration_minutes=data.get('slotDuration', 30),
            working_hours=data.get('workingHours'),
            excluded_dates=excluded_dates
        )

        return jsonify({
            'message': f'Generated {len(timeslots)} timeslots',
            'count': len(timeslots),
            'dateRange': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@admin_bookings_bp.route('/timeslots/<int:timeslot_id>', methods=['DELETE'])
@require_admin
def delete_timeslot(timeslot_id: int):
    """Delete a timeslot (only if not booked)"""
    db = get_db()

    timeslot = db.query(Timeslot).filter(Timeslot.id == timeslot_id).first()
    if not timeslot:
        return jsonify({'error': 'Timeslot not found'}), 404

    # Check if timeslot has bookings
    if timeslot.bookings:
        return jsonify({'error': 'Cannot delete timeslot with existing bookings'}), 400

    db.delete(timeslot)
    db.commit()

    return jsonify({'message': 'Timeslot deleted'}), 200


# ==================
# BOOKING MANAGEMENT
# ==================

@admin_bookings_bp.route('/bookings', methods=['GET'])
@require_admin
def list_all_bookings():
    """List all bookings with filters"""
    db = get_db()

    status = request.args.get('status')
    room_id = request.args.get('roomId')
    user_id = request.args.get('userId')
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 50)), 100)

    query = db.query(Booking)

    if status:
        query = query.filter(Booking.status == status)
    if room_id:
        query = query.filter(Booking.room_id == int(room_id))
    if user_id:
        query = query.filter(Booking.user_id == int(user_id))
    if from_date:
        query = query.filter(Booking.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        query = query.filter(Booking.created_at <= datetime.fromisoformat(to_date))

    total = query.count()
    bookings = query.order_by(Booking.created_at.desc()) \
                    .offset((page - 1) * limit) \
                    .limit(limit) \
                    .all()

    return jsonify({
        'items': [b.to_dict(include_relations=True) for b in bookings],
        'total': total,
        'page': page,
        'limit': limit
    }), 200


@admin_bookings_bp.route('/bookings/<int:booking_id>/status', methods=['PUT'])
@require_admin
def update_booking_status(booking_id: int):
    """
    Update booking status (admin override).

    Request Body:
        - status: new status (required)
    """
    db = get_db()
    data = request.get_json()

    if not data.get('status'):
        return jsonify({'error': 'status is required'}), 400

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    new_status = data['status']

    try:
        if new_status == 'completed':
            booking = BookingService.complete_booking(db, booking_id)
        elif new_status == 'no_show':
            booking = BookingService.mark_no_show(db, booking_id)
        elif new_status == 'cancelled':
            result = BookingService.cancel_booking(db, booking_id, cancelled_by_admin=True)
            booking = result['booking']
        else:
            return jsonify({'error': f'Invalid status transition to: {new_status}'}), 400

        return jsonify(booking.to_dict(include_relations=True)), 200

    except BookingError as e:
        return jsonify({'error': str(e)}), 400


@admin_bookings_bp.route('/bookings/stats', methods=['GET'])
@require_admin
def get_booking_stats():
    """Get booking statistics"""
    db = get_db()

    from_date = request.args.get('fromDate', datetime.utcnow().replace(day=1).isoformat())
    to_date = request.args.get('toDate', datetime.utcnow().isoformat())

    stats = {
        'total': db.query(Booking).filter(
            Booking.created_at >= from_date,
            Booking.created_at <= to_date
        ).count(),
        'byStatus': {},
        'revenue': 0
    }

    for status in ['pending', 'confirmed', 'cancelled', 'completed', 'no_show']:
        stats['byStatus'][status] = db.query(Booking).filter(
            Booking.status == status,
            Booking.created_at >= from_date,
            Booking.created_at <= to_date
        ).count()

    # Calculate revenue from paid bookings
    from sqlalchemy import func
    revenue = db.query(func.sum(Booking.price)).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= from_date,
        Booking.created_at <= to_date
    ).scalar()

    stats['revenue'] = float(revenue) if revenue else 0

    return jsonify(stats), 200
```

---

## WebSocket Events

**File:** `python/api/src/routes/websocket_booking.py`

```python
from flask_socketio import emit, join_room, leave_room
from src.extensions import socketio

@socketio.on('join_booking_room')
def on_join_booking_room(data):
    """Join room for booking updates"""
    user_id = data.get('userId')
    if user_id:
        join_room(f'user_{user_id}')

@socketio.on('leave_booking_room')
def on_leave_booking_room(data):
    """Leave booking update room"""
    user_id = data.get('userId')
    if user_id:
        leave_room(f'user_{user_id}')

def emit_booking_update(user_id: int, booking: dict, event_type: str):
    """Emit booking update to user"""
    socketio.emit('booking_update', {
        'type': event_type,
        'booking': booking
    }, room=f'user_{user_id}')

def emit_booking_reminder(user_id: int, booking: dict):
    """Emit booking reminder to user"""
    socketio.emit('booking_reminder', {
        'booking': booking,
        'message': 'Your appointment is coming up!'
    }, room=f'user_{user_id}')
```

---

## Integration Tests

**File:** `python/api/tests/integration/test_booking_api.py`

```python
import pytest
from datetime import datetime, timedelta

class TestBookingAPI:
    """Integration tests for booking API endpoints"""

    def test_list_rooms(self, client):
        """Test listing available rooms"""
        response = client.get('/api/v1/bookings/rooms')

        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert 'total' in data

    def test_get_room_timeslots(self, client, test_room):
        """Test getting available timeslots"""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')

        response = client.get(
            f'/api/v1/bookings/rooms/{test_room.id}/timeslots?date={tomorrow}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'timeslots' in data

    def test_create_booking_authenticated(self, auth_client, test_room, test_timeslot):
        """Test creating a booking as authenticated user"""
        response = auth_client.post('/api/v1/bookings', json={
            'timeslotId': test_timeslot.id,
            'roomId': test_room.id,
            'notes': 'Test booking'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['booking']['status'] == 'pending'

    def test_create_booking_unauthenticated(self, client, test_room, test_timeslot):
        """Test creating booking without auth fails"""
        response = client.post('/api/v1/bookings', json={
            'timeslotId': test_timeslot.id,
            'roomId': test_room.id
        })

        assert response.status_code == 401

    def test_cancel_booking(self, auth_client, user_booking):
        """Test cancelling own booking"""
        response = auth_client.put(f'/api/v1/bookings/{user_booking.id}/cancel')

        assert response.status_code == 200
        data = response.get_json()
        assert data['booking']['status'] == 'cancelled'

    def test_cannot_cancel_others_booking(self, auth_client, other_user_booking):
        """Test cannot cancel another user's booking"""
        response = auth_client.put(f'/api/v1/bookings/{other_user_booking.id}/cancel')

        assert response.status_code == 403

    def test_admin_list_all_bookings(self, admin_client):
        """Test admin can list all bookings"""
        response = admin_client.get('/api/v1/admin/bookings')

        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data

    def test_admin_generate_timeslots(self, admin_client, test_room):
        """Test admin can generate timeslots"""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')
        next_week = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%dT00:00:00')

        response = admin_client.post('/api/v1/admin/timeslots/generate', json={
            'roomId': test_room.id,
            'startDate': tomorrow,
            'endDate': next_week,
            'slotDuration': 30,
            'workingHours': {'start': '09:00', 'end': '17:00'}
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['count'] > 0
```

---

## API Documentation

### User Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/bookings/rooms` | List available rooms | No |
| GET | `/api/v1/bookings/rooms/:id` | Get room details | No |
| GET | `/api/v1/bookings/rooms/:id/timeslots` | Get available timeslots | No |
| POST | `/api/v1/bookings` | Create booking | Yes |
| GET | `/api/v1/bookings` | List user's bookings | Yes |
| GET | `/api/v1/bookings/:id` | Get booking details | Yes |
| PUT | `/api/v1/bookings/:id/cancel` | Cancel booking | Yes |
| PUT | `/api/v1/bookings/:id/reschedule` | Reschedule booking | Yes |

### Admin Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/admin/rooms` | Create room | Admin |
| PUT | `/api/v1/admin/rooms/:id` | Update room | Admin |
| DELETE | `/api/v1/admin/rooms/:id` | Delete room | Admin |
| POST | `/api/v1/admin/timeslots/generate` | Generate timeslots | Admin |
| DELETE | `/api/v1/admin/timeslots/:id` | Delete timeslot | Admin |
| GET | `/api/v1/admin/bookings` | List all bookings | Admin |
| PUT | `/api/v1/admin/bookings/:id/status` | Update status | Admin |
| GET | `/api/v1/admin/bookings/stats` | Get statistics | Admin |

---

## Definition of Done

- [ ] All user API endpoints implemented
- [ ] All admin API endpoints implemented
- [ ] WebSocket notifications working
- [ ] Integration tests passing
- [ ] API documentation complete
- [ ] Error handling comprehensive
- [ ] Rate limiting configured
- [ ] Code reviewed and approved

---

## Next Sprint

[Sprint 8: Ticket System - Database Models & Services](./sprint-8-ticket-models.md)
