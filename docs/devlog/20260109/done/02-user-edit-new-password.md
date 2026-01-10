# Sprint 02: User Edit - New Password Field

**Date:** 2026-01-09
**Priority:** High
**Type:** Feature Implementation + E2E Testing
**Section:** Admin User Management

## Goal

Add a "New Password" field to the Account tab in the User Edit page, allowing admins to reset a user's password.

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required

### Test Execution

```bash
# Full pre-commit check (recommended)
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --admin --unit --integration --e2e

# Admin E2E tests only
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-user-edit

# Skip style checks
./bin/pre-commit-check.sh --admin --unit --integration --e2e --no-style
```

### Definition of Done
- [ ] All E2E tests passing
- [ ] No TypeScript errors
- [ ] ESLint checks pass
- [ ] New Password field visible in Account tab
- [ ] Password field has proper validation (min length, etc.)
- [ ] Password only sent to API when field is not empty
- [ ] Success feedback shown after password change
- [ ] Docker image rebuilt and tested by human
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

### Build & Deploy for Testing

```bash
# Rebuild frontend Docker image
cd ~/dantweb/vbwd-sdk/vbwd-frontend
make up-build

# Or rebuild just admin app
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npm run build
```

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`
- User: `test@example.com` / `TestPass123@`

---

## Tasks

### Task 2.1: E2E Tests - New Password Field

**Goal:** Write Playwright tests for new password field behavior

**Test Requirements:**
- [ ] New Password field is visible in Account tab
- [ ] Field is initially empty
- [ ] Field accepts input
- [ ] Form submits successfully with new password
- [ ] Form submits successfully without new password (optional field)
- [ ] Password validation error shown for too short passwords

**Test File:** `tests/e2e/admin-user-edit-password.spec.ts`

**Acceptance Criteria:**
- [ ] Tests written and initially failing (red phase)
- [ ] Tests cover password field scenarios
- [ ] Tests use proper data-testid selectors

---

### Task 2.2: Implementation - Password Field UI

**Goal:** Add new password field to Account tab

**Implementation Requirements:**
- [ ] Add password input field after Role select
- [ ] Label: "New Password"
- [ ] Placeholder: "Leave empty to keep current password"
- [ ] Input type: password
- [ ] Add data-testid="new-password-input"
- [ ] Add help text explaining the field is optional

**Files to Modify:**
- `src/views/UserEdit.vue` - Add password field to Account section

**Acceptance Criteria:**
- [ ] Field renders correctly in Account tab
- [ ] Field is visually consistent with other form fields

---

### Task 2.3: Implementation - Password Validation

**Goal:** Add client-side validation for password field

**Validation Rules:**
- [ ] Password is optional (empty is valid)
- [ ] If provided, minimum 8 characters
- [ ] Show validation error if too short

**Implementation Requirements:**
- [ ] Add password to form data
- [ ] Add validation in validateForm()
- [ ] Show validation error message

**Acceptance Criteria:**
- [ ] Empty password passes validation
- [ ] Short password shows error
- [ ] Valid password passes validation

---

### Task 2.4: Implementation - API Integration

**Goal:** Send new password to API when provided

**Implementation Requirements:**
- [ ] Include password in updateUser payload only if not empty
- [ ] Handle API response for password update
- [ ] Show success message after password change

**API Endpoint:**
- `PUT /api/v1/admin/users/{id}` - Should accept `password` field

**Files to Modify:**
- `src/views/UserEdit.vue` - Update handleSubmit
- `src/stores/users.ts` - Verify updateUser accepts password (if needed)

**Acceptance Criteria:**
- [ ] Password sent to API when provided
- [ ] Password NOT sent when field is empty
- [ ] Success feedback shown

---

### Task 2.5: Build & Human Testing

**Goal:** Rebuild Docker image and verify changes manually

**Requirements:**
- [ ] Run `npm run build` in admin app
- [ ] Rebuild Docker image with `make up-build`
- [ ] Verify password field renders correctly
- [ ] Test password change functionality
- [ ] Test form submission without password
- [ ] Verify validation errors display

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-frontend
make up-build
```

**Acceptance Criteria:**
- [ ] Password field visible and functional
- [ ] No console errors in browser
- [ ] Human tester approves implementation

---

## API Reference

### Update User Endpoint
```
PUT /api/v1/admin/users/{id}
Content-Type: application/json

{
  "is_active": true,
  "name": "John Doe",
  "password": "newpassword123"  // Optional - only include if changing
}
```

---

## Files to Modify

### Views
- `src/views/UserEdit.vue` - Add password field and validation

### Stores (if needed)
- `src/stores/users.ts` - Verify password support in updateUser

### Tests
- `tests/e2e/admin-user-edit-password.spec.ts` - New E2E test file

### Backend (required)
- `vbwd-backend/src/routes/admin/users.py` - Add password handling to update_user endpoint

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 2.1 E2E Tests - Password Field | ✅ Complete | 10 tests (added login verification test) |
| 2.2 Password Field UI | ✅ Complete | Added to Account section |
| 2.3 Password Validation | ✅ Complete | Min 8 chars if provided |
| 2.4 API Integration | ✅ Complete | Backend updated to handle password field |
| 2.5 Build & Human Testing | ⏳ Awaiting Human | Backend + Frontend Docker rebuilt |

---

## Sprint Completion Workflow

When all tasks are complete and Definition of Done is satisfied:

1. **Move sprint file to `/done`:**
   ```bash
   mv docs/devlog/20260109/todo/02-user-edit-new-password.md docs/devlog/20260109/done/
   ```

2. **Create completion report in `/reports`:**
   ```bash
   # Create: docs/devlog/20260109/reports/02-user-edit-new-password-report.md
   ```

3. **Update `status.md`:**
   - Change sprint status from ⏳ Pending to ✅ Complete
