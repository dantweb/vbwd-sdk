# TODO: Checkout Page Enhancements

**Created:** 2026-01-22
**Priority:** HIGH

## Overview
Implement the full checkout flow as described in requirements.

---

## Backend Tasks

### 1. Email Check Endpoint
**File:** `vbwd-backend/src/routes/auth.py`
```python
@auth_bp.route("/check-email", methods=["GET"])
def check_email():
    email = request.args.get("email")
    # Return { "exists": bool, "can_login": bool }
```
- [ ] Create endpoint
- [ ] Add rate limiting
- [ ] Write unit tests
- [ ] Write integration tests

### 2. Payment Methods API
**File:** `vbwd-backend/src/routes/settings.py` or new route
```python
@settings_bp.route("/payment-methods", methods=["GET"])
def get_payment_methods():
    # Return list of enabled payment methods
```
- [ ] Create model for PaymentMethod (or use config)
- [ ] Create endpoint
- [ ] Return: `[{ id, name, description, icon_url }]`
- [ ] Write tests

### 3. Terms and Conditions API
**File:** `vbwd-backend/src/routes/settings.py`
```python
@settings_bp.route("/terms", methods=["GET"])
def get_terms():
    # Return terms content or URL
```
- [ ] Create endpoint
- [ ] Support URL or inline content
- [ ] Write tests

### 4. Guest Registration Event Handler
**File:** `vbwd-backend/src/handlers/guest_registration_handler.py`
- [ ] Create GuestRegistrationEvent
- [ ] Handle registration during checkout
- [ ] Link to checkout flow

---

## Frontend Tasks

### 1. Email Block Component
**File:** `vbwd-frontend/user/vue/src/components/checkout/EmailBlock.vue`
- [ ] Email input with validation
- [ ] Debounced API call to check-email
- [ ] States: unchecked, checking, new_user, existing_user
- [ ] Sign Up / Login button
- [ ] Green highlight on successful login

### 2. Billing Address Component
**File:** `vbwd-frontend/user/vue/src/components/checkout/BillingAddress.vue`
- [ ] Street, City, Zip, Country fields
- [ ] Country dropdown
- [ ] Validation
- [ ] Auto-fill from profile if logged in

### 3. Payment Methods Component
**File:** `vbwd-frontend/user/vue/src/components/checkout/PaymentMethods.vue`
- [ ] Fetch methods from API
- [ ] Radio button selection
- [ ] Method icons/descriptions
- [ ] Selected method stored in checkout store

### 4. Terms Checkbox Component
**File:** `vbwd-frontend/user/vue/src/components/checkout/TermsCheckbox.vue`
- [ ] Checkbox with label
- [ ] Link opens popup/modal
- [ ] Fetch terms content from API
- [ ] Track acceptance in store

### 5. Update Checkout.vue
**File:** `vbwd-frontend/user/vue/src/views/Checkout.vue`
- [ ] Remove auth requirement (allow guest)
- [ ] Add EmailBlock component
- [ ] Add BillingAddress component
- [ ] Add PaymentMethods component
- [ ] Add TermsCheckbox component
- [ ] Update Pay button logic
- [ ] Handle registration flow

### 6. Update Checkout Store
**File:** `vbwd-frontend/user/vue/src/stores/checkout.ts`
- [ ] Add email verification state
- [ ] Add billing address state
- [ ] Add payment method state
- [ ] Add terms acceptance state
- [ ] Add canPay computed property
- [ ] Add login/register actions

---

## E2E Tests to Create

### 1. checkout-email.spec.ts
- [ ] Email input visible
- [ ] Check email API called on input
- [ ] New user: password field appears
- [ ] Existing user: login hint appears
- [ ] Login success: block turns green

### 2. checkout-billing.spec.ts
- [ ] Billing address fields visible
- [ ] Fields required for submission
- [ ] Validation errors displayed
- [ ] Auto-fill for logged in users

### 3. checkout-payment.spec.ts
- [ ] Payment methods loaded from API
- [ ] Methods displayed as options
- [ ] Selection required
- [ ] Selected method persists

### 4. checkout-conditions.spec.ts
- [ ] Checkbox visible
- [ ] Link opens popup with terms
- [ ] Pay button disabled until checked
- [ ] Pay button enabled when all requirements met

---

## Data Test IDs to Add

```
[data-testid="email-block"]
[data-testid="email-input"]
[data-testid="email-check-loading"]
[data-testid="email-new-user"]
[data-testid="email-existing-user"]
[data-testid="password-input"]
[data-testid="signup-button"]
[data-testid="login-button"]
[data-testid="email-block-success"]

[data-testid="billing-address-block"]
[data-testid="billing-street"]
[data-testid="billing-city"]
[data-testid="billing-zip"]
[data-testid="billing-country"]

[data-testid="payment-methods-block"]
[data-testid="payment-method-invoice"]
[data-testid="payment-method-stripe"]
[data-testid="payment-method-selected"]

[data-testid="terms-checkbox"]
[data-testid="terms-link"]
[data-testid="terms-popup"]
[data-testid="pay-button"]
[data-testid="pay-button-disabled"]
```

---

## Acceptance Criteria

1. User can enter email and see if registered
2. New users can create password on checkout
3. Existing users can login on checkout
4. Billing address is collected
5. Payment method must be selected
6. Terms must be accepted
7. Pay button activates only when all requirements met
8. Invoice payment method creates pending invoice
9. All flows have E2E test coverage
