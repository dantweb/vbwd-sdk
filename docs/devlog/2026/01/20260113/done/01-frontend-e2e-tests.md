# Sprint 01: Frontend E2E Tests (TDD-First)

**Date:** 2026-01-13
**Priority:** High
**Type:** Frontend Testing
**Section:** User Checkout Flow
**Prerequisite:** None
**Blocks:** Sprint 05 (Frontend Implementation)

## Goal

Write Playwright E2E tests for the checkout flow BEFORE any implementation.
These tests define the expected behavior and will initially FAIL.

**TDD Principle:** Tests are the specification. Implementation makes them pass.

## Key Business Rules (Tests Must Verify)

1. **Payment-First Activation**: Subscription is `pending` until payment
2. **Invoice Line Items**: Can contain subscription + token bundles + add-ons
3. **Token Credit**: Tokens credited to balance only after payment

## Tasks

### Task 1.1: Create Test Fixtures

**File:** `vbwd-frontend/user/vue/tests/e2e/fixtures/checkout.fixtures.ts`

```typescript
import { Page } from '@playwright/test';

export const TEST_USER = {
  email: 'test@example.com',
  password: 'TestPass123@',
};

export async function loginAsTestUser(page: Page): Promise<void> {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', TEST_USER.email);
  await page.fill('[data-testid="password"]', TEST_USER.password);
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/dashboard');
}

export async function navigateToCheckout(page: Page, planSlug: string = 'pro'): Promise<void> {
  await page.goto(`/checkout/${planSlug}`);
}

export async function selectPlanFromList(page: Page): Promise<void> {
  await page.goto('/plans');
  await page.click('[data-testid^="select-plan-"]');
  await page.waitForURL(/\/checkout\//);
}
```

---

### Task 1.2: Checkout Page Display Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-display.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser, navigateToCheckout } from '../fixtures/checkout.fixtures';

test.describe('Checkout Page Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('displays plan details in order summary', async ({ page }) => {
    await navigateToCheckout(page, 'pro');

    await expect(page.locator('[data-testid="order-summary"]')).toBeVisible();
    await expect(page.locator('[data-testid="plan-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="plan-price"]')).toBeVisible();
  });

  test('displays confirm button', async ({ page }) => {
    await navigateToCheckout(page, 'pro');

    await expect(page.locator('[data-testid="confirm-checkout"]')).toBeVisible();
    await expect(page.locator('[data-testid="confirm-checkout"]')).toBeEnabled();
  });

  test('shows loading state while fetching plan', async ({ page }) => {
    await page.route('**/api/v1/tarif-plans/**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.continue();
    });

    await navigateToCheckout(page, 'pro');

    await expect(page.locator('[data-testid="checkout-loading"]')).toBeVisible();
  });

  test('shows error for invalid plan slug', async ({ page }) => {
    await navigateToCheckout(page, 'invalid-plan-slug');

    await expect(page.locator('[data-testid="checkout-error"]')).toBeVisible();
  });

  test('redirects unauthenticated user to login', async ({ page }) => {
    // Clear auth state
    await page.context().clearCookies();
    await page.goto('/checkout/pro');

    await expect(page).toHaveURL(/\/login/);
  });
});
```

---

### Task 1.3: Token Bundle Selection Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/token-bundles.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser, navigateToCheckout } from '../fixtures/checkout.fixtures';

test.describe('Token Bundle Selection', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
    await navigateToCheckout(page, 'pro');
  });

  test('displays available token bundles', async ({ page }) => {
    await expect(page.locator('[data-testid="token-bundles-section"]')).toBeVisible();
    await expect(page.locator('[data-testid^="token-bundle-"]')).toHaveCount.greaterThan(0);
  });

  test('can add token bundle to order', async ({ page }) => {
    await page.click('[data-testid="token-bundle-1000"]');

    await expect(page.locator('[data-testid="order-summary"]')).toContainText('1000 Tokens');
  });

  test('can remove token bundle from order', async ({ page }) => {
    await page.click('[data-testid="token-bundle-1000"]');
    await page.click('[data-testid="remove-token-bundle-1000"]');

    await expect(page.locator('[data-testid="order-summary"]')).not.toContainText('1000 Tokens');
  });

  test('updates total price when bundle added', async ({ page }) => {
    const initialTotal = await page.locator('[data-testid="order-total"]').textContent();

    await page.click('[data-testid="token-bundle-1000"]');

    const newTotal = await page.locator('[data-testid="order-total"]').textContent();
    expect(newTotal).not.toBe(initialTotal);
  });

  test('can add multiple bundles', async ({ page }) => {
    await page.click('[data-testid="token-bundle-1000"]');
    await page.click('[data-testid="token-bundle-5000"]');

    const lineItems = page.locator('[data-testid^="line-item-token-bundle-"]');
    await expect(lineItems).toHaveCount(2);
  });
});
```

---

### Task 1.4: Add-on Selection Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/addons.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser, navigateToCheckout } from '../fixtures/checkout.fixtures';

test.describe('Add-on Selection', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
    await navigateToCheckout(page, 'pro');
  });

  test('displays available add-ons', async ({ page }) => {
    await expect(page.locator('[data-testid="addons-section"]')).toBeVisible();
    await expect(page.locator('[data-testid^="addon-"]')).toHaveCount.greaterThan(0);
  });

  test('can add addon to order', async ({ page }) => {
    await page.click('[data-testid="addon-priority-support"]');

    await expect(page.locator('[data-testid="order-summary"]')).toContainText('Priority Support');
  });

  test('can remove addon from order', async ({ page }) => {
    await page.click('[data-testid="addon-priority-support"]');
    await page.click('[data-testid="remove-addon-priority-support"]');

    await expect(page.locator('[data-testid="order-summary"]')).not.toContainText('Priority Support');
  });

  test('shows addon description', async ({ page }) => {
    await expect(page.locator('[data-testid="addon-priority-support-description"]')).toBeVisible();
  });

  test('shows addon price', async ({ page }) => {
    await expect(page.locator('[data-testid="addon-priority-support-price"]')).toBeVisible();
  });
});
```

---

### Task 1.5: Checkout Submission Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-submit.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser, navigateToCheckout } from '../fixtures/checkout.fixtures';

test.describe('Checkout Submission', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
    await navigateToCheckout(page, 'pro');
  });

  test('creates pending subscription on confirm', async ({ page }) => {
    await page.click('[data-testid="confirm-checkout"]');

    await expect(page.locator('[data-testid="checkout-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="subscription-status"]')).toHaveText('Pending');
  });

  test('shows invoice number after checkout', async ({ page }) => {
    await page.click('[data-testid="confirm-checkout"]');

    await expect(page.locator('[data-testid="invoice-number"]')).toBeVisible();
    await expect(page.locator('[data-testid="invoice-number"]')).toContainText('INV-');
  });

  test('shows payment required message', async ({ page }) => {
    await page.click('[data-testid="confirm-checkout"]');

    await expect(page.locator('[data-testid="payment-required-message"]')).toBeVisible();
  });

  test('shows invoice line items after checkout', async ({ page }) => {
    await page.click('[data-testid="token-bundle-1000"]');
    await page.click('[data-testid="addon-priority-support"]');
    await page.click('[data-testid="confirm-checkout"]');

    const lineItems = page.locator('[data-testid^="invoice-line-item-"]');
    await expect(lineItems).toHaveCount(3); // subscription + bundle + addon
  });

  test('shows loading state during submission', async ({ page }) => {
    await page.route('**/api/v1/user/checkout', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.continue();
    });

    await page.click('[data-testid="confirm-checkout"]');

    await expect(page.locator('[data-testid="checkout-submitting"]')).toBeVisible();
  });

  test('handles API error gracefully', async ({ page }) => {
    await page.route('**/api/v1/user/checkout', (route) => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Invalid plan' }),
      });
    });

    await page.click('[data-testid="confirm-checkout"]');

    await expect(page.locator('[data-testid="checkout-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="checkout-error"]')).toContainText('Invalid plan');
  });

  test('disables confirm button during submission', async ({ page }) => {
    await page.route('**/api/v1/user/checkout', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.continue();
    });

    await page.click('[data-testid="confirm-checkout"]');

    await expect(page.locator('[data-testid="confirm-checkout"]')).toBeDisabled();
  });
});
```

---

### Task 1.6: Post-Checkout Navigation Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/post-checkout.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser, navigateToCheckout } from '../fixtures/checkout.fixtures';

test.describe('Post-Checkout Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
    await navigateToCheckout(page, 'pro');
    await page.click('[data-testid="confirm-checkout"]');
    await page.waitForSelector('[data-testid="checkout-success"]');
  });

  test('can navigate to subscription page', async ({ page }) => {
    await page.click('[data-testid="view-subscription-btn"]');

    await expect(page).toHaveURL('/subscription');
  });

  test('can navigate to invoices page', async ({ page }) => {
    await page.click('[data-testid="view-invoice-btn"]');

    await expect(page).toHaveURL(/\/invoices/);
  });

  test('can go back to plans', async ({ page }) => {
    await page.click('[data-testid="back-to-plans-btn"]');

    await expect(page).toHaveURL('/plans');
  });
});
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

### Run Playwright Tests Directly
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/user/vue

# Run all checkout tests
npx playwright test tests/e2e/checkout/ --reporter=list

# Run with UI for debugging
npx playwright test tests/e2e/checkout/ --ui
```

---

## Run Tests (Expected: ALL FAIL)

**Expected Result:** All tests should FAIL because:
1. `data-testid` attributes don't exist yet
2. API endpoints not implemented
3. Checkout.vue is placeholder

---

## Definition of Done

- [ ] Test fixtures created
- [ ] Checkout display tests written
- [ ] Token bundle selection tests written
- [ ] Add-on selection tests written
- [ ] Checkout submission tests written
- [ ] Post-checkout navigation tests written
- [ ] All tests run (and FAIL as expected)
- [ ] Tests documented with expected behavior
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Test Fixtures | ⏳ Pending | |
| 1.2 Checkout Display Tests | ⏳ Pending | |
| 1.3 Token Bundle Tests | ⏳ Pending | |
| 1.4 Add-on Tests | ⏳ Pending | |
| 1.5 Checkout Submit Tests | ⏳ Pending | |
| 1.6 Post-Checkout Tests | ⏳ Pending | |

---

## Next Sprint

After this sprint, proceed to:
- **Sprint 02:** Backend Integration Tests (TDD)
- **Sprint 03:** Backend Checkout Events & Handlers
