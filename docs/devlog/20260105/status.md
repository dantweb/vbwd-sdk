# Development Log - 2026-01-05

## Session Start

**Date:** 2026-01-05
**Focus:** Fix Docker startup issues, then continue with planned work

---

## Sprint Focus
- Fix Docker startup issues (new priority)
- Architectural Deviations Analysis
- E2E Test Infrastructure Improvements

## Todo

| # | Task | Status |
|---|------|--------|
| 8 | [Frontend: Test Infrastructure Fixes](todo/08-frontend-test-fixes.md) | Pending |

## Completed

| # | Task | Status |
|---|------|--------|
| 0 | [Fix Docker Startup](done/00-fix-docker-startup.md) | **Done** |
| 1 | [Architecture Decision: Plugin vs Flat](done/01-architectural-decision-plugin-vs-flat.md) | **Done** |
| 2 | [CLI Plugin Manager](done/02-cli-plugin-manager.md) | **Done** |
| 3 | [Core SDK Migration](done/03-core-sdk-migration.md) | **Done** |
| 4 | [E2E & Integration Tests](done/04-e2e-integration-user-subscription-flow.md) | **Done** |
| 5 | [Backend: Admin Create User](done/05-backend-admin-create-user.md) | **Done** |
| 6 | [Backend: Admin Create Subscription](done/06-backend-admin-create-subscription.md) | **Done** |
| 7 | [Frontend: Admin Create User Form](done/07-frontend-admin-create-user-form.md) | **Done** |
| - | Architecture Decision: Core SDK Usage (ApiClient, Auth, EventBus) | **Done** |
| - | [Original Sprint 01](done/01-architectural-deviations-and-e2e-improvements.md) | **Superseded** |

---

## Resolved Issues

### Docker Startup Error - FIXED

**Problem:** `make up` failed with `KeyError: 'ContainerConfig'`

**Solution:** Removed corrupted adminer container with `docker-compose down` and restarted.

**Services Status (all running):**
- ✅ postgres: Up (healthy)
- ✅ redis: Up (healthy)
- ✅ api: Up
- ✅ adminer: Up

---

## Discovered Issues (Now Fixed)

### 1. currency_repository.py - Arguments Swapped - FIXED

API returned 500 error on `/api/v1/tarif-plans`:
```
TypeError: 'Query' object is not callable
```
**Root Cause:** `super().__init__(Currency, session)` had arguments in wrong order.
**Fix:** Changed to `super().__init__(session, Currency)`.

### 2. auth_service.py - Non-existent Method - FIXED

Registration returned 500 error:
```
AttributeError: 'UserRepository' object has no attribute 'create'
```
**Root Cause:** Called `self._user_repo.create()` but BaseRepository only has `save()`.
**Fix:** Changed to `self._user_repo.save(new_user)`.

### 3. events.py - Wrong Authentication Import - FIXED

API container crashed on startup:
```
ModuleNotFoundError: No module named 'flask_jwt_extended'
```
**Root Cause:** Used `flask_jwt_extended` instead of custom `src.middleware.auth`.
**Fix:** Changed to use `@require_auth` and `g.user_id`.

---

## Test Results

### Backend Integration Tests: 14 passed, 2 xpassed

All tests pass. After Sprint 05 & 06 implementation:
- ✅ `POST /admin/users` - **Implemented** (Sprint 05)
- ✅ `POST /admin/subscriptions` - **Implemented** (Sprint 06)

### Frontend E2E Tests: 1 passed, 7 failed

Failures reveal **TDD discoveries**:
- Admin UI lacks "Create" buttons for users/subscriptions (mirrors API limitation)
- Page headers don't match expected patterns ("VBWD Admin" vs "Users", "Subscriptions")
- Tests need to be updated to match actual UI implementation

---

## Context from 2026-01-02

### Completed
- Bug fixes (nginx proxy, Plans page, PlanForm features)
- Demo data installation script
- Admin E2E tests (108 tests)
- Architecture documentation updates

### Known Issues
- E2E tests timeout in docker (need E2E_BASE_URL) - **Next priority**
- ~~Frontend uses flat structure instead of planned plugin architecture~~ **RESOLVED** - This is by design (see ADR)
- Shared component library is minimal

