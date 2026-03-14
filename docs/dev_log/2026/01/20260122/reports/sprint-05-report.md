# Sprint 05 - Terms & Conditions Report

## Summary
Implemented terms and conditions checkbox with popup modal showing full terms text.

## Completed Items

### Backend
- **settings.py** - Added endpoint at `vbwd-backend/src/routes/settings.py:71-110`
  - `GET /api/v1/settings/terms` - Public endpoint
  - Returns title and markdown content
  - Currently uses hardcoded terms (can be made dynamic later)

### Frontend User App
- **TermsCheckbox.vue** - Component at `vbwd-frontend/user/vue/src/components/checkout/TermsCheckbox.vue`
  - Checkbox with "I agree to Terms and Conditions" label
  - Clickable link opens popup modal
  - Popup displays full terms content
  - Basic markdown-to-HTML conversion
  - Close button and click-outside-to-close
  - Emits `change` event with acceptance state

### Checkout.vue Integration
- Added TermsCheckbox to checkout page
- Tracks `termsAccepted` state
- Required for checkout completion

## Technical Decisions
- Static terms content in backend (not database-driven yet)
- Simple markdown conversion (headers, lists, paragraphs)
- Modal popup instead of separate page
- Terms loaded on component mount

## API Response Format
```json
{
  "title": "Terms and Conditions",
  "content": "## Terms and Conditions\n\n### 1. Acceptance..."
}
```

## Files Created/Modified
| File | Action |
|------|--------|
| `src/routes/settings.py` | Modified (added /terms endpoint) |
| `components/checkout/TermsCheckbox.vue` | Created |
| `views/Checkout.vue` | Modified |

## UI Components
- Checkbox with label
- Modal overlay with blur background
- Header with close button
- Scrollable content area
- Footer with close button
