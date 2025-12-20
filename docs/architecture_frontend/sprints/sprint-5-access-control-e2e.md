# Sprint 5: Access Control & Comprehensive E2E Tests

**Goal:** Implement tariff-based access control and comprehensive E2E test coverage.

---

## Objectives

- [ ] Route guards for tariff-based access control
- [ ] Component-level permission directives
- [ ] Composable for permission checking
- [ ] Upgrade prompts for restricted content
- [ ] Comprehensive E2E test suite
- [ ] Performance testing with Playwright
- [ ] Accessibility testing (WCAG 2.1 AA)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile responsive testing

---

## Tasks

### 5.1 Access Control Service

**File:** `src/core/access/AccessControl.ts`

```typescript
import { inject } from 'vue';
import { IAuthService } from '../auth/IAuthService';
import { Subscription, TariffPlan } from '../api/types/user.types';

export class AccessControl {
  constructor(private authService: IAuthService) {}

  /**
   * Check if user has active subscription to any of the required plans
   */
  async hasAccessToPlan(requiredPlans: string[]): Promise<boolean> {
    if (!this.authService.isAuthenticated.value) {
      return false;
    }

    // Get user's active subscriptions from API
    const subscriptions = await this.authService.currentUser.value?.subscriptions;

    if (!subscriptions) {
      return false;
    }

    const activeSubscriptions = subscriptions.filter(
      (sub: Subscription) => sub.status === 'active'
    );

    // Check if any active subscription matches required plans
    return activeSubscriptions.some((sub: Subscription) =>
      requiredPlans.includes(sub.plan.slug)
    );
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission: string): boolean {
    const user = this.authService.currentUser.value;

    if (!user) {
      return false;
    }

    // TODO: Implement role-based permissions
    // For now, admins have all permissions
    if (user.role === 'admin') {
      return true;
    }

    return false;
  }

  /**
   * Check if user has specific role
   */
  hasRole(role: string): boolean {
    const user = this.authService.currentUser.value;
    return user?.role === role;
  }

  /**
   * Get highest tier plan user has access to
   */
  async getHighestAccessLevel(): Promise<string | null> {
    const user = this.authService.currentUser.value;

    if (!user) {
      return null;
    }

    const subscriptions = await user.subscriptions;

    if (!subscriptions || subscriptions.length === 0) {
      return null;
    }

    const activeSubscriptions = subscriptions.filter(
      (sub: Subscription) => sub.status === 'active'
    );

    // Define plan hierarchy (customize based on your plans)
    const planHierarchy: Record<string, number> = {
      basic: 1,
      professional: 2,
      premium: 3,
      enterprise: 4,
    };

    let highestLevel = 0;
    let highestPlan: string | null = null;

    for (const sub of activeSubscriptions) {
      const level = planHierarchy[sub.plan.slug] || 0;
      if (level > highestLevel) {
        highestLevel = level;
        highestPlan = sub.plan.slug;
      }
    }

    return highestPlan;
  }
}

// Composable for use in components
export function useAccessControl() {
  const authService = inject<IAuthService>('authService');

  if (!authService) {
    throw new Error('AuthService not provided');
  }

  const accessControl = new AccessControl(authService);

  return {
    hasAccessToPlan: accessControl.hasAccessToPlan.bind(accessControl),
    hasPermission: accessControl.hasPermission.bind(accessControl),
    hasRole: accessControl.hasRole.bind(accessControl),
    getHighestAccessLevel: accessControl.getHighestAccessLevel.bind(accessControl),
  };
}
```

---

### 5.2 Route Guard for Plan Access

**File:** `src/core/router/guards.ts` (extend)

```typescript
import { NavigationGuard } from 'vue-router';
import { inject } from 'vue';
import { IAuthService } from '../auth/IAuthService';
import { AccessControl } from '../access/AccessControl';

export const authGuard: NavigationGuard = async (to, from, next) => {
  const authService = inject<IAuthService>('authService');

  if (!authService) {
    next(false);
    return;
  }

  if (to.meta.requiresAuth && !authService.isAuthenticated.value) {
    next({
      name: 'login',
      query: { redirect: to.fullPath },
    });
  } else {
    next();
  }
};

export const planGuard: NavigationGuard = async (to, from, next) => {
  const authService = inject<IAuthService>('authService');

  if (!authService) {
    next(false);
    return;
  }

  const requiredPlans = to.meta.requiredPlan as string[] | undefined;

  if (!requiredPlans || requiredPlans.length === 0) {
    next();
    return;
  }

  const accessControl = new AccessControl(authService);
  const hasAccess = await accessControl.hasAccessToPlan(requiredPlans);

  if (!hasAccess) {
    next({
      name: 'upgrade',
      query: {
        plan: requiredPlans[0],
        redirect: to.fullPath,
      },
    });
  } else {
    next();
  }
};

// Apply guards to router
export function setupRouterGuards(router: Router) {
  router.beforeEach(authGuard);
  router.beforeEach(planGuard);
}
```

---

### 5.3 Access Control Directive

**File:** `src/core/directives/v-access.ts`

```typescript
import { Directive, DirectiveBinding } from 'vue';
import { AccessControl } from '../access/AccessControl';

interface AccessDirectiveBinding extends DirectiveBinding {
  value: {
    plans?: string[];
    permission?: string;
    role?: string;
  };
}

/**
 * v-access directive for hiding/showing elements based on access control
 *
 * Usage:
 * <div v-access="{ plans: ['premium'] }">Premium Content</div>
 * <button v-access="{ permission: 'edit' }">Edit</button>
 * <div v-access="{ role: 'admin' }">Admin Only</div>
 */
export const vAccess: Directive = {
  async mounted(el: HTMLElement, binding: AccessDirectiveBinding) {
    const { plans, permission, role } = binding.value;

    // Get access control instance from app context
    const accessControl = binding.instance?.$accessControl as AccessControl;

    if (!accessControl) {
      console.error('AccessControl not available');
      el.style.display = 'none';
      return;
    }

    let hasAccess = true;

    if (plans) {
      hasAccess = await accessControl.hasAccessToPlan(plans);
    } else if (permission) {
      hasAccess = accessControl.hasPermission(permission);
    } else if (role) {
      hasAccess = accessControl.hasRole(role);
    }

    if (!hasAccess) {
      el.style.display = 'none';
    }
  },
};
```

---

### 5.4 Upgrade Prompt Component

**File:** `src/shared/components/UpgradePrompt.vue`

```vue
<template>
  <div class="max-w-md mx-auto mt-12 text-center">
    <svg
      class="mx-auto h-24 w-24 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
      />
    </svg>

    <h2 class="mt-4 text-2xl font-bold text-gray-900">
      Upgrade Required
    </h2>

    <p class="mt-2 text-gray-600">
      This feature requires a {{ requiredPlan }} subscription.
    </p>

    <div class="mt-6 space-x-4">
      <router-link
        to="/wizard"
        class="inline-block px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      >
        Upgrade Now
      </router-link>

      <button
        @click="$router.back()"
        class="inline-block px-6 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
      >
        Go Back
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  requiredPlan: string;
}>();
</script>
```

---

### 5.5 Comprehensive E2E Test Suite

**File:** `tests/e2e/complete-user-journey.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Complete User Journey', () => {
  test('new user can signup, subscribe, and access features', async ({ page }) => {
    // 1. Start wizard
    await page.goto('/wizard');

    // 2. Step 1: Upload files
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([
      'tests/fixtures/sample-image-1.jpg',
      'tests/fixtures/sample-image-2.jpg',
    ]);
    await page.click('button:has-text("Next")');

    // 3. Step 2: Email & GDPR
    const email = `test-${Date.now()}@example.com`;
    await page.fill('input[type="email"]', email);
    await page.check('input[type="checkbox"]');
    await page.click('button:has-text("Next")');

    // 4. Step 3: Select plan
    await page.waitForSelector('text=Basic');
    await page.click('text=Basic');
    await page.click('button:has-text("Next")');

    // 5. Step 4: Billing info
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="address"]', '123 Main St');
    await page.fill('input[name="city"]', 'New York');
    await page.fill('input[name="postalCode"]', '10001');
    await page.check('input[value="stripe"]');

    // 6. Submit (mocked payment)
    await page.click('button:has-text("Proceed to Payment")');

    // 7. After payment confirmation, should be redirected to cabinet
    await page.waitForURL(/\/cabinet/, { timeout: 10000 });

    // 8. Verify subscription is active
    await page.goto('/cabinet/subscriptions');
    await expect(page.locator('text=Basic')).toBeVisible();
    await expect(page.locator('text=active')).toBeVisible();

    // 9. Try to access premium feature (should be denied)
    await page.goto('/premium-feature');
    await expect(page.locator('text=Upgrade Required')).toBeVisible();

    // 10. Access allowed basic features
    await page.goto('/basic-feature');
    await expect(page.locator('text=Basic Feature')).toBeVisible();
  });

  test('existing user can login and manage account', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'existing@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Should redirect to cabinet
    await expect(page).toHaveURL(/\/cabinet/);

    // Navigate to profile
    await page.click('text=Profile');
    await expect(page).toHaveURL(/\/cabinet\/profile/);

    // Edit profile
    await page.fill('input[name="firstName"]', 'Jane');
    await page.click('button:has-text("Save Changes")');
    await expect(page.locator('text=Profile updated successfully')).toBeVisible();

    // View subscriptions
    await page.click('text=Subscriptions');
    await expect(page.locator('[data-testid="subscription-card"]')).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('wizard has proper ARIA labels', async ({ page }) => {
    await page.goto('/wizard');

    // Check for proper labels
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toHaveAttribute('aria-label');

    // Check for proper headings hierarchy
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();

    // Check for keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('forms have proper validation messages', async ({ page }) => {
    await page.goto('/wizard');

    // Try to submit without files
    await page.click('button:has-text("Next")');

    // Should show validation message
    await expect(page.locator('[role="alert"]')).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('wizard loads in under 2 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/wizard');
    await page.waitForSelector('h1');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000);
  });

  test('plan loading is under 1 second', async ({ page }) => {
    await page.goto('/wizard');

    // Navigate to plans step
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(['tests/fixtures/sample-image-1.jpg']);
    await page.click('button:has-text("Next")');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.check('input[type="checkbox"]');
    await page.click('button:has-text("Next")');

    // Measure plan loading time
    const startTime = Date.now();
    await page.waitForSelector('text=Basic');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(1000);
  });
});

test.describe('Mobile Responsive', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test('wizard works on mobile', async ({ page }) => {
    await page.goto('/wizard');

    // Should have mobile-optimized layout
    const container = page.locator('.wizard-container');
    const boundingBox = await container.boundingBox();

    expect(boundingBox?.width).toBeLessThanOrEqual(375);

    // Should be able to upload files
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(['tests/fixtures/sample-image-1.jpg']);
    await expect(page.locator('text=sample-image-1.jpg')).toBeVisible();
  });
});
```

---

### 5.6 CI/CD Integration

**File:** `.github/workflows/frontend-tests.yml`

```yaml
name: Frontend Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        working-directory: ./frontend/user/vue
        run: npm ci

      - name: Run linter
        working-directory: ./frontend/user/vue
        run: npm run lint

      - name: Run unit tests
        working-directory: ./frontend/user/vue
        run: npm run test:unit

      - name: Install Playwright
        working-directory: ./frontend/user/vue
        run: npx playwright install --with-deps

      - name: Run E2E tests
        working-directory: ./frontend/user/vue
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: frontend/user/vue/playwright-report/

      - name: Build
        working-directory: ./frontend/user/vue
        run: npm run build
```

---

## Testing Checklist

- [ ] Access control blocks unauthorized users
- [ ] Upgrade prompts shown for restricted content
- [ ] Route guards redirect to upgrade page
- [ ] Component directive hides restricted UI
- [ ] E2E tests cover all user journeys
- [ ] Accessibility tests pass (WCAG 2.1 AA)
- [ ] Performance metrics meet targets
- [ ] Mobile responsive tests pass
- [ ] Cross-browser tests pass

---

## Definition of Done

- [ ] Access control system fully implemented
- [ ] Route guards protect restricted routes
- [ ] Component-level access control works
- [ ] Upgrade prompts functional
- [ ] Comprehensive E2E test suite (90%+ coverage)
- [ ] Accessibility compliance verified
- [ ] Performance benchmarks met
- [ ] CI/CD pipeline configured
- [ ] All tests pass
- [ ] Documentation updated

---

## Project Complete

All frontend sprints completed. Platform ready for plugin development and extensions.
