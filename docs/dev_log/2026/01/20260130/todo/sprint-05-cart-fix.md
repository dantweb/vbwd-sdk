# Sprint 05: Cart Integration Fix

**Date:** 2026-01-30
**Status:** TODO
**Prerequisite:** Sprint 03 complete (pages done), Sprint 04 attempted (lazy loading)

## Objective

Fix all 11 failing E2E tests by resolving the Pinia store reactivity issue between the core library and user app.

## Current Test Status

| Test Suite | Passing | Failing | Total |
|------------|---------|---------|-------|
| tokens-page.spec.ts | 6 | 1 | 7 |
| addons-page.spec.ts | 9 | 1 | 10 |
| cart.spec.ts | 3 | 9 | 12 |
| **Total** | **18** | **11** | **29** |

## Root Cause Analysis

### Problem
The cart store from `@vbwd/view-component` is imported via dynamic import (lazy loading) in both `UserLayout.vue` and `Tokens.vue`/`AddOns.vue`. While both components call `useCartStore()`, the reactivity chain is broken:

1. **Tokens.vue** calls `useCartStore()` and `addItem()` - item IS added to the store
2. **UserLayout.vue** calls `useCartStore()` - gets the SAME store instance
3. BUT: The local refs in UserLayout (`cartItemCountRef`, etc.) don't update when the store changes

### Why Sprint 04 Approach Failed
The `watch()` calls in UserLayout.vue watch the Pinia store's refs, but:
- The watches are set up AFTER onMounted completes
- When Tokens.vue adds an item, the store updates
- BUT UserLayout's watches might not be properly connected due to timing

### Evidence
- Cart data IS saved to localStorage (store works)
- Cart count badge never appears (reactivity broken)
- Same behavior across all cart tests

## Solution Options

### Option A: Direct Store Reference (Recommended)
Instead of copying store values to local refs, use the store directly in the template.

**Approach:**
1. Store the Pinia store instance in a reactive ref
2. Access store properties directly in template: `store?.items`, `store?.itemCount`
3. Use optional chaining for null safety before store loads

### Option B: Provide/Inject Pattern
Create the store at app level and inject it into components.

**Approach:**
1. Create store in App.vue and provide it
2. Inject store in UserLayout.vue and page components
3. Ensures single instance and proper reactivity

### Option C: Global Cart Composable
Create a composable in the user app that wraps the core library store.

**Approach:**
1. Create `useCart()` composable in user app
2. Import and instantiate core library store once
3. Export reactive refs that all components share

### Option D: Synchronous Store Import
Import the store synchronously at module level (original approach that broke rendering).

**Approach:**
1. Investigate WHY the original import broke rendering
2. Fix the root cause (possibly circular dependency or SSR issue)
3. Use simple synchronous import

## Chosen Approach: Option A

Direct store reference is the simplest fix with minimal code changes.

## Implementation Plan

### Phase 1: Fix UserLayout.vue

```typescript
// Instead of copying to local refs
const cartStore = shallowRef<ReturnType<typeof useCartStore> | null>(null);

onMounted(async () => {
  const { useCartStore } = await import('@vbwd/view-component');
  cartStore.value = useCartStore();
});

// In template, use optional chaining
// v-if="cartStore?.itemCount && cartStore.itemCount > 0"
// {{ cartStore?.itemCount }}
```

### Phase 2: Verify Tokens.vue and AddOns.vue

Ensure `addItem()` is called correctly and store is properly initialized.

### Phase 3: Run Tests

Verify all 29 tests pass.

## Sprint Tasks

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 1 | Refactor UserLayout.vue | Use direct store reference | S |
| 2 | Update template bindings | Use optional chaining for store access | S |
| 3 | Verify Tokens.vue | Confirm addToCart works | S |
| 4 | Verify AddOns.vue | Confirm addToCart works | S |
| 5 | Run tokens-page tests | Expect 7/7 | S |
| 6 | Run addons-page tests | Expect 10/10 | S |
| 7 | Run cart tests | Expect 12/12 | M |
| 8 | Full regression test | Run all E2E tests | S |

## Files to Modify

| File | Changes |
|------|---------|
| `user/vue/src/layouts/UserLayout.vue` | Simplify store usage with direct reference |
| `user/vue/src/views/Tokens.vue` | Verify addToCart implementation |
| `user/vue/src/views/AddOns.vue` | Verify addToCart implementation |

## Test Commands

```bash
# Run single test for quick feedback
cd vbwd-frontend && docker run --rm --network=host \
  -v "$PWD/user:/app" -v "$PWD/core:/core" -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/cart.spec.ts -g 'adding item updates cart count' --config=playwright.docker.config.ts"

# Run all cart-related tests
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
| cart.spec.ts | 3/12 | 12/12 |
| **Total** | **18/29** | **29/29** |

## Technical Notes

### Pinia Store Behavior
- `defineStore()` returns a function, not the store itself
- Calling `useCartStore()` returns the actual store instance
- Stores are singletons within a Pinia instance
- Dynamic imports don't affect store singleton behavior

### Vue Reactivity with Pinia
- Pinia stores are reactive by default
- `storeToRefs()` extracts refs that maintain reactivity
- Direct store access in templates is reactive
- `shallowRef` only tracks `.value` reassignment, not deep changes

### Key Insight
The issue is NOT with Pinia or the store. The issue is with how UserLayout.vue tries to "copy" store values to local refs instead of using the store directly.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Template errors with null store | Use optional chaining (?.) |
| Store not loaded before interaction | Show loading state or disable buttons |
| Breaking existing functionality | Run full test suite |

## Definition of Done

1. All 29 E2E tests pass
2. Cart icon shows count when items added
3. Cart dropdown displays items correctly
4. Cart persists across navigation and refresh
5. No TypeScript errors
6. No console errors in browser
