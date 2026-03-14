# Sprint: Frontend - Admin Create User Form

**Date:** 2026-01-06
**Priority:** High
**Type:** Frontend Implementation
**Tests:** `vbwd-frontend/admin/vue/tests/e2e/admin-user-subscription-flow.spec.ts`

---

## Core Requirements

### Methodology
- **TDD-First**: E2E tests already exist. Run tests BEFORE and AFTER implementation.
- **SOLID Principles**: Single responsibility components, composable stores.
- **Clean Code**: Readable, well-named, self-documenting code.
- **No Over-engineering**: Minimal code to pass tests. No speculative features.

### Test Execution
```bash
# ALWAYS run tests in docker-compose environment
cd vbwd-frontend/admin/vue

# Ensure backend is running
cd ../../../vbwd-backend && docker-compose up -d && cd ../vbwd-frontend/admin/vue

# Run BEFORE implementation (should fail)
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-subscription-flow \
    --grep "Step 2: Create new user" --reporter=list

# Run AFTER implementation (should pass)
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-subscription-flow --reporter=list

# Run unit tests during development
npm run test
```

### Design Decisions
- **Form Type**: Separate page at `/admin/users/create` (not modal)
- **Navigation**: Button on Users list navigates to create page

### Definition of Done
- [ ] All existing E2E tests pass (no regressions)
- [ ] "Step 2: Create new user" test passes
- [ ] Route `/admin/users/create` exists
- [ ] Form matches existing UI patterns in codebase
- [ ] No unnecessary components/abstractions added
- [ ] Works with backend Sprint 05

---

## Objective

Implement Create User form in Admin panel so admin can create users with full details.

**TDD Discovery:** E2E tests expect "Create User" button and form, but they don't exist.
Tests timeout waiting for `button:has-text("Create")`.

---

## Test Reference

Tests that will pass after implementation:

```typescript
// From admin-user-subscription-flow.spec.ts (currently failing)
test('Step 2: Create new user with all fields', async ({ page }) => {
    await page.goto('/admin/users');

    // Click "Create User" or "Add User" button
    const createButton = page.locator('button:has-text("Create"), button:has-text("Add")').first();
    await createButton.click();

    // Wait for form to appear
    await page.waitForSelector('form', { timeout: 5000 });

    // Fill User fields
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    // ... etc
});
```

---

## Current State

**Users.vue** - Has list view but no create functionality
**UserDetails.vue** - Shows user details but no edit/create form

---

## Implementation Plan

### Phase 1: Create User Form Component

**File:** `src/components/forms/UserForm.vue`

```vue
<template>
  <form @submit.prevent="handleSubmit" class="user-form">
    <h2>{{ isEdit ? 'Edit User' : 'Create User' }}</h2>

    <!-- User Fields -->
    <section class="form-section">
      <h3>Account</h3>

      <div class="form-group">
        <label for="email">Email *</label>
        <input
          id="email"
          name="email"
          type="email"
          v-model="form.email"
          required
          :disabled="isEdit"
        />
        <span v-if="errors.email" class="error">{{ errors.email }}</span>
      </div>

      <div class="form-group" v-if="!isEdit">
        <label for="password">Password *</label>
        <input
          id="password"
          name="password"
          type="password"
          v-model="form.password"
          required
          minlength="8"
        />
        <span v-if="errors.password" class="error">{{ errors.password }}</span>
      </div>

      <div class="form-group">
        <label for="status">Status</label>
        <select id="status" name="status" v-model="form.status">
          <option value="pending">Pending</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      <div class="form-group">
        <label for="role">Role</label>
        <select id="role" name="role" v-model="form.role">
          <option value="user">User</option>
          <option value="admin">Admin</option>
          <option value="vendor">Vendor</option>
        </select>
      </div>
    </section>

    <!-- UserDetails Fields -->
    <section class="form-section">
      <h3>Personal Details</h3>

      <div class="form-row">
        <div class="form-group">
          <label for="firstName">First Name</label>
          <input
            id="firstName"
            name="firstName"
            type="text"
            v-model="form.details.first_name"
          />
        </div>

        <div class="form-group">
          <label for="lastName">Last Name</label>
          <input
            id="lastName"
            name="lastName"
            type="text"
            v-model="form.details.last_name"
          />
        </div>
      </div>

      <div class="form-group">
        <label for="addressLine1">Address Line 1</label>
        <input
          id="addressLine1"
          name="addressLine1"
          type="text"
          v-model="form.details.address_line_1"
        />
      </div>

      <div class="form-group">
        <label for="addressLine2">Address Line 2</label>
        <input
          id="addressLine2"
          name="addressLine2"
          type="text"
          v-model="form.details.address_line_2"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="city">City</label>
          <input
            id="city"
            name="city"
            type="text"
            v-model="form.details.city"
          />
        </div>

        <div class="form-group">
          <label for="postalCode">Postal Code</label>
          <input
            id="postalCode"
            name="postalCode"
            type="text"
            v-model="form.details.postal_code"
          />
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="country">Country</label>
          <select id="country" name="country" v-model="form.details.country">
            <option value="">Select Country</option>
            <option value="DE">Germany</option>
            <option value="AT">Austria</option>
            <option value="CH">Switzerland</option>
            <option value="US">United States</option>
            <option value="GB">United Kingdom</option>
            <!-- Add more countries as needed -->
          </select>
        </div>

        <div class="form-group">
          <label for="phone">Phone</label>
          <input
            id="phone"
            name="phone"
            type="tel"
            v-model="form.details.phone"
          />
        </div>
      </div>
    </section>

    <!-- Form Actions -->
    <div class="form-actions">
      <button type="button" @click="$emit('cancel')" class="btn-secondary">
        Cancel
      </button>
      <button type="submit" class="btn-primary" :disabled="isSubmitting">
        {{ isSubmitting ? 'Saving...' : 'Save' }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';

interface UserFormData {
  email: string;
  password: string;
  status: string;
  role: string;
  details: {
    first_name: string;
    last_name: string;
    address_line_1: string;
    address_line_2: string;
    city: string;
    postal_code: string;
    country: string;
    phone: string;
  };
}

const props = defineProps<{
  initialData?: Partial<UserFormData>;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  (e: 'submit', data: UserFormData): void;
  (e: 'cancel'): void;
}>();

const isSubmitting = ref(false);
const errors = reactive<Record<string, string>>({});

const form = reactive<UserFormData>({
  email: props.initialData?.email || '',
  password: '',
  status: props.initialData?.status || 'pending',
  role: props.initialData?.role || 'user',
  details: {
    first_name: props.initialData?.details?.first_name || '',
    last_name: props.initialData?.details?.last_name || '',
    address_line_1: props.initialData?.details?.address_line_1 || '',
    address_line_2: props.initialData?.details?.address_line_2 || '',
    city: props.initialData?.details?.city || '',
    postal_code: props.initialData?.details?.postal_code || '',
    country: props.initialData?.details?.country || '',
    phone: props.initialData?.details?.phone || '',
  },
});

const handleSubmit = () => {
  // Clear previous errors
  Object.keys(errors).forEach(key => delete errors[key]);

  // Validate
  if (!form.email) {
    errors.email = 'Email is required';
    return;
  }
  if (!props.isEdit && !form.password) {
    errors.password = 'Password is required';
    return;
  }
  if (!props.isEdit && form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
    return;
  }

  isSubmitting.value = true;
  emit('submit', { ...form });
};
</script>
```

### Phase 2: Update Users Page

**File:** `src/views/Users.vue` (extend)

```vue
<template>
  <div class="users-page">
    <header class="page-header">
      <h1>Users</h1>
      <button @click="showCreateForm = true" class="btn-primary">
        Create User
      </button>
    </header>

    <!-- Create User Modal/Drawer -->
    <div v-if="showCreateForm" class="modal-overlay">
      <div class="modal-content">
        <UserForm
          @submit="handleCreateUser"
          @cancel="showCreateForm = false"
        />
      </div>
    </div>

    <!-- User List -->
    <div class="user-list">
      <!-- existing user list content -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import UserForm from '@/components/forms/UserForm.vue';

const router = useRouter();
const usersStore = useUsersStore();

const showCreateForm = ref(false);

const handleCreateUser = async (data: any) => {
  try {
    const result = await usersStore.createUser(data);
    showCreateForm.value = false;

    // Show success toast
    // toast.success('User created successfully');

    // Navigate to user details
    router.push(`/admin/users/${result.id}`);
  } catch (error: any) {
    // Show error toast
    // toast.error(error.message || 'Failed to create user');
  }
};
</script>
```

### Phase 3: Update Users Store

**File:** `src/stores/users.ts` (add method)

```typescript
import { defineStore } from 'pinia';
import api from '@/api';

interface CreateUserData {
  email: string;
  password: string;
  status?: string;
  role?: string;
  details?: {
    first_name?: string;
    last_name?: string;
    address_line_1?: string;
    address_line_2?: string;
    city?: string;
    postal_code?: string;
    country?: string;
    phone?: string;
  };
}

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [] as any[],
    currentUser: null as any,
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async createUser(data: CreateUserData) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.post('/admin/users/', data);
        const newUser = response.data;

        // Add to local list
        this.users.unshift(newUser);

        return newUser;
      } catch (error: any) {
        this.error = error.response?.data?.error || 'Failed to create user';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // ... existing methods
  },
});
```

### Phase 4: Add Route

**File:** `src/router/index.ts` (extend)

```typescript
// Add route for create user page (if using separate page instead of modal)
{
  path: '/admin/users/create',
  name: 'CreateUser',
  component: () => import('@/views/UserCreate.vue'),
  meta: { requiresAuth: true, requiresAdmin: true },
},
```

---

## UI/UX Requirements

### Create Button
- Located in page header next to "Users" title
- Text: "Create User" or "Add User"
- Primary button styling

### Form Layout
- Two sections: "Account" and "Personal Details"
- Form fields match database schema
- Required fields marked with asterisk
- Validation errors shown inline

### Modal/Drawer
- Form appears in modal overlay
- Close on "Cancel" or backdrop click
- Prevent background scroll when open

### Success Flow
1. User clicks "Create User"
2. Modal opens with empty form
3. User fills in details
4. User clicks "Save"
5. API call to POST /admin/users
6. On success: close modal, show toast, navigate to user details
7. On error: show error message, keep form open

---

## Acceptance Criteria

- [ ] "Create User" button visible on Users page
- [ ] Clicking button opens form modal
- [ ] Form has all User fields (email, password, status, role)
- [ ] Form has all UserDetails fields (name, address, phone, etc.)
- [ ] Form validation works (required fields, password length)
- [ ] Submit calls POST /admin/users API
- [ ] Success redirects to user details page
- [ ] Error shows message in form
- [ ] E2E test `Step 2: Create new user with all fields` passes

---

## Test Verification

```bash
# Run E2E test
E2E_BASE_URL=http://localhost:8081 npx playwright test admin-user-subscription-flow \
    --grep "Step 2: Create new user"
```

---

*Created: 2026-01-05*
*Relates to: Sprint 04 (E2E & Integration Tests)*
*Depends on: Sprint 05 (Backend Admin Create User)*
