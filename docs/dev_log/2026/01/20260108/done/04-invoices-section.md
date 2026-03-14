# Sprint 04: Invoices Section

**Date:** 2026-01-08
**Priority:** High
**Type:** E2E Testing + Bug Fixes
**Section:** Invoices

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
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-invoice
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

### Task 4.1: Invoices List - Sortable Columns

**Goal:** Add column sorting to Invoices table

**Implementation Requirements:**
- Add sort indicators (▲/▼) to column headers
- Support sorting by: Invoice Number, Customer Email, Amount, Status, Date
- Toggle between ASC/DESC on column click
- Persist sort state during session

**Test Requirements:**
- Add sorting tests to `admin-invoices-fields.spec.ts`
- Verify clicking column header sorts data
- Verify sort direction toggles

**Acceptance Criteria:**
- [ ] Column headers are clickable
- [ ] Sort indicator shows current sort column/direction
- [ ] Data reorders correctly on sort
- [ ] E2E test verifies sorting functionality

---

### Task 4.2: Invoices List - Field Population Test

**Goal:** Verify all table fields are populated in Invoices list view

**Test File:** `tests/e2e/admin-invoices-fields.spec.ts`

**Test Requirements:**
- Verify columns: Invoice Number, Customer Email, Amount, Status, Date
- Test that each field contains actual data (not empty/undefined)
- Verify amount formatting (currency symbol, proper decimals)
- Verify status badge colors (paid=green, open=blue, draft=gray, void=red, uncollectible=yellow)
- Test with multiple invoices

**Acceptance Criteria:**
- [ ] E2E test created: `admin-invoices-fields.spec.ts`
- [ ] Test verifies all 5 columns have data
- [ ] Amount is properly formatted
- [ ] Status badges display correctly
- [ ] Any missing field mappings fixed in `Invoices.vue`
- [ ] Test passes consistently

---

### Task 4.3: Invoices List - Filter & Pagination Test

**Goal:** Verify filters and pagination work correctly

**Test Requirements (add to fields test):**
- Test status filter: All, Draft, Open, Paid, Void, Uncollectible
- Verify pagination works (20 items per page)
- Verify total count updates with filters

**Acceptance Criteria:**
- [ ] Status filter correctly filters data
- [ ] Pagination updates with filtered results
- [ ] Total count is accurate

---

### Task 4.4: Invoice Details & Actions Test

**Goal:** Test invoice details view and actions

**Test File:** `tests/e2e/admin-invoice-actions.spec.ts`

**Test Requirements:**
- **View Details:**
  - Customer Information (email, name)
  - Invoice Information (number, status, amount, due date, paid at, created)
  - Line Items table (description, quantity, unit price, amount)
  - Subtotal calculation
  - Billing Address (if present)

- **Actions:**
  - Resend Invoice (always available)
  - Void Invoice (only for open/draft status)
  - Verify action results

**Acceptance Criteria:**
- [ ] E2E test created: `admin-invoice-actions.spec.ts`
- [ ] Details view shows all sections
- [ ] Line items display correctly
- [ ] Resend action works
- [ ] Void action works (for eligible invoices)
- [ ] Status updates after void
- [ ] Any bugs found are fixed

---

## API Endpoints

- `GET /api/v1/admin/invoices` - List (params: page, per_page, status)
- `GET /api/v1/admin/invoices/:id` - Details
- `POST /api/v1/admin/invoices/:id/resend` - Resend invoice
- `POST /api/v1/admin/invoices/:id/void` - Void invoice

---

## Files to Modify

- `src/views/Invoices.vue` - List view, field mappings, filters
- `src/views/InvoiceDetails.vue` - Details view, actions
- `src/stores/invoices.ts` - Store
- `tests/e2e/admin-invoices-fields.spec.ts` - New test
- `tests/e2e/admin-invoice-actions.spec.ts` - New test

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Sortable columns | ⏳ Pending | |
| 4.2 Invoices fields test | ⏳ Pending | |
| 4.3 Filter & pagination test | ⏳ Pending | |
| 4.4 Details & actions test | ⏳ Pending | |
