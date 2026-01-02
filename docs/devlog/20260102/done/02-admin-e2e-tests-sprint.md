# Sprint: Admin E2E Playwright Tests

**Sprint:** Admin Full E2E Test Coverage
**Date:** 2026-01-02
**Status:** IN PROGRESS
**Methodology:** TDD-First, Page Object Model, API Mocking

---

## Objective

Implement comprehensive E2E tests for all admin views using Playwright. Tests will use API mocking to ensure consistent, fast execution without backend dependencies.

---

## Current State

- **Existing E2E:** 1 file (`admin-login.spec.ts`) with 7 tests
- **Views to Test:** 14 views (excluding Login which is already tested)
- **Target:** Full E2E coverage for all admin functionality

---

## Sprint Tasks

### Phase 1: Test Infrastructure

| Task | Status |
|------|--------|
| Create shared test fixtures (`fixtures/admin.ts`) | Pending |
| Create API mock helpers (`helpers/api-mocks.ts`) | Pending |
| Create page object models for reusable interactions | Pending |

### Phase 2: User Management E2E

| Task | Status |
|------|--------|
| `admin-users.spec.ts` - User list view | Pending |
| `admin-user-details.spec.ts` - User details view | Pending |

**Test Cases:**
- Display users list with pagination
- Search users by email
- Filter users by status
- Navigate to user details
- Suspend/activate user
- View user statistics

### Phase 3: Plan Management E2E

| Task | Status |
|------|--------|
| `admin-plans.spec.ts` - Plans list view | Pending |
| `admin-plan-form.spec.ts` - Create/edit plan | Pending |

**Test Cases:**
- Display plans list
- Create new plan with validation
- Edit existing plan
- Archive/restore plan
- Form validation errors

### Phase 4: Subscription Management E2E

| Task | Status |
|------|--------|
| `admin-subscriptions.spec.ts` - Subscriptions list | Pending |
| `admin-subscription-details.spec.ts` - Details view | Pending |

**Test Cases:**
- Display subscriptions with filters
- Filter by status (active, cancelled, expired, trial)
- View subscription details
- Cancel subscription
- View payment history

### Phase 5: Invoice Management E2E

| Task | Status |
|------|--------|
| `admin-invoices.spec.ts` - Invoice list | Pending |
| `admin-invoice-details.spec.ts` - Invoice details | Pending |

**Test Cases:**
- Display invoice list
- Filter by status
- View invoice details with line items
- Resend invoice action
- Void invoice action

### Phase 6: Webhook Management E2E

| Task | Status |
|------|--------|
| `admin-webhooks.spec.ts` - Webhooks list | Pending |
| `admin-webhook-details.spec.ts` - Webhook details | Pending |

**Test Cases:**
- Display webhook list
- Enable/disable webhook
- Delete webhook
- View delivery history
- Test webhook functionality

### Phase 7: Analytics Dashboard E2E

| Task | Status |
|------|--------|
| `admin-analytics.spec.ts` - Analytics view | Pending |

**Test Cases:**
- Display KPI cards (MRR, Revenue, Users, Churn)
- Show plan distribution
- Display recent activity
- Date range filtering
- Refresh functionality

### Phase 8: Settings E2E

| Task | Status |
|------|--------|
| `admin-settings.spec.ts` - Settings view | Pending |

**Test Cases:**
- Display company settings form
- Update billing settings
- Save notification preferences
- Form validation
- Success/error feedback

---

## Test File Structure

```
tests/e2e/
├── fixtures/
│   └── admin.ts           # Shared fixtures (auth, API mocks)
├── helpers/
│   └── api-mocks.ts       # Reusable API mock functions
├── admin-login.spec.ts    # Existing (7 tests)
├── admin-users.spec.ts    # New
├── admin-user-details.spec.ts
├── admin-plans.spec.ts
├── admin-plan-form.spec.ts
├── admin-subscriptions.spec.ts
├── admin-subscription-details.spec.ts
├── admin-invoices.spec.ts
├── admin-invoice-details.spec.ts
├── admin-webhooks.spec.ts
├── admin-webhook-details.spec.ts
├── admin-analytics.spec.ts
└── admin-settings.spec.ts
```

---

## API Mock Strategy

All tests will mock API responses using Playwright's `page.route()`:

```typescript
// Example mock pattern
await page.route('**/api/v1/admin/users', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ users: [...], total: 100 })
  });
});
```

### Mock Data Categories:
- **Users:** List, details, stats
- **Plans:** List, single plan, create/update responses
- **Subscriptions:** List, details, payment history
- **Invoices:** List, details, line items
- **Webhooks:** List, details, delivery history
- **Analytics:** KPIs, plan distribution, activity
- **Settings:** Company info, billing, notifications

---

## Success Criteria

- [ ] All 14 admin views have E2E coverage
- [ ] Tests run in isolation (no backend dependency)
- [ ] Tests complete in < 60 seconds total
- [ ] All tests pass in CI environment
- [ ] Coverage for happy path and error scenarios

---

## Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run specific test file
npx playwright test admin-users.spec.ts

# Run with UI mode
npm run test:e2e:ui

# Run in headed mode
npx playwright test --headed
```

---

*Sprint created: 2026-01-02*
