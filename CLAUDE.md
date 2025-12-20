# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vbwd-sdk** - Medical Diagnostic Submission Platform

Dockerized web application for submitting medical diagnostic requests (dermatology, etc.). Users submit images via multi-step form, backend validates and forwards to LoopAI diagnostic API, results delivered via email and WebSocket.

License: CC0 1.0 Universal (Public Domain)

## Architecture

### Container Stack
- **frontend**: Vue.js 3 applications (nginx)
  - User app: `frontend/user/vue/`
  - Admin app: `frontend/admin/vue/`
- **python**: Python 3.11 / Flask API (port 5000)
- **mysql**: MySQL 8.0 database

### Key Components
- **Fire-and-forget submission**: Returns 202, processes in background thread
- **LoopAI integration**: External diagnostic API client (`loopai_client.py`)
- **WebSocket notifications**: Real-time status updates via flask-socketio
- **Email service**: Results delivery via email

## Development Commands

### Using Make (recommended)
```bash
# Start all services
make up

# Start with rebuild
make up-build

# Stop services
make down

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
make logs-mysql

# Shell access
make shell-python
make shell-frontend
make shell-mysql

# Health check (verify inter-container connectivity)
make health

# Clean up (removes volumes and logs)
make clean
```

### Using docker-compose directly
```bash
# Start services
docker-compose up -d

# Run tests
docker-compose run --rm python-test
docker-compose run --rm frontend npm test

# Run specific pytest command
docker-compose run --rm python-test pytest tests/unit/test_validator_service.py -v

# Run single test
docker-compose run --rm python-test pytest tests/unit/test_validator_service.py::TestValidatorService::test_validate_email -v
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

frontend/
  user/vue/          # User-facing Vue.js app
  admin/vue/         # Admin backoffice Vue.js app

container/           # Dockerfiles per service
  python/
    Dockerfile       # Production Python image
    Dockerfile.test  # Test runner image
  frontend/
  mysql/
```

## API Workflow

### Submission Flow
1. User submits form to `/submit` (POST)
2. Validates synchronously (email, consent, images)
3. Creates `Submission` record in DB (status: pending)
4. Returns 202 immediately
5. Background thread:
   - Calls LoopAI API with images
   - Updates submission status
   - Sends email with results
   - Emits WebSocket event

### Admin Flow
- Admin can view all submissions
- Admin can see full details including results

## Testing Strategy

All tests run in Docker containers via `python-test` service:

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

- `FLASK_SECRET_KEY`: Session encryption key
- `LOOPAI_API_URL`: External diagnostic API endpoint (default: http://loopai-web:5000)
- `LOOPAI_API_KEY`: API authentication key
- `MYSQL_ROOT_PASSWORD`: MySQL root password
- `MYSQL_DATABASE`: Database name (default: vbwd)
- `MYSQL_USER`: Database user (default: vbwd)
- `MYSQL_PASSWORD`: Database password (default: vbwd)

## Key Design Patterns

- **Fire-and-forget**: Immediate response with background processing
- **Dependency Injection**: Services injected into routes
- **Service Layer**: Business logic separated from routes
- **Background Execution**: ThreadPoolExecutor for non-blocking operations
- **WebSocket**: Real-time updates for submission status

## Common Issues

### Health Check
If services can't communicate, run:
```bash
make health
```

This verifies:
- Frontend → Backend connectivity
- Backend → Database connectivity

### Database Connection
If MySQL connection fails, ensure:
1. MySQL service is healthy: `docker-compose ps`
2. Credentials in `.env` match `docker-compose.yaml`
3. Wait for MySQL healthcheck to pass (10s intervals)

## Documentation

- Architecture overview: `docs/architecture/README.md` (NOTE: Contains aspirational SaaS design, not current implementation)
- Development logs: `docs/devlog/YYYYMMDD/`