# Sprint 02: Plans Section

**Date:** 2026-01-08
**Priority:** High
**Type:** E2E Testing + Bug Fixes
**Section:** Plans

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
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-plan
```

### Definition of Done
- [ ] All new E2E tests pass
- [ ] Existing E2E tests still pass
- [ ] No TypeScript errors (`npx vue-tsc --noEmit`)
- [ ] Code follows existing patterns

### Docker Rebuild (Required after code changes)
```bash
cd /home/dtkachev/dantweb/vbwd-sdk/vbwd-frontend
docker-compose down && docker-compose up -d admin-app
```

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`

---

## Tasks

### Task 2.1: Plans List - Sortable Columns

**Goal:** Add column sorting to Plans table

**Implementation Requirements:**
- Add sort indicators (▲/▼) to column headers
- Support sorting by: Name, Price, Billing Period, Subscriber Count, Status
- Toggle between ASC/DESC on column click
- Persist sort state during session

**Test Requirements:**
- Add sorting tests to `admin-plans-fields.spec.ts`
- Verify clicking column header sorts data
- Verify sort direction toggles

**Acceptance Criteria:**
- [ ] Column headers are clickable
- [ ] Sort indicator shows current sort column/direction
- [ ] Data reorders correctly on sort
- [ ] E2E test verifies sorting functionality

---

### Task 2.2: Plans List - Field Population Test

**Goal:** Verify all table fields are populated in Plans list view

**Test File:** `tests/e2e/admin-plans-fields.spec.ts`

**Test Requirements:**
- Verify columns: Name, Price, Billing Period, Subscriber Count, Status
- Test that each field contains actual data (not empty/undefined)
- Test with multiple plans
- Test archived plans visibility toggle

**Current Issue:** Not all fields may be populated from API response

**Acceptance Criteria:**
- [ ] E2E test created: `admin-plans-fields.spec.ts`
- [ ] Test verifies all 5 columns have data
- [ ] Any missing field mappings fixed in `Plans.vue`
- [ ] Test passes consistently

---

### Task 2.3: Plan Edit - Update Tests & Bug Fixes

**Goal:** Test plan status and field updates, fix any errors

**Test File:** `tests/e2e/admin-plan-edit.spec.ts`

**Test Requirements:**
- Test changing plan status (Active → Inactive)
- Test updating plan fields:
  - Name
  - Price
  - Billing period
  - Features (JSON)
- Test archive/unarchive functionality
- Verify changes persist and reflect in list

**Acceptance Criteria:**
- [ ] E2E test created: `admin-plan-edit.spec.ts`
- [ ] Status changes work correctly
- [ ] Field updates persist
- [ ] Archive/unarchive functionality works
- [ ] All found bugs fixed

---

## API Endpoints

- `GET /api/v1/admin/plans` - Plans list (with query params: include_archived)
- `GET /api/v1/admin/plans/:id` - Plan details
- `POST /api/v1/admin/plans` - Create plan
- `PUT /api/v1/admin/plans/:id` - Update plan
- `POST /api/v1/admin/plans/:id/archive` - Archive plan
- `POST /api/v1/admin/plans/:id/unarchive` - Unarchive plan

---

## Files to Modify

- `src/views/Plans.vue` - List view, field mappings
- `src/views/PlanForm.vue` - Edit form
- `src/stores/planAdmin.ts` - Store
- `tests/e2e/admin-plans-fields.spec.ts` - New test
- `tests/e2e/admin-plan-edit.spec.ts` - New test

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Sortable columns | ✅ Complete | 5 sorting tests |
| 2.2 Plans fields test | ✅ Complete | 6 field tests |
| 2.3 Plan edit test | ✅ Complete | 12 edit tests |

---

## Completion Summary

**Total: 23 E2E tests passing**

### Bug Fixes Applied
1. **Billing Period Enum Fix**: Backend expects UPPERCASE enum values (MONTHLY, YEARLY) but frontend was sending lowercase
   - Fixed: Added `.toUpperCase()` in PlanForm.vue before API submission
   - Fixed: Changed form select option values to UPPERCASE

### Test Files Created
- `tests/e2e/admin-plans-fields.spec.ts` - 11 tests
- `tests/e2e/admin-plan-edit.spec.ts` - 12 tests

### Implementation Files Modified
- `src/views/Plans.vue` - Added sortable columns with indicators
- `src/views/PlanForm.vue` - Fixed billing period enum values
- `src/stores/planAdmin.ts` - Updated type definitions
