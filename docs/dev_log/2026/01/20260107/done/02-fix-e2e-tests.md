# Sprint Task 02: Fix E2E Tests

**Priority:** High
**Type:** Test Fixes
**Estimated Effort:** Medium
**Depends on:** 01-add-data-testid-attributes

---

## Objective

Get all E2E tests passing with proper selectors and flow.

---

## Current Test Files

- `admin-users.spec.ts` - Users management tests
- `admin-user-details.spec.ts` - User details tests
- `admin-user-subscription-flow.spec.ts` - Full flow test

---

## Known Issues

1. **Navigation after login** - Direct URL navigation logs out user; must click sidebar links
2. **Selector timeouts** - Tests use CSS classes that may not exist
3. **Auth mocking** - Mock auth doesn't work with real backend

---

## Fix Strategy

### 1. Update Auth Flow
- Login via UI (not mock)
- Navigate via sidebar clicks (not direct URL)
- Wait for page load after navigation

### 2. Update Selectors
- Replace CSS class selectors with data-testid
- Use flexible selectors with fallbacks during transition

### 3. Update Wait Strategy
- Wait for specific elements instead of arbitrary timeouts
- Use `waitForLoadState('networkidle')` after navigation

---

## Tests to Fix

### admin-users.spec.ts
- [ ] should display users list
- [ ] should search users by email
- [ ] should filter users by status
- [ ] should navigate to user details
- [ ] should display user status badges
- [ ] should show pagination when many users

### admin-user-subscription-flow.spec.ts
- [ ] Step 1: Navigate to Users page
- [ ] Step 2: Create new user
- [ ] Step 3: Verify user in list
- [ ] Step 4: Navigate to Subscriptions
- [ ] Step 5: Create subscription (needs UI)
- [ ] Step 6: Navigate to Invoices
- [ ] Step 7: Verify invoice

---

## Acceptance Criteria

- [ ] All 6 admin-users tests pass
- [ ] Flow test steps 1-4 pass
- [ ] Tests run reliably (no flaky failures)
- [ ] Tests work with `--headed` flag

---

*Created: 2026-01-07*
