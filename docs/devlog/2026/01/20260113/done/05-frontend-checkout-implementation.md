# Sprint 05: Frontend Checkout Implementation

**Date:** 2026-01-13
**Priority:** High
**Type:** Frontend Implementation
**Section:** User Checkout Flow
**Prerequisite:** Sprint 01 (E2E Tests), Sprint 03-04 (Backend)
**Blocks:** Sprint 06 (Integration Testing)

## Goal

Implement the checkout UI that makes all E2E tests from Sprint 01 PASS.

**TDD Completion:** This sprint makes the failing tests pass.

## Tasks

### Task 5.1: Create Checkout Store

**File:** `vbwd-frontend/user/vue/src/stores/checkout.ts`

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from '@/api';

interface Plan {
  id: string;
  name: string;
  slug: string;
  price: number;
  currency: string;
  billing_period: string;
}

interface TokenBundle {
  id: string;
  name: string;
  token_amount: number;
  price: number;
}

interface AddOn {
  id: string;
  name: string;
  description: string;
  price: number;
  billing_period: string;
}

interface CheckoutState {
  plan: Plan | null;
  selectedBundles: TokenBundle[];
  selectedAddons: AddOn[];
  loading: boolean;
  submitting: boolean;
  error: string | null;
  checkoutResult: any | null;
}

export const useCheckoutStore = defineStore('checkout', () => {
  const plan = ref<Plan | null>(null);
  const selectedBundles = ref<TokenBundle[]>([]);
  const selectedAddons = ref<AddOn[]>([]);
  const availableBundles = ref<TokenBundle[]>([]);
  const availableAddons = ref<AddOn[]>([]);
  const loading = ref(false);
  const submitting = ref(false);
  const error = ref<string | null>(null);
  const checkoutResult = ref<any | null>(null);

  const orderTotal = computed(() => {
    let total = plan.value?.price || 0;
    total += selectedBundles.value.reduce((sum, b) => sum + b.price, 0);
    total += selectedAddons.value.reduce((sum, a) => sum + a.price, 0);
    return total;
  });

  const lineItems = computed(() => {
    const items = [];
    if (plan.value) {
      items.push({
        type: 'subscription',
        name: plan.value.name,
        price: plan.value.price,
      });
    }
    selectedBundles.value.forEach((b) => {
      items.push({
        type: 'token_bundle',
        name: b.name,
        price: b.price,
      });
    });
    selectedAddons.value.forEach((a) => {
      items.push({
        type: 'add_on',
        name: a.name,
        price: a.price,
      });
    });
    return items;
  });

  async function loadPlan(slug: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.get(`/tarif-plans/${slug}`);
      plan.value = response.data;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to load plan';
    } finally {
      loading.value = false;
    }
  }

  async function loadOptions() {
    try {
      const [bundlesRes, addonsRes] = await Promise.all([
        api.get('/token-bundles'),
        api.get('/addons'),
      ]);
      availableBundles.value = bundlesRes.data.bundles || [];
      availableAddons.value = addonsRes.data.addons || [];
    } catch (e) {
      // Options are optional, don't fail
    }
  }

  function addBundle(bundle: TokenBundle) {
    if (!selectedBundles.value.find((b) => b.id === bundle.id)) {
      selectedBundles.value.push(bundle);
    }
  }

  function removeBundle(bundleId: string) {
    selectedBundles.value = selectedBundles.value.filter((b) => b.id !== bundleId);
  }

  function addAddon(addon: AddOn) {
    if (!selectedAddons.value.find((a) => a.id === addon.id)) {
      selectedAddons.value.push(addon);
    }
  }

  function removeAddon(addonId: string) {
    selectedAddons.value = selectedAddons.value.filter((a) => a.id !== addonId);
  }

  async function submitCheckout() {
    if (!plan.value) {
      error.value = 'No plan selected';
      return;
    }

    submitting.value = true;
    error.value = null;

    try {
      const response = await api.post('/user/checkout', {
        plan_id: plan.value.id,
        token_bundle_ids: selectedBundles.value.map((b) => b.id),
        add_on_ids: selectedAddons.value.map((a) => a.id),
      });
      checkoutResult.value = response.data;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Checkout failed';
    } finally {
      submitting.value = false;
    }
  }

  function reset() {
    plan.value = null;
    selectedBundles.value = [];
    selectedAddons.value = [];
    error.value = null;
    checkoutResult.value = null;
  }

  return {
    plan,
    selectedBundles,
    selectedAddons,
    availableBundles,
    availableAddons,
    loading,
    submitting,
    error,
    checkoutResult,
    orderTotal,
    lineItems,
    loadPlan,
    loadOptions,
    addBundle,
    removeBundle,
    addAddon,
    removeAddon,
    submitCheckout,
    reset,
  };
});
```

---

### Task 5.2: Update Checkout.vue

**File:** `vbwd-frontend/user/vue/src/views/Checkout.vue`

```vue
<template>
  <div class="checkout-page">
    <!-- Loading State -->
    <div v-if="store.loading" data-testid="checkout-loading" class="loading">
      Loading plan details...
    </div>

    <!-- Error State -->
    <div v-else-if="store.error && !store.checkoutResult" data-testid="checkout-error" class="error">
      {{ store.error }}
    </div>

    <!-- Checkout Success -->
    <div v-else-if="store.checkoutResult" data-testid="checkout-success" class="success">
      <h2>Checkout Created</h2>

      <div class="status-info">
        <p>
          Subscription Status:
          <span data-testid="subscription-status">
            {{ store.checkoutResult.subscription.status === 'pending' ? 'Pending' : 'Active' }}
          </span>
        </p>
        <p data-testid="invoice-number">
          Invoice: {{ store.checkoutResult.invoice.invoice_number }}
        </p>
      </div>

      <div data-testid="payment-required-message" class="payment-message">
        Complete payment to activate your subscription.
      </div>

      <!-- Invoice Line Items -->
      <div data-testid="invoice-line-items" class="invoice-items">
        <h3>Invoice Items</h3>
        <div
          v-for="(item, index) in store.checkoutResult.invoice.line_items"
          :key="index"
          :data-testid="`invoice-line-item-${item.type}`"
          class="line-item"
        >
          <span>{{ item.description }}</span>
          <span>${{ item.total_price }}</span>
        </div>
        <div class="total">
          <strong>Total: ${{ store.checkoutResult.invoice.total_amount }}</strong>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="actions">
        <button data-testid="view-subscription-btn" @click="goToSubscription">
          View Subscription
        </button>
        <button data-testid="view-invoice-btn" @click="goToInvoice">
          View Invoice
        </button>
        <button data-testid="back-to-plans-btn" @click="goToPlans">
          Back to Plans
        </button>
      </div>
    </div>

    <!-- Checkout Form -->
    <div v-else-if="store.plan" class="checkout-form">
      <h1>Checkout</h1>

      <!-- Order Summary -->
      <div data-testid="order-summary" class="order-summary">
        <h2>Order Summary</h2>

        <div class="plan-details">
          <span data-testid="plan-name">{{ store.plan.name }}</span>
          <span data-testid="plan-price">${{ store.plan.price }}/{{ store.plan.billing_period }}</span>
        </div>

        <!-- Selected Items -->
        <div v-for="item in store.lineItems" :key="item.name" :data-testid="`line-item-${item.type}-${item.name}`">
          <span>{{ item.name }}</span>
          <span>${{ item.price }}</span>
          <button
            v-if="item.type === 'token_bundle'"
            :data-testid="`remove-token-bundle-${item.name.split(' ')[0]}`"
            @click="store.removeBundle(item.id)"
          >
            Remove
          </button>
          <button
            v-if="item.type === 'add_on'"
            :data-testid="`remove-addon-${item.name.toLowerCase().replace(/ /g, '-')}`"
            @click="store.removeAddon(item.id)"
          >
            Remove
          </button>
        </div>

        <div data-testid="order-total" class="total">
          <strong>Total: ${{ store.orderTotal }}</strong>
        </div>
      </div>

      <!-- Token Bundles Section -->
      <div data-testid="token-bundles-section" class="token-bundles">
        <h3>Add Token Bundles</h3>
        <div
          v-for="bundle in store.availableBundles"
          :key="bundle.id"
          :data-testid="`token-bundle-${bundle.token_amount}`"
          class="bundle-option"
          @click="store.addBundle(bundle)"
        >
          <span>{{ bundle.name }}</span>
          <span>${{ bundle.price }}</span>
        </div>
      </div>

      <!-- Add-ons Section -->
      <div data-testid="addons-section" class="addons">
        <h3>Add-ons</h3>
        <div
          v-for="addon in store.availableAddons"
          :key="addon.id"
          :data-testid="`addon-${addon.name.toLowerCase().replace(/ /g, '-')}`"
          class="addon-option"
          @click="store.addAddon(addon)"
        >
          <span>{{ addon.name }}</span>
          <span :data-testid="`addon-${addon.name.toLowerCase().replace(/ /g, '-')}-price`">
            ${{ addon.price }}
          </span>
          <p :data-testid="`addon-${addon.name.toLowerCase().replace(/ /g, '-')}-description`">
            {{ addon.description }}
          </p>
        </div>
      </div>

      <!-- Confirm Button -->
      <div class="confirm-section">
        <div v-if="store.submitting" data-testid="checkout-submitting">
          Processing...
        </div>
        <button
          data-testid="confirm-checkout"
          :disabled="store.submitting"
          @click="store.submitCheckout"
        >
          Confirm Purchase
        </button>
      </div>

      <!-- Error Display -->
      <div v-if="store.error" data-testid="checkout-error" class="error">
        {{ store.error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useCheckoutStore } from '@/stores/checkout';

const route = useRoute();
const router = useRouter();
const store = useCheckoutStore();

onMounted(async () => {
  const planSlug = route.params.planSlug as string;
  if (planSlug) {
    await store.loadPlan(planSlug);
    await store.loadOptions();
  }
});

function goToSubscription() {
  router.push('/subscription');
}

function goToInvoice() {
  const invoiceId = store.checkoutResult?.invoice?.id;
  router.push(`/invoices/${invoiceId}`);
}

function goToPlans() {
  router.push('/plans');
}
</script>

<style scoped>
.checkout-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.loading,
.error {
  padding: 1rem;
  border-radius: 4px;
}

.error {
  background: #fee;
  color: #c00;
}

.order-summary {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.total {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #ddd;
}

.bundle-option,
.addon-option {
  padding: 0.5rem;
  border: 1px solid #ddd;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.bundle-option:hover,
.addon-option:hover {
  background: #f0f0f0;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

---

### Task 5.3: Update Router

**File:** `vbwd-frontend/user/vue/src/router/index.ts` (update)

```typescript
{
  path: '/checkout/:planSlug',
  name: 'Checkout',
  component: () => import('@/views/Checkout.vue'),
  meta: { requiresAuth: true }
}
```

---

### Task 5.4: Create API Endpoints for Options

**File:** `vbwd-frontend/user/vue/src/api/index.ts` (update if needed)

Ensure the API client can call:
- `GET /api/v1/token-bundles`
- `GET /api/v1/addons`
- `POST /api/v1/user/checkout`

---

### Task 5.5: Run E2E Tests (Should PASS)

```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/user/vue

# Run all checkout tests
npx playwright test tests/e2e/checkout/ --reporter=list

# All tests from Sprint 01 should now PASS
```

---

### Task 5.6: Fix Failing Tests

If any tests fail, debug and fix:

```bash
# Run with UI for debugging
npx playwright test tests/e2e/checkout/ --ui

# Run specific test file
npx playwright test tests/e2e/checkout/checkout-submit.spec.ts

# Run with headed browser
npx playwright test tests/e2e/checkout/ --headed
```

---

## Build & Test Commands

**IMPORTANT:** Always rebuild and run tests after making changes.

### Rebuild Frontend
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend

# Rebuild user frontend
make dev-user
```

### Run Tests with Pre-Commit Script
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend

# Run style checks (ESLint + TypeScript) for user app
./bin/pre-commit-check.sh --user

# Run user E2E tests only
./bin/pre-commit-check.sh --user --e2e

# Run user unit tests only
./bin/pre-commit-check.sh --user --unit

# Run all checks for user app
./bin/pre-commit-check.sh --user --unit --e2e

# Run everything for all apps
./bin/pre-commit-check.sh --all
```

---

## Definition of Done

- [ ] Checkout store created
- [ ] Checkout.vue implemented with all data-testid attributes
- [ ] Router updated
- [ ] All Sprint 01 E2E tests PASS
- [ ] No console errors in browser
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 5.1 Checkout Store | ⏳ Pending | |
| 5.2 Checkout.vue | ⏳ Pending | |
| 5.3 Router Update | ⏳ Pending | |
| 5.4 API Endpoints | ⏳ Pending | |
| 5.5 Run E2E Tests | ⏳ Pending | Should PASS |
| 5.6 Fix Failing Tests | ⏳ Pending | If needed |

---

## Next Sprint

After this sprint, proceed to:
- **Sprint 06:** Full Integration Testing
