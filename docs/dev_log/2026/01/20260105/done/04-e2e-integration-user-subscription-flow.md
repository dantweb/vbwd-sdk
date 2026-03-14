# Sprint: E2E & Integration Tests - User Subscription Flow

**Date:** 2026-01-05
**Priority:** High
**Type:** Testing
**Methodology:** TDD-First, Event-Driven, SOLID, Liskov, DI, Clean Code

---

## Objective

Create comprehensive tests for the complete user-subscription-invoice flow:
1. **Playwright E2E Tests** - Admin creates user, assigns subscription, verifies invoice
2. **Python Integration Tests** - Backend API endpoints with event verification

---

## Data Models Reference

### User Model
```python
class User(BaseModel):
    email: str                    # Required, unique
    password_hash: str            # Required
    status: UserStatus            # PENDING | ACTIVE | SUSPENDED | DELETED
    role: UserRole                # USER | ADMIN | VENDOR
```

### UserDetails Model
```python
class UserDetails(BaseModel):
    user_id: UUID                 # FK to User
    first_name: str               # Optional
    last_name: str                # Optional
    address_line_1: str           # Optional
    address_line_2: str           # Optional
    city: str                     # Optional
    postal_code: str              # Optional
    country: str                  # ISO 3166-1 alpha-2 (e.g., "DE", "US")
    phone: str                    # Optional
```

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

### Invoice Model
```python
class UserInvoice(BaseModel):
    user_id: UUID                 # FK to User
    tarif_plan_id: UUID           # FK to TarifPlan
    subscription_id: UUID         # FK to Subscription
    invoice_number: str           # Unique, e.g., "INV-20260105120000-A1B2C3"
    amount: Decimal               # Invoice amount
    currency: str                 # Default "EUR"
    status: InvoiceStatus         # PENDING | PAID | FAILED | CANCELLED | REFUNDED
    payment_method: str           # Optional
    payment_ref: str              # Optional
    invoiced_at: datetime         # When invoice was created
    paid_at: datetime             # Optional
    expires_at: datetime          # Optional
```

---

## Part 1: Playwright E2E Tests

### Test File: `admin-user-subscription-flow.spec.ts`

**Location:** `vbwd-frontend/admin/vue/tests/e2e/`

### Test Scenario

```gherkin
Feature: Admin creates user and subscription
  As an admin
  I want to create a new user with subscription
  So that the user can access paid features

  Scenario: Complete user-subscription-invoice flow
    Given I am logged in as admin
    When I create a new user with all details
    And I create a subscription for the user
    Then an invoice should be created with status "pending"
```

### Test Implementation

```typescript
// tests/e2e/admin-user-subscription-flow.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Admin User-Subscription-Invoice Flow', () => {
  // Test data
  const testUser = {
    email: `test.user.${Date.now()}@example.com`,
    password: 'TestPass123@',
    firstName: 'John',
    lastName: 'Doe',
    addressLine1: 'Hauptstraße 123',
    addressLine2: 'Apt 4B',
    city: 'Berlin',
    postalCode: '10115',
    country: 'DE',
    phone: '+49 30 12345678',
  };

  let createdUserId: string;
  let createdSubscriptionId: string;

  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'AdminPass123@');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');
  });

  test('Step 1: Navigate to Users page', async ({ page }) => {
    await page.click('a[href="/users"]');
    await expect(page).toHaveURL('/users');
    await expect(page.locator('h1')).toContainText('Users');
  });

  test('Step 2: Create new user with all fields', async ({ page }) => {
    // Navigate to users
    await page.goto('/users');

    // Click "Create User" button
    await page.click('button:has-text("Create User")');
    await expect(page.locator('h2')).toContainText('Create User');

    // Fill User fields
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.selectOption('select[name="status"]', 'active');
    await page.selectOption('select[name="role"]', 'user');

    // Fill UserDetails fields
    await page.fill('input[name="firstName"]', testUser.firstName);
    await page.fill('input[name="lastName"]', testUser.lastName);
    await page.fill('input[name="addressLine1"]', testUser.addressLine1);
    await page.fill('input[name="addressLine2"]', testUser.addressLine2);
    await page.fill('input[name="city"]', testUser.city);
    await page.fill('input[name="postalCode"]', testUser.postalCode);
    await page.selectOption('select[name="country"]', testUser.country);
    await page.fill('input[name="phone"]', testUser.phone);

    // Submit form
    await page.click('button[type="submit"]:has-text("Save")');

    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page).toHaveURL(/\/users\/[\w-]+/);

    // Capture user ID from URL
    const url = page.url();
    createdUserId = url.split('/users/')[1];
  });

  test('Step 3: Verify user details are saved', async ({ page }) => {
    await page.goto(`/users/${createdUserId}`);

    // Verify User fields
    await expect(page.locator('[data-testid="user-email"]')).toContainText(testUser.email);
    await expect(page.locator('[data-testid="user-status"]')).toContainText('active');

    // Verify UserDetails fields
    await expect(page.locator('[data-testid="user-firstName"]')).toContainText(testUser.firstName);
    await expect(page.locator('[data-testid="user-lastName"]')).toContainText(testUser.lastName);
    await expect(page.locator('[data-testid="user-city"]')).toContainText(testUser.city);
    await expect(page.locator('[data-testid="user-country"]')).toContainText(testUser.country);
  });

  test('Step 4: Navigate to Subscriptions page', async ({ page }) => {
    await page.click('a[href="/subscriptions"]');
    await expect(page).toHaveURL('/subscriptions');
    await expect(page.locator('h1')).toContainText('Subscriptions');
  });

  test('Step 5: Create subscription for user', async ({ page }) => {
    await page.goto('/subscriptions');

    // Click "Create Subscription" button
    await page.click('button:has-text("Create Subscription")');
    await expect(page.locator('h2')).toContainText('Create Subscription');

    // Select user
    await page.click('[data-testid="user-select"]');
    await page.fill('[data-testid="user-search"]', testUser.email);
    await page.click(`[data-testid="user-option"]:has-text("${testUser.email}")`);

    // Select plan (first available plan)
    await page.click('[data-testid="plan-select"]');
    await page.click('[data-testid="plan-option"]:first-child');

    // Set start date to now
    const now = new Date().toISOString().split('T')[0];
    await page.fill('input[name="startDate"]', now);

    // Submit form
    await page.click('button[type="submit"]:has-text("Save")');

    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page).toHaveURL(/\/subscriptions\/[\w-]+/);

    // Capture subscription ID
    const url = page.url();
    createdSubscriptionId = url.split('/subscriptions/')[1];
  });

  test('Step 6: Verify subscription is active', async ({ page }) => {
    await page.goto(`/subscriptions/${createdSubscriptionId}`);

    await expect(page.locator('[data-testid="subscription-status"]')).toContainText('active');
    await expect(page.locator('[data-testid="subscription-user"]')).toContainText(testUser.email);
  });

  test('Step 7: Navigate to Invoices and find user invoice', async ({ page }) => {
    await page.click('a[href="/invoices"]');
    await expect(page).toHaveURL('/invoices');

    // Search for user's invoice
    await page.fill('[data-testid="invoice-search"]', testUser.email);
    await page.click('button:has-text("Search")');

    // Verify invoice appears
    await expect(page.locator('table tbody tr').first()).toBeVisible();
  });

  test('Step 8: Verify invoice status is "pending"', async ({ page }) => {
    await page.goto('/invoices');

    // Filter by user email
    await page.fill('[data-testid="invoice-search"]', testUser.email);
    await page.click('button:has-text("Search")');

    // Click on first invoice
    await page.click('table tbody tr:first-child');

    // Verify invoice details
    await expect(page.locator('[data-testid="invoice-status"]')).toContainText('pending');
    await expect(page.locator('[data-testid="invoice-user"]')).toContainText(testUser.email);
    await expect(page.locator('[data-testid="invoice-amount"]')).toBeVisible();
  });

  test.afterAll(async ({ request }) => {
    // Cleanup: Delete test user via API
    if (createdUserId) {
      await request.delete(`/api/v1/admin/users/${createdUserId}`);
    }
  });
});
```

### E2E Test Checklist

- [ ] `admin-user-subscription-flow.spec.ts` created
- [ ] Login as admin works
- [ ] Navigate to Users page
- [ ] Create User form with all User fields
- [ ] Create User form with all UserDetails fields
- [ ] User creation success verification
- [ ] Navigate to Subscriptions page
- [ ] Create Subscription with user selection
- [ ] Plan selection and start date
- [ ] Subscription creation success
- [ ] Navigate to Invoices page
- [ ] Find invoice by user email
- [ ] Verify invoice status is "pending"
- [ ] Test cleanup (delete test data)

---

## Part 2: Python Integration Tests

### Test File: `test_user_subscription_flow.py`

**Location:** `vbwd-backend/tests/integration/`

### Principles Applied

- **TDD-First**: Write tests before implementation changes
- **Event-Driven**: Verify events are dispatched correctly
- **SOLID**: Single responsibility per test
- **Liskov**: Test through interfaces, not implementations
- **DI**: Use injected dependencies, mock where needed
- **Clean Code**: Clear test names, arrange-act-assert pattern

### Test Implementation

```python
# tests/integration/test_user_subscription_flow.py

"""
Integration tests for User-Subscription-Invoice flow.

Tests the complete flow from user creation through subscription
assignment and automatic invoice generation.

Methodology: TDD-First, Event-Driven, SOLID, Liskov, DI
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from src.models.enums import (
    UserStatus,
    UserRole,
    SubscriptionStatus,
    InvoiceStatus,
)


class TestUserCreationAPI:
    """Test user creation endpoint."""

    def test_create_user_returns_201(self, client, admin_token):
        """POST /admin/users creates user and returns 201."""
        # Arrange
        user_data = {
            "email": f"test.{datetime.utcnow().timestamp()}@example.com",
            "password": "TestPass123@",
            "status": "active",
            "role": "user",
            "details": {
                "first_name": "John",
                "last_name": "Doe",
                "address_line_1": "Hauptstraße 123",
                "city": "Berlin",
                "postal_code": "10115",
                "country": "DE",
                "phone": "+49 30 12345678",
            },
        }

        # Act
        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["email"] == user_data["email"]
        assert data["status"] == "active"

    def test_create_user_with_details_saves_all_fields(self, client, admin_token):
        """User details are persisted correctly."""
        # Arrange
        user_data = {
            "email": f"details.{datetime.utcnow().timestamp()}@example.com",
            "password": "TestPass123@",
            "details": {
                "first_name": "Jane",
                "last_name": "Smith",
                "address_line_1": "Musterweg 42",
                "address_line_2": "Apt 3",
                "city": "Munich",
                "postal_code": "80331",
                "country": "DE",
                "phone": "+49 89 9876543",
            },
        }

        # Act
        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.get_json()
        assert data["details"]["first_name"] == "Jane"
        assert data["details"]["last_name"] == "Smith"
        assert data["details"]["city"] == "Munich"
        assert data["details"]["country"] == "DE"

    def test_create_user_emits_user_created_event(
        self, client, admin_token, event_dispatcher_mock
    ):
        """User creation dispatches 'user:created' event."""
        # Arrange
        user_data = {
            "email": f"event.{datetime.utcnow().timestamp()}@example.com",
            "password": "TestPass123@",
        }

        # Act
        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 201
        event_dispatcher_mock.dispatch.assert_called_with(
            "user:created",
            pytest.approx_dict({"user_id": pytest.any(str), "email": user_data["email"]}),
        )


class TestSubscriptionCreationAPI:
    """Test subscription creation endpoint."""

    def test_create_subscription_returns_201(
        self, client, admin_token, test_user, test_plan
    ):
        """POST /admin/subscriptions creates subscription."""
        # Arrange
        subscription_data = {
            "user_id": str(test_user.id),
            "tarif_plan_id": str(test_plan.id),
            "started_at": datetime.utcnow().isoformat(),
        }

        # Act
        response = client.post(
            "/api/v1/admin/subscriptions",
            json=subscription_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.get_json()
        assert data["user_id"] == str(test_user.id)
        assert data["status"] == "active"

    def test_create_subscription_activates_immediately(
        self, client, admin_token, test_user, test_plan
    ):
        """Subscription with current start date is immediately active."""
        # Arrange
        now = datetime.utcnow()
        subscription_data = {
            "user_id": str(test_user.id),
            "tarif_plan_id": str(test_plan.id),
            "started_at": now.isoformat(),
        }

        # Act
        response = client.post(
            "/api/v1/admin/subscriptions",
            json=subscription_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        data = response.get_json()
        assert data["status"] == "active"
        assert data["started_at"] is not None
        assert data["expires_at"] is not None

    def test_create_subscription_creates_invoice(
        self, client, admin_token, test_user, test_plan
    ):
        """Subscription creation generates invoice."""
        # Arrange
        subscription_data = {
            "user_id": str(test_user.id),
            "tarif_plan_id": str(test_plan.id),
            "started_at": datetime.utcnow().isoformat(),
        }

        # Act
        response = client.post(
            "/api/v1/admin/subscriptions",
            json=subscription_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert - subscription created
        assert response.status_code == 201
        subscription_id = response.get_json()["id"]

        # Assert - invoice exists
        invoices_response = client.get(
            f"/api/v1/admin/invoices?subscription_id={subscription_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        invoices = invoices_response.get_json()["items"]
        assert len(invoices) >= 1
        assert invoices[0]["status"] == "pending"

    def test_create_subscription_emits_subscription_created_event(
        self, client, admin_token, test_user, test_plan, event_dispatcher_mock
    ):
        """Subscription creation dispatches 'subscription:created' event."""
        # Arrange
        subscription_data = {
            "user_id": str(test_user.id),
            "tarif_plan_id": str(test_plan.id),
            "started_at": datetime.utcnow().isoformat(),
        }

        # Act
        response = client.post(
            "/api/v1/admin/subscriptions",
            json=subscription_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        event_dispatcher_mock.dispatch.assert_any_call(
            "subscription:created",
            pytest.approx_dict({
                "subscription_id": pytest.any(str),
                "user_id": str(test_user.id),
                "plan_id": str(test_plan.id),
            }),
        )


class TestInvoiceCreationAPI:
    """Test invoice creation and retrieval."""

    def test_invoice_created_with_pending_status(
        self, client, admin_token, test_subscription
    ):
        """Invoice for new subscription has 'pending' status."""
        # Act
        response = client.get(
            f"/api/v1/admin/invoices?subscription_id={test_subscription.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        data = response.get_json()
        assert len(data["items"]) >= 1
        invoice = data["items"][0]
        assert invoice["status"] == "pending"

    def test_invoice_has_correct_amount(
        self, client, admin_token, test_subscription, test_plan
    ):
        """Invoice amount matches plan price."""
        # Act
        response = client.get(
            f"/api/v1/admin/invoices?subscription_id={test_subscription.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        invoice = response.get_json()["items"][0]
        assert Decimal(invoice["amount"]) == test_plan.price

    def test_invoice_linked_to_subscription(
        self, client, admin_token, test_subscription
    ):
        """Invoice has correct subscription_id."""
        # Act
        response = client.get(
            f"/api/v1/admin/invoices?subscription_id={test_subscription.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        invoice = response.get_json()["items"][0]
        assert invoice["subscription_id"] == str(test_subscription.id)

    def test_invoice_emits_invoice_created_event(
        self, client, admin_token, test_user, test_plan, event_dispatcher_mock
    ):
        """Invoice creation dispatches 'invoice:created' event."""
        # Arrange
        subscription_data = {
            "user_id": str(test_user.id),
            "tarif_plan_id": str(test_plan.id),
            "started_at": datetime.utcnow().isoformat(),
        }

        # Act
        client.post(
            "/api/v1/admin/subscriptions",
            json=subscription_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        event_dispatcher_mock.dispatch.assert_any_call(
            "invoice:created",
            pytest.approx_dict({
                "invoice_id": pytest.any(str),
                "user_id": str(test_user.id),
                "amount": pytest.any(str),
            }),
        )


class TestCompleteFlow:
    """Test complete user-subscription-invoice flow."""

    def test_full_flow_creates_all_entities(self, client, admin_token, test_plan):
        """Complete flow: create user → subscription → verify invoice."""
        # Step 1: Create user
        user_data = {
            "email": f"flow.{datetime.utcnow().timestamp()}@example.com",
            "password": "TestPass123@",
            "status": "active",
            "details": {
                "first_name": "Flow",
                "last_name": "Test",
                "city": "Berlin",
                "country": "DE",
            },
        }
        user_response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert user_response.status_code == 201
        user_id = user_response.get_json()["id"]

        # Step 2: Create subscription
        subscription_data = {
            "user_id": user_id,
            "tarif_plan_id": str(test_plan.id),
            "started_at": datetime.utcnow().isoformat(),
        }
        subscription_response = client.post(
            "/api/v1/admin/subscriptions",
            json=subscription_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert subscription_response.status_code == 201
        subscription_id = subscription_response.get_json()["id"]

        # Step 3: Verify invoice
        invoices_response = client.get(
            f"/api/v1/admin/invoices?user_id={user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        invoices = invoices_response.get_json()["items"]

        assert len(invoices) >= 1
        invoice = invoices[0]
        assert invoice["status"] == "pending"
        assert invoice["subscription_id"] == subscription_id
        assert invoice["user_id"] == user_id


# Fixtures

@pytest.fixture
def test_user(db_session, user_factory):
    """Create test user for subscription tests."""
    return user_factory.create(
        email=f"fixture.{datetime.utcnow().timestamp()}@example.com",
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def test_plan(db_session, plan_factory):
    """Create test plan for subscription tests."""
    return plan_factory.create(
        name="Test Plan",
        price=Decimal("9.99"),
        billing_period="monthly",
        is_active=True,
    )


@pytest.fixture
def test_subscription(db_session, test_user, test_plan, subscription_factory):
    """Create test subscription with invoice."""
    return subscription_factory.create(
        user_id=test_user.id,
        tarif_plan_id=test_plan.id,
        status=SubscriptionStatus.ACTIVE,
    )


@pytest.fixture
def event_dispatcher_mock(mocker):
    """Mock event dispatcher for event verification."""
    return mocker.patch("src.events.dispatcher.dispatch")
```

### Integration Test Checklist

- [ ] `test_user_subscription_flow.py` created
- [ ] `TestUserCreationAPI` - POST /admin/users tests
- [ ] `TestSubscriptionCreationAPI` - POST /admin/subscriptions tests
- [ ] `TestInvoiceCreationAPI` - Invoice verification tests
- [ ] `TestCompleteFlow` - End-to-end API flow test
- [ ] Event dispatch verification for all operations
- [ ] Fixtures for test data
- [ ] Cleanup after tests

---

## Part 3: API Endpoints Required

### Endpoints to Verify/Implement

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/api/v1/admin/users` | Create user with details | Verify |
| GET | `/api/v1/admin/users/:id` | Get user by ID | Verify |
| POST | `/api/v1/admin/subscriptions` | Create subscription | Verify |
| GET | `/api/v1/admin/subscriptions/:id` | Get subscription | Verify |
| GET | `/api/v1/admin/invoices` | List invoices (with filters) | Verify |
| GET | `/api/v1/admin/invoices/:id` | Get invoice by ID | Verify |

### Required Request/Response Schemas

```python
# POST /api/v1/admin/users
CreateUserRequest = {
    "email": str,           # Required
    "password": str,        # Required
    "status": str,          # Optional, default "pending"
    "role": str,            # Optional, default "user"
    "details": {            # Optional
        "first_name": str,
        "last_name": str,
        "address_line_1": str,
        "address_line_2": str,
        "city": str,
        "postal_code": str,
        "country": str,     # ISO 3166-1 alpha-2
        "phone": str,
    }
}

# POST /api/v1/admin/subscriptions
CreateSubscriptionRequest = {
    "user_id": str,         # UUID, required
    "tarif_plan_id": str,   # UUID, required
    "started_at": str,      # ISO datetime, required
}
```

---

## Part 4: Events to Verify

### Event-Driven Architecture

| Event | Trigger | Payload |
|-------|---------|---------|
| `user:created` | POST /admin/users | `{user_id, email}` |
| `subscription:created` | POST /admin/subscriptions | `{subscription_id, user_id, plan_id}` |
| `subscription:activated` | Subscription starts | `{subscription_id, started_at, expires_at}` |
| `invoice:created` | New subscription | `{invoice_id, user_id, amount, currency}` |

---

## Acceptance Criteria

### E2E Tests
- [ ] Admin can login
- [ ] Admin can create user with all User fields
- [ ] Admin can create user with all UserDetails fields
- [ ] Admin can create subscription for user
- [ ] Invoice is automatically created
- [ ] Invoice status is "pending"

### Integration Tests
- [ ] All API endpoints return correct status codes
- [ ] User creation persists all fields
- [ ] Subscription creation activates immediately
- [ ] Invoice is created with subscription
- [ ] Events are dispatched for all operations
- [ ] All tests pass with real PostgreSQL

### Code Quality
- [ ] TDD-first (tests written before fixes)
- [ ] Clean Code (readable, well-named)
- [ ] SOLID principles followed
- [ ] DI used for dependencies
- [ ] No over-engineering

---

## Notes

- Invoice status in DB is `pending` (not `issued`) - verify UI shows correct status
- Tests should clean up created data after execution
- Use factory fixtures for test data creation
- Mock event dispatcher to verify events without side effects

---

*Created: 2026-01-05*
