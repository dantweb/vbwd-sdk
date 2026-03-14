# Sprint: Backend - Admin Create User Endpoint

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
    pytest tests/integration/test_user_subscription_flow.py::TestAPIEndpointExistence::test_admin_create_user_endpoint_exists -v

# Run AFTER implementation (should pass)
docker-compose run --rm -e API_BASE_URL=http://api:5000/api/v1 test \
    pytest tests/integration/test_user_subscription_flow.py -v

# Run unit tests during development
docker-compose run --rm test pytest tests/unit/ -v
```

### Design Decisions
- **User Status**: Admin-created users are set to `active` immediately (no email verification)
- **Events**: Dispatch `user:created` event for audit trail and integrations

### Definition of Done
- [ ] All existing tests pass (no regressions)
- [ ] New endpoint test passes (removes xfail)
- [ ] `user:created` event is dispatched
- [ ] Code follows existing patterns in codebase
- [ ] No unnecessary abstractions added

---

## Objective

Implement `POST /api/v1/admin/users` endpoint so admin can create users with full details.

**TDD Discovery:** Integration tests expect this endpoint but it doesn't exist.
Currently admin must use `/auth/register` workaround.

---

## Test Reference

Tests that will pass after implementation:

```python
# From test_user_subscription_flow.py (marked as xfail)
@pytest.mark.xfail(reason="TDD: POST /admin/users not implemented yet")
def test_admin_create_user_endpoint_exists(self, auth_headers):
    response = requests.post(
        f"{self.BASE_URL}/admin/users",
        json={},
        headers=auth_headers,
        timeout=10
    )
    assert response.status_code != 404, "POST /admin/users endpoint not found"
```

---

## Data Models

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

---

## API Specification

### Endpoint

```
POST /api/v1/admin/users
```

### Request Schema

```python
CreateUserRequest = {
    "email": str,           # Required, unique
    "password": str,        # Required, min 8 chars, complexity rules
    "status": str,          # Optional, default "pending" (pending|active|suspended)
    "role": str,            # Optional, default "user" (user|admin|vendor)
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
```

### Response Schema

```python
# 201 Created
CreateUserResponse = {
    "id": str,              # UUID
    "email": str,
    "status": str,
    "role": str,
    "details": {
        "first_name": str | None,
        "last_name": str | None,
        "address_line_1": str | None,
        "address_line_2": str | None,
        "city": str | None,
        "postal_code": str | None,
        "country": str | None,
        "phone": str | None,
    } | None,
    "created_at": str,      # ISO datetime
}

# 400 Bad Request
ErrorResponse = {
    "error": str,
    "details": dict | None,
}

# 409 Conflict (email exists)
ConflictResponse = {
    "error": "User with this email already exists"
}
```

---

## Implementation Plan

### Phase 1: Schema Definition

**File:** `src/schemas/admin_user_schemas.py`

```python
from marshmallow import Schema, fields, validate

class UserDetailsSchema(Schema):
    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    address_line_1 = fields.Str(validate=validate.Length(max=255))
    address_line_2 = fields.Str(validate=validate.Length(max=255))
    city = fields.Str(validate=validate.Length(max=100))
    postal_code = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(validate=validate.Length(equal=2))  # ISO alpha-2
    phone = fields.Str(validate=validate.Length(max=50))

class CreateUserRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    status = fields.Str(validate=validate.OneOf(['pending', 'active', 'suspended']))
    role = fields.Str(validate=validate.OneOf(['user', 'admin', 'vendor']))
    details = fields.Nested(UserDetailsSchema)
```

### Phase 2: Service Method

**File:** `src/services/admin_user_service.py`

```python
from typing import Optional
from uuid import UUID
from src.models.user import User
from src.models.user_details import UserDetails
from src.models.enums import UserStatus, UserRole
from src.repositories.user_repository import UserRepository
from src.repositories.user_details_repository import UserDetailsRepository
from src.events.dispatcher import EventDispatcher

class AdminUserService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_details_repository: UserDetailsRepository,
        event_dispatcher: EventDispatcher,
    ):
        self._user_repo = user_repository
        self._details_repo = user_details_repository
        self._dispatcher = event_dispatcher

    def create_user(
        self,
        email: str,
        password: str,
        status: str = 'pending',
        role: str = 'user',
        details: Optional[dict] = None,
    ) -> User:
        """Create user with optional details.

        Args:
            email: User email (unique)
            password: Plaintext password (will be hashed)
            status: User status (pending|active|suspended)
            role: User role (user|admin|vendor)
            details: Optional UserDetails fields

        Returns:
            Created User with details populated

        Raises:
            ValueError: If email already exists
        """
        # Check for existing user
        existing = self._user_repo.find_by_email(email)
        if existing:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = self._hash_password(password)

        # Create user
        user = User()
        user.email = email
        user.password_hash = password_hash
        user.status = UserStatus(status)
        user.role = UserRole(role)

        created_user = self._user_repo.save(user)

        # Create details if provided
        if details:
            user_details = UserDetails()
            user_details.user_id = created_user.id
            for key, value in details.items():
                if hasattr(user_details, key):
                    setattr(user_details, key, value)
            self._details_repo.save(user_details)
            created_user.details = user_details

        # Dispatch event
        self._dispatcher.dispatch('user:created', {
            'user_id': str(created_user.id),
            'email': created_user.email,
            'role': created_user.role.value,
        })

        return created_user

    def _hash_password(self, password: str) -> str:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

### Phase 3: Route Implementation

**File:** `src/routes/admin/users.py` (extend existing)

```python
@admin_users_bp.route('/', methods=['POST'])
@require_auth
@require_admin
def create_user():
    """
    Create new user with optional details.

    ---
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "status": "active",
            "role": "user",
            "details": {
                "first_name": "John",
                "last_name": "Doe",
                "city": "Berlin",
                "country": "DE"
            }
        }

    Returns:
        201: Created user with details
        400: Validation error
        409: Email already exists
    """
    try:
        data = create_user_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': str(err.messages)}), 400

    # Get service from container
    admin_user_service = current_app.container.admin_user_service()

    try:
        user = admin_user_service.create_user(
            email=data['email'],
            password=data['password'],
            status=data.get('status', 'pending'),
            role=data.get('role', 'user'),
            details=data.get('details'),
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 409

    return jsonify(user.to_dict()), 201
```

### Phase 4: Container Registration

**File:** `src/container.py` (extend)

```python
class Container(containers.DeclarativeContainer):
    # ... existing providers ...

    admin_user_service = providers.Factory(
        AdminUserService,
        user_repository=user_repository,
        user_details_repository=user_details_repository,
        event_dispatcher=event_dispatcher,
    )
```

---

## Events

| Event | Payload |
|-------|---------|
| `user:created` | `{user_id: str, email: str, role: str}` |

---

## Acceptance Criteria

- [ ] `POST /api/v1/admin/users` returns 201 on success
- [ ] User is created with hashed password
- [ ] UserDetails are created if provided
- [ ] `user:created` event is dispatched
- [ ] 409 returned if email already exists
- [ ] 400 returned for validation errors
- [ ] Only admin role can access endpoint
- [ ] Integration test `test_admin_create_user_endpoint_exists` passes

---

## Test Verification

```bash
# Run integration tests
docker-compose run --rm -e API_BASE_URL=http://api:5000/api/v1 test \
    pytest tests/integration/test_user_subscription_flow.py::TestAPIEndpointExistence::test_admin_create_user_endpoint_exists -v
```

---

*Created: 2026-01-05*
*Relates to: Sprint 04 (E2E & Integration Tests)*
