# Sprint 03: Checkout Page Integration

**Priority:** HIGH
**Estimated Effort:** Medium
**Dependencies:** Sprint 01, Sprint 02

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Session Token Integration** | Hybrid: Guests get session token, logged-in users use auth token + session for cart tracking |
| **Block Order** | Email → Billing → Payment → Terms (standard e-commerce flow) |

### Session Token Flow

```
Guest User:
  /plans → Click plan → Create checkout session (anonymous token) → /checkout/:plan
  Session stored in Redis with plan_slug, cart items, expires 30min

Logged-in User:
  /plans → Click plan → Create checkout session (JWT-based) → /checkout/:plan
  Session linked to user_id, preserves cart across sessions
```

---

## Core Requirements

This sprint follows our development standards:

| Requirement | Description |
|-------------|-------------|
| **TDD-first** | Write failing tests BEFORE production code |
| **SOLID** | Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion |
| **DRY** | Don't Repeat Yourself - reuse existing code and patterns |
| **Clean Code** | Readable, maintainable, self-documenting code |
| **No Over-engineering** | Only implement what's needed NOW, no premature abstractions |

---

## Objective
Integrate EmailBlock into Checkout.vue and enable guest checkout flow (allow unauthenticated users to access /checkout).

---

## TDD Phase 1: Write Failing E2E Tests FIRST

### 1.1 E2E Tests for Guest Checkout Flow

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-guest-flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Guest Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
  });

  test('allows access to checkout page without auth', async ({ page }) => {
    await page.goto('/checkout/pro');

    // Should NOT redirect to login
    await expect(page).toHaveURL(/\/checkout\/pro/);

    // Should show email block
    await expect(page.locator('[data-testid="email-block"]')).toBeVisible();
  });

  test('shows all checkout blocks in correct order', async ({ page }) => {
    await page.goto('/checkout/pro');

    // Verify block order
    const blocks = page.locator('[data-testid$="-block"]');
    await expect(blocks).toHaveCount(4); // email, billing, payment, order-summary
  });

  test('disables proceed without authentication', async ({ page }) => {
    await page.goto('/checkout/pro');

    // Pay button should be disabled without auth
    await expect(page.locator('[data-testid="pay-button"]')).toBeDisabled();
  });

  test('enables proceed after authentication', async ({ page }) => {
    // Mock APIs
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: false } });
    });
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({ json: { success: true, token: 'test-token', user_id: 'user-123' } });
    });
    await page.route('**/api/v1/tarif-plans/**', async (route) => {
      await route.fulfill({
        json: { id: 'plan-1', name: 'Pro', slug: 'pro', price: 29, billing_period: 'monthly' }
      });
    });

    await page.goto('/checkout/pro');

    // Register as new user
    await page.fill('[data-testid="email-input"]', 'new@example.com');
    await page.waitForSelector('[data-testid="email-new-user"]');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="signup-button"]');

    // Wait for authentication success
    await page.waitForSelector('[data-testid="email-block-success"]');

    // Now form fields should be accessible
    await expect(page.locator('[data-testid="email-block-success"]')).toBeVisible();
  });

  test('preserves selected plan during auth flow', async ({ page }) => {
    await page.route('**/api/v1/tarif-plans/pro', async (route) => {
      await route.fulfill({
        json: { id: 'plan-1', name: 'Pro Plan', slug: 'pro', price: 29.99, billing_period: 'monthly' }
      });
    });

    await page.goto('/checkout/pro');

    // Plan should be loaded even without auth
    await expect(page.locator('[data-testid="plan-name"]')).toContainText('Pro');
  });
});
```

### 1.2 E2E Tests for Authenticated User Flow

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-authed-flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../fixtures/checkout.fixtures';

test.describe('Authenticated Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('shows email block in success state for logged in user', async ({ page }) => {
    await page.goto('/checkout/pro');

    // Email block should show logged-in state
    await expect(page.locator('[data-testid="email-block-success"]')).toBeVisible();
  });

  test('auto-fills email for logged in user', async ({ page }) => {
    await page.goto('/checkout/pro');

    // Email should be pre-filled
    await expect(page.locator('[data-testid="email-block"]')).toContainText('test@example.com');
  });

  test('allows checkout submission for logged in user', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    // Confirm button should be available
    await expect(page.locator('[data-testid="confirm-checkout"]')).toBeEnabled();
  });
});
```

---

## TDD Phase 2: Write Minimal Production Code

### 2.1 Update Router - Allow Guest Checkout

**File:** `vbwd-frontend/user/vue/src/router/index.ts`

```typescript
// Change checkout route meta
{
  path: '/checkout/:planSlug',
  name: 'checkout',
  component: () => import('../views/Checkout.vue'),
  meta: { requiresAuth: false }  // Changed from true to false
}
```

### 2.2 Update Checkout.vue

**File:** `vbwd-frontend/user/vue/src/views/Checkout.vue`

```vue
<template>
  <div class="checkout">
    <h1>Checkout</h1>

    <!-- Loading State -->
    <div v-if="store.loading" class="loading-state" data-testid="checkout-loading">
      <div class="spinner" />
      <p>Loading plan details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error && !store.checkoutResult" class="error-state" data-testid="checkout-error">
      <p>{{ store.error }}</p>
      <router-link to="/plans" class="btn secondary">Back to Plans</router-link>
    </div>

    <!-- Checkout Success (existing code) -->
    <div v-else-if="store.checkoutResult" class="checkout-success" data-testid="checkout-success">
      <!-- ... existing success template ... -->
    </div>

    <!-- Checkout Form -->
    <div v-else-if="store.plan" class="checkout-content">
      <!-- Step 1: Email Block (NEW) -->
      <EmailBlock
        :initial-email="userEmail"
        :is-authenticated="isAuthenticated"
        @authenticated="handleAuthenticated"
        class="checkout-block"
      />

      <!-- Order Summary (moved/existing) -->
      <div class="card order-summary" data-testid="order-summary">
        <!-- ... existing order summary ... -->
      </div>

      <!-- Token Bundles (existing) -->
      <div v-if="store.availableBundles.length > 0" class="card" data-testid="token-bundles-section">
        <!-- ... existing bundles ... -->
      </div>

      <!-- Add-ons (existing) -->
      <div v-if="store.availableAddons.length > 0" class="card" data-testid="addons-section">
        <!-- ... existing addons ... -->
      </div>

      <!-- Confirm Section (updated) -->
      <div class="checkout-actions">
        <router-link to="/plans" class="btn secondary">Back to Plans</router-link>
        <button
          data-testid="confirm-checkout"
          class="btn primary"
          :disabled="!canCheckout"
          @click="store.submitCheckout"
        >
          {{ store.submitting ? 'Processing...' : 'Confirm Purchase' }}
        </button>
      </div>

      <div v-if="store.error" data-testid="checkout-error" class="error-message">
        {{ store.error }}
      </div>
    </div>

    <!-- No Plan -->
    <div v-else class="no-plan">
      <p>No plan selected.</p>
      <router-link to="/plans" class="btn primary">Browse Plans</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useCheckoutStore } from '@/stores/checkout';
import { isAuthenticated as checkAuth } from '@/api';
import EmailBlock from '@/components/checkout/EmailBlock.vue';

const route = useRoute();
const router = useRouter();
const store = useCheckoutStore();

// Auth state
const isAuthenticated = ref(checkAuth());
const userEmail = ref('');
const authenticatedUserId = ref<string | null>(null);

// Computed
const canCheckout = computed(() => {
  return isAuthenticated.value && !store.submitting;
});

// Handle authentication from EmailBlock
const handleAuthenticated = (userId: string) => {
  authenticatedUserId.value = userId;
  isAuthenticated.value = true;
};

// Load user email if authenticated
const loadUserEmail = async () => {
  if (isAuthenticated.value) {
    try {
      // Could fetch from profile store or API
      // For now, extract from token or use placeholder
      userEmail.value = localStorage.getItem('user_email') || '';
    } catch {
      // Ignore
    }
  }
};

onMounted(async () => {
  const planSlug = route.params.planSlug as string;
  if (planSlug) {
    await store.loadPlan(planSlug);
    await store.loadOptions();
  }
  await loadUserEmail();
});

onUnmounted(() => {
  store.reset();
});

// ... existing helper functions ...
</script>
```

### 2.3 Update Checkout Store (if needed)

**File:** `vbwd-frontend/user/vue/src/stores/checkout.ts`

```typescript
// Add to checkout store if not already present

// Add user_id to checkout submission
async function submitCheckout() {
  if (!plan.value) return;

  submitting.value = true;
  error.value = null;

  try {
    const response = await api.post('/user/checkout', {
      plan_id: plan.value.id,
      token_bundle_ids: selectedBundles.value.map(b => b.id),
      add_on_ids: selectedAddons.value.map(a => a.id),
      currency: 'USD',
    });

    checkoutResult.value = response;
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Checkout failed';
  } finally {
    submitting.value = false;
  }
}
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | EmailBlock handles auth, Checkout handles order |
| **O** - Open/Closed | Checkout accepts EmailBlock via slot/component |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | EmailBlock emits single event |
| **D** - Dependency Inversion | Store injected, not instantiated |

## No Over-engineering

- Reuse existing Checkout.vue structure
- EmailBlock is self-contained
- No new state management library
- Minimal route changes

---

## Verification Checklist

- [ ] E2E tests written and FAILING
- [ ] Router updated (requiresAuth: false)
- [ ] EmailBlock integrated into Checkout.vue
- [ ] canCheckout computed property added
- [ ] All tests PASSING
- [ ] Existing checkout tests still pass
- [ ] Manual browser test

## Run Tests

> **All tests run in Docker containers.** Run commands from `vbwd-frontend/` directory.

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# From vbwd-frontend/user/vue/
npm run test:e2e -- checkout/                    # All checkout tests
npm run test:e2e -- checkout-guest-flow.spec.ts  # Guest flow
npm run test:e2e -- checkout-authed-flow.spec.ts # Authenticated flow

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!

# Full regression
npm run test && npm run test:e2e
```

## Regression Check
Ensure existing tests in `plan-switching.spec.ts` still pass - they use `loginAsTestUser` so should continue working.
