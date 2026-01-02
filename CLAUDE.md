# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vbwd-sdk** - SaaS marketplace platform with subscription billing, user management, and admin dashboard.

- **CE (Community Edition)**: Self-hosted subscription platform (current focus)
- **ME (Marketplace Edition)**: Cloud SaaS marketplace (planned)

**Last Updated:** 2026-01-02
**License:** CC0 1.0 Universal (Public Domain)

## Monorepo Structure

```
vbwd-sdk/
├── vbwd-backend/           # Python/Flask API (292 tests)
├── vbwd-frontend/          # Vue.js applications
│   ├── user/vue/           # User-facing app
│   ├── admin/vue/          # Admin backoffice (71 unit, 108 E2E tests)
│   └── core/               # Shared component library
└── docs/                   # Architecture documentation
    ├── architecture_core_server_ce/      # Backend architecture
    ├── architecture_core_view_admin/     # Admin frontend architecture
    ├── architecture_core_view_component/ # Shared component architecture
    └── devlog/                           # Development logs
```

## Development Commands

### Backend (`vbwd-backend/`)

```bash
make up                  # Start services (API, PostgreSQL, Redis)
make up-build            # Start with rebuild
make down                # Stop services
make test                # Run unit tests
make test-unit           # Unit tests only
make test-integration    # Integration tests (real PostgreSQL)
make test-coverage       # Tests with coverage report
make lint                # Static analysis (black, flake8, mypy)
make pre-commit          # Full check (lint + unit + integration)
make pre-commit-quick    # Quick check (lint + unit)
make shell               # Access API container bash
make logs                # View service logs
```

### Frontend (`vbwd-frontend/`)

```bash
make up                  # Start production containers
make dev                 # Start development mode
make test                # Run unit tests (user + admin)
make test-admin          # Admin unit tests only
make test-user           # User unit tests only
make lint                # Run ESLint for all apps
```

### Admin Frontend (`vbwd-frontend/admin/vue/`)

```bash
npm run dev              # Start dev server (port 5174)
npm run build            # Production build
npm run test             # Unit tests (Vitest)
npm run test:e2e         # E2E tests (Playwright)
npm run test:e2e:ui      # E2E with Playwright UI
npm run lint             # ESLint
```

### Pre-commit Checks (`vbwd-frontend/`)

```bash
./bin/pre-commit-check.sh --admin --unit     # Admin unit tests
./bin/pre-commit-check.sh --admin --e2e      # Admin E2E tests
./bin/pre-commit-check.sh --admin --style    # Lint + TypeScript
```

## Tech Stack

**Backend**: Python 3.11, Flask 3.0, PostgreSQL 16, Redis 7, SQLAlchemy 2.0
**Frontend**: Vue.js 3, Vite, Pinia, Vue Router, TypeScript
**Testing**: Pytest (backend), Vitest (unit), Playwright (E2E)
**Infrastructure**: Docker, Alembic migrations, Gunicorn, Nginx

## Backend Architecture

### Layered Architecture
Routes → Services → Repositories → Models

- **Routes** (`src/routes/`): API endpoints, input validation
- **Services** (`src/services/`): Business logic with dependency injection
- **Repositories** (`src/repositories/`): Data access layer
- **Models** (`src/models/`): SQLAlchemy ORM entities

### Key Patterns
- Dependency injection via `dependency-injector`
- Event-driven architecture for async operations
- SDK adapter pattern for payment providers
- Plugin system for extensibility

### Plugin System (Backend)

Located in `vbwd-backend/src/plugins/`:
```python
from src.plugins.manager import PluginManager
from src.plugins.base import BasePlugin, PluginMetadata

class MyPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="my-plugin", version="1.0.0", ...)

    def on_enable(self): ...
    def on_disable(self): ...

manager = PluginManager(event_dispatcher)
manager.register_plugin(MyPlugin())
manager.initialize_plugin("my-plugin")
manager.enable_plugin("my-plugin")
```

### API Routes
All routes under `/api/v1/`:
- `/auth/` - register, login, logout, refresh
- `/user/` - profile, subscriptions
- `/tarif-plans/` - plan listing
- `/invoices/` - invoice management
- `/admin/` - admin operations (requires admin role)

## Frontend Architecture

### Plugin System (View-Core)

Located in `vbwd-frontend/core/src/plugins/`:
```typescript
import { PluginRegistry, PlatformSDK, IPlugin } from '@vbwd/view-component';

const myPlugin: IPlugin = {
  name: 'my-plugin',
  version: '1.0.0',
  install(sdk) {
    sdk.addRoute({ path: '/my-page', name: 'MyPage', component: () => import('./MyPage.vue') });
    sdk.createStore('myStore', { state: () => ({ count: 0 }) });
  },
  activate() { console.log('Plugin activated'); },
  deactivate() { console.log('Plugin deactivated'); }
};

const registry = new PluginRegistry();
registry.register(myPlugin);
await registry.installAll(sdk);
await registry.activate('my-plugin');
```

**Note:** Admin app currently uses flat structure instead of plugins.

### Admin App Structure
```
admin/vue/
├── src/
│   ├── api/              # API client
│   ├── stores/           # Pinia stores
│   │   ├── auth.ts       # Authentication
│   │   ├── users.ts      # User management
│   │   ├── planAdmin.ts  # Plan management
│   │   ├── subscriptions.ts
│   │   ├── invoices.ts
│   │   ├── webhooks.ts
│   │   └── analytics.ts
│   ├── views/            # Page components
│   │   ├── Dashboard.vue
│   │   ├── Users.vue, UserDetails.vue
│   │   ├── Plans.vue, PlanForm.vue
│   │   ├── Subscriptions.vue, SubscriptionDetails.vue
│   │   ├── Invoices.vue, InvoiceDetails.vue
│   │   ├── Webhooks.vue, WebhookDetails.vue
│   │   ├── Analytics.vue
│   │   └── Settings.vue
│   └── router/           # Vue Router config
└── tests/
    ├── unit/             # Vitest unit tests
    └── e2e/              # Playwright E2E tests
```

## Testing

### Backend
```bash
docker-compose run --rm test pytest tests/unit/ -v
docker-compose run --rm test pytest tests/unit/services/test_auth_service.py -v
```

### Frontend E2E (Playwright)
```bash
cd vbwd-frontend/admin/vue
npx playwright test                    # Run all tests
npx playwright test admin-users        # Run specific spec
npx playwright test --ui               # Interactive UI mode
E2E_BASE_URL=http://localhost:8081 npx playwright test  # Against docker
```

Test credentials:
- Admin: `admin@example.com` / `AdminPass123@`
- User: `test@example.com` / `TestPass123@`

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

## Key Configuration

### Environment Variables (`.env`)
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `JWT_SECRET_KEY` - JWT signing key
- `FLASK_ENV` - development/production

### Nginx Proxy
The frontend nginx proxies `/api/` to the backend:
- User app: port 8080
- Admin app: port 8081
- Backend API: port 5000 (internal)

## Known Issues

1. **E2E Tests in Docker**: Need `E2E_BASE_URL` env var to run against docker container
2. **Architectural Deviations**: Frontend uses flat structure instead of planned plugin architecture
3. **Shared Components**: `@vbwd/view-component` is minimal, apps have duplicate code

## Documentation

- **Backend Architecture**: `docs/architecture_core_server_ce/README.md`
- **Admin Architecture**: `docs/architecture_core_view_admin/README.md`
- **Component Architecture**: `docs/architecture_core_view_component/README.md`
- **Development Logs**: `docs/devlog/YYYYMMDD/`
