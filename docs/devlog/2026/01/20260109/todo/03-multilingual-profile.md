# Sprint 03: Multilingual Platform + Admin Profile Page

**Date:** 2026-01-09
**Priority:** High
**Type:** Feature Implementation + E2E Testing
**Section:** Admin Platform Infrastructure

## Goal

Make the admin platform multilingual by extracting all translatable strings and implementing i18n support. Create a Profile page for admin users to manage their account settings including language preference.

## Clarified Requirements

Based on Q&A session:

| Aspect | Decision |
|--------|----------|
| **Languages** | English + German + Russian (3 languages) |
| **Profile link location** | User menu dropdown |
| **Theme switching** | No UI implementation, just store in config JSON |
| **Balance field** | Display only on Profile (read-only), edit via Users management |
| **Profile editability** | Fully editable (except email, role, balance) |
| **Address fields** | All fields shown on Profile page |
| **DB state** | user_details table EXISTS, need to ADD 4 new fields |

### Existing user_details Fields
- user_id, first_name, last_name
- address_line_1, address_line_2, city, postal_code, country, phone
- id, created_at, updated_at, version (from BaseModel)

### New Fields to Add
- `company` - VARCHAR(255)
- `tax_number` - VARCHAR(100)
- `config` - JSONB (language, theme preferences)
- `balance` - DECIMAL(10,2), default 0.00

## Core Requirements

### Methodology
- **TDD-First**: Write Playwright E2E tests BEFORE implementation
- **SOLID Principles**: Single responsibility, clean separation
- **Clean Code**: Self-documenting, consistent patterns
- **No Over-engineering**: Only build what's required
- **Code Reuse**: Leverage existing patterns

### Test Execution

```bash
# Full pre-commit check (recommended)
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --admin --unit --integration --e2e

# Admin E2E tests only
cd ~/dantweb/vbwd-sdk/vbwd-frontend/admin/vue
npx playwright test admin-profile

# Skip style checks
./bin/pre-commit-check.sh --admin --unit --integration --e2e --no-style
```

### Definition of Done
- [ ] All E2E tests passing
- [ ] No TypeScript errors
- [ ] ESLint checks pass
- [ ] Backend UserDetails model updated with new fields
- [ ] Database migration created and applied
- [ ] i18n infrastructure setup (vue-i18n)
- [ ] All hardcoded strings extracted to language files
- [ ] Profile page functional with all fields
- [ ] Language selector working
- [ ] DEFAULT_LANGUAGE env variable respected
- [ ] Docker images rebuilt and tested by human
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

### Build & Deploy for Testing

```bash
# Backend
cd ~/dantweb/vbwd-sdk/vbwd-backend
make up-build

# Frontend
cd ~/dantweb/vbwd-sdk/vbwd-frontend
make up-build
```

### Test Credentials
- Admin: `admin@example.com` / `AdminPass123@`
- User: `test@example.com` / `TestPass123@`

---

## Tasks

### Task 3.1: Backend - Update UserDetails Model

**Goal:** Add new fields to UserDetails model

**New Fields:**
- `company` - VARCHAR(255), nullable - User's company name
- `tax_number` - VARCHAR(100), nullable - Tax/VAT number
- `config` - JSON, nullable - User-specific configuration (language, theme, etc.)
- `balance` - DECIMAL(10,2), default 0.00 - User's account balance

**Files to Modify:**
- `vbwd-backend/src/models/user_details.py` - Add new columns
- `vbwd-backend/src/models/user_details.py` - Update `to_dict()` method

**Acceptance Criteria:**
- [ ] Model has all new fields
- [ ] to_dict() includes new fields
- [ ] Default values set correctly

---

### Task 3.2: Backend - Database Migration

**Goal:** Create and apply Alembic migration for new fields

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose exec api flask db migrate -m "Add company, tax_number, config, balance to user_details"
docker-compose exec api flask db upgrade
```

**Acceptance Criteria:**
- [ ] Migration file created
- [ ] Migration applies without errors
- [ ] Fields exist in database

---

### Task 3.3: Backend - Environment Configuration

**Goal:** Add DEFAULT_LANGUAGE to environment configuration

**Implementation:**
- Add `DEFAULT_LANGUAGE=en` to `.env.example`
- Add to config class
- Create endpoint to get default language

**Files to Modify:**
- `vbwd-backend/.env.example`
- `vbwd-backend/src/config.py`

**Acceptance Criteria:**
- [ ] DEFAULT_LANGUAGE in .env.example
- [ ] Config class reads the variable
- [ ] Default is 'en' if not set

---

### Task 3.4: Backend - Profile API Endpoints

**Goal:** Create/update API endpoints for admin profile

**Endpoints:**
- `GET /api/v1/admin/profile` - Get current admin's profile
- `PUT /api/v1/admin/profile` - Update current admin's profile
- `GET /api/v1/config/languages` - Get available languages and default

**Response Format (GET profile):**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin",
    "is_active": true,
    "details": {
      "first_name": "Admin",
      "last_name": "User",
      "company": "ACME Corp",
      "tax_number": "DE123456789",
      "phone": "+1234567890",
      "address_line_1": "123 Main St",
      "city": "Berlin",
      "postal_code": "10115",
      "country": "DE",
      "config": {
        "language": "en",
        "theme": "light"
      },
      "balance": 100.00
    }
  }
}
```

**Files to Create/Modify:**
- `vbwd-backend/src/routes/admin/profile.py` - New file
- `vbwd-backend/src/routes/admin/__init__.py` - Register blueprint
- `vbwd-backend/src/routes/config.py` - Languages endpoint

**Acceptance Criteria:**
- [ ] GET profile returns current user data
- [ ] PUT profile updates user details
- [ ] Languages endpoint returns available languages

---

### Task 3.5: E2E Tests - Profile Page

**Goal:** Write Playwright tests for Profile page

**Test Requirements:**
- [ ] Profile page is accessible from user menu
- [ ] Profile page displays user email (readonly)
- [ ] Profile page displays user name
- [ ] Profile page displays role (readonly)
- [ ] Profile page displays company field
- [ ] Profile page displays tax number field
- [ ] Profile page has language selector
- [ ] Profile page saves changes successfully
- [ ] Language change updates UI language

**Test File:** `tests/e2e/admin-profile.spec.ts`

**Acceptance Criteria:**
- [ ] Tests written and initially failing (red phase)
- [ ] Tests cover all profile scenarios
- [ ] Tests use proper data-testid selectors

---

### Task 3.6: Frontend - i18n Infrastructure Setup

**Goal:** Setup vue-i18n for internationalization

**Implementation:**
- Install vue-i18n
- Create i18n plugin configuration
- Create language files structure
- Initialize with DEFAULT_LANGUAGE from API

**File Structure:**
```
admin/vue/src/
├── i18n/
│   ├── index.ts          # i18n configuration
│   └── locales/
│       ├── en.json       # English translations
│       ├── de.json       # German translations
│       └── ru.json       # Russian translations
```

**Files to Create:**
- `src/i18n/index.ts`
- `src/i18n/locales/en.json`
- `src/i18n/locales/de.json`
- `src/i18n/locales/ru.json`

**Files to Modify:**
- `src/main.ts` - Register i18n plugin
- `package.json` - Add vue-i18n dependency

**Acceptance Criteria:**
- [ ] vue-i18n installed and configured
- [ ] Language files created
- [ ] i18n available in all components

---

### Task 3.7: Frontend - Extract Strings from Views

**Goal:** Replace all hardcoded strings with i18n keys

**Views to Update:**
- [ ] `Login.vue`
- [ ] `Dashboard.vue`
- [ ] `Users.vue`
- [ ] `UserDetails.vue`
- [ ] `UserEdit.vue`
- [ ] `UserCreate.vue`
- [ ] `Plans.vue`
- [ ] `PlanForm.vue`
- [ ] `Subscriptions.vue`
- [ ] `SubscriptionDetails.vue`
- [ ] `SubscriptionCreate.vue`
- [ ] `Invoices.vue`
- [ ] `InvoiceDetails.vue`
- [ ] `Webhooks.vue`
- [ ] `WebhookDetails.vue`
- [ ] `Analytics.vue`
- [ ] `Settings.vue`
- [ ] `Forbidden.vue`
- [ ] `App.vue` (navbar, user menu)

**Pattern:**
```vue
<!-- Before -->
<h1>Users</h1>
<button>Save Changes</button>

<!-- After -->
<h1>{{ $t('users.title') }}</h1>
<button>{{ $t('common.saveChanges') }}</button>
```

**Acceptance Criteria:**
- [ ] All user-visible strings extracted
- [ ] English translations complete
- [ ] German translations complete (basic)
- [ ] No hardcoded strings remain

---

### Task 3.8: Frontend - Profile Page Implementation

**Goal:** Create Profile page for admin users

**Page Components:**
- Email (readonly)
- Name (first_name, last_name) - editable
- Role (readonly badge)
- Company - editable
- Tax Number - editable
- Phone - editable
- Address fields (address_line_1, address_line_2, city, postal_code, country) - editable
- Balance (readonly, display only)
- Language selector dropdown - editable
- Save button

**Files to Create:**
- `src/views/Profile.vue`

**Files to Modify:**
- `src/router/index.ts` - Add profile route
- `src/App.vue` - Add profile link to user menu

**Acceptance Criteria:**
- [ ] Profile page renders correctly
- [ ] All fields display current values
- [ ] Language selector shows available languages
- [ ] Save button updates profile
- [ ] Success message shown after save

---

### Task 3.9: Frontend - Language Selector Integration

**Goal:** Make language selector functional

**Implementation:**
- Fetch available languages from API
- Store selected language in user config
- Update i18n locale on change
- Persist language preference

**Behavior:**
1. On app load: Check user's saved language preference
2. If no preference: Use DEFAULT_LANGUAGE from API
3. On language change: Update UI immediately + save to backend

**Files to Modify:**
- `src/views/Profile.vue` - Language selector
- `src/stores/auth.ts` - Store language preference
- `src/App.vue` - Initialize language on load

**Acceptance Criteria:**
- [ ] Language selector shows available options
- [ ] Changing language updates UI immediately
- [ ] Language preference persists after logout/login

---

### Task 3.10: Build & Human Testing

**Goal:** Rebuild Docker images and verify changes manually

**Requirements:**
- [ ] Run backend tests
- [ ] Run frontend tests
- [ ] Rebuild backend Docker image
- [ ] Rebuild frontend Docker image
- [ ] Verify Profile page works
- [ ] Verify language switching works
- [ ] Verify all pages display correctly in both languages
- [ ] No console errors in browser

**Commands:**
```bash
# Backend
cd ~/dantweb/vbwd-sdk/vbwd-backend
make test
make up-build

# Frontend
cd ~/dantweb/vbwd-sdk/vbwd-frontend
./bin/pre-commit-check.sh --admin --unit --integration
make up-build
```

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Profile page functional
- [ ] Language switching works
- [ ] Human tester approves implementation

---

## API Reference

### Get Admin Profile
```
GET /api/v1/admin/profile
Authorization: Bearer <token>

Response 200:
{
  "user": { ... }
}
```

### Update Admin Profile
```
PUT /api/v1/admin/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "company": "ACME Corp",
  "tax_number": "DE123456789",
  "phone": "+1234567890",
  "config": {
    "language": "de",
    "theme": "light"
  }
}

Response 200:
{
  "user": { ... },
  "message": "Profile updated"
}
```

### Get Available Languages
```
GET /api/v1/config/languages

Response 200:
{
  "languages": [
    { "code": "en", "name": "English" },
    { "code": "de", "name": "Deutsch" },
    { "code": "ru", "name": "Русский" }
  ],
  "default": "en"
}
```

---

## i18n Key Structure

```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "loading": "Loading...",
    "error": "Error",
    "success": "Success",
    "saveChanges": "Save Changes",
    "back": "Back",
    "search": "Search...",
    "noResults": "No results found",
    "actions": "Actions"
  },
  "nav": {
    "dashboard": "Dashboard",
    "users": "Users",
    "plans": "Plans",
    "subscriptions": "Subscriptions",
    "invoices": "Invoices",
    "webhooks": "Webhooks",
    "analytics": "Analytics",
    "settings": "Settings",
    "profile": "Profile",
    "logout": "Logout"
  },
  "auth": {
    "login": "Login",
    "email": "Email",
    "password": "Password",
    "loginButton": "Sign In",
    "invalidCredentials": "Invalid credentials"
  },
  "users": {
    "title": "Users",
    "createUser": "Create User",
    "editUser": "Edit User",
    "email": "Email",
    "name": "Name",
    "status": "Status",
    "role": "Role",
    "active": "Active",
    "inactive": "Inactive"
  },
  "profile": {
    "title": "Profile",
    "personalInfo": "Personal Information",
    "companyInfo": "Company Information",
    "preferences": "Preferences",
    "language": "Language",
    "company": "Company",
    "taxNumber": "Tax Number",
    "emailReadonly": "Email cannot be changed",
    "roleReadonly": "Role is managed by administrators"
  }
}
```

---

## Files Summary

### Backend - Create
- `src/routes/admin/profile.py`
- `src/routes/config.py`
- Migration file (auto-generated)

### Backend - Modify
- `src/models/user_details.py`
- `src/routes/admin/__init__.py`
- `src/config.py`
- `.env.example`

### Frontend - Create
- `src/i18n/index.ts`
- `src/i18n/locales/en.json`
- `src/i18n/locales/de.json`
- `src/i18n/locales/ru.json`
- `src/views/Profile.vue`
- `tests/e2e/admin-profile.spec.ts`

### Frontend - Modify
- `package.json`
- `src/main.ts`
- `src/router/index.ts`
- `src/App.vue`
- All view files (string extraction)

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 3.1 Backend - UserDetails Model | ⏳ Pending | |
| 3.2 Backend - Database Migration | ⏳ Pending | |
| 3.3 Backend - Environment Config | ⏳ Pending | |
| 3.4 Backend - Profile API | ⏳ Pending | |
| 3.5 E2E Tests - Profile Page | ⏳ Pending | |
| 3.6 Frontend - i18n Setup | ⏳ Pending | |
| 3.7 Frontend - Extract Strings | ⏳ Pending | |
| 3.8 Frontend - Profile Page | ⏳ Pending | |
| 3.9 Frontend - Language Selector | ⏳ Pending | |
| 3.10 Build & Human Testing | ⏳ Pending | |

---

## Sprint Completion Workflow

When all tasks are complete and Definition of Done is satisfied:

1. **Move sprint file to `/done`:**
   ```bash
   mv docs/devlog/20260109/todo/03-multilingual-profile.md docs/devlog/20260109/done/
   ```

2. **Create completion report in `/reports`:**
   ```bash
   # Create: docs/devlog/20260109/reports/03-multilingual-profile-report.md
   ```

3. **Update `status.md`:**
   - Change sprint status from ⏳ Pending to ✅ Complete
