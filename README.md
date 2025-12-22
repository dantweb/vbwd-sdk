# VBWD SDK

**The ViBe coding We have Deserved**

A comprehensive SaaS marketplace platform enabling vendors to connect their products without building CRM and billing infrastructure from scratch.

---

## Repositories

The VBWD platform is split into three repositories:

| Repository | Description | Status | Link |
|------------|-------------|--------|------|
| **vbwd-sdk** | Documentation & Architecture | Active | [github.com/dantweb/vbwd-sdk](https://github.com/dantweb/vbwd-sdk) |
| **vbwd-backend** | Python/Flask API | 292 tests | [github.com/dantweb/vbwd-backend](https://github.com/dantweb/vbwd-backend) |
| **vbwd-frontend** | Vue.js Applications | Active | [github.com/dantweb/vbwd-frontend](https://github.com/dantweb/vbwd-frontend) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        VBWD Platform                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────────────────┐   │
│  │  vbwd-frontend  │         │       vbwd-backend          │   │
│  │                 │  HTTP   │                             │   │
│  │  - User App     │◄───────►│  - Flask API                │   │
│  │  - Admin App    │         │  - PostgreSQL               │   │
│  │                 │         │  - Redis                    │   │
│  │  Vue.js 3       │         │  - Payment SDK              │   │
│  │  Vite           │         │  - Webhook System           │   │
│  └─────────────────┘         └─────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Description

VBWD is a dual-edition platform designed to revolutionize how SaaS products are built and distributed:

- **CE (Community Edition)** - Self-hosted subscription and billing platform for individual companies
- **ME (Marketplace Edition)** - Cloud SaaS marketplace where vendors connect their products and instantly get complete CRM + billing infrastructure

The platform provides turnkey solutions for:
- User management and CRM
- Subscription billing and payment processing
- Booking and appointment scheduling
- Event ticketing with QR validation
- Multi-tenant architecture
- Plugin-based extensibility

---

## Tech Stack

### Backend ([vbwd-backend](https://github.com/dantweb/vbwd-backend))
- Python 3.11 / Flask 3.0
- PostgreSQL 16
- Redis 7
- SQLAlchemy 2.0
- Event-driven architecture
- SDK adapter pattern for payments

### Frontend ([vbwd-frontend](https://github.com/dantweb/vbwd-frontend))
- Vue.js 3
- Vite
- Pinia state management
- Vue Router

---

## Documentation

This repository contains all architecture and planning documentation:

- **Architecture**: `docs/architecture_core_server_ce/`
- **Development Logs**: `docs/devlog/`
- **Future Ideas**: `future_implementation_ideas/`

---

## Development Status

### Backend Progress (292 tests)
- ✅ Sprint 0-4: Foundation, Data Layer, Auth, Subscriptions, Plugin System
- ✅ Sprint 11-15: Event System, SDK Adapters, Webhooks
- ✅ Sprint 18: Payment Events & Handlers
- ⏳ Stripe/PayPal plugins (planned)

### Frontend Progress
- ✅ User App scaffold
- ✅ Admin App scaffold
- ⏳ Component development

---

## Quick Start

### Backend
```bash
git clone https://github.com/dantweb/vbwd-backend.git
cd vbwd-backend
cp .env.example .env
make up
make test
```

### Frontend
```bash
git clone https://github.com/dantweb/vbwd-frontend.git
cd vbwd-frontend
make dev
```

---

## Contributing

This project follows strict development principles:
- **TDD First**: Write tests before implementation
- **SOLID Principles**: Clean, maintainable, extensible code
- **Dependency Injection**: Loose coupling throughout
- **Dockerized Testing**: All tests run in containers

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

---

## License

**CC0-1.0 Universal (Public Domain)**

This project is dedicated to the public domain. You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.

---

**Built with care for the SaaS community**
