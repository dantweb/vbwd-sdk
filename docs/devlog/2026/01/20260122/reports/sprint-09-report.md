# Sprint 09 - Countries Configuration Report

## Summary
Implemented admin backend and frontend for managing countries with drag-and-drop reordering.

## Completed Items

### Backend

#### Model
- **Country** - Model at `vbwd-backend/src/models/country.py`
  - `code` - ISO 3166-1 alpha-2 code (unique, 2 chars)
  - `name` - Country name (max 100 chars)
  - `is_enabled` - Whether country is available for selection
  - `position` - Sort order for enabled countries

#### Migration
- **20260122_add_country_table.py** - Migration at `vbwd-backend/alembic/versions/`
  - Creates country table
  - Seeds 36 countries (DACH region enabled by default)
  - DE, AT, CH enabled with positions 1, 2, 3

#### Repository
- **CountryRepository** - At `vbwd-backend/src/repositories/country_repository.py`
  - `find_all()` - All countries
  - `find_by_code(code)` - Single country lookup
  - `find_enabled()` - Enabled countries sorted by position
  - `find_disabled()` - Disabled countries sorted by name
  - `enable(code)` - Enable a country
  - `disable(code)` - Disable a country
  - `update_positions(codes)` - Bulk position update

#### Admin Routes
- **admin_countries_bp** - Blueprint at `vbwd-backend/src/routes/admin/countries.py`
  - `GET /` - List all countries
  - `POST /<code>/enable` - Enable country
  - `POST /<code>/disable` - Disable country
  - `PUT /reorder` - Update positions (accepts `codes` array)
  - `GET /enabled` - List enabled countries
  - `GET /disabled` - List disabled countries

### Frontend Admin App

#### Store
- **useCountriesStore** - Pinia store at `vbwd-frontend/admin/vue/src/stores/countries.ts`
  - State: countries array, loading, error
  - Getters: sortedEnabled, sortedDisabled
  - Actions: fetchAllCountries, enableCountry, disableCountry, reorderCountries

#### View
- **Countries.vue** - At `vbwd-frontend/admin/vue/src/views/Countries.vue`
  - Two-panel layout (enabled/disabled)
  - Drag-and-drop reordering for enabled countries
  - Enable/disable buttons
  - Search filter for disabled countries
  - Flag emoji display
  - Success notifications

#### Router
- Added route: `/countries` -> Countries.vue

#### i18n
- Added translations for `countriesConfig` namespace
- Supported locales: en, de

#### Sidebar
- Added expandable Settings section
- Countries link under Settings

### Integration Tests
- **test_admin_countries.py** - At `vbwd-backend/tests/integration/`
  - Tests for all admin endpoints
  - Repository tests
  - Authorization tests

## Technical Decisions
- Drag-and-drop using native HTML5 drag events
- Optimistic updates with revert on error
- DACH countries (DE, AT, CH) enabled by default
- Flag emoji generated from country code
- Expandable Settings section in sidebar

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/admin/countries | List all countries |
| POST | /api/v1/admin/countries/:code/enable | Enable country |
| POST | /api/v1/admin/countries/:code/disable | Disable country |
| PUT | /api/v1/admin/countries/reorder | Update order |
| GET | /api/v1/settings/countries | Public: enabled countries |

## Files Created/Modified
| File | Action |
|------|--------|
| `src/models/country.py` | Created |
| `src/repositories/country_repository.py` | Created |
| `src/routes/admin/countries.py` | Created |
| `src/routes/admin/__init__.py` | Modified |
| `src/routes/settings.py` | Modified |
| `src/app.py` | Modified |
| `alembic/versions/20260122_add_country_table.py` | Created |
| `tests/integration/test_admin_countries.py` | Created |
| `stores/countries.ts` | Created |
| `views/Countries.vue` | Created |
| `router/index.ts` | Modified |
| `layouts/AdminSidebar.vue` | Modified |
| `i18n/locales/en.json` | Modified |
| `i18n/locales/de.json` | Modified |

## Default Countries (36)
DE, AT, CH, BE, NL, LU, FR, IT, ES, PT, GB, IE, DK, SE, NO, FI, PL, CZ, SK, HU, SI, HR, RO, BG, GR, CY, MT, EE, LV, LT, US, CA, AU, NZ, JP, KR

## Enabled by Default
1. Germany (DE) - Position 1
2. Austria (AT) - Position 2
3. Switzerland (CH) - Position 3
