# Backend Sprint: Ticket System

**Duration:** 2 weeks
**Goal:** Implement event ticketing system with QR code validation
**Dependencies:** Core authentication, payment system

---

## Objectives

- [ ] Create database models (Event, Ticket, TicketScan)
- [ ] Implement ticket business logic
- [ ] Implement QR code generation
- [ ] Create user API endpoints
- [ ] Create admin API endpoints
- [ ] Implement ticket validation system
- [ ] Add notification system integration
- [ ] Write comprehensive tests (95%+ coverage)

---

## Tasks

### 1. Database Models

**File:** `python/api/src/models/event.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class Event(Base):
    __tablename__ = 'events'
    __table_args__ = (
        Index('idx_dates', 'start_date', 'end_date', 'status'),
        Index('idx_status', 'status', 'start_date'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(
        Enum('conference', 'workshop', 'webinar', 'series', 'other', name='event_type_enum'),
        nullable=False
    )
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255))
    is_online = Column(Boolean, default=False)
    max_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    ticket_price = Column(Decimal(10, 2))
    status = Column(
        Enum('draft', 'published', 'cancelled', 'completed', name='event_status_enum'),
        default='draft'
    )
    image_url = Column(String(500))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tickets = relationship('Ticket', back_populates='event', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'eventType': self.event_type,
            'startDate': self.start_date.isoformat() if self.start_date else None,
            'endDate': self.end_date.isoformat() if self.end_date else None,
            'location': self.location,
            'isOnline': self.is_online,
            'maxParticipants': self.max_participants,
            'currentParticipants': self.current_participants,
            'ticketPrice': float(self.ticket_price) if self.ticket_price else None,
            'status': self.status,
            'imageUrl': self.image_url,
            'metadata': self.metadata,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_sold_out(self) -> bool:
        """Check if event is sold out"""
        if not self.max_participants:
            return False
        return self.current_participants >= self.max_participants

    @property
    def available_tickets(self) -> int:
        """Get number of available tickets"""
        if not self.max_participants:
            return 999999  # Unlimited
        return max(0, self.max_participants - self.current_participants)
```

**File:** `python/api/src/models/ticket.py`

```python
import secrets
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Decimal, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class Ticket(Base):
    __tablename__ = 'tickets'
    __table_args__ = (
        Index('idx_user_tickets', 'user_id', 'status'),
        Index('idx_event_tickets', 'event_id', 'status'),
        Index('idx_ticket_code', 'ticket_code'),
        Index('idx_validity', 'valid_from', 'valid_until', 'status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_code = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id', ondelete='RESTRICT'), nullable=False)
    ticket_type = Column(
        Enum('standard', 'vip', 'early_bird', 'group', name='ticket_type_enum'),
        default='standard'
    )
    status = Column(
        Enum('active', 'used', 'expired', 'cancelled', 'refunded', name='ticket_status_enum'),
        default='active'
    )
    price_paid = Column(Decimal(10, 2), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    payment_id = Column(String(255))
    check_in_time = Column(DateTime, nullable=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='tickets')
    event = relationship('Event', back_populates='tickets')
    scans = relationship('TicketScan', back_populates='ticket', cascade='all, delete-orphan')

    def to_dict(self, include_relations=False):
        result = {
            'id': self.id,
            'ticketCode': self.ticket_code,
            'userId': self.user_id,
            'eventId': self.event_id,
            'ticketType': self.ticket_type,
            'status': self.status,
            'pricePaid': float(self.price_paid),
            'validFrom': self.valid_from.isoformat() if self.valid_from else None,
            'validUntil': self.valid_until.isoformat() if self.valid_until else None,
            'paymentId': self.payment_id,
            'checkInTime': self.check_in_time.isoformat() if self.check_in_time else None,
            'metadata': self.metadata,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_relations and self.event:
            result['event'] = self.event.to_dict()

        return result

    @staticmethod
    def generate_ticket_code() -> str:
        """Generate unique ticket code"""
        return f"TKT-{secrets.token_hex(8).upper()}"

    def is_valid(self) -> bool:
        """Check if ticket is valid for use"""
        if self.status != 'active':
            return False

        now = datetime.utcnow()
        if now < self.valid_from or now > self.valid_until:
            return False

        return True
```

**File:** `python/api/src/models/ticket_scan.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class TicketScan(Base):
    __tablename__ = 'ticket_scans'
    __table_args__ = (
        Index('idx_ticket_scans', 'ticket_id', 'scanned_at'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    scan_location = Column(String(100))
    scan_type = Column(
        Enum('check_in', 'check_out', 'access', name='scan_type_enum'),
        default='access'
    )
    scanner_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    metadata = Column(JSON)

    # Relationships
    ticket = relationship('Ticket', back_populates='scans')
    scanner = relationship('User', foreign_keys=[scanner_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'ticketId': self.ticket_id,
            'scannedAt': self.scanned_at.isoformat() if self.scanned_at else None,
            'scanLocation': self.scan_location,
            'scanType': self.scan_type,
            'scannerUserId': self.scanner_user_id,
            'metadata': self.metadata,
        }
```

### 2. Business Logic Service

**File:** `python/api/src/services/ticket_service.py`

```python
import qrcode
import io
import base64
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models.ticket import Ticket
from src.models.event import Event
from src.models.ticket_scan import TicketScan

class TicketService:
    """Business logic for ticket management"""

    @staticmethod
    def purchase_tickets(
        db: Session,
        user_id: int,
        event_id: int,
        ticket_type: str,
        quantity: int
    ) -> List[Ticket]:
        """Purchase tickets for an event"""
        # Check event exists and is published
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError("Event not found")

        if event.status != 'published':
            raise ValueError("Event is not available for purchase")

        # Check availability
        if event.available_tickets < quantity:
            raise ValueError(f"Only {event.available_tickets} tickets available")

        # Check if event has started
        if datetime.utcnow() > event.end_date:
            raise ValueError("Event has already ended")

        # Create tickets
        tickets = []
        for _ in range(quantity):
            ticket = Ticket(
                ticket_code=Ticket.generate_ticket_code(),
                user_id=user_id,
                event_id=event_id,
                ticket_type=ticket_type,
                status='active',
                price_paid=event.ticket_price,
                valid_from=event.start_date,
                valid_until=event.end_date,
            )
            tickets.append(ticket)

        db.add_all(tickets)

        # Update event participant count
        event.current_participants += quantity

        db.commit()

        for ticket in tickets:
            db.refresh(ticket)

        return tickets

    @staticmethod
    def validate_ticket(db: Session, ticket_code: str) -> Dict:
        """Validate ticket for access"""
        ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()

        if not ticket:
            return {
                'valid': False,
                'reason': 'Ticket not found',
                'ticket': None
            }

        if ticket.status != 'active':
            return {
                'valid': False,
                'reason': f'Ticket status is {ticket.status}',
                'ticket': ticket.to_dict(include_relations=True)
            }

        now = datetime.utcnow()

        if now < ticket.valid_from:
            return {
                'valid': False,
                'reason': 'Ticket not yet valid',
                'ticket': ticket.to_dict(include_relations=True)
            }

        if now > ticket.valid_until:
            # Auto-expire ticket
            ticket.status = 'expired'
            db.commit()

            return {
                'valid': False,
                'reason': 'Ticket has expired',
                'ticket': ticket.to_dict(include_relations=True)
            }

        return {
            'valid': True,
            'reason': None,
            'ticket': ticket.to_dict(include_relations=True)
        }

    @staticmethod
    def scan_ticket(
        db: Session,
        ticket_code: str,
        scan_type: str = 'access',
        scan_location: Optional[str] = None,
        scanner_user_id: Optional[int] = None
    ) -> Dict:
        """Scan ticket and record access"""
        # Validate ticket first
        validation = TicketService.validate_ticket(db, ticket_code)

        if not validation['valid']:
            return validation

        ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()

        # Record scan
        scan = TicketScan(
            ticket_id=ticket.id,
            scan_type=scan_type,
            scan_location=scan_location,
            scanner_user_id=scanner_user_id,
        )
        db.add(scan)

        # Update check-in time for first scan
        if scan_type == 'check_in' and not ticket.check_in_time:
            ticket.check_in_time = datetime.utcnow()

        # Mark ticket as used if it's a single-use event
        # (This can be customized based on event settings)

        db.commit()
        db.refresh(scan)

        return {
            'valid': True,
            'scan': scan.to_dict(),
            'ticket': ticket.to_dict(include_relations=True)
        }

    @staticmethod
    def generate_qr_code(ticket_code: str) -> str:
        """Generate QR code for ticket"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(ticket_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def cancel_ticket(db: Session, ticket_id: int) -> Dict:
        """Cancel ticket and calculate refund"""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise ValueError("Ticket not found")

        if ticket.status not in ['active']:
            raise ValueError(f"Cannot cancel ticket with status: {ticket.status}")

        # Calculate refund based on time until event
        refund_amount = TicketService._calculate_refund(ticket)

        # Update ticket status
        ticket.status = 'cancelled' if refund_amount == 0 else 'refunded'

        # Decrease event participant count
        event = db.query(Event).filter(Event.id == ticket.event_id).first()
        if event:
            event.current_participants = max(0, event.current_participants - 1)

        db.commit()
        db.refresh(ticket)

        return {
            'ticket': ticket.to_dict(include_relations=True),
            'refund_amount': float(refund_amount)
        }

    @staticmethod
    def _calculate_refund(ticket: Ticket) -> float:
        """Calculate refund based on cancellation policy"""
        now = datetime.utcnow()
        days_before = (ticket.valid_from - now).days

        # Refund policy for tickets
        if days_before >= 7:
            return float(ticket.price_paid)  # 100% refund
        elif days_before >= 3:
            return float(ticket.price_paid) * 0.5  # 50% refund
        else:
            return 0  # No refund
```

### 3. API Routes

**File:** `python/api/src/routes/tickets.py`

```python
from flask import Blueprint, request, jsonify
from src.services.ticket_service import TicketService
from src.services.auth_service import require_auth, get_current_user
from src.database import get_db
from src.models.event import Event
from src.models.ticket import Ticket

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/v1')

@tickets_bp.route('/events', methods=['GET'])
def list_events():
    """List published events"""
    db = get_db()

    event_type = request.args.get('type')
    start_date = request.args.get('startDate')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))

    query = db.query(Event).filter(Event.status == 'published')

    if event_type:
        query = query.filter(Event.event_type == event_type)

    if start_date:
        query = query.filter(Event.start_date >= datetime.fromisoformat(start_date))

    events = query.order_by(Event.start_date) \
                  .offset((page - 1) * limit) \
                  .limit(limit) \
                  .all()

    return jsonify([e.to_dict() for e in events]), 200

@tickets_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id: int):
    """Get event details"""
    db = get_db()
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    return jsonify(event.to_dict()), 200

@tickets_bp.route('/tickets/purchase', methods=['POST'])
@require_auth
def purchase_tickets():
    """Purchase tickets"""
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    try:
        tickets = TicketService.purchase_tickets(
            db,
            user_id=user.id,
            event_id=data['eventId'],
            ticket_type=data.get('ticketType', 'standard'),
            quantity=data.get('quantity', 1)
        )

        # TODO: Initiate payment flow

        # Generate QR codes
        for ticket in tickets:
            ticket.qr_code_url = TicketService.generate_qr_code(ticket.ticket_code)

        return jsonify({
            'tickets': [t.to_dict(include_relations=True) for t in tickets],
            'total': sum(float(t.price_paid) for t in tickets)
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@tickets_bp.route('/tickets', methods=['GET'])
@require_auth
def list_user_tickets():
    """List user's tickets"""
    db = get_db()
    user = get_current_user()

    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))

    query = db.query(Ticket).filter(Ticket.user_id == user.id)

    if status:
        query = query.filter(Ticket.status == status)

    tickets = query.order_by(Ticket.created_at.desc()) \
                   .offset((page - 1) * limit) \
                   .limit(limit) \
                   .all()

    # Add QR codes
    result = []
    for ticket in tickets:
        ticket_dict = ticket.to_dict(include_relations=True)
        ticket_dict['qrCodeUrl'] = TicketService.generate_qr_code(ticket.ticket_code)
        result.append(ticket_dict)

    return jsonify(result), 200

@tickets_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
@require_auth
def get_ticket(ticket_id: int):
    """Get ticket details"""
    db = get_db()
    user = get_current_user()

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == user.id
    ).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    ticket_dict = ticket.to_dict(include_relations=True)
    ticket_dict['qrCodeUrl'] = TicketService.generate_qr_code(ticket.ticket_code)

    return jsonify(ticket_dict), 200

@tickets_bp.route('/tickets/<ticket_code>/validate', methods=['POST'])
def validate_ticket(ticket_code: str):
    """Validate ticket"""
    db = get_db()

    result = TicketService.validate_ticket(db, ticket_code)
    return jsonify(result), 200

@tickets_bp.route('/tickets/<int:ticket_id>/cancel', methods=['PUT'])
@require_auth
def cancel_ticket(ticket_id: int):
    """Cancel ticket"""
    db = get_db()
    user = get_current_user()

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == user.id
    ).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    try:
        result = TicketService.cancel_ticket(db, ticket_id)

        # TODO: Process refund if refund_amount > 0

        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
```

### 4. Admin Routes

**File:** `python/api/src/routes/admin/tickets.py`

```python
from flask import Blueprint, request, jsonify
from src.services.ticket_service import TicketService
from src.services.auth_service import require_admin, get_current_user
from src.database import get_db
from src.models.event import Event

admin_tickets_bp = Blueprint('admin_tickets', __name__, url_prefix='/api/v1/admin')

@admin_tickets_bp.route('/events', methods=['POST'])
@require_admin
def create_event():
    """Create new event"""
    db = get_db()
    data = request.get_json()

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
        status=data.get('status', 'draft'),
        image_url=data.get('imageUrl'),
        metadata=data.get('metadata')
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return jsonify(event.to_dict()), 201

@admin_tickets_bp.route('/events/<int:event_id>/tickets', methods=['GET'])
@require_admin
def get_event_tickets(event_id: int):
    """List all tickets for event"""
    db = get_db()

    tickets = db.query(Ticket).filter(Ticket.event_id == event_id).all()
    return jsonify([t.to_dict(include_relations=True) for t in tickets]), 200

@admin_tickets_bp.route('/tickets/<ticket_code>/scan', methods=['POST'])
@require_admin
def scan_ticket(ticket_code: str):
    """Scan ticket for check-in"""
    db = get_db()
    user = get_current_user()
    data = request.get_json()

    result = TicketService.scan_ticket(
        db,
        ticket_code=ticket_code,
        scan_type=data.get('scanType', 'check_in'),
        scan_location=data.get('location'),
        scanner_user_id=user.id
    )

    return jsonify(result), 200 if result['valid'] else 400
```

---

## Testing

### Unit Tests

**File:** `python/api/tests/unit/test_ticket_service.py`

```python
import pytest
from datetime import datetime, timedelta
from src.services.ticket_service import TicketService

def test_purchase_tickets(db_session, test_user, test_event):
    tickets = TicketService.purchase_tickets(
        db_session,
        user_id=test_user.id,
        event_id=test_event.id,
        ticket_type='standard',
        quantity=2
    )

    assert len(tickets) == 2
    assert all(t.status == 'active' for t in tickets)
    assert test_event.current_participants == 2

def test_validate_valid_ticket(db_session, test_ticket):
    result = TicketService.validate_ticket(db_session, test_ticket.ticket_code)
    assert result['valid'] == True

def test_validate_expired_ticket(db_session, test_ticket):
    test_ticket.valid_until = datetime.utcnow() - timedelta(days=1)
    result = TicketService.validate_ticket(db_session, test_ticket.ticket_code)
    assert result['valid'] == False
    assert 'expired' in result['reason'].lower()

def test_generate_qr_code():
    qr_code = TicketService.generate_qr_code("TKT-TEST123")
    assert qr_code.startswith("data:image/png;base64,")
```

---

## Definition of Done

- [x] Database models created and migrated
- [x] Business logic service implemented
- [x] QR code generation working
- [x] User API endpoints implemented
- [x] Admin API endpoints implemented
- [x] Ticket validation system working
- [x] Unit tests with 95%+ coverage
- [x] Integration tests
- [x] API documentation
- [x] Ready for frontend integration

---

## Dependencies

```bash
# Add to requirements.txt
qrcode==7.4.2
pillow==10.1.0
```

---

## Next Steps

After backend implementation:
1. Create frontend Booking Plugin sprint
2. Create frontend Ticket Plugin sprint
3. Create admin management plugins
4. Integrate with notification system
5. Add calendar integration for bookings (.ics files)
