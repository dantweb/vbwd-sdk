# Sprint 05: User Frontend Sync & Security

**Date:** 2026-01-12
**Priority:** High
**Type:** Feature Implementation + E2E Testing + Security
**Section:** User Dashboard & Session Management

## Goal

Update the user frontend to stay synchronized with admin changes, enhance the user dashboard with profile details and subscription management, and implement secure session expiration.

## Overview

This sprint covers:
1. **Data Synchronization**: Admin changes reflect on user side (on page refresh)
2. **User Dashboard Enhancement**: Profile, subscriptions, token balance, invoices
3. **Plan Selection**: Active plans listing with checkout flow
4. **Session Security**: Configurable session expiration (72 hours default)

## Clarified Requirements

| Aspect | Decision |
|--------|----------|
| **Data sync** | On page refresh only (no real-time/WebSocket) |
| **Checkout page** | Placeholder only ("Checkout coming soon") |
| **Invoice actions** | View + Download PDF + Pay pending invoices |
| **Session reset** | Only explicit user actions reset timer (not background fetches) |
| **User navigation** | Dashboard, Profile, Subscription, Plans (4 items) |

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required
- **Security First**: Proper session management and access control

### Test Execution

```bash
# User frontend tests
cd ~/dantweb/vbwd-sdk/vbwd-frontend/user/vue
npx playwright test

# Cross-app sync tests (requires both frontends running)
cd ~/dantweb/vbwd-sdk/vbwd-frontend
npx playwright test admin-user-sync
```

### Definition of Done
- [ ] All E2E tests passing (including sync tests)
- [ ] No TypeScript errors
- [ ] ESLint checks pass
- [ ] Admin changes visible on user side
- [ ] User dashboard shows profile, subscriptions, balance, invoices
- [ ] Select a plan page with checkout flow
- [ ] Session expiration working (configurable via ENV)
- [ ] User frontend rebuilt with `make rebuild-user` or equivalent
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

### Build & Deploy

After implementation, rebuild both frontends:

```bash
# From project root
make up-build

# Or individually:
cd vbwd-frontend/user && docker-compose up -d --build
cd vbwd-frontend/admin && docker-compose up -d --build
```

- User dashboard: http://localhost:8080
- Admin dashboard: http://localhost:8081

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`
- User: `test@example.com` / `TestPass123@`

---

## Tasks

### Task 5.1: E2E Tests - Admin-User Data Sync

**Goal:** Write Playwright tests to verify admin changes reflect on user side

**Test Scenarios:**
- [ ] Admin updates user subscription → User sees updated subscription
- [ ] Admin changes plan details → User sees updated plan info
- [ ] Admin creates invoice → User sees new invoice
- [ ] Admin updates user profile → User sees updated profile
- [ ] Admin toggles subscription status → User sees correct status

**Test File:** `tests/e2e/admin-user-sync.spec.ts`

**Test Pattern:**
```typescript
test('admin subscription change reflects on user side', async ({ browser }) => {
  // 1. Login as admin
  const adminPage = await browser.newPage();
  await adminLogin(adminPage);

  // 2. Get user's current subscription state
  const userPage = await browser.newPage();
  await userLogin(userPage);
  const initialState = await getUserSubscription(userPage);

  // 3. Admin makes change
  await adminPage.goto('/subscriptions/user-subscription-id');
  await adminPage.click('[data-testid="cancel-subscription"]');
  await adminPage.waitForSelector('[data-testid="status-cancelled"]');

  // 4. User refreshes and sees change
  await userPage.reload();
  await expect(userPage.locator('[data-testid="subscription-status"]'))
    .toHaveText('Cancelled');
});
```

**Acceptance Criteria:**
- [ ] Tests verify real-time or refresh-based sync
- [ ] Tests cover subscription, invoice, and profile changes
- [ ] Tests use proper data-testid selectors

---

### Task 5.2: Backend - Session Expiration Configuration

**Goal:** Add configurable session expiration via environment variables

**Environment Variables:**
```bash
# vbwd-backend/.env
USER_SESSION_EXPIRY_HOURS=72    # Default 72 hours for user dashboard
ADMIN_SESSION_EXPIRY_HOURS=24   # Default 24 hours for admin dashboard
```

**Implementation:**
- Add to `.env.example`
- Update config.py to read these values
- Modify JWT token generation to use these values
- Add middleware to check session expiry based on last activity

**Files to Modify:**
- `vbwd-backend/.env.example`
- `vbwd-backend/src/config.py`
- `vbwd-backend/src/services/auth_service.py`
- `vbwd-backend/src/routes/auth.py`

**Session Logic:**
```python
# Session expires after X hours since last USER ACTION (not background fetches)
# Only explicit user actions (clicks, form submits) update last_activity timestamp
# Background API calls (data fetches) do NOT reset the timer
# If current_time - last_activity > SESSION_EXPIRY, invalidate session
```

**Implementation Notes:**
- Add header `X-User-Action: true` on explicit user actions
- Backend only updates `last_activity` when this header is present
- Background fetches don't include this header

**Acceptance Criteria:**
- [ ] USER_SESSION_EXPIRY_HOURS configurable (default 72)
- [ ] ADMIN_SESSION_EXPIRY_HOURS configurable (default 24)
- [ ] Session expires after configured hours of inactivity
- [ ] Last activity timestamp updated on each request

---

### Task 5.3: Frontend User - Dashboard Enhancement

**Goal:** Enhance user dashboard with profile, subscriptions, balance, invoices

**Dashboard Sections:**

1. **Profile Summary** (top section)
   - User name
   - Email
   - Account status
   - Link to full profile

2. **Current Subscription** (main section)
   - Plan name
   - Status badge
   - Billing period
   - Next billing date
   - Token balance (from user_details.balance)
   - "Manage Subscription" button

3. **Recent Invoices** (bottom section)
   - Last 5 invoices
   - Invoice number, amount, status, date
   - "View All Invoices" link

**Files to Modify:**
- `vbwd-frontend/user/vue/src/views/Dashboard.vue`

**Acceptance Criteria:**
- [ ] Dashboard shows profile summary
- [ ] Dashboard shows current subscription with token balance
- [ ] Dashboard shows recent invoices
- [ ] All data loads correctly from API

---

### Task 5.4: Frontend User - Profile Page Enhancement

**Goal:** Extend Profile page with full user details

**Profile Fields:**
- Email (readonly)
- First Name
- Last Name
- Company
- Tax Number
- Phone
- Address Line 1
- Address Line 2
- City
- Postal Code
- Country
- Token Balance (readonly, display only)

**Files to Modify:**
- `vbwd-frontend/user/vue/src/views/Profile.vue`

**Acceptance Criteria:**
- [ ] All user details fields displayed
- [ ] Editable fields can be updated
- [ ] Balance shown as readonly
- [ ] Save functionality works

---

### Task 5.5: Frontend User - Subscription Page

**Goal:** Create comprehensive subscription page

**Subscription Page Sections:**

1. **Current Subscription Card**
   - Plan name and description
   - Status (Active/Cancelled/Trial/etc.)
   - Current period dates
   - Price and billing cycle
   - Token balance

2. **Token Balance Section**
   - Current balance display
   - "Purchase Tokens" button (future: links to token bundles)

3. **Invoices Table** (sortable, searchable)
   - Columns: Invoice #, Date, Amount, Status, Actions
   - Sortable by any column
   - Quick search filter
   - Pagination
   - Click row to view invoice details
   - Actions: View, Download PDF, Pay (for pending invoices)

**Route:** `/subscription`

**Files to Create:**
- `vbwd-frontend/user/vue/src/views/Subscription.vue`

**Files to Modify:**
- `vbwd-frontend/user/vue/src/router/index.ts`

**Acceptance Criteria:**
- [ ] Current subscription data displayed
- [ ] Token balance visible
- [ ] Invoices table with sorting and search
- [ ] Pagination works
- [ ] Click invoice opens detail view

---

### Task 5.6: Frontend User - Select a Plan Page

**Goal:** Create page to browse and select subscription plans

**Select Plan Page:**

1. **Plan Cards Grid**
   - Only active plans displayed (is_active = true)
   - Plan name and description
   - Price and billing period
   - Feature highlights
   - "Select" button

2. **Plan Selection Flow**
   - Click "Select" on plan
   - Navigate to `/checkout?plan=<plan_id>`

3. **Checkout Page (Placeholder)**
   - Shows selected plan info
   - Displays "Checkout coming soon" message
   - Back button to return to plans

**Route:** `/plans` and `/checkout`

**Files to Create:**
- `vbwd-frontend/user/vue/src/views/SelectPlan.vue`
- `vbwd-frontend/user/vue/src/views/Checkout.vue` (placeholder with "coming soon")

**Files to Modify:**
- `vbwd-frontend/user/vue/src/router/index.ts`

**API Endpoint:**
```
GET /api/v1/tarif-plans?active=true
```

**Acceptance Criteria:**
- [ ] Only active plans shown
- [ ] Plan details displayed correctly
- [ ] Select button navigates to checkout
- [ ] Checkout page receives plan ID

---

### Task 5.7: Frontend User - Access Control & Session

**Goal:** Implement proper access control and session expiration UI

**Security Requirements:**

1. **Route Guards**
   - All dashboard routes require authentication
   - Redirect to login if not authenticated
   - Redirect to login if session expired

2. **Session Expiration Handling**
   - Check session validity on each route change
   - Show "Session expired" message on login page
   - Clear local storage on session expiry

3. **API Interceptor**
   - On 401 response, redirect to login
   - Show appropriate message

**Files to Modify:**
- `vbwd-frontend/user/vue/src/router/index.ts` (guards)
- `vbwd-frontend/user/vue/src/api/index.ts` (interceptor)
- `vbwd-frontend/user/vue/src/stores/auth.ts`

**Acceptance Criteria:**
- [ ] Unauthenticated users cannot access dashboard
- [ ] Expired sessions redirect to login
- [ ] 401 responses handled gracefully
- [ ] Session expiry message shown

---

### Task 5.8: E2E Tests - User Dashboard & Session

**Goal:** Write E2E tests for user dashboard and session expiration

**Test Requirements:**
- [ ] Dashboard loads with all sections
- [ ] Profile page shows all fields
- [ ] Subscription page shows current subscription
- [ ] Invoices table sorting works
- [ ] Invoices table search works
- [ ] Select plan page shows active plans only
- [ ] Checkout redirect works
- [ ] Unauthenticated access redirects to login

**Test Files:**
- `tests/e2e/user-dashboard.spec.ts`
- `tests/e2e/user-subscription.spec.ts`
- `tests/e2e/user-select-plan.spec.ts`
- `tests/e2e/user-session.spec.ts`

**Acceptance Criteria:**
- [ ] All user flow tests pass
- [ ] Session expiration tested
- [ ] Access control tested

---

### Task 5.9: Integration & Final Testing

**Goal:** Full integration testing of admin-user sync and security

**Test Flow:**
1. Admin logs in, modifies user subscription
2. User logs in, sees updated subscription
3. User browses plans, selects one
4. User views subscription and invoices
5. Session expires after inactivity
6. User redirected to login

**Commands:**
```bash
# Run all E2E tests
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --user --e2e
./bin/pre-commit-check.sh --admin --e2e

# Run sync-specific tests
npx playwright test admin-user-sync
```

**Acceptance Criteria:**
- [ ] All E2E tests pass
- [ ] Manual QA complete
- [ ] No console errors
- [ ] Security verified

---

## Environment Variables

### Backend (.env)

```bash
# Session configuration
USER_SESSION_EXPIRY_HOURS=72     # User dashboard session (default: 72 hours)
ADMIN_SESSION_EXPIRY_HOURS=24    # Admin dashboard session (default: 24 hours)
```

### Frontend User (.env)

```bash
# Optional: can read from API or hardcode
VITE_SESSION_CHECK_INTERVAL=60000  # Check session every 60 seconds
```

### Frontend Admin (.env)

```bash
VITE_SESSION_CHECK_INTERVAL=60000  # Check session every 60 seconds
```

---

## API Endpoints (User)

### Get User Dashboard Data
```
GET /api/v1/user/dashboard
Authorization: Bearer <token>

Response 200:
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "details": {
      "first_name": "John",
      "last_name": "Doe",
      "balance": 150.00,
      ...
    }
  },
  "subscription": {
    "id": "uuid",
    "plan": { "name": "Pro", "price": 29.99 },
    "status": "active",
    "current_period_end": "2026-02-12",
    ...
  },
  "recent_invoices": [
    { "id": "uuid", "number": "INV-001", "amount": 29.99, "status": "paid" }
  ]
}
```

### Get User Invoices (Paginated)
```
GET /api/v1/user/invoices?page=1&per_page=20&sort=created_at&order=desc&search=INV
Authorization: Bearer <token>

Response 200:
{
  "items": [...],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### Get Active Plans
```
GET /api/v1/tarif-plans?active=true

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "name": "Basic",
      "description": "...",
      "price": 9.99,
      "billing_period": "monthly",
      "is_active": true
    }
  ]
}
```

---

## Files Summary

### Backend - Modify
- `.env.example`
- `src/config.py`
- `src/services/auth_service.py`
- `src/routes/auth.py`
- `src/routes/user/` (dashboard endpoint)

### Frontend User - Create
- `src/views/Subscription.vue`
- `src/views/SelectPlan.vue`
- `src/views/Checkout.vue`
- `tests/e2e/user-dashboard.spec.ts`
- `tests/e2e/user-subscription.spec.ts`
- `tests/e2e/user-select-plan.spec.ts`
- `tests/e2e/user-session.spec.ts`
- `tests/e2e/admin-user-sync.spec.ts`

### Frontend User - Modify
- `src/views/Dashboard.vue`
- `src/views/Profile.vue`
- `src/router/index.ts`
- `src/api/index.ts`
- `src/stores/auth.ts`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 5.1 E2E Tests - Admin-User Sync | ⏳ Pending | |
| 5.2 Backend - Session Expiration | ⏳ Pending | |
| 5.3 User Dashboard Enhancement | ⏳ Pending | |
| 5.4 User Profile Enhancement | ⏳ Pending | |
| 5.5 User Subscription Page | ⏳ Pending | |
| 5.6 User Select Plan Page | ⏳ Pending | |
| 5.7 User Access Control & Session | ⏳ Pending | |
| 5.8 E2E Tests - User Dashboard | ⏳ Pending | |
| 5.9 Integration & Final Testing | ⏳ Pending | |
