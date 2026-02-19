# Sprint 03 Progress Report: Plans Page Restructure

**Date:** 2026-01-30
**Sprint:** 03 - Plans Page Restructure
**Status:** In Progress (Phase 2 Complete)

## Executive Summary

Sprint 03 aims to restructure the plans/checkout flow by adding dedicated `/tokens` and `/add-ons` pages with a shopping cart system. Today's work completed the core cart store implementation and both new pages, achieving 15/29 E2E tests passing. A Pinia store integration issue is blocking cart functionality.

## Objectives

1. Create shopping cart store in shared `@vbwd/view-component` library
2. Create `/tokens` page for token bundle purchases
3. Create `/add-ons` page with subscription-dependent/independent sections
4. Integrate cart into user app layout

## Completed Work

### Phase 1: Core Library (Complete)

#### Cart Store (`core/src/stores/cart.ts`)
- **26 unit tests passing**
- Pinia store with setup function syntax
- localStorage persistence with `vbwd_cart` key
- Full CRUD operations: `addItem`, `removeItem`, `updateQuantity`, `clearCart`
- Getters: `itemCount`, `total`, `isEmpty`, `getItemById`, `getItemsByType`
- Factory function `createCartStore()` for custom instances

```typescript
interface ICartItem {
  type: 'plan' | 'token_bundle' | 'addon';
  id: string;
  name: string;
  price: number;
  quantity: number;
  metadata?: Record<string, unknown>;
}
```

#### Cart UI Components (`core/src/components/cart/`)
| Component | Description |
|-----------|-------------|
| `CartIcon.vue` | Header icon with badge counter |
| `CartItem.vue` | Single item row with quantity controls |
| `CartEmpty.vue` | Empty state message |
| `CartDropdown.vue` | Full dropdown with items and checkout |

### Phase 2: User App Pages (Complete)

#### Tokens Page (`/tokens`)
**6/7 E2E tests passing**

| Test | Status |
|------|--------|
| displays page title | ✅ |
| displays available token bundles | ✅ |
| shows token amount for each bundle | ✅ |
| shows price for each bundle | ✅ |
| can add token bundle to cart | ❌ (cart disabled) |
| can navigate back to plans | ✅ |
| can navigate to plans via breadcrumb | ✅ |

**Features:**
- Fetches token bundles from `/api/v1/token-bundles`
- Grid layout with responsive cards
- Price formatting with currency support
- Loading/error states
- Breadcrumb navigation

#### Add-ons Page (`/add-ons`)
**9/10 E2E tests passing**

| Test | Status |
|------|--------|
| displays page title | ✅ |
| displays subscription-dependent add-ons section | ✅ |
| displays subscription-independent add-ons section | ✅ |
| shows section headers | ✅ |
| displays add-on cards with name | ✅ |
| displays add-on cards with price | ✅ |
| displays add-on cards with description | ✅ |
| can add add-on to cart | ❌ (cart disabled) |
| can navigate back to plans | ✅ |
| subscription-dependent section shows info | ✅ |

**Features:**
- Two sections based on `conditions.subscription_parent`
- Subscription-dependent add-ons require active subscription
- Global add-ons available to all users
- Fetches add-ons from `/api/v1/addons`
- Checks subscription status for eligibility

#### Layout Updates
- Added cart icon to sidebar footer
- Added "Tokens" and "Add-ons" nav links
- Cart dropdown (visual only, functionality disabled)

#### Router Updates
```typescript
{ path: '/tokens', name: 'tokens', component: Tokens.vue }
{ path: '/add-ons', name: 'add-ons', component: AddOns.vue }
{ path: '/checkout/cart', name: 'checkout-cart', component: Checkout.vue }
```

## Known Issue: Pinia Store Integration

### Problem
Importing `useCartStore` from `@vbwd/view-component` causes the Vue app to fail to render completely. The page loads but Vue components don't mount.

### Investigation
1. Core library correctly externalizes Pinia in `vite.config.ts`
2. Cart store unit tests pass (26/26) in isolation
3. User app creates Pinia instance correctly
4. Import fails silently - no console errors visible

### Symptoms
- Page shows blank content area
- Sidebar renders (when cart import removed from layout)
- No JavaScript errors in browser console
- Vue app `#app` div remains empty

### Workaround
Cart store import disabled in:
- `UserLayout.vue` - uses mock object
- `Tokens.vue` - `addToCart` logs to console
- `AddOns.vue` - `addToCart` logs to console

### Suspected Causes
1. Pinia instance not shared correctly between packages
2. Store initialization timing (module load vs component mount)
3. Possible circular dependency in core library exports

## Test Results Summary

| Test Suite | Passing | Failing | Total |
|------------|---------|---------|-------|
| Cart Store (Unit) | 26 | 0 | 26 |
| Tokens Page (E2E) | 6 | 1 | 7 |
| Add-ons Page (E2E) | 9 | 1 | 10 |
| Cart (E2E) | 0 | 12 | 12 |
| **E2E Total** | **15** | **14** | **29** |

## Files Created/Modified

### Created
| File | Purpose |
|------|---------|
| `core/src/stores/cart.ts` | Cart Pinia store |
| `core/tests/stores/cart.spec.ts` | Cart unit tests |
| `core/src/components/cart/CartIcon.vue` | Cart icon component |
| `core/src/components/cart/CartItem.vue` | Cart item component |
| `core/src/components/cart/CartEmpty.vue` | Empty state component |
| `core/src/components/cart/CartDropdown.vue` | Dropdown component |
| `core/src/components/cart/index.ts` | Cart exports |
| `user/vue/src/views/Tokens.vue` | Tokens page |
| `user/vue/src/views/AddOns.vue` | Add-ons page |
| `user/vue/tests/e2e/tokens-page.spec.ts` | Tokens E2E tests |
| `user/vue/tests/e2e/addons-page.spec.ts` | Add-ons E2E tests |
| `user/vue/tests/e2e/cart.spec.ts` | Cart E2E tests |

### Modified
| File | Changes |
|------|---------|
| `core/src/stores/index.ts` | Export cart store |
| `core/src/components/index.ts` | Export cart components |
| `user/vue/src/router/index.ts` | Add new routes |
| `user/vue/src/layouts/UserLayout.vue` | Add cart icon, nav links |

## Next Steps

### Phase 3: Integration (Remaining)
1. **Debug Pinia Integration**
   - Test store sharing with simple counter store
   - Check for circular dependencies in core exports
   - Try lazy loading store in components
   - Consider using `storeToRefs` pattern

2. **Enable Cart Functionality**
   - Re-enable cart store imports
   - Connect add-to-cart buttons
   - Verify cart persistence across pages

3. **Update Checkout**
   - Read cart items on checkout page
   - Support cart-based checkout (no plan required)
   - Clear cart after successful checkout

4. **Plans Page Enhancement**
   - Add inline token bundles section
   - Add inline add-ons section
   - Add "View All" links to new pages

## Technical Notes

### API Endpoints Used
- `GET /api/v1/token-bundles` - Returns `{ bundles: TokenBundle[] }`
- `GET /api/v1/addons` - Returns `{ addons: AddOn[] }`
- `GET /api/v1/user/subscription` - Returns subscription status

### Price Handling
Backend returns prices as strings (e.g., `"10.00"`). Frontend parses to number for formatting:
```typescript
const numPrice = typeof price === 'string' ? parseFloat(price) : price;
```

### Add-on Categorization
```typescript
// Subscription-dependent
addon.conditions?.subscription_parent !== null

// Global (subscription-independent)
!addon.conditions?.subscription_parent
```

## Conclusion

Sprint 03 has made significant progress with pages and cart store complete. The main blocker is the Pinia store integration issue preventing cart functionality. Once resolved, enabling cart features should be straightforward as all the infrastructure is in place.

**Estimated Remaining Effort:**
- Pinia debugging: Investigation needed
- Cart integration: Small once Pinia fixed
- Checkout updates: Medium
- Plans page enhancement: Medium
