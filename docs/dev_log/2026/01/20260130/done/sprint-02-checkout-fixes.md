# Sprint 02: Checkout E2E Test Fixes

**Date:** 2026-01-30
**Status:** TODO
**Estimated Scope:** P1 + P2 + P3

## Objective

Fix all 12 failing checkout E2E tests by addressing three issues:
1. **P1:** Add missing `data-testid="confirm-checkout"` (fixes 11 tests)
2. **P2:** Fix auth redirect for unauthenticated users (fixes 1 test)
3. **P3:** Update pre-commit script Playwright version

## Principles

- **TDD:** Use existing failing E2E tests as "red" tests → implement → "green"
- **SOLID:** Single responsibility - each fix addresses one concern
- **Liskov:** Route guards maintain consistent behavior across all protected routes
- **DI:** Use existing Vue Router and auth store patterns
- **DRY:** Reuse existing auth guard logic if available
- **Clean Code:** Minimal, readable changes with clear intent
- **No Over-engineering:** Simple attribute addition, simple redirect logic

## Pre-Implementation Checklist

- [ ] Backend services running (`cd vbwd-backend && make up`)
- [ ] Frontend services running (`cd vbwd-frontend && make up`)
- [ ] Verify services accessible at http://localhost:8080

## TDD Flow

```
1. RUN E2E tests (RED)     → 12 failures confirmed
2. IMPLEMENT P1            → Add data-testid
3. IMPLEMENT P2            → Fix auth redirect + update test
4. RUN E2E tests (GREEN)   → 0 failures expected
5. UPDATE P3               → Pre-commit script version
6. VERIFY                  → Final test pass
```

---

## Task 1: Verify Current State (RED)

**Command:**
```bash
cd /home/dtkachev/dantweb/vbwd-sdk/vbwd-frontend

docker run --rm --network=host \
  -v "$PWD/user:/app" \
  -v "$PWD/core:/core" \
  -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/checkout/ --config=playwright.docker.config.ts"
```

**Expected:** 12 failures, 13 passes

---

## Task 2: P1 - Add data-testid="confirm-checkout"

### 2.1 Locate the Checkout Component

**File:** `vbwd-frontend/user/vue/src/views/Checkout.vue`

### 2.2 Find the Confirm Button

Search for the checkout confirmation button (likely has text like "Confirm", "Submit", "Pay", or similar).

### 2.3 Add Test ID

**Before:**
```vue
<button @click="confirmCheckout" ...>
  Confirm Order
</button>
```

**After:**
```vue
<button data-testid="confirm-checkout" @click="confirmCheckout" ...>
  Confirm Order
</button>
```

### 2.4 Verify (Partial GREEN)

Run tests - expect 11 more tests to pass (1 should still fail - auth redirect).

---

## Task 3: P2 - Fix Auth Redirect

### 3.1 Locate Router Configuration

**File:** `vbwd-frontend/user/vue/src/router/index.ts`

### 3.2 Find Checkout Route

Look for route definition with path `/checkout/:planSlug` or similar.

### 3.3 Add/Fix Navigation Guard

**Pattern A - Route-level guard:**
```typescript
{
  path: '/checkout/:planSlug',
  name: 'Checkout',
  component: () => import('@/views/Checkout.vue'),
  meta: { requiresAuth: true }
}
```

**Pattern B - Global beforeEach (if meta.requiresAuth exists):**
```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  } else {
    next()
  }
})
```

### 3.4 Update E2E Test for Redirect Param

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-display.spec.ts`

**Find test:** `redirects unauthenticated user to login`

**Update assertion:**
```typescript
test('redirects unauthenticated user to login', async ({ page }) => {
  // Clear any existing auth
  await page.context().clearCookies();

  // Try to access checkout without auth
  await page.goto('/checkout/pro');

  // Wait for redirect to login page with redirect param
  await page.waitForURL(/\/login.*redirect/, { timeout: 10000 });
  await expect(page).toHaveURL(/\/login/);
  await expect(page).toHaveURL(/redirect=%2Fcheckout%2Fpro/);
});
```

### 3.5 Verify (Full GREEN)

Run tests - expect all 25 tests to pass.

---

## Task 4: P3 - Update Pre-commit Script

### 4.1 Update Playwright Version

**File:** `vbwd-frontend/bin/pre-commit-check.sh`

**Find and replace (2 occurrences):**
```bash
# Line 261 and 282
# FROM:
mcr.microsoft.com/playwright:v1.40.0-jammy
# TO:
mcr.microsoft.com/playwright:v1.57.0-jammy
```

---

## Final Verification

### Run Checkout Tests
```bash
cd /home/dtkachev/dantweb/vbwd-sdk/vbwd-frontend

docker run --rm --network=host \
  -v "$PWD/user:/app" \
  -v "$PWD/core:/core" \
  -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/checkout/ --config=playwright.docker.config.ts"
```

**Expected Result:** 25 passed, 0 failed

### Run Style Checks (Optional)
```bash
cd /home/dtkachev/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --user --no-style --e2e
```

---

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| All 25 checkout E2E tests pass | ⬜ |
| `data-testid="confirm-checkout"` added | ⬜ |
| Unauthenticated users redirect to `/login?redirect=...` | ⬜ |
| E2E test updated to verify redirect param | ⬜ |
| Pre-commit script uses Playwright v1.57.0 | ⬜ |
| No TypeScript errors | ⬜ |
| No ESLint errors | ⬜ |

---

## Files to Modify

| File | Change |
|------|--------|
| `vbwd-frontend/user/vue/src/views/Checkout.vue` | Add `data-testid="confirm-checkout"` |
| `vbwd-frontend/user/vue/src/router/index.ts` | Fix auth guard redirect |
| `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-display.spec.ts` | Update redirect assertion |
| `vbwd-frontend/bin/pre-commit-check.sh` | Update Playwright version |

---

## Rollback Plan

If issues arise, revert changes:
```bash
git checkout -- vbwd-frontend/user/vue/src/views/Checkout.vue
git checkout -- vbwd-frontend/user/vue/src/router/index.ts
git checkout -- vbwd-frontend/user/vue/tests/e2e/checkout/checkout-display.spec.ts
git checkout -- vbwd-frontend/bin/pre-commit-check.sh
```
