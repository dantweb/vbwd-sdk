# Sprint 04: Frontend Token Bundles Table & Config

**Date:** 2026-01-12
**Priority:** High
**Type:** Feature Implementation + E2E Testing
**Section:** Admin Token Bundles Management

## Goal

Implement the Token Bundles management UI in the Tokens tab of the Settings page. This includes a paginated table listing all token bundles, and a detail/edit view for configuring individual bundles.

## Dependencies

- **Sprint 01:** Settings page tabs must be complete
- **Sprint 03:** Backend API must be complete

## Clarified Requirements

| Aspect | Decision |
|--------|----------|
| **Edit form** | Separate page at `/settings/token-bundles/:id` |
| **Currency** | Uses default currency (no currency dropdown needed) |
| **Create form** | Separate page at `/settings/token-bundles/new` |

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required
- **Code Reuse**: Follow patterns from Plans.vue and PlanForm.vue

### Test Execution

```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-token-bundles
npm run test
```

### Definition of Done
- [ ] All E2E tests passing
- [ ] No TypeScript errors
- [ ] ESLint checks pass
- [ ] Token bundles table displays in Tokens tab
- [ ] Click row opens bundle config
- [ ] CRUD operations functional
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

### Task 4.1: E2E Tests - Token Bundles Table

**Goal:** Write Playwright tests for Token Bundles table

**Test Requirements:**
- [ ] Tokens tab shows Token Bundles heading
- [ ] Table displays bundle list
- [ ] Table has columns: Name, Tokens, Price, Currency, Status, Actions
- [ ] Pagination works
- [ ] "Create Bundle" button visible
- [ ] Click on row navigates to bundle detail

**Test File:** `tests/e2e/admin-token-bundles.spec.ts`

**Acceptance Criteria:**
- [ ] Tests written and initially failing (red phase)
- [ ] Tests cover table functionality
- [ ] Tests use proper data-testid selectors

---

### Task 4.2: Frontend - Token Bundles API Client

**Goal:** Create API client for token bundles

**API Methods:**
```typescript
// src/api/tokenBundles.ts
export const tokenBundlesApi = {
  list: (params: ListParams) => api.get('/admin/token-bundles', { params }),
  get: (id: string) => api.get(`/admin/token-bundles/${id}`),
  create: (data: CreateBundleData) => api.post('/admin/token-bundles', data),
  update: (id: string, data: UpdateBundleData) => api.put(`/admin/token-bundles/${id}`, data),
  delete: (id: string) => api.delete(`/admin/token-bundles/${id}`)
}
```

**Files to Create:**
- `src/api/tokenBundles.ts`

**Acceptance Criteria:**
- [ ] All API methods implemented
- [ ] TypeScript types defined
- [ ] Error handling

---

### Task 4.3: Frontend - Token Bundles Pinia Store

**Goal:** Create Pinia store for token bundles state

**Store Structure:**
```typescript
// src/stores/tokenBundles.ts
export const useTokenBundlesStore = defineStore('tokenBundles', {
  state: () => ({
    bundles: [] as TokenBundle[],
    currentBundle: null as TokenBundle | null,
    loading: false,
    error: null as string | null,
    pagination: {
      page: 1,
      perPage: 20,
      total: 0,
      pages: 0
    }
  }),

  actions: {
    async fetchBundles(page?: number),
    async fetchBundle(id: string),
    async createBundle(data: CreateBundleData),
    async updateBundle(id: string, data: UpdateBundleData),
    async deleteBundle(id: string)
  }
})
```

**Files to Create:**
- `src/stores/tokenBundles.ts`

**Acceptance Criteria:**
- [ ] Store manages bundle state
- [ ] Loading/error states handled
- [ ] Pagination supported

---

### Task 4.4: Frontend - Token Bundles Table Component

**Goal:** Create paginated table for token bundles in Settings Tokens tab

**Table Columns:**
| Column | Field | Sortable |
|--------|-------|----------|
| Name | name | Yes |
| Tokens | token_amount | Yes |
| Price | price (default currency) | Yes |
| Status | is_active | No |
| Actions | edit/delete | No |

**Component Features:**
- Sortable columns
- Pagination
- Status badges (Active/Inactive)
- Row click opens detail view
- Create button in header

**Files to Modify:**
- `src/views/Settings.vue` (Tokens tab content)

**UI Structure:**
```vue
<div v-if="activeTab === 'tokens'" data-testid="tokens-tab-content">
  <div class="section-header">
    <h2>Token Bundles</h2>
    <button @click="createBundle" data-testid="create-bundle-btn">
      Create Bundle
    </button>
  </div>

  <table data-testid="token-bundles-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Tokens</th>
        <th>Price</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="bundle in bundles"
        :key="bundle.id"
        @click="openBundle(bundle.id)"
        data-testid="bundle-row"
      >
        <td>{{ bundle.name }}</td>
        <td>{{ bundle.token_amount.toLocaleString() }}</td>
        <td>{{ formatPrice(bundle.price, bundle.currency) }}</td>
        <td>
          <span :class="bundle.is_active ? 'badge-active' : 'badge-inactive'">
            {{ bundle.is_active ? 'Active' : 'Inactive' }}
          </span>
        </td>
        <td>
          <button @click.stop="editBundle(bundle.id)">Edit</button>
          <button @click.stop="deleteBundle(bundle.id)">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>

  <Pagination
    :current-page="pagination.page"
    :total-pages="pagination.pages"
    @page-change="handlePageChange"
  />
</div>
```

**Acceptance Criteria:**
- [ ] Table renders bundle list
- [ ] Pagination works
- [ ] Row click navigates to detail
- [ ] Create button works

---

### Task 4.5: Frontend - Token Bundle Detail/Edit Page

**Goal:** Create page for viewing and editing token bundle

**Routes:**
- `/settings/token-bundles/new` - Create new bundle
- `/settings/token-bundles/:id` - Edit existing bundle

**Form Fields:**
- Name (text input)
- Description (textarea, optional)
- Token Amount (number input)
- Price (number input) - displayed in default currency
- Is Active (checkbox/toggle)
- Sort Order (number input)

**Files to Create:**
- `src/views/TokenBundleForm.vue`

**Files to Modify:**
- `src/router/index.ts` (add route)

**Component Structure:**
```vue
<template>
  <div class="token-bundle-form">
    <h1>{{ isEdit ? 'Edit Token Bundle' : 'Create Token Bundle' }}</h1>

    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="name">Name</label>
        <input
          id="name"
          v-model="form.name"
          required
          data-testid="bundle-name-input"
        />
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          id="description"
          v-model="form.description"
          data-testid="bundle-description-input"
        />
      </div>

      <div class="form-group">
        <label for="tokenAmount">Token Amount</label>
        <input
          id="tokenAmount"
          type="number"
          v-model.number="form.token_amount"
          min="1"
          required
          data-testid="bundle-tokens-input"
        />
      </div>

      <div class="form-group">
        <label for="price">Price</label>
        <input
          id="price"
          type="number"
          v-model.number="form.price"
          step="0.01"
          min="0"
          required
          data-testid="bundle-price-input"
        />
      </div>

      <div class="form-group">
        <label>
          <input
            type="checkbox"
            v-model="form.is_active"
            data-testid="bundle-active-checkbox"
          />
          Active
        </label>
      </div>

      <div class="form-actions">
        <button type="button" @click="cancel">Cancel</button>
        <button type="submit" data-testid="bundle-save-btn">
          {{ isEdit ? 'Save Changes' : 'Create Bundle' }}
        </button>
      </div>
    </form>
  </div>
</template>
```

**Acceptance Criteria:**
- [ ] Form displays all fields
- [ ] Currency dropdown populated
- [ ] Create mode works
- [ ] Edit mode loads existing data
- [ ] Save updates backend

---

### Task 4.6: E2E Tests - Token Bundle Form

**Goal:** Write Playwright tests for Token Bundle form

**Test Requirements:**
- [ ] Form page loads
- [ ] All form fields present
- [ ] Currency dropdown populated
- [ ] Create new bundle works
- [ ] Edit existing bundle works
- [ ] Validation errors display
- [ ] Cancel returns to list

**Test File:** `tests/e2e/admin-token-bundle-form.spec.ts`

**Acceptance Criteria:**
- [ ] Tests cover create flow
- [ ] Tests cover edit flow
- [ ] Tests cover validation

---

### Task 4.7: Integration & Final Testing

**Goal:** Full integration testing

**Requirements:**
- [ ] Run all E2E tests
- [ ] Run unit tests
- [ ] Manual end-to-end flow testing
- [ ] No console errors

**Test Flow:**
1. Navigate to Settings > Tokens tab
2. See empty state or list
3. Click "Create Bundle"
4. Fill form and save
5. See new bundle in list
6. Click bundle row
7. Edit bundle
8. Save changes
9. Delete bundle

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-token-bundles admin-token-bundle-form
npm run test
```

**Acceptance Criteria:**
- [ ] All E2E tests pass
- [ ] All unit tests pass
- [ ] Manual QA complete
- [ ] No regression in other features

---

## Files Summary

### Create
- `src/api/tokenBundles.ts`
- `src/stores/tokenBundles.ts`
- `src/views/TokenBundleForm.vue`
- `tests/e2e/admin-token-bundles.spec.ts`
- `tests/e2e/admin-token-bundle-form.spec.ts`
- `tests/unit/stores/tokenBundles.spec.ts`

### Modify
- `src/views/Settings.vue` (Tokens tab content)
- `src/router/index.ts` (add routes)

---

## TypeScript Types

```typescript
// types/tokenBundle.ts
export interface TokenBundle {
  id: string
  name: string
  description: string | null
  token_amount: number
  price: string
  currency: {
    id: string
    code: string
    symbol: string
  }
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface CreateBundleData {
  name: string
  description?: string
  token_amount: number
  price: number
  currency_id: string
  is_active?: boolean
  sort_order?: number
}

export interface UpdateBundleData extends Partial<CreateBundleData> {}

export interface TokenBundleListResponse {
  items: TokenBundle[]
  total: number
  page: number
  per_page: number
  pages: number
}
```

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 4.1 E2E Tests - Table | ⏳ Pending | |
| 4.2 API Client | ⏳ Pending | |
| 4.3 Pinia Store | ⏳ Pending | |
| 4.4 Table Component | ⏳ Pending | |
| 4.5 Detail/Edit Page | ⏳ Pending | |
| 4.6 E2E Tests - Form | ⏳ Pending | |
| 4.7 Integration Testing | ⏳ Pending | |
