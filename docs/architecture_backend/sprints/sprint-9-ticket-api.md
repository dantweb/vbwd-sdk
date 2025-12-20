# Sprint 9: Ticket System - API Routes

**Goal:** Implement user and admin API endpoints for event ticketing
**Dependencies:** Sprint 8 (Ticket Models & Services)

---

## Objectives

- [ ] Create event browsing API endpoints
- [ ] Create user ticket management endpoints
- [ ] Create admin event management endpoints
- [ ] Implement ticket scanner endpoints
- [ ] Add QR code generation to ticket responses
- [ ] Implement WebSocket notifications
- [ ] Write integration tests
- [ ] Create API documentation

---

## API Routes

### 1. Event Routes (Public)

**File:** `python/api/src/routes/events.py`

```python
from flask import Blueprint, request, jsonify
from datetime import datetime
from src.database import get_db
from src.models.event import Event, EventStatus
from src.models.event_tier import EventTier

events_bp = Blueprint('events', __name__, url_prefix='/api/v1/events')


@events_bp.route('', methods=['GET'])
def list_events():
    """
    List published events with filtering and pagination.

    Query Parameters:
        - type: Filter by event type
        - startDate: Filter events starting after this date
        - endDate: Filter events ending before this date
        - isOnline: Filter by online/offline
        - page: Page number (default: 1)
        - limit: Items per page (default: 25)

    Returns:
        200: Paginated list of events
    """
    db = get_db()

    event_type = request.args.get('type')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    is_online = request.args.get('isOnline')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 25)), 100)

    query = db.query(Event).filter(Event.status == EventStatus.PUBLISHED)

    if event_type:
        query = query.filter(Event.event_type == event_type)

    if start_date:
        query = query.filter(Event.start_date >= datetime.fromisoformat(start_date))

    if end_date:
        query = query.filter(Event.end_date <= datetime.fromisoformat(end_date))

    if is_online is not None:
        is_online_bool = is_online.lower() == 'true'
        query = query.filter(Event.is_online == is_online_bool)

    total = query.count()
    events = query.order_by(Event.start_date) \
                  .offset((page - 1) * limit) \
                  .limit(limit) \
                  .all()

    return jsonify({
        'items': [e.to_dict() for e in events],
        'total': total,
        'page': page,
        'limit': limit,
        'pages': (total + limit - 1) // limit
    }), 200


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id: int):
    """
    Get event details with pricing tiers.

    Returns:
        200: Event details with tiers
        404: Event not found
    """
    db = get_db()

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Only show published events to public
    if event.status != EventStatus.PUBLISHED:
        return jsonify({'error': 'Event not found'}), 404

    event_dict = event.to_dict()

    # Include active pricing tiers
    tiers = db.query(EventTier).filter(
        EventTier.event_id == event_id,
        EventTier.is_active == True
    ).order_by(EventTier.sort_order).all()

    event_dict['tiers'] = [t.to_dict() for t in tiers]

    return jsonify(event_dict), 200


@events_bp.route('/upcoming', methods=['GET'])
def list_upcoming_events():
    """
    List upcoming events (convenience endpoint).

    Returns:
        200: List of upcoming events
    """
    db = get_db()
    now = datetime.utcnow()

    events = db.query(Event).filter(
        Event.status == EventStatus.PUBLISHED,
        Event.start_date > now
    ).order_by(Event.start_date).limit(10).all()

    return jsonify([e.to_dict() for e in events]), 200
```

### 2. Ticket Routes (User)

**File:** `python/api/src/routes/tickets.py`

```python
from flask import Blueprint, request, jsonify
from src.services.ticket_service import TicketService, TicketError
from src.services.qr_code_service import QRCodeService
from src.services.auth_service import require_auth, get_current_user
from src.database import get_db
from src.models.ticket import Ticket

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/v1/tickets')


@tickets_bp.route('/purchase', methods=['POST'])
@require_auth
def purchase_tickets():
    """
    Purchase tickets for an event.

    Request Body:
        - eventId: int (required)
        - ticketType: string (default: 'standard')
        - tierId: int (optional, for tiered pricing)
        - quantity: int (default: 1)

    Returns:
        201: Tickets created with payment info
        400: Validation error
        401: Unauthorized
    """
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    if not data.get('eventId'):
        return jsonify({'error': 'eventId is required'}), 400

    try:
        tickets = TicketService.purchase_tickets(
            db,
            user_id=user.id,
            event_id=data['eventId'],
            ticket_type=data.get('ticketType', 'standard'),
            tier_id=data.get('tierId'),
            quantity=data.get('quantity', 1)
        )

        # Generate QR codes for tickets
        ticket_results = []
        for ticket in tickets:
            ticket_dict = ticket.to_dict(include_relations=True)
            ticket_dict['qrCodeUrl'] = QRCodeService.generate_ticket_qr(ticket.ticket_code)
            ticket_results.append(ticket_dict)

        total = sum(float(t.price_paid) for t in tickets)

        # TODO: Create payment session
        # checkout_url = payment_service.create_checkout(tickets, total)

        return jsonify({
            'tickets': ticket_results,
            'total': total,
            'checkoutUrl': None,
            'message': 'Tickets created. Complete payment to confirm.'
        }), 201

    except TicketError as e:
        return jsonify({'error': str(e)}), 400


@tickets_bp.route('', methods=['GET'])
@require_auth
def list_user_tickets():
    """
    List current user's tickets.

    Query Parameters:
        - status: Filter by status
        - eventId: Filter by event
        - page: Page number (default: 1)
        - limit: Items per page (default: 25)

    Returns:
        200: Paginated list of tickets with QR codes
    """
    db = get_db()
    user = get_current_user()

    status = request.args.get('status')
    event_id = request.args.get('eventId')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 25)), 100)

    query = db.query(Ticket).filter(Ticket.user_id == user.id)

    if status:
        query = query.filter(Ticket.status == status)

    if event_id:
        query = query.filter(Ticket.event_id == int(event_id))

    total = query.count()
    tickets = query.order_by(Ticket.created_at.desc()) \
                   .offset((page - 1) * limit) \
                   .limit(limit) \
                   .all()

    # Add QR codes
    result = []
    for ticket in tickets:
        ticket_dict = ticket.to_dict(include_relations=True)
        ticket_dict['qrCodeUrl'] = QRCodeService.generate_ticket_qr(ticket.ticket_code)
        result.append(ticket_dict)

    return jsonify({
        'items': result,
        'total': total,
        'page': page,
        'limit': limit
    }), 200


@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@require_auth
def get_ticket(ticket_id: int):
    """
    Get ticket details with QR code.

    Returns:
        200: Ticket details
        403: Not owner
        404: Not found
    """
    db = get_db()
    user = get_current_user()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    ticket_dict = ticket.to_dict(include_relations=True)
    ticket_dict['qrCodeUrl'] = QRCodeService.generate_ticket_qr(ticket.ticket_code)

    return jsonify(ticket_dict), 200


@tickets_bp.route('/<int:ticket_id>/qr', methods=['GET'])
@require_auth
def get_ticket_qr(ticket_id: int):
    """
    Get ticket QR code.

    Returns:
        200: QR code data URL
        403: Not owner
        404: Not found
    """
    db = get_db()
    user = get_current_user()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    qr_code = QRCodeService.generate_ticket_qr(ticket.ticket_code)

    return jsonify({
        'ticketCode': ticket.ticket_code,
        'qrCodeUrl': qr_code
    }), 200


@tickets_bp.route('/<ticket_code>/validate', methods=['POST'])
def validate_ticket(ticket_code: str):
    """
    Validate ticket (public endpoint for scanners).

    Returns:
        200: Validation result
    """
    db = get_db()

    result = TicketService.validate_ticket(db, ticket_code)

    return jsonify(result), 200


@tickets_bp.route('/<int:ticket_id>/cancel', methods=['PUT'])
@require_auth
def cancel_ticket(ticket_id: int):
    """
    Cancel a ticket.

    Returns:
        200: Cancellation result with refund
        400: Cannot cancel
        403: Not owner
        404: Not found
    """
    db = get_db()
    user = get_current_user()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    try:
        result = TicketService.cancel_ticket(db, ticket_id)

        # TODO: Process refund
        # if result['refund_amount'] > 0:
        #     payment_service.process_refund(ticket, result['refund_amount'])

        return jsonify({
            'ticket': result['ticket'],
            'refundAmount': result['refund_amount'],
            'message': 'Ticket cancelled successfully'
        }), 200

    except TicketError as e:
        return jsonify({'error': str(e)}), 400


@tickets_bp.route('/<int:ticket_id>/transfer', methods=['POST'])
@require_auth
def transfer_ticket(ticket_id: int):
    """
    Transfer ticket to another user.

    Request Body:
        - toEmail: string (required) - Email of recipient

    Returns:
        200: Transfer successful
        400: Cannot transfer
        403: Not owner
        404: Not found
    """
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    if not data.get('toEmail'):
        return jsonify({'error': 'toEmail is required'}), 400

    # Find recipient user
    from src.models.user import User
    recipient = db.query(User).filter(User.email == data['toEmail']).first()

    if not recipient:
        return jsonify({'error': 'Recipient user not found'}), 400

    if recipient.id == user.id:
        return jsonify({'error': 'Cannot transfer to yourself'}), 400

    try:
        updated_ticket = TicketService.transfer_ticket(
            db,
            ticket_id=ticket_id,
            from_user_id=user.id,
            to_user_id=recipient.id,
            notes=data.get('notes')
        )

        # TODO: Send transfer notification emails

        return jsonify({
            'ticket': updated_ticket.to_dict(include_relations=True),
            'message': f'Ticket transferred to {data["toEmail"]}'
        }), 200

    except TicketError as e:
        return jsonify({'error': str(e)}), 400
```

### 3. Admin Event Routes

**File:** `python/api/src/routes/admin/events.py`

```python
from flask import Blueprint, request, jsonify
from datetime import datetime
from src.services.auth_service import require_admin
from src.database import get_db
from src.models.event import Event, EventStatus
from src.models.event_tier import EventTier

admin_events_bp = Blueprint('admin_events', __name__, url_prefix='/api/v1/admin/events')


@admin_events_bp.route('', methods=['POST'])
@require_admin
def create_event():
    """Create a new event"""
    db = get_db()
    data = request.get_json()

    required_fields = ['name', 'eventType', 'startDate', 'endDate', 'ticketPrice']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    event = Event(
        name=data['name'],
        description=data.get('description'),
        event_type=data['eventType'],
        start_date=datetime.fromisoformat(data['startDate']),
        end_date=datetime.fromisoformat(data['endDate']),
        location=data.get('location'),
        is_online=data.get('isOnline', False),
        max_participants=data.get('maxParticipants'),
        ticket_price=data['ticketPrice'],
        status=data.get('status', EventStatus.DRAFT),
        image_url=data.get('imageUrl'),
        metadata=data.get('metadata')
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return jsonify(event.to_dict()), 201


@admin_events_bp.route('', methods=['GET'])
@require_admin
def list_all_events():
    """List all events including drafts"""
    db = get_db()

    status = request.args.get('status')
    event_type = request.args.get('type')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 50)), 100)

    query = db.query(Event)

    if status:
        query = query.filter(Event.status == status)
    if event_type:
        query = query.filter(Event.event_type == event_type)

    total = query.count()
    events = query.order_by(Event.created_at.desc()) \
                  .offset((page - 1) * limit) \
                  .limit(limit) \
                  .all()

    return jsonify({
        'items': [e.to_dict() for e in events],
        'total': total,
        'page': page,
        'limit': limit
    }), 200


@admin_events_bp.route('/<int:event_id>', methods=['PUT'])
@require_admin
def update_event(event_id: int):
    """Update event details"""
    db = get_db()
    data = request.get_json()

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Update allowed fields
    updateable_fields = [
        'name', 'description', 'eventType', 'startDate', 'endDate',
        'location', 'isOnline', 'maxParticipants', 'ticketPrice',
        'status', 'imageUrl', 'metadata'
    ]
    field_mapping = {
        'eventType': 'event_type',
        'startDate': 'start_date',
        'endDate': 'end_date',
        'isOnline': 'is_online',
        'maxParticipants': 'max_participants',
        'ticketPrice': 'ticket_price',
        'imageUrl': 'image_url'
    }

    for field in updateable_fields:
        if field in data:
            attr_name = field_mapping.get(field, field)
            value = data[field]

            # Parse dates
            if field in ['startDate', 'endDate'] and value:
                value = datetime.fromisoformat(value)

            setattr(event, attr_name, value)

    db.commit()
    db.refresh(event)

    return jsonify(event.to_dict()), 200


@admin_events_bp.route('/<int:event_id>', methods=['DELETE'])
@require_admin
def delete_event(event_id: int):
    """Delete or cancel an event"""
    db = get_db()

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # If event has tickets, mark as cancelled instead of deleting
    if event.current_participants > 0:
        event.status = EventStatus.CANCELLED
        db.commit()
        return jsonify({'message': 'Event cancelled (has active tickets)'}), 200

    db.delete(event)
    db.commit()

    return jsonify({'message': 'Event deleted'}), 200


@admin_events_bp.route('/<int:event_id>/publish', methods=['PUT'])
@require_admin
def publish_event(event_id: int):
    """Publish an event"""
    db = get_db()

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    if event.status not in [EventStatus.DRAFT]:
        return jsonify({'error': f'Cannot publish event with status: {event.status}'}), 400

    event.status = EventStatus.PUBLISHED
    db.commit()
    db.refresh(event)

    return jsonify(event.to_dict()), 200


# ==================
# EVENT TIERS
# ==================

@admin_events_bp.route('/<int:event_id>/tiers', methods=['POST'])
@require_admin
def create_event_tier(event_id: int):
    """Create a pricing tier for an event"""
    db = get_db()
    data = request.get_json()

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    tier = EventTier(
        event_id=event_id,
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        max_quantity=data.get('maxQuantity'),
        benefits=data.get('benefits'),
        is_active=data.get('isActive', True),
        sort_order=data.get('sortOrder', 0)
    )

    db.add(tier)
    db.commit()
    db.refresh(tier)

    return jsonify(tier.to_dict()), 201


@admin_events_bp.route('/<int:event_id>/tiers', methods=['GET'])
@require_admin
def list_event_tiers(event_id: int):
    """List all tiers for an event"""
    db = get_db()

    tiers = db.query(EventTier).filter(
        EventTier.event_id == event_id
    ).order_by(EventTier.sort_order).all()

    return jsonify([t.to_dict() for t in tiers]), 200


@admin_events_bp.route('/<int:event_id>/tiers/<int:tier_id>', methods=['PUT'])
@require_admin
def update_event_tier(event_id: int, tier_id: int):
    """Update an event tier"""
    db = get_db()
    data = request.get_json()

    tier = db.query(EventTier).filter(
        EventTier.id == tier_id,
        EventTier.event_id == event_id
    ).first()

    if not tier:
        return jsonify({'error': 'Tier not found'}), 404

    for field in ['name', 'description', 'price', 'maxQuantity', 'benefits', 'isActive', 'sortOrder']:
        if field in data:
            attr_name = {
                'maxQuantity': 'max_quantity',
                'isActive': 'is_active',
                'sortOrder': 'sort_order'
            }.get(field, field)
            setattr(tier, attr_name, data[field])

    db.commit()
    db.refresh(tier)

    return jsonify(tier.to_dict()), 200


# ==================
# TICKETS MANAGEMENT
# ==================

@admin_events_bp.route('/<int:event_id>/tickets', methods=['GET'])
@require_admin
def list_event_tickets(event_id: int):
    """List all tickets for an event"""
    db = get_db()

    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 50)), 100)

    query = db.query(Ticket).filter(Ticket.event_id == event_id)

    if status:
        query = query.filter(Ticket.status == status)

    total = query.count()
    tickets = query.order_by(Ticket.created_at.desc()) \
                   .offset((page - 1) * limit) \
                   .limit(limit) \
                   .all()

    return jsonify({
        'items': [t.to_dict(include_relations=True) for t in tickets],
        'total': total,
        'page': page,
        'limit': limit
    }), 200


@admin_events_bp.route('/<int:event_id>/stats', methods=['GET'])
@require_admin
def get_event_stats(event_id: int):
    """Get event statistics"""
    db = get_db()

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    from sqlalchemy import func
    from src.models.ticket import Ticket, TicketStatus

    stats = {
        'event': event.to_dict(),
        'tickets': {
            'total': db.query(Ticket).filter(Ticket.event_id == event_id).count(),
            'byStatus': {}
        },
        'revenue': 0,
        'checkIns': 0
    }

    for status in ['active', 'used', 'expired', 'cancelled', 'refunded']:
        stats['tickets']['byStatus'][status] = db.query(Ticket).filter(
            Ticket.event_id == event_id,
            Ticket.status == status
        ).count()

    # Revenue from paid tickets
    revenue = db.query(func.sum(Ticket.price_paid)).filter(
        Ticket.event_id == event_id,
        Ticket.status.in_(['active', 'used'])
    ).scalar()
    stats['revenue'] = float(revenue) if revenue else 0

    # Check-in count
    stats['checkIns'] = db.query(Ticket).filter(
        Ticket.event_id == event_id,
        Ticket.check_in_time.isnot(None)
    ).count()

    return jsonify(stats), 200
```

### 4. Ticket Scanner Routes

**File:** `python/api/src/routes/admin/scanner.py`

```python
from flask import Blueprint, request, jsonify
from src.services.ticket_service import TicketService
from src.services.auth_service import require_admin, get_current_user
from src.database import get_db
from src.models.ticket import Ticket
from src.models.ticket_scan import TicketScan

scanner_bp = Blueprint('scanner', __name__, url_prefix='/api/v1/admin/scanner')


@scanner_bp.route('/scan', methods=['POST'])
@require_admin
def scan_ticket():
    """
    Scan a ticket for check-in or access.

    Request Body:
        - ticketCode: string (required)
        - scanType: string (check_in, check_out, access) default: check_in
        - location: string (optional)
        - deviceInfo: string (optional)
        - markAsUsed: boolean (default: false)

    Returns:
        200: Scan successful
        400: Invalid ticket
    """
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    if not data.get('ticketCode'):
        return jsonify({'error': 'ticketCode is required'}), 400

    result = TicketService.scan_ticket(
        db,
        ticket_code=data['ticketCode'],
        scan_type=data.get('scanType', 'check_in'),
        scan_location=data.get('location'),
        scanner_user_id=user.id,
        device_info=data.get('deviceInfo'),
        mark_as_used=data.get('markAsUsed', False)
    )

    status_code = 200 if result['valid'] else 400
    return jsonify(result), status_code


@scanner_bp.route('/validate', methods=['POST'])
@require_admin
def validate_ticket():
    """
    Validate ticket without recording a scan.

    Request Body:
        - ticketCode: string (required)

    Returns:
        200: Validation result
    """
    db = get_db()
    data = request.get_json()

    if not data.get('ticketCode'):
        return jsonify({'error': 'ticketCode is required'}), 400

    result = TicketService.validate_ticket(db, data['ticketCode'])

    return jsonify(result), 200


@scanner_bp.route('/history/<ticket_code>', methods=['GET'])
@require_admin
def get_scan_history(ticket_code: str):
    """
    Get scan history for a ticket.

    Returns:
        200: List of scans
        404: Ticket not found
    """
    db = get_db()

    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    scans = db.query(TicketScan).filter(
        TicketScan.ticket_id == ticket.id
    ).order_by(TicketScan.scanned_at.desc()).all()

    return jsonify({
        'ticket': ticket.to_dict(include_relations=True),
        'scans': [s.to_dict() for s in scans]
    }), 200


@scanner_bp.route('/bulk-scan', methods=['POST'])
@require_admin
def bulk_scan():
    """
    Scan multiple tickets at once.

    Request Body:
        - ticketCodes: list of strings (required)
        - scanType: string (default: check_in)
        - location: string (optional)

    Returns:
        200: Results for each ticket
    """
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    if not data.get('ticketCodes'):
        return jsonify({'error': 'ticketCodes is required'}), 400

    results = []
    for ticket_code in data['ticketCodes']:
        result = TicketService.scan_ticket(
            db,
            ticket_code=ticket_code,
            scan_type=data.get('scanType', 'check_in'),
            scan_location=data.get('location'),
            scanner_user_id=user.id
        )
        result['ticketCode'] = ticket_code
        results.append(result)

    successful = sum(1 for r in results if r['valid'])

    return jsonify({
        'results': results,
        'summary': {
            'total': len(results),
            'successful': successful,
            'failed': len(results) - successful
        }
    }), 200
```

---

## WebSocket Events

**File:** `python/api/src/routes/websocket_tickets.py`

```python
from flask_socketio import emit, join_room, leave_room
from src.extensions import socketio

@socketio.on('join_event_room')
def on_join_event_room(data):
    """Join room for event updates (admin use)"""
    event_id = data.get('eventId')
    if event_id:
        join_room(f'event_{event_id}')

@socketio.on('join_user_tickets')
def on_join_user_tickets(data):
    """Join room for user ticket updates"""
    user_id = data.get('userId')
    if user_id:
        join_room(f'user_tickets_{user_id}')

def emit_ticket_purchased(event_id: int, ticket_count: int, current_count: int):
    """Emit ticket purchase update to event room"""
    socketio.emit('tickets_purchased', {
        'eventId': event_id,
        'ticketCount': ticket_count,
        'currentParticipants': current_count
    }, room=f'event_{event_id}')

def emit_ticket_scanned(event_id: int, ticket: dict):
    """Emit ticket scan to event room"""
    socketio.emit('ticket_scanned', {
        'eventId': event_id,
        'ticket': ticket
    }, room=f'event_{event_id}')

def emit_ticket_update(user_id: int, ticket: dict, event_type: str):
    """Emit ticket update to user"""
    socketio.emit('ticket_update', {
        'type': event_type,
        'ticket': ticket
    }, room=f'user_tickets_{user_id}')
```

---

## Integration Tests

**File:** `python/api/tests/integration/test_ticket_api.py`

```python
import pytest
from datetime import datetime, timedelta

class TestTicketAPI:
    """Integration tests for ticket API endpoints"""

    def test_list_events(self, client, published_event):
        """Test listing published events"""
        response = client.get('/api/v1/events')

        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert len(data['items']) >= 1

    def test_get_event_details(self, client, published_event):
        """Test getting event details"""
        response = client.get(f'/api/v1/events/{published_event.id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == published_event.name

    def test_purchase_tickets(self, auth_client, published_event):
        """Test purchasing tickets"""
        response = auth_client.post('/api/v1/tickets/purchase', json={
            'eventId': published_event.id,
            'quantity': 2
        })

        assert response.status_code == 201
        data = response.get_json()
        assert len(data['tickets']) == 2
        assert all('qrCodeUrl' in t for t in data['tickets'])

    def test_list_user_tickets(self, auth_client, user_ticket):
        """Test listing user's tickets"""
        response = auth_client.get('/api/v1/tickets')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) >= 1

    def test_validate_ticket(self, client, active_ticket):
        """Test ticket validation"""
        response = client.post(f'/api/v1/tickets/{active_ticket.ticket_code}/validate')

        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] == True

    def test_transfer_ticket(self, auth_client, user_ticket, other_user):
        """Test ticket transfer"""
        response = auth_client.post(f'/api/v1/tickets/{user_ticket.id}/transfer', json={
            'toEmail': other_user.email
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['ticket']['userId'] == other_user.id

    def test_admin_scan_ticket(self, admin_client, active_ticket):
        """Test admin ticket scanning"""
        response = admin_client.post('/api/v1/admin/scanner/scan', json={
            'ticketCode': active_ticket.ticket_code,
            'scanType': 'check_in',
            'location': 'Main Gate'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] == True

    def test_admin_create_event(self, admin_client):
        """Test admin event creation"""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        next_week = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = admin_client.post('/api/v1/admin/events', json={
            'name': 'Test Conference',
            'eventType': 'conference',
            'startDate': tomorrow,
            'endDate': next_week,
            'ticketPrice': 99.99,
            'maxParticipants': 100
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Test Conference'
        assert data['status'] == 'draft'
```

---

## API Documentation

### Event Endpoints (Public)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/events` | List published events | No |
| GET | `/api/v1/events/:id` | Get event details | No |
| GET | `/api/v1/events/upcoming` | List upcoming events | No |

### Ticket Endpoints (User)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/tickets/purchase` | Purchase tickets | Yes |
| GET | `/api/v1/tickets` | List user's tickets | Yes |
| GET | `/api/v1/tickets/:id` | Get ticket details | Yes |
| GET | `/api/v1/tickets/:id/qr` | Get ticket QR code | Yes |
| POST | `/api/v1/tickets/:code/validate` | Validate ticket | No |
| PUT | `/api/v1/tickets/:id/cancel` | Cancel ticket | Yes |
| POST | `/api/v1/tickets/:id/transfer` | Transfer ticket | Yes |

### Admin Event Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/admin/events` | Create event | Admin |
| GET | `/api/v1/admin/events` | List all events | Admin |
| PUT | `/api/v1/admin/events/:id` | Update event | Admin |
| DELETE | `/api/v1/admin/events/:id` | Delete/cancel event | Admin |
| PUT | `/api/v1/admin/events/:id/publish` | Publish event | Admin |
| POST | `/api/v1/admin/events/:id/tiers` | Create pricing tier | Admin |
| GET | `/api/v1/admin/events/:id/tiers` | List pricing tiers | Admin |
| PUT | `/api/v1/admin/events/:id/tiers/:tid` | Update tier | Admin |
| GET | `/api/v1/admin/events/:id/tickets` | List event tickets | Admin |
| GET | `/api/v1/admin/events/:id/stats` | Get event stats | Admin |

### Scanner Endpoints (Admin)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/admin/scanner/scan` | Scan ticket | Admin |
| POST | `/api/v1/admin/scanner/validate` | Validate without scan | Admin |
| GET | `/api/v1/admin/scanner/history/:code` | Get scan history | Admin |
| POST | `/api/v1/admin/scanner/bulk-scan` | Bulk scan tickets | Admin |

---

## Definition of Done

- [ ] All event endpoints implemented
- [ ] All ticket endpoints implemented
- [ ] All admin endpoints implemented
- [ ] Scanner functionality working
- [ ] QR codes generated for tickets
- [ ] WebSocket events emitted
- [ ] Integration tests passing
- [ ] API documentation complete
- [ ] Rate limiting configured
- [ ] Code reviewed and approved

---

## Next Steps

After completing backend implementation:

1. **Frontend Booking Plugin** - User booking interface
2. **Frontend Ticket Plugin** - User ticket interface
3. **Admin Management Plugins** - Booking & event management
4. **Mobile Scanner App** - QR code scanner for events
5. **Email Templates** - Booking/ticket confirmations
6. **Calendar Integration** - .ics file generation
7. **PDF Ticket Generation** - Printable tickets with QR codes
