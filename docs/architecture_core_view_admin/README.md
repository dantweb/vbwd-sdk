# VBWD Admin Application Architecture

**Project:** VBWD-SDK - Admin Dashboard Application
**Status:** Initial Development
**License:** CC0 1.0 Universal (Public Domain)

---

## 1. Project Overview

The **VBWD Admin Application** is a separate Vue.js 3 + TypeScript application for administrative operations. It shares the same **Core SDK** (`@vbwd/core-sdk`) with the user-facing application but implements admin-specific plugins.

### Key Features

- **User Management**: View, edit, suspend user accounts
- **Plan Management**: Create, edit, deactivate tariff plans
- **Subscription Management**: View, modify user subscriptions
- **Invoice Management**: View invoices, manual payment marking
- **Analytics Dashboard**: Metrics, charts, reports
- **Webhook Monitoring**: View webhook logs and events
- **Settings**: System configuration

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VBWD Admin Application                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Application Shell                       │   │
│  │  - Admin Router (Vue Router, /admin base)               │   │
│  │  - Plugin Loader & Registry (from Core SDK)            │   │
│  │  - Admin Layout (sidebar, topbar)                      │   │
│  │  - Global State (Pinia)                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             Core SDK (@vbwd/core-sdk)                    │   │
│  │  - API Client (admin endpoints)                         │   │
│  │  - Auth Service (role: admin required)                 │   │
│  │  - Plugin System                                        │   │
│  │  - Event Bus                                            │   │
│  │  - Validation Service                                   │   │
│  │  - Shared UI Components                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Admin Plugin Layer                     │   │
│  │                                                          │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │   │
│  │  │ User Mgmt      │  │ Plan Mgmt      │  │ Analytics │  │   │
│  │  │ Plugin         │  │ Plugin         │  │ Plugin    │  │   │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │   │
│  │                                                          │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │   │
│  │  │ Invoice Mgmt   │  │ Webhook        │  │ Settings  │  │   │
│  │  │ Plugin         │  │ Monitor Plugin │  │ Plugin    │  │   │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Backend API   │
                  │  (Flask)       │
                  │  /api/v1/admin/*│
                  └────────────────┘
```

---

## 3. Admin Plugins

### 3.1 User Management Plugin

**Responsibilities:**
- List all users with pagination, search, filters
- View user details (profile, subscriptions, invoices)
- Edit user profile
- Suspend/activate user accounts
- View user activity logs

**Routes:**
- `/admin/users` - User list
- `/admin/users/:id` - User details
- `/admin/users/:id/edit` - Edit user
- `/admin/users/:id/subscriptions` - User subscriptions
- `/admin/users/:id/invoices` - User invoices

**Components:**
- `UserList.vue` - Table with filters and search
- `UserDetails.vue` - Full user information
- `UserEditForm.vue` - Edit user form
- `UserSubscriptions.vue` - User's subscription list
- `UserActivityLog.vue` - Activity history

---

### 3.2 Plan Management Plugin

**Responsibilities:**
- List all tariff plans
- Create new tariff plans
- Edit existing plans
- Activate/deactivate plans
- Set pricing and features
- Manage multi-currency pricing

**Routes:**
- `/admin/plans` - Plan list
- `/admin/plans/new` - Create plan
- `/admin/plans/:id/edit` - Edit plan
- `/admin/plans/:id/pricing` - Multi-currency pricing

**Components:**
- `PlanList.vue` - Table of all plans
- `PlanForm.vue` - Create/edit plan form
- `PlanPricingMatrix.vue` - Currency pricing grid
- `PlanFeatureEditor.vue` - Manage plan features

---

### 3.3 Subscription Management Plugin

**Responsibilities:**
- View all subscriptions with filters (status, plan, date)
- Manual subscription activation/cancellation
- Extend subscription periods
- Upgrade/downgrade subscriptions
- View subscription history

**Routes:**
- `/admin/subscriptions` - Subscription list
- `/admin/subscriptions/:id` - Subscription details
- `/admin/subscriptions/:id/edit` - Modify subscription

**Components:**
- `SubscriptionList.vue` - Filterable subscription table
- `SubscriptionDetails.vue` - Subscription info
- `SubscriptionActions.vue` - Extend, cancel, modify

---

### 3.4 Invoice Management Plugin

**Responsibilities:**
- List all invoices with filters
- View invoice details
- Manual payment marking
- Generate invoice PDFs
- Resend invoice emails
- View payment provider references

**Routes:**
- `/admin/invoices` - Invoice list
- `/admin/invoices/:id` - Invoice details

**Components:**
- `InvoiceList.vue` - Invoice table with filters
- `InvoiceDetails.vue` - Full invoice view
- `InvoiceActions.vue` - Mark paid, resend, download

---

### 3.5 Analytics Plugin

**Responsibilities:**
- Dashboard with key metrics (MRR, ARR, churn)
- Revenue charts (daily, monthly, yearly)
- User growth charts
- Subscription conversion funnel
- Plan popularity statistics
- Payment method breakdown

**Routes:**
- `/admin/analytics` - Main dashboard
- `/admin/analytics/revenue` - Revenue reports
- `/admin/analytics/users` - User analytics
- `/admin/analytics/subscriptions` - Subscription metrics

**Components:**
- `AnalyticsDashboard.vue` - Overview with KPIs
- `RevenueChart.vue` - Revenue visualization (Chart.js/ECharts)
- `UserGrowthChart.vue` - User growth over time
- `ConversionFunnel.vue` - Signup to paid conversion
- `PlanDistribution.vue` - Plan popularity pie chart

---

### 3.6 Webhook Monitor Plugin

**Responsibilities:**
- View webhook events from payment providers
- View event payloads
- Retry failed webhooks
- View webhook processing logs
- Filter by provider, event type, status

**Routes:**
- `/admin/webhooks` - Webhook event list
- `/admin/webhooks/:id` - Event details

**Components:**
- `WebhookList.vue` - Event list with filters
- `WebhookDetails.vue` - Event payload viewer (JSON)
- `WebhookRetry.vue` - Retry failed webhook

---

### 3.7 Settings Plugin

**Responsibilities:**
- System configuration
- Email template management
- SMTP settings
- Payment provider settings (Stripe/PayPal keys)
- Tax configuration
- Currency management

**Routes:**
- `/admin/settings` - Settings dashboard
- `/admin/settings/email` - Email settings
- `/admin/settings/payments` - Payment config
- `/admin/settings/taxes` - Tax settings

**Components:**
- `SettingsDashboard.vue` - Settings navigation
- `EmailSettings.vue` - Email config form
- `PaymentSettings.vue` - Payment provider config
- `TaxSettings.vue` - Tax configuration

---

## 4. Admin Layout Structure

### 4.1 Admin Layout Component

```
┌─────────────────────────────────────────────────────────┐
│ Topbar                                                  │
│ [VBWD Admin] [Search] [Notifications] [Admin User ▼]  │
├─────────────┬───────────────────────────────────────────┤
│             │                                           │
│  Sidebar    │  Main Content Area                        │
│             │  <router-view />                          │
│  Dashboard  │                                           │
│  Users      │                                           │
│  Plans      │                                           │
│  Subscr.    │                                           │
│  Invoices   │                                           │
│  Analytics  │                                           │
│  Webhooks   │                                           │
│  Settings   │                                           │
│             │                                           │
└─────────────┴───────────────────────────────────────────┘
```

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
```

---

## 5. Directory Structure

```
frontend/admin/vue/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── playwright.config.ts
├── vitest.config.ts
│
├── src/
│   ├── main.ts                    # Admin app entry point
│   ├── App.vue                    # Root component
│   │
│   ├── layouts/
│   │   ├── AdminLayout.vue        # Main admin layout
│   │   ├── AdminTopbar.vue        # Top navigation bar
│   │   └── AdminSidebar.vue       # Left sidebar menu
│   │
│   ├── plugins/                   # Admin-specific plugins
│   │   ├── user-management/
│   │   │   ├── index.ts           # Plugin entry
│   │   │   ├── routes.ts
│   │   │   ├── store/
│   │   │   │   └── userAdminStore.ts
│   │   │   ├── components/
│   │   │   │   ├── UserList.vue
│   │   │   │   ├── UserDetails.vue
│   │   │   │   └── UserEditForm.vue
│   │   │   └── composables/
│   │   │       └── useUserManagement.ts
│   │   │
│   │   ├── plan-management/
│   │   │   ├── index.ts
│   │   │   ├── routes.ts
│   │   │   ├── store/
│   │   │   │   └── planAdminStore.ts
│   │   │   ├── components/
│   │   │   │   ├── PlanList.vue
│   │   │   │   ├── PlanForm.vue
│   │   │   │   └── PlanPricingMatrix.vue
│   │   │   └── composables/
│   │   │       └── usePlanManagement.ts
│   │   │
│   │   ├── subscription-management/
│   │   ├── invoice-management/
│   │   ├── analytics/
│   │   ├── webhook-monitor/
│   │   └── settings/
│   │
│   ├── views/
│   │   └── Dashboard.vue          # Admin dashboard
│   │
│   └── router/
│       └── index.ts               # Admin router config
│
├── tests/
│   ├── unit/
│   └── e2e/
│       ├── admin-login.spec.ts
│       ├── user-management.spec.ts
│       ├── plan-management.spec.ts
│       └── analytics.spec.ts
│
└── node_modules/
    └── @vbwd/core -> ../../core   # Symlink to core SDK
```

---

## 6. Authentication & Access Control

### 6.1 Admin Authentication

Admin login is separate from user login but uses the same AuthService from Core SDK.

**Requirements:**
- User must have `role: 'admin'`
- Login at `/admin/login`
- Separate session management
- Admin-only API endpoints (`/api/v1/admin/*`)

### 6.2 Route Protection

All admin routes require:
1. Authentication (via `authGuard`)
2. Admin role (via `adminRoleGuard`)

**Example:**
```typescript
{
  path: '/admin',
  component: AdminLayout,
  meta: {
    requiresAuth: true,
    requiredRole: 'admin'
  },
  children: [...]
}
```

---

## 7. Admin API Endpoints (Backend)

### 7.1 User Management
- `GET /api/v1/admin/users` - List users (paginated)
- `GET /api/v1/admin/users/:id` - Get user details
- `PUT /api/v1/admin/users/:id` - Update user
- `PUT /api/v1/admin/users/:id/status` - Suspend/activate user
- `GET /api/v1/admin/users/:id/subscriptions` - User subscriptions
- `GET /api/v1/admin/users/:id/invoices` - User invoices

### 7.2 Plan Management
- `GET /api/v1/admin/tarif-plans` - List all plans (including inactive)
- `POST /api/v1/admin/tarif-plans` - Create plan
- `PUT /api/v1/admin/tarif-plans/:id` - Update plan
- `DELETE /api/v1/admin/tarif-plans/:id` - Deactivate plan

### 7.3 Subscription Management
- `GET /api/v1/admin/subscriptions` - List all subscriptions
- `GET /api/v1/admin/subscriptions/:id` - Get subscription
- `PUT /api/v1/admin/subscriptions/:id` - Update subscription
- `PUT /api/v1/admin/subscriptions/:id/cancel` - Cancel subscription
- `PUT /api/v1/admin/subscriptions/:id/extend` - Extend subscription

### 7.4 Invoice Management
- `GET /api/v1/admin/invoices` - List all invoices
- `GET /api/v1/admin/invoices/:id` - Get invoice
- `PUT /api/v1/admin/invoices/:id/mark-paid` - Manually mark as paid

### 7.5 Analytics
- `GET /api/v1/admin/analytics/overview` - Dashboard metrics
- `GET /api/v1/admin/analytics/revenue` - Revenue data
- `GET /api/v1/admin/analytics/users` - User growth data
- `GET /api/v1/admin/analytics/subscriptions` - Subscription metrics

### 7.6 Webhooks
- `GET /api/v1/admin/webhooks` - List webhook events
- `GET /api/v1/admin/webhooks/:id` - Get event details
- `POST /api/v1/admin/webhooks/:id/retry` - Retry failed webhook

---

## 8. Shared Core SDK Usage

The admin app uses the same Core SDK as the user app:

```typescript
// main.ts
import { createPlatformSDK } from '@vbwd/core';

const sdk = createPlatformSDK(app, router);

// SDK provides:
// - sdk.apiClient (with admin endpoints)
// - sdk.authService (checks admin role)
// - sdk.eventBus
// - sdk.validationService
```

**Admin-specific API calls:**
```typescript
// Uses IApiClient.admin endpoints
const users = await sdk.apiClient.admin.users.list();
const plans = await sdk.apiClient.admin.plans.list();
```

---

## 9. Development Principles

- **TDD First**: Write E2E tests for admin workflows
- **SOLID**: Admin plugins implement IPlugin
- **DRY**: Reuse Core SDK components and logic
- **Type Safety**: Full TypeScript coverage
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Lazy load plugins, optimize tables

---

## 10. Testing Strategy

### 10.1 E2E Tests (Playwright)

**Critical Flows:**
- Admin login with valid/invalid credentials
- User management (create, edit, suspend)
- Plan management (create, edit, deactivate)
- Subscription modification
- Invoice manual payment marking
- Analytics dashboard loading

**Example:** `tests/e2e/user-management.spec.ts`
```typescript
test('admin can suspend user account', async ({ page }) => {
  // Login as admin
  await page.goto('/admin/login');
  await page.fill('input[type="email"]', 'admin@example.com');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');

  // Navigate to users
  await page.click('text=Users');
  await expect(page).toHaveURL('/admin/users');

  // Find user and suspend
  await page.click('tr:has-text("john@example.com") button:has-text("Actions")');
  await page.click('text=Suspend');
  await page.click('button:has-text("Confirm")');

  // Verify status changed
  await expect(page.locator('text=suspended')).toBeVisible();
});
```

### 10.2 Unit Tests (Vitest)

- Admin store logic
- Admin composables
- Admin-specific utilities

---

## 11. UI/UX Design

### 11.1 Admin Theme
- Darker sidebar for admin feel
- Tables with pagination and sorting
- Search and filter components
- Action buttons with confirmation dialogs
- Toast notifications for success/error

### 11.2 Data Tables
- Pagination (10, 25, 50, 100 per page)
- Column sorting
- Search/filter bar
- Bulk actions (select multiple rows)
- Export to CSV

### 11.3 Forms
- Validation with immediate feedback
- Save/Cancel actions
- Dirty state tracking ("You have unsaved changes")

---

## 12. PlantUML Diagrams

All admin architecture diagrams:

| Diagram                     | File                              | Description                       |
|-----------------------------|-----------------------------------|-----------------------------------|
| Admin Plugin Architecture   | `puml/admin-plugin-architecture.puml` | Admin plugin system      |
| User Management Flow        | `puml/user-management-flow.puml`  | Admin user CRUD operations        |
| Analytics Dashboard         | `puml/analytics-architecture.puml`| Analytics plugin structure        |
| Admin Layout Structure      | `puml/admin-layout.puml`          | Layout component hierarchy        |

---

## Related Documentation

- [Core SDK Documentation](../architecture_core_view_sdk/README.md)
- [User App Architecture](../architecture_core_view_user/README.md)
- [Server Architecture](../architecture_server/README.md)
- [Admin Sprint Plans](./sprints/README.md)
