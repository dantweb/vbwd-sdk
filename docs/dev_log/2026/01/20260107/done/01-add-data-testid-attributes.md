# Sprint Task 01: Add data-testid Attributes

**Priority:** High
**Type:** Test Infrastructure
**Estimated Effort:** Medium

---

## Objective

Add `data-testid` attributes to all interactive elements in admin views to improve E2E test reliability.

---

## Elements to Add data-testid

### Users.vue
- `data-testid="users-view"` - main container
- `data-testid="create-user-button"` - create button
- `data-testid="search-input"` - search field
- `data-testid="status-filter"` - status dropdown
- `data-testid="users-table"` - table element
- `data-testid="user-row-{id}"` - each row

### UserDetails.vue
- `data-testid="user-details-view"`
- `data-testid="edit-user-button"`
- `data-testid="user-email"`
- `data-testid="user-status"`

### UserCreate.vue
- `data-testid="user-create-form"`
- `data-testid="email-input"`
- `data-testid="password-input"`
- `data-testid="status-select"`
- `data-testid="role-select"`
- `data-testid="submit-button"`
- `data-testid="cancel-button"`

### Subscriptions.vue
- `data-testid="subscriptions-view"`
- `data-testid="create-subscription-button"`
- `data-testid="subscriptions-table"`

### Invoices.vue
- `data-testid="invoices-view"`
- `data-testid="invoices-table"`

### Navigation (Sidebar)
- `data-testid="nav-dashboard"`
- `data-testid="nav-users"`
- `data-testid="nav-plans"`
- `data-testid="nav-subscriptions"`
- `data-testid="nav-invoices"`
- `data-testid="nav-analytics"`
- `data-testid="nav-webhooks"`
- `data-testid="nav-settings"`

### Login.vue
- `data-testid="login-form"`
- `data-testid="email-input"`
- `data-testid="password-input"`
- `data-testid="login-button"`

---

## Acceptance Criteria

- [ ] All views have main container data-testid
- [ ] All buttons have data-testid
- [ ] All form inputs have data-testid
- [ ] Navigation links have data-testid
- [ ] E2E tests updated to use new selectors
- [ ] All E2E tests pass

---

*Created: 2026-01-07*
