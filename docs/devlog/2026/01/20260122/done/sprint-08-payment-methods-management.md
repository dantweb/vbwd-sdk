# Sprint 08: Payment Methods Management (Enterprise)

**Priority:** HIGH
**Estimated Effort:** Large
**Dependencies:** Sprint 04 (basic payment methods API)

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

## Overview

Implement a full-featured payment methods management system similar to enterprise e-commerce platforms (Shopware, OXID, Magento). This includes:

- Database model `payment_methods` with comprehensive fields
- Admin CRUD interface for payment method management
- Plugin architecture for payment provider integrations
- Integration with VBWD Core Component SDK

---

## Clarified Requirements

Based on stakeholder input:

| Requirement | Decision |
|-------------|----------|
| Credentials storage | Environment variables only (`config` for non-sensitive settings) |
| i18n translations | Include `payment_method_translations` table |
| Reorder UX | Native HTML5 drag-drop (no external library) |
| Fee handling | Configurable per method via `fee_charged_to` field |
| Invoice flow | Create invoice → show confirmation (current behavior) |
| Plugin example | Interface/architecture only (no concrete implementation) |
| Admin access | Standard admin role sufficient |
| Code field | **Immutable after creation** |
| Invoice FK | No FK, store code as plain string in invoices |

---

## Part 1: Data Model Design

### 1.1 PaymentMethod Model Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `id` | UUID | Primary key | Yes |
| `code` | VARCHAR(50) | Unique identifier (e.g., 'invoice', 'stripe'). **Immutable after creation** | Yes |
| `name` | VARCHAR(100) | Display name | Yes |
| `description` | TEXT | Detailed description | No |
| `short_description` | VARCHAR(255) | Brief description for checkout | No |
| `icon` | VARCHAR(255) | Icon class or URL | No |
| `plugin_id` | VARCHAR(100) | Associated plugin identifier (null for core) | No |
| `is_active` | BOOLEAN | Whether method is available | Yes |
| `is_default` | BOOLEAN | Default payment method | Yes |
| `position` | INTEGER | Sort order in lists | Yes |
| `min_amount` | DECIMAL(10,2) | Minimum order amount | No |
| `max_amount` | DECIMAL(10,2) | Maximum order amount | No |
| `currencies` | JSON | Supported currencies array | No |
| `countries` | JSON | Supported country codes array | No |
| `config` | JSON | **Non-sensitive** provider settings (credentials via env vars) | No |
| `fee_type` | VARCHAR(20) | 'fixed', 'percentage', 'none' | Yes |
| `fee_amount` | DECIMAL(10,4) | Fee amount (fixed or percentage) | No |
| `fee_charged_to` | VARCHAR(20) | 'customer' or 'merchant' - who pays the fee | Yes |
| `instructions` | TEXT | Payment instructions for customer | No |
| `created_at` | TIMESTAMP | Creation timestamp | Yes |
| `updated_at` | TIMESTAMP | Last update timestamp | Yes |

**Note:** Invoices store `payment_method_code` as plain string (no FK constraint) for historical data integrity.

### 1.2 Related Model: PaymentMethodTranslation (i18n)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `payment_method_id` | UUID | FK to payment_methods |
| `locale` | VARCHAR(5) | Locale code (e.g., 'en', 'de', 'fr') |
| `name` | VARCHAR(100) | Translated name |
| `description` | TEXT | Translated description |
| `short_description` | VARCHAR(255) | Translated short description |
| `instructions` | TEXT | Translated instructions |

### 1.3 Default Payment Method: Invoice

```python
# Default seed data
DEFAULT_INVOICE_METHOD = {
    'code': 'invoice',
    'name': 'Invoice',
    'description': 'Pay by invoice. You will receive an invoice via email after checkout.',
    'short_description': 'Pay by invoice',
    'icon': 'invoice',
    'plugin_id': None,  # Core method, no plugin
    'is_active': True,
    'is_default': True,
    'position': 1,
    'min_amount': None,
    'max_amount': None,
    'currencies': ['EUR', 'USD', 'GBP'],
    'countries': None,  # All countries
    'config': {},  # Non-sensitive settings only (credentials via env vars)
    'fee_type': 'none',
    'fee_amount': None,
    'fee_charged_to': 'customer',  # Default, but fee is 'none' anyway
    'instructions': 'You will receive an invoice via email. Please transfer the amount within 14 days.',
}
```

### 1.4 Security: Credentials via Environment Variables

Payment provider credentials (API keys, secrets) are **never** stored in the database. They are accessed via environment variables:

```python
# Example: Stripe credentials
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Example: PayPal credentials
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
```

The `config` JSON field stores only non-sensitive settings:
```python
# Example config for Stripe (non-sensitive)
{
    'supported_card_brands': ['visa', 'mastercard', 'amex'],
    'capture_method': 'automatic',  # or 'manual'
    'payment_method_types': ['card'],
}
```

---

## Part 2: TDD - Backend Tests FIRST

### 2.1 Unit Tests: PaymentMethod Model

**File:** `vbwd-backend/tests/unit/models/test_payment_method.py`

```python
import pytest
from uuid import uuid4
from decimal import Decimal
from src.models.payment_method import PaymentMethod


class TestPaymentMethodModel:
    """Unit tests for PaymentMethod model."""

    def test_create_payment_method_with_required_fields(self):
        """Should create payment method with required fields."""
        method = PaymentMethod(
            code='test_method',
            name='Test Method',
            is_active=True,
            is_default=False,
            position=1,
            fee_type='none',
        )

        assert method.code == 'test_method'
        assert method.name == 'Test Method'
        assert method.is_active is True

    def test_code_is_unique_constraint(self):
        """Code should be unique."""
        # This will be tested in integration tests
        pass

    def test_default_values(self):
        """Should have correct default values."""
        method = PaymentMethod(code='test', name='Test')

        assert method.is_active is True
        assert method.is_default is False
        assert method.position == 0
        assert method.fee_type == 'none'

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all relevant fields."""
        method = PaymentMethod(
            id=uuid4(),
            code='invoice',
            name='Invoice',
            description='Pay by invoice',
            short_description='Invoice payment',
            icon='invoice',
            plugin_id=None,
            is_active=True,
            is_default=True,
            position=1,
            min_amount=Decimal('10.00'),
            max_amount=Decimal('10000.00'),
            currencies=['EUR', 'USD'],
            countries=['DE', 'AT', 'CH'],
            fee_type='fixed',
            fee_amount=Decimal('2.50'),
            instructions='Pay within 14 days',
        )

        data = method.to_dict()

        assert data['code'] == 'invoice'
        assert data['name'] == 'Invoice'
        assert data['currencies'] == ['EUR', 'USD']
        assert data['fee_amount'] == 2.50

    def test_is_available_for_amount(self):
        """Should check if method available for given amount."""
        method = PaymentMethod(
            code='test',
            name='Test',
            min_amount=Decimal('10.00'),
            max_amount=Decimal('100.00'),
        )

        assert method.is_available_for_amount(Decimal('50.00')) is True
        assert method.is_available_for_amount(Decimal('5.00')) is False
        assert method.is_available_for_amount(Decimal('150.00')) is False

    def test_is_available_for_currency(self):
        """Should check if method available for given currency."""
        method = PaymentMethod(
            code='test',
            name='Test',
            currencies=['EUR', 'USD'],
        )

        assert method.is_available_for_currency('EUR') is True
        assert method.is_available_for_currency('GBP') is False

    def test_is_available_for_country(self):
        """Should check if method available for given country."""
        method = PaymentMethod(
            code='test',
            name='Test',
            countries=['DE', 'AT'],
        )

        assert method.is_available_for_country('DE') is True
        assert method.is_available_for_country('US') is False

    def test_calculate_fee_fixed(self):
        """Should calculate fixed fee correctly."""
        method = PaymentMethod(
            code='test',
            name='Test',
            fee_type='fixed',
            fee_amount=Decimal('2.50'),
        )

        assert method.calculate_fee(Decimal('100.00')) == Decimal('2.50')

    def test_calculate_fee_percentage(self):
        """Should calculate percentage fee correctly."""
        method = PaymentMethod(
            code='test',
            name='Test',
            fee_type='percentage',
            fee_amount=Decimal('2.5'),  # 2.5%
        )

        assert method.calculate_fee(Decimal('100.00')) == Decimal('2.50')

    def test_calculate_fee_none(self):
        """Should return zero for no fee."""
        method = PaymentMethod(
            code='test',
            name='Test',
            fee_type='none',
        )

        assert method.calculate_fee(Decimal('100.00')) == Decimal('0.00')
```

### 2.2 Unit Tests: PaymentMethodService

**File:** `vbwd-backend/tests/unit/services/test_payment_method_service.py`

```python
import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from src.services.payment_method_service import PaymentMethodService


class TestPaymentMethodService:
    """Unit tests for PaymentMethodService."""

    @pytest.fixture
    def mock_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_repo):
        return PaymentMethodService(repository=mock_repo)

    def test_get_active_methods(self, service, mock_repo):
        """Should return only active payment methods."""
        mock_repo.find_all_active.return_value = [
            Mock(code='invoice', is_active=True),
            Mock(code='stripe', is_active=True),
        ]

        methods = service.get_active_methods()

        assert len(methods) == 2
        mock_repo.find_all_active.assert_called_once()

    def test_get_available_methods_filters_by_context(self, service, mock_repo):
        """Should filter methods by amount, currency, country."""
        mock_method = Mock()
        mock_method.is_available_for_amount.return_value = True
        mock_method.is_available_for_currency.return_value = True
        mock_method.is_available_for_country.return_value = True

        mock_repo.find_all_active.return_value = [mock_method]

        methods = service.get_available_methods(
            amount=Decimal('100.00'),
            currency='EUR',
            country='DE',
        )

        assert len(methods) == 1

    def test_get_method_by_code(self, service, mock_repo):
        """Should return method by code."""
        mock_repo.find_by_code.return_value = Mock(code='invoice')

        method = service.get_by_code('invoice')

        assert method.code == 'invoice'
        mock_repo.find_by_code.assert_called_once_with('invoice')

    def test_create_method(self, service, mock_repo):
        """Should create new payment method."""
        mock_repo.find_by_code.return_value = None
        mock_repo.create.return_value = Mock(code='new_method')

        result = service.create({
            'code': 'new_method',
            'name': 'New Method',
        })

        assert result.code == 'new_method'

    def test_create_method_fails_for_duplicate_code(self, service, mock_repo):
        """Should fail if code already exists."""
        mock_repo.find_by_code.return_value = Mock(code='existing')

        with pytest.raises(ValueError, match='already exists'):
            service.create({'code': 'existing', 'name': 'Test'})

    def test_update_method(self, service, mock_repo):
        """Should update existing method."""
        existing = Mock(code='invoice')
        mock_repo.find_by_id.return_value = existing
        mock_repo.save.return_value = existing

        result = service.update('method-id', {'name': 'Updated Name'})

        assert mock_repo.save.called

    def test_set_default_clears_other_defaults(self, service, mock_repo):
        """Setting default should clear other defaults."""
        mock_repo.find_by_id.return_value = Mock(is_default=False)
        mock_repo.clear_defaults.return_value = None
        mock_repo.save.return_value = Mock(is_default=True)

        service.set_default('method-id')

        mock_repo.clear_defaults.assert_called_once()
```

### 2.3 Integration Tests: Payment Methods API

**File:** `vbwd-backend/tests/integration/routes/test_admin_payment_methods.py`

```python
import pytest

class TestAdminPaymentMethodsAPI:
    """Integration tests for admin payment methods endpoints."""

    def test_list_all_payment_methods(self, client, admin_auth_headers):
        """Should list all payment methods for admin."""
        response = client.get(
            "/api/v1/admin/payment-methods",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'methods' in data
        assert isinstance(data['methods'], list)

    def test_get_payment_method_by_id(self, client, admin_auth_headers, invoice_method):
        """Should get payment method by ID."""
        response = client.get(
            f"/api/v1/admin/payment-methods/{invoice_method.id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 'invoice'

    def test_create_payment_method(self, client, admin_auth_headers):
        """Should create new payment method."""
        response = client.post(
            "/api/v1/admin/payment-methods",
            headers=admin_auth_headers,
            json={
                'code': 'test_method',
                'name': 'Test Payment Method',
                'description': 'A test payment method',
                'is_active': True,
                'fee_type': 'fixed',
                'fee_amount': 1.50,
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['code'] == 'test_method'

    def test_create_fails_without_required_fields(self, client, admin_auth_headers):
        """Should fail without required fields."""
        response = client.post(
            "/api/v1/admin/payment-methods",
            headers=admin_auth_headers,
            json={'name': 'Missing Code'}
        )

        assert response.status_code == 400

    def test_update_payment_method(self, client, admin_auth_headers, invoice_method):
        """Should update payment method."""
        response = client.put(
            f"/api/v1/admin/payment-methods/{invoice_method.id}",
            headers=admin_auth_headers,
            json={'name': 'Updated Invoice', 'description': 'Updated description'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Invoice'

    def test_toggle_active_status(self, client, admin_auth_headers, invoice_method):
        """Should toggle active status."""
        response = client.patch(
            f"/api/v1/admin/payment-methods/{invoice_method.id}/toggle-active",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['is_active'] is False  # Toggled from True

    def test_set_default_method(self, client, admin_auth_headers, invoice_method):
        """Should set method as default."""
        response = client.patch(
            f"/api/v1/admin/payment-methods/{invoice_method.id}/set-default",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['is_default'] is True

    def test_delete_payment_method(self, client, admin_auth_headers, test_method):
        """Should delete non-core payment method."""
        response = client.delete(
            f"/api/v1/admin/payment-methods/{test_method.id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 204

    def test_cannot_delete_core_method(self, client, admin_auth_headers, invoice_method):
        """Should not delete core invoice method."""
        response = client.delete(
            f"/api/v1/admin/payment-methods/{invoice_method.id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 400
        assert 'cannot delete core' in response.get_json()['error'].lower()

    def test_reorder_methods(self, client, admin_auth_headers):
        """Should reorder payment methods."""
        response = client.post(
            "/api/v1/admin/payment-methods/reorder",
            headers=admin_auth_headers,
            json={
                'order': ['method-id-1', 'method-id-2', 'method-id-3']
            }
        )

        assert response.status_code == 200

    def test_requires_admin_auth(self, client):
        """Should require admin authentication."""
        response = client.get("/api/v1/admin/payment-methods")
        assert response.status_code == 401
```

---

## Part 3: Backend Implementation

### 3.1 PaymentMethod Model

**File:** `vbwd-backend/src/models/payment_method.py`

```python
"""Payment Method model."""
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.dialects.postgresql import UUID, JSON
from src.extensions import db


class PaymentMethod(db.Model):
    """
    Payment method configuration.

    Stores both core methods (invoice) and plugin-provided methods
    (Stripe, PayPal, etc.).
    """

    __tablename__ = 'payment_methods'

    # Primary key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Identification
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    icon = db.Column(db.String(255))

    # Plugin association (null for core methods)
    plugin_id = db.Column(db.String(100), nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)

    # Availability constraints
    min_amount = db.Column(db.Numeric(10, 2), nullable=True)
    max_amount = db.Column(db.Numeric(10, 2), nullable=True)
    currencies = db.Column(JSON, default=list)  # ['EUR', 'USD']
    countries = db.Column(JSON, default=list)   # ['DE', 'AT'] or [] for all

    # Fees
    fee_type = db.Column(db.String(20), default='none', nullable=False)  # 'none', 'fixed', 'percentage'
    fee_amount = db.Column(db.Numeric(10, 4), nullable=True)
    fee_charged_to = db.Column(db.String(20), default='customer', nullable=False)  # 'customer' or 'merchant'

    # Configuration
    config = db.Column(JSON, default=dict)  # Provider-specific settings
    instructions = db.Column(db.Text)  # Customer instructions

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    translations = db.relationship('PaymentMethodTranslation', backref='payment_method', lazy='dynamic')

    def __repr__(self):
        return f'<PaymentMethod {self.code}>'

    def to_dict(self, include_config: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'short_description': self.short_description,
            'icon': self.icon,
            'plugin_id': self.plugin_id,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'position': self.position,
            'min_amount': float(self.min_amount) if self.min_amount else None,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'currencies': self.currencies or [],
            'countries': self.countries or [],
            'fee_type': self.fee_type,
            'fee_amount': float(self.fee_amount) if self.fee_amount else None,
            'fee_charged_to': self.fee_charged_to,
            'instructions': self.instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_config:
            data['config'] = self.config or {}
        return data

    def to_public_dict(self) -> Dict[str, Any]:
        """Public view (no sensitive config)."""
        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'short_description': self.short_description,
            'icon': self.icon,
            'fee_type': self.fee_type,
            'fee_amount': float(self.fee_amount) if self.fee_amount else None,
            'instructions': self.instructions,
        }

    def is_available_for_amount(self, amount: Decimal) -> bool:
        """Check if method available for given amount."""
        if self.min_amount and amount < self.min_amount:
            return False
        if self.max_amount and amount > self.max_amount:
            return False
        return True

    def is_available_for_currency(self, currency: str) -> bool:
        """Check if method available for given currency."""
        if not self.currencies:  # Empty = all currencies
            return True
        return currency.upper() in [c.upper() for c in self.currencies]

    def is_available_for_country(self, country: str) -> bool:
        """Check if method available for given country."""
        if not self.countries:  # Empty = all countries
            return True
        return country.upper() in [c.upper() for c in self.countries]

    def calculate_fee(self, amount: Decimal) -> Decimal:
        """Calculate payment fee for given amount."""
        if self.fee_type == 'none' or not self.fee_amount:
            return Decimal('0.00')
        if self.fee_type == 'fixed':
            return Decimal(str(self.fee_amount))
        if self.fee_type == 'percentage':
            return (amount * Decimal(str(self.fee_amount)) / 100).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def is_core_method(self) -> bool:
        """Check if this is a core (non-plugin) method."""
        return self.plugin_id is None


class PaymentMethodTranslation(db.Model):
    """Payment method translations for i18n."""

    __tablename__ = 'payment_method_translations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    payment_method_id = db.Column(UUID(as_uuid=True), db.ForeignKey('payment_methods.id'), nullable=False)
    locale = db.Column(db.String(5), nullable=False)  # 'en', 'de', 'fr'
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    instructions = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('payment_method_id', 'locale', name='uq_payment_method_locale'),
    )
```

### 3.2 Migration

**File:** `vbwd-backend/alembic/versions/20260122_payment_methods.py`

```python
"""Add payment_methods table.

Revision ID: 20260122_payment_methods
Revises: [previous_migration]
Create Date: 2026-01-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260122_payment_methods'
down_revision = None  # Set to previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create payment_methods table
    op.create_table(
        'payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('short_description', sa.String(255)),
        sa.Column('icon', sa.String(255)),
        sa.Column('plugin_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False),
        sa.Column('position', sa.Integer, default=0, nullable=False),
        sa.Column('min_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('currencies', postgresql.JSON, default=[]),
        sa.Column('countries', postgresql.JSON, default=[]),
        sa.Column('fee_type', sa.String(20), default='none', nullable=False),
        sa.Column('fee_amount', sa.Numeric(10, 4), nullable=True),
        sa.Column('fee_charged_to', sa.String(20), default='customer', nullable=False),
        sa.Column('config', postgresql.JSON, default={}),
        sa.Column('instructions', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # Create translations table
    op.create_table(
        'payment_method_translations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('payment_methods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('locale', sa.String(5), nullable=False),
        sa.Column('name', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('short_description', sa.String(255)),
        sa.Column('instructions', sa.Text),
        sa.UniqueConstraint('payment_method_id', 'locale', name='uq_payment_method_locale'),
    )

    # Seed default Invoice method
    from uuid import uuid4
    from datetime import datetime

    op.execute(f"""
        INSERT INTO payment_methods (
            id, code, name, description, short_description, icon,
            plugin_id, is_active, is_default, position,
            currencies, fee_type, instructions, created_at, updated_at
        ) VALUES (
            '{uuid4()}', 'invoice', 'Invoice',
            'Pay by invoice. You will receive an invoice via email after checkout.',
            'Pay by invoice',
            'invoice',
            NULL, TRUE, TRUE, 1,
            '["EUR", "USD", "GBP"]'::json,
            'none',
            'You will receive an invoice via email. Please transfer the amount within 14 days.',
            '{datetime.utcnow().isoformat()}',
            '{datetime.utcnow().isoformat()}'
        )
    """)


def downgrade():
    op.drop_table('payment_method_translations')
    op.drop_table('payment_methods')
```

### 3.3 Admin Routes

**File:** `vbwd-backend/src/routes/admin/payment_methods.py`

```python
"""Admin routes for payment method management."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.extensions import db
from src.decorators import admin_required
from src.services.payment_method_service import PaymentMethodService
from src.repositories.payment_method_repository import PaymentMethodRepository

admin_payment_methods_bp = Blueprint(
    "admin_payment_methods",
    __name__,
    url_prefix="/api/v1/admin/payment-methods"
)


def get_service():
    """Get service instance."""
    repo = PaymentMethodRepository(db.session)
    return PaymentMethodService(repository=repo)


@admin_payment_methods_bp.route("", methods=["GET"])
@jwt_required()
@admin_required
def list_methods():
    """List all payment methods."""
    service = get_service()
    methods = service.get_all()
    return jsonify({
        "methods": [m.to_dict(include_config=True) for m in methods]
    }), 200


@admin_payment_methods_bp.route("/<method_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_method(method_id):
    """Get payment method by ID."""
    service = get_service()
    method = service.get_by_id(method_id)
    if not method:
        return jsonify({"error": "Payment method not found"}), 404
    return jsonify(method.to_dict(include_config=True)), 200


@admin_payment_methods_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_method():
    """Create new payment method."""
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('code'):
        return jsonify({"error": "Code is required"}), 400
    if not data.get('name'):
        return jsonify({"error": "Name is required"}), 400

    service = get_service()
    try:
        method = service.create(data)
        return jsonify(method.to_dict(include_config=True)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@admin_payment_methods_bp.route("/<method_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_method(method_id):
    """Update payment method."""
    data = request.get_json() or {}
    service = get_service()

    try:
        method = service.update(method_id, data)
        if not method:
            return jsonify({"error": "Payment method not found"}), 404
        return jsonify(method.to_dict(include_config=True)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@admin_payment_methods_bp.route("/<method_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_method(method_id):
    """Delete payment method."""
    service = get_service()
    method = service.get_by_id(method_id)

    if not method:
        return jsonify({"error": "Payment method not found"}), 404

    if method.is_core_method and method.code == 'invoice':
        return jsonify({"error": "Cannot delete core Invoice payment method"}), 400

    service.delete(method_id)
    return "", 204


@admin_payment_methods_bp.route("/<method_id>/toggle-active", methods=["PATCH"])
@jwt_required()
@admin_required
def toggle_active(method_id):
    """Toggle payment method active status."""
    service = get_service()
    method = service.toggle_active(method_id)
    if not method:
        return jsonify({"error": "Payment method not found"}), 404
    return jsonify(method.to_dict()), 200


@admin_payment_methods_bp.route("/<method_id>/set-default", methods=["PATCH"])
@jwt_required()
@admin_required
def set_default(method_id):
    """Set payment method as default."""
    service = get_service()
    method = service.set_default(method_id)
    if not method:
        return jsonify({"error": "Payment method not found"}), 404
    return jsonify(method.to_dict()), 200


@admin_payment_methods_bp.route("/reorder", methods=["POST"])
@jwt_required()
@admin_required
def reorder_methods():
    """Reorder payment methods."""
    data = request.get_json() or {}
    order = data.get('order', [])

    if not order:
        return jsonify({"error": "Order array required"}), 400

    service = get_service()
    service.reorder(order)
    return jsonify({"success": True}), 200
```

---

## Part 4: Admin Frontend (Using VBWD Core Component SDK)

### 4.1 E2E Tests FIRST

**File:** `vbwd-frontend/admin/vue/tests/e2e/admin-payment-methods.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './fixtures/admin.fixtures';

test.describe('Admin Payment Methods Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('displays payment methods list', async ({ page }) => {
    await page.goto('/admin/payment-methods');

    await expect(page.locator('[data-testid="payment-methods-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="payment-method-invoice"]')).toBeVisible();
  });

  test('shows Invoice as default method', async ({ page }) => {
    await page.goto('/admin/payment-methods');

    const invoiceRow = page.locator('[data-testid="payment-method-invoice"]');
    await expect(invoiceRow.locator('[data-testid="default-badge"]')).toBeVisible();
  });

  test('can create new payment method', async ({ page }) => {
    await page.goto('/admin/payment-methods');
    await page.click('[data-testid="add-method-btn"]');

    await expect(page.locator('[data-testid="payment-method-form"]')).toBeVisible();

    await page.fill('[data-testid="method-code"]', 'test_method');
    await page.fill('[data-testid="method-name"]', 'Test Method');
    await page.fill('[data-testid="method-description"]', 'A test payment method');
    await page.selectOption('[data-testid="method-fee-type"]', 'fixed');
    await page.fill('[data-testid="method-fee-amount"]', '1.50');

    await page.click('[data-testid="save-method-btn"]');

    await expect(page.locator('[data-testid="payment-method-test_method"]')).toBeVisible();
  });

  test('can edit payment method', async ({ page }) => {
    await page.goto('/admin/payment-methods');

    await page.click('[data-testid="payment-method-invoice"] [data-testid="edit-btn"]');

    await expect(page.locator('[data-testid="payment-method-form"]')).toBeVisible();

    await page.fill('[data-testid="method-name"]', 'Invoice (Updated)');
    await page.click('[data-testid="save-method-btn"]');

    await expect(page.locator('[data-testid="payment-method-invoice"]')).toContainText('Invoice (Updated)');
  });

  test('can toggle method active status', async ({ page }) => {
    await page.goto('/admin/payment-methods');

    const invoiceRow = page.locator('[data-testid="payment-method-invoice"]');
    const toggleBtn = invoiceRow.locator('[data-testid="toggle-active-btn"]');

    await toggleBtn.click();

    // Should show as inactive
    await expect(invoiceRow.locator('[data-testid="inactive-badge"]')).toBeVisible();
  });

  test('cannot delete core Invoice method', async ({ page }) => {
    await page.goto('/admin/payment-methods');

    const invoiceRow = page.locator('[data-testid="payment-method-invoice"]');
    const deleteBtn = invoiceRow.locator('[data-testid="delete-btn"]');

    // Delete button should be disabled for core method
    await expect(deleteBtn).toBeDisabled();
  });

  test('can reorder payment methods via drag and drop', async ({ page }) => {
    // Create additional method first
    await page.goto('/admin/payment-methods');
    await page.click('[data-testid="add-method-btn"]');
    await page.fill('[data-testid="method-code"]', 'second_method');
    await page.fill('[data-testid="method-name"]', 'Second Method');
    await page.click('[data-testid="save-method-btn"]');

    // Verify order can be changed
    const firstMethod = page.locator('[data-testid="payment-methods-list"] > div').first();
    const secondMethod = page.locator('[data-testid="payment-methods-list"] > div').nth(1);

    // Drag second to first position
    await secondMethod.dragTo(firstMethod);

    // Verify new order persists after reload
    await page.reload();
    const newFirst = page.locator('[data-testid="payment-methods-list"] > div').first();
    await expect(newFirst).toHaveAttribute('data-testid', 'payment-method-second_method');
  });

  test('shows plugin badge for plugin-based methods', async ({ page }) => {
    // This test assumes a plugin-based method exists
    await page.goto('/admin/payment-methods');

    const pluginMethod = page.locator('[data-plugin-id]').first();
    if (await pluginMethod.isVisible()) {
      await expect(pluginMethod.locator('[data-testid="plugin-badge"]')).toBeVisible();
    }
  });
});
```

### 4.2 Admin Store (Using VBWD Core SDK Patterns)

**File:** `vbwd-frontend/admin/vue/src/stores/paymentMethods.ts`

```typescript
/**
 * Payment Methods Admin Store
 *
 * Uses patterns from VBWD Core Component SDK:
 * - Type-safe API client
 * - Reactive state management
 * - Error handling patterns
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/api';

export interface PaymentMethod {
  id: string;
  code: string;
  name: string;
  description?: string;
  short_description?: string;
  icon?: string;
  plugin_id?: string;
  is_active: boolean;
  is_default: boolean;
  position: number;
  min_amount?: number;
  max_amount?: number;
  currencies: string[];
  countries: string[];
  fee_type: 'none' | 'fixed' | 'percentage';
  fee_amount?: number;
  fee_charged_to: 'customer' | 'merchant';
  config?: Record<string, unknown>;
  instructions?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentMethodFormData {
  code: string;
  name: string;
  description?: string;
  short_description?: string;
  icon?: string;
  is_active?: boolean;
  min_amount?: number;
  max_amount?: number;
  currencies?: string[];
  countries?: string[];
  fee_type?: 'none' | 'fixed' | 'percentage';
  fee_amount?: number;
  fee_charged_to?: 'customer' | 'merchant';
  config?: Record<string, unknown>;
  instructions?: string;
}

export const usePaymentMethodsStore = defineStore('adminPaymentMethods', () => {
  // State
  const methods = ref<PaymentMethod[]>([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref<string | null>(null);
  const selectedMethod = ref<PaymentMethod | null>(null);

  // Getters
  const activeMethods = computed(() =>
    methods.value.filter(m => m.is_active)
  );

  const defaultMethod = computed(() =>
    methods.value.find(m => m.is_default)
  );

  const sortedMethods = computed(() =>
    [...methods.value].sort((a, b) => a.position - b.position)
  );

  const pluginMethods = computed(() =>
    methods.value.filter(m => m.plugin_id !== null)
  );

  const coreMethods = computed(() =>
    methods.value.filter(m => m.plugin_id === null)
  );

  // Actions
  async function fetchAll(): Promise<void> {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get('/admin/payment-methods');
      methods.value = response.methods;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to load payment methods';
    } finally {
      loading.value = false;
    }
  }

  async function fetchOne(id: string): Promise<PaymentMethod | null> {
    loading.value = true;
    error.value = null;

    try {
      const method = await api.get(`/admin/payment-methods/${id}`);
      selectedMethod.value = method;
      return method;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to load payment method';
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function create(data: PaymentMethodFormData): Promise<PaymentMethod | null> {
    saving.value = true;
    error.value = null;

    try {
      const method = await api.post('/admin/payment-methods', data);
      methods.value.push(method);
      return method;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to create payment method';
      return null;
    } finally {
      saving.value = false;
    }
  }

  async function update(id: string, data: Partial<PaymentMethodFormData>): Promise<PaymentMethod | null> {
    saving.value = true;
    error.value = null;

    try {
      const method = await api.put(`/admin/payment-methods/${id}`, data);
      const index = methods.value.findIndex(m => m.id === id);
      if (index >= 0) {
        methods.value[index] = method;
      }
      return method;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to update payment method';
      return null;
    } finally {
      saving.value = false;
    }
  }

  async function remove(id: string): Promise<boolean> {
    saving.value = true;
    error.value = null;

    try {
      await api.delete(`/admin/payment-methods/${id}`);
      methods.value = methods.value.filter(m => m.id !== id);
      return true;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to delete payment method';
      return false;
    } finally {
      saving.value = false;
    }
  }

  async function toggleActive(id: string): Promise<PaymentMethod | null> {
    try {
      const method = await api.patch(`/admin/payment-methods/${id}/toggle-active`);
      const index = methods.value.findIndex(m => m.id === id);
      if (index >= 0) {
        methods.value[index] = method;
      }
      return method;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to toggle status';
      return null;
    }
  }

  async function setDefault(id: string): Promise<PaymentMethod | null> {
    try {
      const method = await api.patch(`/admin/payment-methods/${id}/set-default`);
      // Clear other defaults
      methods.value.forEach(m => m.is_default = false);
      const index = methods.value.findIndex(m => m.id === id);
      if (index >= 0) {
        methods.value[index] = method;
      }
      return method;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to set default';
      return null;
    }
  }

  async function reorder(order: string[]): Promise<boolean> {
    try {
      await api.post('/admin/payment-methods/reorder', { order });
      // Update local positions
      order.forEach((id, index) => {
        const method = methods.value.find(m => m.id === id);
        if (method) {
          method.position = index;
        }
      });
      return true;
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to reorder';
      return false;
    }
  }

  function clearError(): void {
    error.value = null;
  }

  function selectMethod(method: PaymentMethod | null): void {
    selectedMethod.value = method;
  }

  return {
    // State
    methods,
    loading,
    saving,
    error,
    selectedMethod,

    // Getters
    activeMethods,
    defaultMethod,
    sortedMethods,
    pluginMethods,
    coreMethods,

    // Actions
    fetchAll,
    fetchOne,
    create,
    update,
    remove,
    toggleActive,
    setDefault,
    reorder,
    clearError,
    selectMethod,
  };
});
```

### 4.3 Admin View Component

**File:** `vbwd-frontend/admin/vue/src/views/PaymentMethods.vue`

```vue
<template>
  <div class="payment-methods-page">
    <div class="page-header">
      <h1>Payment Methods</h1>
      <button
        data-testid="add-method-btn"
        class="btn primary"
        @click="openCreateForm"
      >
        Add Payment Method
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="loading">Loading...</div>

    <!-- Error -->
    <div v-if="store.error" class="error-banner">
      {{ store.error }}
      <button @click="store.clearError">Dismiss</button>
    </div>

    <!-- Methods List -->
    <div
      v-else
      data-testid="payment-methods-list"
      class="methods-list"
    >
      <div
        v-for="method in store.sortedMethods"
        :key="method.id"
        :data-testid="`payment-method-${method.code}`"
        :data-plugin-id="method.plugin_id"
        class="method-card"
        :class="{ inactive: !method.is_active }"
      >
        <div class="method-icon">
          <span :class="`icon-${method.icon || 'payment'}`"></span>
        </div>

        <div class="method-info">
          <h3>{{ method.name }}</h3>
          <p>{{ method.short_description || method.description }}</p>

          <div class="badges">
            <span v-if="method.is_default" data-testid="default-badge" class="badge default">
              Default
            </span>
            <span v-if="!method.is_active" data-testid="inactive-badge" class="badge inactive">
              Inactive
            </span>
            <span v-if="method.plugin_id" data-testid="plugin-badge" class="badge plugin">
              Plugin: {{ method.plugin_id }}
            </span>
            <span v-if="method.fee_type !== 'none'" class="badge fee">
              Fee: {{ formatFee(method) }}
            </span>
          </div>
        </div>

        <div class="method-actions">
          <button
            data-testid="edit-btn"
            class="btn icon"
            title="Edit"
            @click="openEditForm(method)"
          >
            ✏️
          </button>

          <button
            data-testid="toggle-active-btn"
            class="btn icon"
            :title="method.is_active ? 'Deactivate' : 'Activate'"
            @click="store.toggleActive(method.id)"
          >
            {{ method.is_active ? '🔴' : '🟢' }}
          </button>

          <button
            v-if="!method.is_default"
            data-testid="set-default-btn"
            class="btn icon"
            title="Set as default"
            @click="store.setDefault(method.id)"
          >
            ⭐
          </button>

          <button
            data-testid="delete-btn"
            class="btn icon danger"
            title="Delete"
            :disabled="method.code === 'invoice'"
            @click="confirmDelete(method)"
          >
            🗑️
          </button>
        </div>

        <div class="drag-handle" title="Drag to reorder">⋮⋮</div>
      </div>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay">
      <div class="modal" data-testid="payment-method-form">
        <div class="modal-header">
          <h2>{{ editingMethod ? 'Edit' : 'Add' }} Payment Method</h2>
          <button class="close-btn" @click="closeForm">&times;</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>Code *</label>
            <input
              v-model="formData.code"
              data-testid="method-code"
              :disabled="!!editingMethod"
              placeholder="unique_code"
            />
          </div>

          <div class="form-group">
            <label>Name *</label>
            <input
              v-model="formData.name"
              data-testid="method-name"
              placeholder="Payment Method Name"
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="formData.description"
              data-testid="method-description"
              rows="3"
            />
          </div>

          <div class="form-group">
            <label>Short Description</label>
            <input
              v-model="formData.short_description"
              data-testid="method-short-description"
              placeholder="Brief description for checkout"
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Fee Type</label>
              <select v-model="formData.fee_type" data-testid="method-fee-type">
                <option value="none">No Fee</option>
                <option value="fixed">Fixed Amount</option>
                <option value="percentage">Percentage</option>
              </select>
            </div>

            <div class="form-group" v-if="formData.fee_type !== 'none'">
              <label>Fee Amount</label>
              <input
                v-model.number="formData.fee_amount"
                data-testid="method-fee-amount"
                type="number"
                step="0.01"
                :placeholder="formData.fee_type === 'percentage' ? '2.5%' : '€1.50'"
              />
            </div>
          </div>

          <div class="form-group" v-if="formData.fee_type !== 'none'">
            <label>Fee Charged To</label>
            <select v-model="formData.fee_charged_to" data-testid="method-fee-charged-to">
              <option value="customer">Customer pays fee</option>
              <option value="merchant">Merchant pays fee</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Min Amount</label>
              <input
                v-model.number="formData.min_amount"
                data-testid="method-min-amount"
                type="number"
                step="0.01"
              />
            </div>

            <div class="form-group">
              <label>Max Amount</label>
              <input
                v-model.number="formData.max_amount"
                data-testid="method-max-amount"
                type="number"
                step="0.01"
              />
            </div>
          </div>

          <div class="form-group">
            <label>Supported Currencies (comma-separated)</label>
            <input
              v-model="currenciesInput"
              data-testid="method-currencies"
              placeholder="EUR, USD, GBP"
            />
          </div>

          <div class="form-group">
            <label>Supported Countries (comma-separated, empty = all)</label>
            <input
              v-model="countriesInput"
              data-testid="method-countries"
              placeholder="DE, AT, CH"
            />
          </div>

          <div class="form-group">
            <label>Customer Instructions</label>
            <textarea
              v-model="formData.instructions"
              data-testid="method-instructions"
              rows="3"
              placeholder="Instructions shown to customer after selecting this method"
            />
          </div>

          <div class="form-group">
            <label>
              <input type="checkbox" v-model="formData.is_active" />
              Active
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn secondary" @click="closeForm">Cancel</button>
          <button
            data-testid="save-method-btn"
            class="btn primary"
            :disabled="store.saving || !isFormValid"
            @click="saveMethod"
          >
            {{ store.saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deletingMethod" class="modal-overlay">
      <div class="modal confirm-modal">
        <h3>Delete Payment Method?</h3>
        <p>Are you sure you want to delete "{{ deletingMethod.name }}"?</p>
        <div class="modal-footer">
          <button class="btn secondary" @click="deletingMethod = null">Cancel</button>
          <button class="btn danger" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { usePaymentMethodsStore, type PaymentMethod, type PaymentMethodFormData } from '@/stores/paymentMethods';

const store = usePaymentMethodsStore();

// Form state
const showForm = ref(false);
const editingMethod = ref<PaymentMethod | null>(null);
const deletingMethod = ref<PaymentMethod | null>(null);

const formData = reactive<PaymentMethodFormData>({
  code: '',
  name: '',
  description: '',
  short_description: '',
  is_active: true,
  fee_type: 'none',
  fee_amount: undefined,
  fee_charged_to: 'customer',
  min_amount: undefined,
  max_amount: undefined,
  currencies: [],
  countries: [],
  instructions: '',
});

// Comma-separated inputs
const currenciesInput = ref('');
const countriesInput = ref('');

const isFormValid = computed(() => {
  return formData.code && formData.name;
});

function formatFee(method: PaymentMethod): string {
  if (method.fee_type === 'fixed') {
    return `€${method.fee_amount?.toFixed(2)}`;
  }
  if (method.fee_type === 'percentage') {
    return `${method.fee_amount}%`;
  }
  return 'None';
}

function openCreateForm() {
  editingMethod.value = null;
  Object.assign(formData, {
    code: '',
    name: '',
    description: '',
    short_description: '',
    is_active: true,
    fee_type: 'none',
    fee_amount: undefined,
    fee_charged_to: 'customer',
    min_amount: undefined,
    max_amount: undefined,
    instructions: '',
  });
  currenciesInput.value = '';
  countriesInput.value = '';
  showForm.value = true;
}

function openEditForm(method: PaymentMethod) {
  editingMethod.value = method;
  Object.assign(formData, {
    code: method.code,
    name: method.name,
    description: method.description || '',
    short_description: method.short_description || '',
    is_active: method.is_active,
    fee_type: method.fee_type,
    fee_amount: method.fee_amount,
    fee_charged_to: method.fee_charged_to || 'customer',
    min_amount: method.min_amount,
    max_amount: method.max_amount,
    instructions: method.instructions || '',
  });
  currenciesInput.value = method.currencies?.join(', ') || '';
  countriesInput.value = method.countries?.join(', ') || '';
  showForm.value = true;
}

function closeForm() {
  showForm.value = false;
  editingMethod.value = null;
}

async function saveMethod() {
  // Parse currencies and countries
  formData.currencies = currenciesInput.value
    .split(',')
    .map(c => c.trim().toUpperCase())
    .filter(Boolean);

  formData.countries = countriesInput.value
    .split(',')
    .map(c => c.trim().toUpperCase())
    .filter(Boolean);

  let result;
  if (editingMethod.value) {
    result = await store.update(editingMethod.value.id, formData);
  } else {
    result = await store.create(formData);
  }

  if (result) {
    closeForm();
  }
}

function confirmDelete(method: PaymentMethod) {
  deletingMethod.value = method;
}

async function doDelete() {
  if (deletingMethod.value) {
    await store.remove(deletingMethod.value.id);
    deletingMethod.value = null;
  }
}

onMounted(() => {
  store.fetchAll();
});
</script>

<style scoped>
/* Styles following admin app patterns */
.payment-methods-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.methods-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.method-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.method-card.inactive {
  opacity: 0.6;
  background: #f5f5f5;
}

.method-icon {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 8px;
  font-size: 24px;
}

.method-info {
  flex: 1;
}

.method-info h3 {
  margin: 0 0 5px 0;
}

.method-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.badges {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge.default { background: #e3f2fd; color: #1976d2; }
.badge.inactive { background: #ffebee; color: #c62828; }
.badge.plugin { background: #f3e5f5; color: #7b1fa2; }
.badge.fee { background: #fff3e0; color: #ef6c00; }

.method-actions {
  display: flex;
  gap: 5px;
}

.btn.icon {
  padding: 8px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.btn.icon:hover {
  background: #f0f0f0;
}

.btn.icon:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.drag-handle {
  color: #ccc;
  cursor: grab;
  padding: 10px;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 20px;
  border-top: 1px solid #eee;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn.primary { background: #3498db; color: white; }
.btn.secondary { background: #ecf0f1; color: #333; }
.btn.danger { background: #e74c3c; color: white; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
```

---

## Part 5: Plugin Integration Architecture

### 5.1 Backend: Payment Provider Plugin Interface

Payment plugins (Stripe, PayPal) should implement the `PaymentProviderPlugin` interface and register their payment method:

```python
# Example: StripePaymentPlugin
class StripePaymentPlugin(PaymentProviderPlugin):
    """Stripe payment provider plugin."""

    @property
    def name(self) -> str:
        return "stripe"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def component(self) -> str:
        return "payment"

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Stripe SDK."""
        import stripe
        stripe.api_key = config.get('secret_key')

    def activate(self) -> None:
        """Register Stripe payment method in database."""
        from src.services.payment_method_service import PaymentMethodService

        service = PaymentMethodService.get_instance()
        service.register_plugin_method({
            'code': 'stripe',
            'name': 'Credit Card (Stripe)',
            'description': 'Pay securely with credit or debit card',
            'short_description': 'Credit/Debit Card',
            'icon': 'credit-card',
            'plugin_id': self.name,
            'fee_type': 'percentage',
            'fee_amount': 2.9,  # Stripe's fee
        })

    def deactivate(self) -> None:
        """Deactivate Stripe payment method."""
        service = PaymentMethodService.get_instance()
        service.deactivate_plugin_method('stripe')
```

### 5.2 Frontend: Plugin Payment Method Component

Using VBWD Core Component SDK, plugins can register their checkout components:

```typescript
// Example: stripe-payment-plugin/index.ts
import type { IPlugin, IPlatformSDK } from '@vbwd/view-component';

export const stripePaymentPlugin: IPlugin = {
  name: 'stripe-payment',
  version: '1.0.0',
  description: 'Stripe payment integration',

  install(sdk: IPlatformSDK) {
    // Register Stripe checkout component
    sdk.addComponent('StripePaymentForm', () =>
      import('./components/StripePaymentForm.vue')
    );

    // Register store for Stripe state
    sdk.createStore('stripePayment', {
      state: () => ({
        clientSecret: null,
        paymentIntentId: null,
      }),
      actions: {
        async createPaymentIntent(amount: number, currency: string) {
          // Call backend to create Stripe PaymentIntent
        },
      },
    });
  },

  activate() {
    console.log('Stripe payment plugin activated');
  },

  deactivate() {
    console.log('Stripe payment plugin deactivated');
  },
};
```

### 5.3 Checkout Integration

The checkout page dynamically loads payment method components based on the selected method's plugin:

```vue
<!-- Checkout.vue - Payment method section -->
<template>
  <div class="payment-method-form">
    <!-- Core Invoice method -->
    <InvoicePaymentInfo
      v-if="selectedMethod?.code === 'invoice'"
      :instructions="selectedMethod.instructions"
    />

    <!-- Plugin-based methods loaded dynamically -->
    <component
      v-else-if="selectedMethod?.plugin_id"
      :is="getPluginComponent(selectedMethod.plugin_id)"
      :method="selectedMethod"
      @payment-ready="onPaymentReady"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePluginRegistry } from '@vbwd/view-component';

const registry = usePluginRegistry();

function getPluginComponent(pluginId: string) {
  // Get component from plugin registry
  const componentName = `${pluginId}-payment-form`;
  return registry.getComponent(componentName);
}
</script>
```

---

## Part 6: SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Model handles data, Service handles business logic, Repository handles persistence |
| **O** - Open/Closed | New payment methods added via plugins without modifying core code |
| **L** - Liskov Substitution | All payment plugins implement PaymentProviderPlugin interface |
| **I** - Interface Segregation | PaymentMethod model has specific availability check methods |
| **D** - Dependency Inversion | Service depends on Repository interface, not implementation |

## No Over-engineering Rules

1. ✅ i18n via separate translations table (not in-model JSON)
2. ✅ Simple fee calculation (fixed/percentage), not complex pricing rules
3. ✅ Plugin registration via code, not config files
4. ✅ No caching layer (premature optimization)
5. ✅ Admin drag-drop uses native HTML5 (no library)

---

## Verification Checklist

### Backend
- [ ] Unit tests for PaymentMethod model FAILING
- [ ] Unit tests for PaymentMethodService FAILING
- [ ] Integration tests for admin routes FAILING
- [ ] Model implemented with all fields
- [ ] Migration created and tested
- [ ] Service with CRUD operations
- [ ] Admin routes registered
- [ ] All backend tests PASSING

### Frontend (Admin)
- [ ] E2E tests for admin view FAILING
- [ ] Store implemented with actions
- [ ] PaymentMethods.vue view component
- [ ] Form validation
- [ ] All frontend tests PASSING

### Integration
- [ ] Invoice method seeded by default
- [ ] User checkout shows active methods
- [ ] Plugin methods can register

## Run Tests

> **All tests run in Docker containers.**

### Backend (from `vbwd-backend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --unit           # Unit tests
./bin/pre-commit-check.sh --integration    # Integration tests
./bin/pre-commit-check.sh                  # Full check

# Makefile commands
make test-unit -- -k "payment_method"
make test-integration -- -k "TestAdminPaymentMethods"

# Full regression before commit
make pre-commit
```

### Database Migration

```bash
# Create migration
docker-compose exec api flask db migrate -m "add payment_methods"

# Run migration
docker-compose exec api flask db upgrade
```

### Frontend Admin (from `vbwd-frontend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --admin --unit   # Unit tests
./bin/pre-commit-check.sh --admin --e2e    # E2E tests
./bin/pre-commit-check.sh --admin --style  # Lint + TypeScript

# From vbwd-frontend/admin/vue/
npm run test -- --grep "paymentMethods"
npm run test:e2e -- admin-payment-methods.spec.ts

# ⚠️ IMPORTANT: Rebuild after changing .vue or .ts files
npm run build  # Required before E2E tests!

# Full regression
npm run test && npm run test:e2e
```
