# Sprint 4: User Cabinet & Subscription Management

**Goal:** Build user cabinet plugin for profile, password, and subscription management.

---

## Objectives

- [ ] User Cabinet plugin (implements IPlugin)
- [ ] Protected routes with auth guard
- [ ] Profile management (name, email)
- [ ] Password change functionality
- [ ] Address management
- [ ] View active subscriptions
- [ ] Subscription actions (upgrade, cancel)
- [ ] Invoice list and download
- [ ] E2E tests for cabinet features

---

## Tasks

### 4.1 User Cabinet Plugin Structure

```
src/plugins/user-cabinet/
├── index.ts                      # Plugin entry
├── routes.ts                     # Protected routes
├── store/
│   ├── userStore.ts              # User data store
│   └── subscriptionStore.ts      # Subscription store
├── components/
│   ├── CabinetLayout.vue         # Layout with sidebar
│   ├── CabinetSidebar.vue        # Navigation sidebar
│   ├── profile/
│   │   ├── ProfileForm.vue       # Profile editing
│   │   ├── PasswordForm.vue      # Password change
│   │   └── AddressForm.vue       # Address management
│   ├── subscriptions/
│   │   ├── SubscriptionList.vue
│   │   ├── SubscriptionCard.vue
│   │   ├── UpgradeDialog.vue
│   │   └── CancelDialog.vue
│   └── invoices/
│       ├── InvoiceList.vue
│       └── InvoiceRow.vue
└── __tests__/
    └── e2e/
        └── cabinet.spec.ts
```

---

### 4.2 User Store

**File:** `src/plugins/user-cabinet/store/userStore.ts`

```typescript
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useApi } from '@/core/api';
import type { UserProfile, UserDetails } from '@/core/api/types/user.types';

export const useUserStore = defineStore('user', () => {
  const api = useApi();

  const profile = ref<UserProfile | null>(null);
  const details = ref<UserDetails | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function loadProfile() {
    loading.value = true;
    error.value = null;
    try {
      profile.value = await api.user.getProfile();
    } catch (err: any) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function loadDetails() {
    loading.value = true;
    error.value = null;
    try {
      details.value = await api.user.getDetails();
    } catch (err: any) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function updateProfile(data: Partial<UserProfile>) {
    loading.value = true;
    error.value = null;
    try {
      profile.value = await api.user.updateProfile(data);
    } catch (err: any) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateDetails(data: Partial<UserDetails>) {
    loading.value = true;
    error.value = null;
    try {
      details.value = await api.user.updateDetails(data);
    } catch (err: any) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    profile,
    details,
    loading,
    error,
    loadProfile,
    loadDetails,
    updateProfile,
    updateDetails,
  };
});
```

---

### 4.3 Subscription Store

**File:** `src/plugins/user-cabinet/store/subscriptionStore.ts`

```typescript
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useApi } from '@/core/api';
import type { Subscription, Invoice } from '@/core/api/types/user.types';

export const useSubscriptionStore = defineStore('subscription', () => {
  const api = useApi();

  const subscriptions = ref<Subscription[]>([]);
  const invoices = ref<Invoice[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function loadSubscriptions() {
    loading.value = true;
    error.value = null;
    try {
      subscriptions.value = await api.user.getSubscriptions();
    } catch (err: any) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function loadInvoices() {
    loading.value = true;
    error.value = null;
    try {
      invoices.value = await api.user.getInvoices();
    } catch (err: any) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  function getActiveSubscriptions() {
    return subscriptions.value.filter((sub) => sub.status === 'active');
  }

  return {
    subscriptions,
    invoices,
    loading,
    error,
    loadSubscriptions,
    loadInvoices,
    getActiveSubscriptions,
  };
});
```

---

### 4.4 Cabinet Layout

**File:** `src/plugins/user-cabinet/components/CabinetLayout.vue`

```vue
<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 py-8">
      <div class="grid md:grid-cols-4 gap-8">
        <!-- Sidebar -->
        <div class="md:col-span-1">
          <CabinetSidebar />
        </div>

        <!-- Content -->
        <div class="md:col-span-3">
          <div class="bg-white rounded-lg shadow-md p-6">
            <router-view />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CabinetSidebar from './CabinetSidebar.vue';
</script>
```

---

### 4.5 Profile Form

**File:** `src/plugins/user-cabinet/components/profile/ProfileForm.vue`

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">Profile Settings</h2>

    <form @submit.prevent="handleSubmit" class="space-y-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          v-model="form.email"
          type="email"
          disabled
          class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
        />
        <p class="text-xs text-gray-500 mt-1">Email cannot be changed</p>
      </div>

      <div class="grid md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            First Name
          </label>
          <input
            v-model="form.firstName"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Last Name
          </label>
          <input
            v-model="form.lastName"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Address
        </label>
        <input
          v-model="form.addressLine1"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
      </div>

      <div class="grid md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            City
          </label>
          <input
            v-model="form.city"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Postal Code
          </label>
          <input
            v-model="form.postalCode"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Country
          </label>
          <input
            v-model="form.country"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      <button
        type="submit"
        class="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        :disabled="store.loading"
      >
        {{ store.loading ? 'Saving...' : 'Save Changes' }}
      </button>

      <p v-if="successMessage" class="text-green-600">{{ successMessage }}</p>
      <p v-if="store.error" class="text-red-600">{{ store.error }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useUserStore } from '../../store/userStore';

const store = useUserStore();
const successMessage = ref('');

const form = reactive({
  email: '',
  firstName: '',
  lastName: '',
  addressLine1: '',
  city: '',
  postalCode: '',
  country: '',
});

onMounted(async () => {
  await store.loadProfile();
  await store.loadDetails();

  if (store.profile) {
    form.email = store.profile.email;
  }

  if (store.details) {
    form.firstName = store.details.firstName;
    form.lastName = store.details.lastName;
    form.addressLine1 = store.details.addressLine1;
    form.city = store.details.city;
    form.postalCode = store.details.postalCode;
    form.country = store.details.country;
  }
});

async function handleSubmit() {
  try {
    await store.updateDetails({
      firstName: form.firstName,
      lastName: form.lastName,
      addressLine1: form.addressLine1,
      city: form.city,
      postalCode: form.postalCode,
      country: form.country,
    });

    successMessage.value = 'Profile updated successfully!';
    setTimeout(() => (successMessage.value = ''), 3000);
  } catch (error) {
    console.error('Failed to update profile:', error);
  }
}
</script>
```

---

### 4.6 Subscription List

**File:** `src/plugins/user-cabinet/components/subscriptions/SubscriptionList.vue`

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">My Subscriptions</h2>

    <div v-if="store.loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
    </div>

    <div v-else-if="store.subscriptions.length === 0" class="text-center py-12">
      <p class="text-gray-600">You don't have any subscriptions yet.</p>
      <router-link
        to="/wizard"
        class="mt-4 inline-block px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      >
        Browse Plans
      </router-link>
    </div>

    <div v-else class="space-y-4">
      <SubscriptionCard
        v-for="subscription in store.subscriptions"
        :key="subscription.id"
        :subscription="subscription"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useSubscriptionStore } from '../../store/subscriptionStore';
import SubscriptionCard from './SubscriptionCard.vue';

const store = useSubscriptionStore();

onMounted(async () => {
  await store.loadSubscriptions();
});
</script>
```

---

### 4.7 Routes with Auth Guard

**File:** `src/plugins/user-cabinet/routes.ts`

```typescript
import { PluginRoute } from '@core/plugin/IPlugin';

export const cabinetRoutes: PluginRoute[] = [
  {
    path: '/cabinet',
    component: () => import('./components/CabinetLayout.vue'),
    meta: {
      requiresAuth: true,
      title: 'My Account',
    },
    children: [
      {
        path: '',
        name: 'cabinet-dashboard',
        component: () => import('./components/Dashboard.vue'),
        meta: { title: 'Dashboard' },
      },
      {
        path: 'profile',
        name: 'cabinet-profile',
        component: () => import('./components/profile/ProfileForm.vue'),
        meta: { title: 'Profile' },
      },
      {
        path: 'subscriptions',
        name: 'cabinet-subscriptions',
        component: () => import('./components/subscriptions/SubscriptionList.vue'),
        meta: { title: 'Subscriptions' },
      },
      {
        path: 'invoices',
        name: 'cabinet-invoices',
        component: () => import('./components/invoices/InvoiceList.vue'),
        meta: { title: 'Invoices' },
      },
    ],
  },
];
```

---

### 4.8 Plugin Registration

**File:** `src/plugins/user-cabinet/index.ts`

```typescript
import { App } from 'vue';
import { IPlugin } from '@core/plugin/IPlugin';
import { PlatformSDK } from '@core/sdk/PlatformSDK';
import { cabinetRoutes } from './routes';

export class UserCabinetPlugin implements IPlugin {
  readonly name = 'user-cabinet';
  readonly version = '1.0.0';

  async install(app: App, sdk: PlatformSDK): Promise<void> {
    // Register routes
    cabinetRoutes.forEach((route) => {
      sdk.router.addRoute(route);
    });
  }

  registerRoutes() {
    return cabinetRoutes;
  }
}
```

---

## Testing Checklist

- [ ] User can view profile
- [ ] User can edit profile
- [ ] User can change password
- [ ] User can view subscriptions
- [ ] User can see subscription details
- [ ] User can view invoices
- [ ] Routes are protected by auth guard
- [ ] Redirects to login if not authenticated
- [ ] E2E tests pass

---

## Definition of Done

- [ ] User Cabinet plugin implemented
- [ ] All cabinet pages functional
- [ ] Profile management works
- [ ] Subscription viewing works
- [ ] Invoice listing works
- [ ] Auth guard protects routes
- [ ] Store manages state correctly
- [ ] E2E tests pass
- [ ] Documentation updated

---

## Next Sprint

**Sprint 5:** Access Control & Comprehensive E2E Tests
