# Core SDK Development Sprints

**Project:** VBWD Core SDK (`@vbwd/core-sdk`)
**Methodology:** TDD, SOLID, Clean Code
**Status:** Planning Phase

---

## Overview

The Core SDK is the foundation for both User and Admin applications. It must be developed first before application-specific plugins can be built.

**Critical Path:** Core SDK → User App → Admin App

---

## Sprint Sequence

### [Sprint 0: Core SDK Foundation](./sprint-0-foundation.md)
**Duration:** 1 week
**Goal:** Setup Core SDK project structure and build system

**Key Deliverables:**
- ✅ Core SDK project setup (TypeScript + Vite)
- ✅ Package.json configuration
- ✅ Build pipeline
- ✅ Testing infrastructure (Vitest)
- ✅ Linting and formatting (ESLint + Prettier)
- ✅ CI/CD pipeline

**Dependencies:** None

---

### [Sprint 1: Plugin System Core](./sprint-1-plugin-system.md)
**Duration:** 1 week
**Goal:** Build the plugin architecture foundation

**Key Deliverables:**
- ✅ IPlugin interface (ISP compliant)
- ✅ PluginRegistry with dependency management
- ✅ PluginLoader with lifecycle hooks
- ✅ PlatformSDK interface
- ✅ Unit tests (95%+ coverage)
- ✅ Integration test examples

**Dependencies:** Sprint 0

---

### [Sprint 2: API Client & HTTP Layer](./sprint-2-api-client.md)
**Duration:** 2 weeks
**Goal:** Build type-safe API client with interceptors

**Key Deliverables:**
- ✅ IApiClient interface
- ✅ ApiClient implementation (Axios-based)
- ✅ Request/Response interceptors
- ✅ Token management
- ✅ Error normalization
- ✅ All API type definitions
- ✅ Comprehensive unit tests

**Dependencies:** Sprint 1

---

### [Sprint 3: Authentication Service](./sprint-3-auth-service.md)
**Duration:** 1 week
**Goal:** Build authentication and session management

**Key Deliverables:**
- ✅ IAuthService interface
- ✅ AuthService implementation
- ✅ authStore (Pinia)
- ✅ JWT token management
- ✅ Session persistence
- ✅ Role checking
- ✅ Unit tests

**Dependencies:** Sprint 2

---

### [Sprint 4: Event Bus & Validation](./sprint-4-events-validation.md)
**Duration:** 1 week
**Goal:** Build event bus and validation service

**Key Deliverables:**
- ✅ IEventBus interface
- ✅ EventBus implementation
- ✅ PlatformEvents enum
- ✅ IValidationService interface
- ✅ ValidationService with Zod
- ✅ Common validation schemas
- ✅ Unit tests

**Dependencies:** Sprint 1

---

### [Sprint 5: Shared UI Components](./sprint-5-ui-components.md)
**Duration:** 2 weeks
**Goal:** Build reusable UI component library

**Key Deliverables:**
- ✅ Button, Input, Checkbox, Select components
- ✅ Modal, Dialog components
- ✅ Table component (with sorting, pagination)
- ✅ Form components
- ✅ Loading states
- ✅ Toast notifications
- ✅ Tailwind CSS styling
- ✅ Accessibility (WCAG 2.1 AA)
- ✅ Component tests

**Dependencies:** Sprint 1

---

### [Sprint 6: Composables & Utilities](./sprint-6-composables-utils.md)
**Duration:** 1 week
**Goal:** Build shared composables and utilities

**Key Deliverables:**
- ✅ useApi composable
- ✅ useAuth composable
- ✅ useForm composable
- ✅ useNotification composable
- ✅ Format utilities (date, currency, number)
- ✅ Storage utilities (localStorage wrapper)
- ✅ Unit tests

**Dependencies:** Sprint 2, Sprint 3, Sprint 4

---

### [Sprint 7: Access Control System](./sprint-7-access-control.md)
**Duration:** 1 week
**Goal:** Build tariff-based and role-based access control

**Key Deliverables:**
- ✅ AccessControl service
- ✅ useAccessControl composable
- ✅ v-access directive
- ✅ Route guards (authGuard, planGuard, adminGuard)
- ✅ Permission checking utilities
- ✅ Unit tests

**Dependencies:** Sprint 3

---

### [Sprint 8: Integration & Documentation](./sprint-8-integration-docs.md)
**Duration:** 1 week
**Goal:** Integration testing and comprehensive documentation

**Key Deliverables:**
- ✅ Integration tests (plugin loading, API client, auth flow)
- ✅ API documentation (TypeDoc)
- ✅ Usage examples for all features
- ✅ Migration guide (symlink → npm package)
- ✅ Troubleshooting guide
- ✅ Performance benchmarks

**Dependencies:** All previous sprints

---

## Development Principles

### TDD (Test-Driven Development)
1. Write interface/types first
2. Write unit tests
3. Implement feature
4. Refactor with tests passing

### SOLID Principles
- **Single Responsibility:** Each module has one purpose
- **Open/Closed:** Extend via interfaces, don't modify core
- **Liskov Substitution:** All implementations honor contracts
- **Interface Segregation:** Small, focused interfaces
- **Dependency Inversion:** Depend on abstractions

### Code Quality Standards
- **TypeScript Strict Mode:** Enabled
- **Coverage Target:** 95%+ for Core SDK
- **No `any` Types:** All types must be explicit
- **ESLint:** No errors, no warnings
- **Prettier:** Consistent formatting

---

## Technology Stack

| Category           | Technology          | Version  | Purpose                  |
|--------------------|---------------------|----------|--------------------------|
| Language           | TypeScript         | 5.x      | Type-safe development    |
| Build Tool         | Vite               | 5.x      | Fast builds              |
| HTTP Client        | Axios              | 1.x      | API communication        |
| State Management   | Pinia              | 2.x      | Reactive stores          |
| Validation         | Zod                | 3.x      | Schema validation        |
| UI Framework       | Vue.js 3           | 3.4+     | Reactive components      |
| Routing            | Vue Router         | 4.x      | Peer dependency          |
| Styling            | Tailwind CSS       | 3.x      | Utility-first CSS        |
| Testing            | Vitest             | Latest   | Unit tests               |
| Docs               | TypeDoc            | Latest   | API documentation        |

---

## Testing Strategy

### Unit Tests (Vitest)
- **Coverage:** 95%+ for all core modules
- **Scope:** Services, composables, utilities
- **Run:** `npm run test:unit`

### Integration Tests
- **Scope:** Plugin loading, multi-module interactions
- **Run:** `npm run test:integration`

### Coverage Requirements
- **Critical Modules:** 95%+ (Plugin system, API client, Auth)
- **UI Components:** 90%+
- **Utilities:** 90%+

---

## Sprint Progress Tracking

| Sprint | Status | Start Date | End Date | Coverage | Notes |
|--------|--------|------------|----------|----------|-------|
| 0      | 📋 Planned | TBD | TBD | - | Foundation |
| 1      | 📋 Planned | TBD | TBD | 95% | Plugin system |
| 2      | 📋 Planned | TBD | TBD | 95% | API client |
| 3      | 📋 Planned | TBD | TBD | 95% | Authentication |
| 4      | 📋 Planned | TBD | TBD | 95% | Events & Validation |
| 5      | 📋 Planned | TBD | TBD | 90% | UI components |
| 6      | 📋 Planned | TBD | TBD | 90% | Composables |
| 7      | 📋 Planned | TBD | TBD | 95% | Access control |
| 8      | 📋 Planned | TBD | TBD | - | Integration & Docs |

**Legend:**
- 📋 Planned
- 🏗️ In Progress
- ✅ Complete
- ⏸️ On Hold

---

## Getting Started

### Setup Development Environment

```bash
# Create Core SDK directory
mkdir -p frontend/core
cd frontend/core

# Initialize project
npm init -y

# Install dependencies
npm install vue@3 vue-router@4 pinia@2 axios@1 zod@3

# Install dev dependencies
npm install -D \
  typescript@5 \
  vite@5 \
  vitest \
  @vue/test-utils \
  happy-dom \
  eslint \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin \
  prettier \
  eslint-config-prettier \
  typedoc

# Create project structure
mkdir -p src/{plugin,api,auth,events,validation,access,sdk,components,composables,utils,types}
mkdir -p __tests__/{unit,integration}
```

---

## Build & Test Commands

```bash
# Development
npm run dev           # Watch mode for development

# Build
npm run build         # Compile TypeScript to dist/

# Test
npm run test:unit     # Run unit tests
npm run test:watch    # Watch mode for tests
npm run test:coverage # Generate coverage report

# Lint & Format
npm run lint          # Run ESLint
npm run format        # Run Prettier

# Documentation
npm run docs          # Generate TypeDoc documentation
```

---

## Integration with Apps

### During Development (Symlinks)

```bash
# From frontend/user/vue/
npm link ../../core

# From frontend/admin/vue/
npm link ../../core
```

Both apps will see Core SDK changes immediately.

### Future (NPM Package)

```bash
# Publish Core SDK
cd frontend/core
npm version 1.0.0
npm publish

# Install in apps
cd ../user/vue
npm install @vbwd/core-sdk@1.0.0

cd ../../admin/vue
npm install @vbwd/core-sdk@1.0.0
```

---

## Related Documentation

- [Core SDK Architecture](../README.md)
- [User App Architecture](../../architecture_frontend/README.md)
- [Admin App Architecture](../../architecture_admin/README.md)
- [Backend Architecture](../../architecture_backend/README.md)
