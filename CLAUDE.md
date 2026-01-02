# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vbwd-sdk** - SaaS marketplace platform enabling vendors to connect their products with complete CRM, billing, and subscription infrastructure.

- **CE (Community Edition)**: Self-hosted subscription platform
- **ME (Marketplace Edition)**: Cloud SaaS marketplace (planned)

License: CC0 1.0 Universal (Public Domain)

## Monorepo Structure

```
vbwd-sdk/
├── vbwd-backend/      # Python/Flask API
├── vbwd-frontend/     # Vue.js applications
│   ├── user/          # User-facing app
│   ├── admin/         # Admin backoffice
│   └── core/          # Shared component library
└── docs/              # Architecture documentation
```

## Development Commands

### Backend (`vbwd-backend/`)

```bash
make up                  # Start services (API, PostgreSQL, Redis)
make up-build            # Start with rebuild
make down                # Stop services
make test                # Run unit tests (SQLite in-memory)
make test-unit           # Unit tests only
make test-integration    # Integration tests (real PostgreSQL)
make test-coverage       # Tests with coverage report
make lint                # Static analysis (black, flake8, mypy)
make pre-commit          # Full check (lint + unit + integration)
make pre-commit-quick    # Quick check (lint + unit)
make shell               # Access API container bash
make logs                # View service logs
```

Running a specific test:
```bash
docker-compose run --rm test pytest tests/unit/services/test_auth_service.py -v
docker-compose run --rm test pytest tests/unit/services/test_auth_service.py::TestAuthService::test_login -v
```

### Frontend (`vbwd-frontend/`)

```bash
make dev                 # Start development mode (hot reload)
make up                  # Start production containers
make test                # Run unit tests (user + admin)
make lint                # Run ESLint
make test-e2e            # Run Playwright E2E tests
make test-e2e-ui         # E2E with Playwright UI
make test-e2e-headed     # E2E in visible browser
make test-e2e-file FILE=auth.spec.ts  # Specific E2E test
make playwright-install  # Install Playwright browsers
```

### Root Level

```bash
make up                  # Start all containers (backend + frontend)
make down                # Stop all services
make ps                  # Show status of all containers
```

## Tech Stack

**Backend**: Python 3.11, Flask 3.0, PostgreSQL 16, Redis 7, SQLAlchemy 2.0
**Frontend**: Vue.js 3, Vite, Pinia, Vue Router, Playwright (E2E)
**Infrastructure**: Docker, Alembic migrations, Gunicorn

## Backend Architecture

### Layered Architecture
Routes → Services → Repositories → Models

- **Routes** (`src/routes/`): API endpoints, input validation
- **Services** (`src/services/`): Business logic with dependency injection
- **Repositories** (`src/repositories/`): Data access layer
- **Models** (`src/models/`): SQLAlchemy ORM entities

### Dependency Injection
All dependencies wired through `src/container.py` using `dependency-injector`. Services and repositories are injected per-request.

### Event-Driven System
Domain events (`src/events/`) dispatched to handlers (`src/handlers/`):
- `UserCreatedEvent`, `SubscriptionCreatedEvent`, `PaymentProcessedEvent`
- Handlers perform async operations like sending emails, webhooks

### SDK Adapter Pattern
Pluggable payment providers via `src/sdk/`:
- `SDKInterface` - abstract payment interface
- `SDKRegistry` - register/retrieve adapters
- `MockAdapter` - testing adapter

### API Routes
All routes under `/api/v1/`:
- `/auth/` - register, login, logout, refresh
- `/user/` - profile, subscriptions
- `/tarif-plans/` - plan listing
- `/invoices/` - invoice management
- `/admin/` - admin operations

## Testing Strategy

### Unit Tests (fast, SQLite in-memory)
```bash
docker-compose run --rm test pytest tests/unit/ -v
```

### Integration Tests (real PostgreSQL, HTTP API)
```bash
docker-compose --profile test-integration run --rm test-integration pytest tests/integration/ -v
```

### E2E Tests (Playwright)
```bash
cd vbwd-frontend && make test-e2e
```

Test credentials (seeded):
- User: `test@example.com` / `TestPass123@`
- Admin: `admin@example.com` / `AdminPass123@`

## Database

PostgreSQL 16 with Alembic migrations.

```bash
# Run migrations
docker-compose exec api flask db upgrade

# Create migration
docker-compose exec api flask db migrate -m "description"

# Access database
docker-compose exec postgres psql -U vbwd -d vbwd
```

## Pre-Commit Quality Checks

The backend includes `bin/pre-commit-check.sh`:
- Phase A: Black formatting, Flake8 style, MyPy types
- Phase B: Unit tests
- Phase C: Integration tests

```bash
./bin/pre-commit-check.sh          # Full check
./bin/pre-commit-check.sh --quick  # Skip integration
./bin/pre-commit-check.sh --lint   # Only static analysis
```

## Key Files

| File | Purpose |
|------|---------|
| `vbwd-backend/src/app.py` | Flask app factory |
| `vbwd-backend/src/container.py` | DI container |
| `vbwd-backend/src/config.py` | Configuration |
| `vbwd-backend/docker-compose.yaml` | Backend services |
| `vbwd-frontend/docker-compose.yaml` | Frontend services |

## Environment Variables

Copy `.env.example` to `.env` in `vbwd-backend/`:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `JWT_SECRET_KEY` - JWT signing key
- `SMTP_*` - Email configuration
- `TEST_DATA_SEED` / `TEST_DATA_CLEANUP` - Test data management
