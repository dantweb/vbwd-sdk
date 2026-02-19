# Sprint: Backend - Admin Create Subscription Endpoint

**Date:** 2026-01-06
**Priority:** High
**Type:** Backend Implementation
**Tests:** `vbwd-backend/tests/integration/test_user_subscription_flow.py`

---

## Core Requirements

### Methodology
- **TDD-First**: Tests already exist. Run tests BEFORE and AFTER implementation.
- **SOLID Principles**: Single responsibility, dependency injection, interface segregation.
- **Clean Code**: Readable, well-named, self-documenting code.
- **No Over-engineering**: Minimal code to pass tests. No speculative features.

### Test Execution
```bash
# ALWAYS run tests in docker-compose
cd vbwd-backend

# Run BEFORE implementation (should see xfail)
docker-compose run --rm -e API_BASE_URL=http://api:5000/api/v1 test \
    pytest tests/integration/test_user_subscription_flow.py::TestAPIEndpointExistence::test_admin_create_subscription_endpoint_exists -v

# Run AFTER implementation (should pass)
docker-compose run --rm -e API_BASE_URL=http://api:5000/api/v1 test \
    pytest tests/integration/test_user_subscription_flow.py -v

# Run unit tests during development
docker-compose run --rm test pytest tests/unit/ -v
```

### Design Decisions
- **Multiple Subscriptions**: Reject with 409 Conflict if user already has active subscription
- **Events**: Dispatch `subscription:created` and `invoice:created` events

### Definition of Done
- [ ] All existing tests pass (no regressions)
- [ ] New endpoint test passes (removes xfail)
- [ ] Invoice auto-creation works
- [ ] Returns 409 if user has active subscription
- [ ] `subscription:created` event is dispatched
- [ ] `invoice:created` event is dispatched
- [ ] Code follows existing patterns in codebase
- [ ] No unnecessary abstractions added

---

## Objective

Implement `POST /api/v1/admin/subscriptions` endpoint so admin can create subscriptions for users, with automatic invoice generation.

**TDD Discovery:** Integration tests expect this endpoint but it doesn't exist.
Currently there is no way to create subscriptions via admin API.

---

## Test Reference

Tests that will pass after implementation:

```python
# From test_user_subscription_flow.py (marked as xfail)
@pytest.mark.xfail(reason="TDD: POST /admin/subscriptions not implemented yet")
def test_admin_create_subscription_endpoint_exists(self, auth_headers):
    response = requests.post(
        f"{self.BASE_URL}/admin/subscriptions",
        json={},
        headers=auth_headers,
        timeout=10
    )
    assert response.status_code != 404, "POST /admin/subscriptions endpoint not found"
```

---

## Data Models

### Subscription Model
```python
class Subscription(BaseModel):
    user_id: UUID                 # FK to User
    tarif_plan_id: UUID           # FK to TarifPlan
    pending_plan_id: UUID         # Optional, for plan changes
    status: SubscriptionStatus    # PENDING | ACTIVE | PAUSED | CANCELLED | EXPIRED
    started_at: datetime          # When subscription started
    expires_at: datetime          # When subscription expires
    cancelled_at: datetime        # Optional
    paused_at: datetime           # Optional
```

### Invoice Model (Auto-generated)
```python
class UserInvoice(BaseModel):
    user_id: UUID                 # FK to User
    tarif_plan_id: UUID           # FK to TarifPlan
    subscription_id: UUID         # FK to Subscription
    invoice_number: str           # Unique, e.g., "INV-20260105120000-A1B2C3"
    amount: Decimal               # Invoice amount (from plan price)
    currency: str                 # Default "EUR"
    status: InvoiceStatus         # PENDING (default for new subscriptions)
    invoiced_at: datetime         # When invoice was created
    expires_at: datetime          # Payment due date
```

---

## API Specification

### Endpoint

```
POST /api/v1/admin/subscriptions
```

### Request Schema

```python
CreateSubscriptionRequest = {
    "user_id": str,             # UUID, required
    "tarif_plan_id": str,       # UUID, required
    "started_at": str,          # ISO datetime, required (when subscription starts)
    "billing_period_months": int,  # Optional, default from plan
}
```

### Response Schema

```python
# 201 Created
CreateSubscriptionResponse = {
    "id": str,                  # UUID
    "user_id": str,
    "tarif_plan_id": str,
    "status": str,              # "active" or "pending"
    "started_at": str,          # ISO datetime
    "expires_at": str,          # ISO datetime
    "created_at": str,          # ISO datetime
    "invoice": {                # Auto-generated invoice
        "id": str,
        "invoice_number": str,
        "amount": str,
        "currency": str,
        "status": str,          # "pending"
    }
}

# 400 Bad Request
ErrorResponse = {
    "error": str,
    "details": dict | None,
}

# 404 Not Found (user or plan doesn't exist)
NotFoundResponse = {
    "error": "User not found" | "Plan not found"
}

# 409 Conflict (user already has active subscription)
ConflictResponse = {
    "error": "User already has an active subscription"
}
```

---

## Implementation Plan

### Phase 1: Schema Definition

**File:** `src/schemas/admin_subscription_schemas.py`

```python
from marshmallow import Schema, fields, validate

class CreateSubscriptionRequestSchema(Schema):
    user_id = fields.UUID(required=True)
    tarif_plan_id = fields.UUID(required=True)
    started_at = fields.DateTime(required=True)
    billing_period_months = fields.Int(validate=validate.Range(min=1, max=36))
```

### Phase 2: Service Method

**File:** `src/services/admin_subscription_service.py`

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional
from uuid import UUID
from decimal import Decimal

from src.models.subscription import Subscription
from src.models.user_invoice import UserInvoice
from src.models.enums import SubscriptionStatus, InvoiceStatus
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.invoice_repository import InvoiceRepository
from src.repositories.user_repository import UserRepository
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.events.dispatcher import EventDispatcher


class AdminSubscriptionService:
    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        invoice_repository: InvoiceRepository,
        user_repository: UserRepository,
        plan_repository: TarifPlanRepository,
        event_dispatcher: EventDispatcher,
    ):
        self._sub_repo = subscription_repository
        self._invoice_repo = invoice_repository
        self._user_repo = user_repository
        self._plan_repo = plan_repository
        self._dispatcher = event_dispatcher

    def create_subscription(
        self,
        user_id: UUID,
        tarif_plan_id: UUID,
        started_at: datetime,
        billing_period_months: Optional[int] = None,
    ) -> dict:
        """Create subscription for user with auto-generated invoice.

        Args:
            user_id: Target user UUID
            tarif_plan_id: Plan UUID
            started_at: When subscription should start
            billing_period_months: Override plan's billing period

        Returns:
            Dict with subscription and invoice data

        Raises:
            ValueError: If user/plan not found or user has active subscription
        """
        # Validate user exists
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Validate plan exists
        plan = self._plan_repo.find_by_id(tarif_plan_id)
        if not plan:
            raise ValueError("Plan not found")

        # Check for existing active subscription
        existing = self._sub_repo.find_active_by_user_id(user_id)
        if existing:
            raise ValueError("User already has an active subscription")

        # Calculate expiration
        months = billing_period_months or self._get_plan_billing_months(plan)
        expires_at = started_at + relativedelta(months=months)

        # Determine initial status
        now = datetime.utcnow()
        status = SubscriptionStatus.ACTIVE if started_at <= now else SubscriptionStatus.PENDING

        # Create subscription
        subscription = Subscription()
        subscription.user_id = user_id
        subscription.tarif_plan_id = tarif_plan_id
        subscription.status = status
        subscription.started_at = started_at
        subscription.expires_at = expires_at

        created_sub = self._sub_repo.save(subscription)

        # Dispatch subscription event
        self._dispatcher.dispatch('subscription:created', {
            'subscription_id': str(created_sub.id),
            'user_id': str(user_id),
            'plan_id': str(tarif_plan_id),
            'status': status.value,
        })

        # Create invoice
        invoice = self._create_invoice(created_sub, user, plan)

        return {
            'subscription': created_sub,
            'invoice': invoice,
        }

    def _create_invoice(
        self,
        subscription: Subscription,
        user,
        plan,
    ) -> UserInvoice:
        """Create pending invoice for subscription."""
        invoice = UserInvoice()
        invoice.user_id = subscription.user_id
        invoice.tarif_plan_id = subscription.tarif_plan_id
        invoice.subscription_id = subscription.id
        invoice.invoice_number = self._generate_invoice_number()
        invoice.amount = plan.price
        invoice.currency = plan.currency or 'EUR'
        invoice.status = InvoiceStatus.PENDING
        invoice.invoiced_at = datetime.utcnow()
        invoice.expires_at = datetime.utcnow() + relativedelta(days=30)

        created_invoice = self._invoice_repo.save(invoice)

        # Dispatch invoice event
        self._dispatcher.dispatch('invoice:created', {
            'invoice_id': str(created_invoice.id),
            'user_id': str(subscription.user_id),
            'subscription_id': str(subscription.id),
            'amount': str(created_invoice.amount),
            'currency': created_invoice.currency,
        })

        return created_invoice

    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        import secrets
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        suffix = secrets.token_hex(3).upper()
        return f"INV-{timestamp}-{suffix}"

    def _get_plan_billing_months(self, plan) -> int:
        """Get billing period in months from plan."""
        period_map = {
            'monthly': 1,
            'quarterly': 3,
            'yearly': 12,
            'lifetime': 1200,  # ~100 years
        }
        return period_map.get(plan.billing_period, 1)
```

### Phase 3: Route Implementation

**File:** `src/routes/admin/subscriptions.py` (extend existing)

```python
from marshmallow import ValidationError

@admin_subs_bp.route('/', methods=['POST'])
@require_auth
@require_admin
def create_subscription():
    """
    Create subscription for user with auto-generated invoice.

    ---
    Request body:
        {
            "user_id": "uuid-here",
            "tarif_plan_id": "uuid-here",
            "started_at": "2026-01-06T00:00:00Z"
        }

    Returns:
        201: Created subscription with invoice
        400: Validation error
        404: User or plan not found
        409: User already has active subscription
    """
    try:
        data = create_subscription_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': str(err.messages)}), 400

    # Get service from container
    admin_sub_service = current_app.container.admin_subscription_service()

    try:
        result = admin_sub_service.create_subscription(
            user_id=data['user_id'],
            tarif_plan_id=data['tarif_plan_id'],
            started_at=data['started_at'],
            billing_period_months=data.get('billing_period_months'),
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return jsonify({'error': error_msg}), 404
        if "already has" in error_msg.lower():
            return jsonify({'error': error_msg}), 409
        return jsonify({'error': error_msg}), 400

    subscription = result['subscription']
    invoice = result['invoice']

    return jsonify({
        'id': str(subscription.id),
        'user_id': str(subscription.user_id),
        'tarif_plan_id': str(subscription.tarif_plan_id),
        'status': subscription.status.value,
        'started_at': subscription.started_at.isoformat(),
        'expires_at': subscription.expires_at.isoformat(),
        'created_at': subscription.created_at.isoformat(),
        'invoice': {
            'id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'amount': str(invoice.amount),
            'currency': invoice.currency,
            'status': invoice.status.value,
        }
    }), 201
```

### Phase 4: Container Registration

**File:** `src/container.py` (extend)

```python
class Container(containers.DeclarativeContainer):
    # ... existing providers ...

    admin_subscription_service = providers.Factory(
        AdminSubscriptionService,
        subscription_repository=subscription_repository,
        invoice_repository=invoice_repository,
        user_repository=user_repository,
        plan_repository=tarif_plan_repository,
        event_dispatcher=event_dispatcher,
    )
```

### Phase 5: Repository Method

**File:** `src/repositories/subscription_repository.py` (add method)

```python
def find_active_by_user_id(self, user_id: UUID) -> Optional[Subscription]:
    """Find active subscription for user."""
    return (
        self._session.query(Subscription)
        .filter_by(user_id=user_id, status=SubscriptionStatus.ACTIVE)
        .first()
    )
```

---

## Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `subscription:created` | POST /admin/subscriptions | `{subscription_id, user_id, plan_id, status}` |
| `invoice:created` | Auto with subscription | `{invoice_id, user_id, subscription_id, amount, currency}` |

---

## Business Rules

1. **Status Determination:**
   - `started_at <= now` → status = `active`
   - `started_at > now` → status = `pending`

2. **Invoice Auto-Creation:**
   - Every new subscription creates a `pending` invoice
   - Invoice amount = plan price
   - Invoice expires in 30 days

3. **Single Active Subscription:**
   - User can only have ONE active subscription
   - Creating second subscription returns 409 Conflict

4. **Billing Period Calculation:**
   - `monthly` = 1 month
   - `quarterly` = 3 months
   - `yearly` = 12 months
   - `lifetime` = 1200 months (~100 years)

---

## Acceptance Criteria

- [ ] `POST /api/v1/admin/subscriptions` returns 201 on success
- [ ] Subscription is created with correct status
- [ ] Invoice is auto-generated with pending status
- [ ] `subscription:created` event is dispatched
- [ ] `invoice:created` event is dispatched
- [ ] 404 returned if user not found
- [ ] 404 returned if plan not found
- [ ] 409 returned if user has active subscription
- [ ] 400 returned for validation errors
- [ ] Only admin role can access endpoint
- [ ] Integration test `test_admin_create_subscription_endpoint_exists` passes

---

## Test Verification

```bash
# Run integration tests
docker-compose run --rm -e API_BASE_URL=http://api:5000/api/v1 test \
    pytest tests/integration/test_user_subscription_flow.py::TestAPIEndpointExistence::test_admin_create_subscription_endpoint_exists -v
```

---

*Created: 2026-01-05*
*Relates to: Sprint 04 (E2E & Integration Tests)*
*Depends on: Sprint 05 (Admin Create User) - for full flow testing*
