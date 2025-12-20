# Sprint 0: Admin Foundation & Layout

**Goal:** Setup admin application structure, layout, and role-based authentication.

---

## Objectives

- [ ] Admin app project setup (separate from user app)
- [ ] Symlink to Core SDK (`@vbwd/core-sdk`)
- [ ] Admin layout with sidebar and topbar
- [ ] Admin authentication with role check
- [ ] Admin router with `adminRoleGuard`
- [ ] Admin dashboard (empty state)
- [ ] E2E test for admin login

---

## Tasks

### 0.1 Project Setup

**Commands:**

```bash
# Create admin Vue.js app
cd frontend/admin
npm create vite@latest vue -- --template vue-ts

cd vue

# Install dependencies (same as user app)
npm install vue-router@4 pinia@2 axios zod

# Install dev dependencies
npm install -D \
  @playwright/test \
  vitest \
  @vitest/ui \
  @vue/test-utils \
  happy-dom \
  tailwindcss \
  postcss \
  autoprefixer \
  eslint \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin \
  prettier \
  eslint-config-prettier \
  eslint-plugin-vue

# Initialize Tailwind
npx tailwindcss init -p
```

**Create symlink to Core SDK:**

```bash
# From frontend/admin/vue/
npm link ../../core
```

**package.json:**
```json
{
  "name": "vbwd-admin",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --port 8081",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "test": "npm run test:unit && npm run test:e2e",
    "test:unit": "vitest",
    "test:e2e": "playwright test",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx --fix"
  },
  "dependencies": {
    "@vbwd/core": "file:../../core",
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7"
  }
}
```

---

### 0.2 Admin Router with Role Guard

**File:** `src/router/index.ts`

```typescript
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@vbwd/core';

const router = createRouter({
  history: createWebHistory('/admin'),  // Base path /admin
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
    },
    {
      path: '/',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: {
        requiresAuth: true,
        requiredRole: 'admin',
      },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/Dashboard.vue'),
        },
      ],
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('../views/Forbidden.vue'),
    },
  ],
});

// Admin role guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } });
    return;
  }

  if (to.meta.requiredRole === 'admin') {
    if (authStore.currentUser?.role !== 'admin') {
      next({ name: 'forbidden' });
      return;
    }
  }

  next();
});

export default router;
```

---

### 0.3 Admin Layout

**File:** `src/layouts/AdminLayout.vue`

```vue
<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Topbar -->
    <AdminTopbar />

    <div class="flex">
      <!-- Sidebar -->
      <AdminSidebar />

      <!-- Main Content -->
      <main class="flex-1 p-8">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AdminTopbar from '../components/AdminTopbar.vue';
import AdminSidebar from '../components/AdminSidebar.vue';
</script>
```

**File:** `src/components/AdminTopbar.vue`

```vue
<template>
  <div class="bg-white border-b border-gray-200 px-6 py-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <h1 class="text-xl font-bold text-gray-900">VBWD Admin</h1>
      </div>

      <div class="flex items-center space-x-4">
        <!-- Search (placeholder) -->
        <div class="relative">
          <input
            type="search"
            placeholder="Search..."
            class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <!-- User Menu -->
        <div class="relative">
          <button
            class="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
            @click="showUserMenu = !showUserMenu"
          >
            <span>{{ authStore.currentUser?.email }}</span>
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          <!-- Dropdown -->
          <div
            v-if="showUserMenu"
            class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10"
          >
            <button
              class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              @click="handleLogout"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@vbwd/core';

const router = useRouter();
const authStore = useAuthStore();
const showUserMenu = ref(false);

async function handleLogout() {
  await authStore.logout();
  router.push({ name: 'login' });
}
</script>
```

**File:** `src/components/AdminSidebar.vue`

```vue
<template>
  <aside class="w-64 bg-gray-800 text-white min-h-screen">
    <nav class="mt-8">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
        active-class="bg-gray-900 text-white"
      >
        <component :is="item.icon" class="h-5 w-5 mr-3" />
        {{ item.label }}
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const menuItems = computed(() => [
  { path: '/', label: 'Dashboard', icon: 'DashboardIcon' },
  { path: '/users', label: 'Users', icon: 'UsersIcon' },
  { path: '/plans', label: 'Plans', icon: 'TagIcon' },
  { path: '/subscriptions', label: 'Subscriptions', icon: 'RefreshIcon' },
  { path: '/invoices', label: 'Invoices', icon: 'DocumentIcon' },
  { path: '/analytics', label: 'Analytics', icon: 'ChartIcon' },
  { path: '/webhooks', label: 'Webhooks', icon: 'BoltIcon' },
  { path: '/settings', label: 'Settings', icon: 'CogIcon' },
]);
</script>
```

---

### 0.4 Admin Login View

**File:** `src/views/Login.vue`

```vue
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center mb-6">Admin Login</h1>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            v-model="form.email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            v-model="form.password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <button
          type="submit"
          class="w-full py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
          :disabled="loading"
        >
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>

        <p v-if="error" class="text-red-600 text-sm text-center">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@vbwd/core';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = reactive({
  email: '',
  password: '',
});

const loading = ref(false);
const error = ref('');

async function handleLogin() {
  loading.value = true;
  error.value = '';

  try {
    await authStore.login(form.email, form.password);

    // Check if user is admin
    if (authStore.currentUser?.role !== 'admin') {
      error.value = 'Access denied. Admin role required.';
      await authStore.logout();
      return;
    }

    // Redirect to original page or dashboard
    const redirect = route.query.redirect as string || '/';
    router.push(redirect);
  } catch (err: any) {
    error.value = err.message || 'Login failed';
  } finally {
    loading.value = false;
  }
}
</script>
```

---

### 0.5 Admin Dashboard (Empty State)

**File:** `src/views/Dashboard.vue`

```vue
<template>
  <div>
    <h1 class="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

    <!-- Placeholder KPIs -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">Total Users</div>
        <div class="text-3xl font-bold text-gray-900">-</div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">Active Subscriptions</div>
        <div class="text-3xl font-bold text-gray-900">-</div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">MRR</div>
        <div class="text-3xl font-bold text-gray-900">-</div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">Churn Rate</div>
        <div class="text-3xl font-bold text-gray-900">-</div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
      <div class="grid grid-cols-2 gap-4">
        <router-link
          to="/users"
          class="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          Manage Users
        </router-link>
        <router-link
          to="/plans"
          class="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          Manage Plans
        </router-link>
      </div>
    </div>
  </div>
</template>
```

---

### 0.6 E2E Test for Admin Login

**File:** `tests/e2e/admin-login.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Admin Login', () => {
  test('admin can login successfully', async ({ page }) => {
    await page.goto('/admin/login');

    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/admin/');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('non-admin cannot access admin area', async ({ page }) => {
    await page.goto('/admin/login');

    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');

    // Should show error
    await expect(page.locator('text=Access denied')).toBeVisible();
  });

  test('redirects to login if not authenticated', async ({ page }) => {
    await page.goto('/admin/');

    // Should redirect to login
    await expect(page).toHaveURL('/admin/login');
  });
});
```

---

## Testing Checklist

- [ ] Admin app runs on port 8081
- [ ] Symlink to Core SDK works
- [ ] Admin login with valid admin credentials
- [ ] Admin role check prevents non-admin access
- [ ] Layout renders correctly (sidebar + topbar)
- [ ] Dashboard is accessible after login
- [ ] Logout functionality works
- [ ] E2E tests pass

---

## Definition of Done

- [ ] Admin app project setup complete
- [ ] Core SDK symlinked
- [ ] Admin layout implemented
- [ ] Admin authentication with role check
- [ ] Admin router with guards
- [ ] Dashboard view (empty state)
- [ ] E2E test for login passes
- [ ] Documentation updated

---

## Next Sprint

**Sprint 1:** User Management Plugin
