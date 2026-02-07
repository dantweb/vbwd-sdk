# Sprint Overview: Checkout Enhancement

**Total Sprints:** 10
**Methodology:** TDD-first, SOLID, DRY, Clean Code, No Over-engineering
**Status:** ✅ ALL SPRINTS COMPLETED

---

## Core Requirements (All Sprints)

Every sprint MUST follow these development standards:

| Requirement | Description | Verification |
|-------------|-------------|--------------|
| **TDD-first** | Write failing tests BEFORE production code | Tests exist before implementation |
| **SOLID** | Apply all 5 principles where applicable | Documented per sprint |
| **DRY** | Reuse existing code, avoid duplication | Code review checklist |
| **Clean Code** | Readable, maintainable, self-documenting | No magic numbers, clear naming |
| **No Over-engineering** | Only implement what's needed NOW | No unused abstractions |

### TDD Workflow (Mandatory)

```
1. Write E2E tests (Playwright) → FAILING
2. Write Unit tests (Vitest/Pytest) → FAILING
3. Write minimal production code
4. All tests → PASSING
5. Refactor if needed (tests still pass)
6. Commit and move to next sprint
```

### No Over-engineering Rules

1. **No premature abstraction** - Wait until you have 3 similar things
2. **No unused features** - Only implement what's needed now
3. **No complex libraries** - Use simple solutions first
4. **No caching without profiling** - Optimize when measured
5. **No database tables for config** - Start with code/files
6. **No event handlers for sync ops** - Direct calls are fine

---

## Sprint Dependency Graph

```
Sprint 01: Email Check API (Backend) ✅
    ↓
Sprint 02: Email Block Component (Frontend) ✅
    ↓
Sprint 03: Checkout Integration ✅ ←──────────────────────┐
    ↓                                                     │
Sprint 04: Payment Methods (uses Sprint 08) ✅ ───────────┤
    ↓                                                     │
Sprint 05: Terms & Conditions ✅ ─────────────────────────┤
    ↓                                                     │
Sprint 09: Countries Configuration ✅ ────────────────────┤
    ↓                                                     │
Sprint 06: Billing Address (uses Sprint 09) ✅ ───────────┘
    ↓
Sprint 07: Pay Button & Final Integration ✅
    ↓
Sprint 08: Payment Methods Management (Admin) ✅
    ↓
Sprint 10: Pre-commit Check Fixes ✅
```

---

## Sprint Summary

| Sprint | Name | Effort | Priority | Status |
|--------|------|--------|----------|--------|
| 01 | [Email Check API](../done/sprint-01-email-check-api.md) | Small | HIGH | ✅ DONE |
| 02 | [Email Block Frontend](../done/sprint-02-email-block-frontend.md) | Medium | HIGH | ✅ DONE |
| 03 | [Checkout Integration](../done/sprint-03-checkout-integration.md) | Medium | HIGH | ✅ DONE |
| 04 | [Payment Methods UI](../done/sprint-04-payment-methods.md) | Medium | MEDIUM | ✅ DONE |
| 05 | [Terms & Conditions](../done/sprint-05-terms-conditions.md) | Small | MEDIUM | ✅ DONE |
| 06 | [Billing Address](../done/sprint-06-billing-address.md) | Medium | MEDIUM | ✅ DONE |
| 07 | [Pay Button Integration](../done/sprint-07-pay-button-integration.md) | Medium | HIGH | ✅ DONE |
| 08 | [Payment Methods Management](../done/sprint-08-payment-methods-management.md) | Large | HIGH | ✅ DONE |
| 09 | [Countries Configuration](../done/sprint-09-countries-configuration.md) | Medium | MEDIUM | ✅ DONE |
| 10 | [Pre-commit Check Fixes](../done/sprint-10-precommit-fixes.md) | Small | HIGH | ✅ DONE |

---

## SOLID Principles Checklist

Apply and document these principles in each sprint:

- [ ] **S - Single Responsibility**: Each class/component has one reason to change
- [ ] **O - Open/Closed**: Open for extension, closed for modification
- [ ] **L - Liskov Substitution**: Subtypes substitutable for base types
- [ ] **I - Interface Segregation**: Small, focused interfaces
- [ ] **D - Dependency Inversion**: Depend on abstractions, not concretions

---

## Files Created Per Sprint

### Backend Files
```
src/services/settings_service.py       # Sprint 04, 05
src/routes/settings.py                 # Sprint 04, 05
src/routes/auth.py                     # Sprint 01 (add check-email)
src/routes/user.py                     # Sprint 06 (add billing-address)
```

### Frontend Files
```
src/composables/useEmailCheck.ts       # Sprint 02
src/composables/usePaymentMethods.ts   # Sprint 04
src/utils/debounce.ts                  # Sprint 02

src/components/checkout/EmailBlock.vue       # Sprint 02
src/components/checkout/BillingAddress.vue   # Sprint 06
src/components/checkout/PaymentMethods.vue   # Sprint 04
src/components/checkout/TermsCheckbox.vue    # Sprint 05

src/stores/checkout.ts                 # Sprint 07 (update)
src/views/Checkout.vue                 # Sprint 03, 07 (update)
src/router/index.ts                    # Sprint 03 (update)
```

### Test Files
```
# Backend
tests/unit/services/test_auth_service.py      # Sprint 01
tests/unit/services/test_settings_service.py  # Sprint 04
tests/integration/routes/test_auth_routes.py  # Sprint 01
tests/integration/routes/test_settings_routes.py  # Sprint 04, 05
tests/integration/routes/test_user_routes.py  # Sprint 06

# Frontend
tests/unit/composables/useEmailCheck.spec.ts      # Sprint 02
tests/unit/composables/usePaymentMethods.spec.ts  # Sprint 04
tests/unit/components/TermsCheckbox.spec.ts       # Sprint 05
tests/unit/stores/checkout.spec.ts                # Sprint 07

tests/e2e/checkout/checkout-email.spec.ts         # Sprint 02
tests/e2e/checkout/checkout-guest-flow.spec.ts    # Sprint 03
tests/e2e/checkout/checkout-authed-flow.spec.ts   # Sprint 03
tests/e2e/checkout/checkout-payment.spec.ts       # Sprint 04
tests/e2e/checkout/checkout-conditions.spec.ts    # Sprint 05
tests/e2e/checkout/checkout-billing.spec.ts       # Sprint 06
tests/e2e/checkout/checkout-full-flow.spec.ts     # Sprint 07
```

---

## Testing & Build Commands

> **IMPORTANT:** All tests run in Docker containers. Commands are executed from either `vbwd-backend/` or `vbwd-frontend/` directory.

### Pre-commit Check Script

Use `./bin/pre-commit-check.sh` for standardized testing:

```bash
# From vbwd-backend/
./bin/pre-commit-check.sh              # Full check (lint + unit + integration)
./bin/pre-commit-check.sh --quick      # Quick check (lint + unit only)
./bin/pre-commit-check.sh --unit       # Unit tests only
./bin/pre-commit-check.sh --integration # Integration tests only

# From vbwd-frontend/
./bin/pre-commit-check.sh --admin --unit    # Admin unit tests
./bin/pre-commit-check.sh --admin --e2e     # Admin E2E tests
./bin/pre-commit-check.sh --admin --style   # Lint + TypeScript
./bin/pre-commit-check.sh --user --unit     # User unit tests
./bin/pre-commit-check.sh --user --e2e      # User E2E tests
```

### Backend Commands (Makefile)

Run from `vbwd-backend/` directory:

```bash
# Docker Management
make up                    # Start services (API, PostgreSQL, Redis)
make up-build              # Start with rebuild
make down                  # Stop services

# Testing (runs in Docker)
make test                  # All tests
make test-unit             # Unit tests only
make test-unit -- -k "test_name"        # Specific test
make test-integration      # Integration tests (real PostgreSQL)
make test-integration -- -k "TestClass" # Specific test class
make test-coverage         # Tests with coverage report

# Code Quality
make lint                  # Static analysis (black, flake8, mypy)
make pre-commit            # Full check (lint + unit + integration)
make pre-commit-quick      # Quick check (lint + unit)

# Database
make shell                 # Access API container bash
make logs                  # View service logs
```

### Frontend Commands

Run from `vbwd-frontend/` or specific app directory:

```bash
# From vbwd-frontend/
make up                    # Start production containers
make dev                   # Start development mode
make test                  # Run all unit tests (user + admin)
make test-admin            # Admin unit tests only
make test-user             # User unit tests only
make lint                  # Run ESLint for all apps

# From vbwd-frontend/admin/vue/ or vbwd-frontend/user/vue/
npm run dev                # Start dev server
npm run build              # Production build
npm run test               # Unit tests (Vitest)
npm run test:e2e           # E2E tests (Playwright, runs in Docker)
npm run test:e2e:ui        # E2E with Playwright UI
npm run lint               # ESLint
```

### ⚠️ IMPORTANT: Rebuild After Code Changes

**Frontend must be rebuilt after changing production code or views:**

```bash
# After changing .vue files, .ts files, or any frontend code:
cd vbwd-frontend/admin/vue && npm run build   # Admin app
cd vbwd-frontend/user/vue && npm run build    # User app

# Or use Docker rebuild:
cd vbwd-frontend && make up-build
```

**E2E tests run against the built/served app, not source files!**

### E2E Test Environment

```bash
# E2E tests run against Docker containers
# Set base URL if needed:
E2E_BASE_URL=http://localhost:8080 npm run test:e2e   # User app
E2E_BASE_URL=http://localhost:8081 npm run test:e2e   # Admin app
```

---

## Definition of Done

Each sprint is complete when:

1. ✅ All tests pass (unit, integration, E2E)
2. ✅ Code follows SOLID principles
3. ✅ No over-engineering
4. ✅ Existing tests still pass (regression)
5. ✅ Manual browser test works
6. ✅ Code committed with descriptive message
