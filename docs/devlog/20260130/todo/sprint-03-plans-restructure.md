# Sprint 03: Plans Page Restructure

**Date:** 2026-01-30
**Status:** TODO

## Objective

Restructure the plans/checkout flow to separate token bundles and add-ons into dedicated pages while maintaining inline access from the plans page.

## New Page Structure

```
/plans                 → Plans overview with inline token bundles & add-ons sections
/tokens                → Dedicated token bundles page
/add-ons               → Dedicated add-ons page (split by subscription dependency)
/checkout/:planSlug    → Existing checkout flow
```

## Requirements

### 1. `/plans` Page Enhancement
- Keep existing plan cards
- Add collapsible section for token bundles preview
- Add collapsible section for add-ons preview
- Add "View All" links to `/tokens` and `/add-ons`

### 2. `/tokens` Page (NEW)
- Display all available token bundles
- Grid/card layout matching plans page style
- Token amount, price, description
- "Add to Cart" or "Purchase" button
- Back to plans navigation

### 3. `/add-ons` Page (NEW)
Split into two blocks based on `conditions.subscription_parent`:

**Block 1: Subscription-Dependent Add-ons**
- Add-ons where `subscription_parent` = specific subscription ID
- Requires active subscription to purchase
- Shows which subscription(s) they apply to

**Block 2: Subscription-Independent Add-ons**
- Add-ons where `subscription_parent` = null
- Available to all users
- Affects all subscriptions or account-wide

### 4. Backend Changes (if needed)
- Verify add-ons API returns `conditions` field
- Add filter parameters for add-on type
- May need new endpoint: `GET /api/v1/add-ons?scope=subscription|global`

## Principles

- **TDD:** Write E2E tests for new pages first
- **SOLID:** Each page component has single responsibility
- **DRY:** Reuse existing card/grid components
- **Clean Code:** Consistent naming, clear component structure
- **No Over-engineering:** Simple navigation, no complex state management

## Technical Approach

### Frontend Components

```
src/views/
├── Plans.vue           # Enhanced with sections
├── Tokens.vue          # NEW - token bundles page
└── AddOns.vue          # NEW - add-ons page with blocks

src/components/
├── plans/
│   ├── PlanCard.vue           # Existing
│   ├── TokenBundleCard.vue    # NEW or reuse from checkout
│   └── AddOnCard.vue          # NEW or reuse from checkout
└── shared/
    └── SectionHeader.vue      # "Token Bundles" with "View All" link
```

### Router Updates

```typescript
// src/router/index.ts
{
  path: '/tokens',
  name: 'tokens',
  component: () => import('../views/Tokens.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/add-ons',
  name: 'add-ons',
  component: () => import('../views/AddOns.vue'),
  meta: { requiresAuth: true }
}
```

### Add-on Filtering Logic

```typescript
// Pseudo-code for add-on categorization
const subscriptionDependent = addons.filter(a =>
  a.conditions?.subscription_parent !== null
);

const subscriptionIndependent = addons.filter(a =>
  a.conditions?.subscription_parent === null
);
```

## TDD: E2E Tests First

### Test File: `tokens-page.spec.ts`
```typescript
test.describe('Tokens Page', () => {
  test('displays available token bundles', async ({ page }) => {
    await page.goto('/tokens');
    await expect(page.locator('[data-testid="token-bundle-card"]')).toHaveCount.above(0);
  });

  test('shows token amount and price', async ({ page }) => {
    await page.goto('/tokens');
    await expect(page.locator('[data-testid="token-amount"]').first()).toBeVisible();
    await expect(page.locator('[data-testid="token-price"]').first()).toBeVisible();
  });

  test('can navigate back to plans', async ({ page }) => {
    await page.goto('/tokens');
    await page.click('[data-testid="back-to-plans"]');
    await expect(page).toHaveURL('/plans');
  });
});
```

### Test File: `addons-page.spec.ts`
```typescript
test.describe('Add-ons Page', () => {
  test('displays subscription-dependent add-ons block', async ({ page }) => {
    await page.goto('/add-ons');
    await expect(page.locator('[data-testid="subscription-addons-section"]')).toBeVisible();
  });

  test('displays subscription-independent add-ons block', async ({ page }) => {
    await page.goto('/add-ons');
    await expect(page.locator('[data-testid="global-addons-section"]')).toBeVisible();
  });

  test('shows add-on details', async ({ page }) => {
    await page.goto('/add-ons');
    const card = page.locator('[data-testid^="addon-card-"]').first();
    await expect(card.locator('[data-testid="addon-name"]')).toBeVisible();
    await expect(card.locator('[data-testid="addon-price"]')).toBeVisible();
  });
});
```

## Sprint Tasks

| # | Task | Files | Effort |
|---|------|-------|--------|
| 1 | Write E2E tests for /tokens page | `tests/e2e/tokens-page.spec.ts` | S |
| 2 | Write E2E tests for /add-ons page | `tests/e2e/addons-page.spec.ts` | S |
| 3 | Create Tokens.vue page | `src/views/Tokens.vue` | M |
| 4 | Create AddOns.vue page with blocks | `src/views/AddOns.vue` | M |
| 5 | Add routes to router | `src/router/index.ts` | S |
| 6 | Enhance Plans.vue with sections | `src/views/Plans.vue` | M |
| 7 | Verify/update backend API | Backend if needed | S |
| 8 | Run E2E tests (GREEN) | - | S |

## Test Commands

```bash
# Run tokens page tests
cd vbwd-frontend && docker run --rm --network=host \
  -v "$PWD/user:/app" -v "$PWD/core:/core" -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/tokens-page.spec.ts --config=playwright.docker.config.ts"

# Run add-ons page tests
cd vbwd-frontend && docker run --rm --network=host \
  -v "$PWD/user:/app" -v "$PWD/core:/core" -w /app \
  mcr.microsoft.com/playwright:v1.57.0-jammy \
  sh -c "npm install --silent && npx playwright test vue/tests/e2e/addons-page.spec.ts --config=playwright.docker.config.ts"
```

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| `/tokens` page displays token bundles | ⬜ |
| `/add-ons` page displays two blocks | ⬜ |
| Subscription-dependent add-ons in first block | ⬜ |
| Subscription-independent add-ons in second block | ⬜ |
| `/plans` has links to both new pages | ⬜ |
| Navigation between pages works | ⬜ |
| All E2E tests pass | ⬜ |
| No TypeScript errors | ⬜ |
| No ESLint errors | ⬜ |

## Files to Create/Modify

| File | Action |
|------|--------|
| `vbwd-frontend/user/vue/src/views/Tokens.vue` | CREATE |
| `vbwd-frontend/user/vue/src/views/AddOns.vue` | CREATE |
| `vbwd-frontend/user/vue/src/router/index.ts` | MODIFY |
| `vbwd-frontend/user/vue/src/views/Plans.vue` | MODIFY |
| `vbwd-frontend/user/vue/tests/e2e/tokens-page.spec.ts` | CREATE |
| `vbwd-frontend/user/vue/tests/e2e/addons-page.spec.ts` | CREATE |

## Clarified Requirements

1. ✅ Tokens can be purchased without subscription
2. ✅ "Purchase" action adds item to cart (not direct checkout)
3. ✅ Cart system: Pinia store + localStorage persistence

## Additional Scope: Shopping Cart

### Cart in Shared Library (view_component)

Following DRY, SOLID, Liskov principles - cart goes in `vbwd-frontend/core/` for reuse by both admin and user apps.

**Location:** `vbwd-frontend/core/src/`

#### Cart Store (`stores/cart.ts`)

```typescript
// Interface following Liskov - any cart item type can be substituted
interface ICartItem {
  type: 'plan' | 'token_bundle' | 'addon';
  id: string;
  name: string;
  price: number;
  quantity: number;
  metadata?: Record<string, unknown>; // Extensible for app-specific data
}

// Factory function for DI - allows injecting custom storage
export function createCartStore(storageKey = 'vbwd_cart') {
  return defineStore('cart', {
    state: () => ({
      items: [] as ICartItem[],
    }),
    getters: {
      itemCount: (state) => state.items.reduce((sum, i) => sum + i.quantity, 0),
      total: (state) => state.items.reduce((sum, i) => sum + i.price * i.quantity, 0),
      isEmpty: (state) => state.items.length === 0,
    },
    actions: {
      addItem(item: Omit<ICartItem, 'quantity'>) { /* ... */ },
      removeItem(id: string) { /* ... */ },
      updateQuantity(id: string, quantity: number) { /* ... */ },
      clearCart() { /* ... */ },
    },
    // Persistence via localStorage
    persist: { key: storageKey },
  });
}

// Default export for simple usage
export const useCartStore = createCartStore();
```

#### Cart Components (`components/cart/`)

```
core/src/components/cart/
├── CartIcon.vue           # Header icon with badge (uses slot for custom icon)
├── CartDropdown.vue       # Dropdown with item list
├── CartItem.vue           # Single item row (slot for custom actions)
├── CartEmpty.vue          # Empty state component
├── index.ts               # Exports all cart components
└── types.ts               # Cart-specific types
```

#### Export from Core (`index.ts`)

```typescript
// stores
export { useCartStore, createCartStore, type ICartItem } from './stores/cart';

// components
export { CartIcon, CartDropdown, CartItem, CartEmpty } from './components/cart';
```

### Usage in Apps

**User App:**
```typescript
import { useCartStore, CartIcon, CartDropdown } from '@vbwd/view-component';

const cart = useCartStore();
cart.addItem({ type: 'token_bundle', id: '123', name: '1000 Tokens', price: 10 });
```

**Admin App (if needed):**
```typescript
import { useCartStore } from '@vbwd/view-component';
// Same API, shared implementation
```

### Cart Flow

```
/tokens → "Add to Cart" → Cart icon updates → User can:
  - Continue shopping
  - Click cart icon → View cart dropdown
  - Click "Checkout" → Navigate to /checkout with cart items
```

## Updated Sprint Tasks

### Phase 1: Core Library (Shared Components) - COMPLETED

| # | Task | Location | Status |
|---|------|----------|--------|
| 1 | Write unit tests for cart store | `core/tests/stores/cart.spec.ts` | ✅ 26 tests |
| 2 | Create cart Pinia store with persistence | `core/src/stores/cart.ts` | ✅ |
| 3 | Create CartIcon component | `core/src/components/cart/CartIcon.vue` | ✅ |
| 4 | Create CartItem component | `core/src/components/cart/CartItem.vue` | ✅ |
| 5 | Create CartDropdown component | `core/src/components/cart/CartDropdown.vue` | ✅ |
| 6 | Create CartEmpty component | `core/src/components/cart/CartEmpty.vue` | ✅ |
| 7 | Export from core index.ts | `core/src/index.ts` | ✅ |
| 8 | Rebuild core package | `core/` | ✅ |

### Phase 2: User App Pages - IN PROGRESS

| # | Task | Location | Status |
|---|------|----------|--------|
| 9 | Write E2E tests for /tokens page | `user/tests/e2e/tokens-page.spec.ts` | ✅ |
| 10 | Write E2E tests for /add-ons page | `user/tests/e2e/addons-page.spec.ts` | ✅ |
| 11 | Write E2E tests for cart | `user/tests/e2e/cart.spec.ts` | ✅ |
| 12 | Create Tokens.vue page | `user/src/views/Tokens.vue` | ✅ |
| 13 | Create AddOns.vue page | `user/src/views/AddOns.vue` | ✅ |
| 14 | Add routes to router | `user/src/router/index.ts` | ✅ |
| 15 | Add cart to header layout | `user/src/layouts/UserLayout.vue` | ✅ |
| 16 | Enhance Plans.vue with sections | `user/src/views/Plans.vue` | ⬜ TODO |

### Phase 3: Integration

| # | Task | Location | Status |
|---|------|----------|--------|
| 17 | Update Checkout to use cart | `user/src/views/Checkout.vue` | ⬜ TODO |
| 18 | Run E2E tests (GREEN) | - | 🔶 Partial |

## Test Results (2026-01-30)

### Tokens Page: 6/7 tests passing
- ✅ displays page title
- ✅ displays available token bundles
- ✅ shows token amount for each bundle
- ✅ shows price for each bundle
- ❌ can add token bundle to cart (cart disabled)
- ✅ can navigate back to plans
- ✅ can navigate to plans via breadcrumb

### Add-ons Page: 9/10 tests passing
- ✅ displays page title
- ✅ displays subscription-dependent add-ons section
- ✅ displays subscription-independent add-ons section
- ✅ shows section headers
- ✅ displays add-on cards with name
- ✅ displays add-on cards with price
- ✅ displays add-on cards with description
- ❌ can add add-on to cart (cart disabled)
- ✅ can navigate back to plans
- ✅ subscription-dependent section shows info when no subscription

### Cart Tests: 0/12 tests passing (cart functionality disabled)

## Known Issue: Cart Store Import

The cart store from `@vbwd/view-component` cannot be imported in the user app without breaking the Vue app rendering. Investigation revealed:

1. Core package correctly externalizes Pinia in vite.config.ts
2. Cart store unit tests pass in the core package (26/26)
3. Importing `useCartStore` in UserLayout.vue or page components causes the Vue app to fail to render

**Workaround:** Cart store import is temporarily disabled. Pages work correctly without cart integration.

**Next Steps:**
1. Debug the Pinia instance sharing between core library and user app
2. Check if the issue is with how the store is registered at module load time
3. Consider lazy loading the cart store or using a different initialization pattern
