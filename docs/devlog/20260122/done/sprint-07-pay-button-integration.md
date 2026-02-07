# Sprint 07: Pay Button and Final Integration

**Priority:** HIGH
**Estimated Effort:** Medium
**Dependencies:** Sprints 03-06, Sprint 09

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **After Checkout** | Redirect to /success page with invoice details |
| **Error Display** | Inline error message below pay button, stay on checkout page |

### Success Page

After successful checkout:
1. Backend returns `{ invoice: { id, number, ... }, subscription: {...} }`
2. Frontend redirects to `/success?invoice={id}`
3. Success page displays:
   - "Thank you for your order!"
   - Invoice number and total
   - "What's next" section (email confirmation, payment instructions for invoice)
   - Link to download invoice PDF
   - Link to dashboard

### Error Handling

On checkout error:
1. Display inline error message below pay button
2. Keep user on checkout page (don't redirect)
3. Error message format: "Checkout failed: {error_message}"
4. Allow user to fix issues and retry

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
Integrate all checkout components (Email, Billing, Payment Methods, Terms) and implement the Pay button with conditional activation logic.

---

## TDD Phase 1: Write Failing E2E Tests FIRST

### 1.1 Full Checkout Flow Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-full-flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Full Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear auth for guest checkout tests
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());

    // Mock APIs
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: false } });
    });
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({ json: { success: true, token: 'test-token', user_id: 'user-123' } });
    });
    await page.route('**/api/v1/settings/payment-methods', async (route) => {
      await route.fulfill({
        json: { methods: [{ id: 'invoice', name: 'Invoice', description: 'Pay by invoice', enabled: true }] }
      });
    });
    await page.route('**/api/v1/settings/terms', async (route) => {
      await route.fulfill({ json: { title: 'Terms', content: 'Test terms content' } });
    });
    await page.route('**/api/v1/tarif-plans/pro', async (route) => {
      await route.fulfill({
        json: { id: 'plan-1', name: 'Pro', slug: 'pro', price: 29, billing_period: 'monthly' }
      });
    });
  });

  test('pay button disabled until all requirements met', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="email-block"]');

    // Initially disabled
    await expect(page.locator('[data-testid="pay-button"]')).toBeDisabled();
  });

  test('pay button shows requirements status', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="email-block"]');

    // Should show what's missing
    await expect(page.locator('[data-testid="checkout-requirements"]')).toBeVisible();
  });

  test('complete guest checkout flow', async ({ page }) => {
    await page.route('**/api/v1/user/checkout', async (route) => {
      await route.fulfill({
        json: {
          subscription: { id: 'sub-1', status: 'pending' },
          invoice: { id: 'inv-1', invoice_number: 'INV-001', total_amount: 29 }
        }
      });
    });
    await page.route('**/api/v1/user/billing-address', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: {} });
      } else {
        await route.fulfill({ json: { street: 'Test', city: 'Test', zip: '12345', country: 'DE' } });
      }
    });

    await page.goto('/checkout/pro');

    // 1. Register as new user
    await page.fill('[data-testid="email-input"]', 'new@example.com');
    await page.waitForSelector('[data-testid="email-new-user"]');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="signup-button"]');
    await page.waitForSelector('[data-testid="email-block-success"]');

    // 2. Fill billing address
    await page.fill('[data-testid="billing-street"]', '123 Test St');
    await page.fill('[data-testid="billing-city"]', 'Berlin');
    await page.fill('[data-testid="billing-zip"]', '10115');
    await page.selectOption('[data-testid="billing-country"]', 'DE');

    // 3. Select payment method
    await page.click('[data-testid="payment-method-invoice"]');

    // 4. Accept terms
    await page.click('[data-testid="terms-checkbox"]');

    // 5. Pay button should be enabled
    await expect(page.locator('[data-testid="pay-button"]')).toBeEnabled();

    // 6. Click pay
    await page.click('[data-testid="pay-button"]');

    // 7. Should show success
    await page.waitForSelector('[data-testid="checkout-success"]');
    await expect(page.locator('[data-testid="invoice-number"]')).toContainText('INV-');
  });

  test('validates all fields before submission', async ({ page }) => {
    await page.goto('/checkout/pro');

    // Register but don't fill other fields
    await page.fill('[data-testid="email-input"]', 'new@example.com');
    await page.waitForSelector('[data-testid="email-new-user"]');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="signup-button"]');
    await page.waitForSelector('[data-testid="email-block-success"]');

    // Pay button should still be disabled
    await expect(page.locator('[data-testid="pay-button"]')).toBeDisabled();

    // Requirements should show what's missing
    const reqs = page.locator('[data-testid="checkout-requirements"]');
    await expect(reqs).toContainText(/billing|address/i);
    await expect(reqs).toContainText(/payment/i);
    await expect(reqs).toContainText(/terms/i);
  });
});
```

---

## TDD Phase 2: Write Failing Unit Tests

### 2.1 Unit Test: canPay Computed

**File:** `vbwd-frontend/user/vue/tests/unit/stores/checkout.spec.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useCheckoutStore } from '@/stores/checkout';

describe('Checkout Store - canPay', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('returns false when not authenticated', () => {
    const store = useCheckoutStore();
    store.isAuthenticated = false;

    expect(store.canPay).toBe(false);
  });

  it('returns false when billing address incomplete', () => {
    const store = useCheckoutStore();
    store.isAuthenticated = true;
    store.billingAddress = { street: '', city: '', zip: '', country: '' };

    expect(store.canPay).toBe(false);
  });

  it('returns false when no payment method selected', () => {
    const store = useCheckoutStore();
    store.isAuthenticated = true;
    store.billingAddress = { street: 'Test', city: 'Test', zip: '12345', country: 'DE' };
    store.selectedPaymentMethod = null;

    expect(store.canPay).toBe(false);
  });

  it('returns false when terms not accepted', () => {
    const store = useCheckoutStore();
    store.isAuthenticated = true;
    store.billingAddress = { street: 'Test', city: 'Test', zip: '12345', country: 'DE' };
    store.selectedPaymentMethod = 'invoice';
    store.termsAccepted = false;

    expect(store.canPay).toBe(false);
  });

  it('returns true when all requirements met', () => {
    const store = useCheckoutStore();
    store.isAuthenticated = true;
    store.billingAddress = { street: 'Test', city: 'Test', zip: '12345', country: 'DE' };
    store.selectedPaymentMethod = 'invoice';
    store.termsAccepted = true;
    store.plan = { id: 'plan-1', name: 'Pro' };

    expect(store.canPay).toBe(true);
  });
});
```

---

## TDD Phase 3: Update Production Code

### 3.1 Update Checkout Store

**File:** `vbwd-frontend/user/vue/src/stores/checkout.ts`

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/api';

interface BillingAddress {
  street: string;
  city: string;
  zip: string;
  country: string;
}

interface CheckoutRequirements {
  authenticated: boolean;
  billingComplete: boolean;
  paymentSelected: boolean;
  termsAccepted: boolean;
}

export const useCheckoutStore = defineStore('checkout', () => {
  // Existing state
  const plan = ref<any>(null);
  const selectedBundles = ref<any[]>([]);
  const selectedAddons = ref<any[]>([]);
  const availableBundles = ref<any[]>([]);
  const availableAddons = ref<any[]>([]);
  const loading = ref(false);
  const submitting = ref(false);
  const error = ref<string | null>(null);
  const checkoutResult = ref<any>(null);

  // New state for enhanced checkout
  const isAuthenticated = ref(false);
  const billingAddress = ref<BillingAddress>({ street: '', city: '', zip: '', country: '' });
  const selectedPaymentMethod = ref<string | null>(null);
  const termsAccepted = ref(false);

  // Computed: Check if billing address is complete
  const isBillingComplete = computed(() => {
    const addr = billingAddress.value;
    return !!(addr.street && addr.city && addr.zip && addr.country);
  });

  // Computed: Requirements status
  const requirements = computed<CheckoutRequirements>(() => ({
    authenticated: isAuthenticated.value,
    billingComplete: isBillingComplete.value,
    paymentSelected: selectedPaymentMethod.value !== null,
    termsAccepted: termsAccepted.value,
  }));

  // Computed: Missing requirements list
  const missingRequirements = computed(() => {
    const missing: string[] = [];
    if (!requirements.value.authenticated) missing.push('Sign in or create account');
    if (!requirements.value.billingComplete) missing.push('Complete billing address');
    if (!requirements.value.paymentSelected) missing.push('Select payment method');
    if (!requirements.value.termsAccepted) missing.push('Accept terms and conditions');
    return missing;
  });

  // Computed: Can submit checkout
  const canPay = computed(() => {
    return (
      plan.value !== null &&
      isAuthenticated.value &&
      isBillingComplete.value &&
      selectedPaymentMethod.value !== null &&
      termsAccepted.value &&
      !submitting.value
    );
  });

  // Actions
  const setAuthenticated = (value: boolean) => {
    isAuthenticated.value = value;
  };

  const setBillingAddress = (address: BillingAddress) => {
    billingAddress.value = address;
  };

  const setPaymentMethod = (methodId: string) => {
    selectedPaymentMethod.value = methodId;
  };

  const setTermsAccepted = (accepted: boolean) => {
    termsAccepted.value = accepted;
  };

  // Existing methods
  const loadPlan = async (slug: string) => {
    loading.value = true;
    error.value = null;
    try {
      plan.value = await api.get(`/tarif-plans/${slug}`);
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to load plan';
    } finally {
      loading.value = false;
    }
  };

  const loadOptions = async () => {
    try {
      const [bundles, addons] = await Promise.all([
        api.get('/token-bundles').catch(() => ({ bundles: [] })),
        api.get('/addons').catch(() => ({ addons: [] })),
      ]);
      availableBundles.value = bundles.bundles || [];
      availableAddons.value = addons.addons || [];
    } catch {
      // Ignore - optional
    }
  };

  const submitCheckout = async () => {
    if (!canPay.value || !plan.value) return;

    submitting.value = true;
    error.value = null;

    try {
      // Save billing address first
      await api.put('/user/billing-address', billingAddress.value);

      // Submit checkout
      const response = await api.post('/user/checkout', {
        plan_id: plan.value.id,
        token_bundle_ids: selectedBundles.value.map(b => b.id),
        add_on_ids: selectedAddons.value.map(a => a.id),
        payment_method: selectedPaymentMethod.value,
        currency: 'USD',
      });

      checkoutResult.value = response;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Checkout failed';
    } finally {
      submitting.value = false;
    }
  };

  const reset = () => {
    plan.value = null;
    selectedBundles.value = [];
    selectedAddons.value = [];
    checkoutResult.value = null;
    error.value = null;
    billingAddress.value = { street: '', city: '', zip: '', country: '' };
    selectedPaymentMethod.value = null;
    termsAccepted.value = false;
  };

  // ... keep existing bundle/addon methods ...

  return {
    // State
    plan,
    selectedBundles,
    selectedAddons,
    availableBundles,
    availableAddons,
    loading,
    submitting,
    error,
    checkoutResult,
    isAuthenticated,
    billingAddress,
    selectedPaymentMethod,
    termsAccepted,

    // Computed
    canPay,
    isBillingComplete,
    requirements,
    missingRequirements,

    // Actions
    loadPlan,
    loadOptions,
    submitCheckout,
    reset,
    setAuthenticated,
    setBillingAddress,
    setPaymentMethod,
    setTermsAccepted,
  };
});
```

### 3.2 Update Checkout.vue - Final Integration

**File:** `vbwd-frontend/user/vue/src/views/Checkout.vue`

```vue
<template>
  <div class="checkout">
    <h1>Checkout</h1>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-state" data-testid="checkout-loading">
      <div class="spinner" />
      <p>Loading...</p>
    </div>

    <!-- Error -->
    <div v-else-if="store.error && !store.checkoutResult" class="error-state" data-testid="checkout-error">
      <p>{{ store.error }}</p>
      <router-link to="/plans" class="btn secondary">Back to Plans</router-link>
    </div>

    <!-- Success -->
    <div v-else-if="store.checkoutResult" class="checkout-success" data-testid="checkout-success">
      <!-- ... existing success template ... -->
    </div>

    <!-- Checkout Form -->
    <div v-else-if="store.plan" class="checkout-form">
      <div class="checkout-grid">
        <!-- Left Column: Form Blocks -->
        <div class="form-column">
          <!-- 1. Email Block -->
          <EmailBlock
            :initial-email="userEmail"
            :is-authenticated="store.isAuthenticated"
            @authenticated="handleAuthenticated"
          />

          <!-- 2. Billing Address -->
          <BillingAddress
            @change="store.setBillingAddress"
            @valid="(v) => billingValid = v"
          />

          <!-- 3. Payment Methods -->
          <PaymentMethods
            @selected="store.setPaymentMethod"
          />

          <!-- 4. Terms Checkbox -->
          <TermsCheckbox
            @change="store.setTermsAccepted"
          />
        </div>

        <!-- Right Column: Order Summary -->
        <div class="summary-column">
          <div class="card order-summary" data-testid="order-summary">
            <h2>Order Summary</h2>
            <div class="plan-row">
              <span data-testid="plan-name">{{ store.plan.name }}</span>
              <span data-testid="plan-price">${{ store.plan.price }}</span>
            </div>
            <!-- ... bundles, addons, total ... -->
          </div>

          <!-- Requirements Status -->
          <div v-if="store.missingRequirements.length > 0" class="requirements" data-testid="checkout-requirements">
            <p>To complete checkout:</p>
            <ul>
              <li v-for="req in store.missingRequirements" :key="req">{{ req }}</li>
            </ul>
          </div>

          <!-- Pay Button -->
          <button
            data-testid="pay-button"
            class="btn primary pay-button"
            :disabled="!store.canPay"
            @click="store.submitCheckout"
          >
            <span v-if="store.submitting">Processing...</span>
            <span v-else>Pay ${{ orderTotal }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- No Plan -->
    <div v-else class="no-plan">
      <router-link to="/plans" class="btn primary">Browse Plans</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useCheckoutStore } from '@/stores/checkout';
import { isAuthenticated as checkAuth } from '@/api';
import EmailBlock from '@/components/checkout/EmailBlock.vue';
import BillingAddress from '@/components/checkout/BillingAddress.vue';
import PaymentMethods from '@/components/checkout/PaymentMethods.vue';
import TermsCheckbox from '@/components/checkout/TermsCheckbox.vue';

const route = useRoute();
const store = useCheckoutStore();

const userEmail = ref('');
const billingValid = ref(false);

const orderTotal = computed(() => {
  let total = store.plan?.price || 0;
  // Add bundles and addons
  return total.toFixed(2);
});

const handleAuthenticated = (userId: string) => {
  store.setAuthenticated(true);
};

onMounted(async () => {
  // Check initial auth state
  store.setAuthenticated(checkAuth());

  const planSlug = route.params.planSlug as string;
  if (planSlug) {
    await store.loadPlan(planSlug);
    await store.loadOptions();
  }
});

onUnmounted(() => {
  store.reset();
});
</script>

<style scoped>
.checkout-form {
  max-width: 1100px;
}

.checkout-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 30px;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-column {
  position: sticky;
  top: 20px;
  align-self: start;
}

.requirements {
  background: #fff3cd;
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.requirements ul {
  margin: 10px 0 0 20px;
}

.pay-button {
  width: 100%;
  padding: 15px;
  font-size: 1.1rem;
  margin-top: 15px;
}

.pay-button:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .checkout-grid {
    grid-template-columns: 1fr;
  }

  .summary-column {
    position: static;
  }
}
</style>
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Each component handles one block, store handles state |
| **O** - Open/Closed | New requirements can be added to computed without changing logic |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | Components emit focused events |
| **D** - Dependency Inversion | Components depend on store interface, not implementation |

## No Over-engineering

- No form library (native HTML + Vue)
- No complex validation framework
- Requirements shown as simple list
- Single-page checkout (no multi-step wizard)
- Reuses existing checkout submission logic

---

## Verification Checklist

- [ ] E2E tests for full flow written and FAILING
- [ ] Unit tests for canPay computed written and FAILING
- [ ] Store updated with new state and computed
- [ ] Checkout.vue integrates all components
- [ ] All tests PASSING
- [ ] Manual browser test of full flow
- [ ] Existing tests still pass

## Run Tests

> **All tests run in Docker containers.** Run commands from `vbwd-frontend/` directory.

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --user --unit    # Unit tests
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# From vbwd-frontend/user/vue/
npm run test -- --grep "canPay"                  # Unit tests
npm run test:e2e -- checkout-full-flow.spec.ts  # Full flow test
npm run test:e2e -- checkout/                    # All checkout tests

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!

# Full regression
npm run test && npm run test:e2e
```

## Final Regression Check

Run ALL checkout tests to ensure nothing is broken:

```bash
npm run test:e2e -- checkout/
npm run test -- stores/checkout
```
