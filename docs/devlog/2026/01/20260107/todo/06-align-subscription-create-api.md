# Task 06: Align Subscription Create API

**Priority:** High
**Type:** Backend
**Estimate:** Small

## Problem

The frontend `SubscriptionCreate.vue` sends data that doesn't match what the backend expects.

### Frontend Sends (stores/subscriptions.ts)
```typescript
POST /admin/subscriptions
{
  user_id: string,
  plan_id: string,      // Frontend uses "plan_id"
  status?: string,      // "active" | "trialing"
  trial_days?: number   // Number of trial days
}
```

### Backend Expects (routes/admin/subscriptions.py)
```python
POST /admin/subscriptions
{
  user_id: string,
  tarif_plan_id: string,  # Backend uses "tarif_plan_id"
  started_at: ISO_datetime  # Required start date
}
```

## Solution Options

### Option A: Update Backend to Accept Frontend Format (Recommended)
Modify `routes/admin/subscriptions.py` to:
1. Accept `plan_id` as alias for `tarif_plan_id`
2. Default `started_at` to now if not provided
3. Handle `status` and `trial_days` parameters

### Option B: Update Frontend to Match Backend
Modify `stores/subscriptions.ts` and `SubscriptionCreate.vue` to:
1. Send `tarif_plan_id` instead of `plan_id`
2. Send `started_at` with current datetime
3. Remove `status` and `trial_days` fields

## Implementation (Option A)

### File: `vbwd-backend/src/routes/admin/subscriptions.py`

**Update `create_subscription` function (line 30):**

```python
@admin_subs_bp.route('/', methods=['POST'])
@require_auth
@require_admin
def create_subscription():
    """
    Create subscription for user with auto-generated invoice.

    Body:
        - user_id: str (required, UUID)
        - plan_id or tarif_plan_id: str (required, UUID)
        - started_at: str (optional, ISO datetime, defaults to now)
        - status: str (optional, "active" or "trialing")
        - trial_days: int (optional, for trialing status)

    Returns:
        201: Created subscription with invoice
        400: Validation error
        404: User or plan not found
        409: User already has active subscription
    """
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('user_id'):
        return jsonify({'error': 'user_id is required'}), 400

    # Accept both plan_id and tarif_plan_id
    plan_id = data.get('plan_id') or data.get('tarif_plan_id')
    if not plan_id:
        return jsonify({'error': 'plan_id is required'}), 400

    # Parse started_at or default to now
    started_at_str = data.get('started_at')
    if started_at_str:
        try:
            started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
            if started_at.tzinfo:
                started_at = started_at.replace(tzinfo=None)
        except (ValueError, AttributeError):
            return jsonify({'error': 'Invalid started_at format. Use ISO 8601.'}), 400
    else:
        started_at = datetime.utcnow()

    # Handle trial_days
    trial_days = data.get('trial_days')
    requested_status = data.get('status', 'active')

    user_repo = UserRepository(db.session)
    plan_repo = TarifPlanRepository(db.session)
    sub_repo = SubscriptionRepository(db.session)

    # Validate user exists
    user = user_repo.find_by_id(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Validate plan exists
    plan = plan_repo.find_by_id(plan_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    # Check for existing active subscription
    existing = sub_repo.find_active_by_user(data['user_id'])
    if existing:
        return jsonify({'error': 'User already has an active subscription'}), 409

    # Calculate expiration
    billing_months = data.get('billing_period_months') or _get_billing_months(plan.billing_period)

    # Handle trialing status with trial_days
    if requested_status == 'trialing' and trial_days:
        expires_at = started_at + timedelta(days=trial_days)
        status = SubscriptionStatus.TRIALING
    else:
        expires_at = started_at + relativedelta(months=billing_months)
        now = datetime.utcnow()
        status = SubscriptionStatus.ACTIVE if started_at <= now else SubscriptionStatus.PENDING

    # Override status if explicitly set
    if requested_status == 'trialing':
        status = SubscriptionStatus.TRIALING
    elif requested_status == 'active':
        status = SubscriptionStatus.ACTIVE

    # Create subscription
    subscription = Subscription()
    subscription.user_id = user.id
    subscription.tarif_plan_id = plan.id
    subscription.status = status
    subscription.started_at = started_at
    subscription.expires_at = expires_at

    db.session.add(subscription)
    db.session.flush()

    # Create invoice (skip for trialing)
    invoice = None
    if status != SubscriptionStatus.TRIALING:
        invoice = UserInvoice()
        invoice.user_id = user.id
        invoice.tarif_plan_id = plan.id
        invoice.subscription_id = subscription.id
        invoice.invoice_number = UserInvoice.generate_invoice_number()
        invoice.amount = plan.price or plan.price_float or 0
        invoice.currency = plan.currency or 'EUR'
        invoice.status = InvoiceStatus.PENDING
        invoice.invoiced_at = datetime.utcnow()
        invoice.expires_at = datetime.utcnow() + timedelta(days=30)
        db.session.add(invoice)

    db.session.commit()

    # Build response
    response = {
        'subscription': {
            'id': str(subscription.id),
            'user_id': str(subscription.user_id),
            'tarif_plan_id': str(subscription.tarif_plan_id),
            'status': subscription.status.value,
            'started_at': subscription.started_at.isoformat() if subscription.started_at else None,
            'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
            'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
        }
    }

    if invoice:
        response['subscription']['invoice'] = {
            'id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'amount': str(invoice.amount),
            'currency': invoice.currency,
            'status': invoice.status.value,
        }

    return jsonify(response), 201
```

## Testing

```bash
# Test create subscription (minimal)
curl -X POST http://localhost:5000/api/v1/admin/subscriptions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<uuid>", "plan_id": "<uuid>"}'

# Test create subscription with trial
curl -X POST http://localhost:5000/api/v1/admin/subscriptions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<uuid>", "plan_id": "<uuid>", "status": "trialing", "trial_days": 14}'
```

## Acceptance Criteria

- [ ] `POST /admin/subscriptions` accepts `plan_id` as alias
- [ ] `started_at` defaults to now if not provided
- [ ] `status` parameter works ("active", "trialing")
- [ ] `trial_days` parameter sets expiration for trials
- [ ] Existing tests still pass
- [ ] E2E create subscription flow works end-to-end
