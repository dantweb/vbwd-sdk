# Sprint 01: Email Check API Endpoint

**Priority:** HIGH
**Estimated Effort:** Small
**Dependencies:** None

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Security** | Require checkout session token + rate limiting + FraudCheckService |
| **Fraud Threshold** | >5 email checks from same IP in 1 minute triggers fraud detection |
| **On Suspicious Activity** | Log + notify admin + require CAPTCHA + block IP (15 min) |
| **Session Token** | Created on plan selection; JWT for logged-in users, anonymous token for guests |
| **Response Format** | Minimal `{ "exists": true/false }` only |
| **Email Validation** | Strict validation, return 400 on invalid, **exclude `+` symbol** |

### FraudCheckService (New)

A new extensible service to detect and handle suspicious activity:

```python
class FraudCheckService:
    """Detects suspicious activity patterns."""

    def check_rate_limit(self, ip: str, action: str) -> FraudResult:
        """
        Check if IP exceeds rate limit for action.

        Threshold: >5 email checks from same IP in 1 minute
        """
        pass

    def on_suspicious_activity(self, ip: str, action: str) -> None:
        """
        Handle suspicious activity:
        1. Log the incident
        2. Notify admin via event
        3. Require CAPTCHA for subsequent requests
        4. Block IP for 15 minutes
        """
        pass
```

### Checkout Session Token

- **Created**: When user clicks on a plan (plan selection page)
- **Logged-in user**: JWT token with user context
- **Guest user**: Anonymous token (UUID-based)
- **Stored**: Redis with expiration (30 min)
- **Required**: For all checkout API calls including email check

---

## Core Requirements

This sprint follows our development standards:

| Requirement | Description |
|-------------|-------------|
| **TDD-first** | Write failing tests BEFORE production code |
| **SOLID** | Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion |
| **DRY** | Don't Repeat Yourself - reuse existing code and patterns |
| **Clean Code** | Readable, maintainable, self-documenting code |
| **No Over-engineering** | Only implement what's needed NOW, no premature abstractions |

---

## Objective
Create a backend endpoint to check if an email is already registered. This is the foundation for the checkout email flow.

---

## TDD Phase 1: Write Failing Tests FIRST

### 1.1 Unit Test: AuthService.check_email_exists()

**File:** `vbwd-backend/tests/unit/services/test_auth_service.py`

```python
# Add to existing test file

class TestCheckEmailExists:
    """Tests for email existence check."""

    def test_returns_true_for_existing_email(self, auth_service, mock_user_repo):
        """Existing email should return exists=True."""
        mock_user_repo.find_by_email.return_value = Mock(id="user-123")

        result = auth_service.check_email_exists("existing@example.com")

        assert result.exists is True
        mock_user_repo.find_by_email.assert_called_once_with("existing@example.com")

    def test_returns_false_for_new_email(self, auth_service, mock_user_repo):
        """New email should return exists=False."""
        mock_user_repo.find_by_email.return_value = None

        result = auth_service.check_email_exists("new@example.com")

        assert result.exists is False

    def test_normalizes_email_to_lowercase(self, auth_service, mock_user_repo):
        """Email should be normalized to lowercase."""
        mock_user_repo.find_by_email.return_value = None

        auth_service.check_email_exists("TEST@Example.COM")

        mock_user_repo.find_by_email.assert_called_once_with("test@example.com")

    def test_returns_error_for_invalid_email_format(self, auth_service):
        """Invalid email format should return error."""
        result = auth_service.check_email_exists("not-an-email")

        assert result.success is False
        assert "invalid" in result.error.lower()

    def test_rejects_email_with_plus_symbol(self, auth_service):
        """Email with + symbol should be rejected (prevents alias abuse)."""
        result = auth_service.check_email_exists("test+alias@example.com")

        assert result.success is False
        assert "invalid" in result.error.lower()
```

### 1.2 Unit Test: FraudCheckService

**File:** `vbwd-backend/tests/unit/services/test_fraud_check_service.py`

```python
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta


class TestFraudCheckService:
    """Tests for FraudCheckService."""

    def test_allows_first_request(self, fraud_service, mock_redis):
        """First request from IP should be allowed."""
        mock_redis.get.return_value = None

        result = fraud_service.check_rate_limit("192.168.1.1", "email_check")

        assert result.allowed is True
        assert result.suspicious is False

    def test_allows_requests_under_threshold(self, fraud_service, mock_redis):
        """Requests under threshold (<=5/min) should be allowed."""
        mock_redis.get.return_value = "4"  # 4 previous requests

        result = fraud_service.check_rate_limit("192.168.1.1", "email_check")

        assert result.allowed is True

    def test_flags_requests_over_threshold(self, fraud_service, mock_redis):
        """More than 5 requests/min should trigger fraud detection."""
        mock_redis.get.return_value = "6"  # 6 previous requests

        result = fraud_service.check_rate_limit("192.168.1.1", "email_check")

        assert result.allowed is False
        assert result.suspicious is True

    def test_blocks_ip_on_suspicious_activity(self, fraud_service, mock_redis):
        """Suspicious activity should block IP for 15 minutes."""
        fraud_service.on_suspicious_activity("192.168.1.1", "email_check")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "blocked:192.168.1.1"
        assert call_args[0][1] == 900  # 15 minutes in seconds

    def test_requires_captcha_after_suspicious(self, fraud_service, mock_redis):
        """Subsequent requests after suspicious activity should require CAPTCHA."""
        mock_redis.get.return_value = "1"  # IP is blocked

        result = fraud_service.check_rate_limit("192.168.1.1", "email_check")

        assert result.requires_captcha is True

    def test_logs_suspicious_activity(self, fraud_service, mock_logger):
        """Suspicious activity should be logged."""
        fraud_service.on_suspicious_activity("192.168.1.1", "email_check")

        mock_logger.warning.assert_called()
        log_message = mock_logger.warning.call_args[0][0]
        assert "192.168.1.1" in log_message
        assert "email_check" in log_message

    def test_notifies_admin_on_suspicious(self, fraud_service, mock_event_dispatcher):
        """Suspicious activity should notify admin via event."""
        fraud_service.on_suspicious_activity("192.168.1.1", "email_check")

        mock_event_dispatcher.dispatch.assert_called_once()
        event = mock_event_dispatcher.dispatch.call_args[0][0]
        assert event.type == "fraud.suspicious_activity"
```

### 1.3 Integration Test: GET /api/v1/auth/check-email

**File:** `vbwd-backend/tests/integration/routes/test_auth_routes.py`

```python
# Add to existing test file

class TestCheckEmailEndpoint:
    """Integration tests for email check endpoint."""

    def test_requires_checkout_session_token(self, client):
        """Endpoint should require checkout session token."""
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": "test@example.com"}
            # No X-Checkout-Session header
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "session" in data["error"].lower()

    def test_accepts_valid_checkout_session_token(self, client, checkout_session_token):
        """Valid checkout session token should be accepted."""
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": "brand-new@example.com"},
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 200

    def test_returns_exists_true_for_registered_email(self, client, test_user, checkout_session_token):
        """Registered email should return exists=True."""
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": test_user.email},
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["exists"] is True

    def test_returns_exists_false_for_new_email(self, client, checkout_session_token):
        """New email should return exists=False."""
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": "brand-new@example.com"},
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["exists"] is False

    def test_returns_400_for_missing_email(self, client, checkout_session_token):
        """Missing email param should return 400."""
        response = client.get(
            "/api/v1/auth/check-email",
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "email" in data["error"].lower()

    def test_returns_400_for_invalid_email_format(self, client, checkout_session_token):
        """Invalid email format should return 400."""
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": "not-valid"},
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 400

    def test_returns_400_for_email_with_plus_symbol(self, client, checkout_session_token):
        """Email with + symbol should return 400."""
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": "test+alias@example.com"},
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "invalid" in data["error"].lower()

    def test_fraud_detection_blocks_after_threshold(self, client, checkout_session_token):
        """Should block IP after >5 requests per minute."""
        # Make 6 requests quickly (exceeds threshold)
        for i in range(6):
            client.get(
                "/api/v1/auth/check-email",
                query_string={"email": f"test{i}@example.com"},
                headers={"X-Checkout-Session": checkout_session_token}
            )

        # 7th request should be blocked
        response = client.get(
            "/api/v1/auth/check-email",
            query_string={"email": "test7@example.com"},
            headers={"X-Checkout-Session": checkout_session_token}
        )

        assert response.status_code == 429
        data = response.get_json()
        assert data.get("requires_captcha") is True
```

### 1.4 Unit Test: CheckoutSessionService

**File:** `vbwd-backend/tests/unit/services/test_checkout_session_service.py`

```python
import pytest
from unittest.mock import Mock
from uuid import uuid4


class TestCheckoutSessionService:
    """Tests for CheckoutSessionService."""

    def test_creates_jwt_token_for_logged_in_user(self, session_service, mock_user):
        """Should create JWT token for authenticated user."""
        token = session_service.create_session(user=mock_user, plan_slug="pro")

        assert token is not None
        decoded = session_service.decode_session(token)
        assert decoded["user_id"] == str(mock_user.id)
        assert decoded["plan_slug"] == "pro"

    def test_creates_anonymous_token_for_guest(self, session_service):
        """Should create anonymous token for guest user."""
        token = session_service.create_session(user=None, plan_slug="basic")

        assert token is not None
        decoded = session_service.decode_session(token)
        assert decoded["user_id"] is None
        assert decoded["plan_slug"] == "basic"
        assert "session_id" in decoded  # Anonymous UUID

    def test_token_stored_in_redis(self, session_service, mock_redis):
        """Token should be stored in Redis with expiration."""
        token = session_service.create_session(user=None, plan_slug="basic")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 1800  # 30 minutes in seconds

    def test_validates_existing_token(self, session_service, mock_redis):
        """Should validate existing token in Redis."""
        token = session_service.create_session(user=None, plan_slug="basic")
        mock_redis.exists.return_value = True

        result = session_service.validate_session(token)

        assert result.valid is True

    def test_rejects_expired_token(self, session_service, mock_redis):
        """Should reject expired/invalid token."""
        mock_redis.exists.return_value = False

        result = session_service.validate_session("invalid-token")

        assert result.valid is False
```

---

## TDD Phase 2: Write Minimal Production Code

### 2.1 Add DTO for Response

**File:** `vbwd-backend/src/schemas/auth_schemas.py`

```python
# Add to existing file

class EmailCheckResponseSchema(Schema):
    """Response schema for email check."""
    exists = fields.Boolean(required=True)
```

### 2.2 Add Service Method

**File:** `vbwd-backend/src/services/auth_service.py`

```python
# Add to AuthService class

def check_email_exists(self, email: str) -> AuthResult:
    """
    Check if email is already registered.

    Args:
        email: Email address to check

    Returns:
        AuthResult with exists=True/False or error
    """
    # Validate email format
    if not self._is_valid_email(email):
        return AuthResult(success=False, error="Invalid email format")

    # Normalize and check
    normalized_email = email.lower().strip()
    user = self._user_repository.find_by_email(normalized_email)

    return AuthResult(success=True, exists=user is not None)

def _is_valid_email(self, email: str) -> bool:
    """
    Strict email validation.
    Note: + symbol is excluded to prevent email alias abuse.
    """
    import re
    # Excludes + symbol intentionally (prevents test+1@example.com aliases)
    pattern = r'^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

### 2.3 Add Route

**File:** `vbwd-backend/src/routes/auth.py`

```python
# Add to existing file

@auth_bp.route("/check-email", methods=["GET"])
@limiter.limit("30 per minute")  # Stricter limit to prevent enumeration
def check_email():
    """
    Check if email is registered.

    Query params:
        email: Email address to check

    Returns:
        200: { "exists": boolean }
        400: { "error": "message" }
    """
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "Email parameter required"}), 400

    user_repo = UserRepository(db.session)
    auth_service = AuthService(user_repository=user_repo)

    result = auth_service.check_email_exists(email)

    if result.success:
        return jsonify({"exists": result.exists}), 200
    else:
        return jsonify({"error": result.error}), 400
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Service handles logic, route handles HTTP |
| **O** - Open/Closed | AuthResult extended with `exists` field, not modified |
| **L** - Liskov Substitution | N/A for this sprint |
| **I** - Interface Segregation | Simple endpoint, single purpose |
| **D** - Dependency Inversion | Service depends on repository interface |

## No Over-engineering

- No new event handler (simple sync operation)
- No caching (premature optimization)
- No complex validation (email regex is sufficient)
- Reuse existing AuthService class

---

## Files Created/Modified

### New Files
```
vbwd-backend/src/services/fraud_check_service.py      # FraudCheckService
vbwd-backend/src/services/checkout_session_service.py # CheckoutSessionService
vbwd-backend/tests/unit/services/test_fraud_check_service.py
vbwd-backend/tests/unit/services/test_checkout_session_service.py
```

### Modified Files
```
vbwd-backend/src/services/auth_service.py            # Add check_email_exists()
vbwd-backend/src/routes/auth.py                      # Add /check-email endpoint
vbwd-backend/tests/unit/services/test_auth_service.py
vbwd-backend/tests/integration/routes/test_auth_routes.py
```

---

## Verification Checklist

- [ ] Unit tests written and FAILING (AuthService, FraudCheckService, CheckoutSessionService)
- [ ] Integration tests written and FAILING
- [ ] FraudCheckService implemented (Redis-based rate limiting)
- [ ] CheckoutSessionService implemented (JWT + Redis)
- [ ] AuthService.check_email_exists() implemented
- [ ] Route /check-email implemented with session token validation
- [ ] Email validation excludes + symbol
- [ ] All tests PASSING
- [ ] Fraud detection: >5 requests/min triggers block
- [ ] Manual API test via curl/Postman

## Run Tests

> **All tests run in Docker containers.** Run commands from `vbwd-backend/` directory.

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --unit           # Unit tests only
./bin/pre-commit-check.sh --integration    # Integration tests only
./bin/pre-commit-check.sh                  # Full check

# Makefile commands
make test-unit -- -k "test_check_email"
make test-integration -- -k "TestCheckEmailEndpoint"

# Full regression before commit
make pre-commit
```
