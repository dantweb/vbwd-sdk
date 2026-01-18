# Sprint 02: Add-Ons Navigation & Pages

**Date:** 2026-01-12
**Priority:** High
**Type:** Feature Implementation + E2E Testing
**Section:** Navigation Enhancement

## Goal

Add "Add-Ons" section under Tarifs navigation with two tabs (Tab1 and Tab2). This creates a sub-navigation structure for tariff-related features.

## Clarified Requirements

| Aspect | Decision |
|--------|----------|
| **Navigation style** | Expandable section - click "Tarifs" to expand/collapse submenu |
| **Tab names** | Tab1 and Tab2 remain as placeholders for now |
| **Tab content** | Both tabs show placeholder content |

## Navigation Target Structure

```
Tarifs (click to expand/collapse)
├── Plans (existing)
└── Add-Ons (NEW)
    ├── Tab1 (placeholder)
    └── Tab2 (placeholder)
```

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required

### Test Execution

```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-addons
```

### Definition of Done
- [ ] All E2E tests passing
- [ ] No TypeScript errors
- [ ] ESLint checks pass
- [ ] Add-Ons navigation item visible under Tarifs
- [ ] Add-Ons page has 2 tabs
- [ ] App rebuilt with `make rebuild-admin` (see root Makefile)
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

### Build & Deploy

After implementation, rebuild the admin frontend:

```bash
# From project root
make rebuild-admin

# This runs:
# 1. cd vbwd-frontend/admin/vue && npm run build
# 2. cd vbwd-frontend/admin && docker-compose down
# 3. cd vbwd-frontend/admin && docker-compose up -d --build
```

Admin dashboard available at: http://localhost:8081

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`

---

## Tasks

### Task 2.1: E2E Tests - Add-Ons Navigation & Page

**Goal:** Write Playwright tests for Add-Ons

**Test Requirements:**
- [ ] Tarifs section is expandable or has submenu
- [ ] Add-Ons link is visible in navigation
- [ ] Add-Ons page loads successfully
- [ ] Add-Ons page has Tab1
- [ ] Add-Ons page has Tab2
- [ ] Tab switching works correctly

**Test File:** `tests/e2e/admin-addons.spec.ts`

**Acceptance Criteria:**
- [ ] Tests written and initially failing (red phase)
- [ ] Tests cover navigation and tab scenarios
- [ ] Tests use proper data-testid selectors

---

### Task 2.2: Frontend - Update Navigation Structure

**Goal:** Add Tarifs submenu with Plans and Add-Ons

**Implementation Options:**
1. Expandable sidebar section
2. Dropdown menu
3. Nested routes

**Recommended Approach:** Expandable sidebar section

**Files to Modify:**
- `src/App.vue` (navigation sidebar)
- `src/router/index.ts` (add route)

**Navigation Structure:**
```html
<div class="nav-section">
  <button @click="tarifsExpanded = !tarifsExpanded" data-testid="nav-tarifs">
    Tarifs
    <span>{{ tarifsExpanded ? '▼' : '▶' }}</span>
  </button>
  <div v-show="tarifsExpanded" class="nav-submenu">
    <router-link to="/plans" data-testid="nav-plans">Plans</router-link>
    <router-link to="/add-ons" data-testid="nav-addons">Add-Ons</router-link>
  </div>
</div>
```

**Acceptance Criteria:**
- [ ] Tarifs section expandable
- [ ] Plans and Add-Ons links visible when expanded
- [ ] Active state shown for current route

---

### Task 2.3: Frontend - Add-Ons Route

**Goal:** Create Add-Ons route

**Implementation:**
- Add `/add-ons` route
- Create AddOns.vue component
- Protect with admin auth guard

**Files to Create:**
- `src/views/AddOns.vue`

**Files to Modify:**
- `src/router/index.ts`

**Route Definition:**
```typescript
{
  path: '/add-ons',
  name: 'AddOns',
  component: () => import('../views/AddOns.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

**Acceptance Criteria:**
- [ ] Route accessible at /add-ons
- [ ] Protected by authentication
- [ ] Component loads without errors

---

### Task 2.4: Frontend - Add-Ons Page with Tabs

**Goal:** Create Add-Ons page with Tab1 and Tab2

**Implementation:**
- Create page with tab navigation
- Tab1: Placeholder content
- Tab2: Placeholder content

**Component Structure:**
```vue
<template>
  <div class="add-ons-page">
    <h1>Add-Ons</h1>

    <div class="tabs" data-testid="addons-tabs">
      <button
        :class="{ active: activeTab === 'tab1' }"
        @click="activeTab = 'tab1'"
        data-testid="addons-tab1"
      >
        Tab1
      </button>
      <button
        :class="{ active: activeTab === 'tab2' }"
        @click="activeTab = 'tab2'"
        data-testid="addons-tab2"
      >
        Tab2
      </button>
    </div>

    <div v-if="activeTab === 'tab1'" data-testid="addons-tab1-content">
      <p>Tab1 content coming soon...</p>
    </div>

    <div v-if="activeTab === 'tab2'" data-testid="addons-tab2-content">
      <p>Tab2 content coming soon...</p>
    </div>
  </div>
</template>
```

**Files to Create:**
- `src/views/AddOns.vue`

**Acceptance Criteria:**
- [ ] Page renders with tabs
- [ ] Tab switching works
- [ ] Placeholder content displays

---

### Task 2.5: Integration & Testing

**Goal:** Verify Add-Ons navigation and page work

**Requirements:**
- [ ] Run E2E tests
- [ ] Manual verification of navigation
- [ ] Tab switching works
- [ ] No console errors

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-addons
```

**Acceptance Criteria:**
- [ ] All E2E tests pass
- [ ] Navigation works correctly
- [ ] Manual QA complete

---

## Files Summary

### Create
- `src/views/AddOns.vue`
- `tests/e2e/admin-addons.spec.ts`

### Modify
- `src/App.vue` (navigation)
- `src/router/index.ts` (routes)

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 2.1 E2E Tests - Add-Ons | ⏳ Pending | |
| 2.2 Update Navigation Structure | ⏳ Pending | |
| 2.3 Add-Ons Route | ⏳ Pending | |
| 2.4 Add-Ons Page with Tabs | ⏳ Pending | |
| 2.5 Integration & Testing | ⏳ Pending | |
