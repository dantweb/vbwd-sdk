# Sprint 5: Admin API & Webhooks

**Goal:** Implement admin management endpoints and webhook handlers for payment providers.

**Prerequisites:** Sprint 4 complete (payments)

---

## Objectives

- [ ] Admin user management endpoints
- [ ] Admin subscription management
- [ ] Admin invoice management
- [ ] Admin tariff plan CRUD
- [ ] Admin currency/tax management
- [ ] PayPal webhook handler
- [ ] Stripe webhook handler
- [ ] Background job for expiration checks

---

## Tasks

### 5.1 Admin Routes - Users

**File:** `python/api/src/routes/admin/users.py`

```python
"""Admin user management routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from marshmallow import Schema, fields, validate, ValidationError
from src.container import Container
from src.middleware.auth import require_auth, require_admin
from src.models import UserStatus

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")


class UserFilterSchema(Schema):
    """Schema for user list filters."""
    status = fields.Str(validate=validate.OneOf(["pending", "active", "suspended", "deleted"]))
    limit = fields.Int(load_default=50, validate=validate.Range(min=1, max=100))
    offset = fields.Int(load_default=0, validate=validate.Range(min=0))


class UpdateUserSchema(Schema):
    """Schema for user update."""
    status = fields.Str(validate=validate.OneOf(["pending", "active", "suspended", "deleted"]))
    role = fields.Str(validate=validate.OneOf(["user", "admin"]))


filter_schema = UserFilterSchema()
update_schema = UpdateUserSchema()


@admin_users_bp.route("", methods=["GET"])
@require_auth
@require_admin
@inject
def list_users(
    user_service=Provide[Container.user_service],
):
    """
    List all users with filters.

    GET /api/v1/admin/users?status=active&limit=50&offset=0
    Authorization: Bearer <admin_token>
    """
    try:
        params = filter_schema.load(request.args)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    users = user_service.list_users(
        status=params.get("status"),
        limit=params["limit"],
        offset=params["offset"],
    )

    return jsonify({
        "users": [u.to_dict() for u in users],
        "limit": params["limit"],
        "offset": params["offset"],
    }), 200


@admin_users_bp.route("/<int:user_id>", methods=["GET"])
@require_auth
@require_admin
@inject
def get_user(
    user_id: int,
    user_service=Provide[Container.user_service],
):
    """
    Get user details with subscriptions and invoices.

    GET /api/v1/admin/users/123
    Authorization: Bearer <admin_token>
    """
    user = user_service.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    details = user_service.get_user_details(user_id)

    return jsonify({
        "user": user.to_dict(),
        "details": details.to_dict() if details else None,
        "subscriptions": [s.to_dict() for s in user.subscriptions],
        "invoices": [i.to_dict() for i in user.invoices],
    }), 200


@admin_users_bp.route("/<int:user_id>", methods=["PUT"])
@require_auth
@require_admin
@inject
def update_user(
    user_id: int,
    user_service=Provide[Container.user_service],
):
    """
    Update user status or role.

    PUT /api/v1/admin/users/123
    Authorization: Bearer <admin_token>
    {
        "status": "suspended"
    }
    """
    try:
        data = update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user = user_service.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if "status" in data:
        user = user_service.update_user_status(user_id, UserStatus(data["status"]))

    if "role" in data:
        from src.models import UserRole
        user = user_service.update_user_role(user_id, UserRole(data["role"]))

    return jsonify(user.to_dict()), 200
```

---

### 5.2 Admin Routes - Subscriptions

**File:** `python/api/src/routes/admin/subscriptions.py`

```python
"""Admin subscription management routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from marshmallow import Schema, fields, validate, ValidationError
from src.container import Container
from src.middleware.auth import require_auth, require_admin

admin_subscriptions_bp = Blueprint(
    "admin_subscriptions", __name__, url_prefix="/admin/subscriptions"
)


class SubscriptionFilterSchema(Schema):
    """Schema for subscription list filters."""
    user_id = fields.Int()
    status = fields.Str(validate=validate.OneOf(["active", "inactive", "cancelled", "expired"]))
    limit = fields.Int(load_default=50)
    offset = fields.Int(load_default=0)


class UpdateSubscriptionSchema(Schema):
    """Schema for subscription update."""
    status = fields.Str(validate=validate.OneOf(["active", "inactive", "cancelled", "expired"]))
    extend_days = fields.Int(validate=validate.Range(min=1, max=365))


filter_schema = SubscriptionFilterSchema()
update_schema = UpdateSubscriptionSchema()


@admin_subscriptions_bp.route("", methods=["GET"])
@require_auth
@require_admin
@inject
def list_subscriptions(
    subscription_service=Provide[Container.subscription_service],
):
    """
    List all subscriptions with filters.

    GET /api/v1/admin/subscriptions?status=active&user_id=123
    Authorization: Bearer <admin_token>
    """
    try:
        params = filter_schema.load(request.args)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    subscriptions = subscription_service.list_subscriptions(
        user_id=params.get("user_id"),
        status=params.get("status"),
        limit=params["limit"],
        offset=params["offset"],
    )

    return jsonify({
        "subscriptions": [s.to_dict() for s in subscriptions],
    }), 200


@admin_subscriptions_bp.route("/<int:subscription_id>", methods=["PUT"])
@require_auth
@require_admin
@inject
def update_subscription(
    subscription_id: int,
    subscription_service=Provide[Container.subscription_service],
):
    """
    Update subscription status or extend.

    PUT /api/v1/admin/subscriptions/123
    Authorization: Bearer <admin_token>
    {
        "extend_days": 30
    }
    """
    try:
        data = update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    subscription = subscription_service._subscription_repo.find_by_id(subscription_id)
    if not subscription:
        return jsonify({"error": "Subscription not found"}), 404

    if "extend_days" in data:
        subscription = subscription_service.extend_subscription(
            subscription_id, data["extend_days"]
        )

    if "status" in data:
        from src.models import SubscriptionStatus
        if data["status"] == "active":
            subscription = subscription_service.activate_subscription(subscription_id)
        elif data["status"] == "cancelled":
            subscription = subscription_service.cancel_subscription(subscription_id)
        elif data["status"] == "expired":
            subscription = subscription_service.expire_subscription(subscription_id)

    return jsonify(subscription.to_dict()), 200
```

---

### 5.3 Admin Routes - Invoices

**File:** `python/api/src/routes/admin/invoices.py`

```python
"""Admin invoice management routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from marshmallow import Schema, fields, validate, ValidationError
from src.container import Container
from src.middleware.auth import require_auth, require_admin

admin_invoices_bp = Blueprint(
    "admin_invoices", __name__, url_prefix="/admin/invoices"
)


class InvoiceFilterSchema(Schema):
    """Schema for invoice list filters."""
    user_id = fields.Int()
    status = fields.Str(validate=validate.OneOf(["invoiced", "paid", "expired", "cancelled"]))
    limit = fields.Int(load_default=50)
    offset = fields.Int(load_default=0)


class UpdateInvoiceSchema(Schema):
    """Schema for invoice update."""
    status = fields.Str(validate=validate.OneOf(["paid", "cancelled", "expired"]))
    payment_ref = fields.Str()


filter_schema = InvoiceFilterSchema()
update_schema = UpdateInvoiceSchema()


@admin_invoices_bp.route("", methods=["GET"])
@require_auth
@require_admin
@inject
def list_invoices(
    invoice_service=Provide[Container.invoice_service],
):
    """
    List all invoices with filters.

    GET /api/v1/admin/invoices?status=paid&user_id=123
    Authorization: Bearer <admin_token>
    """
    try:
        params = filter_schema.load(request.args)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    invoices = invoice_service.list_invoices(
        user_id=params.get("user_id"),
        status=params.get("status"),
        limit=params["limit"],
        offset=params["offset"],
    )

    return jsonify({
        "invoices": [i.to_dict() for i in invoices],
    }), 200


@admin_invoices_bp.route("/<int:invoice_id>", methods=["PUT"])
@require_auth
@require_admin
@inject
def update_invoice(
    invoice_id: int,
    invoice_service=Provide[Container.invoice_service],
):
    """
    Manually update invoice status.

    PUT /api/v1/admin/invoices/123
    Authorization: Bearer <admin_token>
    {
        "status": "paid",
        "payment_ref": "MANUAL-123"
    }
    """
    try:
        data = update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    invoice = invoice_service._invoice_repo.find_by_id(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    if data.get("status") == "paid":
        from src.models import PaymentMethod
        invoice = invoice_service.mark_paid(
            invoice_id,
            payment_ref=data.get("payment_ref", "ADMIN-MANUAL"),
            payment_method=PaymentMethod.MANUAL,
        )
    elif data.get("status") == "cancelled":
        invoice = invoice_service.mark_cancelled(invoice_id)
    elif data.get("status") == "expired":
        invoice = invoice_service.mark_expired(invoice_id)

    return jsonify(invoice.to_dict()), 200
```

---

### 5.4 Admin Routes - Tariff Plans

**File:** `python/api/src/routes/admin/tarif_plans.py`

```python
"""Admin tariff plan management routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from marshmallow import Schema, fields, validate, ValidationError
from decimal import Decimal
from src.container import Container
from src.middleware.auth import require_auth, require_admin
from src.models import TarifPlan, BillingPeriod

admin_tarif_plans_bp = Blueprint(
    "admin_tarif_plans", __name__, url_prefix="/admin/tarif-plans"
)


class CreateTarifPlanSchema(Schema):
    """Schema for creating tariff plan."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    slug = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    price = fields.Decimal(required=True, as_string=True)
    currency = fields.Str(load_default="EUR", validate=validate.Length(equal=3))
    billing_period = fields.Str(
        required=True,
        validate=validate.OneOf(["monthly", "quarterly", "yearly", "one_time"]),
    )
    features = fields.List(fields.Str())
    is_active = fields.Bool(load_default=True)
    sort_order = fields.Int(load_default=0)


class UpdateTarifPlanSchema(Schema):
    """Schema for updating tariff plan."""
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    price = fields.Decimal(as_string=True)
    features = fields.List(fields.Str())
    is_active = fields.Bool()
    sort_order = fields.Int()


create_schema = CreateTarifPlanSchema()
update_schema = UpdateTarifPlanSchema()


@admin_tarif_plans_bp.route("", methods=["GET"])
@require_auth
@require_admin
@inject
def list_tarif_plans(
    tarif_plan_service=Provide[Container.tarif_plan_service],
):
    """
    List all tariff plans (including inactive).

    GET /api/v1/admin/tarif-plans
    Authorization: Bearer <admin_token>
    """
    plans = tarif_plan_service._plan_repo.find_all()

    return jsonify({
        "tarif_plans": [p.to_dict() for p in plans],
    }), 200


@admin_tarif_plans_bp.route("", methods=["POST"])
@require_auth
@require_admin
@inject
def create_tarif_plan(
    tarif_plan_service=Provide[Container.tarif_plan_service],
):
    """
    Create new tariff plan.

    POST /api/v1/admin/tarif-plans
    Authorization: Bearer <admin_token>
    {
        "name": "Pro Plan",
        "slug": "pro",
        "price": "29.99",
        "billing_period": "monthly",
        "features": ["Feature A", "Feature B"]
    }
    """
    try:
        data = create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    # Check slug uniqueness
    existing = tarif_plan_service.get_plan_by_slug(data["slug"])
    if existing:
        return jsonify({"error": "Slug already exists"}), 400

    plan = TarifPlan(
        name=data["name"],
        slug=data["slug"],
        description=data.get("description"),
        price=Decimal(data["price"]),
        currency=data["currency"],
        billing_period=BillingPeriod(data["billing_period"]),
        features=data.get("features", []),
        is_active=data["is_active"],
        sort_order=data["sort_order"],
    )

    plan = tarif_plan_service._plan_repo.save(plan)

    return jsonify(plan.to_dict()), 201


@admin_tarif_plans_bp.route("/<int:plan_id>", methods=["PUT"])
@require_auth
@require_admin
@inject
def update_tarif_plan(
    plan_id: int,
    tarif_plan_service=Provide[Container.tarif_plan_service],
):
    """
    Update tariff plan.

    PUT /api/v1/admin/tarif-plans/123
    Authorization: Bearer <admin_token>
    {
        "is_active": false
    }
    """
    try:
        data = update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    plan = tarif_plan_service.get_plan_by_id(plan_id)
    if not plan:
        return jsonify({"error": "Tariff plan not found"}), 404

    # Update fields
    for field in ["name", "description", "features", "is_active", "sort_order"]:
        if field in data:
            setattr(plan, field, data[field])

    if "price" in data:
        plan.price = Decimal(data["price"])

    plan = tarif_plan_service._plan_repo.save(plan)

    return jsonify(plan.to_dict()), 200
```

---

### 5.5 Webhook Routes

**File:** `python/api/src/routes/webhooks.py`

```python
"""Webhook handler routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from src.container import Container

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@webhooks_bp.route("/paypal", methods=["POST"])
@inject
def paypal_webhook(
    payment_service=Provide[Container.payment_service],
):
    """
    PayPal webhook handler.

    POST /api/v1/webhooks/paypal

    PayPal sends events for:
    - CHECKOUT.ORDER.APPROVED
    - PAYMENT.CAPTURE.COMPLETED
    - PAYMENT.CAPTURE.DENIED
    """
    # Get raw payload for signature verification
    payload = request.json
    signature = request.headers.get("PAYPAL-TRANSMISSION-SIG", "")

    try:
        success = payment_service.process_webhook(
            provider="paypal",
            payload=payload,
            signature=signature,
        )

        if success:
            return jsonify({"status": "processed"}), 200
        else:
            return jsonify({"status": "ignored"}), 200

    except Exception as e:
        # Log error but return 200 to prevent PayPal retries
        print(f"PayPal webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 200


@webhooks_bp.route("/stripe", methods=["POST"])
@inject
def stripe_webhook(
    payment_service=Provide[Container.payment_service],
):
    """
    Stripe webhook handler.

    POST /api/v1/webhooks/stripe

    Stripe sends events for:
    - checkout.session.completed
    - checkout.session.expired
    - payment_intent.payment_failed
    """
    payload = request.json
    signature = request.headers.get("Stripe-Signature", "")

    try:
        success = payment_service.process_webhook(
            provider="stripe",
            payload=payload,
            signature=signature,
        )

        if success:
            return jsonify({"status": "processed"}), 200
        else:
            return jsonify({"status": "ignored"}), 200

    except Exception as e:
        # Log error but return 200 to prevent Stripe retries
        print(f"Stripe webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 200
```

---

### 5.6 Background Jobs

**File:** `python/api/src/jobs/expiration_check.py`

```python
"""Background job for checking expirations."""
from datetime import datetime


def check_subscriptions_expiration(app, subscription_service):
    """
    Check and expire subscriptions.

    Should be run via cron or scheduler (e.g., every hour).
    """
    with app.app_context():
        count = subscription_service.check_and_expire_subscriptions()
        print(f"[{datetime.utcnow()}] Expired {count} subscriptions")
        return count


def check_invoices_expiration(app, invoice_service):
    """
    Check and expire pending invoices.

    Should be run via cron or scheduler (e.g., every hour).
    """
    with app.app_context():
        count = invoice_service.expire_pending_invoices()
        print(f"[{datetime.utcnow()}] Expired {count} invoices")
        return count
```

**File:** `python/api/src/jobs/scheduler.py`

```python
"""Job scheduler setup."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.jobs.expiration_check import (
    check_subscriptions_expiration,
    check_invoices_expiration,
)


def setup_scheduler(app, container):
    """
    Setup background job scheduler.

    Runs expiration checks every hour.
    """
    scheduler = BackgroundScheduler()

    # Subscription expiration check - every hour
    scheduler.add_job(
        func=lambda: check_subscriptions_expiration(
            app,
            container.subscription_service(),
        ),
        trigger=IntervalTrigger(hours=1),
        id="subscription_expiration",
        name="Check subscription expirations",
        replace_existing=True,
    )

    # Invoice expiration check - every hour
    scheduler.add_job(
        func=lambda: check_invoices_expiration(
            app,
            container.invoice_service(),
        ),
        trigger=IntervalTrigger(hours=1),
        id="invoice_expiration",
        name="Check invoice expirations",
        replace_existing=True,
    )

    scheduler.start()
    return scheduler
```

---

### 5.7 Admin Blueprint Registration

**File:** `python/api/src/routes/admin/__init__.py`

```python
"""Admin routes package."""
from flask import Blueprint
from src.routes.admin.users import admin_users_bp
from src.routes.admin.subscriptions import admin_subscriptions_bp
from src.routes.admin.invoices import admin_invoices_bp
from src.routes.admin.tarif_plans import admin_tarif_plans_bp

admin_bp = Blueprint("admin", __name__)

admin_bp.register_blueprint(admin_users_bp)
admin_bp.register_blueprint(admin_subscriptions_bp)
admin_bp.register_blueprint(admin_invoices_bp)
admin_bp.register_blueprint(admin_tarif_plans_bp)
```

---

### 5.8 Updated App Factory

**File:** `python/api/src/app.py` (updated)

```python
"""Flask application factory."""
from flask import Flask
from src.container import Container


def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object("src.config.Config")
    if config:
        app.config.update(config)

    # Initialize DI container
    container = Container()
    container.config.from_dict(app.config)
    app.container = container

    # Initialize extensions
    from src.extensions import db
    db.init_app(app)

    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.user import user_bp
    from src.routes.tarif_plans import tarif_plans_bp
    from src.routes.subscriptions import subscriptions_bp
    from src.routes.checkout import checkout_bp
    from src.routes.invoices import invoices_bp
    from src.routes.webhooks import webhooks_bp
    from src.routes.admin import admin_bp

    api_prefix = "/api/v1"
    app.register_blueprint(auth_bp, url_prefix=api_prefix)
    app.register_blueprint(user_bp, url_prefix=api_prefix)
    app.register_blueprint(tarif_plans_bp, url_prefix=api_prefix)
    app.register_blueprint(subscriptions_bp, url_prefix=api_prefix)
    app.register_blueprint(checkout_bp, url_prefix=api_prefix)
    app.register_blueprint(invoices_bp, url_prefix=api_prefix)
    app.register_blueprint(webhooks_bp, url_prefix=api_prefix)
    app.register_blueprint(admin_bp, url_prefix=api_prefix)

    # Health check
    @app.route(f"{api_prefix}/health")
    def health():
        return {"status": "ok"}

    # Setup scheduler (non-test only)
    if not app.config.get("TESTING"):
        from src.jobs.scheduler import setup_scheduler
        setup_scheduler(app, container)

    return app
```

---

## Integration Tests

**File:** `python/api/tests/integration/test_admin_flow.py`

```python
"""Integration tests for admin flow."""
import pytest


class TestAdminUserManagement:
    """Test admin user management."""

    def test_admin_can_list_users(self, client, admin_auth_headers):
        """Admin should be able to list all users."""
        response = client.get(
            "/api/v1/admin/users",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        assert "users" in response.json

    def test_admin_can_suspend_user(self, client, admin_auth_headers, test_user):
        """Admin should be able to suspend user."""
        response = client.put(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"status": "suspended"},
        )

        assert response.status_code == 200
        assert response.json["status"] == "suspended"

    def test_non_admin_cannot_access(self, client, auth_headers):
        """Non-admin should get 403."""
        response = client.get(
            "/api/v1/admin/users",
            headers=auth_headers,
        )

        assert response.status_code == 403


class TestWebhookHandling:
    """Test webhook handlers."""

    def test_stripe_webhook_processes_payment(self, client):
        """Stripe webhook should process payment completion."""
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_intent": "pi_123",
                    "payment_status": "paid",
                    "metadata": {
                        "invoice_id": "1",
                    },
                },
            },
        }

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": "test"},
        )

        assert response.status_code == 200
```

---

## Verification Checklist

```bash
# Run all tests
docker-compose run --rm python pytest -v

# Run admin tests specifically
docker-compose run --rm python pytest tests/integration/test_admin_flow.py -v

# Test admin endpoints
TOKEN=$(# get admin token)

# List users
curl http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN"

# Create tariff plan
curl -X POST http://localhost:5000/api/v1/admin/tarif-plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Enterprise",
    "slug": "enterprise",
    "price": "99.99",
    "billing_period": "monthly",
    "features": ["Unlimited access", "Priority support"]
  }'
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Admin user routes | [ ] | List, get, update |
| Admin subscription routes | [ ] | List, update, extend |
| Admin invoice routes | [ ] | List, update |
| Admin tariff plan routes | [ ] | CRUD |
| PayPal webhook handler | [ ] | Event processing |
| Stripe webhook handler | [ ] | Event processing |
| Background scheduler | [ ] | Expiration checks |
| Integration tests | [ ] | Full admin flow |

---

## Post-Sprint: Production Readiness

After completing all sprints, consider:

1. **Security Audit**
   - Rate limiting on all endpoints
   - Input sanitization review
   - SQL injection testing
   - XSS prevention verification

2. **Performance**
   - Database query optimization
   - Connection pooling configuration
   - Caching strategy (Redis)

3. **Monitoring**
   - Logging configuration
   - Error tracking (Sentry)
   - Metrics collection

4. **Documentation**
   - API documentation (OpenAPI/Swagger)
   - Deployment guide
   - Operations runbook

---

## API Summary

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/tarif-plans` | GET | List tariff plans |
| `/api/v1/tarif-plans/{slug}` | GET | Get tariff plan |

### User Endpoints (Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/user/profile` | GET | Get profile |
| `/api/v1/user/details` | GET/PUT | User details |
| `/api/v1/user/subscriptions` | GET | List subscriptions |
| `/api/v1/user/subscriptions/active` | GET | Active subscription |
| `/api/v1/user/invoices` | GET | List invoices |
| `/api/v1/checkout/create` | POST | Create checkout |
| `/api/v1/checkout/confirm` | POST | Confirm payment |

### Admin Endpoints (Admin Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/users` | GET | List users |
| `/api/v1/admin/users/{id}` | GET/PUT | User management |
| `/api/v1/admin/subscriptions` | GET | List subscriptions |
| `/api/v1/admin/subscriptions/{id}` | PUT | Update subscription |
| `/api/v1/admin/invoices` | GET | List invoices |
| `/api/v1/admin/invoices/{id}` | PUT | Update invoice |
| `/api/v1/admin/tarif-plans` | GET/POST | Tariff plans |
| `/api/v1/admin/tarif-plans/{id}` | PUT | Update plan |

### Webhook Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/webhooks/paypal` | POST | PayPal webhooks |
| `/api/v1/webhooks/stripe` | POST | Stripe webhooks |
