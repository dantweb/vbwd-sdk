# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vbwd-sdk** - Dual-purpose platform with two distinct implementations:

1. **Current Implementation**: Medical diagnostic submission platform (LoopAI integration)
2. **Aspirational Architecture**: SaaS marketplace with subscription billing (documented in `docs/architecture_core_server_ce/`)

**Note**: The README.md describes the aspirational SaaS marketplace vision, while the actual codebase implements the medical diagnostic platform. This CLAUDE.md documents what's actually implemented.

License: CC0 1.0 Universal (Public Domain)

## Current Implementation Architecture

### Container Stack
- **frontend**: Vue.js 3 applications (nginx, port 8080)
  - User app: `frontend/user/vue/`
  - Admin app: `frontend/admin/vue/`
- **python**: Python 3.11 / Flask API (port 5000)
- **postgres**: PostgreSQL 16 database (port 5432)
- **python-test**: Test runner (profile: test)

### Key Components
- **Fire-and-forget submission**: Returns 202, processes in background thread via ThreadPoolExecutor
- **LoopAI integration**: External diagnostic API client (`loopai_client.py`)
- **WebSocket notifications**: Real-time status updates via flask-socketio
- **Email service**: Results delivery via SMTP

## Development Commands

### Using Make (recommended)
```bash
# Start all services
make up

# Start with rebuild
make up-build

# Stop services
make down

# Build containers
make build

# Run all tests
make test

# Run Python tests only
make test-python

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run with coverage report
make test-coverage

# View logs (all services)
make logs

# View specific service logs
make logs-python
make logs-frontend

# Shell access
make shell-python
make shell-frontend

# Clean up (removes volumes and logs)
make clean
```

**Note**: The Makefile currently references `mysql` in some targets (logs-mysql, shell-mysql, health check, clean) but the actual database is PostgreSQL. Use `postgres` service name with docker-compose directly:

```bash
# PostgreSQL shell access
docker-compose exec postgres psql -U vbwd -d vbwd

# View PostgreSQL logs
docker-compose logs -f postgres

# Health check (backend -> database)
docker-compose exec python python -c "from sqlalchemy import create_engine; e=create_engine('postgresql://vbwd:vbwd@postgres:5432/vbwd'); c=e.connect(); print('Database: OK'); c.close()"
```

### Using docker-compose directly
```bash
# Start services
docker-compose up -d

# Run tests
docker-compose run --rm python-test

# Run specific pytest command
docker-compose run --rm python-test pytest tests/unit/test_validator_service.py -v

# Run single test
docker-compose run --rm python-test pytest tests/unit/test_validator_service.py::TestValidatorService::test_validate_email -v

# Shell access to services
docker-compose exec python bash
docker-compose exec postgres psql -U vbwd -d vbwd
```

## Project Structure

```
python/api/
  src/
    routes/          # API endpoints
      user.py        # /submit, /status/<id>
      admin.py       # Admin operations
      websocket.py   # WebSocket events
      health.py      # Health check
    models/
      submission.py  # Submission data model
      admin_user.py  # Admin user model
    services/
      submission_service.py   # Business logic
      validator_service.py    # Input validation
      loopai_client.py        # External API client
      email_service.py        # Email delivery
      auth_service.py         # Authentication
  tests/
    unit/            # Unit tests
    integration/     # Integration tests
    fixtures/        # Test fixtures
    conftest.py      # Pytest configuration
  requirements.txt
  gunicorn.conf.py

frontend/
  user/vue/          # User-facing Vue.js app
  admin/vue/         # Admin backoffice Vue.js app

container/           # Dockerfiles per service
  python/
    Dockerfile       # Production Python image
    Dockerfile.test  # Test runner image
  frontend/
    Dockerfile
    nginx.conf
  mysql/             # Note: Contains MySQL but postgres is used
```

## API Workflow

### Submission Flow
1. User submits form to `/submit` (POST)
2. Validates synchronously (email, consent, images)
3. Creates `Submission` record in DB (status: pending)
4. Returns 202 immediately with submission_id
5. Background thread (ThreadPoolExecutor):
   - Calls LoopAI API with images
   - Updates submission status
   - Sends email with results
   - Emits WebSocket event

### Admin Flow
- Admin can view all submissions
- Admin can see full details including results
- Authentication via auth_service

## Database Schema

### Submission Model
```python
class Submission:
    id (Integer, PK)
    email (String(255), indexed)
    status (Enum: pending, processing, completed, failed)
    images_data (JSON)
    comments (Text)
    consent_given (Boolean)
    consent_timestamp (DateTime)
    result (JSON)
    error (Text)
    loopai_execution_id (String(255))
    created_at (DateTime, indexed)
    updated_at (DateTime)
```

## Testing Strategy

All tests run in Docker containers via `python-test` service (profile: test):

```bash
# Run all tests with coverage
make test-coverage

# Run specific test file
docker-compose run --rm python-test pytest tests/unit/test_validator_service.py -v

# Run specific test
docker-compose run --rm python-test pytest tests/unit/test_validator_service.py::TestValidatorService::test_validate_email -v
```

Tests follow TDD principles with separation of unit and integration tests.

## Environment Configuration

Copy `.env.example` to `.env` and configure:

### Database
- `POSTGRES_PASSWORD`: PostgreSQL password (default: vbwd)
- `POSTGRES_DB`: Database name (default: vbwd)
- `POSTGRES_USER`: Database user (default: vbwd)

### Flask
- `FLASK_ENV`: Environment (development/production)
- `FLASK_SECRET_KEY`: Session encryption key (change in production)

### LoopAI Integration
- `LOOPAI_API_URL`: External diagnostic API endpoint (default: http://loopai-web:5000)
- `LOOPAI_API_KEY`: API authentication key
- `LOOPAI_AGENT_ID`: Agent identifier (default: 1)

### Email
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP port (default: 587)
- `SMTP_USER`: SMTP username
- `SMTP_PASSWORD`: SMTP password

## Key Design Patterns

- **Fire-and-forget**: Immediate 202 response with background processing via ThreadPoolExecutor
- **Dependency Injection**: Services injected into routes
- **Service Layer**: Business logic separated from routes
- **Background Execution**: ThreadPoolExecutor for non-blocking operations
- **WebSocket**: Real-time updates for submission status via flask-socketio

## Common Issues

### Database Mismatch
The Makefile contains outdated MySQL references but the actual database is PostgreSQL:
- Use `postgres` instead of `mysql` in docker-compose commands
- Database URL format: `postgresql://vbwd:vbwd@postgres:5432/vbwd`
- Shell access: `docker-compose exec postgres psql -U vbwd -d vbwd`

### Health Check
If services can't communicate:
```bash
# Frontend → Backend connectivity
docker-compose exec frontend curl -s http://python:5000/health

# Backend → Database connectivity
docker-compose exec python python -c "from sqlalchemy import create_engine; e=create_engine('postgresql://vbwd:vbwd@postgres:5432/vbwd'); c=e.connect(); print('Database: OK'); c.close()"
```

### Database Connection
If PostgreSQL connection fails, ensure:
1. PostgreSQL service is healthy: `docker-compose ps`
2. Credentials in `.env` match `docker-compose.yaml`
3. Wait for PostgreSQL healthcheck to pass (uses `pg_isready`)
4. Database URL uses correct driver: `postgresql://` (not `mysql://`)

## Documentation Structure

- **Current Implementation**: This CLAUDE.md
- **Aspirational SaaS Platform**: `docs/architecture_core_server_ce/README.md`
- **Development logs**: `docs/devlog/YYYYMMDD/`
- **README.md**: Describes aspirational vision (not current state)

The architecture docs in `docs/architecture_core_server_ce/` contain detailed planning for a future SaaS marketplace with subscription billing, payment processing, booking systems, and multi-tenant architecture. This represents the planned evolution of the platform but is not yet implemented.
