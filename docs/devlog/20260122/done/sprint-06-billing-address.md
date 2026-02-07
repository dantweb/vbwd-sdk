# Sprint 06: Billing Address Block

**Priority:** MEDIUM
**Estimated Effort:** Medium
**Dependencies:** Sprint 03, Sprint 09 (Countries Configuration)

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Countries List** | Load from database - admin configures available countries in Sprint 09 |
| **Company Field** | Yes, optional - add company name field (not required) |

### Country Selection

Countries are loaded from the database via `/api/v1/settings/countries` endpoint.
- Admin configures available countries in Settings → Countries (Sprint 09)
- Checkout fetches only enabled countries
- Fallback: If API fails, show hardcoded list (DE, AT, CH, US, GB)

### Billing Address Fields

| Field | Type | Required |
|-------|------|----------|
| `company` | string | No |
| `street` | string | Yes |
| `city` | string | Yes |
| `zip` | string | Yes |
| `country` | string (ISO) | Yes |

---

## Core Requirements

This sprint follows our development standards:

| Requirement | Description |
|-------------|-------------|
| **TDD-first** | Write failing tests BEFORE production code |
| **SOLID** | Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion |
| **DRY** | Don't Repeat Yourself - reuse existing code and patterns |
| **Clean Code** | Readable, maintainable, self-documenting code |
| **No Over-engineering** | Only implement what's needed NOW, no premature abstractions |

---

## Objective
Create billing address form component for checkout. Address is stored with user profile and submitted with checkout.

---

## TDD Phase 1: Write Failing Backend Tests FIRST

### 1.1 Unit Test: User Details with Billing Address

**File:** `vbwd-backend/tests/unit/models/test_user_details.py`

```python
import pytest
from src.models.user_details import UserDetails

class TestUserDetailsBillingAddress:
    """Tests for billing address fields on UserDetails."""

    def test_has_billing_address_fields(self):
        """UserDetails should have billing address fields."""
        details = UserDetails(
            user_id="user-123",
            billing_street="123 Main St",
            billing_city="Berlin",
            billing_zip="10115",
            billing_country="DE",
        )

        assert details.billing_street == "123 Main St"
        assert details.billing_city == "Berlin"
        assert details.billing_zip == "10115"
        assert details.billing_country == "DE"

    def test_billing_address_to_dict(self):
        """Billing address should be included in to_dict."""
        details = UserDetails(
            user_id="user-123",
            billing_street="123 Main St",
            billing_city="Berlin",
            billing_zip="10115",
            billing_country="DE",
        )

        data = details.to_dict()

        assert data['billing_street'] == "123 Main St"
        assert data['billing_city'] == "Berlin"
```

### 1.2 Integration Test: PUT /api/v1/user/billing-address

**File:** `vbwd-backend/tests/integration/routes/test_user_routes.py`

```python
# Add to existing file

class TestBillingAddressEndpoint:
    """Integration tests for billing address endpoint."""

    def test_save_billing_address(self, client, auth_headers, test_user):
        """Should save billing address."""
        response = client.put(
            "/api/v1/user/billing-address",
            headers=auth_headers,
            json={
                "street": "123 Test St",
                "city": "Berlin",
                "zip": "10115",
                "country": "DE",
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['street'] == "123 Test St"

    def test_get_billing_address(self, client, auth_headers, test_user_with_address):
        """Should return saved billing address."""
        response = client.get(
            "/api/v1/user/billing-address",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'street' in data

    def test_requires_auth(self, client):
        """Should require authentication."""
        response = client.put(
            "/api/v1/user/billing-address",
            json={"street": "123 Test St"}
        )

        assert response.status_code == 401

    def test_validates_required_fields(self, client, auth_headers):
        """Should validate required fields."""
        response = client.put(
            "/api/v1/user/billing-address",
            headers=auth_headers,
            json={"street": "123 Test St"}  # Missing city, zip, country
        )

        assert response.status_code == 400
```

---

## TDD Phase 2: Write Minimal Backend Code

### 2.1 Update UserDetails Model (if needed)

**File:** `vbwd-backend/src/models/user_details.py`

```python
# Add billing address fields if not already present

class UserDetails(db.Model):
    __tablename__ = 'user_details'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)

    # Existing fields
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))

    # Billing address fields
    billing_street = db.Column(db.String(255))
    billing_city = db.Column(db.String(100))
    billing_zip = db.Column(db.String(20))
    billing_country = db.Column(db.String(2))  # ISO country code

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'billing_street': self.billing_street,
            'billing_city': self.billing_city,
            'billing_zip': self.billing_zip,
            'billing_country': self.billing_country,
        }
```

### 2.2 Add Route

**File:** `vbwd-backend/src/routes/user.py`

```python
# Add to existing user routes

@user_bp.route("/billing-address", methods=["GET"])
@jwt_required()
def get_billing_address():
    """Get user's billing address."""
    user_id = get_jwt_identity()
    user_repo = UserRepository(db.session)
    details = user_repo.get_user_details(user_id)

    if not details:
        return jsonify({}), 200

    return jsonify({
        'street': details.billing_street,
        'city': details.billing_city,
        'zip': details.billing_zip,
        'country': details.billing_country,
    }), 200


@user_bp.route("/billing-address", methods=["PUT"])
@jwt_required()
def save_billing_address():
    """Save user's billing address."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    # Validate required fields
    required = ['street', 'city', 'zip', 'country']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    user_repo = UserRepository(db.session)

    # Get or create user details
    details = user_repo.get_user_details(user_id)
    if not details:
        details = UserDetails(user_id=user_id)

    # Update billing address
    details.billing_street = data['street']
    details.billing_city = data['city']
    details.billing_zip = data['zip']
    details.billing_country = data['country']

    user_repo.save_user_details(details)

    return jsonify({
        'street': details.billing_street,
        'city': details.billing_city,
        'zip': details.billing_zip,
        'country': details.billing_country,
    }), 200
```

---

## TDD Phase 3: Write Failing Frontend Tests

### 3.1 E2E Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-billing.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../fixtures/checkout.fixtures';

test.describe('Billing Address Block', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('displays billing address block', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await expect(page.locator('[data-testid="billing-address-block"]')).toBeVisible();
  });

  test('shows required address fields', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await expect(page.locator('[data-testid="billing-street"]')).toBeVisible();
    await expect(page.locator('[data-testid="billing-city"]')).toBeVisible();
    await expect(page.locator('[data-testid="billing-zip"]')).toBeVisible();
    await expect(page.locator('[data-testid="billing-country"]')).toBeVisible();
  });

  test('can fill in billing address', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await page.fill('[data-testid="billing-street"]', '123 Test St');
    await page.fill('[data-testid="billing-city"]', 'Berlin');
    await page.fill('[data-testid="billing-zip"]', '10115');
    await page.selectOption('[data-testid="billing-country"]', 'DE');

    await expect(page.locator('[data-testid="billing-street"]')).toHaveValue('123 Test St');
  });

  test('shows validation errors for empty fields', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    // Try to submit with empty fields (trigger validation)
    await page.click('[data-testid="billing-street"]');
    await page.click('[data-testid="billing-city"]');

    // Street should show error
    await expect(page.locator('[data-testid="billing-street-error"]')).toBeVisible();
  });

  test('loads saved address for returning user', async ({ page }) => {
    // Mock saved address
    await page.route('**/api/v1/user/billing-address', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: { street: 'Saved St', city: 'Munich', zip: '80331', country: 'DE' }
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await expect(page.locator('[data-testid="billing-street"]')).toHaveValue('Saved St');
  });
});
```

---

## TDD Phase 4: Write Minimal Frontend Code

### 4.1 Create Component

**File:** `vbwd-frontend/user/vue/src/components/checkout/BillingAddress.vue`

```vue
<template>
  <div class="billing-address-block card" data-testid="billing-address-block">
    <h3>Billing Address</h3>

    <div class="form-group">
      <label for="street">Street Address</label>
      <input
        id="street"
        v-model="address.street"
        type="text"
        placeholder="Street and number"
        data-testid="billing-street"
        :class="{ error: errors.street }"
        @blur="validate('street')"
      />
      <span v-if="errors.street" data-testid="billing-street-error" class="error-text">
        {{ errors.street }}
      </span>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label for="city">City</label>
        <input
          id="city"
          v-model="address.city"
          type="text"
          placeholder="City"
          data-testid="billing-city"
          :class="{ error: errors.city }"
          @blur="validate('city')"
        />
        <span v-if="errors.city" class="error-text">{{ errors.city }}</span>
      </div>

      <div class="form-group">
        <label for="zip">ZIP Code</label>
        <input
          id="zip"
          v-model="address.zip"
          type="text"
          placeholder="ZIP"
          data-testid="billing-zip"
          :class="{ error: errors.zip }"
          @blur="validate('zip')"
        />
        <span v-if="errors.zip" class="error-text">{{ errors.zip }}</span>
      </div>
    </div>

    <div class="form-group">
      <label for="country">Country</label>
      <select
        id="country"
        v-model="address.country"
        data-testid="billing-country"
        :class="{ error: errors.country }"
        @blur="validate('country')"
      >
        <option value="">Select country</option>
        <option value="DE">Germany</option>
        <option value="AT">Austria</option>
        <option value="CH">Switzerland</option>
        <option value="US">United States</option>
        <option value="GB">United Kingdom</option>
        <!-- Add more as needed -->
      </select>
      <span v-if="errors.country" class="error-text">{{ errors.country }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, watch } from 'vue';
import api from '@/api';

const emit = defineEmits<{
  (e: 'change', address: BillingAddressData): void;
  (e: 'valid', isValid: boolean): void;
}>();

interface BillingAddressData {
  street: string;
  city: string;
  zip: string;
  country: string;
}

const address = reactive<BillingAddressData>({
  street: '',
  city: '',
  zip: '',
  country: '',
});

const errors = reactive<Record<string, string>>({});

const validate = (field?: string) => {
  const fieldsToValidate = field ? [field] : ['street', 'city', 'zip', 'country'];

  for (const f of fieldsToValidate) {
    if (!address[f as keyof BillingAddressData]) {
      errors[f] = 'This field is required';
    } else {
      delete errors[f];
    }
  }

  const isValid = Object.keys(errors).length === 0 &&
    address.street && address.city && address.zip && address.country;

  emit('valid', isValid);
  return isValid;
};

const loadSavedAddress = async () => {
  try {
    const saved = await api.get('/user/billing-address');
    if (saved.street) {
      address.street = saved.street;
      address.city = saved.city;
      address.zip = saved.zip;
      address.country = saved.country;
    }
  } catch {
    // No saved address, that's fine
  }
};

// Emit changes
watch(address, () => {
  emit('change', { ...address });
  validate();
}, { deep: true });

onMounted(() => {
  loadSavedAddress();
});
</script>

<style scoped>
.billing-address-block {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

input, select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

input.error, select.error {
  border-color: #e74c3c;
}

.error-text {
  color: #e74c3c;
  font-size: 0.85rem;
  margin-top: 4px;
  display: block;
}
</style>
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Component handles address form only |
| **O** - Open/Closed | Countries can be added without code change |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | Emits 'change' and 'valid' events |
| **D** - Dependency Inversion | Uses api module |

## No Over-engineering

- No separate form library
- Simple field-level validation
- Countries hardcoded (not API call)
- No address autocomplete (can add later)

---

## Verification Checklist

- [ ] Backend unit tests written and FAILING
- [ ] Backend integration tests written and FAILING
- [ ] Model updated with billing fields
- [ ] Route implemented
- [ ] Migration created (if needed)
- [ ] Frontend E2E tests written and FAILING
- [ ] Frontend component implemented
- [ ] All tests PASSING

## Run Tests

> **All tests run in Docker containers.**

### Backend (from `vbwd-backend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --unit           # Unit tests
./bin/pre-commit-check.sh --integration    # Integration tests

# Makefile commands
make test-unit -- -k "billing"
make test-integration -- -k "TestBillingAddress"
```

### Frontend (from `vbwd-frontend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# From vbwd-frontend/user/vue/
npm run test:e2e -- checkout-billing.spec.ts

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!
```

## Database Migration (if fields don't exist)

```bash
# Create migration
docker-compose exec api flask db migrate -m "add billing address fields"

# Run migration
docker-compose exec api flask db upgrade
```
