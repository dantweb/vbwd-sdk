# E2E Test Current Issues - 2026-01-05

## Current Test Results

**Passing Tests (3/8):**
- Step 1: Navigate to Users page
- Step 4: Navigate to Subscriptions page
- Complete flow: Create user, subscription, verify invoice

**Failing Tests (5/8):**
- Step 2: Create new user with all fields
- Step 3: Verify user appears in list
- Step 5: Create subscription for user
- Step 6: Navigate to Invoices and find user invoice
- Step 7: Verify invoice status is pending

---

## Issue 1: Users Page Not Loading

**Error:**
```
TimeoutError: page.waitForSelector: Timeout 10000ms exceeded.
- waiting for locator('.users-view, .users-header') to be visible
```

**Context:**
- Navigation to `/admin/users` succeeds (Step 1 passes)
- But Step 2 fails when trying to wait for `.users-view` class
- The "Create User" button (`data-testid="create-user-button"`) is not found

**Possible Causes:**
1. Page has error state (API returning 500?)
2. Different loading behavior between test runs
3. Authentication issues (even though login works in beforeEach)

---

## Issue 2: Subscriptions Page - No Create Button

**Error:**
```
Error: locator.click: Test timeout of 30000ms exceeded.
- waiting for locator('button:has-text("Create")').first()
```

**Question:**
Is there a "Create Subscription" button on the Subscriptions page? What is its selector?

---

## Issue 3: Invoices Page - No Results

**Error:**
```
Error: element(s) not found
- waiting for locator('text=e2e.flow.xxx@example.com').first()
```

**Context:**
Tests search for test user email but no invoices are found. This is expected since user creation fails.

---

## Questions for User

1. **Backend API Status**: Is the backend API running and responding correctly? Can you verify:
   - `curl http://localhost:5000/api/v1/admin/users` returns users?
   - `curl http://localhost:5000/api/v1/auth/login` works with admin credentials?

2. **Console Errors**: Can you check the browser DevTools console when visiting `http://localhost:8081/admin/users`? Are there any JavaScript errors?

3. **Subscriptions Page**: Does the Subscriptions page have a "Create" button? What is its data-testid or text label?

4. **Test User Creation**: Should the E2E tests create users via the UI form or should they use API calls to seed data first?

5. **Test Data Setup**: Is there any test data seeding script that should run before E2E tests?

---

## Technical Context

- Vue app now mounts correctly (Pinia dedupe fix worked)
- Login flow works (beforeEach passes)
- Navigation works (Step 1, Step 4 pass)
- Issue seems to be with specific page content not loading
