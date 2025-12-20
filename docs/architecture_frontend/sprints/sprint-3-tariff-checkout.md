# Sprint 3: Tariff Plans & Checkout

**Goal:** Extend wizard with tariff plan selection and checkout flow integration.

---

## Objectives

- [ ] Step 3: Display tariff plans from API
- [ ] Plan comparison UI with features
- [ ] Plan selection with validation
- [ ] Step 4: Checkout form (billing details)
- [ ] Payment method selection (PayPal/Stripe)
- [ ] Integration with backend checkout API
- [ ] Loading states and error handling
- [ ] Redirect to payment provider
- [ ] E2E test for complete checkout flow

---

## Tasks

### 3.1 Extend Wizard Store

**File:** `src/plugins/wizard/store/wizardStore.ts` (extend)

```typescript
export interface WizardState {
  // ... existing fields
  step3Data: {
    selectedPlan?: TariffPlan;
  };
  step4Data: {
    firstName?: string;
    lastName?: string;
    address?: string;
    city?: string;
    postalCode?: string;
    country?: string;
    paymentMethod?: 'paypal' | 'stripe';
  };
  availablePlans: TariffPlan[];
  isSubmitting: boolean;
}

// Add actions
async function loadPlans() {
  const api = useApi();
  availablePlans.value = await api.tariffs.list();
}

async function submitCheckout() {
  isSubmitting.value = true;
  try {
    const api = useApi();
    const result = await api.checkout.create({
      tarifPlanId: step3Data.value.selectedPlan!.id,
      paymentMethod: step4Data.value.paymentMethod!,
      userDetails: step4Data.value,
    });

    // Redirect to payment provider
    window.location.href = result.checkoutUrl;
  } catch (error) {
    console.error('Checkout failed:', error);
    throw error;
  } finally {
    isSubmitting.value = false;
  }
}
```

---

### 3.2 Plan Selection Component

**File:** `src/plugins/wizard/components/steps/StepPlans.vue`

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">Choose Your Plan</h2>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
      <p class="mt-4 text-gray-600">Loading plans...</p>
    </div>

    <div v-else class="grid md:grid-cols-3 gap-6">
      <div
        v-for="plan in store.availablePlans"
        :key="plan.id"
        class="border rounded-lg p-6 cursor-pointer transition-all"
        :class="{
          'border-primary-600 ring-2 ring-primary-600 bg-primary-50':
            store.step3Data.selectedPlan?.id === plan.id,
          'border-gray-200 hover:border-primary-300':
            store.step3Data.selectedPlan?.id !== plan.id,
        }"
        @click="selectPlan(plan)"
      >
        <h3 class="text-xl font-bold mb-2">{{ plan.name }}</h3>
        <div class="text-3xl font-bold text-primary-600 mb-4">
          {{ formatPrice(plan.price, plan.currency) }}
          <span class="text-sm font-normal text-gray-600">
            / {{ plan.billingPeriod }}
          </span>
        </div>

        <p class="text-gray-600 mb-6">{{ plan.description }}</p>

        <ul class="space-y-2">
          <li
            v-for="(feature, index) in plan.features"
            :key="index"
            class="flex items-start"
          >
            <svg
              class="h-5 w-5 text-green-500 mr-2 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span class="text-sm text-gray-700">{{ feature }}</span>
          </li>
        </ul>

        <button
          v-if="store.step3Data.selectedPlan?.id === plan.id"
          class="w-full mt-6 py-2 bg-primary-600 text-white rounded-md font-medium"
        >
          Selected
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useWizardStore } from '../../store/wizardStore';
import type { TariffPlan } from '@/core/api/types/user.types';

const store = useWizardStore();
const loading = ref(true);

onMounted(async () => {
  try {
    await store.loadPlans();
  } finally {
    loading.value = false;
  }
});

function selectPlan(plan: TariffPlan) {
  store.step3Data.selectedPlan = plan;
}

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(price);
}
</script>
```

---

### 3.3 Checkout Form Component

**File:** `src/plugins/wizard/components/steps/StepCheckout.vue`

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">Billing Information</h2>

    <!-- Order Summary -->
    <div class="bg-gray-50 rounded-lg p-4 mb-6">
      <h3 class="font-semibold mb-2">Order Summary</h3>
      <div class="flex justify-between">
        <span>{{ store.step3Data.selectedPlan?.name }}</span>
        <span class="font-bold">
          {{ formatPrice(store.step3Data.selectedPlan?.price || 0, store.step3Data.selectedPlan?.currency || 'USD') }}
        </span>
      </div>
    </div>

    <!-- Billing Form -->
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="grid md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            First Name *
          </label>
          <input
            v-model="store.step4Data.firstName"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Last Name *
          </label>
          <input
            v-model="store.step4Data.lastName"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Address *
        </label>
        <input
          v-model="store.step4Data.address"
          type="text"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div class="grid md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            City *
          </label>
          <input
            v-model="store.step4Data.city"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Postal Code *
          </label>
          <input
            v-model="store.step4Data.postalCode"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      <!-- Payment Method -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Payment Method *
        </label>
        <div class="space-y-2">
          <label class="flex items-center p-3 border rounded-md cursor-pointer hover:bg-gray-50">
            <input
              v-model="store.step4Data.paymentMethod"
              type="radio"
              value="stripe"
              class="mr-3"
            />
            <span>Credit Card (Stripe)</span>
          </label>

          <label class="flex items-center p-3 border rounded-md cursor-pointer hover:bg-gray-50">
            <input
              v-model="store.step4Data.paymentMethod"
              type="radio"
              value="paypal"
              class="mr-3"
            />
            <span>PayPal</span>
          </label>
        </div>
      </div>

      <button
        type="submit"
        class="w-full py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
        :disabled="store.isSubmitting"
      >
        {{ store.isSubmitting ? 'Processing...' : 'Proceed to Payment' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useWizardStore } from '../../store/wizardStore';

const store = useWizardStore();

async function handleSubmit() {
  try {
    await store.submitCheckout();
  } catch (error) {
    alert('Checkout failed. Please try again.');
  }
}

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(price);
}
</script>
```

---

### 3.4 E2E Test Extension

**File:** `tests/e2e/flows/wizard-checkout.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Wizard Checkout Flow', () => {
  test('user can complete full wizard with checkout', async ({ page }) => {
    // Step 1: Upload
    await page.goto('/wizard');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(['tests/fixtures/sample-image-1.jpg']);
    await page.click('button:has-text("Next")');

    // Step 2: GDPR
    await page.fill('input[type="email"]', 'test@example.com');
    await page.check('input[type="checkbox"]');
    await page.click('button:has-text("Next")');

    // Step 3: Select Plan
    await expect(page.locator('h2')).toContainText('Choose Your Plan');

    // Wait for plans to load
    await page.waitForSelector('text=Basic', { timeout: 5000 });

    // Click on a plan
    await page.click('text=Basic');
    await expect(page.locator('button:has-text("Selected")')).toBeVisible();

    await page.click('button:has-text("Next")');

    // Step 4: Billing Info
    await expect(page.locator('h2')).toContainText('Billing Information');

    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="address"]', '123 Main St');
    await page.fill('input[name="city"]', 'New York');
    await page.fill('input[name="postalCode"]', '10001');

    // Select payment method
    await page.check('input[value="stripe"]');

    // Submit - should redirect to Stripe
    await page.click('button:has-text("Proceed to Payment")');

    // Wait for redirect (mocked in test environment)
    await page.waitForURL(/checkout|payment/, { timeout: 10000 });
  });
});
```

---

## Testing Checklist

- [ ] Plans load from API
- [ ] Can select a plan
- [ ] Selected plan is highlighted
- [ ] Billing form validates required fields
- [ ] Payment method selection works
- [ ] Checkout API is called with correct data
- [ ] Redirects to payment provider
- [ ] Loading states shown during submission
- [ ] Error handling for failed API calls
- [ ] E2E test covers full flow

---

## Definition of Done

- [ ] Step 3 (tariff plans) implemented
- [ ] Step 4 (checkout) implemented
- [ ] Plans fetch from backend API
- [ ] Checkout integrates with backend
- [ ] Payment provider redirect works
- [ ] All form validations pass
- [ ] E2E test passes
- [ ] Error handling implemented
- [ ] Documentation updated

---

## Next Sprint

**Sprint 4:** User Cabinet & Subscription Management
