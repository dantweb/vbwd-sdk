# Ticket: Architectural Deviations Analysis & E2E Test Improvements

**Date:** 2026-01-05
**Priority:** High
**Type:** Technical Debt + Testing
**Status:** SUPERSEDED

> **Note:** This sprint has been superseded by specific decision documents and sprints:
> - Architecture decisions → `done/01-architectural-decision-plugin-vs-flat.md`
> - Core SDK migration → `todo/03-core-sdk-migration.md`
> - E2E tests → `todo/04-e2e-integration-user-subscription-flow.md`

---

## 1. Architectural Deviations Analysis

### Objective
Identify and document all deviations between planned architecture (in `docs/`) and actual implementation, then create a remediation plan.

### Tasks

#### 1.1 Frontend Architecture Audit
- [ ] Compare `architecture_core_view_admin/README.md` with `admin/vue/src/`
- [ ] Compare `architecture_core_view_component/README.md` with `core/`
- [ ] Document which planned features exist vs. not implemented
- [ ] Create decision document: keep current structure or migrate to plugins?

#### 1.2 Plugin System Analysis

**Backend Plugin System** (`vbwd-backend/src/plugins/`):
- ✅ `BasePlugin` abstract class with lifecycle hooks
- ✅ `PluginManager` with registration, dependency checking
- ✅ `MockPaymentPlugin` implementation exists
- ⏳ Stripe/PayPal plugins not yet implemented

**Frontend Plugin System** (`vbwd-frontend/core/src/plugins/`):
- ✅ `IPlugin` interface with full lifecycle
- ✅ `PluginRegistry` with dependency resolution
- ✅ `PlatformSDK` for routes, components, stores
- ⚠️ NOT USED by admin or user apps

#### 1.3 Key Deviations to Evaluate

| Component | Core SDK Has | Admin App Uses | Decision Needed |
|-----------|-------------|----------------|-----------------|
| Plugin System | ✅ PluginRegistry | ❌ Flat views/ | Migrate or keep flat? |
| API Client | ✅ ApiClient class | ❌ Local api.ts | Use core's client? |
| Auth Store | ✅ auth.ts | ❌ Local auth.ts | Use core's store? |
| Event Bus | ✅ EventBus | ❌ Not used | Integrate events? |
| Route Guards | ✅ AuthGuard, RoleGuard | ✅ Uses guards | Keep as-is |
| Per-plugin stores | ✅ Planned | ❌ Flat stores/ | Acceptable |

#### 1.4 Backend Architecture Audit
- [ ] Compare `architecture_core_server_ce/README.md` with `vbwd-backend/src/`
- [ ] Verify event system implementation matches design
- [ ] Verify SDK adapter pattern implementation

### Deliverables
- `docs/devlog/20260105/done/01-architectural-audit-report.md`
- Decision on plugin architecture: implement or abandon?
- Updated architecture docs if abandoning planned design

---

## 2. E2E Test Improvements

### Current Status
- 108 E2E tests in 13 spec files
- Tests pass with mocked API
- Tests NOT running against real backend (timeout issues)

### Tasks

#### 2.1 Fix E2E Test Infrastructure
- [ ] Update `pre-commit-check.sh` to pass `E2E_BASE_URL` to docker container
- [ ] Configure playwright to connect to docker network
- [ ] Add healthcheck before running E2E tests

#### 2.2 Real Backend Testing
- [ ] Create E2E test mode that hits real API
- [ ] Seed database with test data before E2E run
- [ ] Clean up test data after E2E run

#### 2.3 Missing E2E Coverage

Tests exist but need real backend validation:

| Page | Current Tests | Real Backend Needed |
|------|--------------|---------------------|
| Dashboard | API mocks | Real analytics data |
| Users | List, view, edit | Create/suspend users |
| Plans | List, create, edit | Verify DB changes |
| Subscriptions | List, view | Cancel, extend flows |
| Invoices | List, view | Mark paid, void |
| Webhooks | List, view | Retry webhook |
| Settings | Tab navigation | Save settings |
| Analytics | Date filter | Real metric data |

#### 2.4 Add Missing Tests
- [ ] Error handling scenarios (API failures)
- [ ] Form validation edge cases
- [ ] Pagination with large datasets
- [ ] Search and filter combinations
- [ ] Concurrent edit detection

### Deliverables
- Working E2E tests against real backend
- Updated `pre-commit-check.sh` with `--e2e-real` flag
- Test coverage report

---

## 3. Technical Notes

### E2E_BASE_URL Configuration

Current `playwright.config.ts` supports `E2E_BASE_URL`:

```typescript
const baseURL = process.env.E2E_BASE_URL || 'http://localhost:5174';
const useDevServer = !process.env.E2E_BASE_URL;
```

To run against docker:
```bash
E2E_BASE_URL=http://localhost:8081 npx playwright test
```

### Docker Network Issue

From inside docker container, `localhost:8081` won't work. Options:
1. Use `host.docker.internal:8081` (Docker Desktop)
2. Use docker network IP
3. Run playwright on host, not in container

### Test Data Management

Options:
1. **Fixtures**: Load SQL fixtures before each test file
2. **API Seeding**: Call API to create test data
3. **Database Snapshot**: Restore from snapshot before E2E

---

## Acceptance Criteria

1. [ ] Architectural audit complete with decision document
2. [ ] E2E tests run against real backend successfully
3. [ ] `./bin/pre-commit-check.sh --admin --e2e` passes
4. [ ] Documentation updated with findings

---

*Created: 2026-01-02*
*For: 2026-01-05 Sprint*
