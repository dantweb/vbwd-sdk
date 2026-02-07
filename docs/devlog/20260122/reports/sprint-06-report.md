# Sprint 06 - Billing Address Report

## Summary
Implemented billing address form with country selection fetching from backend API.

## Completed Items

### Backend
- **settings.py** - Added endpoint at `vbwd-backend/src/routes/settings.py:113-129`
  - `GET /api/v1/settings/countries` - Public endpoint
  - Returns enabled countries from CountryRepository
  - Countries ordered by position

### Frontend User App
- **BillingAddressBlock.vue** - Component at `vbwd-frontend/user/vue/src/components/checkout/BillingAddressBlock.vue`
  - Company field (optional)
  - Street address field (required)
  - City field (required)
  - ZIP code field (required)
  - Country dropdown (required)
  - Real-time validation with error messages
  - Touch tracking for validation display
  - Loads saved address for authenticated users
  - Fetches countries from API with fallback

### Form Fields
| Field | Required | Validation |
|-------|----------|------------|
| Company | No | None |
| Street | Yes | Not empty |
| City | Yes | Not empty |
| ZIP | Yes | Not empty |
| Country | Yes | Must select |

### API Integration
- `GET /api/v1/settings/countries` - Fetch available countries
- `GET /api/v1/user/billing-address` - Load saved address (if authenticated)

### Checkout.vue Integration
- Added BillingAddressBlock to checkout page
- Tracks billing address data and validity
- Emits `change` with address data
- Emits `valid` with validation state

## Technical Decisions
- Fallback countries list if API fails (DE, AT, CH, US, GB)
- No format validation for ZIP (varies by country)
- Company field optional per EU requirements
- Load saved address only for authenticated users

## Files Created/Modified
| File | Action |
|------|--------|
| `src/routes/settings.py` | Modified (added /countries endpoint) |
| `components/checkout/BillingAddressBlock.vue` | Created |
| `views/Checkout.vue` | Modified |

## Data Flow
```
BillingAddressBlock
  -> api.get('/settings/countries')
    -> Backend settings_bp route
      -> CountryRepository.find_enabled()
        -> Returns ordered country list
```
