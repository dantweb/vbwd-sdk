# Task 07: E2E Flow Tests for User CRUD

**Priority:** High
**Type:** Frontend (E2E Tests)
**Estimate:** Medium
**Depends On:** Task 05 (Align User Update API)

## Objective

Create comprehensive E2E tests that prove the entire user management flow works:
1. Create a new user
2. View user in list
3. View user details
4. Edit user
5. Verify changes persisted

## Test File

**Path:** `vbwd-frontend/admin/vue/tests/e2e/admin-user-crud-flow.spec.ts`

## Test Implementation

```typescript
/**
 * E2E Tests: User CRUD Flow
 *
 * Tests the complete user management lifecycle:
 * Create -> View -> Edit -> Verify
 *
 * Run with: E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-crud-flow
 */
import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateViaNavbar, waitForView } from './helpers/auth';

// Generate unique email for test isolation
const testEmail = `e2e.user.${Date.now()}@test.local`;
const testPassword = 'TestPass123@';

test.describe('User CRUD Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should create a new user', async ({ page }) => {
    // Navigate to users
    await navigateViaNavbar(page, 'users');
    await waitForView(page, 'users-view');

    // Click Create User button
    await page.locator('[data-testid="create-user-button"]').click();
    await expect(page.locator('[data-testid="user-create-view"]')).toBeVisible();

    // Fill in user form
    await page.locator('#email').fill(testEmail);
    await page.locator('#password').fill(testPassword);
    await page.locator('#status').selectOption('active');
    await page.locator('#role').selectOption('user');
    await page.locator('#firstName').fill('E2E');
    await page.locator('#lastName').fill('TestUser');

    // Submit form
    await page.locator('[data-testid="submit-button"]').click();

    // Should redirect to user details
    await expect(page).toHaveURL(/\/admin\/users\/[\w-]+$/);
    await expect(page.locator('[data-testid="user-details-view"]')).toBeVisible();

    // Verify user data is displayed
    await expect(page.locator('text=' + testEmail)).toBeVisible();
  });

  test('should find created user in list', async ({ page }) => {
    await navigateViaNavbar(page, 'users');
    await waitForView(page, 'users-view');

    // Search for the user
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill(testEmail);
    await searchInput.press('Enter');
    await page.waitForTimeout(500);

    // User should appear in table
    await expect(page.locator(`text=${testEmail}`)).toBeVisible();
  });

  test('should edit user details', async ({ page }) => {
    await navigateViaNavbar(page, 'users');
    await waitForView(page, 'users-view');

    // Search and click on user
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill(testEmail);
    await searchInput.press('Enter');
    await page.waitForTimeout(500);

    // Click on user row
    await page.locator(`text=${testEmail}`).click();
    await expect(page.locator('[data-testid="user-details-view"]')).toBeVisible();

    // Click Edit button
    await page.locator('[data-testid="edit-button"]').click();
    await expect(page.locator('[data-testid="user-edit-view"]')).toBeVisible();

    // Modify user data
    await page.locator('#firstName').fill('Updated');
    await page.locator('#lastName').fill('Name');

    // Submit changes
    await page.locator('[data-testid="submit-button"]').click();

    // Should return to details with updated data
    await expect(page.locator('[data-testid="user-details-view"]')).toBeVisible();
  });

  test('should verify changes persisted', async ({ page }) => {
    await navigateViaNavbar(page, 'users');
    await waitForView(page, 'users-view');

    // Search for user
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill(testEmail);
    await searchInput.press('Enter');
    await page.waitForTimeout(500);

    // Click on user
    await page.locator(`text=${testEmail}`).click();
    await expect(page.locator('[data-testid="user-details-view"]')).toBeVisible();

    // Verify updated name is displayed
    await expect(page.locator('text=Updated Name')).toBeVisible();
  });

  test('should suspend and reactivate user', async ({ page }) => {
    await navigateViaNavbar(page, 'users');
    await waitForView(page, 'users-view');

    // Search and click on user
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill(testEmail);
    await searchInput.press('Enter');
    await page.waitForTimeout(500);
    await page.locator(`text=${testEmail}`).click();

    // Suspend user
    await page.locator('[data-testid="suspend-button"]').click();
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="status-inactive"]')).toBeVisible();

    // Reactivate user
    await page.locator('[data-testid="activate-button"]').click();
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="status-active"]')).toBeVisible();
  });
});
```

## Running the Tests

```bash
cd vbwd-frontend/admin/vue

# Run only this test file
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-crud-flow

# Run with UI for debugging
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-crud-flow --ui

# Run headed to see browser
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-crud-flow --headed
```

## Acceptance Criteria

- [ ] Test creates new user successfully
- [ ] Test finds user in list after creation
- [ ] Test edits user and saves changes
- [ ] Test verifies changes persisted after reload
- [ ] Test suspends and reactivates user
- [ ] All tests pass in CI environment
- [ ] Tests use unique emails for isolation
