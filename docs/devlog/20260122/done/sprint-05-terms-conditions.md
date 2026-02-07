# Sprint 05: Terms and Conditions Checkbox

**Priority:** MEDIUM
**Estimated Effort:** Small
**Dependencies:** Sprint 04

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Terms Source** | Static file - load from `/static/terms.md` |
| **Track Acceptance** | No - just require checkbox, don't store acceptance record |

### Static Terms File

Terms content loaded from static markdown file:
- **Path:** `vbwd-backend/static/terms.md`
- **Format:** Markdown (rendered in popup)
- **Update:** Deploy new file to change terms

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
Create backend API for terms content and frontend checkbox component with popup. Required for checkout submission.

---

## TDD Phase 1: Write Failing Backend Tests FIRST

### 1.1 Integration Test: GET /api/v1/settings/terms

**File:** `vbwd-backend/tests/integration/routes/test_settings_routes.py`

```python
# Add to existing test file

class TestTermsEndpoint:
    """Integration tests for terms and conditions endpoint."""

    def test_returns_terms_content(self, client):
        """Should return terms content."""
        response = client.get("/api/v1/settings/terms")

        assert response.status_code == 200
        data = response.get_json()
        assert 'content' in data
        assert len(data['content']) > 0

    def test_returns_terms_title(self, client):
        """Should return terms title."""
        response = client.get("/api/v1/settings/terms")
        data = response.get_json()

        assert 'title' in data
        assert data['title'] == 'Terms and Conditions'

    def test_does_not_require_auth(self, client):
        """Endpoint should be public."""
        response = client.get("/api/v1/settings/terms")
        assert response.status_code == 200
```

---

## TDD Phase 2: Write Minimal Backend Code

### 2.1 Add to Settings Service

**File:** `vbwd-backend/src/services/settings_service.py`

```python
# Add to SettingsService class

# Terms content - in production, could come from CMS or database
TERMS_CONTENT = """
## Terms and Conditions

### 1. Acceptance of Terms
By accessing and using this service, you accept and agree to be bound by these Terms and Conditions.

### 2. Subscription Services
- Subscriptions are billed according to the selected billing period
- You may cancel your subscription at any time
- Refunds are handled according to our refund policy

### 3. Payment
- Payment is due upon checkout completion
- We accept the payment methods listed during checkout
- All prices include applicable taxes unless stated otherwise

### 4. Privacy
Your use of our services is also governed by our Privacy Policy.

### 5. Limitation of Liability
Our liability is limited to the amount paid for the service.

### 6. Changes to Terms
We reserve the right to modify these terms at any time.

Last updated: 2026-01-01
"""

def get_terms(self) -> dict:
    """
    Get terms and conditions content.

    Returns:
        Dict with title and content
    """
    return {
        'title': 'Terms and Conditions',
        'content': self.TERMS_CONTENT.strip(),
    }
```

### 2.2 Add Route

**File:** `vbwd-backend/src/routes/settings.py`

```python
# Add to existing settings routes

@settings_bp.route("/terms", methods=["GET"])
def get_terms():
    """
    Get terms and conditions.

    Returns:
        200: { "title": "...", "content": "..." }
    """
    service = SettingsService()
    terms = service.get_terms()

    return jsonify(terms), 200
```

---

## TDD Phase 3: Write Failing Frontend Tests

### 3.1 E2E Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-conditions.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../fixtures/checkout.fixtures';

test.describe('Terms and Conditions Checkbox', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('displays terms checkbox', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await expect(page.locator('[data-testid="terms-checkbox"]')).toBeVisible();
  });

  test('checkbox is unchecked by default', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await expect(page.locator('[data-testid="terms-checkbox"] input')).not.toBeChecked();
  });

  test('clicking link opens terms popup', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await page.click('[data-testid="terms-link"]');

    await expect(page.locator('[data-testid="terms-popup"]')).toBeVisible();
    await expect(page.locator('[data-testid="terms-content"]')).toContainText('Terms and Conditions');
  });

  test('popup can be closed', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await page.click('[data-testid="terms-link"]');
    await expect(page.locator('[data-testid="terms-popup"]')).toBeVisible();

    await page.click('[data-testid="terms-popup-close"]');
    await expect(page.locator('[data-testid="terms-popup"]')).not.toBeVisible();
  });

  test('can check the checkbox', async ({ page }) => {
    await page.goto('/checkout/pro');
    await page.waitForSelector('[data-testid="checkout-loading"]', { state: 'hidden' });

    await page.click('[data-testid="terms-checkbox"]');

    await expect(page.locator('[data-testid="terms-checkbox"] input')).toBeChecked();
  });
});
```

### 3.2 Unit Test

**File:** `vbwd-frontend/user/vue/tests/unit/components/TermsCheckbox.spec.ts`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import TermsCheckbox from '@/components/checkout/TermsCheckbox.vue';

vi.mock('@/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      title: 'Terms',
      content: 'Test content'
    })
  }
}));

describe('TermsCheckbox', () => {
  it('renders checkbox unchecked by default', () => {
    const wrapper = mount(TermsCheckbox);
    const checkbox = wrapper.find('input[type="checkbox"]');

    expect(checkbox.element.checked).toBe(false);
  });

  it('emits change event when checked', async () => {
    const wrapper = mount(TermsCheckbox);
    await wrapper.find('input[type="checkbox"]').setValue(true);

    expect(wrapper.emitted('change')).toBeTruthy();
    expect(wrapper.emitted('change')[0]).toEqual([true]);
  });

  it('shows popup when link clicked', async () => {
    const wrapper = mount(TermsCheckbox);
    await wrapper.find('[data-testid="terms-link"]').trigger('click');

    expect(wrapper.find('[data-testid="terms-popup"]').exists()).toBe(true);
  });
});
```

---

## TDD Phase 4: Write Minimal Frontend Code

### 4.1 Create Component

**File:** `vbwd-frontend/user/vue/src/components/checkout/TermsCheckbox.vue`

```vue
<template>
  <div class="terms-checkbox" data-testid="terms-checkbox">
    <label class="checkbox-label">
      <input
        type="checkbox"
        v-model="accepted"
        @change="$emit('change', accepted)"
      />
      <span>
        I agree to the
        <a
          href="#"
          data-testid="terms-link"
          @click.prevent="showPopup = true"
        >
          Terms and Conditions
        </a>
      </span>
    </label>

    <!-- Popup Modal -->
    <div v-if="showPopup" class="popup-overlay" data-testid="terms-popup">
      <div class="popup-content">
        <div class="popup-header">
          <h3>{{ terms?.title || 'Terms and Conditions' }}</h3>
          <button
            data-testid="terms-popup-close"
            class="close-btn"
            @click="showPopup = false"
          >
            &times;
          </button>
        </div>
        <div
          data-testid="terms-content"
          class="popup-body"
          v-html="renderedContent"
        />
        <div class="popup-footer">
          <button class="btn primary" @click="showPopup = false">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import api from '@/api';

defineEmits<{
  (e: 'change', value: boolean): void;
}>();

const accepted = ref(false);
const showPopup = ref(false);
const terms = ref<{ title: string; content: string } | null>(null);

// Simple markdown-like rendering (headers, paragraphs)
const renderedContent = computed(() => {
  if (!terms.value) return 'Loading...';

  return terms.value.content
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>');
});

const loadTerms = async () => {
  try {
    terms.value = await api.get('/settings/terms');
  } catch {
    terms.value = {
      title: 'Terms and Conditions',
      content: 'Failed to load terms. Please try again later.',
    };
  }
};

onMounted(() => {
  loadTerms();
});
</script>

<style scoped>
.terms-checkbox {
  margin: 15px 0;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
}

.checkbox-label input {
  margin-top: 3px;
}

.checkbox-label a {
  color: #3498db;
  text-decoration: underline;
}

/* Popup styles */
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.popup-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  width: 90%;
  display: flex;
  flex-direction: column;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.popup-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.popup-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.popup-body :deep(h3) {
  margin-top: 20px;
}

.popup-body :deep(h4) {
  margin-top: 15px;
}

.popup-body :deep(li) {
  margin-left: 20px;
}

.popup-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  text-align: right;
}

.btn.primary {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Component handles checkbox + popup, nothing else |
| **O** - Open/Closed | Content loaded from API, component doesn't change |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | Single 'change' event emitted |
| **D** - Dependency Inversion | Uses api module abstraction |

## No Over-engineering

- No separate modal component (inline is sufficient)
- Simple markdown-like rendering (no library)
- Terms loaded once on mount
- No state management (local ref)

---

## Verification Checklist

- [ ] Backend tests written and FAILING
- [ ] Backend implementation done
- [ ] Frontend E2E tests written and FAILING
- [ ] Frontend unit tests written and FAILING
- [ ] Frontend component implemented
- [ ] All tests PASSING

## Run Tests

> **All tests run in Docker containers.**

### Backend (from `vbwd-backend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --integration    # Integration tests

# Makefile commands
make test-integration -- -k "TestTermsEndpoint"
```

### Frontend (from `vbwd-frontend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --user --unit    # Unit tests
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# From vbwd-frontend/user/vue/
npm run test -- --grep "TermsCheckbox"
npm run test:e2e -- checkout-conditions.spec.ts

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!
```
