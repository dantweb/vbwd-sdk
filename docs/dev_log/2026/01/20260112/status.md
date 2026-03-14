# Development Log - 2026-01-12

**Date:** 2026-01-12
**Focus:** Admin Settings Tabs, Add-Ons Section, Token Bundles, User Frontend Sync & Security

## Overview

This session covers multiple areas:
1. Admin Settings page restructuring with tabs (Core Settings, Payments, Tokens)
2. Add-Ons section under Tarifs navigation
3. Token Bundles backend model and migrations
4. Token Bundles management UI in admin
5. User frontend synchronization with admin changes
6. User dashboard enhancement (profile, subscriptions, token balance, invoices)
7. Plan selection with checkout flow
8. Session security with configurable expiration

**Previous Session:** [2026-01-09](../20260109/status.md)

## Sprint Summary

| Sprint | Section | Tasks | Status |
|--------|---------|-------|--------|
| 01 | Admin Settings Tabs | 6 tasks | ✅ Complete |
| 02 | Add-Ons Navigation & Pages | 5 tasks | ✅ Complete |
| 03 | Backend Token Bundles | 6 tasks | ✅ Complete |
| 04 | Frontend Token Bundles Table | 7 tasks | ✅ Complete |
| 05 | User Frontend Sync & Security | 9 tasks | ✅ Complete (5.3-5.7) |

## Core Requirements

All sprints must adhere to:

- **TDD-First**: Write E2E Playwright tests BEFORE implementation
- **SOLID Principles**: Clean architecture, single responsibility
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only what's required for the current task
- **Code Reuse**: Leverage existing patterns from `Plans.vue`, `Subscriptions.vue`

## Test Execution

```bash
# Full pre-commit check (recommended)
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --admin --unit --integration --e2e

# Direct Playwright execution
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test

# Run against Docker
E2E_BASE_URL=http://localhost:8081 npx playwright test
```

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`
- User: `test@example.com` / `TestPass123@`

## Sprint Files Structure

```
docs/devlog/20260112/
├── status.md              # This file
├── todo/                  # Pending sprints (empty)
├── done/                  # Completed sprints
│   ├── 01-admin-settings-tabs.md
│   ├── 02-add-ons-section.md
│   ├── 03-backend-token-bundles.md
│   ├── 04-frontend-token-bundles.md
│   └── 05-user-frontend-sync-security.md
└── reports/               # Completion reports
    ├── sprint-01-admin-settings-tabs-report.md
    ├── sprint-02-add-ons-section-report.md
    ├── sprint-03-backend-token-bundles-report.md
    ├── sprint-04-frontend-token-bundles-report.md
    └── sprint-05-user-frontend-report.md
```

### Sprint Completion Workflow
1. Complete all tasks and Definition of Done
2. Move sprint file from `todo/` to `done/`
3. Create completion report in `reports/`
4. Update sprint status in this file (⏳ → ✅)

## Feature Overview

### Token Bundles Concept

Token bundles are upsell products that can be purchased alongside subscriptions:
- Example: 1000 TKN for $5
- Example: 10000 TKN for $50

Admins create and manage these bundles via the admin dashboard. Users can purchase bundles to add tokens to their account balance.

### Navigation Structure (Target)

**Admin Dashboard:**
```
Dashboard
Users
Tarifs
├── Plans
└── Add-Ons (NEW)
    ├── Tab1
    └── Tab2
Subscriptions
Invoices
Webhooks
Analytics
Settings
├── Core Settings (NEW tab)
├── Payments (NEW tab)
└── Tokens (NEW tab)
    └── Token Bundles Table
```

**User Dashboard (4 nav items):**
```
Dashboard      - Profile summary, subscription overview, recent invoices
Profile        - User details (name, address, company, etc.)
Subscription   - Current sub, token balance, invoices table (sortable, searchable)
Plans          - Active plans grid → /checkout (placeholder)
```

### Session Security

**Environment Variables:**
```bash
# vbwd-backend/.env
USER_SESSION_EXPIRY_HOURS=72    # User session expires after 72 hours inactivity
ADMIN_SESSION_EXPIRY_HOURS=24   # Admin session expires after 24 hours inactivity
```

- Sessions expire after X hours of no API contact
- On expiration, user is redirected to login
- Each API request updates the "last activity" timestamp

### Build Commands

```bash
# Rebuild admin frontend (from project root)
make rebuild-admin

# Rebuild all services
make up-build

# See root Makefile for all commands
```

---

## Related Documentation

- [Admin Frontend Architecture](../../architecture_core_view_admin/README.md)
- [Backend API Routes](../../architecture_core_server_ce/README.md)
- [Previous Session](../20260109/status.md)
