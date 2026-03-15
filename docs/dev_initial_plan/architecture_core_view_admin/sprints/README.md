# Admin Application Sprints

**Project:** VBWD-SDK Admin - Plugin-Based Admin Dashboard
**Methodology:** TDD, SOLID, MVP, Clean Code
**Status:** Planning Phase

---

## Overview

Admin application development sprints. The admin app shares the **Core SDK** with the user app, so Sprint 0 and Sprint 1 focus on admin-specific plugins only.

---

## Sprint Sequence

### [Sprint 0: Admin Foundation & Layout](./sprint-0-admin-foundation.md)
**Duration:** 1 week
**Goal:** Setup admin app structure, layout, and authentication

**Key Deliverables:**
- ✅ Admin app project setup (separate from user app)
- ✅ Symlink to Core SDK (`@vbwd/core`)
- ✅ Admin layout (sidebar, topbar)
- ✅ Admin authentication (role check)
- ✅ Admin router with role guard
- ✅ Admin dashboard (empty state)

**Dependencies:** Core SDK (shared with user app)

---

### [Sprint 1: User Management Plugin](./sprint-1-user-management.md)
**Duration:** 2 weeks
**Goal:** Build user management plugin

**Key Deliverables:**
- ✅ User list with pagination, search, filters
- ✅ User details view
- ✅ User edit functionality
- ✅ Suspend/activate user
- ✅ View user subscriptions and invoices
- ✅ E2E tests for user management

**Dependencies:** Sprint 0, Backend admin endpoints

**Backend Requirements:**
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/:id`
- `PUT /api/v1/admin/users/:id`
- `PUT /api/v1/admin/users/:id/status`

---

### [Sprint 2: Plan Management Plugin](./sprint-2-plan-management.md)
**Duration:** 2 weeks
**Goal:** Build tariff plan management plugin

**Key Deliverables:**
- ✅ Plan list (all plans including inactive)
- ✅ Create new plan form
- ✅ Edit existing plan
- ✅ Activate/deactivate plans
- ✅ Multi-currency pricing
- ✅ Feature management
- ✅ E2E tests

**Dependencies:** Sprint 0

**Backend Requirements:**
- `GET /api/v1/admin/tarif-plans`
- `POST /api/v1/admin/tarif-plans`
- `PUT /api/v1/admin/tarif-plans/:id`
- `DELETE /api/v1/admin/tarif-plans/:id`

---

### [Sprint 3: Subscription & Invoice Management](./sprint-3-subscription-invoice.md)
**Duration:** 2 weeks
**Goal:** Build subscription and invoice management plugins

**Key Deliverables:**
- ✅ Subscription list with filters
- ✅ Subscription details and modification
- ✅ Manual subscription actions (cancel, extend)
- ✅ Invoice list with filters
- ✅ Invoice details and actions (mark paid)
- ✅ E2E tests

**Dependencies:** Sprint 1, Sprint 2

**Backend Requirements:**
- `GET /api/v1/admin/subscriptions`
- `PUT /api/v1/admin/subscriptions/:id`
- `GET /api/v1/admin/invoices`
- `PUT /api/v1/admin/invoices/:id/mark-paid`

---

### [Sprint 4: Analytics Dashboard Plugin](./sprint-4-analytics.md)
**Duration:** 2 weeks
**Goal:** Build analytics and reporting plugin

**Key Deliverables:**
- ✅ Dashboard with KPIs (MRR, ARR, churn)
- ✅ Revenue charts (Chart.js or ECharts)
- ✅ User growth visualization
- ✅ Subscription metrics
- ✅ Plan popularity charts
- ✅ Date range filters
- ✅ Export reports

**Dependencies:** Sprint 3

**Backend Requirements:**
- `GET /api/v1/admin/analytics/overview`
- `GET /api/v1/admin/analytics/revenue`
- `GET /api/v1/admin/analytics/users`
- `GET /api/v1/admin/analytics/subscriptions`

---

### [Sprint 5: Webhook Monitor & Settings](./sprint-5-webhooks-settings.md)
**Duration:** 1 week
**Goal:** Build webhook monitoring and system settings

**Key Deliverables:**
- ✅ Webhook event list with filters
- ✅ Webhook event details (JSON viewer)
- ✅ Retry failed webhooks
- ✅ System settings management
- ✅ Email template configuration
- ✅ Payment provider settings

**Dependencies:** Sprint 4

**Backend Requirements:**
- `GET /api/v1/admin/webhooks`
- `GET /api/v1/admin/webhooks/:id`
- `POST /api/v1/admin/webhooks/:id/retry`
- Settings endpoints

---

## Development Principles

### TDD (Test-Driven Development)
1. Write E2E test for admin workflow
2. Write unit tests for stores/composables
3. Implement feature
4. Refactor

### Shared Core SDK
- All core functionality from `@vbwd/core-sdk`
- Admin plugins extend base functionality
- Same components, same patterns
- Learn once, use in both apps

### Admin-Specific Patterns
- Data tables with pagination and sorting
- Bulk actions
- Confirmation dialogs for destructive actions
- Search and filter components
- Toast notifications

---

## Technology Stack

Same as user app (shared Core SDK):

| Category           | Technology          | Version  |
|--------------------|---------------------|----------|
| Framework          | Vue.js             | 3.4+     |
| Language           | TypeScript         | 5.x      |
| Build Tool         | Vite               | 5.x      |
| Routing            | Vue Router         | 4.x      |
| State Management   | Pinia              | 2.x      |
| HTTP Client        | Axios              | 1.x      |
| Validation         | Zod                | 3.x      |
| Styling            | Tailwind CSS       | 3.x      |
| Charts             | Chart.js or ECharts| Latest   |
| E2E Testing        | Playwright         | Latest   |
| Unit Testing       | Vitest             | Latest   |

---

## Sprint Progress Tracking

| Sprint | Status | Start Date | End Date | Notes |
|--------|--------|------------|----------|-------|
| 0      | 📋 Planned | TBD | TBD | Admin foundation |
| 1      | 📋 Planned | TBD | TBD | User management |
| 2      | 📋 Planned | TBD | TBD | Plan management |
| 3      | 📋 Planned | TBD | TBD | Subscriptions & Invoices |
| 4      | 📋 Planned | TBD | TBD | Analytics |
| 5      | 📋 Planned | TBD | TBD | Webhooks & Settings |

**Legend:**
- 📋 Planned
- 🏗️ In Progress
- ✅ Complete
- ⏸️ On Hold
- ❌ Cancelled

---

## Getting Started

### Prerequisites
- Node.js 20+
- npm 10+
- Core SDK setup (from user app Sprint 0)

### Initial Setup

```bash
# Navigate to admin directory
cd frontend/admin/vue

# Install dependencies (includes symlink to core)
npm install

# Run development server
npm run dev

# Accessible at http://localhost:8081/admin

# Run tests
npm run test:unit
npm run test:e2e
```

---

## Related Documentation

- [Admin Architecture Overview](../README.md)
- [Core SDK Documentation](../../architecture_core_view_sdk/README.md)
- [User App Architecture](../../architecture_core_view_user/README.md)
- [Server Architecture](../../architecture_server/README.md)
