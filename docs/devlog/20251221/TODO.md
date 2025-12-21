# Sprint Implementation TODO

**Date Started:** December 21, 2025

---

## Backend Sprints (core_server_ce)

### Foundation
- [x] **Sprint 0**: Foundation (Docker, Flask factory, DI container, base interfaces) ✅ COMPLETE

### Data & Business Logic
- [ ] **Sprint 1**: Data Layer (Alembic, models, repositories, Redis, optimistic locking)
- [ ] **Sprint 2**: Auth & User Management (JWT, bcrypt, UserService, auth middleware)
- [ ] **Sprint 3**: Subscriptions & Tariff Plans (CurrencyService, TaxService, SubscriptionService)
- [ ] **Sprint 4**: Payments & Plugins (EventDispatcher, payment plugins, idempotency)
- [ ] **Sprint 5**: Admin API & Webhooks (Admin routes, Celery background jobs)

### Testing & Event Handlers
- [ ] **Sprint 10**: Concurrency Testing (Locust, distributed testing, load tests)
- [ ] **Sprint 11**: Event Handlers - User (EventDispatcher, UserStatusUpdateHandler)
- [ ] **Sprint 12**: Event Handlers - Subscriptions (SubscriptionCancelHandler, InvoiceRefundHandler)

---

## Frontend Sprints

### Core SDK (core_view_sdk)
- [ ] Sprints 0-8: Plugin system, API client, auth service, validation, UI components

### User App (core_view_user)
- [ ] Sprints 1-7: Wizard plugin, User Cabinet plugin

### Admin App (core_view_admin)
- [ ] Sprints 1-7: User Management, Plan Management, Analytics plugins

---

## Current Sprint

**Sprint 0: Foundation**

Starting implementation...
