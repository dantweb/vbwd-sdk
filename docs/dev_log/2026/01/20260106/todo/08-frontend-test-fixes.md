# Sprint 08: Frontend E2E Test Fixes - Continued

**Date:** 2026-01-06
**Carried from:** 2026-01-05
**Priority:** High
**Type:** Test Infrastructure + Architecture Discovery

---

## Current State Summary

### What's Working
- Vue app mounts correctly (fixed Pinia dedupe issue in vite.config.js)
- Login flow works in E2E tests
- Navigation tests pass (Step 1, Step 4)
- Unit tests: 188 passing (auth.spec.ts fixed)
- TypeScript: No errors

### What's Failing
- E2E: 5/8 tests failing
- Core issue: Pages appear to not fully load or have errors during test execution

---

## Questions for the Architect

### Part 1: Architecture & Design Intent

**Q1. Admin Page Loading Pattern**
The E2E tests navigate to `/admin/users` successfully (Step 1 passes), but when trying to interact with page elements in Step 2, the `.users-view` selector times out.

- What is the intended loading sequence for admin pages?
- Are there multiple async data fetches that must complete before the page is interactive?
- Is there a loading state management pattern (e.g., skeleton loaders, suspense boundaries)?

**Q2. Error Handling Philosophy**
When the Users page fails to display the "Create User" button:

- What should happen when the `/admin/users` API call fails?
- Does the page show an error state? If so, what CSS classes or elements indicate this?
- Is there a retry mechanism or should errors be permanent until page refresh?

**Q3. Authentication Flow**
The `beforeEach` hook logs in successfully, but subsequent page loads may behave differently:

- Does the admin app use token refresh? If so, what triggers it?
- Are there any race conditions between auth state initialization and page data fetching?
- How does the app handle expired tokens mid-session?

---

### Part 2: Feature Implementation Status

**Q4. CRUD Operations**
For each admin entity (Users, Subscriptions, Invoices):

| Entity | List View | Create | Read | Update | Delete |
|--------|-----------|--------|------|--------|--------|
| Users | ? | ? | ? | ? | ? |
| Subscriptions | ? | ? | ? | ? | ? |
| Invoices | ? | ? | ? | ? | ? |

Please fill in with: Implemented / Planned / Not Planned

**Q5. Subscription Creation**
The test expects a "Create Subscription" button on `/admin/subscriptions`:

- Is this feature implemented in the UI?
- If not, what is the intended workflow for creating subscriptions?
- Should subscriptions only be created automatically (e.g., on payment)?

**Q6. Invoice Generation**
The test flow expects invoices to be auto-generated when subscriptions are created:

- Is this the intended behavior?
- What triggers invoice creation in the current architecture?
- Are there manual invoice creation capabilities planned?

---

### Part 3: Testing Strategy

**Q7. E2E Test Data Philosophy**
Currently, E2E tests try to create users through the UI form. Alternative approaches:

1. **UI-First**: Tests create all data through UI (current approach)
2. **API Seeding**: Tests seed data via API, then verify UI displays it
3. **Database Seeding**: Tests run against pre-seeded database
4. **Hybrid**: Mix of approaches depending on what's being tested

Which approach aligns with your vision for this project? Why?

**Q8. Test Isolation vs Integration**
The current tests run as a sequential "flow" where Step 3 depends on Step 2:

- Should tests be independent (each test sets up its own data)?
- Or is the "flow" pattern intentional to test real user journeys?
- How should we handle test data cleanup?

**Q9. Element Selection Strategy**
Tests currently use mixed selectors:
- `data-testid` attributes (explicit)
- CSS classes (`.users-view`)
- Text content (`button:has-text("Create")`)

What is your preferred selector strategy? Should we:
- Add `data-testid` to all interactive elements?
- Rely on semantic HTML and ARIA attributes?
- Use CSS classes with a naming convention?

---

### Part 4: Future Architecture

**Q10. Plugin Architecture Revival**
The admin app uses a flat structure, but the core library has plugin infrastructure:

- Is there intent to migrate admin to plugin architecture?
- What would be the trigger for this migration?
- How would this affect the testing strategy?

**Q11. Shared Component Library**
The `@vbwd/view-component` library currently provides:
- API client
- Auth store
- Event bus
- Basic UI components

What additional shared functionality is planned?
- Form components with validation?
- Data tables with sorting/filtering?
- Modal/dialog system?

**Q12. Multi-Tenant Considerations**
Looking at the User and Subscription models:

- Is multi-tenancy planned for CE (Community Edition)?
- How would this affect the admin UI?
- Should tests account for tenant isolation?

---

### Part 5: Immediate Technical Questions

**Q13. Backend API Verification**
Can you verify these endpoints are working?
```bash
# Health check
curl http://localhost:5000/api/v1/health

# Admin users list
curl -H "Authorization: Bearer <admin_token>" http://localhost:5000/api/v1/admin/users

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"AdminPass123@"}'
```

**Q14. Browser Console Errors**
When you open `http://localhost:8081/admin/users` in a browser (after logging in):
- Are there any console errors?
- What does the Network tab show for API requests?
- Does the "Create User" button appear?

**Q15. Docker Container Health**
```bash
# Are all services healthy?
docker-compose -f vbwd-backend/docker-compose.yml ps
docker-compose -f vbwd-frontend/docker-compose.yml ps

# Any errors in logs?
docker-compose -f vbwd-backend/docker-compose.yml logs api --tail=50
```

---

## Your Formulations Requested

Please provide your thoughts on:

1. **Test Philosophy Statement**: In 2-3 sentences, describe what you believe good E2E tests should accomplish for this project.

2. **Definition of "Admin Ready"**: What criteria would mark the admin panel as "ready for production"?

3. **Priority Stack**: If you could only fix 3 things tomorrow, what would they be and why?

---

## Technical Fixes Already Applied (2026-01-05)

1. **Pinia Dedupe** - Added to vite.config.js:
```javascript
resolve: {
  dedupe: ['vue', 'pinia', 'vue-router']
}
```

2. **Auth Store Tests** - Rewrote with local store definition to avoid cross-package Pinia issues

3. **E2E TypeScript** - Fixed unused variables and RegExp type errors

4. **E2E Selectors** - Improved specificity for page header assertions

---

## Files Modified Today

| File | Changes |
|------|---------|
| `vite.config.js` | Added dedupe and optimizeDeps |
| `tests/unit/stores/auth.spec.ts` | Rewrote with local store mock |
| `tests/e2e/admin-user-subscription-flow.spec.ts` | Fixed selectors, waits, types |

---

## Next Steps (Pending Architect Input)

- [ ] Review architect answers to questions above
- [ ] Implement agreed-upon test data strategy
- [ ] Add missing `data-testid` attributes if decided
- [ ] Verify backend API health
- [ ] Complete remaining E2E test fixes

---

*Created: 2026-01-05*
*Continued: 2026-01-06*
