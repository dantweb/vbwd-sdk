# Sprint 06: Full Integration Testing

**Date:** 2026-01-13
**Priority:** High
**Type:** Integration Testing
**Section:** User Checkout Flow
**Prerequisite:** Sprint 01-05 (All previous sprints)

## Goal

Verify the complete checkout flow works end-to-end with real services.

## Test Scenarios

### Scenario 1: Basic Subscription Checkout

**Steps:**
1. User logs in
2. User navigates to /plans
3. User selects Pro plan
4. User arrives at /checkout/pro
5. User clicks "Confirm Purchase"
6. Subscription created as PENDING
7. Invoice created with subscription line item
8. User sees pending status

**Expected:**
- Subscription status = "pending"
- Invoice status = "pending"
- Invoice has 1 line item (subscription)

---

### Scenario 2: Checkout with Token Bundle

**Steps:**
1. User logs in
2. User navigates to /checkout/pro
3. User adds 1000 token bundle
4. User clicks "Confirm Purchase"
5. Subscription and bundle purchase created as PENDING
6. Invoice created with 2 line items
7. User token balance = 0 (not credited yet)

**Expected:**
- Subscription status = "pending"
- Bundle purchase status = "pending"
- Invoice has 2 line items
- User token balance = 0

---

### Scenario 3: Checkout with Add-on

**Steps:**
1. User logs in
2. User navigates to /checkout/pro
3. User adds Priority Support add-on
4. User clicks "Confirm Purchase"
5. Subscription and add-on created as PENDING
6. Add-on linked to parent subscription

**Expected:**
- Subscription status = "pending"
- Add-on subscription status = "pending"
- Add-on subscription_id = subscription.id

---

### Scenario 4: Payment Activates Everything

**Steps:**
1. Complete Scenario 2 (checkout with bundle)
2. Admin/webhook marks invoice as paid
3. PaymentCapturedEvent processed
4. Subscription becomes ACTIVE
5. Tokens credited to user balance
6. User can see active subscription
7. User can see token balance

**Expected:**
- Subscription status = "active"
- Bundle purchase status = "completed"
- User token balance = 1000
- Invoice status = "paid"

---

### Scenario 5: Full Checkout with All Items

**Steps:**
1. User logs in
2. User navigates to /checkout/pro
3. User adds 1000 token bundle
4. User adds 5000 token bundle
5. User adds Priority Support add-on
6. User clicks "Confirm Purchase"
7. Invoice has 4 line items
8. Admin marks invoice paid
9. All items activated

**Expected:**
- Invoice line items = 4 (1 sub + 2 bundles + 1 addon)
- After payment: subscription active, tokens = 6000, addon active

---

## Tasks

### Task 6.1: Manual Testing Checklist

```markdown
## Manual Test Checklist

### Prerequisites
- [ ] Backend running (make up)
- [ ] Frontend running (make dev)
- [ ] Database seeded with test data
- [ ] Test user exists (test@example.com / TestPass123@)

### Basic Checkout
- [ ] Can navigate to /plans
- [ ] Can select a plan
- [ ] Redirected to /checkout/:slug
- [ ] Plan details displayed
- [ ] Can click Confirm Purchase
- [ ] Success screen shows pending status
- [ ] Invoice number displayed

### Token Bundles
- [ ] Token bundles section visible
- [ ] Can add bundle to order
- [ ] Order total updates
- [ ] Can remove bundle
- [ ] Bundle appears in invoice

### Add-ons
- [ ] Add-ons section visible
- [ ] Can add addon to order
- [ ] Addon shows description
- [ ] Addon shows price
- [ ] Addon appears in invoice

### Payment Flow
- [ ] Can trigger payment webhook
- [ ] Subscription becomes active
- [ ] Tokens credited
- [ ] Add-ons activated

### Error Handling
- [ ] Invalid plan shows error
- [ ] Unauthenticated redirects to login
- [ ] API error shows message
```

---

### Task 6.2: Run All E2E Tests

```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/user/vue

# Run all checkout E2E tests
npx playwright test tests/e2e/checkout/ --reporter=html

# Open report
npx playwright show-report
```

---

### Task 6.3: Run All Backend Tests

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run all tests with coverage
docker-compose run --rm test pytest tests/ -v --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

### Task 6.4: Run Full Stack Test

```bash
cd ~/dantweb/vbwd-sdk

# Start all services
make up

# In another terminal, run E2E tests against real backend
cd vbwd-frontend/user/vue
E2E_BASE_URL=http://localhost:8080 npx playwright test tests/e2e/checkout/
```

---

### Task 6.5: Document Test Results

Create test report with:
- Number of tests passed/failed
- Code coverage percentage
- Any known issues
- Screenshots of key flows

---

## Build & Test Commands

**IMPORTANT:** Always rebuild and run tests after making changes.

### Rebuild All Services
```bash
cd ~/dantweb/vbwd-sdk

# Rebuild and restart all services
make up

# Or rebuild specific parts:
cd vbwd-backend && make up-build
cd vbwd-frontend && make dev-user
```

### Run Backend Tests with Pre-Commit Script
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run all quality checks (lint + unit + integration)
./bin/pre-commit-check.sh

# Quick check (skip integration tests)
./bin/pre-commit-check.sh --quick

# Only run specific checks
./bin/pre-commit-check.sh --lint        # Static analysis only (black, flake8, mypy)
./bin/pre-commit-check.sh --unit        # Unit tests only
./bin/pre-commit-check.sh --integration # Integration tests only
```

### Run Frontend Tests with Pre-Commit Script
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend

# Run style checks for all apps
./bin/pre-commit-check.sh

# Run user app tests
./bin/pre-commit-check.sh --user --unit    # Unit tests
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# Run everything
./bin/pre-commit-check.sh --all
```

---

## Definition of Done

- [ ] All E2E tests pass
- [ ] All backend tests pass
- [ ] Manual testing checklist completed
- [ ] No critical bugs found
- [ ] Test report created
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 6.1 Manual Testing | ⏳ Pending | |
| 6.2 E2E Tests | ⏳ Pending | |
| 6.3 Backend Tests | ⏳ Pending | |
| 6.4 Full Stack Test | ⏳ Pending | |
| 6.5 Document Results | ⏳ Pending | |

---

## Completion

When all sprints are done:
1. Move all sprint files to `/done`
2. Create final report in `/reports`
3. Update `/status.md` with completion status
