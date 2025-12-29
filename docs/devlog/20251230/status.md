# Sprint Status - 2025-12-29

This file tracks the status of all sprints in the 20251230 devlog.

## Completed Sprints

Completed sprints are moved to `/done` folder.

| Sprint | Name | Status | Completion Date |
|--------|------|--------|-----------------|
| 1.1 | Password Reset Flow (TDD) | DONE | 2025-12-29 |
| 1.2 | CSRF Protection | DONE | 2025-12-29 |
| 1.3 | Remove Hardcoded Admin Hint | DONE | 2025-12-29 |
| 2.1-2.3 | Backend Event Handlers | DONE (Already implemented) | 2025-12-29 |
| 2.4 | Frontend Event Bus | DONE | 2025-12-29 |
| **04** | **Access Control (Backend)** | **DONE** | **2025-12-29** |
| **05** | **View Core Extraction & UI Components** | **DONE** | **2025-12-29** |
| **05-01** | **Frontend Access Control** | **DONE** | **2025-12-29** |

## In Progress

| Sprint | Name | Status | Notes |
|--------|------|--------|-------|
| - | None | - | Ready for next sprint |

## Pending Sprints

| Sprint | Name | Priority | Est. Duration | Dependencies |
|--------|------|----------|---------------|--------------|
| 1.4 | HttpOnly Cookie Option | LOW (Optional) | 0.5 day | - |
| 06 | User Cabinet | MEDIUM | 2-3 days | Sprint 05 ✓ |
| 07 | Admin Management | MEDIUM | 2-3 days | Sprint 05 ✓ |
| 08 | Analytics Dashboard | LOW | 2-3 days | Sprint 05 ✓ |

## Implementation Notes

### Sprint 04 - Access Control (Backend)
- Created Role and Permission models with many-to-many relationships
- Created FeatureUsage model for tracking feature usage limits
- Implemented RBACService with permission checking, role assignment
- Implemented FeatureGuard service for tariff-based access control
- Created permission decorators:
  - `@require_permission(*permissions)` - Any permission required
  - `@require_all_permissions(*permissions)` - All permissions required
  - `@require_role(*roles)` - Role-based access
  - `@require_feature(feature_name)` - Feature gating
  - `@check_usage_limit(feature, amount)` - Usage limit tracking
- 28 unit tests for RBAC and FeatureGuard services

### Sprint 05 - View Core Extraction & UI Components
- Renamed package from `@vbwd/core-sdk` to `@vbwd/view-component`
- Created 16 UI components:
  - **UI:** Spinner, Button, Input, Modal, Card, Alert, Badge, Table, Pagination, Dropdown
  - **Forms:** FormField, FormGroup, FormError
  - **Layout:** Container, Row, Col
- Created CSS variables system with dark mode support
- 67 component unit tests
- Build output: index.mjs (69KB), index.cjs (71KB), style.css (28KB)

### Sprint 05-01 - Frontend Access Control
- Created auth store (`useAuthStore`) with user/token/roles management
- Created subscription store (`useSubscriptionStore`) for features/usage
- Created route guards:
  - `authGuard` / `createAuthGuard()` - Authentication + guest route protection
  - `roleGuard` / `createRoleGuard()` - Role-based route access
- Created `useFeatureAccess` composable for feature/usage checking
- Created access control components:
  - `FeatureGate.vue` - Conditional render based on feature access
  - `UsageLimit.vue` - Visual usage/limit progress bar with warning states
- 40 unit tests for guards, composables, and components

### Sprint 1.1 - Password Reset (TDD)
- Created security events (`PasswordResetRequestEvent`, `PasswordResetExecuteEvent`)
- Created PasswordResetToken model with UUID, expiration, usage tracking
- Created PasswordResetRepository with token CRUD operations
- Created PasswordResetService with pure business logic
- Created PasswordResetHandler that calls services and sends emails
- Updated auth routes to emit events (event-driven architecture)
- 23 unit tests - all passing

### Sprint 1.2 - CSRF Protection
- Added Flask-WTF==1.2.1 to requirements
- Configured CSRFProtect in extensions.py
- Exempted all API routes (they use JWT authentication)

### Sprint 1.3 - Remove Hardcoded Admin Hint
- Removed dev-mode credential hint from admin Login.vue
- Verified no other hardcoded credentials exist

### Sprint 2.1-2.3 - Backend Handlers
- User handlers already implemented (welcome email, status updates)
- Subscription handlers already implemented (activation, cancellation)
- Payment handlers already implemented (receipts, failure notifications)
- All handlers have unit tests

### Sprint 2.4 - Frontend Event Bus
- Created EventBus.ts with emit/on/off/once methods
- Created typed events in events.ts with AppEvents constants
- Created payload types for all event categories
- Comprehensive unit tests (20+ test cases)
- Exported from core SDK

---

## Architecture Corrections Made

The original sprint docs had an incorrect event flow:
- **WRONG**: `Request → Service → Event Dispatcher → Handler(s)`
- **CORRECT**: `Request → Route (emit event) → Event Dispatcher → Handler(s) → Services → DB`

All sprint documentation has been updated to reflect the correct event-driven architecture where:
1. Routes emit events (not call services directly)
2. Handlers orchestrate and call services
3. Services contain pure business logic (no event emission)

---

## Files Structure

```
docs/devlog/20251230/
├── status.md                    # This file
├── done/
│   ├── 01-security-fixes.md     # Sprint 01 (DONE)
│   ├── 02-event-system.md       # Sprint 02 (DONE)
│   ├── 04-access-control.md     # Sprint 04 (DONE)
│   ├── 05-ui-components.md      # Sprint 05 (DONE)
│   └── 05-01-frontend-access-control.md  # Sprint 05-01 (DONE)
└── todo/
    ├── sprint-plan.md           # Overall sprint plan
    ├── 06-user-cabinet.md       # Sprint 06 (PENDING)
    ├── 07-admin-management.md   # Sprint 07 (PENDING)
    └── 08-analytics-dashboard.md # Sprint 08 (PENDING)
```
