# Sprint 1: Data Layer

**Goal:** Implement domain models and repository layer with full test coverage.

**Prerequisites:** Sprint 0 complete

---

## Objectives

- [ ] User model with status/role enums
- [ ] UserDetails model
- [ ] UserCase model
- [ ] Currency model (with default + exchange rates)
- [ ] Tax model (VAT and regional taxes)
- [ ] TarifPlan model (with multi-currency pricing)
- [ ] Subscription model with lifecycle states
- [ ] UserInvoice model with payment states + tax breakdown
- [ ] Base repository implementation
- [ ] All entity repositories
- [ ] Database migrations

---

## Tasks

### 1.1 Base Model and Enums

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/models/test_base.py`

```python
"""Tests for base model functionality."""
import pytest
from datetime import datetime


class TestBaseModel:
    """Test cases for BaseModel."""

    def test_base_model_has_id(self):
        """BaseModel should have id field."""
        from src.models.base import BaseModel

        assert hasattr(BaseModel, "id")

    def test_base_model_has_timestamps(self):
        """BaseModel should have created_at and updated_at."""
        from src.models.base import BaseModel

        assert hasattr(BaseModel, "created_at")
        assert hasattr(BaseModel, "updated_at")


class TestUserStatus:
    """Test cases for UserStatus enum."""

    def test_user_status_values(self):
        """UserStatus should have expected values."""
        from src.models.enums import UserStatus

        assert UserStatus.PENDING.value == "pending"
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.SUSPENDED.value == "suspended"
        assert UserStatus.DELETED.value == "deleted"


class TestUserRole:
    """Test cases for UserRole enum."""

    def test_user_role_values(self):
        """UserRole should have expected values."""
        from src.models.enums import UserRole

        assert UserRole.USER.value == "user"
        assert UserRole.ADMIN.value == "admin"


class TestSubscriptionStatus:
    """Test cases for SubscriptionStatus enum."""

    def test_subscription_status_values(self):
        """SubscriptionStatus should have expected values."""
        from src.models.enums import SubscriptionStatus

        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.INACTIVE.value == "inactive"
        assert SubscriptionStatus.CANCELLED.value == "cancelled"
        assert SubscriptionStatus.EXPIRED.value == "expired"


class TestInvoiceStatus:
    """Test cases for InvoiceStatus enum."""

    def test_invoice_status_values(self):
        """InvoiceStatus should have expected values."""
        from src.models.enums import InvoiceStatus

        assert InvoiceStatus.INVOICED.value == "invoiced"
        assert InvoiceStatus.PAID.value == "paid"
        assert InvoiceStatus.EXPIRED.value == "expired"
        assert InvoiceStatus.CANCELLED.value == "cancelled"
```

#### Step 2: Implement to pass

**File:** `python/api/src/models/enums.py`

```python
"""Enumeration types for domain models."""
from enum import Enum


class UserStatus(str, Enum):
    """User account status."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, Enum):
    """User role for authorization."""

    USER = "user"
    ADMIN = "admin"


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvoiceStatus(str, Enum):
    """Invoice payment status."""

    INVOICED = "invoiced"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BillingPeriod(str, Enum):
    """Tariff plan billing period."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ONE_TIME = "one_time"


class PaymentMethod(str, Enum):
    """Payment method type."""

    PAYPAL = "paypal"
    STRIPE = "stripe"
    MANUAL = "manual"


class UserCaseStatus(str, Enum):
    """User case status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
```

**File:** `python/api/src/models/base.py`

```python
"""Base model with common fields."""
from datetime import datetime
from src.extensions import db


class BaseModel(db.Model):
    """
    Abstract base model with common fields.

    All models inherit from this to get:
    - Auto-increment primary key
    - Created/updated timestamps
    """

    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

---

### 1.2 User Model

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/models/test_user.py`

```python
"""Tests for User model."""
import pytest
from datetime import datetime


class TestUserModel:
    """Test cases for User model."""

    def test_user_has_required_fields(self):
        """User should have all required fields."""
        from src.models import User

        # Check columns exist
        columns = [c.name for c in User.__table__.columns]

        assert "id" in columns
        assert "email" in columns
        assert "password_hash" in columns
        assert "status" in columns
        assert "role" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_user_email_is_unique(self):
        """User email should have unique constraint."""
        from src.models import User

        email_column = User.__table__.columns["email"]
        assert email_column.unique is True

    def test_user_default_status_is_pending(self):
        """New user should have pending status by default."""
        from src.models import User
        from src.models.enums import UserStatus

        user = User(email="test@example.com", password_hash="hash")

        assert user.status == UserStatus.PENDING

    def test_user_default_role_is_user(self):
        """New user should have user role by default."""
        from src.models import User
        from src.models.enums import UserRole

        user = User(email="test@example.com", password_hash="hash")

        assert user.role == UserRole.USER

    def test_user_is_active_property(self):
        """User.is_active should return True for active users."""
        from src.models import User
        from src.models.enums import UserStatus

        user = User(email="test@example.com", password_hash="hash")
        user.status = UserStatus.ACTIVE

        assert user.is_active is True

        user.status = UserStatus.SUSPENDED
        assert user.is_active is False

    def test_user_is_admin_property(self):
        """User.is_admin should return True for admin users."""
        from src.models import User
        from src.models.enums import UserRole

        user = User(email="test@example.com", password_hash="hash")

        assert user.is_admin is False

        user.role = UserRole.ADMIN
        assert user.is_admin is True

    def test_user_to_dict_excludes_password(self):
        """User.to_dict should exclude password_hash."""
        from src.models import User

        user = User(
            id=1,
            email="test@example.com",
            password_hash="secret_hash",
        )

        data = user.to_dict()

        assert "email" in data
        assert "password_hash" not in data

    def test_user_repr(self):
        """User should have meaningful repr."""
        from src.models import User

        user = User(id=1, email="test@example.com", password_hash="hash")

        assert "User" in repr(user)
        assert "test@example.com" in repr(user)
```

#### Step 2: Implement to pass

**File:** `python/api/src/models/user.py`

```python
"""User domain model."""
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import UserStatus, UserRole


class User(BaseModel):
    """
    User account model.

    Stores core authentication data. Personal details
    are stored separately in UserDetails for GDPR compliance.
    """

    __tablename__ = "user"

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING,
        index=True,
    )
    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
    )

    # Relationships
    details = db.relationship(
        "UserDetails",
        backref="user",
        uselist=False,
        lazy="joined",
    )
    subscriptions = db.relationship(
        "Subscription",
        backref="user",
        lazy="dynamic",
    )
    invoices = db.relationship(
        "UserInvoice",
        backref="user",
        lazy="dynamic",
    )
    cases = db.relationship(
        "UserCase",
        backref="user",
        lazy="dynamic",
    )

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def to_dict(self) -> dict:
        """
        Convert to dictionary, excluding sensitive data.

        Returns:
            Dictionary representation without password_hash.
        """
        return {
            "id": self.id,
            "email": self.email,
            "status": self.status.value,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
```

---

### 1.3 UserDetails Model

**File:** `python/api/tests/unit/models/test_user_details.py`

```python
"""Tests for UserDetails model."""
import pytest


class TestUserDetailsModel:
    """Test cases for UserDetails model."""

    def test_user_details_has_required_fields(self):
        """UserDetails should have all required fields."""
        from src.models import UserDetails

        columns = [c.name for c in UserDetails.__table__.columns]

        assert "id" in columns
        assert "user_id" in columns
        assert "first_name" in columns
        assert "last_name" in columns
        assert "address_line_1" in columns
        assert "address_line_2" in columns
        assert "city" in columns
        assert "postal_code" in columns
        assert "country" in columns
        assert "phone" in columns

    def test_user_details_user_id_is_unique(self):
        """Each user should have at most one UserDetails."""
        from src.models import UserDetails

        user_id_column = UserDetails.__table__.columns["user_id"]
        assert user_id_column.unique is True

    def test_user_details_full_name_property(self):
        """UserDetails.full_name should combine first and last name."""
        from src.models import UserDetails

        details = UserDetails(first_name="John", last_name="Doe")

        assert details.full_name == "John Doe"

    def test_user_details_full_address_property(self):
        """UserDetails.full_address should format complete address."""
        from src.models import UserDetails

        details = UserDetails(
            address_line_1="123 Main St",
            address_line_2="Apt 4",
            city="Berlin",
            postal_code="10115",
            country="DE",
        )

        address = details.full_address
        assert "123 Main St" in address
        assert "Berlin" in address
        assert "10115" in address
```

**File:** `python/api/src/models/user_details.py`

```python
"""UserDetails domain model."""
from src.extensions import db
from src.models.base import BaseModel


class UserDetails(BaseModel):
    """
    User private details model.

    Separated from User for GDPR compliance.
    Contains PII that may need to be deleted separately.
    """

    __tablename__ = "user_details"

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    address_line_1 = db.Column(db.String(255))
    address_line_2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(2))  # ISO 3166-1 alpha-2
    phone = db.Column(db.String(20))

    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        lines = [
            self.address_line_1,
            self.address_line_2,
            f"{self.postal_code} {self.city}".strip(),
            self.country,
        ]
        return "\n".join(line for line in lines if line)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city": self.city,
            "postal_code": self.postal_code,
            "country": self.country,
            "phone": self.phone,
        }

    def __repr__(self) -> str:
        return f"<UserDetails(user_id={self.user_id}, name='{self.full_name}')>"
```

---

### 1.4 Currency Model

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/models/test_currency.py`

```python
"""Tests for Currency model."""
import pytest
from decimal import Decimal


class TestCurrencyModel:
    """Test cases for Currency model."""

    def test_currency_has_required_fields(self):
        """Currency should have all required fields."""
        from src.models import Currency

        columns = [c.name for c in Currency.__table__.columns]

        assert "id" in columns
        assert "code" in columns
        assert "name" in columns
        assert "symbol" in columns
        assert "exchange_rate" in columns
        assert "is_default" in columns
        assert "is_active" in columns

    def test_currency_code_is_unique(self):
        """Currency code should be unique."""
        from src.models import Currency

        code_column = Currency.__table__.columns["code"]
        assert code_column.unique is True

    def test_currency_exchange_rate_defaults_to_one(self):
        """Default currency should have exchange_rate of 1.0."""
        from src.models import Currency

        currency = Currency(
            code="EUR",
            name="Euro",
            symbol="€",
            is_default=True,
        )

        assert currency.exchange_rate == Decimal("1.0")

    def test_currency_convert_to_method(self):
        """Currency should convert amounts to other currencies."""
        from src.models import Currency

        eur = Currency(code="EUR", name="Euro", symbol="€", exchange_rate=Decimal("1.0"))
        usd = Currency(code="USD", name="US Dollar", symbol="$", exchange_rate=Decimal("1.08"))

        # 100 EUR = 108 USD
        amount_in_usd = eur.convert_to(Decimal("100"), usd)
        assert amount_in_usd == Decimal("108.00")

    def test_currency_convert_from_default_method(self):
        """Currency should convert from default currency."""
        from src.models import Currency

        usd = Currency(code="USD", name="US Dollar", symbol="$", exchange_rate=Decimal("1.08"))

        # 100 in default currency = 108 USD
        amount = usd.convert_from_default(Decimal("100"))
        assert amount == Decimal("108.00")

    def test_currency_format_method(self):
        """Currency.format should format amount with symbol."""
        from src.models import Currency

        eur = Currency(code="EUR", name="Euro", symbol="€")

        formatted = eur.format(Decimal("29.99"))
        assert "29.99" in formatted
        assert "€" in formatted
```

#### Step 2: Implement to pass

**File:** `python/api/src/models/currency.py`

```python
"""Currency domain model."""
from decimal import Decimal, ROUND_HALF_UP
from src.extensions import db
from src.models.base import BaseModel


class Currency(BaseModel):
    """
    Currency model with exchange rates.

    One currency is marked as default (is_default=True).
    All prices are stored in default currency.
    Other currencies use exchange_rate for conversion.
    """

    __tablename__ = "currency"

    code = db.Column(
        db.String(3),
        unique=True,
        nullable=False,
        index=True,
    )  # ISO 4217 code (EUR, USD, GBP)
    name = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    exchange_rate = db.Column(
        db.Numeric(10, 6),
        nullable=False,
        default=Decimal("1.0"),
    )  # Rate relative to default currency
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    decimal_places = db.Column(db.Integer, nullable=False, default=2)

    def convert_from_default(self, amount: Decimal) -> Decimal:
        """
        Convert amount from default currency to this currency.

        Args:
            amount: Amount in default currency.

        Returns:
            Amount in this currency, rounded to decimal_places.
        """
        converted = amount * self.exchange_rate
        return converted.quantize(
            Decimal(10) ** -self.decimal_places,
            rounding=ROUND_HALF_UP,
        )

    def convert_to_default(self, amount: Decimal) -> Decimal:
        """
        Convert amount from this currency to default currency.

        Args:
            amount: Amount in this currency.

        Returns:
            Amount in default currency.
        """
        if self.exchange_rate == 0:
            raise ValueError("Exchange rate cannot be zero")
        return (amount / self.exchange_rate).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def convert_to(self, amount: Decimal, target: "Currency") -> Decimal:
        """
        Convert amount from this currency to target currency.

        Args:
            amount: Amount in this currency.
            target: Target currency.

        Returns:
            Amount in target currency.
        """
        # First convert to default, then to target
        in_default = self.convert_to_default(amount)
        return target.convert_from_default(in_default)

    def format(self, amount: Decimal) -> str:
        """
        Format amount with currency symbol.

        Args:
            amount: Amount to format.

        Returns:
            Formatted string with symbol.
        """
        formatted_amount = f"{amount:.{self.decimal_places}f}"
        return f"{self.symbol}{formatted_amount}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "exchange_rate": str(self.exchange_rate),
            "is_default": self.is_default,
            "is_active": self.is_active,
        }

    def __repr__(self) -> str:
        return f"<Currency(code='{self.code}', rate={self.exchange_rate})>"
```

---

### 1.5 Tax Model

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/models/test_tax.py`

```python
"""Tests for Tax model."""
import pytest
from decimal import Decimal


class TestTaxModel:
    """Test cases for Tax model."""

    def test_tax_has_required_fields(self):
        """Tax should have all required fields."""
        from src.models import Tax

        columns = [c.name for c in Tax.__table__.columns]

        assert "id" in columns
        assert "name" in columns
        assert "code" in columns
        assert "rate" in columns
        assert "country_code" in columns
        assert "region_code" in columns
        assert "is_active" in columns

    def test_tax_code_is_unique(self):
        """Tax code should be unique."""
        from src.models import Tax

        code_column = Tax.__table__.columns["code"]
        assert code_column.unique is True

    def test_tax_rate_is_percentage(self):
        """Tax rate should be stored as percentage (e.g., 19.0 for 19%)."""
        from src.models import Tax

        vat_de = Tax(
            name="German VAT",
            code="VAT_DE",
            rate=Decimal("19.0"),
            country_code="DE",
        )

        assert vat_de.rate == Decimal("19.0")

    def test_tax_calculate_method(self):
        """Tax.calculate should compute tax amount."""
        from src.models import Tax

        vat = Tax(name="VAT", code="VAT_DE", rate=Decimal("19.0"))

        # 100 EUR * 19% = 19 EUR tax
        tax_amount = vat.calculate(Decimal("100.00"))
        assert tax_amount == Decimal("19.00")

    def test_tax_calculate_gross_method(self):
        """Tax.calculate_gross should add tax to net amount."""
        from src.models import Tax

        vat = Tax(name="VAT", code="VAT_DE", rate=Decimal("19.0"))

        # 100 EUR net + 19% = 119 EUR gross
        gross = vat.calculate_gross(Decimal("100.00"))
        assert gross == Decimal("119.00")

    def test_tax_extract_net_method(self):
        """Tax.extract_net should extract net from gross amount."""
        from src.models import Tax

        vat = Tax(name="VAT", code="VAT_DE", rate=Decimal("19.0"))

        # 119 EUR gross - 19% = 100 EUR net
        net = vat.extract_net(Decimal("119.00"))
        assert net == Decimal("100.00")

    def test_tax_is_applicable_for_country(self):
        """Tax.is_applicable should check country/region."""
        from src.models import Tax

        vat_de = Tax(
            name="German VAT",
            code="VAT_DE",
            rate=Decimal("19.0"),
            country_code="DE",
        )

        assert vat_de.is_applicable("DE") is True
        assert vat_de.is_applicable("FR") is False

    def test_tax_zero_rate(self):
        """Tax with zero rate should return zero tax."""
        from src.models import Tax

        exempt = Tax(name="Tax Exempt", code="EXEMPT", rate=Decimal("0.0"))

        assert exempt.calculate(Decimal("100.00")) == Decimal("0.00")


class TestTaxRateModel:
    """Test cases for TaxRate (historical rates)."""

    def test_tax_rate_has_required_fields(self):
        """TaxRate should track historical rates."""
        from src.models import TaxRate

        columns = [c.name for c in TaxRate.__table__.columns]

        assert "id" in columns
        assert "tax_id" in columns
        assert "rate" in columns
        assert "valid_from" in columns
        assert "valid_to" in columns
```

#### Step 2: Implement to pass

**File:** `python/api/src/models/tax.py`

```python
"""Tax domain models."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import Optional
from src.extensions import db
from src.models.base import BaseModel


class Tax(BaseModel):
    """
    Tax configuration model.

    Supports VAT, sales tax, and regional taxes.
    Rates are stored as percentages (e.g., 19.0 for 19%).
    """

    __tablename__ = "tax"

    name = db.Column(db.String(100), nullable=False)
    code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )  # e.g., VAT_DE, VAT_FR, SALES_TAX_CA
    description = db.Column(db.Text)
    rate = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )  # Percentage (19.0 = 19%)
    country_code = db.Column(
        db.String(2),
        index=True,
    )  # ISO 3166-1 alpha-2
    region_code = db.Column(db.String(10))  # State/province code
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_inclusive = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )  # True if prices include tax

    # Relationship to historical rates
    historical_rates = db.relationship(
        "TaxRate",
        backref="tax",
        lazy="dynamic",
    )

    def calculate(self, net_amount: Decimal) -> Decimal:
        """
        Calculate tax amount from net amount.

        Args:
            net_amount: Amount before tax.

        Returns:
            Tax amount.
        """
        tax = (net_amount * self.rate / Decimal("100"))
        return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_gross(self, net_amount: Decimal) -> Decimal:
        """
        Calculate gross amount (net + tax).

        Args:
            net_amount: Amount before tax.

        Returns:
            Gross amount including tax.
        """
        return net_amount + self.calculate(net_amount)

    def extract_net(self, gross_amount: Decimal) -> Decimal:
        """
        Extract net amount from gross (tax-inclusive) amount.

        Args:
            gross_amount: Amount including tax.

        Returns:
            Net amount before tax.
        """
        divisor = Decimal("1") + (self.rate / Decimal("100"))
        net = gross_amount / divisor
        return net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def extract_tax(self, gross_amount: Decimal) -> Decimal:
        """
        Extract tax amount from gross amount.

        Args:
            gross_amount: Amount including tax.

        Returns:
            Tax portion of gross amount.
        """
        net = self.extract_net(gross_amount)
        return gross_amount - net

    def is_applicable(
        self,
        country_code: str,
        region_code: Optional[str] = None,
    ) -> bool:
        """
        Check if this tax applies to given location.

        Args:
            country_code: ISO country code.
            region_code: Optional state/region code.

        Returns:
            True if tax applies.
        """
        if self.country_code and self.country_code != country_code:
            return False
        if self.region_code and self.region_code != region_code:
            return False
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "rate": str(self.rate),
            "country_code": self.country_code,
            "region_code": self.region_code,
            "is_active": self.is_active,
            "is_inclusive": self.is_inclusive,
        }

    def __repr__(self) -> str:
        return f"<Tax(code='{self.code}', rate={self.rate}%)>"


class TaxRate(BaseModel):
    """
    Historical tax rates.

    Tracks rate changes over time for accurate
    invoice recalculation.
    """

    __tablename__ = "tax_rate"

    tax_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tax.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rate = db.Column(db.Numeric(5, 2), nullable=False)
    valid_from = db.Column(db.Date, nullable=False)
    valid_to = db.Column(db.Date)  # NULL means still valid

    def is_valid_on(self, check_date: date) -> bool:
        """Check if rate was valid on given date."""
        if check_date < self.valid_from:
            return False
        if self.valid_to and check_date > self.valid_to:
            return False
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tax_id": self.tax_id,
            "rate": str(self.rate),
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
        }
```

---

### 1.6 TarifPlanPrice Model (Multi-Currency Pricing)

**File:** `python/api/tests/unit/models/test_tarif_plan_price.py`

```python
"""Tests for TarifPlanPrice model."""
import pytest
from decimal import Decimal


class TestTarifPlanPriceModel:
    """Test cases for TarifPlanPrice model."""

    def test_tarif_plan_price_has_required_fields(self):
        """TarifPlanPrice should have all required fields."""
        from src.models import TarifPlanPrice

        columns = [c.name for c in TarifPlanPrice.__table__.columns]

        assert "id" in columns
        assert "tarif_plan_id" in columns
        assert "currency_id" in columns
        assert "price" in columns
        assert "is_auto_calculated" in columns

    def test_tarif_plan_price_unique_constraint(self):
        """Each plan should have at most one price per currency."""
        from src.models import TarifPlanPrice

        # Check unique constraint exists on (tarif_plan_id, currency_id)
        constraints = TarifPlanPrice.__table__.constraints
        unique_constraints = [c for c in constraints if hasattr(c, 'columns')]
        # Verify the constraint includes both columns
        assert any(
            'tarif_plan_id' in str(c.columns) and 'currency_id' in str(c.columns)
            for c in unique_constraints
        )
```

**File:** `python/api/src/models/tarif_plan_price.py`

```python
"""TarifPlanPrice domain model for multi-currency support."""
from decimal import Decimal
from src.extensions import db
from src.models.base import BaseModel


class TarifPlanPrice(BaseModel):
    """
    Tariff plan price in specific currency.

    Allows setting fixed prices per currency or
    auto-calculating from default currency.
    """

    __tablename__ = "tarif_plan_price"
    __table_args__ = (
        db.UniqueConstraint(
            "tarif_plan_id",
            "currency_id",
            name="uq_tarif_plan_currency",
        ),
    )

    tarif_plan_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tarif_plan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    currency_id = db.Column(
        db.BigInteger,
        db.ForeignKey("currency.id"),
        nullable=False,
    )
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_auto_calculated = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )  # True = calculated from default, False = manually set

    # Relationships
    currency = db.relationship("Currency")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tarif_plan_id": self.tarif_plan_id,
            "currency_id": self.currency_id,
            "currency_code": self.currency.code if self.currency else None,
            "price": str(self.price),
            "is_auto_calculated": self.is_auto_calculated,
        }

    def __repr__(self) -> str:
        return f"<TarifPlanPrice(plan={self.tarif_plan_id}, currency={self.currency_id}, price={self.price})>"
```

---

### 1.7 Updated TarifPlan Model (with Tax support)

**File:** `python/api/tests/unit/models/test_tarif_plan.py`

```python
"""Tests for TarifPlan model."""
import pytest
from decimal import Decimal


class TestTarifPlanModel:
    """Test cases for TarifPlan model."""

    def test_tarif_plan_has_required_fields(self):
        """TarifPlan should have all required fields."""
        from src.models import TarifPlan

        columns = [c.name for c in TarifPlan.__table__.columns]

        assert "id" in columns
        assert "name" in columns
        assert "slug" in columns
        assert "description" in columns
        assert "price" in columns
        assert "currency" in columns
        assert "billing_period" in columns
        assert "features" in columns
        assert "is_active" in columns
        assert "sort_order" in columns

    def test_tarif_plan_slug_is_unique(self):
        """TarifPlan slug should be unique."""
        from src.models import TarifPlan

        slug_column = TarifPlan.__table__.columns["slug"]
        assert slug_column.unique is True

    def test_tarif_plan_price_is_decimal(self):
        """TarifPlan price should handle decimal values."""
        from src.models import TarifPlan
        from src.models.enums import BillingPeriod

        plan = TarifPlan(
            name="Pro",
            slug="pro",
            price=Decimal("29.99"),
            currency="EUR",
            billing_period=BillingPeriod.MONTHLY,
        )

        assert plan.price == Decimal("29.99")

    def test_tarif_plan_features_as_json(self):
        """TarifPlan features should store as JSON."""
        from src.models import TarifPlan
        from src.models.enums import BillingPeriod

        features = ["Feature A", "Feature B", "Feature C"]
        plan = TarifPlan(
            name="Pro",
            slug="pro",
            price=Decimal("29.99"),
            currency="EUR",
            billing_period=BillingPeriod.MONTHLY,
            features=features,
        )

        assert plan.features == features

    def test_tarif_plan_default_is_active(self):
        """TarifPlan should be active by default."""
        from src.models import TarifPlan
        from src.models.enums import BillingPeriod

        plan = TarifPlan(
            name="Pro",
            slug="pro",
            price=Decimal("29.99"),
            currency="EUR",
            billing_period=BillingPeriod.MONTHLY,
        )

        assert plan.is_active is True

    def test_tarif_plan_is_recurring_property(self):
        """TarifPlan.is_recurring for non-one_time plans."""
        from src.models import TarifPlan
        from src.models.enums import BillingPeriod

        monthly_plan = TarifPlan(
            name="Monthly",
            slug="monthly",
            price=Decimal("9.99"),
            currency="EUR",
            billing_period=BillingPeriod.MONTHLY,
        )
        assert monthly_plan.is_recurring is True

        one_time_plan = TarifPlan(
            name="Lifetime",
            slug="lifetime",
            price=Decimal("199.99"),
            currency="EUR",
            billing_period=BillingPeriod.ONE_TIME,
        )
        assert one_time_plan.is_recurring is False
```

**File:** `python/api/src/models/tarif_plan.py`

```python
"""TarifPlan domain model."""
from decimal import Decimal
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import BillingPeriod


class TarifPlan(BaseModel):
    """
    Tariff plan model.

    Defines subscription plans with pricing and features.
    """

    __tablename__ = "tarif_plan"

    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="EUR")
    billing_period = db.Column(
        db.Enum(BillingPeriod),
        nullable=False,
    )
    features = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, default=0)

    # Relationships
    subscriptions = db.relationship(
        "Subscription",
        backref="tarif_plan",
        lazy="dynamic",
    )
    invoices = db.relationship(
        "UserInvoice",
        backref="tarif_plan",
        lazy="dynamic",
    )

    @property
    def is_recurring(self) -> bool:
        """Check if this is a recurring subscription plan."""
        return self.billing_period != BillingPeriod.ONE_TIME

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price": str(self.price),
            "currency": self.currency,
            "billing_period": self.billing_period.value,
            "features": self.features,
            "is_active": self.is_active,
            "is_recurring": self.is_recurring,
        }

    def __repr__(self) -> str:
        return f"<TarifPlan(slug='{self.slug}', price={self.price})>"
```

---

### 1.5 Subscription Model

**File:** `python/api/tests/unit/models/test_subscription.py`

```python
"""Tests for Subscription model."""
import pytest
from datetime import datetime, timedelta


class TestSubscriptionModel:
    """Test cases for Subscription model."""

    def test_subscription_has_required_fields(self):
        """Subscription should have all required fields."""
        from src.models import Subscription

        columns = [c.name for c in Subscription.__table__.columns]

        assert "id" in columns
        assert "user_id" in columns
        assert "tarif_plan_id" in columns
        assert "status" in columns
        assert "started_at" in columns
        assert "expires_at" in columns
        assert "cancelled_at" in columns

    def test_subscription_default_status_is_inactive(self):
        """New subscription should be inactive until payment."""
        from src.models import Subscription
        from src.models.enums import SubscriptionStatus

        sub = Subscription(user_id=1, tarif_plan_id=1)

        assert sub.status == SubscriptionStatus.INACTIVE

    def test_subscription_is_valid_property(self):
        """Subscription.is_valid should check status and expiry."""
        from src.models import Subscription
        from src.models.enums import SubscriptionStatus

        # Active and not expired
        sub = Subscription(
            user_id=1,
            tarif_plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        assert sub.is_valid is True

        # Active but expired
        sub.expires_at = datetime.utcnow() - timedelta(days=1)
        assert sub.is_valid is False

        # Inactive
        sub.status = SubscriptionStatus.INACTIVE
        sub.expires_at = datetime.utcnow() + timedelta(days=30)
        assert sub.is_valid is False

    def test_subscription_days_remaining_property(self):
        """Subscription.days_remaining should calculate correctly."""
        from src.models import Subscription
        from src.models.enums import SubscriptionStatus

        sub = Subscription(
            user_id=1,
            tarif_plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=15),
        )

        # Should be approximately 15 (may be 14-15 depending on timing)
        assert 14 <= sub.days_remaining <= 15

    def test_subscription_activate_method(self):
        """Subscription.activate should set status and dates."""
        from src.models import Subscription
        from src.models.enums import SubscriptionStatus

        sub = Subscription(user_id=1, tarif_plan_id=1)
        sub.activate(duration_days=30)

        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.started_at is not None
        assert sub.expires_at is not None
        assert sub.days_remaining >= 29

    def test_subscription_cancel_method(self):
        """Subscription.cancel should set status and cancelled_at."""
        from src.models import Subscription
        from src.models.enums import SubscriptionStatus

        sub = Subscription(
            user_id=1,
            tarif_plan_id=1,
            status=SubscriptionStatus.ACTIVE,
        )
        sub.cancel()

        assert sub.status == SubscriptionStatus.CANCELLED
        assert sub.cancelled_at is not None
```

**File:** `python/api/src/models/subscription.py`

```python
"""Subscription domain model."""
from datetime import datetime, timedelta
from typing import Optional
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import SubscriptionStatus


class Subscription(BaseModel):
    """
    User subscription model.

    Tracks subscription lifecycle from creation through expiration.
    """

    __tablename__ = "subscription"

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tarif_plan_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tarif_plan.id"),
        nullable=False,
    )
    status = db.Column(
        db.Enum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.INACTIVE,
        index=True,
    )
    started_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, index=True)
    cancelled_at = db.Column(db.DateTime)

    # Relationships
    invoices = db.relationship(
        "UserInvoice",
        backref="subscription",
        lazy="dynamic",
    )

    @property
    def is_valid(self) -> bool:
        """Check if subscription is currently valid."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until expiration."""
        if not self.expires_at:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def activate(self, duration_days: int) -> None:
        """
        Activate subscription.

        Args:
            duration_days: Number of days the subscription is valid.
        """
        now = datetime.utcnow()
        self.status = SubscriptionStatus.ACTIVE
        self.started_at = now
        self.expires_at = now + timedelta(days=duration_days)

    def cancel(self) -> None:
        """Cancel subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()

    def expire(self) -> None:
        """Mark subscription as expired."""
        self.status = SubscriptionStatus.EXPIRED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tarif_plan_id": self.tarif_plan_id,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "days_remaining": self.days_remaining,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
```

---

### 1.6 UserInvoice Model

**File:** `python/api/tests/unit/models/test_user_invoice.py`

```python
"""Tests for UserInvoice model."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta


class TestUserInvoiceModel:
    """Test cases for UserInvoice model."""

    def test_user_invoice_has_required_fields(self):
        """UserInvoice should have all required fields."""
        from src.models import UserInvoice

        columns = [c.name for c in UserInvoice.__table__.columns]

        assert "id" in columns
        assert "user_id" in columns
        assert "tarif_plan_id" in columns
        assert "subscription_id" in columns
        assert "invoice_number" in columns
        assert "amount" in columns
        assert "currency" in columns
        assert "status" in columns
        assert "payment_method" in columns
        assert "payment_ref" in columns
        assert "invoiced_at" in columns
        assert "paid_at" in columns
        assert "expires_at" in columns

    def test_user_invoice_number_is_unique(self):
        """Invoice number should be unique."""
        from src.models import UserInvoice

        invoice_number_column = UserInvoice.__table__.columns["invoice_number"]
        assert invoice_number_column.unique is True

    def test_user_invoice_default_status_is_invoiced(self):
        """New invoice should have invoiced status."""
        from src.models import UserInvoice
        from src.models.enums import InvoiceStatus

        invoice = UserInvoice(
            user_id=1,
            tarif_plan_id=1,
            invoice_number="INV-001",
            amount=Decimal("29.99"),
            currency="EUR",
        )

        assert invoice.status == InvoiceStatus.INVOICED

    def test_user_invoice_is_payable_property(self):
        """UserInvoice.is_payable should check status and expiry."""
        from src.models import UserInvoice
        from src.models.enums import InvoiceStatus

        invoice = UserInvoice(
            user_id=1,
            tarif_plan_id=1,
            invoice_number="INV-001",
            amount=Decimal("29.99"),
            currency="EUR",
            status=InvoiceStatus.INVOICED,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        assert invoice.is_payable is True

        # Expired
        invoice.expires_at = datetime.utcnow() - timedelta(days=1)
        assert invoice.is_payable is False

        # Already paid
        invoice.expires_at = datetime.utcnow() + timedelta(days=7)
        invoice.status = InvoiceStatus.PAID
        assert invoice.is_payable is False

    def test_user_invoice_mark_paid_method(self):
        """UserInvoice.mark_paid should update status and payment info."""
        from src.models import UserInvoice
        from src.models.enums import InvoiceStatus, PaymentMethod

        invoice = UserInvoice(
            user_id=1,
            tarif_plan_id=1,
            invoice_number="INV-001",
            amount=Decimal("29.99"),
            currency="EUR",
        )

        invoice.mark_paid(
            payment_ref="PAY-123",
            payment_method=PaymentMethod.STRIPE,
        )

        assert invoice.status == InvoiceStatus.PAID
        assert invoice.payment_ref == "PAY-123"
        assert invoice.payment_method == PaymentMethod.STRIPE
        assert invoice.paid_at is not None

    def test_user_invoice_generate_number_class_method(self):
        """UserInvoice.generate_number should create unique numbers."""
        from src.models import UserInvoice

        number1 = UserInvoice.generate_invoice_number()
        number2 = UserInvoice.generate_invoice_number()

        assert number1.startswith("INV-")
        assert number2.startswith("INV-")
        assert number1 != number2
```

**File:** `python/api/src/models/user_invoice.py`

```python
"""UserInvoice domain model."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import InvoiceStatus, PaymentMethod


class UserInvoice(BaseModel):
    """
    User invoice model.

    Tracks payment records for subscriptions.
    """

    __tablename__ = "user_invoice"

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tarif_plan_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tarif_plan.id"),
        nullable=False,
    )
    subscription_id = db.Column(
        db.BigInteger,
        db.ForeignKey("subscription.id"),
        nullable=True,
    )
    invoice_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="EUR")
    status = db.Column(
        db.Enum(InvoiceStatus),
        nullable=False,
        default=InvoiceStatus.INVOICED,
        index=True,
    )
    payment_method = db.Column(db.Enum(PaymentMethod))
    payment_ref = db.Column(db.String(255))
    invoiced_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    paid_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    @property
    def is_payable(self) -> bool:
        """Check if invoice can still be paid."""
        if self.status != InvoiceStatus.INVOICED:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def mark_paid(
        self,
        payment_ref: str,
        payment_method: PaymentMethod,
    ) -> None:
        """
        Mark invoice as paid.

        Args:
            payment_ref: External payment reference ID.
            payment_method: Payment provider used.
        """
        self.status = InvoiceStatus.PAID
        self.payment_ref = payment_ref
        self.payment_method = payment_method
        self.paid_at = datetime.utcnow()

    def mark_expired(self) -> None:
        """Mark invoice as expired."""
        self.status = InvoiceStatus.EXPIRED

    def mark_cancelled(self) -> None:
        """Mark invoice as cancelled."""
        self.status = InvoiceStatus.CANCELLED

    @staticmethod
    def generate_invoice_number() -> str:
        """Generate unique invoice number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:6].upper()
        return f"INV-{timestamp}-{unique}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tarif_plan_id": self.tarif_plan_id,
            "subscription_id": self.subscription_id,
            "invoice_number": self.invoice_number,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status.value,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "payment_ref": self.payment_ref,
            "is_payable": self.is_payable,
            "invoiced_at": self.invoiced_at.isoformat() if self.invoiced_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def __repr__(self) -> str:
        return f"<UserInvoice(number='{self.invoice_number}', status={self.status.value})>"
```

---

### 1.7 UserCase Model

**File:** `python/api/src/models/user_case.py`

```python
"""UserCase domain model."""
from datetime import date
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import UserCaseStatus


class UserCase(BaseModel):
    """
    User case/project model.

    Stores case descriptions for subscriptions.
    """

    __tablename__ = "user_case"

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = db.Column(db.Text)
    date_started = db.Column(db.Date)
    status = db.Column(
        db.Enum(UserCaseStatus),
        nullable=False,
        default=UserCaseStatus.DRAFT,
        index=True,
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "date_started": self.date_started.isoformat() if self.date_started else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<UserCase(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
```

---

### 1.8 Models Package Init

**File:** `python/api/src/models/__init__.py`

```python
"""Domain models package."""
from src.models.user import User
from src.models.user_details import UserDetails
from src.models.user_case import UserCase
from src.models.tarif_plan import TarifPlan
from src.models.subscription import Subscription
from src.models.user_invoice import UserInvoice
from src.models.enums import (
    UserStatus,
    UserRole,
    SubscriptionStatus,
    InvoiceStatus,
    BillingPeriod,
    PaymentMethod,
    UserCaseStatus,
)

__all__ = [
    # Models
    "User",
    "UserDetails",
    "UserCase",
    "TarifPlan",
    "Subscription",
    "UserInvoice",
    # Enums
    "UserStatus",
    "UserRole",
    "SubscriptionStatus",
    "InvoiceStatus",
    "BillingPeriod",
    "PaymentMethod",
    "UserCaseStatus",
]
```

---

### 1.9 Base Repository Implementation

**File:** `python/api/tests/unit/repositories/test_base_repository.py`

```python
"""Tests for base repository implementation."""
import pytest
from unittest.mock import Mock, MagicMock


class TestBaseRepository:
    """Test cases for BaseRepository."""

    def test_find_by_id_returns_entity(self):
        """find_by_id should return entity when found."""
        from src.repositories.base import BaseRepository

        mock_session = Mock()
        mock_model = Mock()
        mock_entity = Mock(id=1)
        mock_session.get.return_value = mock_entity

        repo = BaseRepository(session=mock_session, model=mock_model)
        result = repo.find_by_id(1)

        assert result == mock_entity
        mock_session.get.assert_called_once_with(mock_model, 1)

    def test_find_by_id_returns_none_when_not_found(self):
        """find_by_id should return None when entity not found."""
        from src.repositories.base import BaseRepository

        mock_session = Mock()
        mock_model = Mock()
        mock_session.get.return_value = None

        repo = BaseRepository(session=mock_session, model=mock_model)
        result = repo.find_by_id(999)

        assert result is None

    def test_save_creates_new_entity(self):
        """save should add new entity without id."""
        from src.repositories.base import BaseRepository

        mock_session = Mock()
        mock_model = Mock()
        mock_entity = Mock(id=None)

        repo = BaseRepository(session=mock_session, model=mock_model)
        repo.save(mock_entity)

        mock_session.add.assert_called_once_with(mock_entity)
        mock_session.commit.assert_called_once()

    def test_delete_removes_entity(self):
        """delete should remove existing entity."""
        from src.repositories.base import BaseRepository

        mock_session = Mock()
        mock_model = Mock()
        mock_entity = Mock(id=1)
        mock_session.get.return_value = mock_entity

        repo = BaseRepository(session=mock_session, model=mock_model)
        result = repo.delete(1)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_entity)
        mock_session.commit.assert_called_once()
```

**File:** `python/api/src/repositories/base.py`

```python
"""Base repository implementation."""
from typing import Generic, TypeVar, Optional, List, Type
from src.interfaces import IRepository

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.

    Implements IRepository interface for any SQLAlchemy model.
    """

    def __init__(self, session, model: Type[T]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session.
            model: SQLAlchemy model class.
        """
        self._session = session
        self._model = model

    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID."""
        return self._session.get(self._model, id)

    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities with pagination."""
        return (
            self._session.query(self._model)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count(self) -> int:
        """Count total entities."""
        return self._session.query(self._model).count()

    def save(self, entity: T) -> T:
        """Save (create or update) entity."""
        if not entity.id:
            self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return entity

    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        entity = self.find_by_id(id)
        if entity:
            self._session.delete(entity)
            self._session.commit()
            return True
        return False
```

---

### 1.10 Entity Repositories

**File:** `python/api/src/repositories/user_repository.py`

```python
"""User repository implementation."""
from typing import Optional, List
from src.repositories.base import BaseRepository
from src.interfaces import IUserRepository
from src.models import User, UserStatus


class UserRepository(BaseRepository[User], IUserRepository):
    """Repository for User entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=User)

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        return (
            self._session.query(User)
            .filter(User.email == email)
            .first()
        )

    def find_by_status(self, status: str) -> List[User]:
        """Find users by status."""
        return (
            self._session.query(User)
            .filter(User.status == status)
            .all()
        )

    def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        return (
            self._session.query(User)
            .filter(User.email == email)
            .count() > 0
        )
```

**File:** `python/api/src/repositories/__init__.py`

```python
"""Repository implementations."""
from src.repositories.base import BaseRepository
from src.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
]
```

---

## Database Migration

**Command:**

```bash
# Initialize migrations (once)
docker-compose run --rm python flask db init

# Create migration
docker-compose run --rm python flask db migrate -m "Initial models"

# Apply migration
docker-compose run --rm python flask db upgrade
```

---

## Verification Checklist

```bash
# Run model tests
docker-compose run --rm python pytest tests/unit/models/ -v

# Run repository tests
docker-compose run --rm python pytest tests/unit/repositories/ -v

# Run all with coverage
docker-compose run --rm python pytest --cov=src/models --cov=src/repositories

# Type check
docker-compose run --rm python mypy src/models/ src/repositories/
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Enums | [ ] | All status/type enums |
| User model | [ ] | With tests |
| UserDetails model | [ ] | With tests |
| UserCase model | [ ] | With tests |
| TarifPlan model | [ ] | With tests |
| Subscription model | [ ] | With lifecycle methods |
| UserInvoice model | [ ] | With payment methods |
| BaseRepository | [ ] | Generic CRUD |
| UserRepository | [ ] | User-specific queries |
| Database migration | [ ] | All tables created |

---

## Next Sprint

[Sprint 2: Auth & Users](./sprint-2-auth-users.md) - Authentication and user management services.
