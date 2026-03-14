# Sprint 1: E2E Test Analysis - Plans → Checkout Flow

**Date:** 2026-01-22
**Status:** COMPLETED

## Objective
Check if E2E Playwright tests exist for the `/plans` (tarifs) → `/checkout` flow and analyze their coverage.

## Route Naming Note
- The user-facing route for tariff plans is `/plans` (not `/tarifs`)
- The checkout route is `/checkout/:planSlug`

## Existing E2E Tests Found

### 1. `plan-switching.spec.ts` (15 tests)

| Test | Status | Description |
|------|--------|-------------|
| displays available plans | ✅ EXISTS | Opens /plans, checks plans-grid visible |
| shows plan details with price | ✅ EXISTS | Verifies plan cards have prices |
| can select a plan and navigate to checkout | ✅ EXISTS | Clicks select button, expects /checkout/ URL |
| checkout page shows order summary | ✅ EXISTS | Verifies order-summary, plan-name, plan-price |
| checkout page has confirm button | ✅ EXISTS | Checks confirm-checkout button visible |
| completing checkout creates invoice | ✅ EXISTS | Full flow, checks INV-* number |
| checkout success shows subscription status | ✅ EXISTS | Verifies subscription-status element |
| checkout success shows payment required message | ✅ EXISTS | Verifies payment-required-message |
| checkout success shows invoice line items | ✅ EXISTS | Verifies invoice-line-items |
| can navigate to invoice after checkout | ✅ EXISTS | Clicks view-invoice-btn |
| new invoice appears in invoices list | ✅ EXISTS | Searches for invoice after checkout |
| can add token bundle to checkout | ✅ EXISTS | Adds 1000 token bundle |
| invoice includes token bundle after checkout | ✅ EXISTS | Verifies line-item-token_bundle |

### 2. `checkout/checkout-display.spec.ts` (5 tests)

| Test | Status | Description |
|------|--------|-------------|
| displays plan details in order summary | ✅ EXISTS | order-summary, plan-name, plan-price |
| displays confirm button | ✅ EXISTS | confirm-checkout visible and enabled |
| shows loading state while fetching plan | ✅ EXISTS | checkout-loading visible during fetch |
| shows error for invalid plan slug | ✅ EXISTS | checkout-error for invalid-plan-slug |
| redirects unauthenticated user to login | ✅ EXISTS | Clears auth, expects /login redirect |

### 3. `checkout/checkout-submit.spec.ts` (7 tests)

| Test | Status | Description |
|------|--------|-------------|
| creates pending subscription | ✅ EXISTS | Verifies subscription status |
| shows invoice number | ✅ EXISTS | INV-* format |
| shows payment required message | ✅ EXISTS | payment-required-message |
| shows line items | ✅ EXISTS | invoice-line-items with 3 items |
| loading state during submission | ✅ EXISTS | checkout-submitting visible |
| handles API errors | ✅ EXISTS | Error handling test |
| disables button during submission | ✅ EXISTS | confirm-checkout disabled |

### 4. `checkout/token-bundles.spec.ts` (3 tests)

| Test | Status | Description |
|------|--------|-------------|
| displays available bundles | ✅ EXISTS | token-bundles-section visible |
| updates total price when added | ✅ EXISTS | order-total changes |
| can add/remove bundles | ⚠️ DATA POLLUTION | Test affected by duplicate data |

### 5. `checkout/addons.spec.ts` (3 tests)

| Test | Status | Description |
|------|--------|-------------|
| displays available add-ons | ✅ EXISTS | addons-section visible |
| shows addon description | ⚠️ DATA POLLUTION | 30+ duplicate add-ons |
| shows addon price | ✅ EXISTS | addon-*-price visible |

## Missing Tests for New Requirements

Based on the user's requirements, the following tests are **NOT implemented** because the functionality doesn't exist yet:

| Feature | Test Needed | Status |
|---------|-------------|--------|
| Email block on checkout | Check email input, Sign Up/Login buttons | ❌ NOT IMPLEMENTED |
| Email verification (is registered?) | API call, field state change | ❌ NOT IMPLEMENTED |
| "Create password" field | Field appears for new users | ❌ NOT IMPLEMENTED |
| Login hint for registered users | Red flyout/hint appears | ❌ NOT IMPLEMENTED |
| Billing Address block | Address fields visible | ❌ NOT IMPLEMENTED |
| Payment methods block | Methods from API visible | ❌ NOT IMPLEMENTED |
| "Agree with conditions" checkbox | Checkbox, URL popup | ❌ NOT IMPLEMENTED |
| Pay button state | Disabled until requirements met | ❌ NOT IMPLEMENTED |

## Current Checkout Page Elements (data-testid)

```
[data-testid="checkout-loading"]     - Loading spinner
[data-testid="checkout-error"]       - Error message
[data-testid="checkout-success"]     - Success container
[data-testid="order-summary"]        - Order summary card
[data-testid="plan-name"]            - Plan name text
[data-testid="plan-price"]           - Plan price text
[data-testid="order-total"]          - Total amount
[data-testid="token-bundles-section"]- Token bundles container
[data-testid="token-bundle-*"]       - Token bundle option
[data-testid="addons-section"]       - Add-ons container
[data-testid="addon-*"]              - Add-on option
[data-testid="confirm-checkout"]     - Submit button
[data-testid="checkout-submitting"]  - Submitting state
[data-testid="invoice-number"]       - Invoice number
[data-testid="invoice-line-items"]   - Line items container
[data-testid="subscription-status"]  - Subscription status
[data-testid="payment-required-message"] - Payment message
```

## Proposed New E2E Test Structure

For the requested checkout form functionality, create:

```
tests/e2e/checkout/
├── checkout-display.spec.ts     ✅ EXISTS
├── checkout-submit.spec.ts      ✅ EXISTS
├── token-bundles.spec.ts        ✅ EXISTS
├── addons.spec.ts               ✅ EXISTS
├── post-checkout.spec.ts        ✅ EXISTS
├── checkout-email.spec.ts       ❌ TO CREATE - Email verification flow
├── checkout-billing.spec.ts     ❌ TO CREATE - Billing address form
├── checkout-payment.spec.ts     ❌ TO CREATE - Payment method selection
└── checkout-conditions.spec.ts  ❌ TO CREATE - Terms checkbox and Pay button
```

## Conclusion

**Existing Tests:** 33+ tests covering the current checkout implementation
**Test Quality:** Good coverage of happy path and error states
**Known Issues:** Test data pollution with duplicate add-ons/bundles

**Gap Analysis:** The existing tests cover the CURRENT implementation. The requested features (email verification, billing address, payment methods, conditions checkbox) are NOT yet implemented in the frontend, so tests for them don't exist.

## Recommendation

1. **Do NOT create tests for non-existent functionality** - Tests will fail
2. **First implement the features** in Checkout.vue following TDD
3. **Then create the corresponding E2E tests**
4. **Clean up test data pollution** for reliable test runs
