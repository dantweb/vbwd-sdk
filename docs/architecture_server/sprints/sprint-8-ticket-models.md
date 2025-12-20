# Sprint 8: Ticket System - Database Models & Services

**Goal:** Implement database models and core services for the event ticketing system
**Dependencies:** Sprint 1 (Data Layer), Sprint 2 (Auth), Sprint 4 (Payments)

---

## Objectives

- [ ] Create Event, EventTier, Ticket database models
- [ ] Create TicketScan and TicketTransfer models
- [ ] Implement TicketService with business logic
- [ ] Implement QR code generation service
- [ ] Create database migrations
- [ ] Write comprehensive unit tests (95%+ coverage)

---

## Database Models

### 1. Event Model

**File:** `python/api/src/models/event.py`

```python
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Decimal as DecimalColumn, Boolean, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class EventType:
    CONFERENCE = 'conference'
    WORKSHOP = 'workshop'
    WEBINAR = 'webinar'
    SERIES = 'series'
    OTHER = 'other'

class EventStatus:
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

class Event(Base):
    """
    Event entity for ticketed events.

    Represents conferences, workshops, webinars, etc.
    Tracks participant capacity and ticket availability.
    """
    __tablename__ = 'events'
    __table_args__ = (
        Index('idx_dates', 'start_date', 'end_date', 'status'),
        Index('idx_status', 'status', 'start_date'),
        Index('idx_event_type', 'event_type', 'status'),
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
    ticket_price = Column(DecimalColumn(10, 2))
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
    tiers = relationship('EventTier', back_populates='event', cascade='all, delete-orphan')

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

    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming"""
        return datetime.utcnow() < self.start_date

    @property
    def is_ongoing(self) -> bool:
        """Check if event is currently happening"""
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date

    @property
    def is_past(self) -> bool:
        """Check if event has ended"""
        return datetime.utcnow() > self.end_date

    def to_dict(self) -> dict:
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
            'availableTickets': self.available_tickets,
            'ticketPrice': float(self.ticket_price) if self.ticket_price else None,
            'status': self.status,
            'imageUrl': self.image_url,
            'isSoldOut': self.is_sold_out,
            'isUpcoming': self.is_upcoming,
            'metadata': self.metadata,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', status='{self.status}')>"
```

### 2. EventTier Model

**File:** `python/api/src/models/event_tier.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class EventTier(Base):
    """
    Event pricing tier (VIP, Early Bird, Group, etc.)

    Allows different pricing levels for the same event.
    """
    __tablename__ = 'event_tiers'
    __table_args__ = (
        Index('idx_event_tier', 'event_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Decimal(10, 2), nullable=False)
    max_quantity = Column(Integer)
    sold_count = Column(Integer, default=0)
    benefits = Column(JSON)  # List of benefits for this tier
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship('Event', back_populates='tiers')
    tickets = relationship('Ticket', back_populates='tier')

    @property
    def available_quantity(self) -> int:
        """Get available tickets for this tier"""
        if not self.max_quantity:
            return 999999
        return max(0, self.max_quantity - self.sold_count)

    @property
    def is_sold_out(self) -> bool:
        """Check if tier is sold out"""
        if not self.max_quantity:
            return False
        return self.sold_count >= self.max_quantity

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'eventId': self.event_id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'maxQuantity': self.max_quantity,
            'soldCount': self.sold_count,
            'availableQuantity': self.available_quantity,
            'benefits': self.benefits,
            'isActive': self.is_active,
            'isSoldOut': self.is_sold_out,
            'sortOrder': self.sort_order,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<EventTier(id={self.id}, name='{self.name}', price={self.price})>"
```

### 3. Ticket Model

**File:** `python/api/src/models/ticket.py`

```python
import secrets
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Decimal, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class TicketType:
    STANDARD = 'standard'
    VIP = 'vip'
    EARLY_BIRD = 'early_bird'
    GROUP = 'group'

class TicketStatus:
    ACTIVE = 'active'
    USED = 'used'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

class Ticket(Base):
    """
    Ticket entity for event access.

    Represents a purchased ticket with unique code for QR scanning.
    Tracks validity period and usage status.
    """
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
    event_tier_id = Column(Integer, ForeignKey('event_tiers.id', ondelete='SET NULL'), nullable=True)
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
    tier = relationship('EventTier', back_populates='tickets')
    scans = relationship('TicketScan', back_populates='ticket', cascade='all, delete-orphan')
    transfers = relationship('TicketTransfer', back_populates='ticket', cascade='all, delete-orphan')

    @staticmethod
    def generate_ticket_code(prefix: str = 'TKT') -> str:
        """Generate unique ticket code"""
        return f"{prefix}-{secrets.token_hex(8).upper()}"

    @property
    def is_valid(self) -> bool:
        """Check if ticket is valid for use"""
        if self.status != TicketStatus.ACTIVE:
            return False

        now = datetime.utcnow()
        return self.valid_from <= now <= self.valid_until

    @property
    def is_checked_in(self) -> bool:
        """Check if ticket has been used for check-in"""
        return self.check_in_time is not None

    def to_dict(self, include_relations: bool = False) -> dict:
        result = {
            'id': self.id,
            'ticketCode': self.ticket_code,
            'userId': self.user_id,
            'eventId': self.event_id,
            'eventTierId': self.event_tier_id,
            'ticketType': self.ticket_type,
            'status': self.status,
            'pricePaid': float(self.price_paid),
            'validFrom': self.valid_from.isoformat() if self.valid_from else None,
            'validUntil': self.valid_until.isoformat() if self.valid_until else None,
            'paymentId': self.payment_id,
            'checkInTime': self.check_in_time.isoformat() if self.check_in_time else None,
            'isValid': self.is_valid,
            'isCheckedIn': self.is_checked_in,
            'metadata': self.metadata,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_relations:
            if self.event:
                result['event'] = self.event.to_dict()
            if self.tier:
                result['tier'] = self.tier.to_dict()

        return result

    def __repr__(self):
        return f"<Ticket(id={self.id}, code='{self.ticket_code}', status='{self.status}')>"
```

### 4. TicketScan Model

**File:** `python/api/src/models/ticket_scan.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class ScanType:
    CHECK_IN = 'check_in'
    CHECK_OUT = 'check_out'
    ACCESS = 'access'

class TicketScan(Base):
    """
    Ticket scan record for access control.

    Records every scan for audit trail and analytics.
    """
    __tablename__ = 'ticket_scans'
    __table_args__ = (
        Index('idx_ticket_scans', 'ticket_id', 'scanned_at'),
        Index('idx_scan_location', 'scan_location', 'scanned_at'),
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
    device_info = Column(String(255))
    metadata = Column(JSON)

    # Relationships
    ticket = relationship('Ticket', back_populates='scans')
    scanner = relationship('User', foreign_keys=[scanner_user_id])

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ticketId': self.ticket_id,
            'scannedAt': self.scanned_at.isoformat() if self.scanned_at else None,
            'scanLocation': self.scan_location,
            'scanType': self.scan_type,
            'scannerUserId': self.scanner_user_id,
            'deviceInfo': self.device_info,
            'metadata': self.metadata,
        }

    def __repr__(self):
        return f"<TicketScan(id={self.id}, ticket={self.ticket_id}, type='{self.scan_type}')>"
```

### 5. TicketTransfer Model

**File:** `python/api/src/models/ticket_transfer.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Index
from sqlalchemy.orm import relationship
from src.models.base import Base

class TicketTransfer(Base):
    """
    Ticket transfer audit record.

    Tracks ownership changes for compliance and support.
    """
    __tablename__ = 'ticket_transfers'
    __table_args__ = (
        Index('idx_ticket_transfers', 'ticket_id', 'transferred_at'),
        Index('idx_from_user', 'from_user_id', 'transferred_at'),
        Index('idx_to_user', 'to_user_id', 'transferred_at'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    from_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    to_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    transferred_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    initiated_by = Column(String(50))  # 'user', 'admin', 'system'

    # Relationships
    ticket = relationship('Ticket', back_populates='transfers')
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ticketId': self.ticket_id,
            'fromUserId': self.from_user_id,
            'toUserId': self.to_user_id,
            'transferredAt': self.transferred_at.isoformat() if self.transferred_at else None,
            'notes': self.notes,
            'initiatedBy': self.initiated_by,
        }

    def __repr__(self):
        return f"<TicketTransfer(id={self.id}, ticket={self.ticket_id})>"
```

---

## Services

### 6. TicketService

**File:** `python/api/src/services/ticket_service.py`

```python
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models.ticket import Ticket, TicketStatus, TicketType
from src.models.event import Event, EventStatus
from src.models.event_tier import EventTier
from src.models.ticket_scan import TicketScan, ScanType
from src.models.ticket_transfer import TicketTransfer

class TicketError(Exception):
    """Custom exception for ticket operations"""
    pass

class TicketService:
    """
    Business logic for ticket management.

    Handles ticket purchase, validation, scanning, transfers, and refunds.
    """

    # Refund policy constants
    FULL_REFUND_DAYS = 7
    PARTIAL_REFUND_DAYS = 3
    PARTIAL_REFUND_PERCENTAGE = 0.5

    @staticmethod
    def purchase_tickets(
        db: Session,
        user_id: int,
        event_id: int,
        ticket_type: str = TicketType.STANDARD,
        tier_id: Optional[int] = None,
        quantity: int = 1
    ) -> List[Ticket]:
        """
        Purchase tickets for an event.

        Args:
            db: Database session
            user_id: Purchasing user
            event_id: Target event
            ticket_type: Type of ticket
            tier_id: Optional pricing tier
            quantity: Number of tickets

        Returns:
            List of created tickets

        Raises:
            TicketError: If purchase not possible
        """
        # Validate event
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise TicketError("Event not found")

        if event.status != EventStatus.PUBLISHED:
            raise TicketError("Event is not available for purchase")

        if event.is_past:
            raise TicketError("Event has already ended")

        # Check availability
        if event.available_tickets < quantity:
            raise TicketError(f"Only {event.available_tickets} tickets available")

        # Determine price
        price = event.ticket_price
        tier = None

        if tier_id:
            tier = db.query(EventTier).filter(
                EventTier.id == tier_id,
                EventTier.event_id == event_id,
                EventTier.is_active == True
            ).first()

            if not tier:
                raise TicketError("Ticket tier not found or inactive")

            if tier.available_quantity < quantity:
                raise TicketError(f"Only {tier.available_quantity} tickets available for this tier")

            price = tier.price

        # Create tickets
        tickets = []
        for _ in range(quantity):
            ticket = Ticket(
                ticket_code=Ticket.generate_ticket_code(),
                user_id=user_id,
                event_id=event_id,
                event_tier_id=tier_id,
                ticket_type=ticket_type,
                status=TicketStatus.ACTIVE,
                price_paid=price,
                valid_from=event.start_date,
                valid_until=event.end_date,
            )
            tickets.append(ticket)

        db.add_all(tickets)

        # Update counts
        event.current_participants += quantity
        if tier:
            tier.sold_count += quantity

        db.commit()

        for ticket in tickets:
            db.refresh(ticket)

        return tickets

    @staticmethod
    def validate_ticket(db: Session, ticket_code: str) -> Dict:
        """
        Validate ticket for access.

        Args:
            db: Database session
            ticket_code: Unique ticket code

        Returns:
            Validation result dict
        """
        ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()

        if not ticket:
            return {
                'valid': False,
                'reason': 'Ticket not found',
                'ticket': None
            }

        if ticket.status != TicketStatus.ACTIVE:
            return {
                'valid': False,
                'reason': f'Ticket status is {ticket.status}',
                'ticket': ticket.to_dict(include_relations=True)
            }

        now = datetime.utcnow()

        if now < ticket.valid_from:
            return {
                'valid': False,
                'reason': 'Ticket is not yet valid',
                'ticket': ticket.to_dict(include_relations=True)
            }

        if now > ticket.valid_until:
            # Auto-expire ticket
            ticket.status = TicketStatus.EXPIRED
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
        scan_type: str = ScanType.ACCESS,
        scan_location: Optional[str] = None,
        scanner_user_id: Optional[int] = None,
        device_info: Optional[str] = None,
        mark_as_used: bool = False
    ) -> Dict:
        """
        Scan ticket and record access.

        Args:
            db: Database session
            ticket_code: Ticket to scan
            scan_type: Type of scan
            scan_location: Location identifier
            scanner_user_id: Staff member scanning
            device_info: Scanner device info
            mark_as_used: Whether to mark single-entry tickets as used

        Returns:
            Scan result dict
        """
        # Validate first
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
            device_info=device_info,
        )
        db.add(scan)

        # Update check-in time
        if scan_type == ScanType.CHECK_IN and not ticket.check_in_time:
            ticket.check_in_time = datetime.utcnow()

        # Mark as used for single-entry events
        if mark_as_used and scan_type == ScanType.CHECK_IN:
            ticket.status = TicketStatus.USED

        db.commit()
        db.refresh(scan)

        return {
            'valid': True,
            'scan': scan.to_dict(),
            'ticket': ticket.to_dict(include_relations=True)
        }

    @staticmethod
    def transfer_ticket(
        db: Session,
        ticket_id: int,
        from_user_id: int,
        to_user_id: int,
        notes: Optional[str] = None,
        initiated_by: str = 'user'
    ) -> Ticket:
        """
        Transfer ticket to another user.

        Args:
            db: Database session
            ticket_id: Ticket to transfer
            from_user_id: Current owner
            to_user_id: New owner
            notes: Transfer notes
            initiated_by: Who initiated (user, admin, system)

        Returns:
            Updated ticket
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise TicketError("Ticket not found")

        if ticket.user_id != from_user_id:
            raise TicketError("Ticket does not belong to specified user")

        if ticket.status != TicketStatus.ACTIVE:
            raise TicketError(f"Cannot transfer ticket with status: {ticket.status}")

        if ticket.is_checked_in:
            raise TicketError("Cannot transfer ticket after check-in")

        # Create transfer record
        transfer = TicketTransfer(
            ticket_id=ticket_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            notes=notes,
            initiated_by=initiated_by,
        )
        db.add(transfer)

        # Update ticket ownership
        ticket.user_id = to_user_id

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def cancel_ticket(db: Session, ticket_id: int) -> Dict:
        """
        Cancel ticket and calculate refund.

        Args:
            db: Database session
            ticket_id: Ticket to cancel

        Returns:
            Dict with ticket and refund_amount
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise TicketError("Ticket not found")

        if ticket.status not in [TicketStatus.ACTIVE]:
            raise TicketError(f"Cannot cancel ticket with status: {ticket.status}")

        if ticket.is_checked_in:
            raise TicketError("Cannot cancel ticket after check-in")

        # Calculate refund
        refund_amount = TicketService._calculate_refund(ticket)

        # Update ticket
        if refund_amount > 0:
            ticket.status = TicketStatus.REFUNDED
        else:
            ticket.status = TicketStatus.CANCELLED

        # Update event count
        event = db.query(Event).filter(Event.id == ticket.event_id).first()
        if event:
            event.current_participants = max(0, event.current_participants - 1)

        # Update tier count if applicable
        if ticket.event_tier_id:
            tier = db.query(EventTier).filter(EventTier.id == ticket.event_tier_id).first()
            if tier:
                tier.sold_count = max(0, tier.sold_count - 1)

        db.commit()
        db.refresh(ticket)

        return {
            'ticket': ticket.to_dict(include_relations=True),
            'refund_amount': float(refund_amount)
        }

    @staticmethod
    def _calculate_refund(ticket: Ticket) -> Decimal:
        """
        Calculate refund based on cancellation policy.

        Policy:
        - 7+ days before: 100% refund
        - 3-7 days before: 50% refund
        - Less than 3 days: No refund
        """
        now = datetime.utcnow()
        days_before = (ticket.valid_from - now).days

        if days_before >= TicketService.FULL_REFUND_DAYS:
            return ticket.price_paid
        elif days_before >= TicketService.PARTIAL_REFUND_DAYS:
            return ticket.price_paid * Decimal(str(TicketService.PARTIAL_REFUND_PERCENTAGE))
        else:
            return Decimal('0.00')

    @staticmethod
    def expire_old_tickets(db: Session) -> int:
        """
        Batch job to expire tickets past their validity.

        Returns:
            Number of tickets expired
        """
        now = datetime.utcnow()

        count = db.query(Ticket).filter(
            Ticket.status == TicketStatus.ACTIVE,
            Ticket.valid_until < now
        ).update({'status': TicketStatus.EXPIRED})

        db.commit()
        return count
```

### 7. QRCodeService

**File:** `python/api/src/services/qr_code_service.py`

```python
import qrcode
import io
import base64
from typing import Optional

class QRCodeService:
    """
    Service for generating QR codes for tickets.
    """

    @staticmethod
    def generate_qr_code(
        data: str,
        size: int = 10,
        border: int = 4,
        error_correction: str = 'L'
    ) -> str:
        """
        Generate QR code as base64 data URL.

        Args:
            data: Data to encode
            size: Box size
            border: Border size
            error_correction: L, M, Q, H

        Returns:
            Base64 data URL
        """
        error_correction_levels = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H,
        }

        qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_L),
            box_size=size,
            border=border,
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def generate_ticket_qr(ticket_code: str, base_url: Optional[str] = None) -> str:
        """
        Generate QR code for a ticket.

        Args:
            ticket_code: Ticket code to encode
            base_url: Optional validation URL base

        Returns:
            Base64 QR code data URL
        """
        if base_url:
            data = f"{base_url}/validate/{ticket_code}"
        else:
            data = ticket_code

        return QRCodeService.generate_qr_code(data, size=10, error_correction='M')
```

---

## Database Migration

**File:** `python/api/migrations/versions/xxx_add_ticket_tables.py`

```python
"""Add ticket system tables

Revision ID: xxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('event_type', sa.Enum('conference', 'workshop', 'webinar', 'series', 'other', name='event_type_enum'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String(255)),
        sa.Column('is_online', sa.Boolean(), default=False),
        sa.Column('max_participants', sa.Integer()),
        sa.Column('current_participants', sa.Integer(), default=0),
        sa.Column('ticket_price', sa.Numeric(10, 2)),
        sa.Column('status', sa.Enum('draft', 'published', 'cancelled', 'completed', name='event_status_enum'), default='draft'),
        sa.Column('image_url', sa.String(500)),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_dates', 'events', ['start_date', 'end_date', 'status'])
    op.create_index('idx_status', 'events', ['status', 'start_date'])

    # Create event_tiers table
    op.create_table(
        'event_tiers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_quantity', sa.Integer()),
        sa.Column('sold_count', sa.Integer(), default=0),
        sa.Column('benefits', sa.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('idx_event_tier', 'event_tiers', ['event_id', 'is_active'])

    # Create tickets table
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ticket_code', sa.String(50), unique=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('event_tier_id', sa.Integer(), sa.ForeignKey('event_tiers.id', ondelete='SET NULL')),
        sa.Column('ticket_type', sa.Enum('standard', 'vip', 'early_bird', 'group', name='ticket_type_enum'), default='standard'),
        sa.Column('status', sa.Enum('active', 'used', 'expired', 'cancelled', 'refunded', name='ticket_status_enum'), default='active'),
        sa.Column('price_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('payment_id', sa.String(255)),
        sa.Column('check_in_time', sa.DateTime()),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_user_tickets', 'tickets', ['user_id', 'status'])
    op.create_index('idx_event_tickets', 'tickets', ['event_id', 'status'])
    op.create_index('idx_ticket_code', 'tickets', ['ticket_code'])
    op.create_index('idx_validity', 'tickets', ['valid_from', 'valid_until', 'status'])

    # Create ticket_scans table
    op.create_table(
        'ticket_scans',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scanned_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('scan_location', sa.String(100)),
        sa.Column('scan_type', sa.Enum('check_in', 'check_out', 'access', name='scan_type_enum'), default='access'),
        sa.Column('scanner_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('device_info', sa.String(255)),
        sa.Column('metadata', sa.JSON()),
    )
    op.create_index('idx_ticket_scans', 'ticket_scans', ['ticket_id', 'scanned_at'])

    # Create ticket_transfers table
    op.create_table(
        'ticket_transfers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('to_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('transferred_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('notes', sa.Text()),
        sa.Column('initiated_by', sa.String(50)),
    )
    op.create_index('idx_ticket_transfers', 'ticket_transfers', ['ticket_id', 'transferred_at'])

def downgrade():
    op.drop_table('ticket_transfers')
    op.drop_table('ticket_scans')
    op.drop_table('tickets')
    op.drop_table('event_tiers')
    op.drop_table('events')
```

---

## Unit Tests

**File:** `python/api/tests/unit/test_ticket_service.py`

```python
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from src.services.ticket_service import TicketService, TicketError
from src.models.ticket import TicketStatus

class TestTicketService:
    """Test suite for TicketService"""

    def test_purchase_tickets_success(self, db_session, test_user, published_event):
        """Test successful ticket purchase"""
        tickets = TicketService.purchase_tickets(
            db_session,
            user_id=test_user.id,
            event_id=published_event.id,
            quantity=2
        )

        assert len(tickets) == 2
        assert all(t.status == TicketStatus.ACTIVE for t in tickets)
        assert published_event.current_participants == 2

    def test_purchase_exceeds_capacity(self, db_session, test_user, sold_out_event):
        """Test purchase fails when sold out"""
        with pytest.raises(TicketError, match="tickets available"):
            TicketService.purchase_tickets(
                db_session,
                user_id=test_user.id,
                event_id=sold_out_event.id,
                quantity=1
            )

    def test_validate_active_ticket(self, db_session, active_ticket):
        """Test validation of active ticket"""
        result = TicketService.validate_ticket(db_session, active_ticket.ticket_code)
        assert result['valid'] == True

    def test_validate_expired_ticket(self, db_session, expired_ticket):
        """Test validation of expired ticket"""
        result = TicketService.validate_ticket(db_session, expired_ticket.ticket_code)
        assert result['valid'] == False
        assert 'expired' in result['reason'].lower()

    def test_scan_ticket(self, db_session, active_ticket, admin_user):
        """Test scanning a ticket"""
        result = TicketService.scan_ticket(
            db_session,
            ticket_code=active_ticket.ticket_code,
            scan_type='check_in',
            scan_location='Main Gate',
            scanner_user_id=admin_user.id
        )

        assert result['valid'] == True
        assert result['scan']['scanType'] == 'check_in'

    def test_transfer_ticket(self, db_session, active_ticket, test_user, other_user):
        """Test ticket transfer"""
        ticket = TicketService.transfer_ticket(
            db_session,
            ticket_id=active_ticket.id,
            from_user_id=test_user.id,
            to_user_id=other_user.id
        )

        assert ticket.user_id == other_user.id

    def test_cancel_ticket_full_refund(self, db_session, active_ticket):
        """Test cancellation with full refund"""
        active_ticket.valid_from = datetime.utcnow() + timedelta(days=14)

        result = TicketService.cancel_ticket(db_session, active_ticket.id)

        assert result['ticket']['status'] == TicketStatus.REFUNDED
        assert result['refund_amount'] == float(active_ticket.price_paid)

    def test_cancel_ticket_no_refund(self, db_session, active_ticket):
        """Test cancellation with no refund"""
        active_ticket.valid_from = datetime.utcnow() + timedelta(days=1)

        result = TicketService.cancel_ticket(db_session, active_ticket.id)

        assert result['ticket']['status'] == TicketStatus.CANCELLED
        assert result['refund_amount'] == 0
```

---

## Definition of Done

- [ ] All database models created with proper relationships
- [ ] Database migrations tested and working
- [ ] TicketService with full CRUD and validation
- [ ] QRCodeService for ticket QR generation
- [ ] Transfer functionality implemented
- [ ] Refund calculation logic working
- [ ] Unit tests with 95%+ coverage
- [ ] Integration tests passing
- [ ] Code reviewed and approved

---

## Related Documentation

- [Ticket Data Model](../puml/ticket-data-model.puml)
- [Ticket Flow](../puml/ticket-flow.puml)
- [Ticket Lifecycle](../puml/ticket-lifecycle.puml)

---

## Dependencies

Add to `requirements.txt`:

```
qrcode==7.4.2
pillow==10.1.0
```

---

## Next Sprint

[Sprint 9: Ticket System - API Routes](./sprint-9-ticket-api.md)
