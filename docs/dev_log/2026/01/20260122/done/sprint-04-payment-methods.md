# Sprint 04: Payment Methods API and UI

**Priority:** MEDIUM
**Estimated Effort:** Medium
**Dependencies:** Sprint 03, Sprint 08

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Payment Methods Source** | Use Sprint 08 PaymentMethod database model (already implemented) |
| **Show Fees** | No - hide fees from UI, include silently in total |

### Integration with Sprint 08

This sprint uses the PaymentMethod model and `/api/v1/settings/payment-methods` endpoint from Sprint 08.

**Key Points:**
- Frontend fetches available methods via public endpoint
- Uses `to_public_dict()` which excludes sensitive config
- Filters by currency/country if provided
- Does NOT display fee information in UI

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
Create backend API to list available payment methods and frontend component for selection. The "Invoice" method is the core payment option.

---

## TDD Phase 1: Write Failing Backend Tests FIRST

### 1.1 Unit Test: Settings Service

**File:** `vbwd-backend/tests/unit/services/test_settings_service.py`

```python
import pytest
from src.services.settings_service import SettingsService

class TestGetPaymentMethods:
    """Tests for payment methods retrieval."""

    def test_returns_list_of_payment_methods(self, settings_service):
        """Should return available payment methods."""
        methods = settings_service.get_payment_methods()

        assert isinstance(methods, list)
        assert len(methods) > 0

    def test_invoice_method_always_available(self, settings_service):
        """Invoice payment method should always be available."""
        methods = settings_service.get_payment_methods()

        invoice_method = next((m for m in methods if m['id'] == 'invoice'), None)
        assert invoice_method is not None
        assert invoice_method['name'] == 'Invoice'
        assert invoice_method['enabled'] is True

    def test_returns_method_with_required_fields(self, settings_service):
        """Each method should have required fields."""
        methods = settings_service.get_payment_methods()

        for method in methods:
            assert 'id' in method
            assert 'name' in method
            assert 'description' in method
            assert 'enabled' in method

    def test_only_returns_enabled_methods(self, settings_service):
        """Should only return methods where enabled=True."""
        methods = settings_service.get_payment_methods()

        for method in methods:
            assert method['enabled'] is True
```

### 1.2 Integration Test: GET /api/v1/settings/payment-methods

**File:** `vbwd-backend/tests/integration/routes/test_settings_routes.py`

```python
import pytest

class TestPaymentMethodsEndpoint:
    """Integration tests for payment methods endpoint."""

    def test_returns_payment_methods(self, client):
        """Should return list of payment methods."""
        response = client.get("/api/v1/settings/payment-methods")

        assert response.status_code == 200
        data = response.get_json()
        assert 'methods' in data
        assert isinstance(data['methods'], list)

    def test_includes_invoice_method(self, client):
        """Should include Invoice payment method."""
        response = client.get("/api/v1/settings/payment-methods")
        data = response.get_json()

        methods = data['methods']
        invoice = next((m for m in methods if m['id'] == 'invoice'), None)

        assert invoice is not None
        assert invoice['name'] == 'Invoice'

    def test_does_not_require_auth(self, client):
        """Endpoint should be public (for checkout page)."""
        # No auth header
        response = client.get("/api/v1/settings/payment-methods")

        assert response.status_code == 200

    def test_method_has_description(self, client):
        """Each method should have a description."""
        response = client.get("/api/v1/settings/payment-methods")
        data = response.get_json()

        for method in data['methods']:
            assert 'description' in method
            assert len(method['description']) > 0
```

---

## TDD Phase 2: Write Minimal Backend Code

### 2.1 Create Settings Service

**File:** `vbwd-backend/src/services/settings_service.py`

```python
"""Settings service for application configuration."""
from typing import List, Dict, Any


class SettingsService:
    """Service for application settings and configuration."""

    # Payment methods configuration
    # In production, this could come from database or config file
    PAYMENT_METHODS = [
        {
            'id': 'invoice',
            'name': 'Invoice',
            'description': 'Pay by invoice. You will receive an invoice via email.',
            'enabled': True,
            'icon': 'invoice',
        },
        # Future methods can be added here:
        # {
        #     'id': 'stripe',
        #     'name': 'Credit Card',
        #     'description': 'Pay with credit or debit card via Stripe.',
        #     'enabled': False,  # Disabled until implemented
        #     'icon': 'credit-card',
        # },
    ]

    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Get list of enabled payment methods.

        Returns:
            List of payment method dictionaries
        """
        return [m for m in self.PAYMENT_METHODS if m['enabled']]

    def get_payment_method(self, method_id: str) -> Dict[str, Any] | None:
        """
        Get a specific payment method by ID.

        Args:
            method_id: The payment method identifier

        Returns:
            Payment method dict or None if not found
        """
        for method in self.PAYMENT_METHODS:
            if method['id'] == method_id and method['enabled']:
                return method
        return None
```

### 2.2 Create Settings Route

**File:** `vbwd-backend/src/routes/settings.py`

```python
"""Settings routes for public configuration."""
from flask import Blueprint, jsonify
from src.services.settings_service import SettingsService

settings_bp = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings_bp.route("/payment-methods", methods=["GET"])
def get_payment_methods():
    """
    Get available payment methods.

    Returns:
        200: { "methods": [...] }
    """
    service = SettingsService()
    methods = service.get_payment_methods()

    return jsonify({"methods": methods}), 200
```

### 2.3 Register Blueprint

**File:** `vbwd-backend/src/routes/__init__.py`

```python
# Add to existing imports and registration
from src.routes.settings import settings_bp

def register_routes(app):
    # ... existing registrations ...
    app.register_blueprint(settings_bp)
```

---

## TDD Phase 3: Write Failing Frontend Tests

### 3.1 E2E Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-payment.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../fixtures/checkout.fixtures';

test.describe('Payment Methods Selection', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('displays payment methods block', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await expect(page.locator('[data-testid="payment-methods-block"]')).toBeVisible();
  });

  test('loads payment methods from API', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    // Should show at least Invoice method
    await expect(page.locator('[data-testid="payment-method-invoice"]')).toBeVisible();
  });

  test('can select a payment method', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    // Click on invoice method
    await page.click('[data-testid="payment-method-invoice"]');

    // Should be selected (visual indicator)
    await expect(page.locator('[data-testid="payment-method-invoice"]')).toHaveClass(/selected/);
  });

  test('shows method description', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    // Should show description
    await expect(page.locator('[data-testid="payment-method-invoice-description"]')).toBeVisible();
  });

  test('requires payment method selection for checkout', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    // Without selection, pay button should indicate need for selection
    // (actual behavior depends on implementation - could be disabled or show message)
    const confirmButton = page.locator('[data-testid="confirm-checkout"]');

    // If no method selected initially, there should be indication
    // This test documents expected behavior
  });
});
```

### 3.2 Unit Test: Payment Methods Store/Composable

**File:** `vbwd-frontend/user/vue/tests/unit/composables/usePaymentMethods.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePaymentMethods } from '@/composables/usePaymentMethods';
import * as api from '@/api';

vi.mock('@/api');

describe('usePaymentMethods', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads payment methods from API', async () => {
    vi.mocked(api.default.get).mockResolvedValue({
      methods: [
        { id: 'invoice', name: 'Invoice', description: 'Pay by invoice', enabled: true }
      ]
    });

    const { loadMethods, methods } = usePaymentMethods();
    await loadMethods();

    expect(methods.value).toHaveLength(1);
    expect(methods.value[0].id).toBe('invoice');
  });

  it('tracks selected method', async () => {
    vi.mocked(api.default.get).mockResolvedValue({
      methods: [{ id: 'invoice', name: 'Invoice', description: 'Test', enabled: true }]
    });

    const { loadMethods, selectMethod, selectedMethod } = usePaymentMethods();
    await loadMethods();
    selectMethod('invoice');

    expect(selectedMethod.value?.id).toBe('invoice');
  });

  it('hasSelection returns true when method selected', async () => {
    vi.mocked(api.default.get).mockResolvedValue({
      methods: [{ id: 'invoice', name: 'Invoice', description: 'Test', enabled: true }]
    });

    const { loadMethods, selectMethod, hasSelection } = usePaymentMethods();
    await loadMethods();

    expect(hasSelection.value).toBe(false);
    selectMethod('invoice');
    expect(hasSelection.value).toBe(true);
  });
});
```

---

## TDD Phase 4: Write Minimal Frontend Code

### 4.1 Create Composable

**File:** `vbwd-frontend/user/vue/src/composables/usePaymentMethods.ts`

```typescript
import { ref, computed } from 'vue';
import api from '@/api';

interface PaymentMethod {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  icon?: string;
}

export function usePaymentMethods() {
  const methods = ref<PaymentMethod[]>([]);
  const selectedMethodId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const loadMethods = async () => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get('/settings/payment-methods');
      methods.value = response.methods;
    } catch {
      error.value = 'Failed to load payment methods';
    } finally {
      loading.value = false;
    }
  };

  const selectMethod = (methodId: string) => {
    const method = methods.value.find(m => m.id === methodId);
    if (method) {
      selectedMethodId.value = methodId;
    }
  };

  const selectedMethod = computed(() =>
    methods.value.find(m => m.id === selectedMethodId.value) || null
  );

  const hasSelection = computed(() => selectedMethodId.value !== null);

  return {
    methods,
    loading,
    error,
    selectedMethodId,
    selectedMethod,
    hasSelection,
    loadMethods,
    selectMethod,
  };
}
```

### 4.2 Create Component

**File:** `vbwd-frontend/user/vue/src/components/checkout/PaymentMethods.vue`

```vue
<template>
  <div class="payment-methods-block card" data-testid="payment-methods-block">
    <h3>Payment Method</h3>

    <div v-if="loading" class="loading">Loading payment methods...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="methods-list">
      <div
        v-for="method in methods"
        :key="method.id"
        :class="['method-option', { selected: selectedMethodId === method.id }]"
        :data-testid="`payment-method-${method.id}`"
        @click="selectMethod(method.id)"
      >
        <div class="method-header">
          <input
            type="radio"
            :id="`method-${method.id}`"
            :checked="selectedMethodId === method.id"
            :name="'payment-method'"
          />
          <label :for="`method-${method.id}`" class="method-name">
            {{ method.name }}
          </label>
        </div>
        <p
          :data-testid="`payment-method-${method.id}-description`"
          class="method-description"
        >
          {{ method.description }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { usePaymentMethods } from '@/composables/usePaymentMethods';

const emit = defineEmits<{
  (e: 'selected', methodId: string): void;
}>();

const {
  methods,
  loading,
  error,
  selectedMethodId,
  loadMethods,
  selectMethod: select,
} = usePaymentMethods();

const selectMethod = (methodId: string) => {
  select(methodId);
  emit('selected', methodId);
};

onMounted(() => {
  loadMethods();
});
</script>

<style scoped>
.payment-methods-block {
  padding: 20px;
}

.methods-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.method-option {
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.method-option:hover {
  border-color: #3498db;
}

.method-option.selected {
  border-color: #3498db;
  background: #f0f7ff;
}

.method-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.method-name {
  font-weight: 600;
  cursor: pointer;
}

.method-description {
  margin: 8px 0 0 26px;
  color: #666;
  font-size: 0.9rem;
}

.loading, .error {
  padding: 20px;
  text-align: center;
  color: #666;
}

.error {
  color: #e74c3c;
}
</style>
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Service returns data, route handles HTTP, component handles UI |
| **O** - Open/Closed | New payment methods added to config array, no code changes |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | Component emits single 'selected' event |
| **D** - Dependency Inversion | Composable abstracts API calls |

## No Over-engineering

- Config-based payment methods (no database table yet)
- Simple list, not complex card components
- No icons/images initially (can add later)
- No payment processing logic (handled elsewhere)

---

## Verification Checklist

- [ ] Backend unit tests written and FAILING
- [ ] Backend integration tests written and FAILING
- [ ] Backend service implemented
- [ ] Backend route implemented
- [ ] Frontend unit tests written and FAILING
- [ ] Frontend E2E tests written and FAILING
- [ ] Frontend composable implemented
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
make test-unit -- -k "payment_methods"
make test-integration -- -k "TestPaymentMethods"
```

### Frontend (from `vbwd-frontend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --user --unit    # Unit tests
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# From vbwd-frontend/user/vue/
npm run test -- --grep "usePaymentMethods"
npm run test:e2e -- checkout-payment.spec.ts

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!
```
