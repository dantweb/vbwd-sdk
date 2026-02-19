# Sprint 02: Email Block Component (Frontend)

**Priority:** HIGH
**Estimated Effort:** Medium
**Dependencies:** Sprint 01 (Email Check API)

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Component Location** | `vbwd-frontend/user/vue/` only |
| **Debounce Delay** | 500ms |
| **Forgot Password** | Yes, link opens modal/redirects to forgot password flow |
| **Registration Fields** | Password + confirmation + strength indicator (weak/medium/strong) |
| **Auth State** | localStorage + global auth store (Pinia) |
| **Success UI** | Disabled email input + Logout button |
| **CAPTCHA** | Invisible Google reCAPTCHA on every email check request |
| **Analytics Events** | Basic + Detailed events with timing |

### Password Strength Indicator

```
weak:   < 8 chars OR only letters/numbers
medium: >= 8 chars + (letters AND numbers)
strong: >= 12 chars + letters + numbers + special chars
```

### Analytics Events

| Event | Data |
|-------|------|
| `email-input-started` | timestamp, plan_slug |
| `email-input-completed` | timestamp, email_domain, duration_ms |
| `email-checked` | email_exists, response_time_ms |
| `login-started` | timestamp |
| `login-success` | timestamp, duration_ms |
| `login-failed` | error_type, timestamp |
| `registration-started` | timestamp |
| `registration-success` | timestamp, duration_ms |
| `registration-failed` | error_type, timestamp |
| `forgot-password-clicked` | timestamp |
| `logout-clicked` | timestamp |

### Invisible reCAPTCHA Integration

```typescript
// Execute reCAPTCHA before email check API call
const token = await grecaptcha.execute(SITE_KEY, { action: 'email_check' });

// Send token with API request
api.get(`/auth/check-email?email=${email}&captcha_token=${token}`);
```

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
Create the email input block for checkout page that checks if user is registered and shows appropriate UI (login vs register).

---

## TDD Phase 1: Write Failing E2E Tests FIRST

### 1.1 E2E Tests

**File:** `vbwd-frontend/user/vue/tests/e2e/checkout/checkout-email.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Checkout Email Block', () => {
  // Note: These tests run WITHOUT pre-authentication
  // The checkout page needs to allow guest access for this to work

  test.beforeEach(async ({ page }) => {
    // Clear any existing auth
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
  });

  test('displays email input block', async ({ page }) => {
    await page.goto('/checkout/pro');

    await expect(page.locator('[data-testid="email-block"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
  });

  test('shows loading state while checking email', async ({ page }) => {
    // Slow down the API response
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({ json: { exists: false } });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'test@example.com');

    // Should show checking state
    await expect(page.locator('[data-testid="email-checking"]')).toBeVisible();
  });

  test('shows register form for new email', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: false } });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'newuser@example.com');

    // Wait for check to complete
    await page.waitForSelector('[data-testid="email-new-user"]');

    // Should show password field for registration
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="signup-button"]')).toBeVisible();
  });

  test('shows login hint for existing email', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: true } });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'existing@example.com');

    // Wait for check to complete
    await page.waitForSelector('[data-testid="email-existing-user"]');

    // Should show login hint with red styling
    await expect(page.locator('[data-testid="login-hint"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-hint"]')).toHaveClass(/text-red|error/);
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();
  });

  test('successful login turns block green', async ({ page }) => {
    // Mock check-email
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: true } });
    });

    // Mock successful login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        json: { success: true, token: 'test-token', user_id: 'user-123' }
      });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'existing@example.com');
    await page.waitForSelector('[data-testid="email-existing-user"]');

    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');

    // Block should turn green on success
    await expect(page.locator('[data-testid="email-block-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-block"]')).toHaveClass(/bg-green|success/);
  });

  test('debounces email check API calls', async ({ page }) => {
    let apiCallCount = 0;
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      apiCallCount++;
      await route.fulfill({ json: { exists: false } });
    });

    await page.goto('/checkout/pro');

    // Type quickly
    await page.locator('[data-testid="email-input"]').pressSequentially('test@example.com', { delay: 50 });

    // Wait for debounce (500ms)
    await page.waitForTimeout(600);

    // Should only make 1-2 calls, not one per character
    expect(apiCallCount).toBeLessThan(5);
  });

  test('shows password strength indicator', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: false } });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'newuser@example.com');
    await page.waitForSelector('[data-testid="email-new-user"]');

    // Test weak password
    await page.fill('[data-testid="password-input"]', 'short');
    await expect(page.locator('[data-testid="password-strength"]')).toContainText('Weak');

    // Test medium password
    await page.fill('[data-testid="password-input"]', 'password123');
    await expect(page.locator('[data-testid="password-strength"]')).toContainText('Medium');

    // Test strong password
    await page.fill('[data-testid="password-input"]', 'StrongPass123!@#');
    await expect(page.locator('[data-testid="password-strength"]')).toContainText('Strong');
  });

  test('requires password confirmation to match', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: false } });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'newuser@example.com');
    await page.waitForSelector('[data-testid="email-new-user"]');

    // Fill password and mismatched confirmation
    await page.fill('[data-testid="password-input"]', 'StrongPass123!');
    await page.fill('[data-testid="password-confirm-input"]', 'DifferentPass123!');

    // Should show mismatch error
    await expect(page.locator('[data-testid="password-mismatch"]')).toBeVisible();
    await expect(page.locator('[data-testid="signup-button"]')).toBeDisabled();

    // Fix confirmation
    await page.fill('[data-testid="password-confirm-input"]', 'StrongPass123!');
    await expect(page.locator('[data-testid="password-mismatch"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="signup-button"]')).not.toBeDisabled();
  });

  test('shows forgot password link for existing user', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: true } });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'existing@example.com');
    await page.waitForSelector('[data-testid="email-existing-user"]');

    await expect(page.locator('[data-testid="forgot-password-link"]')).toBeVisible();
  });

  test('shows logout button after successful login', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: true } });
    });

    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        json: { success: true, token: 'test-token', user_id: 'user-123', user: { email: 'existing@example.com' } }
      });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'existing@example.com');
    await page.waitForSelector('[data-testid="email-existing-user"]');

    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');

    await expect(page.locator('[data-testid="logged-in-state"]')).toBeVisible();
    await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-input"]')).toBeDisabled();
  });

  test('logout resets the form', async ({ page }) => {
    await page.route('**/api/v1/auth/check-email**', async (route) => {
      await route.fulfill({ json: { exists: true } });
    });

    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        json: { success: true, token: 'test-token', user_id: 'user-123', user: { email: 'existing@example.com' } }
      });
    });

    await page.goto('/checkout/pro');
    await page.fill('[data-testid="email-input"]', 'existing@example.com');
    await page.waitForSelector('[data-testid="email-existing-user"]');

    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('[data-testid="logout-button"]');

    // Click logout
    await page.click('[data-testid="logout-button"]');

    // Form should be reset
    await expect(page.locator('[data-testid="email-input"]')).not.toBeDisabled();
    await expect(page.locator('[data-testid="email-input"]')).toHaveValue('');
  });
});
```

---

## TDD Phase 2: Write Failing Unit Tests

### 2.1 Unit Test: useEmailCheck composable

**File:** `vbwd-frontend/user/vue/tests/unit/composables/useEmailCheck.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useEmailCheck } from '@/composables/useEmailCheck';
import { flushPromises } from '@vue/test-utils';
import * as api from '@/api';

vi.mock('@/api');

describe('useEmailCheck', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts with idle state', () => {
    const { state } = useEmailCheck();
    expect(state.value).toBe('idle');
  });

  it('sets checking state during API call', async () => {
    vi.mocked(api.default.get).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ exists: false }), 100))
    );

    const { checkEmail, state } = useEmailCheck();
    checkEmail('test@example.com');

    expect(state.value).toBe('checking');
  });

  it('sets new_user state when email not found', async () => {
    vi.mocked(api.default.get).mockResolvedValue({ exists: false });

    const { checkEmail, state } = useEmailCheck();
    await checkEmail('new@example.com');

    expect(state.value).toBe('new_user');
  });

  it('sets existing_user state when email found', async () => {
    vi.mocked(api.default.get).mockResolvedValue({ exists: true });

    const { checkEmail, state } = useEmailCheck();
    await checkEmail('existing@example.com');

    expect(state.value).toBe('existing_user');
  });

  it('normalizes email before checking', async () => {
    vi.mocked(api.default.get).mockResolvedValue({ exists: false });

    const { checkEmail } = useEmailCheck();
    await checkEmail('  TEST@Example.COM  ');

    expect(api.default.get).toHaveBeenCalledWith(
      expect.stringContaining('test@example.com')
    );
  });

  it('does not call API for invalid email', async () => {
    const { checkEmail, state } = useEmailCheck();
    await checkEmail('not-valid');

    expect(api.default.get).not.toHaveBeenCalled();
    expect(state.value).toBe('idle');
  });
});
```

---

## TDD Phase 3: Write Minimal Production Code

### 3.1 Create Composable

**File:** `vbwd-frontend/user/vue/src/composables/useEmailCheck.ts`

```typescript
import { ref, computed } from 'vue';
import api from '@/api';

type EmailState = 'idle' | 'checking' | 'new_user' | 'existing_user' | 'error';

export function useEmailCheck() {
  const state = ref<EmailState>('idle');
  const email = ref('');
  const error = ref<string | null>(null);

  const isValidEmail = (email: string): boolean => {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
  };

  const checkEmail = async (inputEmail: string, captchaToken?: string): Promise<void> => {
    const normalized = inputEmail.trim().toLowerCase();

    if (!isValidEmail(normalized)) {
      state.value = 'idle';
      return;
    }

    email.value = normalized;
    state.value = 'checking';
    error.value = null;

    try {
      const params = new URLSearchParams({ email: normalized });
      if (captchaToken) {
        params.append('captcha_token', captchaToken);
      }
      const response = await api.get(`/auth/check-email?${params.toString()}`);
      state.value = response.exists ? 'existing_user' : 'new_user';
    } catch (e) {
      state.value = 'error';
      error.value = 'Failed to check email';
    }
  };

  const reset = () => {
    state.value = 'idle';
    email.value = '';
    error.value = null;
  };

  return {
    state,
    email,
    error,
    checkEmail,
    reset,
    isNewUser: computed(() => state.value === 'new_user'),
    isExistingUser: computed(() => state.value === 'existing_user'),
    isChecking: computed(() => state.value === 'checking'),
  };
}
```

### 3.2 Create EmailBlock Component

**File:** `vbwd-frontend/user/vue/src/components/checkout/EmailBlock.vue`

```vue
<template>
  <div
    :class="[
      'email-block',
      { 'success': isLoggedIn, 'error': emailCheck.state.value === 'error' }
    ]"
    :data-testid="isLoggedIn ? 'email-block-success' : 'email-block'"
  >
    <h3>Customer Email</h3>

    <!-- Email Input -->
    <div class="form-group">
      <input
        v-model="emailInput"
        type="email"
        placeholder="Enter your email"
        data-testid="email-input"
        :disabled="isLoggedIn"
        @focus="trackEmailInput"
        @input="debouncedCheck"
      />
      <span v-if="emailCheck.isChecking.value" data-testid="email-checking" class="checking">
        Checking...
      </span>
    </div>

    <!-- New User: Register -->
    <div v-if="emailCheck.isNewUser.value" data-testid="email-new-user" class="new-user-form">
      <p class="hint">Create a password to continue</p>
      <input
        v-model="password"
        type="password"
        placeholder="Create password"
        data-testid="password-input"
        @input="trackPasswordInput"
      />
      <!-- Password Strength Indicator -->
      <div class="password-strength" data-testid="password-strength">
        <div :class="['strength-bar', passwordStrength]"></div>
        <span class="strength-label">{{ passwordStrengthLabel }}</span>
      </div>
      <!-- Password Confirmation -->
      <input
        v-model="passwordConfirm"
        type="password"
        placeholder="Confirm password"
        data-testid="password-confirm-input"
      />
      <p v-if="passwordMismatch" class="error-message" data-testid="password-mismatch">
        Passwords do not match
      </p>
      <button
        data-testid="signup-button"
        class="btn primary"
        :disabled="!canRegister"
        @click="handleRegister"
      >
        Sign Up & Continue
      </button>
    </div>

    <!-- Existing User: Login -->
    <div v-if="emailCheck.isExistingUser.value" data-testid="email-existing-user" class="login-form">
      <p data-testid="login-hint" class="hint text-red">
        Account exists. Enter password to login.
      </p>
      <input
        v-model="password"
        type="password"
        placeholder="Enter password"
        data-testid="password-input"
      />
      <a
        href="#"
        class="forgot-password-link"
        data-testid="forgot-password-link"
        @click.prevent="handleForgotPassword"
      >
        Forgot password?
      </a>
      <button
        data-testid="login-button"
        class="btn primary"
        :disabled="!canLogin"
        @click="handleLogin"
      >
        Login
      </button>
    </div>

    <!-- Logged In Success -->
    <div v-if="isLoggedIn" class="logged-in" data-testid="logged-in-state">
      <div class="logged-in-info">
        <span class="checkmark">✓</span>
        Logged in as {{ emailCheck.email.value }}
      </div>
      <button
        class="btn secondary logout-btn"
        data-testid="logout-button"
        @click="handleLogout"
      >
        Logout
      </button>
    </div>

    <!-- Error -->
    <p v-if="authError" class="error-message">{{ authError }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useEmailCheck } from '@/composables/useEmailCheck';
import { useAuthStore } from '@/stores/auth';
import { useAnalytics } from '@/composables/useAnalytics';
import api from '@/api';
import { debounce } from '@/utils/debounce';

const props = defineProps<{
  planSlug: string;
}>();

const emit = defineEmits<{
  (e: 'authenticated', userId: string): void;
  (e: 'logout'): void;
  (e: 'forgot-password', email: string): void;
}>();

const emailCheck = useEmailCheck();
const authStore = useAuthStore();
const analytics = useAnalytics();

const emailInput = ref('');
const password = ref('');
const passwordConfirm = ref('');
const isLoggedIn = ref(false);
const authError = ref<string | null>(null);
const inputStartTime = ref<number | null>(null);

// Password strength calculation
const passwordStrength = computed(() => {
  const p = password.value;
  if (p.length < 8) return 'weak';
  const hasLetters = /[a-zA-Z]/.test(p);
  const hasNumbers = /[0-9]/.test(p);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(p);
  if (p.length >= 12 && hasLetters && hasNumbers && hasSpecial) return 'strong';
  if (hasLetters && hasNumbers) return 'medium';
  return 'weak';
});

const passwordStrengthLabel = computed(() => {
  const labels = { weak: 'Weak', medium: 'Medium', strong: 'Strong' };
  return labels[passwordStrength.value];
});

const passwordMismatch = computed(() =>
  passwordConfirm.value.length > 0 && password.value !== passwordConfirm.value
);

const canRegister = computed(() =>
  password.value.length >= 8 &&
  password.value === passwordConfirm.value &&
  passwordStrength.value !== 'weak'
);

const canLogin = computed(() => password.value.length > 0);

// Debounced email check with reCAPTCHA
const debouncedCheck = debounce(async () => {
  if (!emailInput.value) return;

  // Track email input completed
  if (inputStartTime.value) {
    analytics.track('email-input-completed', {
      email_domain: emailInput.value.split('@')[1],
      duration_ms: Date.now() - inputStartTime.value,
    });
  }

  // Execute invisible reCAPTCHA
  const captchaToken = await grecaptcha.execute(
    import.meta.env.VITE_RECAPTCHA_SITE_KEY,
    { action: 'email_check' }
  );

  const startTime = Date.now();
  await emailCheck.checkEmail(emailInput.value, captchaToken);

  analytics.track('email-checked', {
    email_exists: emailCheck.isExistingUser.value,
    response_time_ms: Date.now() - startTime,
  });
}, 500);

const trackEmailInput = () => {
  if (!inputStartTime.value) {
    inputStartTime.value = Date.now();
    analytics.track('email-input-started', { plan_slug: props.planSlug });
  }
};

const trackPasswordInput = () => {
  // Track when user starts entering password (first keystroke)
};

const handleLogin = async () => {
  authError.value = null;
  analytics.track('login-started', { timestamp: Date.now() });
  const startTime = Date.now();

  try {
    const response = await api.post('/auth/login', {
      email: emailCheck.email.value,
      password: password.value,
    });
    if (response.success) {
      authStore.setToken(response.token);
      authStore.setUser(response.user);
      isLoggedIn.value = true;
      analytics.track('login-success', { duration_ms: Date.now() - startTime });
      emit('authenticated', response.user_id);
    } else {
      analytics.track('login-failed', { error_type: response.error });
      authError.value = response.error || 'Login failed';
    }
  } catch (e) {
    analytics.track('login-failed', { error_type: 'network_error' });
    authError.value = 'Login failed. Please try again.';
  }
};

const handleRegister = async () => {
  authError.value = null;
  analytics.track('registration-started', { timestamp: Date.now() });
  const startTime = Date.now();

  try {
    const response = await api.post('/auth/register', {
      email: emailCheck.email.value,
      password: password.value,
    });
    if (response.success) {
      authStore.setToken(response.token);
      authStore.setUser(response.user);
      isLoggedIn.value = true;
      analytics.track('registration-success', { duration_ms: Date.now() - startTime });
      emit('authenticated', response.user_id);
    } else {
      analytics.track('registration-failed', { error_type: response.error });
      authError.value = response.error || 'Registration failed';
    }
  } catch (e) {
    analytics.track('registration-failed', { error_type: 'network_error' });
    authError.value = 'Registration failed. Please try again.';
  }
};

const handleForgotPassword = () => {
  analytics.track('forgot-password-clicked', { timestamp: Date.now() });
  emit('forgot-password', emailCheck.email.value);
};

const handleLogout = () => {
  analytics.track('logout-clicked', { timestamp: Date.now() });
  authStore.logout();
  isLoggedIn.value = false;
  emailCheck.reset();
  emailInput.value = '';
  password.value = '';
  passwordConfirm.value = '';
  inputStartTime.value = null;
  emit('logout');
};

// Check if already logged in on mount
onMounted(() => {
  if (authStore.isAuthenticated) {
    isLoggedIn.value = true;
    emailInput.value = authStore.user?.email || '';
  }
});
</script>

<style scoped>
.email-block {
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
}

.email-block.success {
  border-color: #27ae60;
  background: #e8f8f0;
}

.email-block.error {
  border-color: #e74c3c;
}

.form-group {
  position: relative;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 10px;
}

.checking {
  position: absolute;
  right: 12px;
  top: 12px;
  color: #666;
  font-size: 0.875rem;
}

.hint {
  margin: 10px 0;
  font-size: 0.9rem;
}

.text-red {
  color: #e74c3c;
}

.btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.btn.primary {
  background: #3498db;
  color: white;
}

.btn.primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.logged-in {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #27ae60;
  font-weight: 500;
}

.checkmark {
  font-size: 1.5rem;
}

.error-message {
  color: #e74c3c;
  margin-top: 10px;
}

/* Password Strength Indicator */
.password-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.strength-bar {
  height: 4px;
  flex: 1;
  border-radius: 2px;
  transition: background-color 0.3s;
}

.strength-bar.weak {
  background: linear-gradient(90deg, #e74c3c 33%, #ddd 33%);
}

.strength-bar.medium {
  background: linear-gradient(90deg, #f39c12 66%, #ddd 66%);
}

.strength-bar.strong {
  background: #27ae60;
}

.strength-label {
  font-size: 0.75rem;
  text-transform: uppercase;
}

.strength-label.weak { color: #e74c3c; }
.strength-label.medium { color: #f39c12; }
.strength-label.strong { color: #27ae60; }

/* Forgot Password Link */
.forgot-password-link {
  display: block;
  text-align: right;
  font-size: 0.875rem;
  color: #3498db;
  margin-bottom: 10px;
}

.forgot-password-link:hover {
  text-decoration: underline;
}

/* Logged In State */
.logged-in {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logged-in-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #27ae60;
  font-weight: 500;
}

.btn.secondary {
  background: #ecf0f1;
  color: #333;
}

.btn.secondary:hover {
  background: #bdc3c7;
}

.logout-btn {
  width: auto;
  padding: 8px 16px;
}
</style>
```

### 3.3 Add Debounce Utility (if not exists)

**File:** `vbwd-frontend/user/vue/src/utils/debounce.ts`

```typescript
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}
```

### 3.4 Add useAnalytics Composable

**File:** `vbwd-frontend/user/vue/src/composables/useAnalytics.ts`

```typescript
/**
 * Simple analytics composable.
 * Can be extended to integrate with GA4, Plausible, etc.
 */
export function useAnalytics() {
  const track = (event: string, data: Record<string, unknown> = {}) => {
    // Log to console in development
    if (import.meta.env.DEV) {
      console.log('[Analytics]', event, data);
    }

    // Send to analytics provider (example: GA4)
    if (typeof gtag !== 'undefined') {
      gtag('event', event, data);
    }

    // Or custom endpoint
    // api.post('/analytics/events', { event, data, timestamp: Date.now() });
  };

  return { track };
}
```

### 3.5 Load reCAPTCHA Script

**File:** `vbwd-frontend/user/vue/index.html`

```html
<!-- Add before closing </head> -->
<script src="https://www.google.com/recaptcha/api.js?render=YOUR_SITE_KEY" async defer></script>
```

**File:** `.env`

```
VITE_RECAPTCHA_SITE_KEY=your_site_key_here
```

### 3.6 Add reCAPTCHA Type Declarations

**File:** `vbwd-frontend/user/vue/src/types/grecaptcha.d.ts`

```typescript
declare const grecaptcha: {
  ready: (callback: () => void) => void;
  execute: (siteKey: string, options: { action: string }) => Promise<string>;
};
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Composable handles email check, component handles UI |
| **O** - Open/Closed | Composable returns computed properties, easily extendable |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | Component emits single event, minimal props |
| **D** - Dependency Inversion | Uses api module, not direct fetch |

## No Over-engineering

- No global state management for email check (local composable sufficient)
- No complex validation library (simple regex)
- Debounce is a simple utility, not a library
- No separate form library

---

## Files Created

```
vbwd-frontend/user/vue/src/composables/useEmailCheck.ts
vbwd-frontend/user/vue/src/composables/useAnalytics.ts
vbwd-frontend/user/vue/src/components/checkout/EmailBlock.vue
vbwd-frontend/user/vue/src/utils/debounce.ts
vbwd-frontend/user/vue/src/types/grecaptcha.d.ts
vbwd-frontend/user/vue/tests/e2e/checkout/checkout-email.spec.ts
vbwd-frontend/user/vue/tests/unit/composables/useEmailCheck.spec.ts
```

---

## Verification Checklist

- [ ] E2E tests written and FAILING
- [ ] Unit tests written and FAILING
- [ ] useEmailCheck composable implemented (with reCAPTCHA support)
- [ ] useAnalytics composable implemented
- [ ] EmailBlock component implemented
- [ ] Password strength indicator works (weak/medium/strong)
- [ ] Password confirmation validation works
- [ ] Forgot password link shows for existing users
- [ ] Logout button shows after login, resets form
- [ ] Debounce set to 500ms
- [ ] reCAPTCHA integration configured
- [ ] Global auth store integration works
- [ ] All analytics events fire correctly
- [ ] All tests PASSING
- [ ] Manual test in browser

## Run Tests

> **All tests run in Docker containers.** Run commands from `vbwd-frontend/` directory.

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --user --unit    # Unit tests
./bin/pre-commit-check.sh --user --e2e     # E2E tests

# From vbwd-frontend/user/vue/
npm run test -- --grep "useEmailCheck"     # Unit tests
npm run test:e2e -- checkout-email.spec.ts # E2E tests

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!

# Full regression
npm run test && npm run test:e2e
```

## Next Sprint Dependency
- Sprint 03 will integrate this component into Checkout.vue
- Sprint 03 will update router to allow guest checkout
