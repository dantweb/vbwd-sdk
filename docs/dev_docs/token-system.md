# Token System — Plugin Developer Guide

This document explains the vbwd token economy: how tokens are stored, how they flow through the system, and how to integrate token consumption into a new plugin.

---

## Table of Contents

1. [Concepts](#1-concepts)
2. [Data Model](#2-data-model)
3. [Transaction Types](#3-transaction-types)
4. [TokenService API](#4-tokenservice-api)
5. [How Tokens are Credited](#5-how-tokens-are-credited)
6. [How Plugins Consume Tokens](#6-how-plugins-consume-tokens)
7. [Plan Feature Integration](#7-plan-feature-integration)
8. [Frontend Integration](#8-frontend-integration)
9. [Testing Token Logic](#9-testing-token-logic)
10. [Complete Plugin Example](#10-complete-plugin-example)

---

## 1. Concepts

**Tokens** are an in-platform virtual currency used to meter AI-based and usage-based features. They are **not a payment currency** — they cannot be exchanged for money. They are a consumption counter.

Key properties:
- Every user has exactly one `UserTokenBalance` record (created lazily on first credit)
- Tokens are integers — no fractional tokens
- The balance is a running total updated atomically on each transaction
- Every change (credit or debit) creates an immutable `TokenTransaction` audit record
- Tokens cannot go below zero — debit raises `ValueError: Insufficient token balance` if the balance would underflow

**Sources of tokens:**
1. Subscription activation — each plan's `features.default_tokens` is credited when a subscription becomes active
2. Token bundle purchase — user buys a bundle (e.g., 100 tokens for €3) which credits immediately on payment confirmation
3. Admin adjustment — manual credit via admin API (bonus, correction, refund)

**Sinks of tokens:**
1. Plugin feature usage — a plugin calls `token_service.debit_tokens()` when a user performs a token-consuming action
2. Refund — when a purchase is refunded, previously credited tokens are debited (clamped to current balance)

---

## 2. Data Model

### `UserTokenBalance`

```python
# src/models/user_token_balance.py
class UserTokenBalance(BaseModel):
    __tablename__ = "user_token_balance"

    user_id = db.Column(db.UUID, db.ForeignKey("user.id"), unique=True, nullable=False)
    balance = db.Column(db.Integer, nullable=False, default=0)
```

One record per user. `balance` is the authoritative current balance. It is updated in place on every transaction.

### `TokenTransaction`

```python
class TokenTransaction(BaseModel):
    __tablename__ = "token_transaction"

    user_id          = db.Column(db.UUID, db.ForeignKey("user.id"), nullable=False)
    amount           = db.Column(db.Integer, nullable=False)   # positive = credit, negative = debit
    transaction_type = db.Column(db.Enum(TokenTransactionType), nullable=False)
    reference_id     = db.Column(db.UUID, nullable=True)       # session_id, purchase_id, invoice_id…
    description      = db.Column(db.String(255), nullable=True)
    created_at       = db.Column(db.DateTime, nullable=False)
```

Append-only. Never mutated after creation. `reference_id` links back to the thing that caused the transaction (a Taro session ID, a bundle purchase ID, etc.).

### `TokenBundle`

```python
# src/models/token_bundle.py — admin-configured purchasable packages
class TokenBundle(BaseModel):
    name         = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    token_amount = db.Column(db.Integer, nullable=False)
    price        = db.Column(db.Numeric(10, 2), nullable=False)  # in default currency
    is_active    = db.Column(db.Boolean, default=True)
    sort_order   = db.Column(db.Integer, default=0)
```

### `TokenBundlePurchase`

```python
# Tracks a purchase transaction through payment → completion
class TokenBundlePurchase(BaseModel):
    user_id        = db.Column(db.UUID, db.ForeignKey("user.id"))
    bundle_id      = db.Column(db.UUID, db.ForeignKey("token_bundle.id"))
    token_amount   = db.Column(db.Integer, nullable=False)
    total_price    = db.Column(db.Numeric(10, 2), nullable=False)
    status         = db.Column(db.Enum(PurchaseStatus), default=PurchaseStatus.PENDING)
    tokens_credited = db.Column(db.Boolean, default=False)
    completed_at   = db.Column(db.DateTime, nullable=True)
```

---

## 3. Transaction Types

```python
class TokenTransactionType(enum.Enum):
    PURCHASE     = "PURCHASE"      # User bought a token bundle
    SUBSCRIPTION = "SUBSCRIPTION"  # Tokens credited on plan activation
    USAGE        = "USAGE"         # Plugin consumed tokens for a feature
    BONUS        = "BONUS"         # Admin manually granted extra tokens
    ADJUSTMENT   = "ADJUSTMENT"    # Admin correction (positive or negative)
    REFUND       = "REFUND"        # Tokens removed on payment refund
```

When debiting from a plugin, always use `USAGE`. This ensures the transaction history clearly distinguishes between purchases, plan credits, and feature consumption.

---

## 4. TokenService API

`TokenService` is the **only** authorised way to modify token balances. Never write directly to `UserTokenBalance.balance`.

```python
from src.services.token_service import TokenService
from src.repositories.token_repository import TokenBalanceRepository, TokenTransactionRepository
from src.repositories.token_bundle_purchase_repository import TokenBundlePurchaseRepository
from src.models.enums import TokenTransactionType

def _token_svc():
    return TokenService(
        balance_repo=TokenBalanceRepository(db.session),
        transaction_repo=TokenTransactionRepository(db.session),
        purchase_repo=TokenBundlePurchaseRepository(db.session),
    )
```

### `get_balance(user_id) → int`

Returns the user's current token balance. Returns `0` if no balance record exists yet.

```python
balance = _token_svc().get_balance(user_id)
```

### `credit_tokens(user_id, amount, transaction_type, reference_id=None, description=None) → UserTokenBalance`

Credits `amount` tokens. `amount` must be positive.

```python
_token_svc().credit_tokens(
    user_id=user.id,
    amount=200,
    transaction_type=TokenTransactionType.SUBSCRIPTION,
    reference_id=subscription.id,
    description="Pro plan activation",
)
```

### `debit_tokens(user_id, amount, transaction_type, reference_id=None, description=None) → UserTokenBalance`

Debits `amount` tokens. Raises `ValueError("Insufficient token balance")` if the balance would go below zero.

```python
try:
    _token_svc().debit_tokens(
        user_id=user.id,
        amount=10,
        transaction_type=TokenTransactionType.USAGE,
        reference_id=session.id,
        description="Taro reading — 3-card spread",
    )
except ValueError:
    return jsonify({"error": "Insufficient tokens"}), 402
```

### `complete_purchase(purchase_id)`

Marks a `TokenBundlePurchase` as completed and automatically credits the associated tokens. Called by the payment webhook handler when payment succeeds.

```python
_token_svc().complete_purchase(purchase_id=purchase.id)
```

### `refund_tokens(user_id, amount, reference_id=None, description=None) → int`

Debits up to `amount` tokens for a refund. Clamps to the current balance (never errors on insufficient balance — returns the actual amount removed). Used by the refund service.

### `get_transactions(user_id, limit=50, offset=0) → List[TokenTransaction]`

Returns paginated transaction history for a user.

---

## 5. How Tokens are Credited

### On Subscription Activation

When a subscription becomes active, the subscription service reads `plan.features["default_tokens"]` and credits that amount:

```python
# src/services/subscription_service.py (simplified)
def activate_subscription(self, subscription):
    ...
    default_tokens = subscription.tarif_plan.features.get("default_tokens", 0)
    if default_tokens > 0:
        self._token_service.credit_tokens(
            user_id=subscription.user_id,
            amount=default_tokens,
            transaction_type=TokenTransactionType.SUBSCRIPTION,
            reference_id=subscription.id,
            description=f"Plan activation: {subscription.tarif_plan.name}",
        )
```

To enable this for your plan, add `default_tokens` to the plan's `features` JSON in the admin or in your populate script:

```python
TarifPlan(
    name="My AI Plan",
    features={"default_tokens": 500, "my_daily_limit": 5},
    ...
)
```

### On Bundle Purchase

When a user buys a token bundle and the payment is confirmed:
1. Payment provider webhook fires `POST /api/v1/webhooks/<provider>`
2. Webhook handler locates the `TokenBundlePurchase` (via `reference_id` in the payment session)
3. Calls `token_service.complete_purchase(purchase_id)` which credits the tokens atomically

No plugin action required — this is handled by the core payment and token services.

---

## 6. How Plugins Consume Tokens

### Basic Pattern

```python
# In your plugin's service or route:
from src.services.token_service import TokenService
from src.repositories.token_repository import TokenBalanceRepository, TokenTransactionRepository
from src.repositories.token_bundle_purchase_repository import TokenBundlePurchaseRepository
from src.models.enums import TokenTransactionType

TOKEN_COST = 10   # tokens per action — put this in your plugin's config

def _token_svc():
    return TokenService(
        balance_repo=TokenBalanceRepository(db.session),
        transaction_repo=TokenTransactionRepository(db.session),
        purchase_repo=TokenBundlePurchaseRepository(db.session),
    )


@require_auth
def my_feature_endpoint():
    user_id = g.current_user.id

    # 1. Check balance before proceeding
    balance = _token_svc().get_balance(user_id)
    if balance < TOKEN_COST:
        return jsonify({"error": "Insufficient tokens", "required": TOKEN_COST, "balance": balance}), 402

    # 2. Do the actual work first (avoid charging for a failed operation)
    result = do_my_expensive_ai_thing()

    # 3. Charge tokens only after success
    _token_svc().debit_tokens(
        user_id=user_id,
        amount=TOKEN_COST,
        transaction_type=TokenTransactionType.USAGE,
        reference_id=result.id,   # link to the thing that caused the charge
        description=f"My feature: {result.name}",
    )

    return jsonify(result.to_dict()), 201
```

**Rules:**
1. Always check balance **before** doing expensive work — fail fast with a `402 Payment Required`
2. Debit tokens **after** the operation succeeds — never charge for a failed call
3. Pass `reference_id` pointing to the created entity so the transaction is auditable
4. Use `TokenTransactionType.USAGE` for all feature consumption

### Reading Token Cost from Plugin Config

Hardcoding token costs is acceptable for simple plugins. For configurable costs, read from `self._config`:

```python
class MyPlugin(BasePlugin):
    DEFAULT_CONFIG = {"token_cost_per_action": 10}

    def initialize(self, config=None):
        merged = {**self.DEFAULT_CONFIG}
        if config:
            merged.update(config)
        super().initialize(merged)

    @property
    def token_cost(self) -> int:
        return self.get_config("token_cost_per_action", 10)
```

In `routes.py`, access the plugin instance via `current_app.extensions["plugin_manager"].get_plugin("my-plugin").token_cost`.

### Atomic Debit + Create

If you need to atomically create a record and debit tokens (to avoid crediting on DB failure), use Flask-SQLAlchemy's session and flush:

```python
with db.session.begin_nested():
    # Create the record
    session_obj = MySession(user_id=user_id, ...)
    db.session.add(session_obj)
    db.session.flush()   # get session_obj.id without committing

    # Debit tokens (raises ValueError on insufficient balance, rolling back the session)
    _token_svc().debit_tokens(
        user_id=user_id,
        amount=TOKEN_COST,
        transaction_type=TokenTransactionType.USAGE,
        reference_id=session_obj.id,
        description="My action",
    )
# If we reach here, both the record and the debit are in the session
db.session.commit()
```

---

## 7. Plan Feature Integration

### Declaring Token Cost in Plan Features

Plugin-specific feature limits are stored in `TarifPlan.features` (a JSON column). This is the recommended approach for per-plan customisation:

```python
TarifPlan(
    name="Basic",
    features={
        "default_tokens": 50,        # credited on activation
        "my_plugin_daily_limit": 2,  # checked by your plugin
        "my_plugin_token_cost": 10,  # cost per action
    },
)

TarifPlan(
    name="Pro",
    features={
        "default_tokens": 200,
        "my_plugin_daily_limit": 10,
        "my_plugin_token_cost": 5,   # cheaper per-unit on higher plan
    },
)
```

### Reading Plan Features at Runtime

```python
from src.repositories.subscription_repository import SubscriptionRepository
from src.models.enums import SubscriptionStatus

def get_user_plan_features(user_id):
    sub_repo = SubscriptionRepository(db.session)
    active_subs = sub_repo.find_active_by_user(user_id)

    for sub in active_subs:
        plan = sub.tarif_plan
        if plan.features.get("my_plugin_daily_limit") is not None:
            return plan.features
    return {}   # no relevant plan — use plugin defaults


@require_auth
def my_endpoint():
    features = get_user_plan_features(g.current_user.id)
    daily_limit = features.get("my_plugin_daily_limit", 0)
    token_cost  = features.get("my_plugin_token_cost", 10)
    ...
```

### Daily Limit Enforcement

If your plugin enforces a daily limit (like Taro does), track session counts in your own model:

```python
class MyUsageRecord(BaseModel):
    __tablename__ = "my_usage_record"

    user_id    = db.Column(db.UUID, db.ForeignKey("user.id"))
    used_at    = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.UUID, db.ForeignKey("my_session.id"))

# Count today's usages
from datetime import date
today_start = datetime.combine(date.today(), datetime.min.time())
count = (
    db.session.query(MyUsageRecord)
    .filter(MyUsageRecord.user_id == user_id, MyUsageRecord.used_at >= today_start)
    .count()
)
if count >= daily_limit:
    return jsonify({"error": "Daily limit reached", "limit": daily_limit}), 429
```

---

## 8. Frontend Integration

### Displaying Token Balance

The user's token balance is available via the `GET /api/v1/user/profile` response (or a dedicated `GET /api/v1/user/tokens` endpoint). Display it prominently so users know their balance before performing a token-consuming action.

```typescript
// In your plugin's store:
const balance = ref(0);

async function fetchBalance() {
  const data = await ghrmApi.get('/user/tokens');
  balance.value = data.balance;
}
```

### Pre-flight Balance Check

Before triggering a token-consuming action, show how many tokens will be used:

```vue
<template>
  <div class="action-panel">
    <p class="token-cost">
      Cost: <strong>{{ tokenCost }} tokens</strong>
      (you have {{ balance }} tokens)
    </p>
    <button
      :disabled="balance < tokenCost || loading"
      @click="doAction"
    >
      {{ loading ? 'Processing...' : 'Start Reading' }}
    </button>
    <p v-if="balance < tokenCost" class="warning">
      Insufficient tokens. <router-link to="/tokens">Buy more.</router-link>
    </p>
  </div>
</template>
```

### Handling 402 from the API

When the backend returns `402 Payment Required`, the frontend should redirect the user to the token purchase page:

```typescript
async function doAction() {
  try {
    await api.post('/my-feature/sessions');
  } catch (e) {
    if (e.status === 402) {
      router.push('/tokens');   // or open a modal
    }
  }
}
```

### Token Purchase Flow

The user navigates to `/tokens` (provided by the core checkout plugin), selects a bundle, and is directed through the payment flow. On payment success, the backend credits the tokens automatically. The frontend simply re-fetches the balance after returning from checkout.

---

## 9. Testing Token Logic

### Unit Testing

Mock all three repositories:

```python
from unittest.mock import MagicMock
from src.services.token_service import TokenService
from src.models.user_token_balance import UserTokenBalance, TokenTransaction
from src.models.enums import TokenTransactionType
import uuid

def make_token_svc(balance=100):
    user_id = uuid.uuid4()
    bal_obj = UserTokenBalance(user_id=user_id, balance=balance)

    balance_repo = MagicMock()
    balance_repo.find_by_user_id.return_value = bal_obj
    balance_repo.get_or_create.return_value = bal_obj

    transaction_repo = MagicMock()
    purchase_repo = MagicMock()

    svc = TokenService(balance_repo, transaction_repo, purchase_repo)
    return svc, user_id, bal_obj


def test_debit_reduces_balance():
    svc, user_id, bal = make_token_svc(balance=100)
    svc.debit_tokens(user_id, 10, TokenTransactionType.USAGE, description="test")
    assert bal.balance == 90


def test_debit_raises_on_insufficient():
    svc, user_id, _ = make_token_svc(balance=5)
    with pytest.raises(ValueError, match="Insufficient"):
        svc.debit_tokens(user_id, 10, TokenTransactionType.USAGE)


def test_credit_increases_balance():
    svc, user_id, bal = make_token_svc(balance=50)
    svc.credit_tokens(user_id, 100, TokenTransactionType.SUBSCRIPTION)
    assert bal.balance == 150
```

### Testing Your Plugin's Token Integration

Test the full debit flow through your service:

```python
def test_my_feature_deducts_tokens(db_session):
    # Arrange
    user = create_test_user(db_session)
    credit_tokens(user.id, 100, db_session)          # helper to seed balance

    # Act
    response = client.post("/api/v1/my-feature/sessions",
                           headers=auth_headers(user))

    # Assert
    assert response.status_code == 201
    balance = get_balance(user.id, db_session)
    assert balance == 90                              # 100 - 10 token cost

    txns = get_transactions(user.id, db_session)
    assert txns[0].transaction_type == TokenTransactionType.USAGE
    assert txns[0].amount == -10


def test_my_feature_returns_402_on_zero_balance(db_session):
    user = create_test_user(db_session)
    # No tokens credited

    response = client.post("/api/v1/my-feature/sessions",
                           headers=auth_headers(user))

    assert response.status_code == 402
    assert response.json["error"] == "Insufficient tokens"
```

### Integration Test Fixture Pattern

```python
# plugins/my_plugin/tests/conftest.py
import pytest
from src.extensions import db as _db
from src.services.token_service import TokenService
from src.repositories.token_repository import TokenBalanceRepository, TokenTransactionRepository
from src.repositories.token_bundle_purchase_repository import TokenBundlePurchaseRepository
from src.models.enums import TokenTransactionType

@pytest.fixture
def token_svc(db_session):
    return TokenService(
        balance_repo=TokenBalanceRepository(db_session),
        transaction_repo=TokenTransactionRepository(db_session),
        purchase_repo=TokenBundlePurchaseRepository(db_session),
    )

@pytest.fixture
def user_with_tokens(user, token_svc):
    """Create a user with 100 tokens."""
    token_svc.credit_tokens(user.id, 100, TokenTransactionType.SUBSCRIPTION)
    return user
```

---

## 10. Complete Plugin Example

Here is a minimal but complete plugin that consumes tokens. Use it as a reference.

### Backend — `plugins/my-ai-feature/__init__.py`

```python
from src.plugins.base import BasePlugin, PluginMetadata

class MyAIPlugin(BasePlugin):
    DEFAULT_CONFIG = {"token_cost": 10, "daily_limit": 5}

    @property
    def metadata(self):
        return PluginMetadata(
            name="my-ai-feature",
            version="1.0.0",
            author="Your Name",
            description="Token-consuming AI feature",
        )

    def initialize(self, config=None):
        merged = {**self.DEFAULT_CONFIG, **(config or {})}
        super().initialize(merged)

    def get_blueprint(self):
        from plugins.my_ai_feature.src.routes import bp
        return bp

    def get_url_prefix(self): return ""
```

### Backend — `plugins/my-ai-feature/src/routes.py`

```python
from flask import Blueprint, jsonify, g
from src.extensions import db
from src.auth import require_auth
from src.services.token_service import TokenService
from src.repositories.token_repository import TokenBalanceRepository, TokenTransactionRepository
from src.repositories.token_bundle_purchase_repository import TokenBundlePurchaseRepository
from src.models.enums import TokenTransactionType

bp = Blueprint("my_ai_feature", __name__)
TOKEN_COST = 10


def _token_svc():
    return TokenService(
        balance_repo=TokenBalanceRepository(db.session),
        transaction_repo=TokenTransactionRepository(db.session),
        purchase_repo=TokenBundlePurchaseRepository(db.session),
    )


@bp.route("/api/v1/my-ai-feature/generate", methods=["POST"])
@require_auth
def generate():
    user_id = g.current_user.id
    svc = _token_svc()

    # Pre-flight check
    balance = svc.get_balance(user_id)
    if balance < TOKEN_COST:
        return jsonify({
            "error": "Insufficient tokens",
            "required": TOKEN_COST,
            "balance": balance,
        }), 402

    # Do the work
    result = {"output": "AI generated content..."}

    # Charge
    svc.debit_tokens(
        user_id=user_id,
        amount=TOKEN_COST,
        transaction_type=TokenTransactionType.USAGE,
        description="My AI feature generation",
    )

    return jsonify({"result": result, "tokens_used": TOKEN_COST, "balance": balance - TOKEN_COST}), 200


@bp.route("/api/v1/my-ai-feature/balance", methods=["GET"])
@require_auth
def get_balance_endpoint():
    balance = _token_svc().get_balance(g.current_user.id)
    return jsonify({"balance": balance, "token_cost": TOKEN_COST})
```

### User Frontend — `plugins/my-ai-feature/src/views/MyAIFeature.vue`

```vue
<template>
  <div class="feature">
    <div class="balance-banner">
      Your tokens: <strong>{{ balance }}</strong>
      (this action costs {{ tokenCost }})
    </div>

    <button
      :disabled="balance < tokenCost || loading"
      @click="generate"
    >
      {{ loading ? 'Generating…' : 'Generate' }}
    </button>

    <router-link v-if="balance < tokenCost" to="/tokens" class="buy-link">
      Buy more tokens
    </router-link>

    <div v-if="result" class="result">{{ result }}</div>
    <div v-if="error"  class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from 'vbwd-view-component';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const balance  = ref(0);
const tokenCost = ref(10);
const loading  = ref(false);
const result   = ref('');
const error    = ref('');

async function fetchBalance() {
  const resp = await fetch('/api/v1/my-ai-feature/balance', {
    headers: { Authorization: `Bearer ${localStorage.getItem('auth_token')}` },
  });
  const data = await resp.json();
  balance.value   = data.balance;
  tokenCost.value = data.token_cost;
}

async function generate() {
  loading.value = true;
  error.value   = '';
  result.value  = '';
  try {
    const resp = await fetch('/api/v1/my-ai-feature/generate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('auth_token')}` },
    });
    if (resp.status === 402) {
      router.push('/tokens');
      return;
    }
    const data = await resp.json();
    result.value  = data.result.output;
    balance.value = data.balance;   // update displayed balance
  } catch (e) {
    error.value = 'Something went wrong.';
  } finally {
    loading.value = false;
  }
}

onMounted(fetchBalance);
</script>
```

### Plan Feature Configuration

In the populate script or admin UI, set `default_tokens` on plans so users start with tokens when they subscribe:

```python
TarifPlan(
    name="Basic",
    features={
        "default_tokens": 50,
        "my_ai_daily_limit": 2,
    },
)
TarifPlan(
    name="Pro",
    features={
        "default_tokens": 200,
        "my_ai_daily_limit": 10,
    },
)
```

Users on the Basic plan get 50 tokens on activation; Pro users get 200. Additional tokens can always be purchased via token bundles.
