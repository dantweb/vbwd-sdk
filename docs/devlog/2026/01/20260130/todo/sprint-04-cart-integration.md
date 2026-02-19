# Sprint 04: Cart Integration Fix

**Date:** 2026-01-30
**Status:** TODO
**Prerequisite:** Sprint 03 (pages complete, cart store complete)

## Objective

Fix all 14 failing E2E tests by resolving the Pinia store integration issue and enabling cart functionality across the user app.

## Problem Statement

The cart store (`useCartStore`) from `@vbwd/view-component` cannot be imported in the user app without breaking Vue rendering. All cart-related E2E tests fail.

## Failing Tests (14 total)

### Tokens Page (1 failing)
- `can add token bundle to cart` - cart-count element not found

### Add-ons Page (1 failing)
- `can add add-on to cart` - cart-count element not found

### Cart Tests (12 failing)
- `cart icon is visible in header`
- `cart shows zero count when empty`
- `adding item updates cart count`
- `adding multiple items updates cart count`
- `clicking cart icon opens dropdown`
- `cart dropdown shows added items`
- `can remove item from cart`
- `cart shows total price`
- `can navigate to checkout from cart`
- `cart persists across page navigation`
- `cart persists after page refresh`
- `empty cart shows empty state message`

## Root Cause Analysis

### Hypothesis 1: Pinia Instance Mismatch
The core library may be creating its own Pinia instance instead of using the host app's instance.

**Test:** Create a simple counter store in core, import in user app.

### Hypothesis 2: Module Load Timing
The store may be accessed before Pinia is installed in the Vue app.

**Test:** Lazy load the store using dynamic import inside component setup.

### Hypothesis 3: Build Configuration
Pinia may not be properly externalized in the core library build.

**Test:** Check bundle contents for duplicate Pinia code.

## Sprint Tasks

### Phase 1: Debug & Diagnose

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 1 | Create minimal reproduction | Simple counter store to isolate issue | S |
| 2 | Check bundle for Pinia duplication | Inspect `core/dist/index.mjs` | S |
| 3 | Test lazy loading pattern | Dynamic import in component setup | S |
| 4 | Add console logging to store | Debug initialization timing | S |

### Phase 2: Fix Implementation

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 5 | Implement chosen fix | Based on diagnosis results | M |
| 6 | Re-enable cart in UserLayout.vue | Import and use `useCartStore` | S |
| 7 | Re-enable cart in Tokens.vue | Connect addToCart function | S |
| 8 | Re-enable cart in AddOns.vue | Connect addToCart function | S |
| 9 | Rebuild and test locally | Manual verification | S |

### Phase 3: E2E Verification

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 10 | Run tokens-page.spec.ts | Expect 7/7 passing | S |
| 11 | Run addons-page.spec.ts | Expect 10/10 passing | S |
| 12 | Run cart.spec.ts | Expect 12/12 passing | M |
| 13 | Run full checkout tests | Regression check | S |

## Technical Approaches to Try

### Approach A: Lazy Store Loading
```typescript
// Instead of top-level import
import { useCartStore } from '@vbwd/view-component';

// Use dynamic import in setup
const cartStore = ref<ReturnType<typeof useCartStore> | null>(null);
onMounted(async () => {
  const { useCartStore } = await import('@vbwd/view-component');
  cartStore.value = useCartStore();
});
```

### Approach B: Check Pinia Availability
```typescript
import { getActivePinia } from 'pinia';

const pinia = getActivePinia();
if (pinia) {
  const cartStore = useCartStore();
} else {
  console.error('Pinia not initialized');
}
```

### Approach C: Re-export Store from User App
```typescript
// user/vue/src/stores/cart.ts
import { useCartStore as useCartStoreCore } from '@vbwd/view-component';
export const useCartStore = useCartStoreCore;
```

### Approach D: Pass Pinia Instance Explicitly
```typescript
// In core library
export function createCartStoreWithPinia(pinia: Pinia) {
  return defineStore('cart', () => { ... })(pinia);
}

// In user app
import { createCartStoreWithPinia } from '@vbwd/view-component';
const cartStore = createCartStoreWithPinia(pinia);
```

## Test Commands

```bash
# Run individual test suites
cd vbwd-frontend && docker run --rm --network=host \
  -v "$PWD/user:/app" -v "$PWD/core:/core" -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/tokens-page.spec.ts --config=playwright.docker.config.ts"

# Run all Sprint 03/04 tests
cd vbwd-frontend && docker run --rm --network=host \
  -v "$PWD/user:/app" -v "$PWD/core:/core" -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/tokens-page.spec.ts vue/tests/e2e/addons-page.spec.ts vue/tests/e2e/cart.spec.ts --config=playwright.docker.config.ts"
```

## Acceptance Criteria

| Criterion | Current | Target |
|-----------|---------|--------|
| tokens-page.spec.ts | 6/7 | 7/7 |
| addons-page.spec.ts | 9/10 | 10/10 |
| cart.spec.ts | 0/12 | 12/12 |
| **Total** | **15/29** | **29/29** |

## Files to Modify

| File | Changes |
|------|---------|
| `user/vue/src/layouts/UserLayout.vue` | Re-enable cart store import |
| `user/vue/src/views/Tokens.vue` | Re-enable cart store import |
| `user/vue/src/views/AddOns.vue` | Re-enable cart store import |
| `core/src/stores/cart.ts` | Possible fixes based on diagnosis |
| `core/vite.config.ts` | Possible build config changes |

## Principles

- **TDD:** Tests already written, implement to make them pass
- **SOLID:** Single responsibility - cart store handles cart logic only
- **DRY:** Shared cart store in core library
- **No Over-engineering:** Simplest fix that makes tests pass
- **Clean Code:** Clear imports, no hacks

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Fix breaks other functionality | Run full E2E suite after changes |
| Multiple approaches needed | Time-box each approach to 30 min |
| Core library change breaks admin | Test admin app after core changes |

## Definition of Done

1. All 29 E2E tests pass
2. Cart functionality works end-to-end
3. No regressions in existing tests
4. Code follows project patterns
5. Changes documented in sprint report
