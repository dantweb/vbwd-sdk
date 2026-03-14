# Sprint 07: Backend Token Bundles & Add-ons E2E Tests

**Date:** 2026-01-13
**Priority:** High
**Type:** Backend Testing + Implementation
**Section:** Token Bundles & Add-ons
**Prerequisite:** None (can run in parallel with checkout sprints)

## Goal

1. Verify token bundles backend works correctly (already exists)
2. Implement add-ons backend following the tarif plans pattern
3. Write E2E tests for both token bundles and add-ons admin APIs

## Known Issues

### Issue 1: Token Bundles API Returns 500 Error - FIXED
**URL:** `http://localhost:8081/admin/settings` (Tokens tab)
**API Call:** `GET /api/v1/admin/token-bundles?page=1&per_page=20&include_inactive=true`
**Error:** 500 Internal Server Error
**Root Cause:** Missing database migration for `token_bundle` table
**Fix:** Created migration `20260113_add_token_bundle_table.py` and ran `alembic upgrade head`
**Status:** RESOLVED

### Issue 2: Settings Endpoint Not Found
**API Call:** `GET /api/v1/admin/settings`
**Error:** 404 Not Found
**Note:** Frontend expects this endpoint but it doesn't exist in backend (low priority)

---

## Current State

### Token Bundles (EXISTS)
- **Model:** `vbwd-backend/src/models/token_bundle.py`
- **Repository:** `vbwd-backend/src/repositories/token_bundle_repository.py`
- **Routes:** `vbwd-backend/src/routes/admin/token_bundles.py`

```python
# Existing TokenBundle model
class TokenBundle(BaseModel):
    name: str
    description: str
    token_amount: int
    price: Decimal
    is_active: bool
    sort_order: int
```

### Add-ons (NOT IMPLEMENTED)
- Frontend placeholder exists: `vbwd-frontend/admin/vue/src/views/AddOns.vue`
- Backend needs: Model, Repository, Service, Routes

## Add-on Design (Following TarifPlan Pattern)

Add-ons are optional extras that can be attached to subscriptions.
They use a JSON `config` field for flexible parameters (same as tarif plans use `features`).

### Add-on Model Structure

```python
class AddOn(BaseModel):
    """Optional extras that can be added to subscriptions."""

    # Basic info
    name: str                    # "Priority Support"
    slug: str                    # "priority-support" (unique, indexed)
    description: str             # Detailed description

    # Pricing
    price: Decimal               # Base price
    currency: str = "EUR"        # Currency code
    billing_period: BillingPeriod  # monthly, yearly, one_time

    # Configuration (flexible JSON like tarif_plan.features)
    config: dict = {}            # JSON configuration

    # Status
    is_active: bool = True       # Available for purchase
    sort_order: int = 0          # Display order

    # Relationships
    addon_subscriptions: List[AddOnSubscription]
```

### Config JSON Examples

```json
// Priority Support Add-on
{
    "type": "support",
    "response_time_hours": 4,
    "channels": ["email", "chat", "phone"],
    "24x7": true
}

// Extra Storage Add-on
{
    "type": "storage",
    "storage_gb": 100,
    "bandwidth_gb": 500
}

// API Rate Limit Add-on
{
    "type": "api",
    "requests_per_minute": 1000,
    "requests_per_day": 100000
}

// White Label Add-on
{
    "type": "branding",
    "custom_domain": true,
    "remove_branding": true,
    "custom_email_templates": true
}
```

---

## Tasks

### Task 7.1: Token Bundles E2E Tests (TDD-First)

**File:** `vbwd-backend/tests/integration/test_admin_token_bundles.py`

```python
"""E2E tests for admin token bundles API."""
import pytest
from uuid import uuid4
from decimal import Decimal

class TestTokenBundlesListEndpoint:
    """Tests for GET /api/v1/admin/token-bundles"""

    def test_list_requires_admin_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/admin/token-bundles")
        assert response.status_code == 401

    def test_list_requires_admin_role(self, client, user_auth_headers):
        """Regular user gets 403."""
        response = client.get("/api/v1/admin/token-bundles", headers=user_auth_headers)
        assert response.status_code == 403

    def test_list_returns_bundles(self, client, admin_headers, test_token_bundle):
        """Admin can list token bundles."""
        response = client.get("/api/v1/admin/token-bundles", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "bundles" in data
        assert len(data["bundles"]) >= 1

    def test_list_includes_inactive_with_param(self, client, admin_headers, inactive_token_bundle):
        """Can include inactive bundles."""
        response = client.get(
            "/api/v1/admin/token-bundles?include_inactive=true",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        inactive_ids = [b["id"] for b in data["bundles"] if not b["is_active"]]
        assert len(inactive_ids) >= 1

    def test_list_pagination(self, client, admin_headers, multiple_token_bundles):
        """Pagination works correctly."""
        response = client.get(
            "/api/v1/admin/token-bundles?page=1&per_page=2",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["bundles"]) <= 2
        assert "total" in data
        assert "page" in data


class TestTokenBundleCreateEndpoint:
    """Tests for POST /api/v1/admin/token-bundles"""

    def test_create_requires_admin(self, client, user_auth_headers):
        """Regular user cannot create bundles."""
        response = client.post(
            "/api/v1/admin/token-bundles",
            json={"name": "Test", "token_amount": 100, "price": "10.00"},
            headers=user_auth_headers
        )
        assert response.status_code == 403

    def test_create_bundle_success(self, client, admin_headers):
        """Admin can create token bundle."""
        response = client.post(
            "/api/v1/admin/token-bundles",
            json={
                "name": "1000 Tokens",
                "description": "Starter pack",
                "token_amount": 1000,
                "price": "10.00"
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "1000 Tokens"
        assert data["token_amount"] == 1000
        assert data["is_active"] == True

    def test_create_requires_name(self, client, admin_headers):
        """Name is required."""
        response = client.post(
            "/api/v1/admin/token-bundles",
            json={"token_amount": 100, "price": "10.00"},
            headers=admin_headers
        )
        assert response.status_code == 400
        assert "name" in response.get_json()["error"].lower()

    def test_create_requires_positive_token_amount(self, client, admin_headers):
        """Token amount must be positive."""
        response = client.post(
            "/api/v1/admin/token-bundles",
            json={"name": "Test", "token_amount": 0, "price": "10.00"},
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_create_requires_non_negative_price(self, client, admin_headers):
        """Price must be non-negative."""
        response = client.post(
            "/api/v1/admin/token-bundles",
            json={"name": "Test", "token_amount": 100, "price": "-10.00"},
            headers=admin_headers
        )
        assert response.status_code == 400


class TestTokenBundleUpdateEndpoint:
    """Tests for PUT /api/v1/admin/token-bundles/{id}"""

    def test_update_bundle_success(self, client, admin_headers, test_token_bundle):
        """Admin can update token bundle."""
        response = client.put(
            f"/api/v1/admin/token-bundles/{test_token_bundle.id}",
            json={"name": "Updated Bundle", "token_amount": 2000},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Updated Bundle"
        assert data["token_amount"] == 2000

    def test_update_nonexistent_returns_404(self, client, admin_headers):
        """Updating non-existent bundle returns 404."""
        response = client.put(
            f"/api/v1/admin/token-bundles/{uuid4()}",
            json={"name": "Test"},
            headers=admin_headers
        )
        assert response.status_code == 404


class TestTokenBundleActivation:
    """Tests for activation/deactivation endpoints."""

    def test_deactivate_bundle(self, client, admin_headers, test_token_bundle):
        """Can deactivate bundle."""
        response = client.post(
            f"/api/v1/admin/token-bundles/{test_token_bundle.id}/deactivate",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify deactivated
        get_response = client.get(
            f"/api/v1/admin/token-bundles/{test_token_bundle.id}",
            headers=admin_headers
        )
        assert get_response.get_json()["is_active"] == False

    def test_activate_bundle(self, client, admin_headers, inactive_token_bundle):
        """Can activate bundle."""
        response = client.post(
            f"/api/v1/admin/token-bundles/{inactive_token_bundle.id}/activate",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify activated
        get_response = client.get(
            f"/api/v1/admin/token-bundles/{inactive_token_bundle.id}",
            headers=admin_headers
        )
        assert get_response.get_json()["is_active"] == True


class TestTokenBundleDelete:
    """Tests for DELETE /api/v1/admin/token-bundles/{id}"""

    def test_delete_bundle(self, client, admin_headers, test_token_bundle):
        """Can delete bundle."""
        response = client.delete(
            f"/api/v1/admin/token-bundles/{test_token_bundle.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(
            f"/api/v1/admin/token-bundles/{test_token_bundle.id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404
```

---

### Task 7.2: Create Add-on Model

**File:** `vbwd-backend/src/models/addon.py`

```python
"""Add-on model - optional extras for subscriptions."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Numeric, Boolean, Integer, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel, db
from src.models.enums import BillingPeriod, SubscriptionStatus


class AddOn(BaseModel):
    """Optional extras that can be added to subscriptions."""

    __tablename__ = "addons"

    # Basic info
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=True)

    # Pricing
    price = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    billing_period = Column(String(50), nullable=False, default=BillingPeriod.MONTHLY.value)

    # Flexible configuration (like tarif_plan.features)
    config = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    sort_order = Column(Integer, nullable=False, default=0)

    # Relationships
    addon_subscriptions = relationship("AddOnSubscription", back_populates="addon")

    __table_args__ = (
        Index("ix_addons_active_sort", "is_active", "sort_order"),
    )

    @property
    def is_recurring(self) -> bool:
        """Check if this is a recurring add-on."""
        return self.billing_period != BillingPeriod.ONE_TIME.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price": str(self.price),
            "currency": self.currency,
            "billing_period": self.billing_period,
            "config": self.config,
            "is_active": self.is_active,
            "is_recurring": self.is_recurring,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AddOnSubscription(BaseModel):
    """User subscription to an add-on, linked to parent subscription."""

    __tablename__ = "addon_subscriptions"

    user_id = Column(PGUUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    addon_id = Column(PGUUID(as_uuid=True), db.ForeignKey("addons.id"), nullable=False)
    subscription_id = Column(PGUUID(as_uuid=True), db.ForeignKey("subscriptions.id"), nullable=False)

    status = Column(String(50), nullable=False, default=SubscriptionStatus.PENDING.value)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    addon = relationship("AddOn", back_populates="addon_subscriptions")
    user = relationship("User")
    subscription = relationship("Subscription")

    __table_args__ = (
        Index("ix_addon_subs_user_status", "user_id", "status"),
    )

    @property
    def is_valid(self) -> bool:
        """Check if subscription is currently valid."""
        if self.status != SubscriptionStatus.ACTIVE.value:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def activate(self) -> None:
        """Activate this add-on subscription."""
        self.status = SubscriptionStatus.ACTIVE.value
        self.starts_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel this add-on subscription."""
        self.status = SubscriptionStatus.CANCELLED.value
        self.cancelled_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "addon_id": str(self.addon_id),
            "subscription_id": str(self.subscription_id),
            "status": self.status,
            "is_valid": self.is_valid,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "addon": self.addon.to_dict() if self.addon else None,
        }
```

---

### Task 7.3: Create Add-on Repository

**File:** `vbwd-backend/src/repositories/addon_repository.py`

```python
"""Repository for AddOn model."""
from typing import List, Optional, Tuple
from uuid import UUID

from src.models.addon import AddOn, AddOnSubscription
from src.repositories.base import BaseRepository


class AddOnRepository(BaseRepository[AddOn]):
    """Repository for AddOn CRUD operations."""

    def __init__(self, session):
        super().__init__(AddOn, session)

    def find_by_slug(self, slug: str) -> Optional[AddOn]:
        """Find add-on by slug."""
        return self._session.query(AddOn).filter(AddOn.slug == slug).first()

    def find_active(self) -> List[AddOn]:
        """Find all active add-ons ordered by sort_order."""
        return (
            self._session.query(AddOn)
            .filter(AddOn.is_active == True)
            .order_by(AddOn.sort_order, AddOn.name)
            .all()
        )

    def find_all_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        include_inactive: bool = True
    ) -> Tuple[List[AddOn], int]:
        """Find all add-ons with pagination."""
        query = self._session.query(AddOn)

        if not include_inactive:
            query = query.filter(AddOn.is_active == True)

        total = query.count()
        addons = (
            query
            .order_by(AddOn.sort_order, AddOn.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return addons, total

    def slug_exists(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if slug exists (for validation)."""
        query = self._session.query(AddOn).filter(AddOn.slug == slug)
        if exclude_id:
            query = query.filter(AddOn.id != exclude_id)
        return query.count() > 0


class AddOnSubscriptionRepository(BaseRepository[AddOnSubscription]):
    """Repository for AddOnSubscription CRUD operations."""

    def __init__(self, session):
        super().__init__(AddOnSubscription, session)

    def find_by_user(self, user_id: UUID) -> List[AddOnSubscription]:
        """Find all add-on subscriptions for a user."""
        return (
            self._session.query(AddOnSubscription)
            .filter(AddOnSubscription.user_id == user_id)
            .all()
        )

    def find_active_by_user(self, user_id: UUID) -> List[AddOnSubscription]:
        """Find active add-on subscriptions for a user."""
        return (
            self._session.query(AddOnSubscription)
            .filter(
                AddOnSubscription.user_id == user_id,
                AddOnSubscription.status == "active"
            )
            .all()
        )

    def find_by_subscription(self, subscription_id: UUID) -> List[AddOnSubscription]:
        """Find add-on subscriptions linked to a parent subscription."""
        return (
            self._session.query(AddOnSubscription)
            .filter(AddOnSubscription.subscription_id == subscription_id)
            .all()
        )
```

---

### Task 7.4: Create Add-on Admin Routes

**File:** `vbwd-backend/src/routes/admin/addons.py`

```python
"""Admin routes for add-on management."""
from flask import Blueprint, request, jsonify, current_app
from uuid import UUID

from src.decorators import require_auth, require_admin
from src.utils.slug import generate_slug

addons_admin_bp = Blueprint("admin_addons", __name__, url_prefix="/admin/addons")


@addons_admin_bp.route("", methods=["GET"])
@require_auth
@require_admin
def list_addons():
    """List all add-ons with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    include_inactive = request.args.get("include_inactive", "true").lower() == "true"

    repo = current_app.container.addon_repository()
    addons, total = repo.find_all_paginated(
        page=page,
        per_page=per_page,
        include_inactive=include_inactive
    )

    return jsonify({
        "addons": [a.to_dict() for a in addons],
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200


@addons_admin_bp.route("", methods=["POST"])
@require_auth
@require_admin
def create_addon():
    """Create a new add-on."""
    data = request.get_json() or {}

    # Validation
    name = data.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400

    price = data.get("price")
    if price is None:
        return jsonify({"error": "Price is required"}), 400

    try:
        price = float(price)
        if price < 0:
            return jsonify({"error": "Price must be non-negative"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid price format"}), 400

    # Generate slug if not provided
    slug = data.get("slug") or generate_slug(name)

    # Check slug uniqueness
    repo = current_app.container.addon_repository()
    if repo.slug_exists(slug):
        return jsonify({"error": "Slug already exists"}), 400

    from src.models.addon import AddOn
    addon = AddOn(
        name=name,
        slug=slug,
        description=data.get("description"),
        price=price,
        currency=data.get("currency", "EUR"),
        billing_period=data.get("billing_period", "monthly"),
        config=data.get("config", {}),
        is_active=data.get("is_active", True),
        sort_order=data.get("sort_order", 0)
    )

    addon = repo.save(addon)
    return jsonify(addon.to_dict()), 201


@addons_admin_bp.route("/<addon_id>", methods=["GET"])
@require_auth
@require_admin
def get_addon(addon_id: str):
    """Get a single add-on by ID."""
    repo = current_app.container.addon_repository()
    addon = repo.find_by_id(UUID(addon_id))

    if not addon:
        return jsonify({"error": "Add-on not found"}), 404

    return jsonify(addon.to_dict()), 200


@addons_admin_bp.route("/<addon_id>", methods=["PUT"])
@require_auth
@require_admin
def update_addon(addon_id: str):
    """Update an add-on."""
    repo = current_app.container.addon_repository()
    addon = repo.find_by_id(UUID(addon_id))

    if not addon:
        return jsonify({"error": "Add-on not found"}), 404

    data = request.get_json() or {}

    # Update fields
    if "name" in data:
        addon.name = data["name"]
    if "slug" in data:
        if repo.slug_exists(data["slug"], exclude_id=addon.id):
            return jsonify({"error": "Slug already exists"}), 400
        addon.slug = data["slug"]
    if "description" in data:
        addon.description = data["description"]
    if "price" in data:
        addon.price = float(data["price"])
    if "currency" in data:
        addon.currency = data["currency"]
    if "billing_period" in data:
        addon.billing_period = data["billing_period"]
    if "config" in data:
        addon.config = data["config"]
    if "is_active" in data:
        addon.is_active = data["is_active"]
    if "sort_order" in data:
        addon.sort_order = data["sort_order"]

    addon = repo.save(addon)
    return jsonify(addon.to_dict()), 200


@addons_admin_bp.route("/<addon_id>", methods=["DELETE"])
@require_auth
@require_admin
def delete_addon(addon_id: str):
    """Delete an add-on."""
    repo = current_app.container.addon_repository()
    addon = repo.find_by_id(UUID(addon_id))

    if not addon:
        return jsonify({"error": "Add-on not found"}), 404

    # Check for active subscriptions
    addon_sub_repo = current_app.container.addon_subscription_repository()
    active_subs = addon_sub_repo.find_active_by_addon(UUID(addon_id))
    if active_subs:
        return jsonify({
            "error": "Cannot delete add-on with active subscriptions"
        }), 400

    repo.delete(addon.id)
    return jsonify({"message": "Add-on deleted"}), 200


@addons_admin_bp.route("/<addon_id>/activate", methods=["POST"])
@require_auth
@require_admin
def activate_addon(addon_id: str):
    """Activate an add-on."""
    repo = current_app.container.addon_repository()
    addon = repo.find_by_id(UUID(addon_id))

    if not addon:
        return jsonify({"error": "Add-on not found"}), 404

    addon.is_active = True
    addon = repo.save(addon)
    return jsonify(addon.to_dict()), 200


@addons_admin_bp.route("/<addon_id>/deactivate", methods=["POST"])
@require_auth
@require_admin
def deactivate_addon(addon_id: str):
    """Deactivate an add-on."""
    repo = current_app.container.addon_repository()
    addon = repo.find_by_id(UUID(addon_id))

    if not addon:
        return jsonify({"error": "Add-on not found"}), 404

    addon.is_active = False
    addon = repo.save(addon)
    return jsonify(addon.to_dict()), 200
```

---

### Task 7.5: Add-ons E2E Tests (TDD-First)

**File:** `vbwd-backend/tests/integration/test_admin_addons.py`

```python
"""E2E tests for admin add-ons API."""
import pytest
from uuid import uuid4

class TestAddOnsListEndpoint:
    """Tests for GET /api/v1/admin/addons"""

    def test_list_requires_admin_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/admin/addons")
        assert response.status_code == 401

    def test_list_requires_admin_role(self, client, user_auth_headers):
        """Regular user gets 403."""
        response = client.get("/api/v1/admin/addons", headers=user_auth_headers)
        assert response.status_code == 403

    def test_list_returns_addons(self, client, admin_headers, test_addon):
        """Admin can list add-ons."""
        response = client.get("/api/v1/admin/addons", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "addons" in data
        assert len(data["addons"]) >= 1

    def test_list_pagination(self, client, admin_headers, multiple_addons):
        """Pagination works correctly."""
        response = client.get(
            "/api/v1/admin/addons?page=1&per_page=2",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["addons"]) <= 2
        assert "total" in data


class TestAddOnCreateEndpoint:
    """Tests for POST /api/v1/admin/addons"""

    def test_create_addon_success(self, client, admin_headers):
        """Admin can create add-on."""
        response = client.post(
            "/api/v1/admin/addons",
            json={
                "name": "Priority Support",
                "description": "24/7 priority support",
                "price": "15.00",
                "billing_period": "monthly",
                "config": {
                    "type": "support",
                    "response_time_hours": 4,
                    "channels": ["email", "chat", "phone"]
                }
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Priority Support"
        assert data["slug"] == "priority-support"
        assert data["config"]["response_time_hours"] == 4
        assert data["is_active"] == True

    def test_create_requires_name(self, client, admin_headers):
        """Name is required."""
        response = client.post(
            "/api/v1/admin/addons",
            json={"price": "10.00"},
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_create_requires_price(self, client, admin_headers):
        """Price is required."""
        response = client.post(
            "/api/v1/admin/addons",
            json={"name": "Test Add-on"},
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_create_with_custom_slug(self, client, admin_headers):
        """Can provide custom slug."""
        response = client.post(
            "/api/v1/admin/addons",
            json={
                "name": "Extra Storage",
                "slug": "storage-100gb",
                "price": "20.00",
                "config": {"storage_gb": 100}
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        assert response.get_json()["slug"] == "storage-100gb"

    def test_create_duplicate_slug_fails(self, client, admin_headers, test_addon):
        """Duplicate slug returns error."""
        response = client.post(
            "/api/v1/admin/addons",
            json={
                "name": "Another Add-on",
                "slug": test_addon.slug,  # Duplicate
                "price": "10.00"
            },
            headers=admin_headers
        )
        assert response.status_code == 400
        assert "slug" in response.get_json()["error"].lower()

    def test_create_with_one_time_billing(self, client, admin_headers):
        """Can create one-time add-on."""
        response = client.post(
            "/api/v1/admin/addons",
            json={
                "name": "Setup Fee",
                "price": "50.00",
                "billing_period": "one_time",
                "config": {"type": "fee"}
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["billing_period"] == "one_time"
        assert data["is_recurring"] == False


class TestAddOnUpdateEndpoint:
    """Tests for PUT /api/v1/admin/addons/{id}"""

    def test_update_addon_success(self, client, admin_headers, test_addon):
        """Admin can update add-on."""
        response = client.put(
            f"/api/v1/admin/addons/{test_addon.id}",
            json={
                "name": "Updated Add-on",
                "price": "25.00",
                "config": {"updated": True}
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Updated Add-on"
        assert data["config"]["updated"] == True

    def test_update_nonexistent_returns_404(self, client, admin_headers):
        """Updating non-existent add-on returns 404."""
        response = client.put(
            f"/api/v1/admin/addons/{uuid4()}",
            json={"name": "Test"},
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_update_config_merges(self, client, admin_headers, test_addon):
        """Config can be updated."""
        response = client.put(
            f"/api/v1/admin/addons/{test_addon.id}",
            json={"config": {"new_field": "new_value"}}
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.get_json()["config"]["new_field"] == "new_value"


class TestAddOnActivation:
    """Tests for activation/deactivation endpoints."""

    def test_deactivate_addon(self, client, admin_headers, test_addon):
        """Can deactivate add-on."""
        response = client.post(
            f"/api/v1/admin/addons/{test_addon.id}/deactivate",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.get_json()["is_active"] == False

    def test_activate_addon(self, client, admin_headers, inactive_addon):
        """Can activate add-on."""
        response = client.post(
            f"/api/v1/admin/addons/{inactive_addon.id}/activate",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.get_json()["is_active"] == True


class TestAddOnDelete:
    """Tests for DELETE /api/v1/admin/addons/{id}"""

    def test_delete_addon(self, client, admin_headers, test_addon):
        """Can delete add-on without subscriptions."""
        response = client.delete(
            f"/api/v1/admin/addons/{test_addon.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(
            f"/api/v1/admin/addons/{test_addon.id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404

    def test_delete_addon_with_subscriptions_fails(self, client, admin_headers, addon_with_subscription):
        """Cannot delete add-on with active subscriptions."""
        response = client.delete(
            f"/api/v1/admin/addons/{addon_with_subscription.id}",
            headers=admin_headers
        )
        assert response.status_code == 400
        assert "subscription" in response.get_json()["error"].lower()


class TestAddOnConfigValidation:
    """Tests for config JSON validation."""

    def test_config_supports_nested_objects(self, client, admin_headers):
        """Config can contain nested objects."""
        response = client.post(
            "/api/v1/admin/addons",
            json={
                "name": "Complex Add-on",
                "price": "10.00",
                "config": {
                    "limits": {
                        "storage_gb": 100,
                        "bandwidth_gb": 500
                    },
                    "features": ["feature1", "feature2"],
                    "enabled": True
                }
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        config = response.get_json()["config"]
        assert config["limits"]["storage_gb"] == 100
        assert len(config["features"]) == 2

    def test_config_empty_is_allowed(self, client, admin_headers):
        """Empty config is valid."""
        response = client.post(
            "/api/v1/admin/addons",
            json={
                "name": "Simple Add-on",
                "price": "5.00",
                "config": {}
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        assert response.get_json()["config"] == {}
```

---

### Task 7.6: Create Test Fixtures

**File:** `vbwd-backend/tests/fixtures/addon_fixtures.py`

```python
"""Fixtures for add-on and token bundle tests."""
import pytest
from uuid import uuid4
from decimal import Decimal

@pytest.fixture
def test_addon(db_session):
    """Create a test add-on."""
    from src.models.addon import AddOn
    addon = AddOn(
        id=uuid4(),
        name="Test Support",
        slug="test-support",
        description="Test support add-on",
        price=Decimal("15.00"),
        currency="EUR",
        billing_period="monthly",
        config={"type": "support", "response_hours": 24},
        is_active=True,
        sort_order=0
    )
    db_session.add(addon)
    db_session.commit()
    return addon

@pytest.fixture
def inactive_addon(db_session):
    """Create an inactive add-on."""
    from src.models.addon import AddOn
    addon = AddOn(
        id=uuid4(),
        name="Inactive Add-on",
        slug="inactive-addon",
        price=Decimal("10.00"),
        is_active=False
    )
    db_session.add(addon)
    db_session.commit()
    return addon

@pytest.fixture
def multiple_addons(db_session):
    """Create multiple add-ons for pagination tests."""
    from src.models.addon import AddOn
    addons = []
    for i in range(5):
        addon = AddOn(
            id=uuid4(),
            name=f"Add-on {i}",
            slug=f"addon-{i}",
            price=Decimal(f"{10 + i}.00"),
            sort_order=i
        )
        db_session.add(addon)
        addons.append(addon)
    db_session.commit()
    return addons

@pytest.fixture
def addon_with_subscription(db_session, test_addon, test_user, test_subscription):
    """Create add-on with an active subscription."""
    from src.models.addon import AddOnSubscription
    addon_sub = AddOnSubscription(
        id=uuid4(),
        user_id=test_user.id,
        addon_id=test_addon.id,
        subscription_id=test_subscription.id,
        status="active"
    )
    db_session.add(addon_sub)
    db_session.commit()
    return test_addon

@pytest.fixture
def test_token_bundle(db_session):
    """Create a test token bundle."""
    from src.models.token_bundle import TokenBundle
    bundle = TokenBundle(
        id=uuid4(),
        name="1000 Tokens",
        description="Starter pack",
        token_amount=1000,
        price=Decimal("10.00"),
        is_active=True
    )
    db_session.add(bundle)
    db_session.commit()
    return bundle

@pytest.fixture
def inactive_token_bundle(db_session):
    """Create an inactive token bundle."""
    from src.models.token_bundle import TokenBundle
    bundle = TokenBundle(
        id=uuid4(),
        name="Inactive Bundle",
        token_amount=500,
        price=Decimal("5.00"),
        is_active=False
    )
    db_session.add(bundle)
    db_session.commit()
    return bundle

@pytest.fixture
def multiple_token_bundles(db_session):
    """Create multiple bundles for pagination tests."""
    from src.models.token_bundle import TokenBundle
    bundles = []
    for i in range(5):
        bundle = TokenBundle(
            id=uuid4(),
            name=f"{(i+1)*1000} Tokens",
            token_amount=(i+1)*1000,
            price=Decimal(f"{(i+1)*10}.00"),
            sort_order=i
        )
        db_session.add(bundle)
        bundles.append(bundle)
    db_session.commit()
    return bundles
```

---

### Task 7.7: Create Database Migration

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose exec api flask db migrate -m "Add addons and addon_subscriptions tables"
docker-compose exec api flask db upgrade
```

---

### Task 7.8: Register Routes and Repositories

**File:** `vbwd-backend/src/app.py` (update)

```python
# Register addon routes
from src.routes.admin.addons import addons_admin_bp
app.register_blueprint(addons_admin_bp, url_prefix="/api/v1")

# In container setup
addon_repository = providers.Factory(
    AddOnRepository,
    session=session
)
addon_subscription_repository = providers.Factory(
    AddOnSubscriptionRepository,
    session=session
)
```

---

### Task 7.9: Run All Tests

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run token bundle tests
docker-compose run --rm test pytest tests/integration/test_admin_token_bundles.py -v

# Run addon tests
docker-compose run --rm test pytest tests/integration/test_admin_addons.py -v

# Run all tests
docker-compose run --rm test pytest tests/ -v
```

---

## Build & Test Commands

**IMPORTANT:** Always rebuild and run tests after making changes.

### Rebuild Backend
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Rebuild and restart services
make up-build
```

### Run Tests with Pre-Commit Script
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run all quality checks (lint + unit + integration)
./bin/pre-commit-check.sh

# Quick check (skip integration tests)
./bin/pre-commit-check.sh --quick

# Only run specific checks
./bin/pre-commit-check.sh --lint        # Static analysis only (black, flake8, mypy)
./bin/pre-commit-check.sh --unit        # Unit tests only
./bin/pre-commit-check.sh --integration # Integration tests only
```

---

## Definition of Done

- [ ] Token bundle E2E tests written and passing
- [ ] AddOn model created
- [ ] AddOnSubscription model created
- [ ] AddOn repository created
- [ ] Admin add-on routes created
- [ ] Add-on E2E tests written and passing
- [ ] Database migrations applied
- [ ] Routes registered in app
- [ ] All tests pass
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 7.1 Token Bundle Tests | ⏳ Pending | TDD-First |
| 7.2 AddOn Model | ⏳ Pending | |
| 7.3 AddOn Repository | ⏳ Pending | |
| 7.4 Admin Routes | ⏳ Pending | |
| 7.5 AddOn Tests | ⏳ Pending | TDD-First |
| 7.6 Test Fixtures | ⏳ Pending | |
| 7.7 Migration | ⏳ Pending | |
| 7.8 Register Routes | ⏳ Pending | |
| 7.9 Run Tests | ⏳ Pending | |

---

## Add-on Config Examples

### Support Add-on
```json
{
    "type": "support",
    "response_time_hours": 4,
    "channels": ["email", "chat", "phone"],
    "24x7": true,
    "dedicated_manager": false
}
```

### Storage Add-on
```json
{
    "type": "storage",
    "storage_gb": 100,
    "bandwidth_gb": 500,
    "cdn_enabled": true
}
```

### API Limits Add-on
```json
{
    "type": "api",
    "requests_per_minute": 1000,
    "requests_per_day": 100000,
    "rate_limit_bypass": false
}
```

### White Label Add-on
```json
{
    "type": "branding",
    "custom_domain": true,
    "remove_branding": true,
    "custom_email_templates": true,
    "custom_colors": true
}
```

### Team Add-on
```json
{
    "type": "team",
    "additional_seats": 5,
    "role_management": true,
    "audit_log": true
}
```
