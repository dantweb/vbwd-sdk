# Sprint 04: Backend Payment Capture Implementation

**Date:** 2026-01-13
**Priority:** High
**Type:** Backend Implementation
**Section:** Payment Processing
**Prerequisite:** Sprint 03 (Backend Checkout Implementation)
**Blocks:** Sprint 05 (Frontend Implementation)

## Goal

Implement payment capture that activates all pending items:
- Subscription → `active`
- Token bundles → tokens credited to user balance
- Add-ons → `active`

## Architecture

```
POST /webhooks/payment → PaymentCapturedEvent → PaymentCapturedHandler → Services → DB
```

## Tasks

### Task 4.1: Create Token Balance Models

**File:** `vbwd-backend/src/models/user_token_balance.py`

```python
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from enum import Enum

class TokenTransactionType(str, Enum):
    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"

@dataclass
class UserTokenBalance:
    id: UUID
    user_id: UUID
    balance: int
    updated_at: datetime

@dataclass
class TokenTransaction:
    id: UUID
    user_id: UUID
    amount: int  # positive=credit, negative=debit
    transaction_type: TokenTransactionType
    reference_id: UUID = None  # bundle_purchase_id, etc.
    created_at: datetime = None
```

---

### Task 4.2: Create Database Migrations

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose exec api flask db migrate -m "Add user token balance and transactions"
docker-compose exec api flask db upgrade
```

**Tables to create:**
- `user_token_balances`
- `token_transactions`

---

### Task 4.3: Create Token Repository

**File:** `vbwd-backend/src/repositories/token_repository.py`

```python
class TokenRepository:
    def __init__(self, session):
        self._session = session

    def get_balance(self, user_id: UUID) -> Optional[UserTokenBalance]:
        ...

    def save_balance(self, balance: UserTokenBalance) -> UserTokenBalance:
        ...

    def save_transaction(self, transaction: TokenTransaction) -> TokenTransaction:
        ...

    def get_transactions(self, user_id: UUID, limit: int = 50) -> List[TokenTransaction]:
        ...
```

---

### Task 4.4: Create Token Service

**File:** `vbwd-backend/src/services/token_service.py`

```python
class TokenService:
    def __init__(self, token_repo: TokenRepository, bundle_repo: TokenBundleRepository):
        self._token_repo = token_repo
        self._bundle_repo = bundle_repo

    def complete_purchase(self, purchase_id: UUID) -> TokenBundlePurchase:
        """Mark purchase as completed."""
        purchase = self._bundle_repo.get_purchase_by_id(purchase_id)
        if not purchase:
            raise ValueError("Purchase not found")
        purchase.status = PurchaseStatus.COMPLETED
        purchase.completed_at = datetime.utcnow()
        return self._bundle_repo.save_purchase(purchase)

    def credit_tokens(self, user_id: UUID, amount: int, reference_id: UUID) -> UserTokenBalance:
        """Credit tokens to user balance."""
        balance = self._token_repo.get_balance(user_id)
        if not balance:
            balance = UserTokenBalance(
                id=uuid4(),
                user_id=user_id,
                balance=0,
                updated_at=datetime.utcnow()
            )

        balance.balance += amount
        balance.updated_at = datetime.utcnow()
        self._token_repo.save_balance(balance)

        # Record transaction
        transaction = TokenTransaction(
            id=uuid4(),
            user_id=user_id,
            amount=amount,
            transaction_type=TokenTransactionType.PURCHASE,
            reference_id=reference_id,
            created_at=datetime.utcnow()
        )
        self._token_repo.save_transaction(transaction)

        return balance

    def get_balance(self, user_id: UUID) -> int:
        """Get user's current token balance."""
        balance = self._token_repo.get_balance(user_id)
        return balance.balance if balance else 0
```

---

### Task 4.5: Create Payment Events

**File:** `vbwd-backend/src/events/payment_events.py`

```python
from dataclasses import dataclass
from uuid import UUID
from src.events.base import DomainEvent

@dataclass
class PaymentCapturedEvent(DomainEvent):
    """Domain event: Payment was successfully captured."""
    invoice_id: UUID
    payment_reference: str
    amount: str
    currency: str

    def __post_init__(self):
        super().__post_init__()
        self.name = "payment.captured"
```

---

### Task 4.6: Create Payment Captured Handler

**File:** `vbwd-backend/src/handlers/payment_handlers.py`

```python
class PaymentCapturedHandler(IEventHandler):
    """Handler for payment capture. Activates all pending items."""

    def __init__(
        self,
        invoice_service: InvoiceService,
        subscription_service: SubscriptionService,
        token_service: TokenService,
        add_on_service: AddOnService,
        event_dispatcher: EventDispatcher
    ):
        self._invoice_service = invoice_service
        self._subscription_service = subscription_service
        self._token_service = token_service
        self._add_on_service = add_on_service
        self._event_dispatcher = event_dispatcher

    def can_handle(self, event: DomainEvent) -> bool:
        return event.name == "payment.captured"

    def handle(self, event: PaymentCapturedEvent) -> EventResult:
        try:
            # 1. Mark invoice as paid
            invoice = self._invoice_service.mark_paid(
                invoice_id=event.invoice_id,
                payment_reference=event.payment_reference
            )

            # 2. Process each line item
            for line_item in invoice.line_items:
                if line_item.item_type == LineItemType.SUBSCRIPTION:
                    subscription = self._subscription_service.activate(
                        subscription_id=line_item.item_id
                    )
                    self._event_dispatcher.emit("subscription:activated", {
                        "subscription_id": str(subscription.id),
                        "user_id": str(subscription.user_id)
                    })

                elif line_item.item_type == LineItemType.TOKEN_BUNDLE:
                    purchase = self._token_service.complete_purchase(
                        purchase_id=line_item.item_id
                    )
                    bundle = self._token_service.get_bundle(purchase.bundle_id)
                    self._token_service.credit_tokens(
                        user_id=invoice.user_id,
                        amount=bundle.token_amount,
                        reference_id=purchase.id
                    )
                    self._event_dispatcher.emit("tokens:credited", {
                        "user_id": str(invoice.user_id),
                        "amount": bundle.token_amount,
                        "purchase_id": str(purchase.id)
                    })

                elif line_item.item_type == LineItemType.ADD_ON:
                    addon_sub = self._add_on_service.activate(
                        subscription_id=line_item.item_id
                    )
                    self._event_dispatcher.emit("addon:activated", {
                        "addon_subscription_id": str(addon_sub.id),
                        "user_id": str(addon_sub.user_id)
                    })

            return EventResult.success_result({
                "invoice_id": str(invoice.id),
                "status": "paid",
                "items_activated": len(invoice.line_items)
            })

        except Exception as e:
            return EventResult.error_result(str(e))
```

---

### Task 4.7: Update Subscription Service

**File:** `vbwd-backend/src/services/subscription_service.py` (update)

```python
class SubscriptionService:
    # ... existing code ...

    def activate(self, subscription_id: UUID) -> Subscription:
        """Activate a pending subscription."""
        subscription = self._repo.get_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        if subscription.status != SubscriptionStatus.PENDING:
            raise ValueError(f"Cannot activate subscription with status {subscription.status}")

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.starts_at = datetime.utcnow()
        # Set expires_at based on plan billing period
        subscription.expires_at = self._calculate_expiry(subscription)

        return self._repo.save(subscription)
```

---

### Task 4.8: Create Webhook Route

**File:** `vbwd-backend/src/routes/webhooks.py`

```python
from flask import Blueprint, request, jsonify, current_app
from uuid import UUID
from src.events.payment_events import PaymentCapturedEvent

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")

@webhooks_bp.route("/payment", methods=["POST"])
def payment_webhook():
    """
    Handle payment webhook from payment providers.
    Also used by admin to manually mark invoices as paid.
    """
    data = request.get_json() or {}

    invoice_id = data.get("invoice_id")
    payment_reference = data.get("payment_reference")
    amount = data.get("amount")
    currency = data.get("currency", "USD")

    if not all([invoice_id, payment_reference, amount]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        event = PaymentCapturedEvent(
            invoice_id=UUID(invoice_id),
            payment_reference=payment_reference,
            amount=str(amount),
            currency=currency
        )

        dispatcher = current_app.container.event_dispatcher()
        result = dispatcher.emit(event)

        if result.success:
            return jsonify({
                "status": "success",
                "invoice_id": str(invoice_id),
                "items_activated": result.data.get("items_activated")
            }), 200
        else:
            return jsonify({"error": result.error}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

### Task 4.9: Create Token Balance Route

**File:** `vbwd-backend/src/routes/user.py` (add)

```python
@user_bp.route("/tokens/balance", methods=["GET"])
@require_auth
def get_token_balance():
    """Get current user's token balance."""
    user_id = g.user_id
    token_service = current_app.container.token_service()
    balance = token_service.get_balance(UUID(user_id))
    return jsonify({"balance": balance}), 200
```

---

### Task 4.10: Register Handler in DI Container

**File:** `vbwd-backend/src/app.py` (add)

```python
def _register_event_handlers(app: Flask, container) -> None:
    dispatcher = container.event_dispatcher()

    # ... existing handlers ...

    # Payment captured handler
    payment_handler = PaymentCapturedHandler(
        invoice_service=container.invoice_service(),
        subscription_service=container.subscription_service(),
        token_service=container.token_service(),
        add_on_service=container.add_on_service(),
        event_dispatcher=dispatcher
    )
    dispatcher.register("payment.captured", payment_handler)
```

---

### Task 4.11: Write Payment Capture Tests

**File:** `vbwd-backend/tests/integration/test_payment_capture.py`

```python
"""Integration tests for payment capture."""
import pytest

class TestPaymentCapture:
    """Tests for POST /api/v1/webhooks/payment"""

    def test_payment_activates_subscription(self, client, pending_checkout):
        """Payment capture activates pending subscription."""
        response = client.post(
            "/api/v1/webhooks/payment",
            json={
                "invoice_id": pending_checkout["invoice"]["id"],
                "payment_reference": "PAY-123",
                "amount": pending_checkout["invoice"]["total_amount"]
            }
        )
        assert response.status_code == 200

        # Verify subscription is now active
        # ... verification code ...

    def test_payment_credits_tokens(self, client, pending_checkout_with_bundle, auth_headers):
        """Payment capture credits tokens to user balance."""
        response = client.post(
            "/api/v1/webhooks/payment",
            json={
                "invoice_id": pending_checkout_with_bundle["invoice"]["id"],
                "payment_reference": "PAY-456",
                "amount": pending_checkout_with_bundle["invoice"]["total_amount"]
            }
        )
        assert response.status_code == 200

        # Verify tokens credited
        balance_response = client.get(
            "/api/v1/user/tokens/balance",
            headers=auth_headers
        )
        assert balance_response.get_json()["balance"] > 0

    def test_payment_activates_addon(self, client, pending_checkout_with_addon):
        """Payment capture activates pending add-on."""
        response = client.post(
            "/api/v1/webhooks/payment",
            json={
                "invoice_id": pending_checkout_with_addon["invoice"]["id"],
                "payment_reference": "PAY-789",
                "amount": pending_checkout_with_addon["invoice"]["total_amount"]
            }
        )
        assert response.status_code == 200
```

---

### Task 4.12: Run All Tests

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend

# Run all tests
docker-compose run --rm test pytest tests/ -v

# All checkout and payment tests should PASS
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

- [ ] UserTokenBalance model created
- [ ] TokenTransaction model created
- [ ] Database migrations applied
- [ ] TokenRepository created
- [ ] TokenService created
- [ ] PaymentCapturedEvent created
- [ ] PaymentCapturedHandler implemented
- [ ] SubscriptionService.activate() implemented
- [ ] Webhook route created
- [ ] Token balance route created
- [ ] Handler registered in DI
- [ ] Payment capture tests written and PASS
- [ ] All backend tests PASS
- [ ] Sprint moved to `/done`
- [ ] Report created in `/reports`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Token Balance Models | ⏳ Pending | |
| 4.2 Migrations | ⏳ Pending | |
| 4.3 Token Repository | ⏳ Pending | |
| 4.4 Token Service | ⏳ Pending | |
| 4.5 Payment Events | ⏳ Pending | |
| 4.6 Payment Handler | ⏳ Pending | |
| 4.7 Subscription Service Update | ⏳ Pending | |
| 4.8 Webhook Route | ⏳ Pending | |
| 4.9 Token Balance Route | ⏳ Pending | |
| 4.10 Register Handler | ⏳ Pending | |
| 4.11 Payment Tests | ⏳ Pending | |
| 4.12 Run All Tests | ⏳ Pending | |

---

## Next Sprint

After this sprint, proceed to:
- **Sprint 05:** Frontend Checkout Implementation
