# Sprint 02 — GitHub Repo Manager (GHRM) Plugin

**Date:** 2026-03-02
**Principles:** TDD-first · SOLID · DRY · Liskov · Dependency Injection · Clean Code
**Dependencies:** `theme-switcher` plugin (fe-user), `checkout` plugin (fe-user)

---

## Overview

A software catalogue where each software package maps to a tariff plan. Active subscribers are granted access to a protected branch of the package's GitHub repo. Access is revoked (with grace period) on subscription cancellation or payment failure.

Split across:
- **Backend plugin** — GitHub App integration, collaborator lifecycle, models, migrations
- **fe-user plugin** — Software catalogue browsing + package detail pages

---

## Architecture Decisions

| Concern | Decision |
|---|---|
| GitHub auth | GitHub App (per-installation token, fine-grained permissions) |
| GitHub username | User enters manually in profile settings |
| Repo model | Public repo + protected `release` branch (collaborator gets access) |
| Access revocation | Grace period before removal (matches plan `trailing_days`) |
| Package managers | npm, composer, pip, git — all supported |
| Similar software | Manually curated by admin (related packages per package) |
| Categories | Defined in backend plugin config (maps tariff plan categories) |

---

## Access Control Design

### Why public repo + protected branch?

```
Public repo:
  main branch    → open source, anyone can read
  release branch → protected, only collaborators can pull tagged releases

Subscriber gets:
  - Added as collaborator with read access to release branch
  - Can pull/clone specific release tags via any package manager

Non-subscriber sees:
  - Public repo (main branch only)
  - Cannot pull release tags
```

### Package Manager Integration

Each package detail page shows install instructions per manager:

```bash
# npm
npm install git+https://<github-token>@github.com/owner/repo.git#release

# composer
composer require owner/package:dev-release --prefer-source

# pip
pip install git+https://<github-token>@github.com/owner/repo.git@release

# git
git clone -b release https://<github-token>@github.com/owner/repo.git
```

The `<github-token>` is a **scoped deploy token** generated per user via GitHub App.
Tokens are stored encrypted in `user_github_access` and rotated on renewal.

---

## Backend Plugin

### Models & Migrations

#### `github_repo`
```
id              UUID PK
software_package_id  UUID FK → software_package UNIQUE
owner           VARCHAR(128) NOT NULL    -- GitHub org or user
repo_name       VARCHAR(128) NOT NULL    -- repository name
protected_branch VARCHAR(64) DEFAULT 'release'
installation_id  VARCHAR(64)            -- GitHub App installation ID
is_active        BOOLEAN DEFAULT TRUE
created_at       TIMESTAMP
updated_at       TIMESTAMP

UNIQUE(owner, repo_name)
```

#### `software_package`
```
id              UUID PK
name            VARCHAR(255) NOT NULL
slug            VARCHAR(64) UNIQUE NOT NULL
description     TEXT
tech_specs      JSONB
image_gallery   JSONB                   -- list of CmsImage URL paths
changelog_text  TEXT
changelog_url   VARCHAR(512)            -- link to GitHub changelog/releases
download_counter INT DEFAULT 0
deps            JSONB                   -- list of slugs of dependencies
related_packages JSONB                  -- manually curated list of slugs
tariff_plan_id   UUID FK → tarif_plan UNIQUE
is_active        BOOLEAN DEFAULT TRUE
sort_order       INT DEFAULT 0
created_at       TIMESTAMP
updated_at       TIMESTAMP
```

#### `user_github_access`
```
id                  UUID PK
user_id             UUID FK → user UNIQUE
github_username     VARCHAR(128) NOT NULL
deploy_token        TEXT                -- encrypted, scoped GitHub token
token_expires_at    TIMESTAMP
access_status       VARCHAR(32)         -- active | grace | revoked
grace_expires_at    TIMESTAMP           -- NULL if not in grace period
last_synced_at      TIMESTAMP
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

#### `github_access_log`
```
id              UUID PK
user_id         UUID FK → user
repo_id         UUID FK → github_repo
action          VARCHAR(32)     -- add_collaborator | remove_collaborator | grace_started | token_rotated
triggered_by    VARCHAR(64)     -- subscription_event | manual | scheduler
subscription_id UUID FK → subscription (nullable)
meta            JSONB
created_at      TIMESTAMP
```

---

### Repository Layer (DI interfaces)

```
ISoftwarePackageRepository
  find_by_slug(slug) → SoftwarePackage
  find_by_tariff_plan_id(plan_id) → SoftwarePackage
  find_all(page, per_page, category_slug, query) → PaginatedResult
  save(package) → SoftwarePackage
  delete(id) → None
  increment_downloads(slug) → None

IGithubRepoRepository
  find_by_package_id(package_id) → GithubRepo
  find_all() → List[GithubRepo]
  save(repo) → GithubRepo
  delete(id) → None

IUserGithubAccessRepository
  find_by_user_id(user_id) → UserGithubAccess | None
  find_grace_expired(now) → List[UserGithubAccess]
  save(access) → UserGithubAccess
  delete(id) → None

IGithubAccessLogRepository
  log(user_id, repo_id, action, triggered_by, meta) → None
  find_by_user(user_id, page, per_page) → PaginatedResult
```

---

### Service Layer

```
IGithubAppClient                           -- DI interface
  add_collaborator(owner, repo, username, branch) → bool
  remove_collaborator(owner, repo, username) → bool
  create_deploy_token(owner, repo, username) → str
  revoke_deploy_token(token) → None
  get_installation_token(installation_id) → str

GithubAppClient(IGithubAppClient)          -- real implementation (PyGithub / httpx)

MockGithubAppClient(IGithubAppClient)      -- test double


SoftwarePackageService(
    repo: ISoftwarePackageRepository,
    plan_category_slugs: List[str]         -- from plugin config
)
  list_packages(params) → PaginatedResult[SoftwarePackageDTO]
  get_package(slug) → SoftwarePackageDTO
  get_related(slug) → List[SoftwarePackageDTO]
  get_install_instructions(slug, user_id) → InstallInstructionsDTO


GithubAccessService(
    access_repo: IUserGithubAccessRepository,
    log_repo: IGithubAccessLogRepository,
    repo_repo: IGithubRepoRepository,
    github: IGithubAppClient
)
  # Called by subscription event handlers
  on_subscription_activated(user_id, plan_id) → None
  on_subscription_cancelled(user_id, plan_id) → None
  on_subscription_payment_failed(user_id, plan_id) → None
  on_subscription_renewed(user_id, plan_id) → None

  # Grace period scheduler (called by cron)
  revoke_expired_grace_access() → int      -- returns count revoked

  # User-facing
  set_github_username(user_id, username) → UserGithubAccessDTO
  get_access_status(user_id) → UserGithubAccessDTO
  get_install_token(user_id, package_slug) → str
```

---

### Subscription Event Wiring

The backend plugin hooks into the existing vbwd event system:

```python
# plugin on_enable():
event_dispatcher.subscribe('subscription.activated',  github_access_service.on_subscription_activated)
event_dispatcher.subscribe('subscription.cancelled',  github_access_service.on_subscription_cancelled)
event_dispatcher.subscribe('subscription.payment_failed', github_access_service.on_subscription_payment_failed)
event_dispatcher.subscribe('subscription.renewed',    github_access_service.on_subscription_renewed)
```

### Grace Period Flow

```
subscription.cancelled / payment_failed
    ↓
GithubAccessService.on_subscription_cancelled()
    ↓
access_status = 'grace'
grace_expires_at = now + plan.trailing_days
log(action='grace_started')
    ↓
Scheduler (daily cron) → revoke_expired_grace_access()
    ↓
  IF grace_expires_at < now:
    github.remove_collaborator(owner, repo, username)
    github.revoke_deploy_token(token)
    access_status = 'revoked'
    log(action='remove_collaborator')
```

---

### API Endpoints

```
# Public (fe-user)
GET  /api/v1/ghrm/packages                        list (paginated, category, search)
GET  /api/v1/ghrm/packages/<slug>                 package detail
GET  /api/v1/ghrm/packages/<slug>/related         related packages
GET  /api/v1/ghrm/packages/<slug>/install         install instructions (auth required)

# User profile
GET  /api/v1/ghrm/access                          current user's github access status
PUT  /api/v1/ghrm/access/username                 set github username

# Admin
GET  /api/v1/admin/ghrm/packages                  list all packages
POST /api/v1/admin/ghrm/packages                  create
PUT  /api/v1/admin/ghrm/packages/<id>             update
DEL  /api/v1/admin/ghrm/packages/<id>             delete
GET  /api/v1/admin/ghrm/repos                     list github repo mappings
POST /api/v1/admin/ghrm/repos                     create mapping
PUT  /api/v1/admin/ghrm/repos/<id>                update
GET  /api/v1/admin/ghrm/access-log                audit log (paginated)
POST /api/v1/admin/ghrm/access/sync/<user_id>     manual sync for a user
```

---

### Plugin Config (`plugins/config.json`)

```json
{
  "ghrm": {
    "github_app_id": "12345",
    "github_app_private_key_path": "/app/plugins/ghrm/github-app.pem",
    "github_installation_id": "67890",
    "tariff_plan_category_slugs": ["backend", "fe-user", "fe-admin"],
    "grace_period_fallback_days": 7
  }
}
```

---

### Tests (TDD — write first)

```
tests/unit/services/
  test_software_package_service.py
    - test_list_filters_by_category_slug
    - test_get_package_increments_download_counter
    - test_get_install_instructions_requires_active_subscription
    - test_get_related_returns_manually_curated_list

  test_github_access_service.py
    - test_on_activation_adds_collaborator_when_username_set
    - test_on_activation_skips_when_no_github_username
    - test_on_cancellation_sets_grace_status
    - test_on_cancellation_uses_plan_trailing_days
    - test_revoke_expired_removes_collaborator_and_token
    - test_on_renewal_extends_access_and_rotates_token
    - test_payment_failed_starts_grace_period

tests/unit/repositories/
  test_software_package_repository.py
  test_user_github_access_repository.py

tests/integration/
  test_ghrm_packages_api.py
  test_ghrm_access_api.py
  test_github_access_service_integration.py  -- uses MockGithubAppClient
```

---

## fe-user Plugin

### Routes

```
/category                               GhrmCategoryIndex.vue
/category/:category_slug                GhrmPackageList.vue
/category/:category_slug/:package_slug  GhrmPackageDetail.vue
/search                                 GhrmSearch.vue
```

### Components

```
GhrmCategoryIndex.vue
  - Grid of category cards (from plugin config category slugs)
  - Each card → /category/:slug
  - Theme-switcher compliant

GhrmPackageList.vue
  - List/table toggle view
  - Sortable columns: name, downloads, updated_at
  - Pagination + quicksearch within category
  - Each row/card → package detail
  - "Get Package" CTA → /checkout with tariff_plan_id

GhrmPackageDetail.vue
  Tabbed layout:
    Tab 1 — Description (renders description + tech_specs)
    Tab 2 — Changelog (changelog_text or iframe changelog_url)
    Tab 3 — Screenshots (image_gallery rendered)
    Tab 4 — Links + Install
              IF active subscriber:
                Shows install instructions for npm/composer/pip/git
                Deploy token displayed (copy button)
              ELSE:
                "Get Package" button → checkout plugin

  Below tabs — Related Software stream (manually curated)

GhrmSearch.vue
  - Global search across all packages (name, description, slug)
  - List view of results
  - Same card/row as GhrmPackageList

GhrmGithubUsernameForm.vue    -- embedded in user profile settings
  - Input: GitHub username
  - Save → PUT /api/v1/ghrm/access/username
  - Shows current access status (active / grace / revoked / not set)
```

### Store (`useGhrmStore`)

```typescript
state: {
  categories: Category[]
  packages: PaginatedResult<SoftwarePackage>
  currentPackage: SoftwarePackage | null
  relatedPackages: SoftwarePackage[]
  searchResults: PaginatedResult<SoftwarePackage>
  installInstructions: InstallInstructions | null
  accessStatus: GithubAccessStatus | null
  loading: boolean
  error: string | null
}
actions:
  fetchCategories()
  fetchPackages(categorySlug, params)
  fetchPackage(categorySlug, packageSlug)
  fetchRelated(packageSlug)
  fetchInstallInstructions(packageSlug)
  search(query, params)
  fetchAccessStatus()
  setGithubUsername(username)
```

---

## Implementation Order (TDD)

```
1.  Write failing tests for GithubAccessService (mock GitHub client)
2.  Implement models + migrations
3.  Implement MockGithubAppClient (test double)
4.  Implement GithubAppClient (real — PyGithub)
5.  Implement repositories
6.  Implement GithubAccessService (tests go green)
7.  Wire subscription event handlers
8.  Implement grace period scheduler (cron job or APScheduler)
9.  Write failing tests for SoftwarePackageService
10. Implement SoftwarePackageService (tests go green)
11. Implement admin API endpoints
12. Implement public + user API endpoints
13. fe-user: GhrmCategoryIndex + GhrmPackageList
14. fe-user: GhrmPackageDetail (tabs + install instructions)
15. fe-user: GhrmSearch
16. fe-user: GhrmGithubUsernameForm (in user profile)
17. E2E: subscribe → set username → view install token → cancel → grace → revoke
```
