# Booking & Ticket System

**Status:** Planning Phase
**Priority:** High
**Dependencies:** Core authentication, payment system

---

## Overview

The platform supports two additional access control mechanisms:

1. **Booking System** - Time-slot based reservations for private services (dentist appointments, consultations, private sessions)
2. **Ticket System** - Time-limited access tokens for events with multiple participants

---

## Entity Relationships

```
User (1) ──── (N) Booking ──── (1) Timeslot ──── (1) Room/Resource
User (1) ──── (N) Ticket ──── (1) Event
Event (1) ──── (N) Ticket
```

---

## 1. Booking System

### Use Cases

- **Medical Appointments**: Book 30-minute dentist appointment
- **Consultations**: Book 1-hour consultation with expert
- **Private Sessions**: Book therapy session, coaching call
- **Room Rentals**: Book meeting room for specific time

### Database Schema

**Table: `rooms`**
```sql
CREATE TABLE rooms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capacity INT DEFAULT 1,
    room_type ENUM('office', 'consultation', 'meeting', 'treatment') NOT NULL,
    hourly_rate DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Table: `timeslots`**
```sql
CREATE TABLE timeslots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    price DECIMAL(10,2),
    max_bookings INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    INDEX idx_room_time (room_id, start_time, end_time),
    INDEX idx_availability (is_available, start_time)
);
```

**Table: `bookings`**
```sql
CREATE TABLE bookings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    timeslot_id INT NOT NULL,
    room_id INT NOT NULL,
    status ENUM('pending', 'confirmed', 'cancelled', 'completed', 'no_show') DEFAULT 'pending',
    booking_type VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    payment_status ENUM('pending', 'paid', 'refunded') DEFAULT 'pending',
    payment_id VARCHAR(255),
    notes TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (timeslot_id) REFERENCES timeslots(id) ON DELETE RESTRICT,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE RESTRICT,
    INDEX idx_user_bookings (user_id, status),
    INDEX idx_timeslot (timeslot_id),
    INDEX idx_status (status, created_at)
);
```

### API Endpoints

#### User Endpoints

```
GET    /api/v1/bookings/rooms
       List available rooms with filters

GET    /api/v1/bookings/rooms/:id/timeslots
       Get available timeslots for a room
       Query: ?date=2025-01-15&duration=30

POST   /api/v1/bookings
       Create new booking
       Body: { timeslotId, roomId, notes }

GET    /api/v1/bookings
       List user's bookings
       Query: ?status=confirmed&page=1

GET    /api/v1/bookings/:id
       Get booking details

PUT    /api/v1/bookings/:id/cancel
       Cancel booking (with refund policy)

PUT    /api/v1/bookings/:id/reschedule
       Reschedule booking to new timeslot
```

#### Admin Endpoints

```
POST   /api/v1/admin/rooms
       Create room

PUT    /api/v1/admin/rooms/:id
       Update room

DELETE /api/v1/admin/rooms/:id
       Delete room

POST   /api/v1/admin/timeslots/generate
       Generate timeslots for room
       Body: { roomId, startDate, endDate, slotDuration, workingHours }

GET    /api/v1/admin/bookings
       List all bookings with filters

PUT    /api/v1/admin/bookings/:id/status
       Update booking status
```

---

## 2. Ticket System

### Use Cases

- **Conference Tickets**: Access to 3-day tech conference
- **Workshop Access**: 1-day workshop with 50 participants
- **Webinar Tickets**: Live webinar access
- **Event Series**: Multi-session event access

### Database Schema

**Table: `events`**
```sql
CREATE TABLE events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    event_type ENUM('conference', 'workshop', 'webinar', 'series', 'other') NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    location VARCHAR(255),
    is_online BOOLEAN DEFAULT FALSE,
    max_participants INT,
    current_participants INT DEFAULT 0,
    ticket_price DECIMAL(10,2),
    status ENUM('draft', 'published', 'cancelled', 'completed') DEFAULT 'draft',
    image_url VARCHAR(500),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dates (start_date, end_date, status),
    INDEX idx_status (status, start_date)
);
```

**Table: `tickets`**
```sql
CREATE TABLE tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    ticket_type ENUM('standard', 'vip', 'early_bird', 'group') DEFAULT 'standard',
    status ENUM('active', 'used', 'expired', 'cancelled', 'refunded') DEFAULT 'active',
    price_paid DECIMAL(10,2) NOT NULL,
    valid_from DATETIME NOT NULL,
    valid_until DATETIME NOT NULL,
    payment_id VARCHAR(255),
    check_in_time TIMESTAMP NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE RESTRICT,
    INDEX idx_user_tickets (user_id, status),
    INDEX idx_event_tickets (event_id, status),
    INDEX idx_ticket_code (ticket_code),
    INDEX idx_validity (valid_from, valid_until, status)
);
```

**Table: `ticket_scans`** (for access control)
```sql
CREATE TABLE ticket_scans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_id INT NOT NULL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_location VARCHAR(100),
    scan_type ENUM('check_in', 'check_out', 'access') DEFAULT 'access',
    scanner_user_id INT,
    metadata JSON,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (scanner_user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_ticket_scans (ticket_id, scanned_at)
);
```

### API Endpoints

#### User Endpoints

```
GET    /api/v1/events
       List published events
       Query: ?type=conference&startDate=2025-01-01&page=1

GET    /api/v1/events/:id
       Get event details

POST   /api/v1/tickets/purchase
       Purchase ticket for event
       Body: { eventId, ticketType, quantity }

GET    /api/v1/tickets
       List user's tickets
       Query: ?status=active&page=1

GET    /api/v1/tickets/:id
       Get ticket details with QR code

POST   /api/v1/tickets/:ticketCode/validate
       Validate ticket (check if valid for access)

PUT    /api/v1/tickets/:id/cancel
       Cancel ticket (with refund policy)
```

#### Admin Endpoints

```
POST   /api/v1/admin/events
       Create event

PUT    /api/v1/admin/events/:id
       Update event

DELETE /api/v1/admin/events/:id
       Delete event

GET    /api/v1/admin/events/:id/tickets
       List all tickets for event

POST   /api/v1/admin/tickets/:ticketCode/scan
       Scan ticket for check-in
       Body: { scanType, location }

GET    /api/v1/admin/tickets/:id/scans
       Get ticket scan history

PUT    /api/v1/admin/tickets/:id/status
       Update ticket status
```

---

## Business Logic

### Booking System

#### Booking Creation Flow
1. User selects room and available timeslot
2. System checks timeslot availability
3. System creates pending booking
4. User completes payment
5. On payment success:
   - Mark booking as `confirmed`
   - Mark timeslot as unavailable
   - Send confirmation email
6. On payment failure:
   - Cancel booking
   - Release timeslot

#### Cancellation Policy
```python
def calculate_refund(booking, cancellation_time):
    hours_before = (booking.start_time - cancellation_time).hours

    if hours_before >= 24:
        return booking.price * 1.0  # 100% refund
    elif hours_before >= 6:
        return booking.price * 0.5  # 50% refund
    else:
        return 0  # No refund
```

#### Booking States
- `pending` → `confirmed` (payment received)
- `confirmed` → `cancelled` (user cancels)
- `confirmed` → `completed` (appointment completed)
- `confirmed` → `no_show` (user didn't show up)

### Ticket System

#### Ticket Purchase Flow
1. User selects event and quantity
2. System checks availability (max_participants)
3. System creates pending tickets
4. User completes payment
5. On payment success:
   - Mark tickets as `active`
   - Generate unique ticket codes
   - Increment event participant count
   - Send tickets via email with QR codes
6. On payment failure:
   - Delete pending tickets

#### Ticket Validation
```python
def validate_ticket(ticket_code):
    ticket = get_ticket_by_code(ticket_code)

    if not ticket:
        return {"valid": False, "reason": "Ticket not found"}

    if ticket.status != "active":
        return {"valid": False, "reason": f"Ticket is {ticket.status}"}

    now = datetime.now()
    if now < ticket.valid_from:
        return {"valid": False, "reason": "Ticket not yet valid"}

    if now > ticket.valid_until:
        return {"valid": False, "reason": "Ticket expired"}

    return {"valid": True, "ticket": ticket}
```

#### Ticket States
- `active` → `used` (scanned for check-in)
- `active` → `expired` (validity period ended)
- `active` → `cancelled` (user cancels)
- `active` → `refunded` (payment refunded)

---

## Integration with Existing Systems

### Payment Integration

Both bookings and tickets use the existing payment system:

```python
# Booking payment
checkout_data = {
    "type": "booking",
    "booking_id": booking.id,
    "amount": booking.price,
    "currency": "USD",
    "description": f"Booking for {room.name} on {timeslot.start_time}"
}

# Ticket payment
checkout_data = {
    "type": "ticket",
    "event_id": event.id,
    "quantity": 2,
    "amount": event.ticket_price * 2,
    "currency": "USD",
    "description": f"{quantity} tickets for {event.name}"
}
```

### Notification Integration

- **Booking Confirmed**: Email with booking details, calendar invite (.ics)
- **Booking Reminder**: Email 24 hours before appointment
- **Ticket Purchased**: Email with QR codes and event details
- **Event Reminder**: Email 24 hours before event start

### Access Control Integration

Users can access content/features based on:
1. **Subscription Plans** (existing) - Recurring access
2. **Active Bookings** (new) - Time-slot specific access
3. **Valid Tickets** (new) - Event-period access

```python
def check_user_access(user, resource):
    # Check subscription (existing)
    if has_active_subscription(user, resource.required_plan):
        return True

    # Check active booking (new)
    if has_active_booking(user, resource.room_id):
        return True

    # Check valid ticket (new)
    if has_valid_ticket(user, resource.event_id):
        return True

    return False
```

---

## Frontend Architecture

### New Plugins

#### 1. Booking Plugin (User)
- **Routes:**
  - `/bookings` - List user's bookings
  - `/bookings/new` - Browse rooms and book timeslots
  - `/bookings/:id` - Booking details
- **Components:**
  - `RoomList.vue` - Browse available rooms
  - `TimeslotCalendar.vue` - Visual calendar for selecting timeslots
  - `BookingCard.vue` - Display booking info
  - `BookingForm.vue` - Create/reschedule booking
- **Store:** `bookingStore` (Pinia)

#### 2. Ticket Plugin (User)
- **Routes:**
  - `/events` - Browse events
  - `/events/:id` - Event details
  - `/tickets` - My tickets
  - `/tickets/:id` - Ticket details with QR code
- **Components:**
  - `EventList.vue` - Browse events with filters
  - `EventCard.vue` - Display event info
  - `TicketCard.vue` - Display ticket with QR code
  - `TicketPurchase.vue` - Purchase flow
- **Store:** `ticketStore` (Pinia)

#### 3. Booking Management Plugin (Admin)
- **Routes:**
  - `/admin/bookings` - Manage all bookings
  - `/admin/rooms` - Manage rooms
  - `/admin/timeslots` - Manage timeslots
- **Components:**
  - `BookingManagement.vue` - Admin booking list
  - `RoomManagement.vue` - CRUD rooms
  - `TimeslotGenerator.vue` - Generate timeslots

#### 4. Event Management Plugin (Admin)
- **Routes:**
  - `/admin/events` - Manage events
  - `/admin/events/:id/tickets` - Event ticket management
  - `/admin/scanner` - Ticket scanner interface
- **Components:**
  - `EventManagement.vue` - CRUD events
  - `TicketScanner.vue` - QR code scanner
  - `TicketList.vue` - Event ticket list

---

## API Type Definitions

**File:** `frontend/core/src/types/booking.ts`

```typescript
export interface Room {
  id: number;
  name: string;
  description: string;
  capacity: number;
  roomType: 'office' | 'consultation' | 'meeting' | 'treatment';
  hourlyRate: number;
  isActive: boolean;
  metadata?: Record<string, any>;
}

export interface Timeslot {
  id: number;
  roomId: number;
  startTime: string;
  endTime: string;
  isAvailable: boolean;
  price: number;
  maxBookings: number;
}

export interface Booking {
  id: number;
  userId: number;
  timeslotId: number;
  roomId: number;
  room: Room;
  timeslot: Timeslot;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show';
  bookingType?: string;
  price: number;
  paymentStatus: 'pending' | 'paid' | 'refunded';
  paymentId?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  cancelledAt?: string;
}

export interface CreateBookingRequest {
  timeslotId: number;
  roomId: number;
  notes?: string;
}
```

**File:** `frontend/core/src/types/ticket.ts`

```typescript
export interface Event {
  id: number;
  name: string;
  description: string;
  eventType: 'conference' | 'workshop' | 'webinar' | 'series' | 'other';
  startDate: string;
  endDate: string;
  location?: string;
  isOnline: boolean;
  maxParticipants?: number;
  currentParticipants: number;
  ticketPrice: number;
  status: 'draft' | 'published' | 'cancelled' | 'completed';
  imageUrl?: string;
  metadata?: Record<string, any>;
}

export interface Ticket {
  id: number;
  ticketCode: string;
  userId: number;
  eventId: number;
  event: Event;
  ticketType: 'standard' | 'vip' | 'early_bird' | 'group';
  status: 'active' | 'used' | 'expired' | 'cancelled' | 'refunded';
  pricePaid: number;
  validFrom: string;
  validUntil: string;
  paymentId?: string;
  checkInTime?: string;
  qrCodeUrl?: string;
  metadata?: Record<string, any>;
}

export interface PurchaseTicketRequest {
  eventId: number;
  ticketType: 'standard' | 'vip' | 'early_bird' | 'group';
  quantity: number;
}

export interface ValidateTicketResponse {
  valid: boolean;
  reason?: string;
  ticket?: Ticket;
}
```

---

## Implementation Sprints

### Booking System
- **[Sprint 6: Booking Models & Services](./sprints/sprint-6-booking-models.md)** - Database models, business logic
- **[Sprint 7: Booking API Routes](./sprints/sprint-7-booking-api.md)** - User and admin endpoints

### Ticket System
- **[Sprint 8: Ticket Models & Services](./sprints/sprint-8-ticket-models.md)** - Database models, QR generation
- **[Sprint 9: Ticket API Routes](./sprints/sprint-9-ticket-api.md)** - Events, tickets, scanner API

---

## PlantUML Diagrams

### Booking System
- **[Booking Data Model](./puml/booking-data-model.puml)** - Entity relationships (Room, Timeslot, Booking)
- **[Booking Flow](./puml/booking-flow.puml)** - Sequence diagram for booking lifecycle
- **[Booking Lifecycle](./puml/booking-lifecycle.puml)** - State machine for booking status

### Ticket System
- **[Ticket Data Model](./puml/ticket-data-model.puml)** - Entity relationships (Event, Ticket, Scan)
- **[Ticket Flow](./puml/ticket-flow.puml)** - Sequence diagram for ticket purchase and validation
- **[Ticket Lifecycle](./puml/ticket-lifecycle.puml)** - State machine for ticket status

---

## Next Steps

1. ~~Create backend implementation sprints~~ ✓
2. Create frontend plugin sprints
3. ~~Design QR code generation system~~ ✓ (in Sprint 8)
4. Plan notification templates
5. ~~Define refund policies~~ ✓ (in Services)
6. Design calendar integration (.ics files)

---

## Related Documentation

- [Backend Architecture](./README.md)
- [Payment Architecture](./puml/payment-architecture.puml)
- [Data Model](./puml/data-model.puml) (updated with booking/ticket entities)
- [Sprint Overview](./sprints/README.md)
