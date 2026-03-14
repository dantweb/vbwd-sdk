# Sprint 01: Users Section

**Date:** 2026-01-08
**Priority:** High
**Type:** E2E Testing + Bug Fixes + Feature Implementation
**Section:** Users

---

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE fixing/implementing features
- **SOLID Principles**: Single responsibility, clear interfaces, dependency injection
- **Clean Code**: Self-documenting, minimal complexity, consistent patterns
- **No Over-engineering**: Only implement what's explicitly required

### Test Execution

**Pre-commit check script (recommended):**
```bash
cd /home/dtkachev/dantweb/vbwd-sdk/vbwd-frontend

# Style checks only (ESLint + TypeScript)
./bin/pre-commit-check.sh --admin

# Style + Unit tests
./bin/pre-commit-check.sh --admin --unit

# Style + E2E tests
./bin/pre-commit-check.sh --admin --e2e

# All checks
./bin/pre-commit-check.sh --admin --unit --e2e
```

**Direct Playwright execution:**
```bash
cd /home/dtkachev/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-users
```

### Definition of Done
- [x] All new E2E tests pass
- [x] Existing E2E tests still pass
- [x] No TypeScript errors (`npx vue-tsc --noEmit`)
- [x] Code follows existing patterns

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`

---

## Tasks

### Task 1.1: Users List - Field Population Test & Fix

**Goal:** Verify all table fields are populated in Users list view

**Test File:** `tests/e2e/admin-users-fields.spec.ts`

**Test Requirements:**
- Verify columns: Email, Name, Status, Roles, Created
- Test that each field contains actual data (not empty/undefined)
- Test with multiple users to ensure consistency

**Current Issue:** Some table fields may display empty/undefined values

**Acceptance Criteria:**
- [x] E2E test created: `admin-users-fields.spec.ts`
- [x] Test verifies all 5 columns have data
- [x] Any missing field mappings fixed in `Users.vue`
- [x] Test passes consistently

---

### Task 1.2: Users List - Sortable Columns

**Goal:** Add column sorting to Users table

**Implementation Requirements:**
- Add sort indicators (▲/▼) to column headers
- Support sorting by: Email, Name, Status, Created
- Toggle between ASC/DESC on column click
- Persist sort state during session

**Test Requirements:**
- Add sorting tests to `admin-users-fields.spec.ts`
- Verify clicking column header sorts data
- Verify sort direction toggles

**Acceptance Criteria:**
- [x] Column headers are clickable
- [x] Sort indicator shows current sort column/direction
- [x] Data reorders correctly on sort
- [x] E2E test verifies sorting functionality

---

### Task 1.3: Users List - Direct Navigation to Edit Page

**Goal:** Row click navigates directly to edit page, bypassing details view

**Current Behavior:**
```
Click row → /admin/users/:id (details)
Click Edit button → /admin/users/:id/edit
```

**Required Behavior:**
```
Click row → /admin/users/:id/edit (direct to edit)
```

**Implementation:**
- Update `Users.vue` row click handler
- Change `router.push(\`/admin/users/${id}\`)` to `router.push(\`/admin/users/${id}/edit\`)`

**Acceptance Criteria:**
- [x] Row click navigates to `/admin/users/:id/edit`
- [x] Edit page loads correctly
- [x] E2E test verifies new navigation behavior

---

### Task 1.4: User Edit - Status Change Test & Validation

**Goal:** Test that user status and other fields update correctly

**Test File:** `tests/e2e/admin-user-edit.spec.ts`

**Test Requirements:**
- Test changing user status (Active → Inactive, Inactive → Active)
- Test updating other fields (name, email, roles)
- Verify changes persist after save
- Verify changes reflect in list view

**Acceptance Criteria:**
- [x] E2E test created: `admin-user-edit.spec.ts`
- [x] Test verifies status change works
- [x] Test verifies other field updates work
- [x] Test verifies persistence (reload shows saved values)
- [x] Any bugs found are fixed

---

## API Endpoints

- `GET /api/v1/admin/users` - Users list (with query params: page, per_page, search, status)
- `GET /api/v1/admin/users/:id` - User details
- `PUT /api/v1/admin/users/:id` - Update user

---

## Files to Modify

- `src/views/Users.vue` - List view, sorting, navigation
- `src/views/UserEdit.vue` - Edit form
- `src/stores/users.ts` - Store (if sorting needs backend support)
- `tests/e2e/admin-users-fields.spec.ts` - New test
- `tests/e2e/admin-user-edit.spec.ts` - New test

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Field population test | ✅ Complete | `admin-users-fields.spec.ts` - 10 tests |
| 1.2 Sortable columns | ✅ Complete | Client-side sorting with indicators |
| 1.3 Direct edit navigation | ✅ Complete | Row click → Edit page directly |
| 1.4 User edit test | ✅ Complete | `admin-user-edit.spec.ts` - 9 tests |

---

## Completion Summary

**Completed:** 2026-01-08
**Total Tests:** 41 passing
**Test Files:**
- `admin-users-fields.spec.ts` - 10 tests (new)
- `admin-user-edit.spec.ts` - 9 tests (new)
- `admin-user-crud-flow.spec.ts` - 6 tests (updated)
- `admin-user-details.spec.ts` - 6 tests (rewritten)
- `admin-users.spec.ts` - 10 tests (updated)
