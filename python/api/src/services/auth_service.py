import os
import hashlib
import secrets
from datetime import datetime, timedelta
from src.models.admin_user import AdminUser


class AuthService:
    """Service for admin authentication."""

    def __init__(self):
        self._secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
        # Simple token storage (in production, use Redis or DB)
        self._tokens = {}

    def verify_admin_token(self, token: str) -> bool:
        """Verify if token is valid."""
        if not token:
            return False

        # For development: accept a static dev token
        if os.getenv('FLASK_ENV') == 'development' and token == 'dev-admin-token':
            return True

        # Check token in storage
        token_data = self._tokens.get(token)
        if not token_data:
            return False

        # Check expiration
        if datetime.utcnow() > token_data['expires_at']:
            del self._tokens[token]
            return False

        return True

    def authenticate(self, username: str, password: str) -> str:
        """Authenticate admin and return token."""
        user = AdminUser.query.filter_by(username=username, is_active=True).first()

        if not user or not user.check_password(password):
            return None

        # Generate token
        token = secrets.token_urlsafe(32)
        self._tokens[token] = {
            'user_id': user.id,
            'expires_at': datetime.utcnow() + timedelta(hours=24)
        }

        # Update last login
        user.last_login = datetime.utcnow()
        from src import db
        db.session.commit()

        return token

    def logout(self, token: str) -> bool:
        """Invalidate token."""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False
