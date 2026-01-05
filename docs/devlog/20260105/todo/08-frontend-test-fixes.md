# Sprint: Frontend - Test Infrastructure Fixes

**Date:** 2026-01-05
**Priority:** High
**Type:** Test Infrastructure
**Goal:** All frontend tests pass (unit + E2E)

---

## Core Requirements

### Methodology
- **TDD-First**: Fix tests to match actual implementation
- **No Over-engineering**: Minimal fixes, no refactoring unrelated code
- **Clean Code**: Follow existing patterns

### Test Execution
```bash
cd vbwd-frontend/admin/vue

# Unit tests
npm run test

# E2E tests
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-subscription-flow --reporter=list

# Full pre-commit check
cd .. && ./bin/pre-commit-check.sh --admin --unit --e2e
```

### Definition of Done
- [ ] All unit tests pass (71/71)
- [ ] All E2E tests pass (8/8)
- [ ] No TypeScript errors in test files
- [ ] No ESLint errors in test files

---

## Current Issues

### Issue 1: Unit Test - auth.spec.ts (7 tests failing)

**Error:**
```
Error: [🍍]: "getActivePinia()" was called but there was no active Pinia.
```

**Root Cause:** Tests don't call `setActivePinia(createPinia())` before using the store.

**File:** `tests/unit/stores/auth.spec.ts`

**Fix:** Add Pinia setup in beforeEach:
```typescript
import { setActivePinia, createPinia } from 'pinia';

beforeEach(() => {
  setActivePinia(createPinia());
});
```

---

### Issue 2: E2E Test - Login Timeout

**Error:**
```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
waiting for locator('input[id="username"]')
```

**Root Cause:** The login page may not be fully loaded, or there's a navigation/routing issue.

**File:** `tests/e2e/admin-user-subscription-flow.spec.ts`

**Fix:** Add proper wait for page load:
```typescript
test.beforeEach(async ({ page }) => {
  await page.goto('/admin/login');
  await page.waitForLoadState('networkidle');
  // ... rest of login
});
```

---

### Issue 3: E2E Test - Page Header Assertions

**Error:**
```
Expected pattern: /Users/i
Received string: "VBWD Admin"
```

**Root Cause:** Tests expect page title in h1/h2, but AdminLayout shows "VBWD Admin" in header. The page content has h2 with "Users" but it's not the first h1/h2.

**File:** `tests/e2e/admin-user-subscription-flow.spec.ts`

**Fix:** Use more specific selector for page content:
```typescript
// Instead of:
await expect(page.locator('h1, h2').first()).toContainText(/Users/i);

// Use:
await expect(page.locator('.users-view h2, main h2').first()).toContainText(/Users/i);
```

---

### Issue 4: TypeScript Error - Unused Variables

**Error:**
```
'createdUserId' is assigned a value but never used
'createdSubscriptionId' is assigned a value but never used
```

**File:** `tests/e2e/admin-user-subscription-flow.spec.ts:38-39`

**Fix:** Either use the variables or prefix with underscore:
```typescript
let _createdUserId: string | null = null;
let _createdSubscriptionId: string | null = null;
```

---

### Issue 5: TypeScript Error - RegExp in selectOption

**Error:**
```
Argument of type '{ label: RegExp; }' is not assignable to parameter
Type 'RegExp' is not assignable to type 'string'.
```

**File:** `tests/e2e/admin-user-subscription-flow.spec.ts:191`

**Fix:** Convert RegExp to string match:
```typescript
// Instead of:
await userSelect.selectOption({ label: new RegExp(testUser.email) });

// Use:
const options = await userSelect.locator('option').allTextContents();
const match = options.find(opt => opt.includes(testUser.email));
if (match) await userSelect.selectOption({ label: match });
```

---

### Issue 6: TypeScript Error - Wrong Argument Count

**Error:**
```
Expected 1 arguments, but got 2.
```

**File:** `tests/unit/stores/auth.spec.ts:68,85`

**Root Cause:** `authStore.login()` signature changed - tests pass extra argument.

**Fix:** Update test calls to match current API:
```typescript
// Check current login signature and update tests accordingly
```

---

## Implementation Plan

### Phase 1: Fix Unit Tests (auth.spec.ts)

1. Add Pinia setup in beforeEach
2. Fix login() call signatures
3. Verify all 7 tests pass

### Phase 2: Fix E2E TypeScript Errors

1. Prefix unused variables with underscore
2. Fix RegExp selectOption type error
3. Verify TypeScript compiles

### Phase 3: Fix E2E Runtime Errors

1. Add waitForLoadState after goto
2. Update page header selectors to be more specific
3. Verify all 8 E2E tests pass

---

## Test Files to Modify

| File | Changes |
|------|---------|
| `tests/unit/stores/auth.spec.ts` | Add Pinia setup, fix login calls |
| `tests/e2e/admin-user-subscription-flow.spec.ts` | Fix selectors, waits, types |

---

## Acceptance Criteria

- [ ] `npm run test` shows 71 passed, 0 failed
- [ ] `npx playwright test admin-user-subscription-flow` shows 8 passed
- [ ] `npx vue-tsc --noEmit` shows no errors
- [ ] `npm run lint` shows no errors

---

*Created: 2026-01-05*
*Depends on: Sprint 07 (Frontend Create User Form)*
