# Sprint 01: User Edit Page - Tabs Implementation

**Date:** 2026-01-09
**Priority:** High
**Type:** Feature Implementation + E2E Testing
**Section:** Admin User Management

## Goal

Transform the User Edit page from a single-form layout to a tabbed interface with three tabs:
1. **Account** - Current form fields (email, status, role, first/last name)
2. **Subscriptions** - List of user's subscriptions with pagination and search
3. **Invoices** - List of user's invoices with pagination and search

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required
- **Code Reuse**: Leverage existing patterns from `Subscriptions.vue` and `Invoices.vue`

### Test Execution

```bash
# Full pre-commit check (recommended)
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --admin --unit --integration --e2e

# Admin E2E tests only
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-user-edit

# Skip style checks
./bin/pre-commit-check.sh --admin --unit --integration --e2e --no-style
```

### Definition of Done
- [x] All E2E tests passing
- [x] No TypeScript errors
- [x] ESLint checks pass
- [x] Tabs navigation works correctly
- [x] Subscriptions tab shows user's subscriptions with pagination
- [x] Invoices tab shows user's invoices with pagination
- [x] Account tab retains all current functionality
- [x] Click on subscription/invoice row navigates to details page
- [x] Docker image rebuilt and tested by human
- [x] Sprint moved to `/done` folder
- [x] Completion report created in `/reports`

### Build & Deploy for Testing

After modifying production files, rebuild the app and Docker image:

```bash
# Rebuild frontend Docker image
cd ~/dantweb/vbwd-sdk/vbwd-frontend
make up-build

# Or rebuild just admin app
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npm run build

# Restart containers to pick up changes
cd ~/dantweb/vbwd-sdk/vbwd-frontend
make down && make up
```

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`
- User: `test@example.com` / `TestPass123@`

---

## Tasks

### Task 1.1: E2E Tests - Tab Navigation

**Goal:** Write Playwright tests for tab navigation behavior

**Test Requirements:**
- [ ] Verify 3 tabs are visible: Account, Subscriptions, Invoices
- [ ] Account tab is active by default
- [ ] Clicking Subscriptions tab shows subscriptions content
- [ ] Clicking Invoices tab shows invoices content
- [ ] Clicking Account tab returns to account form
- [ ] Tab state persists URL hash (optional: `#account`, `#subscriptions`, `#invoices`)

**Test File:** `tests/e2e/admin-user-edit-tabs.spec.ts`

**Acceptance Criteria:**
- [ ] Tests written and initially failing (red phase)
- [ ] Tests cover all tab navigation scenarios
- [ ] Tests use proper data-testid selectors

---

### Task 1.2: E2E Tests - Account Tab

**Goal:** Verify Account tab retains existing functionality

**Test Requirements:**
- [ ] Account tab contains current form fields (email, status, role, names)
- [ ] Form submission works from Account tab
- [ ] Validation errors display correctly
- [ ] Cancel button navigates back

**Test File:** `tests/e2e/admin-user-edit-tabs.spec.ts`

**Acceptance Criteria:**
- [ ] Existing UserEdit functionality covered by new tests
- [ ] No regression in form behavior

---

### Task 1.3: E2E Tests - Subscriptions Tab

**Goal:** Write Playwright tests for Subscriptions tab

**Test Requirements:**
- [ ] Subscriptions tab shows table with user's subscriptions
- [ ] Table columns: Plan, Status, Created Date
- [ ] Pagination controls appear when needed
- [ ] Search input filters subscriptions
- [ ] Click on row navigates to subscription details
- [ ] Empty state shows message when no subscriptions
- [ ] Loading state displays during fetch

**Test File:** `tests/e2e/admin-user-edit-tabs.spec.ts`

**Acceptance Criteria:**
- [ ] Tests verify subscriptions are filtered by current user
- [ ] Pagination tests included
- [ ] Row click navigation tested

---

### Task 1.4: E2E Tests - Invoices Tab

**Goal:** Write Playwright tests for Invoices tab

**Test Requirements:**
- [ ] Invoices tab shows table with user's invoices
- [ ] Table columns: Invoice #, Amount, Status, Date
- [ ] Pagination controls appear when needed
- [ ] Search input filters invoices
- [ ] Click on row navigates to invoice details
- [ ] Empty state shows message when no invoices
- [ ] Loading state displays during fetch

**Test File:** `tests/e2e/admin-user-edit-tabs.spec.ts`

**Acceptance Criteria:**
- [ ] Tests verify invoices are filtered by current user
- [ ] Amount formatting verified
- [ ] Row click navigation tested

---

### Task 1.5: Implementation - Tab Component Structure

**Goal:** Implement tabbed interface in UserEdit.vue

**Implementation Requirements:**
- [ ] Add tab navigation UI (3 tabs)
- [ ] Implement tab state management (reactive activeTab)
- [ ] Wrap current form in Account tab content
- [ ] Create Subscriptions tab content component/section
- [ ] Create Invoices tab content component/section
- [ ] Apply consistent styling with existing admin patterns

**Files to Modify:**
- `src/views/UserEdit.vue` - Add tab structure

**Reusable Patterns:**
- Table structure from `Subscriptions.vue` lines 106-173
- Pagination from `Subscriptions.vue` lines 175-197
- Search/filter from `Subscriptions.vue` lines 20-73
- Status badges from existing components

**Acceptance Criteria:**
- [ ] Tabs render correctly
- [ ] Tab switching works
- [ ] Account form retains functionality
- [ ] No code duplication - reuse existing utilities

---

### Task 1.6: Implementation - Subscriptions & Invoices Tabs

**Goal:** Implement data fetching and display for Subscriptions and Invoices tabs

**Implementation Requirements:**
- [ ] Fetch user's subscriptions filtered by user_id
- [ ] Fetch user's invoices filtered by user_id
- [ ] Implement client-side search
- [ ] Implement pagination
- [ ] Implement sortable columns
- [ ] Handle loading/error/empty states
- [ ] Navigate to details on row click

**API Endpoints (verify or add):**
- `GET /api/v1/admin/subscriptions?user_id={id}` - Filter by user
- `GET /api/v1/admin/invoices?user_id={id}` - Filter by user

**Files to Modify:**
- `src/views/UserEdit.vue` - Tab content implementation
- `src/stores/subscriptions.ts` - Add user filter support (if needed)
- `src/stores/invoices.ts` - Add user filter support (if needed)

**Acceptance Criteria:**
- [ ] Data loads correctly for each tab
- [ ] Search works within user's data
- [ ] Pagination functional
- [ ] Row click navigates to details page
- [ ] All E2E tests pass (green phase)

---

### Task 1.7: Build & Human Testing

**Goal:** Rebuild Docker image and verify changes manually

**Requirements:**
- [ ] Run `npm run build` in admin app
- [ ] Rebuild Docker image with `make up-build`
- [ ] Verify tabs render correctly in browser
- [ ] Test tab navigation manually
- [ ] Verify subscriptions load for a user
- [ ] Verify invoices load for a user
- [ ] Test pagination manually
- [ ] Test search functionality manually

**Commands:**
```bash
# Full rebuild
cd ~/dantweb/vbwd-sdk/vbwd-frontend
make up-build

# Access admin at
http://localhost:8081/admin/users/{user-id}/edit
```

**Acceptance Criteria:**
- [ ] All tabs visible and functional
- [ ] No console errors in browser
- [ ] Data loads correctly
- [ ] Human tester approves implementation

---

## API Endpoints Reference

### Existing Endpoints
- `GET /api/v1/admin/subscriptions` - List all subscriptions
- `GET /api/v1/admin/subscriptions/{id}` - Subscription details
- `GET /api/v1/admin/invoices` - List all invoices
- `GET /api/v1/admin/invoices/{id}` - Invoice details

### Required for This Sprint
- Verify `user_id` filter support in existing endpoints
- If not supported, add query parameter filtering

---

## Files to Modify

### Views
- `src/views/UserEdit.vue` - Main implementation

### Stores (if needed)
- `src/stores/subscriptions.ts` - Add user filter
- `src/stores/invoices.ts` - Add user filter

### Tests
- `tests/e2e/admin-user-edit-tabs.spec.ts` - New E2E test file

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Tab Navigation Tests | ✅ Complete | E2E tests in admin-user-edit-tabs.spec.ts |
| 1.2 Account Tab Tests | ✅ Complete | E2E tests in admin-user-edit-tabs.spec.ts |
| 1.3 Subscriptions Tab Tests | ✅ Complete | E2E tests in admin-user-edit-tabs.spec.ts |
| 1.4 Invoices Tab Tests | ✅ Complete | E2E tests in admin-user-edit-tabs.spec.ts |
| 1.5 Tab Component Structure | ✅ Complete | UserEdit.vue updated with tabs |
| 1.6 Subscriptions & Invoices Implementation | ✅ Complete | Store updated, data fetching works |
| 1.7 Build & Human Testing | ✅ Complete | Docker rebuilt, human verified |

---

## Notes

### Code Reuse Opportunities
1. **Table structure**: Copy pattern from `Subscriptions.vue` lines 106-173
2. **Pagination**: Reuse pagination component pattern from `Subscriptions.vue` lines 175-197
3. **Sorting logic**: Reuse `handleSort`, `getSortIndicator` from existing views
4. **Status badges**: Reuse existing CSS classes
5. **formatDate/formatAmount**: Reuse utility functions

### Potential Refactoring (Future)
- Extract reusable `DataTable` component
- Extract reusable `Pagination` component
- Create shared composable for sorting logic

**Note:** Do NOT refactor during this sprint - focus on feature delivery only.

---

## Sprint Completion Workflow

When all tasks are complete and Definition of Done is satisfied:

1. **Move sprint file to `/done`:**
   ```bash
   mv docs/devlog/20260109/todo/01-user-edit-tabs.md docs/devlog/20260109/done/
   ```

2. **Create completion report in `/reports`:**
   ```bash
   # Create: docs/devlog/20260109/reports/01-user-edit-tabs-report.md
   ```

3. **Update `status.md`:**
   - Change sprint status from ⏳ Pending to ✅ Complete
   - Add completion summary

### Report Template

```markdown
# Sprint 01 Completion Report: User Edit Tabs

**Completed:** 2026-01-XX
**Duration:** X hours

## Summary
- [Brief description of what was implemented]

## Test Results
- Unit Tests: XX passed
- Integration Tests: XX passed
- E2E Tests: XX passed

## Files Modified
- `src/views/UserEdit.vue`
- `tests/e2e/admin-user-edit-tabs.spec.ts`
- [other files...]

## Notes
- [Any issues encountered and how they were resolved]
```
