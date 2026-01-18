# Sprint 01 Completion Report: Frontend E2E Tests (TDD-First)

**Date:** 2026-01-13
**Status:** Completed
**Sprint Type:** Frontend Testing (TDD)

---

## Summary

Sprint 01 established the E2E test specification for the user checkout flow using Playwright. Following TDD principles, these tests define the expected behavior BEFORE implementation. All tests are expected to fail until Sprint 05 (Frontend Implementation) is completed.

---

## Test Statistics

| Metric | Count |
|--------|-------|
| Total Tests | 25 |
| Test Files | 5 |
| Test Fixtures | 1 |

---

## Files Created

### Test Fixtures
- `vbwd-frontend/user/vue/tests/e2e/fixtures/checkout.fixtures.ts`
  - `TEST_USER` credentials
  - `loginAsTestUser()` helper
  - `navigateToCheckout()` helper
  - `selectPlanFromList()` helper

### Test Specifications

| File | Tests | Purpose |
|------|-------|---------|
| `checkout/checkout-display.spec.ts` | 5 | Plan display, loading states, error handling, auth redirect |
| `checkout/token-bundles.spec.ts` | 5 | Token bundle display, selection, removal, price updates |
| `checkout/addons.spec.ts` | 5 | Add-on display, selection, removal, description/price visibility |
| `checkout/checkout-submit.spec.ts` | 8 | Checkout submission, invoice creation, loading states, error handling |
| `checkout/post-checkout.spec.ts` | 3 | Navigation after successful checkout |

---

## Test Coverage by Feature

### Checkout Page Display (5 tests)
1. Displays plan details in order summary
2. Displays confirm button
3. Shows loading state while fetching plan
4. Shows error for invalid plan slug
5. Redirects unauthenticated user to login

### Token Bundle Selection (5 tests)
1. Displays available token bundles
2. Can add token bundle to order
3. Can remove token bundle from order
4. Updates total price when bundle added
5. Can add multiple bundles

### Add-on Selection (5 tests)
1. Displays available add-ons
2. Can add addon to order
3. Can remove addon from order
4. Shows addon description
5. Shows addon price

### Checkout Submission (8 tests)
1. Creates pending subscription on confirm
2. Shows invoice number after checkout
3. Shows payment required message
4. Shows invoice line items after checkout
5. Shows loading state during submission
6. Handles API error gracefully
7. Disables confirm button during submission

### Post-Checkout Navigation (3 tests)
1. Can navigate to subscription page
2. Can navigate to invoices page
3. Can go back to plans

---

## Required data-testid Attributes

For tests to pass, the following `data-testid` attributes must be implemented in the frontend:

### Checkout Page
- `order-summary`
- `plan-name`
- `plan-price`
- `order-total`
- `confirm-checkout`
- `checkout-loading`
- `checkout-error`
- `checkout-submitting`
- `checkout-success`

### Token Bundles
- `token-bundles-section`
- `token-bundle-{amount}` (e.g., `token-bundle-1000`)
- `remove-token-bundle-{amount}`
- `line-item-token-bundle-{id}`

### Add-ons
- `addons-section`
- `addon-{slug}` (e.g., `addon-priority-support`)
- `addon-{slug}-description`
- `addon-{slug}-price`
- `remove-addon-{slug}`

### Post-Checkout
- `subscription-status`
- `invoice-number`
- `invoice-line-item-{id}`
- `payment-required-message`
- `view-subscription-btn`
- `view-invoice-btn`
- `back-to-plans-btn`

---

## API Endpoints Expected

Tests expect the following API endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/tarif-plans/{slug}` | Fetch plan details |
| POST | `/api/v1/user/checkout` | Submit checkout |
| GET | `/api/v1/token-bundles` | List token bundles |
| GET | `/api/v1/addons` | List add-ons |

---

## Running Tests

```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/user

# List all checkout tests
npx playwright test tests/e2e/checkout/ --list

# Run checkout tests (expected to FAIL)
npx playwright test tests/e2e/checkout/

# Run with UI for debugging
npx playwright test tests/e2e/checkout/ --ui
```

---

## TDD Status

| Phase | Status |
|-------|--------|
| Tests Written | Completed |
| Tests Run | Verified (25 tests listed) |
| Expected Result | ALL FAIL |
| Implementation | Sprint 05 |

---

## Next Steps

1. **Sprint 02**: Write backend integration tests (TDD)
2. **Sprint 03**: Implement backend checkout endpoints
3. **Sprint 04**: Implement payment capture
4. **Sprint 05**: Implement frontend to make these tests PASS

---

## Conclusion

Sprint 01 successfully established the E2E test specification for the checkout flow. These 25 tests define the expected behavior and will serve as the acceptance criteria for Sprint 05 (Frontend Implementation).
