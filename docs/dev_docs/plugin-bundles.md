# Plugin Bundles

A **plugin bundle** is the complete cross-stack implementation of a single feature. It consists of coordinated plugins for the backend API, the admin frontend, and the user-facing frontend — all working together to deliver one cohesive capability.

This document explains the bundle concept, how the pieces connect, and walks through every current bundle as a reference.

---

## Table of Contents

1. [What is a Plugin Bundle?](#1-what-is-a-plugin-bundle)
2. [Bundle Structure](#2-bundle-structure)
3. [How the Pieces Connect](#3-how-the-pieces-connect)
4. [Bundle Registry — Current Plugins](#4-bundle-registry--current-plugins)
5. [Bundle: CMS](#5-bundle-cms)
6. [Bundle: GHRM (GitHub Repo Manager)](#6-bundle-ghrm)
7. [Bundle: Taro (AI Tarot)](#7-bundle-taro)
8. [Bundle: Stripe Payments](#8-bundle-stripe-payments)
9. [Building a New Bundle](#9-building-a-new-bundle)
10. [Bundle Checklist](#10-bundle-checklist)

---

## 1. What is a Plugin Bundle?

A single feature — for example, a content management system — spans all three tiers of the platform:

```
┌─────────────────────────────────────────────────────────────┐
│                     Feature: CMS                            │
│                                                             │
│  vbwd-backend        vbwd-fe-admin       vbwd-fe-user       │
│  plugins/cms/        plugins/cms-admin/  plugins/cms/       │
│                                                             │
│  • DB models         • Page editor       • Page viewer      │
│  • REST API          • Image gallery     • Category index   │
│  • File storage      • Layout builder    • Slug routing     │
│  • Migrations        • Widget editor     • i18n support     │
└─────────────────────────────────────────────────────────────┘
```

All three parts are required for the feature to work end-to-end. Together they form a **bundle**.

The name convention is:
- Backend plugin: `<feature>` (e.g., `cms`)
- Admin plugin: `<feature>-admin` (e.g., `cms-admin`)
- User plugin: `<feature>` (e.g., `cms`) — same name as backend, different repo

---

## 2. Bundle Structure

A full bundle occupies these locations across the repos:

```
vbwd-backend/
└── plugins/<feature>/              # Backend plugin
    ├── __init__.py                 # Plugin class
    ├── src/
    │   ├── models/                 # DB schema
    │   ├── repositories/           # Data access
    │   ├── services/               # Business logic
    │   └── routes.py               # REST API endpoints
    ├── migrations/versions/        # DB migrations
    └── bin/populate_<feature>.py   # Idempotent seed script

vbwd-fe-admin/
└── plugins/<feature>-admin/        # Admin frontend plugin
    ├── index.ts                    # Plugin definition (install, nav sections)
    └── src/
        ├── views/                  # Admin pages
        └── components/             # Admin-specific components

vbwd-fe-user/
└── plugins/<feature>/              # User frontend plugin
    ├── index.ts                    # Plugin definition
    ├── locales/                    # i18n strings per locale
    └── src/
        ├── views/                  # User-facing pages
        ├── components/             # User-facing components
        ├── stores/                 # Pinia state
        └── api/                    # API calls to backend
```

---

## 3. How the Pieces Connect

### API Contract

The backend plugin exposes REST endpoints. Both admin and user frontend plugins call these endpoints directly via `fetch` or the core `ApiClient`.

```
vbwd-fe-user                         vbwd-backend
plugins/ghrm/src/api/ghrmApi.ts  →  plugins/ghrm/src/routes.py
GET /api/v1/ghrm/packages            @ghrm_bp.route("/api/v1/ghrm/packages")

vbwd-fe-admin                        vbwd-backend
plugins/ghrm-admin/GhrmTab.vue   →  plugins/ghrm/src/routes.py
GET /api/v1/admin/ghrm/packages      @ghrm_bp.route("/api/v1/admin/ghrm/packages")
```

Admin endpoints are under `/api/v1/admin/` and protected by `@require_auth` + `@require_admin`. Public/user endpoints are under `/api/v1/<feature>/`.

### Plan & Category Link

The backend plugin creates `TarifPlan` records and assigns them to `TarifPlanCategory` records. The admin app exposes these plans in the plan management UI automatically (no extra code needed — the core admin plan UI reads all plans from the DB).

The user frontend navigates to plans by category slug. The GHRM plugin, for example, adds software packages linked to plans; the category slug becomes the URL segment (`/category/backend`).

### CMS Integration

Features that need public-facing pages register CMS pages, layouts, and widgets in their populate script. The CMS plugin (which must be enabled first) renders these pages at their slugs. This means **any plugin can have a public page without touching the frontend router** — it just needs a CMS page with the right layout.

```python
# In populate_ghrm.py:
# Creates CmsPage(slug="category/backend", layout_id=catalogue_layout.id)
# → renders at http://localhost:8080/category/backend
# → CMS picks up GhrmCatalogueContent Vue widget from the layout
```

### Subscription Events

When a user subscribes to a plan managed by a bundle, the backend plugin receives lifecycle events and acts accordingly (grant GitHub access, credit tokens, enable AI features, etc.).

---

## 4. Bundle Registry — Current Plugins

| Bundle | Backend | Admin Plugin | User Plugin | Status |
|---|---|---|---|---|
| CMS | `plugins/cms` | `plugins/cms-admin` | `plugins/cms` | ✅ Complete |
| GHRM | `plugins/ghrm` | `plugins/ghrm-admin` | `plugins/ghrm` | ✅ Complete |
| Taro | `plugins/taro` | `plugins/taro-admin` | `plugins/taro` | ✅ Complete |
| Stripe | `plugins/stripe` | (core admin UI) | `plugins/stripe-payment` | ✅ Complete |
| PayPal | `plugins/paypal` | (core admin UI) | `plugins/paypal-payment` | ✅ Complete |
| YooKassa | `plugins/yookassa` | (core admin UI) | `plugins/yookassa-payment` | ✅ Complete |
| Analytics | `plugins/analytics` | `plugins/analytics-widget` | — | 🔄 Partial |
| Chat | `plugins/chat` | — | `plugins/chat` | 🔄 Partial |

---

## 5. Bundle: CMS

The CMS bundle provides content management: pages, categories, images, layouts, and widgets.

### Backend: `plugins/cms`

**Purpose:** Store and serve structured content.

**Models:**
- `CmsPage` — a published page with a slug, title, rich content JSON, layout, and SEO metadata
- `CmsCategory` — groups pages by topic
- `CmsImage` — uploaded images with file storage abstraction
- `CmsLayout` — named layout templates with `areas` (header, body, footer, etc.)
- `CmsWidget` — reusable content units of type `vue-component`, `html`, or `markdown`
- `CmsLayoutWidget` — assigns a widget to a layout area at a given sort order
- `CmsStyle` — optional CSS overrides per layout

**Public API** (`/api/v1/cms/`):
- `GET /categories` — list all categories
- `GET /pages` — list published pages (filterable by category, language)
- `GET /pages/<slug>` — get page by slug (returns layout + widget config)
- `GET /images` — list images

**Admin API** (`/api/v1/admin/cms/`):
- Full CRUD for all models
- Image upload with Pillow resizing
- Layout + widget assignment editor

**Configuration:**
```json
{
  "uploads_base_path": "/app/uploads",
  "uploads_base_url": "/uploads",
  "allowed_mime_types": ["image/jpeg", "image/png", "image/webp", "image/gif"],
  "max_file_size_bytes": 10485760
}
```

### Admin Plugin: `plugins/cms-admin`

**Routes registered:**
- `/admin/cms/pages` — page list with filters
- `/admin/cms/pages/new` — rich-text editor (TipTap)
- `/admin/cms/pages/:id/edit` — edit existing page
- `/admin/cms/categories` — category manager
- `/admin/cms/images` — image gallery with upload
- `/admin/cms/layouts` — layout editor (define areas)
- `/admin/cms/widgets` — widget editor
- `/admin/cms/styles` — CSS style editor

**Nav section registered:**
```typescript
{ id: 'cms', label: 'CMS', items: [Pages, Categories, Images, Layouts, Widgets, Styles] }
```

**Translations:** en, ru, de, es, fr, ja, zh, th

### User Plugin: `plugins/cms`

**Route registered:**
- `/:slug(.+)` — dynamic route catches all paths not matched by other plugins; fetches CMS page data and renders it

**How it works:**
1. Vue Router matches `/:slug(.+)` with the URL path (e.g., `/about` or `/category/backend`)
2. `CmsPage.vue` calls `GET /api/v1/cms/pages/<slug>`
3. Backend returns page data including the `layout` object with its `areas` and `widgets`
4. `CmsLayoutRenderer.vue` renders each widget in its area
5. Widgets of type `vue-component` are rendered as dynamic Vue components — plugins register their components with the SDK so the CMS can instantiate them by name

**CMS Widget → Vue Component mapping:**
```typescript
// In ghrmPlugin.install(sdk):
sdk.addComponent('GhrmCatalogueContent', () => import('./src/views/GhrmCatalogueContent.vue'));
sdk.addComponent('GhrmPackageDetail',    () => import('./src/views/GhrmPackageDetail.vue'));
```

The widget record in the DB contains `content_json: { component: "GhrmCatalogueContent" }`. The CMS layout renderer looks up this name in the SDK component registry and renders it.

### Seed Script

```bash
docker compose exec api python plugins/cms/src/bin/populate_cms.py
```

Creates: default layouts (with header-nav, footer-nav widgets), category "ghrm", style entries.

---

## 6. Bundle: GHRM

The GHRM (GitHub Repo Manager) bundle provides subscription-gated software distribution via GitHub Releases.

### Backend: `plugins/ghrm`

**Purpose:** Manage a catalogue of software packages, each tied to a `TarifPlan`. Subscribers get a deploy token and a GitHub collaborator invite to the protected branch.

**Models:**
- `GhrmSoftwarePackage` — software package metadata (name, slug, GitHub owner/repo, description, sort_order, sync_api_key)
- `GhrmSoftwareSync` — cached GitHub data (readme, changelog, docs, releases, screenshots) and admin overrides
- `GhrmUserGithubAccess` — links a user to their GitHub account and tracks which packages they have access to
- `GhrmAccessLog` — audit log of grant/revoke actions

**Public API** (`/api/v1/ghrm/`):
- `GET /categories` — list categories (from `TarifPlanCategory` where GHRM plans are assigned)
- `GET /packages` — paginated package list (filterable by category, query)
- `GET /packages/<slug>` — package detail (merged cached + override content)
- `GET /packages/<slug>/related` — related packages
- `GET /packages/<slug>/versions` — release list
- `GET /packages/<slug>/install` — install instructions (requires active subscription + GitHub connection) `@require_auth`
- `GET /access` — current user's GitHub access status `@require_auth`
- `GET /auth/github` — get GitHub OAuth URL `@require_auth`
- `POST /auth/github/callback` — exchange OAuth code for access `@require_auth`
- `DELETE /auth/github` — disconnect GitHub account `@require_auth`
- `GET|POST /sync` — GitHub Actions sync trigger (API key auth, no JWT)

**Admin API** (`/api/v1/admin/ghrm/`):
- Full CRUD for packages
- `POST /packages/<id>/sync` — trigger GitHub sync
- `POST /packages/<id>/rotate-key` — regenerate sync API key
- `POST /access/sync/<user_id>` — manual access sync for a user

**GitHub Sync flow:**
1. GitHub Actions sends `POST /api/v1/ghrm/sync?package=<slug>&key=<sync_api_key>`
2. Backend fetches README, CHANGELOG, docs from GitHub API
3. Fetches releases (tags, assets)
4. Stores in `GhrmSoftwareSync.cached_*` fields
5. If `override_readme` is set by admin, it takes precedence over cached

**Subscription event hooks:**
- `subscription.activated` → grant GitHub collaborator access
- `subscription.cancelled` → start grace period (configurable days)
- `subscription.expired` / `subscription.payment_failed` → revoke access after grace period

**Configuration:**
```json
{
  "github_app_id": "",
  "github_private_key_path": "",
  "github_installation_id": "",
  "oauth_client_id": "",
  "oauth_client_secret": "",
  "oauth_redirect_uri": "http://localhost:8080/ghrm/auth/github/callback",
  "software_category_slugs": ["backend", "fe-admin", "fe-user", "payments"],
  "grace_period_days": 3
}
```

### Admin Plugin: `plugins/ghrm-admin`

Each plan in the admin has a "Software" tab rendered by `GhrmSoftwareTab.vue`.

**Capabilities:**
- Create / update a `GhrmSoftwarePackage` linked to the current plan
- Edit name, description, GitHub owner/repo, author, icon URL
- View and copy the sync API key
- Rotate (regenerate) the sync API key
- Trigger a manual GitHub sync
- See last-synced timestamp

**API calls made:**
- `GET /api/v1/admin/ghrm/packages?tariff_plan_id=<id>`
- `POST /api/v1/admin/ghrm/packages`
- `PUT /api/v1/admin/ghrm/packages/<id>`
- `POST /api/v1/admin/ghrm/packages/<id>/rotate-key`
- `POST /api/v1/admin/ghrm/packages/<id>/sync`

### User Plugin: `plugins/ghrm`

**Routes registered:**
- `/category` → `GhrmCatalogueContent.vue` (all packages, all categories)
- `/category/:category_slug` → `GhrmCatalogueContent.vue` (filtered)
- `/category/:category_slug/:package_slug` → `GhrmPackageDetail.vue`
- `/category/search` → `GhrmSearch.vue`
- `/ghrm/auth/github/callback` → `GhrmOAuthCallback.vue` (handles OAuth return)

All CMS pages for these routes are created by the populate script, which links them to the appropriate layout + widget. The route is matched by the CMS `/:slug(.+)` catch-all route first, which renders the correct widget.

**Package detail tabs:**
- Overview — `readme` (override or cached)
- Screenshots — `screenshots` (admin-uploaded + cached)
- Changelog — `changelog` (override or cached)
- Documentation — `docs` (override or cached)
- Versions — `cached_releases` (tag, date, release notes, assets)
- Install — install instructions if user has active subscription + GitHub connected

**Auth-aware behaviour:**
- Unauthenticated users see the catalogue and package details freely
- The "Install" tab shows a "Log In" prompt for unauthenticated users
- `GET /api/v1/ghrm/access` is only called when the user is authenticated

### Seed Script

```bash
docker compose exec api python plugins/ghrm/src/bin/populate_ghrm.py
```

Creates: software packages for all vbwd plugins and dantweb open-source repos, CMS layouts, widgets, category pages, and demo readme content.

---

## 7. Bundle: Taro

The Taro bundle provides AI-powered Tarot readings with token-based consumption.

### Backend: `plugins/taro`

**Purpose:** Let users draw Tarot cards and receive AI interpretations, with daily session limits enforced per subscription plan and token costs charged per reading.

**Models:**
- `Arcana` — the 78 Tarot cards with meanings (seeded from CSV)
- `TaroSession` — a reading session (3 drawn cards, AI interpretation, expiry)
- `TaroCardDraw` — one card in a session (position, orientation, AI text)

**Key service logic:**
- `TaroSessionService.create_session()` — checks daily limit from plan features, draws 3 random cards, deducts tokens
- `ArcanaInterpretationService.interpret()` — calls the configured LLM API with card + spread context
- Sessions expire after 30 minutes; expired sessions count toward daily limit

**Token costs (configurable):**
- New session: 10 tokens
- Follow-up question: 5 tokens

**Plan features consumed:**
```json
{
  "daily_taro_limit": 3,
  "max_taro_follow_ups": 3
}
```

**User API** (`/api/v1/taro/`):
- `POST /sessions` — start a new reading (deducts tokens)
- `GET /sessions` — list user's sessions
- `GET /sessions/<id>` — get session with card interpretations
- `POST /sessions/<id>/follow-up` — ask follow-up question (deducts tokens)
- `GET /limits` — daily limit status
- `GET /assets/card/<number>` — serve card SVG image

**Admin API** (`/api/v1/admin/taro/`):
- `GET /sessions` — all sessions (paginated)
- `GET /users/<id>/sessions` — user sessions
- `POST /users/<id>/reset-limits` — reset daily count

### Admin Plugin: `plugins/taro-admin`

- Session browser with user, date, spread filters
- Per-user quota override
- Reading history viewer
- Analytics: sessions per day, tokens consumed

### User Plugin: `plugins/taro`

- Animated card flip UI
- 3-card spread (Past / Present / Future)
- Display AI interpretation per card
- Follow-up question input
- Session history list

### Seed Script

```bash
docker compose exec api python plugins/taro/src/bin/populate_taro.py
```

Creates: all 78 Arcana records from CSV. The Taro plugin does not create plans — plans are managed in `install_demo_data.py` or manually in the admin.

---

## 8. Bundle: Stripe Payments

The Stripe bundle wires Stripe Checkout Sessions into the platform's subscription and invoice flow.

### Backend: `plugins/stripe`

**Purpose:** Provide Stripe as a payment provider.

**Flow:**
1. User visits checkout → `POST /api/v1/subscriptions` with `payment_method: "stripe"`
2. `StripePlugin` creates a Stripe Checkout Session and returns the URL
3. User completes payment on Stripe's hosted page
4. Stripe sends `checkout.session.completed` webhook to `POST /api/v1/webhooks/stripe`
5. Backend activates subscription, generates invoice, dispatches `subscription.activated`

**Configuration:**
```json
{
  "secret_key": "",
  "webhook_secret": "",
  "publishable_key": "",
  "sandbox_mode": true,
  "supported_currencies": ["EUR", "USD"],
  "payment_methods": ["card", "sepa_debit", "ideal"]
}
```

### Admin Plugin

Stripe configuration is managed through the core admin Settings → Payment Methods UI. No separate admin plugin is needed.

### User Plugin: `plugins/stripe-payment`

Renders the Stripe redirect / embedded checkout form in the `CheckoutPlugin` flow. When `checkout_plugin` detects the active payment provider is Stripe, it renders `StripeCheckoutForm.vue` which either redirects to Stripe or mounts Stripe Elements.

---

## 9. Building a New Bundle

Follow these steps to add a new cross-stack feature as a bundle.

### Step 1 — Backend Plugin

1. Create `plugins/<name>/__init__.py`:
   ```python
   class MyPlugin(BasePlugin):
       @property
       def metadata(self): return PluginMetadata(name="my-feature", ...)
       def get_blueprint(self): from plugins.my_feature.src.routes import bp; return bp
       def get_url_prefix(self): return ""
   ```

2. Create models in `plugins/<name>/src/models/`
3. Create repositories and services
4. Create `routes.py` with both public (`/api/v1/my-feature/`) and admin (`/api/v1/admin/my-feature/`) endpoints
5. Write migration in `plugins/<name>/migrations/versions/YYYYMMDD_create_my_feature_tables.py`
6. Register in `plugins/plugins.json` and `plugins/config.json`
7. Write unit + integration tests
8. Write `bin/populate_my_feature.py` if the plugin needs seed data

### Step 2 — Admin Plugin

1. Create `vbwd-fe-admin/plugins/my-feature-admin/index.ts`
2. Register routes and nav sections:
   ```typescript
   export const myFeatureAdminPlugin = {
     install(app, router) {
       router.addRoute({ path: '/admin/my-feature', ... });
       extensionRegistry.register('my-feature-admin', {
         navSections: [{ id: 'my-feature', label: 'My Feature', items: [...] }],
       });
     }
   };
   ```
3. Create views in `src/views/`
4. Import in the admin app's main plugin loader

### Step 3 — User Plugin

1. Create `vbwd-fe-user/plugins/my-feature/index.ts` with named export:
   ```typescript
   export const myFeaturePlugin: IPlugin = {
     name: 'my-feature',
     version: '1.0.0',
     install(sdk) {
       sdk.addRoute({ path: '/my-feature', ... });
       sdk.addTranslations('en', en);
     },
   };
   ```
2. Create `locales/en.json` (and other locales)
3. Create `src/views/`, `src/components/`, `src/api/`
4. If the plugin needs CMS pages, register components with `sdk.addComponent()` so CMS widget renderer can find them
5. Import and register in the user app's plugin list

### Step 4 — CMS Integration (optional)

If the feature needs public pages (rather than just routes directly in the Vue Router):

1. In the backend populate script, create:
   - `CmsLayout` with the appropriate areas
   - `CmsWidget` records pointing to your Vue components
   - `CmsPage` records with slugs matching desired URLs
2. In the user plugin, register Vue components with the SDK:
   ```typescript
   sdk.addComponent('MyFeatureView', () => import('./src/views/MyFeatureView.vue'));
   ```
3. The CMS `/:slug(.+)` route will now render your feature at the declared CMS page slug

---

## 10. Bundle Checklist

Use this checklist when shipping a new bundle:

**Backend**
- [ ] Plugin class in `__init__.py` (not re-exported)
- [ ] All models inherit from `BaseModel`
- [ ] `to_dict()` serializes UUIDs as `str()`, datetimes as `.isoformat()`
- [ ] Migration file present with correct `down_revision`
- [ ] Public routes unauthenticated where appropriate; admin routes behind `@require_admin`
- [ ] Registered in `plugins.json` and `config.json`
- [ ] Unit tests for all services (mocked repositories)
- [ ] Integration tests for all routes
- [ ] Idempotent populate script

**Admin Plugin**
- [ ] Routes added under `/admin/<feature>/`
- [ ] Nav sections registered with `extensionRegistry`
- [ ] Auth header uses `admin_token` from `localStorage`
- [ ] Error states displayed (loading, error, empty)

**User Plugin**
- [ ] Named export: `export const myPlugin: IPlugin = { ... }`
- [ ] `locales/en.json` present; all `$t()` keys defined
- [ ] `accessStatus` and auth checks gating protected actions
- [ ] No direct calls to `@require_auth` endpoints from unauthenticated context
- [ ] CMS components registered via `sdk.addComponent()` if using CMS rendering

**Seed Script**
- [ ] `bin/populate_<name>.py` is idempotent (re-runnable without duplicates)
- [ ] `bin/populate-db.sh` wrapper present
- [ ] Registered in root `Makefile` `total-rebuild` target
