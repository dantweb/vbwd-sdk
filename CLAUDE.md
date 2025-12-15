# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vbwd-sdk** - Express Medical Diagnostics Platform

Dockerized iframed web application for express diagnostics in medical fields (dermatology, etc.). Users submit images via multi-step form, backend validates and forwards to diagnostic API, results delivered via email.

License: CC0 1.0 Universal (Public Domain)

## Architecture

### Container Stack
- **frontend**: Vue.js 3 (two apps: `frontend/user/vue/` and `frontend/admin/vue/`)
- **python**: Python 3 / Flask API
- **mysql**: MySQL database

### Directory Structure
```
container/           # Docker configs per container
data/                # Logs and persistent data
  python/logs/
  frontend/logs/
  mysql/             # Binary data
python/api/          # Flask backend
  requirements.txt
  src/routes/        # API route handlers
  src/models/        # Data models
  src/services/      # Business logic
  tests/unit/
  tests/integration/
  tests/fixtures/
frontend/
  admin/vue/         # Admin backoffice (Vue.js)
  user/vue/          # User-facing app (Vue.js)
docs/
  architecture/      # System architecture docs
  devlog/            # Daily development logs (YYYYMMDD/)
```

## Development Commands

```bash
# Run all containers
docker-compose up

# Run tests (always in containers)
docker-compose run --rm python pytest
docker-compose run --rm frontend npm test

# Build
docker-compose build
```

## Development Principles

- **TDD First**: Write tests before implementation
- **SOLID**: All principles strictly enforced
- **LSP**: Liskov Substitution Principle
- **DI**: Dependency Injection throughout
- **Clean Code**: Readable, maintainable, self-documenting
- **Dockerized Tests**: All tests run in containers

## Documentation

- Full architecture: `docs/architecture/README.md`
- Dev logs: `docs/devlog/YYYYMMDD/README.md`
