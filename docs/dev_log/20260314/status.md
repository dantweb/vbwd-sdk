# Sprint Status — 2026-03-14

## Sprints

| # | Sprint | Status | Report |
|---|--------|--------|--------|
| 01 | Code Quality — vbwd-backend | ✅ Done | `reports/02-backend-quality-sprint-report.md` |
| 02 | Code Quality — vbwd-fe-admin | ✅ Done | `reports/03-fe-admin-quality-sprint-report.md` |
| 03 | Code Quality — vbwd-fe-user | ✅ Done | `reports/04-fe-user-quality-sprint-report.md` |

---

## Sprint 01 — vbwd-backend ✅ DONE

**Completed:** 2026-03-14

### Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Fix `datetime.utcnow()` (30 files) — `src/utils/datetime_utils.py` utcnow() helper | ✅ |
| 2 | Extract UUID validation utility — `src/utils/validation.py`, applied to subscriptions.py | ✅ |
| 3 | Fix bare `except: pass` in GHRM sync — now logs WARNING | ✅ |
| 4 | Hash sync API keys | ⏭ Deferred (requires DB migration) |
| 5 | Consolidate dead `archive_plan` code — delegates to `deactivate_plan` | ✅ |
| 6 | Fix `UserTokenBalance.query` → `db.session.query(...)` in admin/users.py | ✅ |
| 7 | Fix `import re` inside function bodies in admin/plans.py | ✅ |
| 8 | Enforce service factory pattern | ✅ Already correct in all plugins |
| 9 | Add README.md to cms, stripe, yookassa, paypal, chat plugins | ✅ |

### Pre-commit
- [x] `./bin/pre-commit-check.sh --lint` → PASS (Black ✓ Flake8 ✓ Mypy ✓)
- [x] `./bin/pre-commit-check.sh --quick` → PASS (1086 unit tests)
- [ ] `./bin/pre-commit-check.sh` (full — integration test has pre-existing UniqueViolation in ghrm test data)

---

## Sprint 02 — vbwd-fe-admin ✅ DONE

**Completed:** 2026-03-14

### Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Type the API client — eliminate `(api as any).method(...)` (39 occurrences) | ✅ |
| 2 | Fix `as any` translation casts in CMS admin plugin (8 occurrences) | ✅ |
| 3 | Remove `console.log` + add `no-console` ESLint rule | ✅ |
| 4 | Centralize API error handling | ⏭ Deferred (no Axios interceptor wiring) |
| 5 | Add README.md to all admin plugins | ✅ |
| — | Pre-existing: Fix `RequestInit` type error in `GhrmSoftwareTab.vue` | ✅ |

### Pre-commit
- [x] `./bin/pre-commit-check.sh --style` → PASS (ESLint ✓ TypeScript ✓)
- [x] `./bin/pre-commit-check.sh --unit --integration` → PASS

---

## Sprint 03 — vbwd-fe-user ✅ DONE

**Completed:** 2026-03-14

### Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Type the CMS API client — eliminate `(api as any).get(...)` (5 occurrences) | ✅ |
| 2 | Extract `registerPluginTranslations` utility | ⏭ Not applicable — sdk.addTranslations() already consistent |
| 3 | Standardize `_active` plugin flag pattern | ⏭ Deferred — passes type check; object-literal TS limitation |
| 4 | Remove `console.log` + add `no-console` ESLint rule | ✅ |
| 5 | Centralize API error handling (incl. 402 → /plans) | ⏭ Deferred (no Axios interceptor setup) |
| 6 | Add README.md to all user plugins (9 plugins) | ✅ |
| — | Pre-existing: Fix `responseType` TS error in `useCmsStore.ts` | ✅ |
| — | Pre-existing: Install `express-rate-limit` (failing unit test) | ✅ |

### Pre-commit
- [x] `./bin/pre-commit-check.sh --style` → PASS (ESLint ✓ TypeScript ✓)
- [x] `./bin/pre-commit-check.sh --unit --integration` → PASS (283 unit tests ✓)
