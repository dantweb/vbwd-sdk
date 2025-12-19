# Sprint 2: Authentication & User Management

**Goal:** Implement authentication service, JWT handling, and user management endpoints.

**Prerequisites:** Sprint 1 complete (models and repositories)

---

## Objectives

- [ ] AuthService with password hashing and JWT
- [ ] UserService for profile management
- [ ] Auth routes (register, login)
- [ ] User routes (profile, details)
- [ ] Auth middleware for protected routes
- [ ] Input validation with Marshmallow schemas

---

## Tasks

### 2.1 AuthService Implementation

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/services/test_auth_service.py`

```python
"""Tests for AuthService."""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


class TestAuthServiceRegister:
    """Test cases for registration."""

    def test_register_creates_new_user(self):
        """register should create user with hashed password."""
        from src.services import AuthService
        from src.models import User, UserStatus

        mock_repo = Mock()
        mock_repo.email_exists.return_value = False
        mock_repo.save.return_value = User(
            id=1,
            email="test@example.com",
            password_hash="hashed",
            status=UserStatus.PENDING,
        )

        service = AuthService(user_repo=mock_repo, secret_key="test-secret")
        result = service.register("test@example.com", "password123")

        assert result.success is True
        assert result.user_id == 1
        assert result.token is not None
        mock_repo.save.assert_called_once()

    def test_register_fails_if_email_exists(self):
        """register should fail if email already registered."""
        from src.services import AuthService

        mock_repo = Mock()
        mock_repo.email_exists.return_value = True

        service = AuthService(user_repo=mock_repo, secret_key="test-secret")
        result = service.register("existing@example.com", "password123")

        assert result.success is False
        assert result.error == "Email already registered"

    def test_register_validates_email_format(self):
        """register should validate email format."""
        from src.services import AuthService

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        result = service.register("invalid-email", "password123")

        assert result.success is False
        assert "email" in result.error.lower()

    def test_register_validates_password_strength(self):
        """register should require minimum password length."""
        from src.services import AuthService

        mock_repo = Mock()
        mock_repo.email_exists.return_value = False
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        result = service.register("test@example.com", "short")

        assert result.success is False
        assert "password" in result.error.lower()


class TestAuthServiceLogin:
    """Test cases for login."""

    def test_login_returns_token_for_valid_credentials(self):
        """login should return JWT token for valid credentials."""
        from src.services import AuthService
        from src.models import User, UserStatus

        mock_repo = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            password_hash="$2b$12$...",  # bcrypt hash
            status=UserStatus.ACTIVE,
        )
        mock_repo.find_by_email.return_value = mock_user

        service = AuthService(user_repo=mock_repo, secret_key="test-secret")
        # Mock password verification
        service.verify_password = Mock(return_value=True)

        result = service.login("test@example.com", "password123")

        assert result.success is True
        assert result.token is not None
        assert result.user_id == 1

    def test_login_fails_for_unknown_email(self):
        """login should fail if email not found."""
        from src.services import AuthService

        mock_repo = Mock()
        mock_repo.find_by_email.return_value = None

        service = AuthService(user_repo=mock_repo, secret_key="test-secret")
        result = service.login("unknown@example.com", "password123")

        assert result.success is False
        assert result.error == "Invalid credentials"

    def test_login_fails_for_wrong_password(self):
        """login should fail for incorrect password."""
        from src.services import AuthService
        from src.models import User, UserStatus

        mock_repo = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            password_hash="$2b$12$...",
            status=UserStatus.ACTIVE,
        )
        mock_repo.find_by_email.return_value = mock_user

        service = AuthService(user_repo=mock_repo, secret_key="test-secret")
        service.verify_password = Mock(return_value=False)

        result = service.login("test@example.com", "wrong-password")

        assert result.success is False
        assert result.error == "Invalid credentials"

    def test_login_fails_for_inactive_user(self):
        """login should fail for non-active users."""
        from src.services import AuthService
        from src.models import User, UserStatus

        mock_repo = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            password_hash="$2b$12$...",
            status=UserStatus.SUSPENDED,
        )
        mock_repo.find_by_email.return_value = mock_user

        service = AuthService(user_repo=mock_repo, secret_key="test-secret")
        service.verify_password = Mock(return_value=True)

        result = service.login("test@example.com", "password123")

        assert result.success is False
        assert "suspended" in result.error.lower() or "inactive" in result.error.lower()


class TestAuthServiceToken:
    """Test cases for JWT token handling."""

    def test_verify_token_returns_user_id(self):
        """verify_token should return user_id for valid token."""
        from src.services import AuthService

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        # Generate a token
        token = service._generate_token(user_id=42)

        # Verify it
        user_id = service.verify_token(token)

        assert user_id == 42

    def test_verify_token_returns_none_for_invalid(self):
        """verify_token should return None for invalid token."""
        from src.services import AuthService

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        user_id = service.verify_token("invalid-token")

        assert user_id is None

    def test_verify_token_returns_none_for_expired(self):
        """verify_token should return None for expired token."""
        from src.services import AuthService
        import jwt
        from datetime import datetime, timedelta

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        # Create expired token
        payload = {
            "user_id": 42,
            "exp": datetime.utcnow() - timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, "test-secret", algorithm="HS256")

        user_id = service.verify_token(expired_token)

        assert user_id is None


class TestAuthServicePassword:
    """Test cases for password hashing."""

    def test_hash_password_returns_bcrypt_hash(self):
        """hash_password should return bcrypt hash."""
        from src.services import AuthService

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        hashed = service.hash_password("password123")

        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_returns_true_for_match(self):
        """verify_password should return True for matching password."""
        from src.services import AuthService

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        hashed = service.hash_password("password123")
        result = service.verify_password("password123", hashed)

        assert result is True

    def test_verify_password_returns_false_for_mismatch(self):
        """verify_password should return False for wrong password."""
        from src.services import AuthService

        mock_repo = Mock()
        service = AuthService(user_repo=mock_repo, secret_key="test-secret")

        hashed = service.hash_password("password123")
        result = service.verify_password("wrong-password", hashed)

        assert result is False
```

#### Step 2: Implement to pass

**File:** `python/api/src/services/auth_service.py`

```python
"""Authentication service implementation."""
import re
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from src.interfaces import IAuthService, IUserRepository, AuthResult
from src.models import User, UserStatus


class AuthService(IAuthService):
    """
    Authentication service.

    Handles registration, login, and JWT token management.
    """

    MIN_PASSWORD_LENGTH = 8
    TOKEN_EXPIRY_HOURS = 24

    def __init__(self, user_repo: IUserRepository, secret_key: str):
        """
        Initialize auth service.

        Args:
            user_repo: User repository for data access.
            secret_key: Secret key for JWT signing.
        """
        self._user_repo = user_repo
        self._secret_key = secret_key

    def register(self, email: str, password: str) -> AuthResult:
        """
        Register new user.

        Args:
            email: User email address.
            password: Plain text password.

        Returns:
            AuthResult with success status, user_id, and token.
        """
        # Validate email format
        if not self._is_valid_email(email):
            return AuthResult(success=False, error="Invalid email format")

        # Validate password strength
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return AuthResult(
                success=False,
                error=f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters",
            )

        # Check if email exists
        if self._user_repo.email_exists(email):
            return AuthResult(success=False, error="Email already registered")

        # Create user
        user = User(
            email=email.lower(),
            password_hash=self.hash_password(password),
            status=UserStatus.PENDING,
        )
        user = self._user_repo.save(user)

        # Generate token
        token = self._generate_token(user.id)

        return AuthResult(
            success=True,
            user_id=user.id,
            token=token,
        )

    def login(self, email: str, password: str) -> AuthResult:
        """
        Authenticate user and return JWT token.

        Args:
            email: User email address.
            password: Plain text password.

        Returns:
            AuthResult with success status and token.
        """
        # Find user
        user = self._user_repo.find_by_email(email.lower())
        if not user:
            return AuthResult(success=False, error="Invalid credentials")

        # Verify password
        if not self.verify_password(password, user.password_hash):
            return AuthResult(success=False, error="Invalid credentials")

        # Check user status
        if user.status == UserStatus.SUSPENDED:
            return AuthResult(success=False, error="Account is suspended")
        if user.status == UserStatus.DELETED:
            return AuthResult(success=False, error="Account not found")

        # Generate token
        token = self._generate_token(user.id)

        return AuthResult(
            success=True,
            user_id=user.id,
            token=token,
        )

    def verify_token(self, token: str) -> Optional[int]:
        """
        Verify JWT token and return user_id if valid.

        Args:
            token: JWT token string.

        Returns:
            User ID if token is valid, None otherwise.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=["HS256"],
            )
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password.

        Returns:
            Bcrypt hash string.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain text password to verify.
            hashed: Bcrypt hash to compare against.

        Returns:
            True if password matches hash.
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8"),
        )

    def _generate_token(self, user_id: int) -> str:
        """Generate JWT token for user."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRY_HOURS),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
```

---

### 2.2 UserService Implementation

**File:** `python/api/tests/unit/services/test_user_service.py`

```python
"""Tests for UserService."""
import pytest
from unittest.mock import Mock


class TestUserServiceGetUser:
    """Test cases for get_user."""

    def test_get_user_returns_user(self):
        """get_user should return user by ID."""
        from src.services import UserService
        from src.models import User

        mock_repo = Mock()
        mock_user = User(id=1, email="test@example.com", password_hash="hash")
        mock_repo.find_by_id.return_value = mock_user

        service = UserService(user_repo=mock_repo)
        result = service.get_user(1)

        assert result == mock_user
        mock_repo.find_by_id.assert_called_once_with(1)

    def test_get_user_returns_none_if_not_found(self):
        """get_user should return None if user not found."""
        from src.services import UserService

        mock_repo = Mock()
        mock_repo.find_by_id.return_value = None

        service = UserService(user_repo=mock_repo)
        result = service.get_user(999)

        assert result is None


class TestUserServiceUpdateDetails:
    """Test cases for update_user_details."""

    def test_update_user_details_creates_if_not_exists(self):
        """update_user_details should create details if not exists."""
        from src.services import UserService
        from src.models import User, UserDetails

        mock_user_repo = Mock()
        mock_details_repo = Mock()
        mock_user = User(id=1, email="test@example.com", password_hash="hash")
        mock_user.details = None
        mock_user_repo.find_by_id.return_value = mock_user
        mock_details_repo.save.return_value = UserDetails(
            id=1, user_id=1, first_name="John"
        )

        service = UserService(
            user_repo=mock_user_repo,
            details_repo=mock_details_repo,
        )
        result = service.update_user_details(1, {"first_name": "John"})

        assert result.first_name == "John"
        mock_details_repo.save.assert_called_once()

    def test_update_user_details_updates_existing(self):
        """update_user_details should update existing details."""
        from src.services import UserService
        from src.models import User, UserDetails

        mock_user_repo = Mock()
        mock_details_repo = Mock()
        existing_details = UserDetails(id=1, user_id=1, first_name="Old")
        mock_user = User(id=1, email="test@example.com", password_hash="hash")
        mock_user.details = existing_details
        mock_user_repo.find_by_id.return_value = mock_user
        mock_details_repo.save.return_value = existing_details

        service = UserService(
            user_repo=mock_user_repo,
            details_repo=mock_details_repo,
        )
        result = service.update_user_details(1, {"first_name": "New"})

        assert result.first_name == "New"


class TestUserServiceUpdateStatus:
    """Test cases for update_user_status."""

    def test_update_user_status_changes_status(self):
        """update_user_status should change user status."""
        from src.services import UserService
        from src.models import User, UserStatus

        mock_repo = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            password_hash="hash",
            status=UserStatus.PENDING,
        )
        mock_repo.find_by_id.return_value = mock_user
        mock_repo.save.return_value = mock_user

        service = UserService(user_repo=mock_repo)
        result = service.update_user_status(1, UserStatus.ACTIVE)

        assert result.status == UserStatus.ACTIVE
        mock_repo.save.assert_called_once()
```

**File:** `python/api/src/services/user_service.py`

```python
"""User management service implementation."""
from typing import Optional
from src.interfaces import IUserService, IUserRepository
from src.models import User, UserDetails, UserStatus


class UserService(IUserService):
    """
    User management service.

    Handles user profile and details management.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        details_repo: Optional["IUserDetailsRepository"] = None,
    ):
        """
        Initialize user service.

        Args:
            user_repo: User repository.
            details_repo: Optional UserDetails repository.
        """
        self._user_repo = user_repo
        self._details_repo = details_repo

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self._user_repo.find_by_id(user_id)

    def get_user_details(self, user_id: int) -> Optional[UserDetails]:
        """Get user details."""
        user = self._user_repo.find_by_id(user_id)
        if user:
            return user.details
        return None

    def update_user_details(self, user_id: int, details: dict) -> UserDetails:
        """
        Update user details.

        Args:
            user_id: User ID.
            details: Dictionary of detail fields to update.

        Returns:
            Updated UserDetails object.
        """
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        if user.details:
            # Update existing details
            user_details = user.details
        else:
            # Create new details
            user_details = UserDetails(user_id=user_id)

        # Update fields
        allowed_fields = [
            "first_name", "last_name", "address_line_1", "address_line_2",
            "city", "postal_code", "country", "phone",
        ]
        for field, value in details.items():
            if field in allowed_fields:
                setattr(user_details, field, value)

        return self._details_repo.save(user_details)

    def update_user_status(self, user_id: int, status: UserStatus) -> User:
        """
        Update user status.

        Args:
            user_id: User ID.
            status: New status.

        Returns:
            Updated User object.
        """
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.status = status
        return self._user_repo.save(user)
```

---

### 2.3 Marshmallow Schemas

**File:** `python/api/src/schemas/auth.py`

```python
"""Authentication request/response schemas."""
from marshmallow import Schema, fields, validate


class RegisterRequestSchema(Schema):
    """Schema for registration request."""

    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
    )


class LoginRequestSchema(Schema):
    """Schema for login request."""

    email = fields.Email(required=True)
    password = fields.Str(required=True)


class AuthResponseSchema(Schema):
    """Schema for authentication response."""

    success = fields.Bool(required=True)
    user_id = fields.Int(allow_none=True)
    token = fields.Str(allow_none=True)
    error = fields.Str(allow_none=True)


class UserSchema(Schema):
    """Schema for user representation."""

    id = fields.Int(dump_only=True)
    email = fields.Email(dump_only=True)
    status = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class UserDetailsSchema(Schema):
    """Schema for user details."""

    id = fields.Int(dump_only=True)
    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    address_line_1 = fields.Str(validate=validate.Length(max=255))
    address_line_2 = fields.Str(validate=validate.Length(max=255))
    city = fields.Str(validate=validate.Length(max=100))
    postal_code = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(validate=validate.Length(equal=2))
    phone = fields.Str(validate=validate.Length(max=20))
```

---

### 2.4 Auth Routes

**File:** `python/api/tests/integration/test_auth_routes.py`

```python
"""Integration tests for auth routes."""
import pytest


class TestRegisterRoute:
    """Test cases for POST /api/v1/auth/register."""

    def test_register_success(self, client, db):
        """Should register new user and return token."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        data = response.json
        assert data["success"] is True
        assert "token" in data
        assert "user_id" in data

    def test_register_duplicate_email(self, client, db, existing_user):
        """Should reject duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": existing_user.email,
                "password": "securepassword123",
            },
        )

        assert response.status_code == 400
        assert response.json["success"] is False

    def test_register_invalid_email(self, client):
        """Should reject invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 400


class TestLoginRoute:
    """Test cases for POST /api/v1/auth/login."""

    def test_login_success(self, client, existing_user):
        """Should login and return token."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": existing_user.email,
                "password": "testpassword",  # From fixture
            },
        )

        assert response.status_code == 200
        data = response.json
        assert data["success"] is True
        assert "token" in data

    def test_login_wrong_password(self, client, existing_user):
        """Should reject wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": existing_user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert response.json["success"] is False
```

**File:** `python/api/src/routes/auth.py`

```python
"""Authentication routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from marshmallow import ValidationError
from src.container import Container
from src.interfaces import IAuthService
from src.schemas.auth import (
    RegisterRequestSchema,
    LoginRequestSchema,
    AuthResponseSchema,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

register_schema = RegisterRequestSchema()
login_schema = LoginRequestSchema()
response_schema = AuthResponseSchema()


@auth_bp.route("/register", methods=["POST"])
@inject
def register(
    auth_service: IAuthService = Provide[Container.auth_service],
):
    """
    Register new user.

    POST /api/v1/auth/register
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    """
    # Validate request
    try:
        data = register_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"success": False, "errors": err.messages}), 400

    # Register user
    result = auth_service.register(data["email"], data["password"])

    if result.success:
        return jsonify(response_schema.dump(result)), 201
    else:
        return jsonify(response_schema.dump(result)), 400


@auth_bp.route("/login", methods=["POST"])
@inject
def login(
    auth_service: IAuthService = Provide[Container.auth_service],
):
    """
    Login user.

    POST /api/v1/auth/login
    {
        "email": "user@example.com",
        "password": "password"
    }
    """
    # Validate request
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"success": False, "errors": err.messages}), 400

    # Login
    result = auth_service.login(data["email"], data["password"])

    if result.success:
        return jsonify(response_schema.dump(result)), 200
    else:
        return jsonify(response_schema.dump(result)), 401
```

---

### 2.5 Auth Middleware

**File:** `python/api/src/middleware/auth.py`

```python
"""Authentication middleware."""
from functools import wraps
from flask import request, jsonify, g
from dependency_injector.wiring import inject, Provide
from src.container import Container
from src.interfaces import IAuthService


def require_auth(f):
    """
    Decorator to require authentication.

    Extracts JWT from Authorization header and validates it.
    Sets g.user_id on success.
    """
    @wraps(f)
    @inject
    def decorated(
        *args,
        auth_service: IAuthService = Provide[Container.auth_service],
        **kwargs,
    ):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401

        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid authorization header"}), 401

        token = parts[1]

        # Verify token
        user_id = auth_service.verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Set user_id in Flask's g object for route access
        g.user_id = user_id

        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """
    Decorator to require admin role.

    Must be used after @require_auth.
    """
    @wraps(f)
    @inject
    def decorated(
        *args,
        user_service: "IUserService" = Provide[Container.user_service],
        **kwargs,
    ):
        user_id = getattr(g, "user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        user = user_service.get_user(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)

    return decorated
```

---

### 2.6 User Routes

**File:** `python/api/src/routes/user.py`

```python
"""User management routes."""
from flask import Blueprint, request, jsonify, g
from dependency_injector.wiring import inject, Provide
from marshmallow import ValidationError
from src.container import Container
from src.interfaces import IUserService
from src.middleware.auth import require_auth
from src.schemas.auth import UserSchema, UserDetailsSchema

user_bp = Blueprint("user", __name__, url_prefix="/user")

user_schema = UserSchema()
details_schema = UserDetailsSchema()


@user_bp.route("/profile", methods=["GET"])
@require_auth
@inject
def get_profile(
    user_service: IUserService = Provide[Container.user_service],
):
    """
    Get current user profile.

    GET /api/v1/user/profile
    Authorization: Bearer <token>
    """
    user = user_service.get_user(g.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user_schema.dump(user)), 200


@user_bp.route("/details", methods=["GET"])
@require_auth
@inject
def get_details(
    user_service: IUserService = Provide[Container.user_service],
):
    """
    Get current user details.

    GET /api/v1/user/details
    Authorization: Bearer <token>
    """
    details = user_service.get_user_details(g.user_id)
    if not details:
        return jsonify({}), 200

    return jsonify(details_schema.dump(details)), 200


@user_bp.route("/details", methods=["PUT"])
@require_auth
@inject
def update_details(
    user_service: IUserService = Provide[Container.user_service],
):
    """
    Update current user details.

    PUT /api/v1/user/details
    Authorization: Bearer <token>
    {
        "first_name": "John",
        "last_name": "Doe",
        ...
    }
    """
    try:
        data = details_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    details = user_service.update_user_details(g.user_id, data)
    return jsonify(details_schema.dump(details)), 200
```

---

## Verification Checklist

```bash
# Run auth service tests
docker-compose run --rm python pytest tests/unit/services/test_auth_service.py -v

# Run user service tests
docker-compose run --rm python pytest tests/unit/services/test_user_service.py -v

# Run integration tests
docker-compose run --rm python pytest tests/integration/test_auth_routes.py -v

# Run all Sprint 2 tests
docker-compose run --rm python pytest tests/unit/services/ tests/integration/test_auth*.py -v

# Test endpoints manually
docker-compose up -d
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| AuthService | [ ] | Register, login, JWT |
| UserService | [ ] | Profile management |
| Auth schemas | [ ] | Marshmallow validation |
| Auth routes | [ ] | /register, /login |
| Auth middleware | [ ] | @require_auth, @require_admin |
| User routes | [ ] | /profile, /details |
| Integration tests | [ ] | Full flow tests |

---

## Next Sprint

[Sprint 3: Subscriptions](./sprint-3-subscriptions.md) - Tariff plans and subscription management.
