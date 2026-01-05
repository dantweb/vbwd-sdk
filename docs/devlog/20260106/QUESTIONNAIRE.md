# Architect & Developer Questionnaire

**Purpose:** Provide context for Claude Code to continue development effectively
**Date:** 2026-01-06
**Fill out and save this file, then ask Claude to read it**

---

## Section 1: Current Blocker - E2E Tests

### 1.1 Page Loading Behavior

When you visit `http://localhost:8081/admin/users` in a browser (after logging in):

**Does the page load correctly?**
- [ ] Yes, I see the Users list and "Create User" button
- [ ] No, I see an error message: `_______________`
- [ ] No, the page is blank/loading forever
- [ ] Other: `_______________`

**Are there console errors? (Open DevTools → Console)**
```
Paste any errors here:

```

**What do API requests show? (DevTools → Network → filter by "api")**
```
List failed requests (status 4xx/5xx):

```

### 1.2 Feature Implementation Status

Fill in the table with: ✅ Done | 🚧 Partial | ❌ Not Started | 🚫 Not Planned

| Feature | Users | Subscriptions | Invoices | Plans |
|---------|-------|---------------|----------|-------|
| List View | | | | |
| Detail View | | | | |
| Create (UI) | | | | |
| Edit (UI) | | | | |
| Delete (UI) | | | | |
| Search/Filter | | | | |

### 1.3 Subscription & Invoice Flow

**How should subscriptions be created?**
- [ ] Admin creates manually via UI form
- [ ] Auto-created when user selects a plan
- [ ] API-only (no UI needed)
- [ ] Other: `_______________`

**How should invoices be generated?**
- [ ] Auto-generated when subscription is created
- [ ] Auto-generated on billing cycle
- [ ] Admin creates manually
- [ ] Other: `_______________`

---

## Section 2: Testing Strategy

### 2.1 Test Data Approach

**How should E2E tests get test data?**
- [ ] **UI-First**: Tests create all data through UI forms
- [ ] **API Seeding**: Tests call API to create data, then verify UI
- [ ] **Database Seeding**: Run SQL/fixtures before tests
- [ ] **Hybrid**: `_______________`

### 2.2 Test Independence

**Should each test be independent?**
- [ ] Yes - each test sets up and tears down its own data
- [ ] No - tests can depend on each other (flow testing)
- [ ] Mix - some independent, some flows

### 2.3 Selector Convention

**What selector strategy should tests use?**
- [ ] `data-testid` attributes (explicit, test-specific)
- [ ] CSS classes (`.users-view`, `.create-btn`)
- [ ] Semantic HTML/ARIA (`role="button"`, `aria-label`)
- [ ] Text content (`button:has-text("Create")`)
- [ ] Mix: `_______________`

**Should I add `data-testid` to all interactive elements?**
- [ ] Yes
- [ ] No, use existing selectors
- [ ] Only for elements that are hard to select otherwise

---

## Section 3: Architecture & Future Plans

### 3.1 Admin Panel Scope

**What is the MVP for "admin ready"?**
```
List the must-have features:
1.
2.
3.
4.
5.
```

**What can wait for later?**
```
List nice-to-have features:
1.
2.
3.
```

### 3.2 Shared Component Library (@vbwd/view-component)

**What should be added to the shared library?**
- [ ] Form components (inputs, selects, validation)
- [ ] Data table component
- [ ] Modal/dialog system
- [ ] Toast/notification system
- [ ] Loading states/skeletons
- [ ] Other: `_______________`

### 3.3 Plugin Architecture

**Will admin migrate to plugin architecture?**
- [ ] Yes, planned for: `_______________`
- [ ] No, flat structure is intentional
- [ ] Maybe later, not a priority

---

## Section 4: Immediate Priorities

### 4.1 Top 3 Priorities

**If you could only fix/implement 3 things, what would they be?**

1. **Priority 1:** `_______________`
   - Why:

2. **Priority 2:** `_______________`
   - Why:

3. **Priority 3:** `_______________`
   - Why:

### 4.2 Known Issues

**Are there any bugs or issues I should know about?**
```
List known issues:
1.
2.
3.
```

### 4.3 Blocked Items

**Is anything blocked on external factors?**
```
List blockers:
1.
2.
```

---

## Section 5: Code Style & Conventions

### 5.1 Error Handling

**How should pages handle API errors?**
- [ ] Show inline error message
- [ ] Show toast notification
- [ ] Redirect to error page
- [ ] Retry automatically
- [ ] Other: `_______________`

### 5.2 Loading States

**How should pages show loading?**
- [ ] Spinner overlay
- [ ] Skeleton loaders
- [ ] Simple "Loading..." text
- [ ] Progress bar
- [ ] Other: `_______________`

### 5.3 Form Validation

**When should forms validate?**
- [ ] On submit only
- [ ] On blur (when leaving field)
- [ ] On change (as user types)
- [ ] Mix: `_______________`

---

## Section 6: Quick Answers

**Backend API base URL:** `http://localhost:____`

**Admin credentials for testing:**
- Email: `_______________`
- Password: `_______________`

**Is demo data installed?**
- [ ] Yes
- [ ] No (need to run: `_______________`)

**Docker services status:**
- [ ] All running
- [ ] Some down: `_______________`

---

## Section 7: Free-Form Notes

**Anything else I should know?**
```
Write any additional context, constraints, or guidance here:




```

---

## How to Use This Questionnaire

1. Fill out the sections above
2. Save this file
3. Tell Claude: "Read the questionnaire at `/docs/devlog/20260106/QUESTIONNAIRE.md` and continue with Sprint 08"
4. Claude will use your answers to:
   - Update test selectors and strategies
   - Prioritize fixes
   - Implement missing features
   - Align with your architectural vision

---

*Created: 2026-01-05*
*For session: 2026-01-06*
