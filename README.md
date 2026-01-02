# VBWD SDK

**SaaS Subscription Platform** - User management, subscription billing, and admin dashboard.

## Quick Start

```bash
# Backend
cd vbwd-backend && make up && make test

# Frontend
cd vbwd-frontend && make up
```

**Admin Panel:** http://localhost:8081
**User App:** http://localhost:8080

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, Flask 3.0, PostgreSQL 16 |
| Frontend | Vue.js 3, Vite, Pinia, TypeScript |
| Testing | Pytest (292), Vitest (71), Playwright (108) |

## Project Structure

```
vbwd-sdk/
├── vbwd-backend/      # Flask API
├── vbwd-frontend/     # Vue.js apps (user, admin, core)
└── docs/              # Architecture documentation
```

## Documentation

- [Development Guide](CLAUDE.md)
- [Backend Architecture](docs/architecture_core_server_ce/README.md)
- [Admin Architecture](docs/architecture_core_view_admin/README.md)

## License

CC0-1.0 Universal (Public Domain)
