# Sprint 2: Checkout Functionality Implementation Analysis

**Date:** 2026-01-22
**Status:** COMPLETED

## Objective
Analyze backend and frontend code to determine what checkout functionality is implemented vs. what's described in the requirements.

---

## 1. CURRENT IMPLEMENTATION STATUS

### 1.1 Frontend - Checkout.vue

**Location:** `vbwd-frontend/user/vue/src/views/Checkout.vue`

| Feature | Status | Notes |
|---------|--------|-------|
| Plan selection display | ✅ DONE | Shows plan name, price, billing period |
| Order summary | ✅ DONE | Displays selected items and total |
| Token bundles selection | ✅ DONE | Can add/remove bundles |
| Add-ons selection | ✅ DONE | Can add/remove add-ons |
| Confirm button | ✅ DONE | Submits checkout request |
| Loading states | ✅ DONE | Loading spinner, submitting state |
| Error handling | ✅ DONE | Displays API errors |
| Success state | ✅ DONE | Shows invoice details |
| **Email input block** | ❌ NOT DONE | Missing |
| **Sign Up / Login buttons** | ❌ NOT DONE | Missing |
| **Billing Address block** | ❌ NOT DONE | Missing |
| **Payment methods selection** | ❌ NOT DONE | Missing |
| **Agree with conditions checkbox** | ❌ NOT DONE | Missing |
| **Terms popup** | ❌ NOT DONE | Missing |
| **Pay button** | ❌ NOT DONE | Uses "Confirm Purchase" instead |

### 1.2 Frontend - Plans.vue

**Location:** `vbwd-frontend/user/vue/src/views/Plans.vue`

| Feature | Status | Notes |
|---------|--------|-------|
| Display tariff plans | ✅ DONE | Grid layout with cards |
| Multi-currency support | ✅ DONE | EUR, USD, GBP selector |
| Plan features list | ✅ DONE | Shows features array |
| Select plan button | ✅ DONE | Navigates to /checkout/:slug |
| "Most Popular" badge | ✅ DONE | Conditional display |
| "Current Plan" badge | ✅ DONE | Checks active subscription |
| Tax rate display | ✅ DONE | Shows percentage |

### 1.3 Backend - Checkout Handler

**Location:** `vbwd-backend/src/handlers/checkout_handler.py`

| Feature | Status | Notes |
|---------|--------|-------|
| Validate plan exists | ✅ DONE | Returns error if not found |
| Validate plan is active | ✅ DONE | Returns error if inactive |
| Create PENDING subscription | ✅ DONE | SubscriptionStatus.PENDING |
| Create PENDING token purchases | ✅ DONE | PurchaseStatus.PENDING |
| Create PENDING add-on subscriptions | ✅ DONE | SubscriptionStatus.PENDING |
| Create invoice with line items | ✅ DONE | InvoiceLineItem for each |
| Calculate total amount | ✅ DONE | Sum of all items |
| Return checkout result | ✅ DONE | subscription, invoice, items |

### 1.4 Backend - Payment Handler

**Location:** `vbwd-backend/src/handlers/payment_handler.py`

| Feature | Status | Notes |
|---------|--------|-------|
| Process PaymentCapturedEvent | ✅ DONE | Handles webhook |
| Mark invoice as paid | ✅ DONE | status='paid', paid_at set |
| Activate subscription | ✅ DONE | PENDING → ACTIVE |
| Set subscription expiration | ✅ DONE | Based on billing period |
| Credit tokens to balance | ✅ DONE | UserTokenBalance updated |
| Record token transaction | ✅ DONE | TokenTransaction created |
| Activate add-on subscriptions | ✅ DONE | PENDING → ACTIVE |

### 1.5 Backend - Auth Routes

**Location:** `vbwd-backend/src/routes/auth.py`

| Feature | Status | Notes |
|---------|--------|-------|
| POST /register | ✅ DONE | Create new user |
| POST /login | ✅ DONE | Authenticate user |
| POST /forgot-password | ✅ DONE | Event-driven reset |
| POST /reset-password | ✅ DONE | Execute reset |
| **GET /check-email** | ❌ NOT DONE | Missing endpoint |

---

## 2. REQUIRED FUNCTIONALITY (NOT IMPLEMENTED)

### 2.1 Email Verification on Checkout

**Requirement:** When user enters email, check if registered via backend API.

**What's needed:**

```
Backend:
- GET /api/v1/auth/check-email?email=user@example.com
- Returns: { exists: boolean }

Frontend (Checkout.vue):
- Email input field
- Debounced API call on input
- State management for email check result
```

**Current status:** ❌ NOT IMPLEMENTED

### 2.2 New User Flow

**Requirement:** If email NOT registered, show "create password" field.

**What's needed:**

```
Frontend:
- Password input (appears after email check returns exists=false)
- Password confirmation field
- Inline registration on checkout submit
```

**Current status:** ❌ NOT IMPLEMENTED

### 2.3 Existing User Flow

**Requirement:** If email IS registered, show login hint with red styling.

**What's needed:**

```
Frontend:
- Red flyout/hint: "User registered, enter password to login"
- Password field for login
- Login button
- On success: block turns green, fields auto-fill
```

**Current status:** ❌ NOT IMPLEMENTED

### 2.4 Billing Address Block

**Requirement:** Collect billing address information.

**What's needed:**

```
Backend:
- Model: user_details or billing_address
- Fields: street, city, zip, country, etc.
- API: POST /api/v1/user/billing-address

Frontend:
- Address form fields
- Country selector
- Validation
```

**Current status:** ❌ NOT IMPLEMENTED
- Note: `user_details` model exists but may not have full billing address fields

### 2.5 Payment Methods Block

**Requirement:** Show payment methods from backend API.

**What's needed:**

```
Backend:
- GET /api/v1/settings/payment-methods
- Returns available payment methods

Frontend:
- Payment method selector (radio/cards)
- Selected method stored in checkout state
- Required for Pay button activation
```

**Current status:** ❌ NOT IMPLEMENTED
- Backend has `payment_method` field on Invoice model
- No API endpoint to list available methods

### 2.6 Agree with Conditions

**Requirement:** Checkbox for terms acceptance with popup.

**What's needed:**

```
Backend:
- GET /api/v1/settings/terms-and-conditions
- Returns: { url: string, content: string }

Frontend:
- Checkbox: "I agree with terms and conditions"
- Link opens popup with content from URL
- Checkbox required for Pay button
```

**Current status:** ❌ NOT IMPLEMENTED

### 2.7 Pay Button Logic

**Requirement:** Button becomes active only when requirements met.

**What's needed:**

```
Frontend computed property:
- canPay = paymentMethodSelected && conditionsAccepted && (isLoggedIn || newUserFieldsValid)
```

**Current status:** ❌ NOT IMPLEMENTED
- Current "Confirm Purchase" button only checks `!store.submitting`

### 2.8 Invoice Payment Method Handler

**Requirement:** When "Invoice" payment method selected, create invoice via event handler.

**What's needed:**

```
Backend:
- InvoicePaymentEventHandler (or modify CheckoutHandler)
- Creates invoice that must be manually marked paid by admin
- Event: InvoicePaymentRequestedEvent
```

**Current status:** ⚠️ PARTIALLY DONE
- Current flow already creates invoice on checkout
- Invoice must be manually marked paid via webhook
- No specific "Invoice" payment method handler

---

## 3. ARCHITECTURAL DEVIATIONS

### 3.1 Plugin Architecture (Frontend)

**Designed (architecture_core_view_user):**
```
src/plugins/
├── wizard/           # Multi-step wizard plugin
├── user-cabinet/     # User dashboard plugin
└── admin-dashboard/  # Admin plugin
```

**Actual implementation:**
```
src/
├── views/            # Flat view components
├── stores/           # Pinia stores
└── components/       # Shared components
```

**Deviation:** Frontend uses flat structure, not plugin architecture.

### 3.2 Wizard Flow

**Designed:**
```
Step 1: Upload & Description
Step 2: User Info & GDPR (email, consent)
Step 3: Tariff Plan Selection
Step 4: Checkout & Payment
Step 5: Account Creation
```

**Actual:**
```
/plans → Select plan → /checkout → Confirm → Invoice created
(Requires authentication before checkout)
```

**Deviation:** No wizard flow. Simple linear navigation with pre-auth.

### 3.3 Guest Checkout

**Designed:** Allow checkout with email only, create account after.

**Actual:** `/checkout` requires authentication (`meta: { requiresAuth: true }`).

**Deviation:** No guest checkout support.

---

## 4. EVENT-DRIVEN ARCHITECTURE STATUS

### 4.1 Implemented Events

| Event | Handler | Status |
|-------|---------|--------|
| CheckoutRequestedEvent | CheckoutHandler | ✅ DONE |
| PaymentCapturedEvent | PaymentCapturedHandler | ✅ DONE |
| PasswordResetRequestEvent | PasswordResetRequestHandler | ✅ DONE |
| PasswordResetExecuteEvent | PasswordResetExecuteHandler | ✅ DONE |

### 4.2 Missing Events

| Event | Purpose | Status |
|-------|---------|--------|
| EmailCheckRequestedEvent | Check if email registered | ❌ NOT DONE |
| InvoicePaymentRequestedEvent | Handle invoice payment method | ❌ NOT DONE |
| GuestRegistrationEvent | Register user during checkout | ❌ NOT DONE |

---

## 5. PAYMENT PROVIDER PLUGIN SYSTEM

**Location:** `vbwd-backend/src/plugins/payment_provider.py`

### 5.1 Plugin Interface

```python
class PaymentProviderPlugin(BasePlugin):
    def create_checkout_session(...)
    def verify_webhook(...)
    def capture_payment(...)
```

### 5.2 Implemented Providers

| Provider | Status | Notes |
|----------|--------|-------|
| MockPaymentPlugin | ✅ DONE | For testing |
| Stripe | ❌ PLANNED | Not implemented |
| PayPal | ❌ PLANNED | Not implemented |
| Invoice (manual) | ⚠️ IMPLICIT | Uses webhook to mark paid |

### 5.3 Invoice Payment Method

The current system implicitly supports "Invoice" payment:
1. Checkout creates invoice with status=PENDING
2. Admin manually calls webhook to mark as paid
3. PaymentCapturedHandler activates items

**No specific "Invoice" payment method handler needed** - the current flow handles it.

---

## 6. DATABASE MODELS STATUS

| Model | Status | Notes |
|-------|--------|-------|
| User | ✅ DONE | email, password_hash, status |
| UserDetails | ✅ DONE | May need billing address fields |
| TarifPlan | ✅ DONE | name, slug, features, price |
| TarifPlanPrice | ✅ DONE | Multi-currency support |
| Subscription | ✅ DONE | status, starts_at, expires_at |
| UserInvoice | ✅ DONE | status, payment_method field exists |
| InvoiceLineItem | ✅ DONE | item_type, item_id, price |
| TokenBundle | ✅ DONE | name, token_amount, price |
| TokenBundlePurchase | ✅ DONE | status, tokens_credited |
| AddOn | ✅ DONE | name, description, price |
| AddOnSubscription | ✅ DONE | status, activated_at |
| UserTokenBalance | ✅ DONE | user_id, balance |
| TokenTransaction | ✅ DONE | type, amount, reference |

---

## 7. SUMMARY

### What IS Implemented ✅

1. **Plans page** with plan selection and currency support
2. **Checkout page** with token bundles and add-ons
3. **Backend checkout handler** creating pending items
4. **Backend payment handler** activating on payment
5. **Invoice system** with line items
6. **Token system** with balance and transactions
7. **E2E tests** (33+ tests for current functionality)
8. **Event-driven architecture** for checkout/payment

### What is NOT Implemented ❌

1. **Email verification endpoint** (`GET /check-email`)
2. **Email input block** on checkout page
3. **New user registration flow** on checkout
4. **Existing user login flow** on checkout
5. **Billing Address collection**
6. **Payment methods API** and selection UI
7. **Terms and conditions checkbox** with popup
8. **Pay button conditional activation**
9. **Guest checkout** (currently requires auth)

### Architectural Deviations ⚠️

1. **No plugin architecture** in frontend
2. **No wizard flow** (simple linear navigation)
3. **Pre-authentication required** (no guest checkout)
4. **Flat component structure** instead of modular plugins

---

## 8. RECOMMENDED IMPLEMENTATION ORDER

If implementing the missing features, prioritize:

1. **Email check endpoint** (backend) - Foundation for checkout flow
2. **Email verification UI** (frontend) - Entry point for checkout
3. **Login/Register on checkout** (both) - Complete auth flow
4. **Payment methods API** (backend) - List available methods
5. **Payment method selector** (frontend) - User selection
6. **Terms checkbox** (frontend) - Compliance requirement
7. **Pay button logic** (frontend) - Final validation
8. **Billing Address** (both) - Can be added later

Each step should follow TDD: write E2E tests first, then implement.
