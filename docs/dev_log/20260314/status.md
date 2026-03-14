# Sprint Status — 2026-03-14

## Sprints

| # | Sprint | Status | Report |
|---|--------|--------|--------|
| 01 | Code Quality — vbwd-backend | ✅ Done | `reports/02-backend-quality-sprint-report.md` |
| 02 | Code Quality — vbwd-fe-admin | ✅ Done | `reports/03-fe-admin-quality-sprint-report.md` |
| 03 | Code Quality — vbwd-fe-user | ✅ Done | `reports/04-fe-user-quality-sprint-report.md` |
| 04 | Billing Gaps — recurring billing & subscription lifecycle | ⏳ Pending approval | — |
| 05 | Email System — templates, SMTP, Mailchimp demo, Mailpit | ✅ Done | — |
| 06 | Fix "Get Package" button — wrong ID, no context, anonymous redirect | ⏳ Pending approval | `sprints/06-fix-get-package-button.md` |
| 07 | GHRM Breadcrumb Widgets — CMS-style widgets, 3-tab admin config (General/CSS/Preview) | ⏳ Pending approval | `sprints/07-ghrm-breadcrumb-widgets.md` |
| 08 | CMS Routing Rules — default page, language/IP/country routing, nginx hybrid, admin UI | ⏳ Pending approval | `sprints/08-cms-routing-rules.md` |
| — | GHRM Plugin v1 — production fix, partial sync, preview, markdown, plugin manager bug | ✅ Done | `reports/06-ghrm-plugin-completion-report.md` |
| — | Root Makefile — `make unit`, `make integration`, `make styles`, `make code-rebuild` | ✅ Done | — |

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

---

## Sprint 04 — Billing Gaps ⏳ PENDING APPROVAL

**Sprint doc:** `sprints/04-billing-gaps.md`

### Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Add `DAILY` billing period — enums, PERIOD_DAYS, Stripe + PayPal interval maps | ⏳ |
| 2 | YooKassa auto-renewal — charge saved payment method on renewal | ⏳ |
| 3 | YooKassa `payment.canceled` webhook handler — emit `PaymentFailedEvent` | ⏳ |
| 4 | Auto-invoke `expire_subscriptions()` + `expire_trials()` via APScheduler | ⏳ |
| 5 | Dunning email sequence — day 3 + day 7 follow-ups via `payment_failed_at` field | ⏳ |

---

## Sprint 05 — Email System ✅ DONE

**Completed:** 2026-03-14

### Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Backend `email` plugin — `EmailTemplate` model, `IEmailSender`/`EmailMessage` interface, `EmailSenderRegistry`, `SmtpEmailSender`, `EmailService` (Jinja2 rendering), `EVENT_CONTEXTS` (8 events), `seeds.py`, admin API routes (6 endpoints) | ✅ |
| 2 | Backend `mailchimp` plugin — `MandrillEmailSender` (Liskov-substitutable reference implementation) | ✅ |
| 3 | fe-admin `email-admin` plugin — `EmailTemplateList.vue`, `EmailTemplateEdit.vue` (3-tab HTML/Text/Preview), `useEmailStore.ts` | ✅ |
| 4 | fe-admin nav — "Messaging → Email Templates" group added via `extensionRegistry` | ✅ |
| 5 | Mailpit service in `docker-compose.yaml` (port 8025 UI / 1025 SMTP) | ✅ |
| 6 | Alembic migration `20260314_create_email_template_table.py` | ✅ |

### Tests
- 23 unit tests (registry, smtp sender, email service) — all ✅
- 28 integration tests (security, CRUD, preview, migration schema, edge cases) — all ✅
- fe-admin: `emailAdminPlugin.spec.ts` (pluginLoader contract, install/activate/deactivate), `EmailTemplateList.spec.ts`
- Full pre-commit: `--full` → **PASS** (1121 unit ✓, 82 integration ✓, lint ✓)
