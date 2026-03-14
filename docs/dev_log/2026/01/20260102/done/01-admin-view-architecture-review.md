# Sprint: Admin View Architecture Review & Alignment

**Date:** 2026-01-02
**Goal:** Align admin frontend implementation with architecture documentation
**Reference:** `/docs/architecture_core_view_admin/README.md`
**Methodology:** TDD-First, SOLID, DI, Liskov Substitution, Clean Code

---

## Core Development Principles

### TDD-First (Test-Driven Development)

All development MUST follow the Red-Green-Refactor cycle:

```
1. RED    → Write failing test first
2. GREEN  → Write minimal code to pass
3. REFACTOR → Clean up while keeping tests green
```

**Rules:**
- No production code without a failing test
- Write E2E test for feature acceptance criteria FIRST
- Write unit tests for business logic BEFORE implementation
- Tests are documentation - they describe expected behavior

### SOLID Principles

| Principle | Application in Admin Frontend |
|-----------|-------------------------------|
| **S**ingle Responsibility | Each component/store has ONE reason to change. `UserList.vue` only lists users, `UserDetails.vue` only shows details |
| **O**pen/Closed | Components open for extension (slots, props), closed for modification. Use composition over inheritance |
| **L**iskov Substitution | All stores implement consistent interface. Any `IAdminStore` can be substituted without breaking code |
| **I**nterface Segregation | Small, focused interfaces. `IUserActions` separate from `IUserQueries` |
| **D**ependency Inversion | Components depend on abstractions (interfaces), not concrete implementations. Inject API client, don't instantiate |

### Dependency Injection (DI)

**Pattern:** Inject dependencies via props, provide/inject, or composables - never instantiate directly.

```typescript
// BAD - Direct instantiation (tight coupling)
const api = new ApiClient({ baseURL: '/api' });

// GOOD - Inject via composable (loose coupling)
import { useApi } from '@/composables/useApi';
const api = useApi();

// GOOD - Inject via provide/inject
const api = inject<IApiClient>('api');
```

**Benefits:**
- Testable (inject mocks in tests)
- Swappable (change implementation without changing consumers)
- Explicit dependencies (clear what a component needs)

### Liskov Substitution Principle (LSP)

All admin stores MUST be interchangeable where a base store is expected:

```typescript
// Base interface - all admin stores implement this
interface IAdminStore {
  loading: boolean;
  error: string | null;
  reset(): void;
}

// UserAdminStore implements IAdminStore
// PlanAdminStore implements IAdminStore
// AnalyticsStore implements IAdminStore

// Any function expecting IAdminStore works with ANY of these:
function handleStoreError(store: IAdminStore) {
  if (store.error) {
    showToast(store.error);
    store.reset();
  }
}
```

### Clean Code Principles

| Principle | Rule |
|-----------|------|
| **Meaningful names** | `fetchUserById(id)` not `getData(x)` |
| **Small functions** | Max 20 lines, single purpose |
| **No magic numbers** | `const MAX_PAGE_SIZE = 100` not `100` |
| **DRY** | Extract common logic to composables |
| **Comments** | Code should be self-documenting; comments explain WHY, not WHAT |
| **Error handling** | Always handle errors explicitly, never swallow |
| **Immutability** | Prefer `const`, avoid mutations |

---

## Executive Summary

This document compares the **expected admin architecture** (from `/docs/architecture_core_view_admin/`) with the **actual implementation** (in `/vbwd-frontend/admin/vue/`) and provides actionable steps to resolve deviations.

---

## 1. Current State Analysis

### 1.1 Target Structure (Flat Pattern - Same as User Frontend)

**Reference:** `vbwd-frontend/user/vue/src/` - Follow the same flat structure pattern.

```
vbwd-frontend/admin/vue/
├── src/
│   ├── main.ts                     # TypeScript entry point
│   ├── App.vue                     # Root component (router-view only)
│   ├── api/
│   │   └── index.ts                # Shared API client singleton
│   ├── layouts/
│   │   ├── AdminLayout.vue         # Main layout with sidebar + topbar
│   │   ├── AdminTopbar.vue         # Top navigation bar
│   │   └── AdminSidebar.vue        # Left sidebar menu
│   ├── stores/                     # Pinia stores (flat, no nesting)
│   │   ├── index.ts                # Barrel exports
│   │   ├── auth.ts                 # Authentication store
│   │   ├── users.ts                # User management store
│   │   ├── plans.ts                # Plan management store
│   │   ├── subscriptions.ts        # Subscription management store
│   │   ├── invoices.ts             # Invoice management store
│   │   ├── analytics.ts            # Analytics store
│   │   ├── webhooks.ts             # Webhook monitoring store
│   │   └── settings.ts             # Settings store
│   ├── views/                      # Page components (flat, no nesting)
│   │   ├── Dashboard.vue           # Main dashboard
│   │   ├── Login.vue               # Login page
│   │   ├── Forbidden.vue           # Access denied page
│   │   ├── Users.vue               # User list & management
│   │   ├── UserDetails.vue         # Single user details
│   │   ├── Plans.vue               # Plan list & management
│   │   ├── PlanForm.vue            # Create/edit plan
│   │   ├── Subscriptions.vue       # Subscription list
│   │   ├── SubscriptionDetails.vue # Single subscription
│   │   ├── Invoices.vue            # Invoice list
│   │   ├── InvoiceDetails.vue      # Single invoice
│   │   ├── Analytics.vue           # Analytics dashboard
│   │   ├── Webhooks.vue            # Webhook list
│   │   ├── WebhookDetails.vue      # Webhook event details
│   │   └── Settings.vue            # System settings
│   ├── router/
│   │   └── index.ts                # TypeScript, lazy loading
│   └── vite-env.d.ts
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                        # Playwright E2E tests
```

**Key Principles (from User Frontend):**
- **Flat stores/** - One file per domain, no nested folders
- **Flat views/** - One file per page, no nested folders
- **Barrel exports** - `stores/index.ts` exports all stores
- **Shared API client** - `api/index.ts` singleton
- **Layout component** - Wraps authenticated routes

### 1.2 Actual Implementation

```
vbwd-frontend/admin/vue/
├── src/
│   ├── main.js                     # JavaScript (not TypeScript)
│   ├── App.vue                     # Contains inline navbar (no layout)
│   ├── api/
│   │   └── index.ts                # Shared API client (good!)
│   ├── stores/
│   │   ├── auth.js                 # JavaScript
│   │   ├── analytics.ts            # TypeScript
│   │   ├── userAdmin.ts            # TypeScript
│   │   └── planAdmin.ts            # TypeScript
│   ├── router/
│   │   └── index.js                # JavaScript, no lazy loading
│   └── views/
│       ├── Login.vue
│       └── Dashboard.vue
├── tests/
│   └── unit/                       # Only unit tests, NO E2E tests
```

---

## 2. Deviation Matrix

| Category | Target (User Frontend Pattern) | Actual | Priority | Status |
|----------|-------------------------------|--------|----------|--------|
| **TypeScript** | All `.ts` files | Mix of `.js` and `.ts` | HIGH | Not Done |
| **Layouts folder** | `layouts/AdminLayout.vue`, `AdminTopbar.vue`, `AdminSidebar.vue` | Empty folder (layout in App.vue) | HIGH | Not Done |
| **Flat stores** | `stores/*.ts` (auth, users, plans, subscriptions, invoices, analytics, webhooks, settings) | Only auth.js, analytics.ts, userAdmin.ts, planAdmin.ts | HIGH | Partial |
| **Flat views** | `views/*.vue` (15 view files) | Only Login.vue, Dashboard.vue | HIGH | Not Done |
| **Router lazy loading** | `() => import()` syntax | Direct imports | MEDIUM | Not Done |
| **Admin role guard** | Role check in router guard | No role verification | HIGH | Not Done |
| **E2E tests** | Playwright tests in `tests/e2e/` | Only unit tests | HIGH | Not Done |
| **Store barrel exports** | `stores/index.ts` with all exports | Exists but incomplete | MEDIUM | Partial |
| **Core SDK usage** | `@vbwd/view-component` ApiClient | Custom local auth.js + shared api | MEDIUM | Partial |
| **Legacy code** | No "Submissions" reference | App.vue has "Submissions" link | HIGH | Not Done |

**Note:** Plugin architecture removed in favor of flat structure matching user frontend.

---

## 3. Positive Findings (Already Done)

1. **Shared API client** - `src/api/index.ts` properly implements singleton pattern matching user frontend
2. **Pinia stores for admin entities** - `userAdmin.ts`, `planAdmin.ts`, `analytics.ts` are well-structured
3. **Core library integration** - Uses `@vbwd/view-component` for ApiClient
4. **Basic auth flow** - Login/logout functionality works

---

## 4. Action Items

### Phase 1: TypeScript Migration (HIGH Priority)

#### 4.1.1 Convert `main.js` to `main.ts`
**File:** `src/main.js` → `src/main.ts`

```typescript
// Target implementation (reference: user frontend main.ts)
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { initializeApi } from './api';

initializeApi();

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');
```

#### 4.1.2 Convert `router/index.js` to `router/index.ts`
**File:** `src/router/index.js` → `src/router/index.ts`

Add:
- TypeScript types (`RouteRecordRaw`)
- Lazy loading with `() => import()`
- Admin role verification in guard

```typescript
// Target implementation
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/admin/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiredRole: 'admin' },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('../views/Dashboard.vue')
      },
      // ... more routes
    ]
  }
];
```

#### 4.1.3 Convert `stores/auth.js` to `stores/auth.ts`
**File:** `src/stores/auth.js` → `src/stores/auth.ts`

Add proper TypeScript types and use shared API client.

---

### Phase 2: Layout Implementation (HIGH Priority)

#### 4.2.1 Create `layouts/` folder
Create new folder: `src/layouts/`

#### 4.2.2 Create `AdminLayout.vue`
**File:** `src/layouts/AdminLayout.vue`

Reference: User frontend's `UserLayout.vue` pattern

```vue
<template>
  <div class="admin-layout">
    <AdminSidebar />
    <div class="admin-main">
      <AdminTopbar />
      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AdminSidebar from './AdminSidebar.vue';
import AdminTopbar from './AdminTopbar.vue';
</script>
```

#### 4.2.3 Create `AdminSidebar.vue`
**File:** `src/layouts/AdminSidebar.vue`

Menu items:
- Dashboard
- Users
- Plans
- Subscriptions
- Invoices
- Analytics
- Webhooks
- Settings

#### 4.2.4 Create `AdminTopbar.vue`
**File:** `src/layouts/AdminTopbar.vue`

Features:
- Brand/logo
- Search (placeholder)
- User menu with logout

#### 4.2.5 Update `App.vue`
Remove inline navbar, use `<router-view />` only:

```vue
<template>
  <router-view />
</template>
```

---

### Phase 3: Remove Legacy Code (HIGH Priority)

#### 4.3.1 Remove "Submissions" reference
**File:** `src/App.vue`

Remove:
```vue
<router-link to="/admin/submissions">Submissions</router-link>
```

This was already done in a previous session but App.vue still references it in the navbar.

---

### Phase 4: Admin Role Verification (HIGH Priority)

#### 4.4.1 Update router guard
Add role verification:

```typescript
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('auth_token');
  const userRole = JSON.parse(localStorage.getItem('user') || '{}').role;

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' });
    return;
  }

  if (to.meta.requiredRole === 'admin' && userRole !== 'admin') {
    next({ name: 'forbidden' });
    return;
  }

  next();
});
```

#### 4.4.2 Create `Forbidden.vue`
**File:** `src/views/Forbidden.vue`

Display "Access Denied" message for non-admin users.

---

### Phase 5: E2E Tests (HIGH Priority)

#### 4.5.1 Create `tests/e2e/` folder
Create folder: `tests/e2e/`

#### 4.5.2 Create `admin-login.spec.ts`
**File:** `tests/e2e/admin-login.spec.ts`

Test cases:
- Admin can login successfully
- Non-admin cannot access admin area
- Redirects to login if not authenticated

#### 4.5.3 Update `playwright.config.ts`
Ensure Playwright config exists and is properly configured.

---

### Phase 6: Missing Stores (HIGH Priority)

Following user frontend pattern - flat stores in `stores/` folder.

#### 4.6.1 Rename existing stores to match pattern
- `stores/userAdmin.ts` → `stores/users.ts`
- `stores/planAdmin.ts` → `stores/plans.ts`

#### 4.6.2 Create missing stores
Create in `src/stores/`:
- `subscriptions.ts` - Subscription management (admin view)
- `invoices.ts` - Invoice management (admin view)
- `webhooks.ts` - Webhook monitoring
- `settings.ts` - System settings

#### 4.6.3 Update barrel exports
**File:** `src/stores/index.ts`

```typescript
// Store barrel exports (matching user frontend pattern)
export { useAuthStore } from './auth';
export { useUsersStore } from './users';
export { usePlansStore } from './plans';
export { useSubscriptionsStore } from './subscriptions';
export { useInvoicesStore } from './invoices';
export { useAnalyticsStore } from './analytics';
export { useWebhooksStore } from './webhooks';
export { useSettingsStore } from './settings';
```

---

### Phase 7: Missing Views (HIGH Priority)

Following user frontend pattern - flat views in `views/` folder (no nested folders).

#### 4.7.1 Create missing views
Create in `src/views/` (flat structure):

| View | Purpose | Route |
|------|---------|-------|
| `Forbidden.vue` | Access denied page | `/admin/forbidden` |
| `Users.vue` | User list with search, filters, pagination | `/admin/users` |
| `UserDetails.vue` | Single user details, subscriptions, invoices | `/admin/users/:id` |
| `Plans.vue` | Plan list management | `/admin/plans` |
| `PlanForm.vue` | Create/edit plan | `/admin/plans/new`, `/admin/plans/:id/edit` |
| `Subscriptions.vue` | All subscriptions list | `/admin/subscriptions` |
| `SubscriptionDetails.vue` | Single subscription details | `/admin/subscriptions/:id` |
| `Invoices.vue` | All invoices list | `/admin/invoices` |
| `InvoiceDetails.vue` | Single invoice details | `/admin/invoices/:id` |
| `Analytics.vue` | Detailed analytics page | `/admin/analytics` |
| `Webhooks.vue` | Webhook events list | `/admin/webhooks` |
| `WebhookDetails.vue` | Webhook event details | `/admin/webhooks/:id` |
| `Settings.vue` | System settings | `/admin/settings` |

#### 4.7.2 View implementation pattern
Each view follows the same pattern as user frontend:

```vue
<template>
  <div class="page-name">
    <h1>Page Title</h1>
    <div v-if="store.loading" class="loading">Loading...</div>
    <div v-else-if="store.error" class="error">{{ store.error }}</div>
    <div v-else>
      <!-- Content -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useXxxStore } from '@/stores';

const store = useXxxStore();

onMounted(async () => {
  await store.fetchData();
});
</script>
```

---

## 5. Implementation Order (TDD Workflow)

### Phase 0: Foundation (No TDD - Infrastructure)

| Step | Task | Effort | Dependencies |
|------|------|--------|--------------|
| 0.1 | Remove "Submissions" link from App.vue | 5 min | None |
| 0.2 | Convert main.js → main.ts | 15 min | None |
| 0.3 | Convert stores/auth.js → auth.ts | 20 min | None |
| 0.4 | Convert router/index.js → index.ts | 30 min | 0.2 |

### Phase 1: Admin Login Flow (TDD)

| Step | Task | Type | Effort |
|------|------|------|--------|
| 1.1 | Write `admin-login.spec.ts` E2E test | RED | 30 min |
| 1.2 | Write `auth.spec.ts` unit tests | RED | 30 min |
| 1.3 | Write `Login.spec.ts` integration test | RED | 30 min |
| 1.4 | Implement auth store (TypeScript) | GREEN | 30 min |
| 1.5 | Update Login.vue component | GREEN | 30 min |
| 1.6 | Add admin role verification to router | GREEN | 30 min |
| 1.7 | Create Forbidden.vue | GREEN | 15 min |
| 1.8 | Verify all login E2E tests pass | VERIFY | 15 min |

### Phase 2: Admin Layout (TDD)

| Step | Task | Type | Effort |
|------|------|------|--------|
| 2.1 | Write `AdminLayout.spec.ts` integration test | RED | 30 min |
| 2.2 | Create layouts/ folder | GREEN | 5 min |
| 2.3 | Create AdminLayout.vue | GREEN | 45 min |
| 2.4 | Create AdminSidebar.vue | GREEN | 45 min |
| 2.5 | Create AdminTopbar.vue | GREEN | 30 min |
| 2.6 | Update App.vue to use `<router-view />` | GREEN | 10 min |
| 2.7 | Update router to use AdminLayout | GREEN | 15 min |
| 2.8 | Verify layout renders correctly | VERIFY | 15 min |

### Phase 3: User Management (TDD)

| Step | Task | Type | Effort |
|------|------|------|--------|
| 3.1 | Write `user-management.spec.ts` E2E test | RED | 45 min |
| 3.2 | Write `userAdmin.spec.ts` unit tests | RED | 45 min |
| 3.3 | Write `UserList.spec.ts` integration test | RED | 30 min |
| 3.4 | Verify userAdmin store implementation | GREEN | 30 min |
| 3.5 | Create UserList.vue | GREEN | 1 hr |
| 3.6 | Create UserDetails.vue | GREEN | 45 min |
| 3.7 | Create UserEdit.vue | GREEN | 30 min |
| 3.8 | Add user routes to router | GREEN | 15 min |
| 3.9 | Verify all user E2E tests pass | VERIFY | 15 min |

### Phase 4: Plan Management (TDD)

| Step | Task | Type | Effort |
|------|------|------|--------|
| 4.1 | Write `plan-management.spec.ts` E2E test | RED | 45 min |
| 4.2 | Write `planAdmin.spec.ts` unit tests | RED | 30 min |
| 4.3 | Write `PlanList.spec.ts` integration test | RED | 30 min |
| 4.4 | Verify planAdmin store implementation | GREEN | 20 min |
| 4.5 | Create PlanList.vue | GREEN | 1 hr |
| 4.6 | Create PlanForm.vue | GREEN | 45 min |
| 4.7 | Add plan routes to router | GREEN | 15 min |
| 4.8 | Verify all plan E2E tests pass | VERIFY | 15 min |

### Phase 5: Analytics Dashboard (TDD)

| Step | Task | Type | Effort |
|------|------|------|--------|
| 5.1 | Write `analytics-dashboard.spec.ts` E2E test | RED | 30 min |
| 5.2 | Write `analytics.spec.ts` unit tests | RED | 30 min |
| 5.3 | Write `Dashboard.spec.ts` integration test | RED | 30 min |
| 5.4 | Verify analytics store implementation | GREEN | 20 min |
| 5.5 | Update Dashboard.vue with KPI cards | GREEN | 1 hr |
| 5.6 | Add data-testid attributes for E2E | GREEN | 15 min |
| 5.7 | Verify all analytics E2E tests pass | VERIFY | 15 min |

### Phase 6: Stores & Remaining Views (TDD)

| Step | Task | Type | Effort |
|------|------|------|--------|
| 6.1 | Rename userAdmin.ts → users.ts, planAdmin.ts → plans.ts | REFACTOR | 15 min |
| 6.2 | Create subscriptions.ts store + Subscriptions.vue + SubscriptionDetails.vue | TDD | 3 hrs |
| 6.3 | Create invoices.ts store + Invoices.vue + InvoiceDetails.vue | TDD | 3 hrs |
| 6.4 | Create webhooks.ts store + Webhooks.vue + WebhookDetails.vue | TDD | 2 hrs |
| 6.5 | Create settings.ts store + Settings.vue | TDD | 2 hrs |
| 6.6 | Update stores/index.ts barrel exports | GREEN | 15 min |

### Summary

| Phase | Focus | Effort |
|-------|-------|--------|
| Phase 0 | Foundation (TypeScript migration) | 1.5 hrs |
| Phase 1 | Admin Login (TDD) | 3.5 hrs |
| Phase 2 | Admin Layout (TDD) | 3 hrs |
| Phase 3 | User Management (TDD) | 5 hrs |
| Phase 4 | Plan Management (TDD) | 4 hrs |
| Phase 5 | Analytics Dashboard (TDD) | 3 hrs |
| Phase 6 | Stores & Remaining Views (TDD) | 10.5 hrs |

**Total Estimated Effort:** ~30.5 hours (with comprehensive test coverage)

### File Count Summary

| Category | Files to Create/Modify |
|----------|------------------------|
| **Stores** | 4 new (subscriptions, invoices, webhooks, settings) + 2 rename + 1 update (index.ts) |
| **Views** | 13 new views |
| **Layouts** | 3 new (AdminLayout, AdminSidebar, AdminTopbar) |
| **Router** | 1 convert + update routes |
| **Tests** | ~15 E2E + ~20 integration + ~50 unit |

---

## 6. Verification Checklist

After completing all steps, verify:

- [ ] All `.js` files converted to `.ts`
- [ ] Admin layout renders with sidebar + topbar
- [ ] Sidebar has all menu items (Users, Plans, Subscriptions, etc.)
- [ ] Router uses lazy loading
- [ ] Admin role verification works (non-admin gets "Access Denied")
- [ ] E2E tests pass for admin login flow
- [ ] No "Submissions" reference in code
- [ ] All views are accessible via sidebar navigation
- [ ] Build completes without TypeScript errors
- [ ] Unit tests pass
- [ ] E2E tests pass

---

## 7. Reference Files

### User Frontend (Reference Implementation)
- `vbwd-frontend/user/vue/src/main.ts` - TypeScript entry point pattern
- `vbwd-frontend/user/vue/src/router/index.ts` - Router with lazy loading
- `vbwd-frontend/user/vue/src/layouts/UserLayout.vue` - Layout pattern
- `vbwd-frontend/user/vue/src/api/index.ts` - Shared API client pattern

### Architecture Documentation
- `/docs/architecture_core_view_admin/README.md` - Main architecture doc
- `/docs/architecture_core_view_admin/sprints/sprint-0-admin-foundation.md` - Sprint 0 details
- `/docs/architecture_core_view_admin/sprints/sprint-1-user-management.md` - User management plugin

### Core Library
- `vbwd-frontend/core/` - Shared `@vbwd/view-component` library

---

## 8. Testing Plan

### 8.1 Testing Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  ← Few, slow, high confidence
                    │ (Playwright)│
                    ├─────────────┤
                    │ Integration │  ← Medium amount, medium speed
                    │  (Vitest)   │
                    ├─────────────┤
                    │    Unit     │  ← Many, fast, focused
                    │  (Vitest)   │
                    └─────────────┘
```

| Layer | Tool | Count | Purpose |
|-------|------|-------|---------|
| **Unit** | Vitest | ~50+ tests | Test isolated functions, stores, composables |
| **Integration** | Vitest + Vue Test Utils | ~20+ tests | Test component interactions, store-component integration |
| **E2E** | Playwright | ~15+ tests | Test full user workflows in browser |

### 8.2 Unit Tests (Vitest)

**Location:** `tests/unit/`

**What to test:**
- Store actions and getters
- Composables
- Utility functions
- Form validation logic

#### 8.2.1 Store Unit Tests

**File:** `tests/unit/stores/userAdmin.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUserAdminStore } from '@/stores/userAdmin';

// Mock the API
vi.mock('@/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn()
  }
}));

describe('UserAdminStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('fetchUsers', () => {
    it('should set loading to true while fetching', async () => {
      const store = useUserAdminStore();
      const { api } = await import('@/api');

      api.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      store.fetchUsers({ page: 1, per_page: 10 });

      expect(store.loading).toBe(true);
    });

    it('should populate users on successful fetch', async () => {
      const store = useUserAdminStore();
      const { api } = await import('@/api');

      const mockUsers = [
        { id: '1', email: 'user1@test.com', name: 'User 1' },
        { id: '2', email: 'user2@test.com', name: 'User 2' }
      ];

      api.get.mockResolvedValue({ users: mockUsers, total: 2 });

      await store.fetchUsers({ page: 1, per_page: 10 });

      expect(store.users).toEqual(mockUsers);
      expect(store.total).toBe(2);
      expect(store.loading).toBe(false);
    });

    it('should set error on fetch failure', async () => {
      const store = useUserAdminStore();
      const { api } = await import('@/api');

      api.get.mockRejectedValue(new Error('Network error'));

      await expect(store.fetchUsers({ page: 1, per_page: 10 })).rejects.toThrow();

      expect(store.error).toBe('Network error');
      expect(store.loading).toBe(false);
    });
  });

  describe('suspendUser', () => {
    it('should call suspend API with reason', async () => {
      const store = useUserAdminStore();
      const { api } = await import('@/api');

      api.post.mockResolvedValue({ success: true });

      await store.suspendUser('user-123', 'Violation of TOS');

      expect(api.post).toHaveBeenCalledWith(
        '/admin/users/user-123/suspend',
        { reason: 'Violation of TOS' }
      );
    });
  });

  describe('reset', () => {
    it('should clear all state', () => {
      const store = useUserAdminStore();

      store.users = [{ id: '1' }];
      store.error = 'Some error';
      store.loading = true;

      store.reset();

      expect(store.users).toEqual([]);
      expect(store.error).toBeNull();
      expect(store.loading).toBe(false);
    });
  });
});
```

**File:** `tests/unit/stores/planAdmin.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { usePlanAdminStore } from '@/stores/planAdmin';

vi.mock('@/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn()
  }
}));

describe('PlanAdminStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('fetchPlans', () => {
    it('should fetch all plans including archived when flag is true', async () => {
      const store = usePlanAdminStore();
      const { api } = await import('@/api');

      api.get.mockResolvedValue({ plans: [] });

      await store.fetchPlans(true);

      expect(api.get).toHaveBeenCalledWith('/admin/tarif-plans', {
        params: { include_archived: true }
      });
    });
  });

  describe('createPlan', () => {
    it('should create plan and return plan_id', async () => {
      const store = usePlanAdminStore();
      const { api } = await import('@/api');

      api.post.mockResolvedValue({ plan_id: 'new-plan-123' });

      const result = await store.createPlan({
        name: 'Premium',
        price: 99,
        billing_period: 'monthly'
      });

      expect(result.plan_id).toBe('new-plan-123');
    });
  });

  describe('archivePlan', () => {
    it('should archive plan by id', async () => {
      const store = usePlanAdminStore();
      const { api } = await import('@/api');

      api.post.mockResolvedValue({ success: true });

      await store.archivePlan('plan-123');

      expect(api.post).toHaveBeenCalledWith('/admin/tarif-plans/plan-123/archive');
    });
  });
});
```

**File:** `tests/unit/stores/analytics.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAnalyticsStore } from '@/stores/analytics';

vi.mock('@/api', () => ({
  api: {
    get: vi.fn()
  }
}));

describe('AnalyticsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('fetchDashboard', () => {
    it('should fetch dashboard data and store it', async () => {
      const store = useAnalyticsStore();
      const { api } = await import('@/api');

      const mockDashboard = {
        mrr: { total: 10000, change_percent: 5.2 },
        revenue: { total: 50000, change_percent: 12.1 },
        churn: { total: 2.5, change_percent: -0.3 }
      };

      api.get.mockResolvedValue(mockDashboard);

      await store.fetchDashboard();

      expect(store.dashboard).toEqual(mockDashboard);
    });

    it('should pass date range params when provided', async () => {
      const store = useAnalyticsStore();
      const { api } = await import('@/api');

      api.get.mockResolvedValue({});

      await store.fetchDashboard({ start: '2026-01-01', end: '2026-01-31' });

      expect(api.get).toHaveBeenCalledWith('/admin/analytics/dashboard', {
        params: { start: '2026-01-01', end: '2026-01-31' }
      });
    });
  });

  describe('fetchPlanDistribution', () => {
    it('should fetch and store plan distribution', async () => {
      const store = useAnalyticsStore();
      const { api } = await import('@/api');

      const mockDistribution = {
        'Basic': 150,
        'Premium': 80,
        'Enterprise': 20
      };

      api.get.mockResolvedValue(mockDistribution);

      await store.fetchPlanDistribution();

      expect(store.planDistribution).toEqual(mockDistribution);
    });
  });
});
```

**File:** `tests/unit/stores/auth.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '@/stores/auth';

vi.mock('@/api', () => ({
  api: {
    post: vi.fn(),
    setToken: vi.fn(),
    clearToken: vi.fn()
  }
}));

describe('AuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('login', () => {
    it('should store token on successful login', async () => {
      const store = useAuthStore();
      const { api } = await import('@/api');

      api.post.mockResolvedValue({
        token: 'jwt-token-123',
        user: { id: '1', email: 'admin@test.com', role: 'admin' }
      });

      await store.login('admin@test.com', 'password');

      expect(store.token).toBe('jwt-token-123');
      expect(store.user.email).toBe('admin@test.com');
      expect(localStorage.getItem('admin_token')).toBe('jwt-token-123');
    });

    it('should set error on login failure', async () => {
      const store = useAuthStore();
      const { api } = await import('@/api');

      api.post.mockRejectedValue(new Error('Invalid credentials'));

      await expect(store.login('bad@test.com', 'wrong')).rejects.toThrow();

      expect(store.error).toBe('Invalid credentials');
    });
  });

  describe('logout', () => {
    it('should clear token and user data', () => {
      const store = useAuthStore();

      store.token = 'some-token';
      store.user = { id: '1' };
      localStorage.setItem('admin_token', 'some-token');

      store.logout();

      expect(store.token).toBeNull();
      expect(store.user).toBeNull();
      expect(localStorage.getItem('admin_token')).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      const store = useAuthStore();
      store.token = 'valid-token';

      expect(store.isAuthenticated).toBe(true);
    });

    it('should return false when token is null', () => {
      const store = useAuthStore();
      store.token = null;

      expect(store.isAuthenticated).toBe(false);
    });
  });

  describe('initAuth', () => {
    it('should restore token from localStorage', () => {
      localStorage.setItem('admin_token', 'stored-token');

      const store = useAuthStore();
      store.initAuth();

      expect(store.token).toBe('stored-token');
    });
  });
});
```

#### 8.2.2 Composables Unit Tests

**File:** `tests/unit/composables/useAdminRole.spec.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useAdminRole } from '@/composables/useAdminRole';

describe('useAdminRole', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return true for admin role', () => {
    localStorage.setItem('user', JSON.stringify({ role: 'admin' }));

    const { isAdmin } = useAdminRole();

    expect(isAdmin.value).toBe(true);
  });

  it('should return false for non-admin role', () => {
    localStorage.setItem('user', JSON.stringify({ role: 'user' }));

    const { isAdmin } = useAdminRole();

    expect(isAdmin.value).toBe(false);
  });

  it('should return false when no user in storage', () => {
    const { isAdmin } = useAdminRole();

    expect(isAdmin.value).toBe(false);
  });
});
```

### 8.3 Integration Tests (Vitest + Vue Test Utils)

**Location:** `tests/integration/`

**What to test:**
- Component + Store interactions
- Component rendering with real stores
- Form submissions
- Router navigation

#### 8.3.1 Component Integration Tests

**File:** `tests/integration/views/Dashboard.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Dashboard from '@/views/Dashboard.vue';
import { useAnalyticsStore } from '@/stores/analytics';

vi.mock('@/api', () => ({
  api: {
    get: vi.fn()
  }
}));

describe('Dashboard.vue Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('should display loading state while fetching', async () => {
    const { api } = await import('@/api');
    api.get.mockImplementation(() => new Promise(() => {}));

    const wrapper = mount(Dashboard);

    expect(wrapper.find('.loading').exists()).toBe(true);
  });

  it('should display dashboard metrics after loading', async () => {
    const { api } = await import('@/api');
    api.get.mockResolvedValue({
      mrr: { total: 10000, change_percent: 5.0 },
      revenue: { total: 50000, change_percent: 10.0 },
      user_growth: { total: 500, change_percent: 15.0 },
      churn: { total: 2.5, change_percent: -0.5 }
    });

    const wrapper = mount(Dashboard);
    await flushPromises();

    expect(wrapper.text()).toContain('10,000');
    expect(wrapper.text()).toContain('+5.0%');
  });

  it('should display error message on fetch failure', async () => {
    const { api } = await import('@/api');
    api.get.mockRejectedValue(new Error('Server error'));

    const wrapper = mount(Dashboard);
    await flushPromises();

    expect(wrapper.find('.error').exists()).toBe(true);
    expect(wrapper.text()).toContain('Server error');
  });
});
```

**File:** `tests/integration/views/Login.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import Login from '@/views/Login.vue';

vi.mock('@/api', () => ({
  api: {
    post: vi.fn(),
    setToken: vi.fn()
  }
}));

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/admin/login', name: 'login', component: Login },
    { path: '/admin/', name: 'dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
});

describe('Login.vue Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should render login form', () => {
    const wrapper = mount(Login, {
      global: { plugins: [router] }
    });

    expect(wrapper.find('input#username').exists()).toBe(true);
    expect(wrapper.find('input#password').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('should submit form and redirect on success', async () => {
    const { api } = await import('@/api');
    api.post.mockResolvedValue({
      token: 'jwt-token',
      user: { id: '1', role: 'admin' }
    });

    const wrapper = mount(Login, {
      global: { plugins: [router] }
    });

    await wrapper.find('input#username').setValue('admin@test.com');
    await wrapper.find('input#password').setValue('password');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(api.post).toHaveBeenCalledWith('/auth/login', {
      email: 'admin@test.com',
      password: 'password'
    });
  });

  it('should display error on login failure', async () => {
    const { api } = await import('@/api');
    api.post.mockRejectedValue(new Error('Invalid credentials'));

    const wrapper = mount(Login, {
      global: { plugins: [router] }
    });

    await wrapper.find('input#username').setValue('bad@test.com');
    await wrapper.find('input#password').setValue('wrong');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('.error').text()).toContain('Invalid credentials');
  });

  it('should disable submit button while loading', async () => {
    const { api } = await import('@/api');
    api.post.mockImplementation(() => new Promise(() => {}));

    const wrapper = mount(Login, {
      global: { plugins: [router] }
    });

    await wrapper.find('input#username').setValue('admin@test.com');
    await wrapper.find('input#password').setValue('password');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined();
  });
});
```

**File:** `tests/integration/views/UserList.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import UserList from '@/views/users/UserList.vue';

vi.mock('@/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

describe('UserList.vue Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('should render user list with pagination', async () => {
    const { api } = await import('@/api');
    api.get.mockResolvedValue({
      users: [
        { id: '1', email: 'user1@test.com', name: 'User 1', is_active: true },
        { id: '2', email: 'user2@test.com', name: 'User 2', is_active: false }
      ],
      total: 2,
      page: 1,
      per_page: 10
    });

    const wrapper = mount(UserList);
    await flushPromises();

    expect(wrapper.findAll('tr').length).toBeGreaterThan(1); // Header + data rows
    expect(wrapper.text()).toContain('user1@test.com');
    expect(wrapper.text()).toContain('user2@test.com');
  });

  it('should filter users by search term', async () => {
    const { api } = await import('@/api');
    api.get.mockResolvedValue({ users: [], total: 0 });

    const wrapper = mount(UserList);
    await flushPromises();

    await wrapper.find('input[type="search"]').setValue('john');
    await wrapper.find('input[type="search"]').trigger('input');
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith('/admin/users', expect.objectContaining({
      params: expect.objectContaining({ search: 'john' })
    }));
  });

  it('should suspend user with confirmation', async () => {
    const { api } = await import('@/api');
    api.get.mockResolvedValue({
      users: [{ id: '1', email: 'user@test.com', name: 'User', is_active: true }],
      total: 1
    });
    api.post.mockResolvedValue({ success: true });

    // Mock window.confirm
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    const wrapper = mount(UserList);
    await flushPromises();

    await wrapper.find('[data-testid="suspend-btn"]').trigger('click');
    await flushPromises();

    expect(api.post).toHaveBeenCalledWith('/admin/users/1/suspend', expect.any(Object));
  });
});
```

### 8.4 E2E Tests (Playwright)

**Location:** `tests/e2e/`

**What to test:**
- Complete user workflows
- Cross-page navigation
- Authentication flows
- Form submissions with backend

#### 8.4.1 Admin Login E2E

**File:** `tests/e2e/admin-login.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Admin Login', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.evaluate(() => localStorage.clear());
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/admin/');

    await expect(page).toHaveURL('/admin/login');
  });

  test('should login successfully with valid admin credentials', async ({ page }) => {
    await page.goto('/admin/login');

    await page.fill('input#username', 'admin@example.com');
    await page.fill('input#password', 'admin123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/admin/');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/admin/login');

    await page.fill('input#username', 'invalid@example.com');
    await page.fill('input#password', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error')).toBeVisible();
    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });

  test('should deny access to non-admin users', async ({ page }) => {
    await page.goto('/admin/login');

    // Login with regular user (non-admin)
    await page.fill('input#username', 'user@example.com');
    await page.fill('input#password', 'userpass');
    await page.click('button[type="submit"]');

    // Should show access denied or redirect to forbidden
    await expect(page.locator('text=Access denied')).toBeVisible();
  });

  test('should logout and redirect to login', async ({ page }) => {
    // First login
    await page.goto('/admin/login');
    await page.fill('input#username', 'admin@example.com');
    await page.fill('input#password', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/admin/');

    // Then logout
    await page.click('[data-testid="logout-button"]');

    await expect(page).toHaveURL('/admin/login');
  });

  test('should persist login across page reload', async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input#username', 'admin@example.com');
    await page.fill('input#password', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/admin/');

    // Reload page
    await page.reload();

    // Should still be on dashboard
    await expect(page).toHaveURL('/admin/');
  });
});
```

#### 8.4.2 User Management E2E

**File:** `tests/e2e/user-management.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('/admin/login');
    await page.fill('input#username', 'admin@example.com');
    await page.fill('input#password', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/admin/');
  });

  test('should navigate to users page from sidebar', async ({ page }) => {
    await page.click('text=Users');

    await expect(page).toHaveURL('/admin/users');
    await expect(page.locator('h1')).toContainText('Users');
  });

  test('should display user list with pagination', async ({ page }) => {
    await page.goto('/admin/users');

    // Should have table with users
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('tr').count()).toBeGreaterThan(1);

    // Should have pagination
    await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
  });

  test('should search users by email', async ({ page }) => {
    await page.goto('/admin/users');

    await page.fill('input[type="search"]', 'john@example.com');
    await page.press('input[type="search"]', 'Enter');

    // Should filter results
    await expect(page.locator('table')).toContainText('john@example.com');
  });

  test('should view user details', async ({ page }) => {
    await page.goto('/admin/users');

    // Click on first user row
    await page.click('tr[data-testid="user-row"]:first-child');

    await expect(page).toHaveURL(/\/admin\/users\/[a-zA-Z0-9-]+/);
    await expect(page.locator('h1')).toContainText('User Details');
  });

  test('should suspend user account', async ({ page }) => {
    await page.goto('/admin/users');

    // Find active user and suspend
    await page.click('tr:has-text("Active") [data-testid="actions-btn"]');
    await page.click('text=Suspend');

    // Confirm dialog
    await page.click('button:has-text("Confirm")');

    // Should show success message
    await expect(page.locator('[data-testid="toast"]')).toContainText('User suspended');
  });

  test('should activate suspended user', async ({ page }) => {
    await page.goto('/admin/users');

    // Find suspended user and activate
    await page.click('tr:has-text("Suspended") [data-testid="actions-btn"]');
    await page.click('text=Activate');

    await expect(page.locator('[data-testid="toast"]')).toContainText('User activated');
  });
});
```

#### 8.4.3 Plan Management E2E

**File:** `tests/e2e/plan-management.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Plan Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input#username', 'admin@example.com');
    await page.fill('input#password', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/admin/');
  });

  test('should navigate to plans page', async ({ page }) => {
    await page.click('text=Plans');

    await expect(page).toHaveURL('/admin/plans');
  });

  test('should display list of plans', async ({ page }) => {
    await page.goto('/admin/plans');

    await expect(page.locator('table')).toBeVisible();
  });

  test('should create new plan', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.click('button:has-text("Create Plan")');

    await expect(page).toHaveURL('/admin/plans/new');

    await page.fill('input[name="name"]', 'Test Plan');
    await page.fill('input[name="price"]', '49.99');
    await page.selectOption('select[name="billing_period"]', 'monthly');
    await page.click('button[type="submit"]');

    await expect(page.locator('[data-testid="toast"]')).toContainText('Plan created');
    await expect(page).toHaveURL('/admin/plans');
  });

  test('should edit existing plan', async ({ page }) => {
    await page.goto('/admin/plans');

    await page.click('tr:first-child [data-testid="edit-btn"]');

    await expect(page).toHaveURL(/\/admin\/plans\/[a-zA-Z0-9-]+\/edit/);

    await page.fill('input[name="price"]', '59.99');
    await page.click('button[type="submit"]');

    await expect(page.locator('[data-testid="toast"]')).toContainText('Plan updated');
  });

  test('should archive plan with confirmation', async ({ page }) => {
    await page.goto('/admin/plans');

    await page.click('tr:has-text("Active") [data-testid="archive-btn"]');

    // Should show confirmation dialog
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await page.click('button:has-text("Confirm Archive")');

    await expect(page.locator('[data-testid="toast"]')).toContainText('Plan archived');
  });
});
```

#### 8.4.4 Analytics Dashboard E2E

**File:** `tests/e2e/analytics-dashboard.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input#username', 'admin@example.com');
    await page.fill('input#password', 'admin123');
    await page.click('button[type="submit"]');
  });

  test('should display dashboard with KPIs', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');

    // Should show KPI cards
    await expect(page.locator('[data-testid="mrr-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-growth-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="churn-card"]')).toBeVisible();
  });

  test('should show loading state while fetching data', async ({ page }) => {
    // Intercept API to delay response
    await page.route('**/api/v1/admin/analytics/dashboard', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.continue();
    });

    await page.goto('/admin/');

    await expect(page.locator('.loading')).toBeVisible();
  });

  test('should display percentage changes', async ({ page }) => {
    await expect(page.locator('.stat-change')).toHaveCount(6);
  });

  test('should navigate to detailed analytics page', async ({ page }) => {
    await page.click('text=Analytics');

    await expect(page).toHaveURL('/admin/analytics');
  });
});
```

### 8.5 Test Coverage Requirements

| Category | Minimum Coverage | Target |
|----------|------------------|--------|
| **Unit Tests** | 80% | 90% |
| **Integration Tests** | 70% | 80% |
| **E2E Tests** | Critical paths 100% | All paths 90% |

### 8.6 Testing Commands

```bash
# Run all tests
npm run test

# Run unit tests only
npm run test:unit

# Run unit tests in watch mode
npm run test:unit -- --watch

# Run unit tests with coverage
npm run test:coverage

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run specific test file
npm run test:unit -- tests/unit/stores/userAdmin.spec.ts
```

### 8.7 Test File Structure

```
tests/
├── unit/
│   ├── stores/
│   │   ├── auth.spec.ts
│   │   ├── users.spec.ts           # Renamed from userAdmin
│   │   ├── plans.spec.ts           # Renamed from planAdmin
│   │   ├── subscriptions.spec.ts
│   │   ├── invoices.spec.ts
│   │   ├── analytics.spec.ts
│   │   ├── webhooks.spec.ts
│   │   └── settings.spec.ts
│   ├── composables/
│   │   ├── useAdminRole.spec.ts
│   │   └── usePagination.spec.ts
│   └── utils/
│       └── formatters.spec.ts
├── integration/
│   ├── views/
│   │   ├── Dashboard.spec.ts
│   │   ├── Login.spec.ts
│   │   ├── Users.spec.ts           # Flat naming
│   │   ├── UserDetails.spec.ts
│   │   ├── Plans.spec.ts
│   │   ├── PlanForm.spec.ts
│   │   ├── Subscriptions.spec.ts
│   │   ├── Invoices.spec.ts
│   │   ├── Analytics.spec.ts
│   │   ├── Webhooks.spec.ts
│   │   └── Settings.spec.ts
│   └── layouts/
│       └── AdminLayout.spec.ts
└── e2e/
    ├── admin-login.spec.ts
    ├── user-management.spec.ts
    ├── plan-management.spec.ts
    ├── subscription-management.spec.ts
    ├── invoice-management.spec.ts
    ├── webhook-management.spec.ts
    ├── settings.spec.ts
    └── analytics-dashboard.spec.ts
```

### 8.8 TDD Implementation Workflow

For each feature, follow this sequence:

```
1. Write E2E test (acceptance criteria)
   └── RED: Test fails (feature doesn't exist)

2. Write Integration test (component behavior)
   └── RED: Test fails

3. Write Unit tests (business logic)
   └── RED: Tests fail

4. Implement store/composable
   └── GREEN: Unit tests pass

5. Implement component
   └── GREEN: Integration tests pass

6. Wire up routing and layout
   └── GREEN: E2E tests pass

7. Refactor
   └── GREEN: All tests still pass
```

**Example: Implementing User Suspend Feature**

```
Step 1: E2E test (user-management.spec.ts)
  → test('should suspend user account')
  → FAILS: No suspend button exists

Step 2: Integration test (UserList.spec.ts)
  → test('should call suspendUser on click')
  → FAILS: UserList doesn't have suspend

Step 3: Unit test (userAdmin.spec.ts)
  → test('should call suspend API')
  → FAILS: suspendUser not implemented

Step 4: Implement suspendUser in store
  → Unit test PASSES

Step 5: Add suspend button to UserList.vue
  → Integration test PASSES

Step 6: Verify E2E flow
  → E2E test PASSES

Step 7: Refactor (extract SuspendUserDialog.vue)
  → All tests still PASS
```

---

## 9. Notes

1. **Flat structure decision:** Plugin architecture from original docs replaced with flat structure matching user frontend. This provides:
   - Consistency between user and admin frontends
   - Simpler navigation and maintenance
   - Easier onboarding for developers
   - Same patterns, same learning curve

2. **Package naming:** Architecture docs reference `@vbwd/core-sdk` but actual implementation uses `@vbwd/view-component`. Use existing `@vbwd/view-component`.

3. **Store naming convention:**
   - Rename `userAdmin.ts` → `users.ts` (matches user frontend pattern)
   - Rename `planAdmin.ts` → `plans.ts`
   - Use domain names, not "Admin" suffix

4. **View naming convention:**
   - List views: `Users.vue`, `Plans.vue`, `Invoices.vue`
   - Detail views: `UserDetails.vue`, `PlanForm.vue`, `InvoiceDetails.vue`
   - No nested folders in `views/`

5. **Backend API compatibility:** Ensure backend has all required admin endpoints:
   - `GET/PUT /api/v1/admin/users`
   - `GET/POST/PUT /api/v1/admin/tarif-plans`
   - `GET/PUT /api/v1/admin/subscriptions`
   - `GET/PUT /api/v1/admin/invoices`
   - `GET /api/v1/admin/analytics/*`
   - `GET /api/v1/admin/webhooks`

6. **Reference implementation:** Always refer to `vbwd-frontend/user/vue/src/` when implementing admin features. The patterns should match exactly.
