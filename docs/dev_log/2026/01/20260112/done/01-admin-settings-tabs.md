# Sprint 01: Admin Settings Page Tabs

**Date:** 2026-01-12
**Priority:** High
**Type:** Feature Implementation + E2E Testing
**Section:** Admin Settings Restructuring

## Goal

Restructure the Admin Settings page to have 3 tabs: Core Settings, Payments, and Tokens.

## Clarified Requirements

| Tab | Content |
|-----|---------|
| **Core Settings** | Service provider legal info: Name, Address, Email, Web links, Bank account data |
| **Payments** | 2 subtabs: (1) Payment methods list for checkout, (2) Tab2 placeholder |
| **Tokens** | Token Bundles table only (implemented in Sprint 04) |

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required
- **Code Reuse**: Leverage existing tab patterns from UserEdit.vue

### Test Execution

```bash
# Full pre-commit check (recommended)
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --admin --unit --integration --e2e

# Admin E2E tests only
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-settings

# Skip style checks
./bin/pre-commit-check.sh --admin --unit --integration --e2e --no-style
```

### Definition of Done
- [ ] All E2E tests passing
- [ ] No TypeScript errors
- [ ] ESLint checks pass
- [ ] Settings page has 3 tabs
- [ ] Tab navigation works correctly
- [ ] Existing settings preserved in Core Settings tab
- [ ] App rebuilt with `make rebuild-admin` (see root Makefile)
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

### Build & Deploy

After implementation, rebuild the admin frontend:

```bash
# From project root
make rebuild-admin

# This runs:
# 1. cd vbwd-frontend/admin/vue && npm run build
# 2. cd vbwd-frontend/admin && docker-compose down
# 3. cd vbwd-frontend/admin && docker-compose up -d --build
```

Admin dashboard available at: http://localhost:8081

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`

---

## Tasks

### Task 1.1: E2E Tests - Settings Tabs

**Goal:** Write Playwright tests for Settings tabs

**Test Requirements:**
- [ ] Settings page has tab navigation
- [ ] Core Settings tab is visible and clickable
- [ ] Payments tab is visible and clickable
- [ ] Tokens tab is visible and clickable
- [ ] Default tab is Core Settings
- [ ] Tab switching works correctly
- [ ] URL reflects active tab (optional: query param or hash)

**Test File:** `tests/e2e/admin-settings-tabs.spec.ts`

**Acceptance Criteria:**
- [ ] Tests written and initially failing (red phase)
- [ ] Tests cover all tab scenarios
- [ ] Tests use proper data-testid selectors

---

### Task 1.2: Frontend - Tab Component Structure

**Goal:** Add tab navigation to Settings.vue

**Implementation:**
- Use existing tab pattern from UserEdit.vue if available
- Or create simple tab component inline

**Tab Structure:**
```vue
<div class="tabs">
  <button
    :class="{ active: activeTab === 'core' }"
    @click="activeTab = 'core'"
    data-testid="tab-core-settings"
  >
    Core Settings
  </button>
  <button
    :class="{ active: activeTab === 'payments' }"
    @click="activeTab = 'payments'"
    data-testid="tab-payments"
  >
    Payments
  </button>
  <button
    :class="{ active: activeTab === 'tokens' }"
    @click="activeTab = 'tokens'"
    data-testid="tab-tokens"
  >
    Tokens
  </button>
</div>
```

**Files to Modify:**
- `src/views/Settings.vue`

**Acceptance Criteria:**
- [ ] Tab buttons render correctly
- [ ] Active tab has visual indicator
- [ ] Tabs are styled consistently with app design

---

### Task 1.3: Frontend - Core Settings Tab Content

**Goal:** Create Core Settings tab with service provider legal information

**Content Fields:**
- Company/Provider Name
- Address (street, city, postal code, country)
- Contact Email
- Website URL
- Other web resource links
- Bank Account Data (IBAN, BIC, Bank Name)

**Implementation:**
- Form for editing service provider details
- Save button to persist changes
- Load existing data from backend

**Files to Modify:**
- `src/views/Settings.vue`

**Acceptance Criteria:**
- [ ] Core Settings shows legal info form
- [ ] All fields editable and saveable
- [ ] Data persists correctly

---

### Task 1.4: Frontend - Payments Tab with Subtabs

**Goal:** Create Payments tab with 2 subtabs

**Subtab Structure:**
1. **Payment Methods** - List of payment methods available for checkout
2. **Tab2** - Empty placeholder for future use

**Implementation:**
- Nested tab navigation within Payments tab
- Payment Methods subtab shows list of available payment providers
- Tab2 shows placeholder message

**Files to Modify:**
- `src/views/Settings.vue`

**Acceptance Criteria:**
- [ ] Payments tab has 2 subtabs
- [ ] Payment Methods subtab shows list
- [ ] Tab2 shows placeholder
- [ ] Subtab switching works correctly

---

### Task 1.5: Frontend - Tokens Tab Placeholder

**Goal:** Create Tokens tab content area

**Implementation:**
- Create placeholder for Token Bundles table (Sprint 04 will implement fully)
- Display header: "Token Bundles"
- Add placeholder message or empty state
- Add data-testid for testing

**Files to Modify:**
- `src/views/Settings.vue`

**Acceptance Criteria:**
- [ ] Tokens tab shows Token Bundles placeholder
- [ ] Ready for Sprint 04 implementation

---

### Task 1.6: Integration & Testing

**Goal:** Verify all tabs work correctly

**Requirements:**
- [ ] Run E2E tests
- [ ] Run unit tests
- [ ] Manual verification of tab switching
- [ ] No console errors

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-settings-tabs
npm run test
```

**Acceptance Criteria:**
- [ ] All E2E tests pass
- [ ] All unit tests pass
- [ ] Manual QA complete

---

## Files Summary

### Create
- `tests/e2e/admin-settings-tabs.spec.ts`

### Modify
- `src/views/Settings.vue`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 1.1 E2E Tests - Settings Tabs | ⏳ Pending | |
| 1.2 Tab Component Structure | ⏳ Pending | |
| 1.3 Core Settings Tab Content | ⏳ Pending | |
| 1.4 Payments Tab Placeholder | ⏳ Pending | |
| 1.5 Tokens Tab Placeholder | ⏳ Pending | |
| 1.6 Integration & Testing | ⏳ Pending | |
