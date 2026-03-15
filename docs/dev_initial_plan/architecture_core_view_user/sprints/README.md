# Frontend Architecture Sprints

**Project:** VBWD-SDK Frontend - Plugin-Based Vue.js 3 Platform
**Methodology:** TDD, SOLID, MVP, Clean Code
**Status:** Planning Phase

---

## Overview

This document provides an overview of the frontend development sprints. Each sprint follows Test-Driven Development (TDD) principles with Playwright E2E tests and Vitest unit tests.

---

## Sprint Sequence

### [Sprint 0: Foundation](./sprint-0-foundation.md)
**Duration:** 1-2 weeks
**Goal:** Establish project structure, plugin system core, and testing infrastructure

**Key Deliverables:**
- ✅ Vite + TypeScript + Vue.js 3 setup
- ✅ Plugin system core (IPlugin, PluginRegistry)
- ✅ Tailwind CSS configuration
- ✅ Vitest + Playwright setup
- ✅ ESLint + Prettier configuration
- ✅ Platform SDK stub

**Dependencies:** None

---

### [Sprint 1: API Client SDK & Authentication](./sprint-1-api-client-auth.md)
**Duration:** 2 weeks
**Goal:** Build type-safe API client and authentication service

**Key Deliverables:**
- ✅ Type-safe API client with all backend endpoints
- ✅ Axios interceptors for token management
- ✅ Authentication service (login, register, logout)
- ✅ Event bus for plugin communication
- ✅ Validation service with Zod
- ✅ Platform SDK with real services

**Dependencies:** Sprint 0

**Backend Requirements:**
- `/api/v1/auth/login` endpoint
- `/api/v1/auth/register` endpoint
- `/api/v1/auth/refresh` endpoint
- JWT token authentication

---

### [Sprint 2: Wizard Plugin - File Upload & Validation](./sprint-2-wizard-plugin.md)
**Duration:** 2 weeks
**Goal:** Build first plugin with multi-step wizard

**Key Deliverables:**
- ✅ Wizard plugin (implements IPlugin)
- ✅ Step 1: File upload with drag & drop
- ✅ Step 2: Email input + GDPR consent
- ✅ Zod validation schemas
- ✅ Wizard state management (Pinia)
- ✅ Playwright E2E test for wizard flow

**Dependencies:** Sprint 0, Sprint 1

**Backend Requirements:**
- File validation endpoint (optional)
- Email validation endpoint (optional)

---

### [Sprint 3: Tariff Plans & Checkout](./sprint-3-tariff-checkout.md)
**Duration:** 2 weeks
**Goal:** Extend wizard with plan selection and checkout

**Key Deliverables:**
- ✅ Step 3: Tariff plan display and selection
- ✅ Step 4: Checkout form with billing details
- ✅ Payment method selection (PayPal/Stripe)
- ✅ Integration with checkout API
- ✅ Payment provider redirect
- ✅ E2E test for complete checkout flow

**Dependencies:** Sprint 2

**Backend Requirements:**
- `/api/v1/tarif-plans` endpoint
- `/api/v1/checkout/create` endpoint
- PayPal/Stripe webhook handling

---

### [Sprint 4: User Cabinet & Subscription Management](./sprint-4-user-cabinet.md)
**Duration:** 2 weeks
**Goal:** Build user cabinet plugin for account management

**Key Deliverables:**
- ✅ User Cabinet plugin (implements IPlugin)
- ✅ Protected routes with auth guard
- ✅ Profile management (name, address, password)
- ✅ Subscription viewing and management
- ✅ Invoice list and download
- ✅ E2E tests for cabinet features

**Dependencies:** Sprint 1, Sprint 3

**Backend Requirements:**
- `/api/v1/user/profile` endpoints
- `/api/v1/user/details` endpoints
- `/api/v1/user/subscriptions` endpoint
- `/api/v1/user/invoices` endpoint

---

### [Sprint 5: Access Control & E2E Tests](./sprint-5-access-control-e2e.md)
**Duration:** 2 weeks
**Goal:** Implement access control and comprehensive testing

**Key Deliverables:**
- ✅ Tariff-based access control system
- ✅ Route guards for plan-restricted pages
- ✅ Component-level permission directive
- ✅ Upgrade prompt components
- ✅ Comprehensive E2E test suite (90%+ coverage)
- ✅ Accessibility testing (WCAG 2.1 AA)
- ✅ Performance benchmarks
- ✅ CI/CD pipeline

**Dependencies:** Sprint 4

**Backend Requirements:**
- User subscription status checking
- Permission/role checking

---

## Development Principles

### TDD (Test-Driven Development)
1. Write E2E test first (Playwright)
2. Write unit tests (Vitest)
3. Implement feature to pass tests
4. Refactor while keeping tests green

### SOLID Principles
- **Single Responsibility:** Each plugin, component, and service has one job
- **Open/Closed:** Extend via plugins without modifying core
- **Liskov Substitution:** All plugins implement IPlugin interface
- **Interface Segregation:** Small, focused interfaces (IApiClient, IAuthService)
- **Dependency Inversion:** Depend on abstractions, inject via SDK

### Clean Code
- TypeScript strict mode enabled
- ESLint + Prettier for consistent formatting
- Meaningful names for variables, functions, and components
- Small, focused functions (< 20 lines)
- DRY (Don't Repeat Yourself)
- Comments explain "why", not "what"

---

## Testing Strategy

### Unit Tests (Vitest)
- **Coverage Target:** 90%+
- **Scope:** Stores, composables, utilities, services
- **Run:** `npm run test:unit`

### E2E Tests (Playwright)
- **Coverage Target:** All critical user flows
- **Scope:** Complete user journeys, cross-page workflows
- **Browsers:** Chromium, Firefox, WebKit
- **Run:** `npm run test:e2e`

### Accessibility Tests
- **Standard:** WCAG 2.1 AA
- **Tools:** Playwright accessibility checks, axe-core
- **Run:** `npm run test:e2e` (included)

### Performance Tests
- **Targets:**
  - Page load < 2s
  - API calls < 1s
  - Interaction response < 100ms
- **Tools:** Playwright performance metrics

---

## Technology Stack Summary

| Category           | Technology          | Version  |
|--------------------|---------------------|----------|
| Framework          | Vue.js             | 3.4+     |
| Language           | TypeScript         | 5.x      |
| Build Tool         | Vite               | 5.x      |
| Routing            | Vue Router         | 4.x      |
| State Management   | Pinia              | 2.x      |
| HTTP Client        | Axios              | 1.x      |
| Validation         | Zod                | 3.x      |
| Styling            | Tailwind CSS       | 3.x      |
| E2E Testing        | Playwright         | Latest   |
| Unit Testing       | Vitest             | Latest   |

---

## Getting Started

### Prerequisites
- Node.js 20+
- npm 10+
- Docker (for full stack testing)

### Initial Setup

```bash
# Navigate to frontend directory
cd frontend/user/vue

# Install dependencies
npm install

# Run development server
npm run dev

# Run unit tests
npm run test:unit

# Run E2E tests
npm run test:e2e

# Run all tests
npm test

# Build for production
npm run build
```

---

## Sprint Progress Tracking

| Sprint | Status | Start Date | End Date | Notes |
|--------|--------|------------|----------|-------|
| 0      | 📋 Planned | TBD | TBD | Foundation |
| 1      | 📋 Planned | TBD | TBD | API & Auth |
| 2      | 📋 Planned | TBD | TBD | Wizard Plugin |
| 3      | 📋 Planned | TBD | TBD | Checkout |
| 4      | 📋 Planned | TBD | TBD | User Cabinet |
| 5      | 📋 Planned | TBD | TBD | Access Control |

**Legend:**
- 📋 Planned
- 🏗️ In Progress
- ✅ Complete
- ⏸️ On Hold
- ❌ Cancelled

---

## Related Documentation

- [Frontend Architecture Overview](../README.md)
- [Server Architecture](../../architecture_server/README.md)
- [Plugin Development Guide](../plugin-development.md) *(to be created)*
- [API Documentation](../../api/README.md) *(to be created)*

---

## Questions & Support

For questions about frontend architecture or sprint planning:
1. Review the main [Frontend Architecture README](../README.md)
2. Check individual sprint documents
3. Review [Server Architecture](../../architecture_server/README.md) for API contracts
4. Consult [CLAUDE.md](../../../CLAUDE.md) for development guidance
