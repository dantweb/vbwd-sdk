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

## Development Commands

```bash
# From root directory
make up              # Start all services
make up-build        # Rebuild and start all services
make rebuild-admin   # Rebuild only admin frontend (fast iteration)
make down            # Stop all services
make ps              # Show status of all containers
make logs            # View backend logs
make clean           # Remove all containers and volumes
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, Flask 3.0, PostgreSQL 16 |
| Frontend | Vue.js 3, Vite, Pinia, TypeScript |
| Testing | Pytest (561), Vitest (251), Playwright (108) |

## Project Structure

```
vbwd-sdk/
├── vbwd-backend/      # Flask API
├── vbwd-frontend/     # Vue.js apps (user, admin, core)
└── docs/              # Architecture documentation
```

## Plugin System

The platform supports runtime plugins for both backend and frontend.

**Backend:** Plugins extend `BasePlugin`, declare Flask blueprints via `get_blueprint()`, and are auto-discovered from `src/plugins/providers/`. Config is persisted to DB (`plugin_config` table) and restored on startup.

**Frontend (Admin):** `PluginRegistry` and `PlatformSDK` initialize in `main.ts`. Plugins implement `IPlugin` from `@vbwd/view-component`, register components/routes via SDK, and are rendered dynamically on the Dashboard.

```bash
# Backend: list plugins
docker compose exec api flask plugins list

# Backend: enable/disable
docker compose exec api flask plugins enable analytics
docker compose exec api flask plugins disable analytics
```

See [CLAUDE.md](CLAUDE.md) for detailed plugin API.

## Documentation

- [Development Guide](CLAUDE.md)
- [Backend Architecture](docs/architecture_core_server_ce/README.md)
- [Admin Architecture](docs/architecture_core_view_admin/README.md)

## License

CC0-1.0 Universal (Public Domain)
