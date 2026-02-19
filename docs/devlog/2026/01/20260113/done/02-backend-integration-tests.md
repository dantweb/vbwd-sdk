# Sprint 02: Backend Integration Tests (TDD-First)

**Date:** 2026-01-13
**Priority:** High
**Type:** Backend Testing
**Section:** User Checkout Flow
**Prerequisite:** None
**Blocks:** Sprint 03, 04 (Backend Implementation)

## Goal

Write pytest integration tests for the checkout API BEFORE implementation.
These tests define the expected API behavior and will initially FAIL.

**TDD Principle:** Tests are the specification. Implementation makes them pass.

## Tasks

### Task 2.1: Create Test Fixtures

**File:** `vbwd-backend/tests/fixtures/checkout_fixtures.py`

```python
"""Fixtures for checkout tests."""
import pytest
from uuid import uuid4
from decimal import Decimal

@pytest.fixture
def test_plan(db_session):
    """Create a test tarif plan."""
    from src.models.tarif_plan import TarifPlan
    plan = TarifPlan(
        id=uuid4(),
        name="Pro Plan",
        slug="pro",
        price=Decimal("29.00"),
        currency="USD",
        billing_period="monthly",
        is_active=True
    )
    db_session.add(plan)
    db_session.commit()
    return plan

@pytest.fixture
def test_token_bundle(db_session):
    """Create a test token bundle."""
    from src.models.token_bundle import TokenBundle
    bundle = TokenBundle(
        id=uuid4(),
        name="1000 Tokens",
        token_amount=1000,
        price=Decimal("10.00"),
        is_active=True
    )
    db_session.add(bundle)
    db_session.commit()
    return bundle

@pytest.fixture
def test_addon(db_session):
    """Create a test add-on."""
    from src.models.addon import AddOn
    addon = AddOn(
        id=uuid4(),
        name="Priority Support",
        description="24/7 priority support",
        price=Decimal("15.00"),
        billing_period="monthly",
        is_active=True
    )
    db_session.add(addon)
    db_session.commit()
    return addon

@pytest.fixture
def pending_checkout(client, auth_headers, test_plan):
    """Create a pending checkout (subscription + invoice)."""
    response = client.post(
        "/api/v1/user/checkout",
        json={"plan_id": str(test_plan.id)},
        headers=auth_headers
    )
    return response.get_json()

@pytest.fixture
def pending_checkout_with_bundle(client, auth_headers, test_plan, test_token_bundle):
    """Create a pending checkout with token bundle."""
    response = client.post(
        "/api/v1/user/checkout",
        json={
            "plan_id": str(test_plan.id),
            "token_bundle_ids": [str(test_token_bundle.id)]
        },
        headers=auth_headers
    )
    return response.get_json()

@pytest.fixture
def pending_checkout_with_addon(client, auth_headers, test_plan, test_addon):
    """Create a pending checkout with add-on."""
    response = client.post(
        "/api/v1/user/checkout",
        json={
            "plan_id": str(test_plan.id),
            "add_on_ids": [str(test_addon.id)]
        },
        headers=auth_headers
    )
    return response.get_json()
```

---

### Task 2.2: Checkout Endpoint Tests

**File:** `vbwd-backend/tests/integration/test_checkout_endpoint.py`

```python
"""Integration tests for POST /api/v1/user/checkout endpoint."""
import pytest
from uuid import uuid4

class TestCheckoutEndpointAuth:
    """Authentication tests for checkout endpoint."""

    def test_checkout_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(uuid4())}
        )
        assert response.status_code == 401

    def test_checkout_with_invalid_token(self, client):
        """Invalid token returns 401."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(uuid4())},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


class TestCheckoutEndpointValidation:
    """Validation tests for checkout endpoint."""

    def test_checkout_requires_plan_id(self, client, auth_headers):
        """Missing plan_id returns 400."""
        response = client.post(
            "/api/v1/user/checkout",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "plan_id" in response.get_json()["error"].lower()

    def test_checkout_invalid_plan_id_format(self, client, auth_headers):
        """Invalid UUID format returns 400."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": "not-a-uuid"},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_checkout_nonexistent_plan(self, client, auth_headers):
        """Non-existent plan returns 400."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(uuid4())},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "not found" in response.get_json()["error"].lower()

    def test_checkout_inactive_plan(self, client, auth_headers, inactive_plan):
        """Inactive plan returns 400."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(inactive_plan.id)},
            headers=auth_headers
        )
        assert response.status_code == 400


class TestCheckoutEndpointSuccess:
    """Success tests for checkout endpoint."""

    def test_checkout_creates_pending_subscription(self, client, auth_headers, test_plan):
        """Checkout creates subscription with PENDING status."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(test_plan.id)},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["subscription"]["status"] == "pending"

    def test_checkout_creates_invoice(self, client, auth_headers, test_plan):
        """Checkout creates pending invoice."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(test_plan.id)},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "invoice" in data
        assert data["invoice"]["status"] == "pending"
        assert data["invoice"]["invoice_number"].startswith("INV-")

    def test_checkout_returns_awaiting_payment_message(self, client, auth_headers, test_plan):
        """Checkout returns message about awaiting payment."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(test_plan.id)},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "awaiting payment" in data["message"].lower()

    def test_checkout_invoice_has_subscription_line_item(self, client, auth_headers, test_plan):
        """Invoice contains subscription as line item."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(test_plan.id)},
            headers=auth_headers
        )
        data = response.get_json()
        line_items = data["invoice"]["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["type"] == "subscription"
```

---

### Task 2.3: Token Bundle Checkout Tests

**File:** `vbwd-backend/tests/integration/test_checkout_token_bundles.py`

```python
"""Integration tests for checkout with token bundles."""
import pytest
from uuid import uuid4

class TestCheckoutWithTokenBundles:
    """Tests for adding token bundles to checkout."""

    def test_checkout_with_single_bundle(self, client, auth_headers, test_plan, test_token_bundle):
        """Can add single token bundle to checkout."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(test_token_bundle.id)]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert len(data["token_bundles"]) == 1
        assert data["token_bundles"][0]["status"] == "pending"

    def test_checkout_with_multiple_bundles(self, client, auth_headers, test_plan, test_token_bundle, test_token_bundle_large):
        """Can add multiple token bundles to checkout."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [
                    str(test_token_bundle.id),
                    str(test_token_bundle_large.id)
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert len(data["token_bundles"]) == 2

    def test_checkout_bundle_appears_in_invoice(self, client, auth_headers, test_plan, test_token_bundle):
        """Token bundle appears as invoice line item."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(test_token_bundle.id)]
            },
            headers=auth_headers
        )
        data = response.get_json()
        line_items = data["invoice"]["line_items"]
        bundle_items = [i for i in line_items if i["type"] == "token_bundle"]
        assert len(bundle_items) == 1

    def test_checkout_invalid_bundle_id(self, client, auth_headers, test_plan):
        """Invalid bundle ID returns error."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(uuid4())]
            },
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_checkout_inactive_bundle(self, client, auth_headers, test_plan, inactive_bundle):
        """Inactive bundle returns error."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(inactive_bundle.id)]
            },
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_checkout_bundle_not_credited_before_payment(self, client, auth_headers, test_plan, test_token_bundle, test_user):
        """Tokens not credited until payment."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(test_token_bundle.id)]
            },
            headers=auth_headers
        )
        assert response.status_code == 201

        # Check balance is still 0
        balance_response = client.get(
            "/api/v1/user/tokens/balance",
            headers=auth_headers
        )
        assert balance_response.get_json()["balance"] == 0
```

---

### Task 2.4: Add-on Checkout Tests

**File:** `vbwd-backend/tests/integration/test_checkout_addons.py`

```python
"""Integration tests for checkout with add-ons."""
import pytest
from uuid import uuid4

class TestCheckoutWithAddons:
    """Tests for adding add-ons to checkout."""

    def test_checkout_with_single_addon(self, client, auth_headers, test_plan, test_addon):
        """Can add single add-on to checkout."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "add_on_ids": [str(test_addon.id)]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert len(data["add_ons"]) == 1
        assert data["add_ons"][0]["status"] == "pending"

    def test_checkout_with_multiple_addons(self, client, auth_headers, test_plan, test_addon, test_addon_premium):
        """Can add multiple add-ons to checkout."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "add_on_ids": [
                    str(test_addon.id),
                    str(test_addon_premium.id)
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert len(data["add_ons"]) == 2

    def test_checkout_addon_appears_in_invoice(self, client, auth_headers, test_plan, test_addon):
        """Add-on appears as invoice line item."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "add_on_ids": [str(test_addon.id)]
            },
            headers=auth_headers
        )
        data = response.get_json()
        line_items = data["invoice"]["line_items"]
        addon_items = [i for i in line_items if i["type"] == "add_on"]
        assert len(addon_items) == 1

    def test_checkout_addon_linked_to_subscription(self, client, auth_headers, test_plan, test_addon):
        """Add-on is linked to parent subscription."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "add_on_ids": [str(test_addon.id)]
            },
            headers=auth_headers
        )
        data = response.get_json()
        assert data["add_ons"][0]["subscription_id"] == data["subscription"]["id"]

    def test_checkout_invalid_addon_id(self, client, auth_headers, test_plan):
        """Invalid add-on ID returns error."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "add_on_ids": [str(uuid4())]
            },
            headers=auth_headers
        )
        assert response.status_code == 400
```

---

### Task 2.5: Invoice Total Calculation Tests

**File:** `vbwd-backend/tests/integration/test_checkout_invoice_total.py`

```python
"""Integration tests for invoice total calculation."""
import pytest
from decimal import Decimal

class TestInvoiceTotalCalculation:
    """Tests for invoice total with multiple items."""

    def test_invoice_total_subscription_only(self, client, auth_headers, test_plan):
        """Invoice total equals plan price."""
        response = client.post(
            "/api/v1/user/checkout",
            json={"plan_id": str(test_plan.id)},
            headers=auth_headers
        )
        data = response.get_json()
        assert Decimal(data["invoice"]["total_amount"]) == test_plan.price

    def test_invoice_total_with_bundle(self, client, auth_headers, test_plan, test_token_bundle):
        """Invoice total includes bundle price."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(test_token_bundle.id)]
            },
            headers=auth_headers
        )
        data = response.get_json()
        expected_total = test_plan.price + test_token_bundle.price
        assert Decimal(data["invoice"]["total_amount"]) == expected_total

    def test_invoice_total_with_addon(self, client, auth_headers, test_plan, test_addon):
        """Invoice total includes add-on price."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "add_on_ids": [str(test_addon.id)]
            },
            headers=auth_headers
        )
        data = response.get_json()
        expected_total = test_plan.price + test_addon.price
        assert Decimal(data["invoice"]["total_amount"]) == expected_total

    def test_invoice_total_all_items(self, client, auth_headers, test_plan, test_token_bundle, test_addon):
        """Invoice total includes all items."""
        response = client.post(
            "/api/v1/user/checkout",
            json={
                "plan_id": str(test_plan.id),
                "token_bundle_ids": [str(test_token_bundle.id)],
                "add_on_ids": [str(test_addon.id)]
            },
            headers=auth_headers
        )
        data = response.get_json()
        expected_total = test_plan.price + test_token_bundle.price + test_addon.price
        assert Decimal(data["invoice"]["total_amount"]) == expected_total
        assert len(data["invoice"]["line_items"]) == 3
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

### Run Pytest Directly
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run all checkout tests
docker-compose run --rm test pytest tests/integration/test_checkout*.py -v

# Run with coverage
docker-compose run --rm test pytest tests/integration/test_checkout*.py -v --cov=src
```

---

## Run Tests (Expected: ALL FAIL)

**Expected Result:** All tests should FAIL because:
1. Checkout endpoint not implemented
2. Token bundle models don't exist
3. Add-on models don't exist
4. Event handlers not implemented

---

## Definition of Done

- [ ] Test fixtures created
- [ ] Checkout endpoint auth tests written
- [ ] Checkout endpoint validation tests written
- [ ] Checkout success tests written
- [ ] Token bundle tests written
- [ ] Add-on tests written
- [ ] Invoice total tests written
- [ ] All tests run (and FAIL as expected)
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Test Fixtures | ⏳ Pending | |
| 2.2 Checkout Endpoint Tests | ⏳ Pending | |
| 2.3 Token Bundle Tests | ⏳ Pending | |
| 2.4 Add-on Tests | ⏳ Pending | |
| 2.5 Invoice Total Tests | ⏳ Pending | |

---

## Next Sprint

After this sprint, proceed to:
- **Sprint 03:** Backend Checkout Implementation (Events & Handlers)
