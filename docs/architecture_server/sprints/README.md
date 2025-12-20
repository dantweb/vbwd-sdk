# VBWD-SDK Backend Sprints

**Component:** Python Flask API Backend
**Methodology:** TDD-First, SOLID, Clean Code
**Runtime:** Dockerized

---

## Overview

This document outlines the implementation sprints for the Python Flask API backend. Each sprint follows strict TDD methodology with SOLID principles enforcement.

## Development Principles

### TDD-First Workflow

```
1. Write failing test (RED)
2. Write minimal code to pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)
4. Repeat
```

### SOLID Principles

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Each class/module has one reason to change |
| **O** - Open/Closed | Open for extension, closed for modification |
| **L** - Liskov Substitution | Subtypes must be substitutable for base types |
| **I** - Interface Segregation | Many specific interfaces over one general |
| **D** - Dependency Inversion | Depend on abstractions, not concretions |

### Dependency Injection Pattern

```python
# BAD: Hard dependency
class UserService:
    def __init__(self):
        self.repo = UserRepository()  # Tight coupling

# GOOD: Injected dependency
class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.repo = user_repo  # Loose coupling, testable
```

### Interface Segregation Example

```python
# BAD: Fat interface
class IRepository(ABC):
    def find_by_id(self, id): ...
    def find_all(self): ...
    def save(self, entity): ...
    def delete(self, id): ...
    def find_by_email(self, email): ...  # User-specific
    def find_active(self): ...  # Subscription-specific

# GOOD: Segregated interfaces
class IReadRepository(ABC):
    def find_by_id(self, id): ...
    def find_all(self): ...

class IWriteRepository(ABC):
    def save(self, entity): ...
    def delete(self, id): ...

class IUserRepository(IReadRepository, IWriteRepository):
    def find_by_email(self, email): ...
```

### Liskov Substitution Principle

```python
# All implementations must honor the contract
class IPaymentGateway(ABC):
    @abstractmethod
    def create_checkout(self, amount: Decimal, currency: str) -> CheckoutSession:
        """Must return CheckoutSession or raise PaymentError"""
        pass

# PayPalGateway and StripeGateway both honor this contract
# Code using IPaymentGateway works with either implementation
```

---

## Sprint Overview

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| 0 | Foundation | Docker, CI, project structure, base classes |
| 1 | Data Layer | Models, repositories, database migrations |
| 2 | Auth & Users | Registration, login, JWT, user management |
| 3 | Subscriptions | Tariff plans, subscription lifecycle |
| 4 | Payments | Invoice, PayPal/Stripe integration |
| 5 | Admin & Webhooks | Admin API, webhook handlers |
| 6 | Booking Models | Room, Timeslot, Booking models & services |
| 7 | Booking API | User and admin booking endpoints |
| 8 | Ticket Models | Event, Ticket, TicketScan models & services |
| 9 | Ticket API | Event browsing, ticket management, scanner |

---

## Docker Commands

```bash
# Run all tests
docker-compose run --rm python pytest

# Run with coverage
docker-compose run --rm python pytest --cov=src --cov-report=html

# Run specific test file
docker-compose run --rm python pytest tests/unit/test_user_service.py

# Run tests with verbose output
docker-compose run --rm python pytest -v

# Run only unit tests
docker-compose run --rm python pytest tests/unit/

# Run only integration tests
docker-compose run --rm python pytest tests/integration/

# Lint code
docker-compose run --rm python flake8 src/

# Type checking
docker-compose run --rm python mypy src/
```

---

## Directory Structure (Target)

```
python/api/
├── requirements.txt
├── pytest.ini
├── src/
│   ├── __init__.py
│   ├── app.py                    # Flask app factory
│   ├── config.py                 # Configuration
│   ├── container.py              # DI container
│   │
│   ├── interfaces/               # Abstract interfaces (ISP)
│   │   ├── __init__.py
│   │   ├── repositories.py       # IRepository interfaces
│   │   ├── services.py           # IService interfaces
│   │   └── gateways.py           # External gateway interfaces
│   │
│   ├── models/                   # Domain entities
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── user_details.py
│   │   ├── user_case.py
│   │   ├── tarif_plan.py
│   │   ├── subscription.py
│   │   └── user_invoice.py
│   │
│   ├── repositories/             # Data access (implements interfaces)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_repository.py
│   │   ├── tarif_plan_repository.py
│   │   ├── subscription_repository.py
│   │   └── invoice_repository.py
│   │
│   ├── services/                 # Business logic (implements interfaces)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── subscription_service.py
│   │   ├── invoice_service.py
│   │   └── payment_service.py
│   │
│   ├── gateways/                 # External integrations
│   │   ├── __init__.py
│   │   ├── paypal_gateway.py
│   │   ├── stripe_gateway.py
│   │   └── email_gateway.py
│   │
│   ├── routes/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── tarif_plans.py
│   │   ├── checkout.py
│   │   ├── admin.py
│   │   └── webhooks.py
│   │
│   ├── middleware/               # Request middleware
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── rate_limit.py
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── validators.py
│       └── exceptions.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py               # Pytest fixtures
    │
    ├── unit/                     # Unit tests (mocked dependencies)
    │   ├── __init__.py
    │   ├── services/
    │   │   ├── test_auth_service.py
    │   │   ├── test_user_service.py
    │   │   ├── test_subscription_service.py
    │   │   └── test_payment_service.py
    │   ├── repositories/
    │   │   └── test_user_repository.py
    │   └── models/
    │       └── test_user.py
    │
    ├── integration/              # Integration tests (real DB)
    │   ├── __init__.py
    │   ├── test_auth_flow.py
    │   ├── test_subscription_flow.py
    │   └── test_payment_flow.py
    │
    └── fixtures/                 # Test data
        ├── __init__.py
        ├── users.py
        ├── tarif_plans.py
        └── invoices.py
```

---

## Sprint Documents

### Core Platform
- [Sprint 0: Foundation](./sprint-0-foundation.md)
- [Sprint 1: Data Layer](./sprint-1-data-layer.md)
- [Sprint 2: Auth & Users](./sprint-2-auth-users.md)
- [Sprint 3: Subscriptions](./sprint-3-subscriptions.md)
- [Sprint 4: Payments](./sprint-4-payments.md)
- [Sprint 5: Admin & Webhooks](./sprint-5-admin-webhooks.md)

### Booking System
- [Sprint 6: Booking Models & Services](./sprint-6-booking-models.md)
- [Sprint 7: Booking API Routes](./sprint-7-booking-api.md)

### Ticket System
- [Sprint 8: Ticket Models & Services](./sprint-8-ticket-models.md)
- [Sprint 9: Ticket API Routes](./sprint-9-ticket-api.md)

### Related PlantUML Diagrams
- [Booking Data Model](../puml/booking-data-model.puml)
- [Booking Flow](../puml/booking-flow.puml)
- [Booking Lifecycle](../puml/booking-lifecycle.puml)
- [Ticket Data Model](../puml/ticket-data-model.puml)
- [Ticket Flow](../puml/ticket-flow.puml)
- [Ticket Lifecycle](../puml/ticket-lifecycle.puml)

---

## Definition of Done

Each sprint item is considered "Done" when:

1. All tests pass (unit + integration)
2. Code coverage >= 80%
3. No linting errors (flake8)
4. Type hints present (mypy passes)
5. Docstrings for public methods
6. Code reviewed
7. Runs successfully in Docker
