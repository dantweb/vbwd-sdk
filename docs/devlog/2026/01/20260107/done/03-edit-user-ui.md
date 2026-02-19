# Sprint Task 03: Add Edit User UI

**Priority:** High
**Type:** Feature
**Estimated Effort:** Medium

---

## Objective

Allow admins to edit existing user details through the UI.

---

## Implementation Options

### Option A: Separate UserEdit.vue
- Create new `UserEdit.vue` view
- Route: `/admin/users/:id/edit`
- Similar to UserCreate but pre-filled

### Option B: Modify UserCreate.vue for dual mode
- Rename to `UserForm.vue`
- Accept `mode` prop: 'create' | 'edit'
- Pre-fill fields in edit mode
- Route: `/admin/users/:id/edit`

**Recommended:** Option B (less duplication)

---

## Fields to Edit

- Email (maybe read-only?)
- Status (active/inactive/suspended)
- Role (user/admin)
- First Name
- Last Name
- Address fields
- Phone

---

## Backend Endpoint

`PUT /api/v1/admin/users/:id`

Request body:
```json
{
  "status": "active",
  "role": "user",
  "details": {
    "first_name": "John",
    "last_name": "Doe",
    ...
  }
}
```

---

## UI Flow

1. User clicks "Edit" button on UserDetails page
2. Navigate to `/admin/users/:id/edit`
3. Form pre-filled with current values
4. User modifies fields
5. Click "Save" - API call
6. Success: Toast + redirect to UserDetails
7. Error: Toast with error message

---

## Acceptance Criteria

- [ ] Edit button on UserDetails page
- [ ] Edit form loads with current user data
- [ ] Can modify status, role, and details
- [ ] Save updates user via API
- [ ] Success/error toast messages
- [ ] Redirect to details after save
- [ ] data-testid attributes added

---

*Created: 2026-01-07*
