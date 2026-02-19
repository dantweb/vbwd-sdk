# Sprint 03 Report: Backend Checkout Implementation

**Date:** 2026-01-13
**Status:** ✅ Complete
**Type:** Backend Implementation

## Summary

Implemented the complete backend checkout flow including models, repositories, events, handlers, and routes. All 33 integration tests from Sprint 02 now pass.

## Tasks Completed

| Task | Status | Notes |
|------|--------|-------|
| 3.1 Check existing models | ✅ Done | TokenBundle, AddOn models existed |
| 3.2 Create missing models | ✅ Done | InvoiceLineItem, TokenBundlePurchase, AddOnSubscription |
| 3.3 Create database migrations | ✅ Done | Tables created via db.create_all() |
| 3.4 Create repositories | ✅ Done | 3 new repositories created |
| 3.5 Create checkout events | ✅ Done | CheckoutRequested, Completed, Failed events |
| 3.6 Create checkout handler | ✅ Done | Full checkout logic with DI container |
| 3.7 Create checkout route | ✅ Done | POST /api/v1/user/checkout |
| 3.8 Register handler in DI | ✅ Done | Container-based repository injection |

## Files Created/Modified

### New Models
```
vbwd-backend/src/models/
├── enums.py               # Added PurchaseStatus, LineItemType
├── invoice_line_item.py   # NEW: Line items for invoices
├── token_bundle_purchase.py # NEW: Token bundle purchases
└── addon_subscription.py  # NEW: Add-on subscriptions
```

### New Repositories
```
vbwd-backend/src/repositories/
├── invoice_line_item_repository.py     # NEW
├── token_bundle_purchase_repository.py # NEW
└── addon_subscription_repository.py    # NEW
```

### New Events & Handler
```
vbwd-backend/src/events/
└── checkout_events.py     # NEW: CheckoutRequested, Completed, Failed

vbwd-backend/src/handlers/
└── checkout_handler.py    # NEW: Full checkout logic
```

### Modified Files
```
src/models/__init__.py         # Export new models
src/models/invoice.py          # Added line_items relationship, subtotal, tax_amount, total_amount
src/repositories/__init__.py   # Export new repositories
src/repositories/base.py       # Fixed save() for transient entities
src/events/__init__.py         # Export checkout events
src/handlers/__init__.py       # Export CheckoutHandler
src/container.py               # Added new repository providers
src/app.py                     # Register CheckoutHandler
src/routes/user.py             # Added /checkout endpoint
src/routes/admin/plans.py      # Fixed slug and price_float handling
tests/fixtures/checkout_fixtures.py # Fixed admin API URLs
```

### Database Changes
```sql
-- New tables created
CREATE TABLE invoice_line_item (...)
CREATE TABLE token_bundle_purchase (...)
CREATE TABLE addon_subscription (...)

-- New columns on user_invoice
ALTER TABLE user_invoice ADD COLUMN subtotal NUMERIC(10, 2);
ALTER TABLE user_invoice ADD COLUMN tax_amount NUMERIC(10, 2) DEFAULT 0;
ALTER TABLE user_invoice ADD COLUMN total_amount NUMERIC(10, 2);
```

## Test Results

```
============================= test session starts ==============================
collected 33 items

tests/integration/test_checkout_addons.py         8 passed
tests/integration/test_checkout_endpoint.py      11 passed
tests/integration/test_checkout_invoice_total.py  7 passed
tests/integration/test_checkout_token_bundles.py  8 passed

============================= 33 passed in 13.51s ==============================
```

## API Endpoint

### POST /api/v1/user/checkout

**Request:**
```json
{
  "plan_id": "uuid-here",
  "token_bundle_ids": ["uuid-1", "uuid-2"],
  "add_on_ids": ["uuid-1", "uuid-2"],
  "currency": "USD"
}
```

**Response (201):**
```json
{
  "subscription": {
    "id": "uuid",
    "status": "pending",
    "plan": {"id": "uuid", "name": "Plan Name", "slug": "plan-slug"}
  },
  "invoice": {
    "id": "uuid",
    "invoice_number": "INV-20260113...",
    "status": "pending",
    "amount": "29.00",
    "currency": "USD",
    "line_items": [...]
  },
  "token_bundles": [...],
  "add_ons": [...],
  "message": "Checkout created. Awaiting payment."
}
```

## Architecture

### Event Flow
```
Route (POST /checkout)
  ↓
CheckoutRequestedEvent
  ↓
DomainEventDispatcher.emit()
  ↓
CheckoutHandler.handle()
  ↓
  ├─ Validate plan exists & is active
  ├─ Create PENDING Subscription
  ├─ Create PENDING TokenBundlePurchases
  ├─ Create PENDING AddOnSubscriptions
  ├─ Create UserInvoice with LineItems
  └─ Return EventResult.success()
```

### Key Design Decisions

1. **Container-based DI**: Handler receives container, gets fresh repos per request
2. **Transient entity detection**: Fixed base repository to use SQLAlchemy inspection
3. **Payment-first activation**: All items created with PENDING status
4. **Line items**: Invoice supports multiple line item types (subscription, bundle, add-on)

## Issues Resolved

| Issue | Resolution |
|-------|------------|
| Session persistence error | Handler gets repos at request time via container |
| Missing slug in plan creation | Added slug generation in admin plans route |
| Missing price_float in plan | Added price_float from Decimal conversion |
| Fixture API URL mismatch | Fixed to use `/admin/tarif-plans/`, `/admin/token-bundles/`, `/admin/addons/` |
| Response wrapped in list | Unwrap single-item list from EventResult.combine() |

## Run Command

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose --profile test-integration run --rm test-integration \
    pytest tests/integration/test_checkout*.py -v --tb=short
```

## Next Steps

- **Sprint 04**: Implement payment capture
  - Payment confirmation webhook
  - Activate subscription on payment
  - Credit tokens on payment
  - Update invoice status

## Definition of Done

- [x] Models created (InvoiceLineItem, TokenBundlePurchase, AddOnSubscription)
- [x] Database tables created
- [x] Repositories implemented
- [x] Checkout events defined
- [x] Checkout handler implemented
- [x] Checkout route exposed
- [x] Handler registered in DI container
- [x] All 33 integration tests passing
- [x] Sprint moved to `/done`
- [x] Report created in `/reports`
