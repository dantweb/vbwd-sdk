# Sprint 3: Tariff Plans & Subscriptions

**Goal:** Implement tariff plan management, multi-currency pricing, and subscription lifecycle.

**Prerequisites:** Sprint 2 complete (auth and user management)

---

## Objectives

- [ ] TarifPlanService with multi-currency pricing
- [ ] CurrencyService for exchange rate management
- [ ] SubscriptionService with lifecycle management
- [ ] TaxService for VAT/tax calculations
- [ ] Public tariff plan endpoints
- [ ] User subscription endpoints

---

## Tasks

### 3.1 CurrencyService Implementation

**TDD Steps:**

#### Step 1: Write failing tests

**File:** `python/api/tests/unit/services/test_currency_service.py`

```python
"""Tests for CurrencyService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal


class TestCurrencyServiceGetDefault:
    """Test cases for get_default_currency."""

    def test_get_default_currency_returns_default(self):
        """get_default_currency should return the default currency."""
        from src.services import CurrencyService
        from src.models import Currency

        mock_repo = Mock()
        default_currency = Currency(
            id=1, code="EUR", name="Euro", symbol="€",
            exchange_rate=Decimal("1.0"), is_default=True,
        )
        mock_repo.find_default.return_value = default_currency

        service = CurrencyService(currency_repo=mock_repo)
        result = service.get_default_currency()

        assert result.code == "EUR"
        assert result.is_default is True


class TestCurrencyServiceConvert:
    """Test cases for currency conversion."""

    def test_convert_amount_between_currencies(self):
        """convert should convert amount between currencies."""
        from src.services import CurrencyService
        from src.models import Currency

        mock_repo = Mock()
        eur = Currency(code="EUR", exchange_rate=Decimal("1.0"))
        usd = Currency(code="USD", exchange_rate=Decimal("1.08"))
        mock_repo.find_by_code.side_effect = lambda c: eur if c == "EUR" else usd

        service = CurrencyService(currency_repo=mock_repo)
        result = service.convert(Decimal("100"), "EUR", "USD")

        assert result == Decimal("108.00")

    def test_convert_same_currency_returns_same_amount(self):
        """convert should return same amount for same currency."""
        from src.services import CurrencyService
        from src.models import Currency

        mock_repo = Mock()
        eur = Currency(code="EUR", exchange_rate=Decimal("1.0"))
        mock_repo.find_by_code.return_value = eur

        service = CurrencyService(currency_repo=mock_repo)
        result = service.convert(Decimal("100"), "EUR", "EUR")

        assert result == Decimal("100.00")


class TestCurrencyServiceGetActive:
    """Test cases for get_active_currencies."""

    def test_get_active_currencies_returns_list(self):
        """get_active_currencies should return active currencies."""
        from src.services import CurrencyService
        from src.models import Currency

        mock_repo = Mock()
        currencies = [
            Currency(code="EUR", is_active=True),
            Currency(code="USD", is_active=True),
        ]
        mock_repo.find_active.return_value = currencies

        service = CurrencyService(currency_repo=mock_repo)
        result = service.get_active_currencies()

        assert len(result) == 2
```

#### Step 2: Implement to pass

**File:** `python/api/src/services/currency_service.py`

```python
"""Currency service implementation."""
from decimal import Decimal
from typing import List, Optional
from src.interfaces import ICurrencyRepository
from src.models import Currency


class CurrencyService:
    """
    Currency management service.

    Handles currency conversion and exchange rate management.
    """

    def __init__(self, currency_repo: ICurrencyRepository):
        self._currency_repo = currency_repo

    def get_default_currency(self) -> Currency:
        """Get the default (base) currency."""
        currency = self._currency_repo.find_default()
        if not currency:
            raise ValueError("No default currency configured")
        return currency

    def get_active_currencies(self) -> List[Currency]:
        """Get all active currencies."""
        return self._currency_repo.find_active()

    def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """Get currency by ISO code."""
        return self._currency_repo.find_by_code(code.upper())

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert.
            from_currency: Source currency code.
            to_currency: Target currency code.

        Returns:
            Converted amount.
        """
        if from_currency == to_currency:
            return amount.quantize(Decimal("0.01"))

        source = self._currency_repo.find_by_code(from_currency)
        target = self._currency_repo.find_by_code(to_currency)

        if not source or not target:
            raise ValueError(f"Unknown currency: {from_currency} or {to_currency}")

        return source.convert_to(amount, target)

    def update_exchange_rate(self, code: str, rate: Decimal) -> Currency:
        """
        Update exchange rate for currency.

        Args:
            code: Currency code.
            rate: New exchange rate relative to default.

        Returns:
            Updated currency.
        """
        currency = self._currency_repo.find_by_code(code)
        if not currency:
            raise ValueError(f"Currency not found: {code}")

        if currency.is_default:
            raise ValueError("Cannot change exchange rate of default currency")

        currency.exchange_rate = rate
        return self._currency_repo.save(currency)
```

---

### 3.2 TaxService Implementation

**File:** `python/api/tests/unit/services/test_tax_service.py`

```python
"""Tests for TaxService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal


class TestTaxServiceGetApplicable:
    """Test cases for getting applicable taxes."""

    def test_get_applicable_tax_for_country(self):
        """get_applicable_tax should return tax for country."""
        from src.services import TaxService
        from src.models import Tax

        mock_repo = Mock()
        vat_de = Tax(code="VAT_DE", rate=Decimal("19.0"), country_code="DE")
        mock_repo.find_by_country.return_value = [vat_de]

        service = TaxService(tax_repo=mock_repo)
        result = service.get_applicable_tax("DE")

        assert result.code == "VAT_DE"
        assert result.rate == Decimal("19.0")

    def test_get_applicable_tax_returns_none_if_not_found(self):
        """get_applicable_tax should return None if no tax configured."""
        from src.services import TaxService

        mock_repo = Mock()
        mock_repo.find_by_country.return_value = []

        service = TaxService(tax_repo=mock_repo)
        result = service.get_applicable_tax("XX")

        assert result is None


class TestTaxServiceCalculate:
    """Test cases for tax calculations."""

    def test_calculate_tax_for_amount(self):
        """calculate_tax should compute tax amount."""
        from src.services import TaxService
        from src.models import Tax

        mock_repo = Mock()
        vat = Tax(code="VAT_DE", rate=Decimal("19.0"))
        mock_repo.find_by_code.return_value = vat

        service = TaxService(tax_repo=mock_repo)
        result = service.calculate_tax(Decimal("100.00"), "VAT_DE")

        assert result == Decimal("19.00")

    def test_calculate_total_with_tax(self):
        """calculate_total_with_tax should return gross amount."""
        from src.services import TaxService
        from src.models import Tax

        mock_repo = Mock()
        vat = Tax(code="VAT_DE", rate=Decimal("19.0"))
        mock_repo.find_by_code.return_value = vat

        service = TaxService(tax_repo=mock_repo)
        result = service.calculate_total_with_tax(Decimal("100.00"), "VAT_DE")

        assert result == Decimal("119.00")
```

**File:** `python/api/src/services/tax_service.py`

```python
"""Tax service implementation."""
from decimal import Decimal
from typing import Optional, List
from src.models import Tax


class TaxService:
    """
    Tax calculation service.

    Handles VAT and regional tax calculations.
    """

    def __init__(self, tax_repo: "ITaxRepository"):
        self._tax_repo = tax_repo

    def get_applicable_tax(
        self,
        country_code: str,
        region_code: Optional[str] = None,
    ) -> Optional[Tax]:
        """
        Get applicable tax for location.

        Args:
            country_code: ISO country code.
            region_code: Optional state/region code.

        Returns:
            Applicable Tax or None.
        """
        taxes = self._tax_repo.find_by_country(country_code)

        # Filter by region if specified
        if region_code:
            regional = [t for t in taxes if t.region_code == region_code]
            if regional:
                return regional[0]

        # Return country-level tax
        country_taxes = [t for t in taxes if not t.region_code]
        return country_taxes[0] if country_taxes else None

    def calculate_tax(
        self,
        net_amount: Decimal,
        tax_code: str,
    ) -> Decimal:
        """
        Calculate tax amount.

        Args:
            net_amount: Amount before tax.
            tax_code: Tax code to apply.

        Returns:
            Tax amount.
        """
        tax = self._tax_repo.find_by_code(tax_code)
        if not tax:
            return Decimal("0.00")
        return tax.calculate(net_amount)

    def calculate_total_with_tax(
        self,
        net_amount: Decimal,
        tax_code: str,
    ) -> Decimal:
        """
        Calculate gross amount including tax.

        Args:
            net_amount: Amount before tax.
            tax_code: Tax code to apply.

        Returns:
            Gross amount (net + tax).
        """
        tax = self._tax_repo.find_by_code(tax_code)
        if not tax:
            return net_amount
        return tax.calculate_gross(net_amount)

    def get_tax_breakdown(
        self,
        net_amount: Decimal,
        country_code: str,
        region_code: Optional[str] = None,
    ) -> dict:
        """
        Get detailed tax breakdown for an amount.

        Returns:
            Dictionary with net, tax, gross, and tax details.
        """
        tax = self.get_applicable_tax(country_code, region_code)

        if not tax:
            return {
                "net_amount": net_amount,
                "tax_amount": Decimal("0.00"),
                "gross_amount": net_amount,
                "tax_code": None,
                "tax_rate": Decimal("0.00"),
            }

        tax_amount = tax.calculate(net_amount)

        return {
            "net_amount": net_amount,
            "tax_amount": tax_amount,
            "gross_amount": net_amount + tax_amount,
            "tax_code": tax.code,
            "tax_rate": tax.rate,
            "tax_name": tax.name,
        }
```

---

### 3.3 TarifPlanService Implementation

**File:** `python/api/tests/unit/services/test_tarif_plan_service.py`

```python
"""Tests for TarifPlanService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal


class TestTarifPlanServiceGetActive:
    """Test cases for getting active plans."""

    def test_get_active_plans_returns_active_only(self):
        """get_active_plans should return only active plans."""
        from src.services import TarifPlanService
        from src.models import TarifPlan, BillingPeriod

        mock_repo = Mock()
        plans = [
            TarifPlan(id=1, name="Basic", slug="basic", is_active=True,
                     price=Decimal("9.99"), billing_period=BillingPeriod.MONTHLY),
            TarifPlan(id=2, name="Pro", slug="pro", is_active=True,
                     price=Decimal("29.99"), billing_period=BillingPeriod.MONTHLY),
        ]
        mock_repo.find_active.return_value = plans

        service = TarifPlanService(tarif_plan_repo=mock_repo)
        result = service.get_active_plans()

        assert len(result) == 2
        mock_repo.find_active.assert_called_once()


class TestTarifPlanServiceGetPriceInCurrency:
    """Test cases for multi-currency pricing."""

    def test_get_price_in_currency_uses_fixed_price(self):
        """get_price_in_currency should use fixed price if set."""
        from src.services import TarifPlanService
        from src.models import TarifPlan, TarifPlanPrice, Currency

        mock_plan_repo = Mock()
        mock_price_repo = Mock()
        mock_currency_service = Mock()

        plan = TarifPlan(id=1, price=Decimal("29.99"))
        fixed_price = TarifPlanPrice(
            tarif_plan_id=1,
            currency_id=2,
            price=Decimal("32.99"),
            is_auto_calculated=False,
        )
        mock_price_repo.find_by_plan_and_currency.return_value = fixed_price

        service = TarifPlanService(
            tarif_plan_repo=mock_plan_repo,
            price_repo=mock_price_repo,
            currency_service=mock_currency_service,
        )
        result = service.get_price_in_currency(plan, currency_id=2)

        assert result == Decimal("32.99")

    def test_get_price_in_currency_calculates_if_no_fixed(self):
        """get_price_in_currency should calculate from default if no fixed price."""
        from src.services import TarifPlanService
        from src.models import TarifPlan, Currency

        mock_plan_repo = Mock()
        mock_price_repo = Mock()
        mock_currency_service = Mock()

        plan = TarifPlan(id=1, price=Decimal("29.99"))
        mock_price_repo.find_by_plan_and_currency.return_value = None
        mock_currency_service.convert.return_value = Decimal("32.39")

        service = TarifPlanService(
            tarif_plan_repo=mock_plan_repo,
            price_repo=mock_price_repo,
            currency_service=mock_currency_service,
        )
        result = service.get_price_in_currency(plan, currency_id=2)

        assert result == Decimal("32.39")
```

**File:** `python/api/src/services/tarif_plan_service.py`

```python
"""Tariff plan service implementation."""
from decimal import Decimal
from typing import List, Optional
from src.models import TarifPlan, TarifPlanPrice


class TarifPlanService:
    """
    Tariff plan management service.

    Handles plan retrieval and multi-currency pricing.
    """

    def __init__(
        self,
        tarif_plan_repo: "ITarifPlanRepository",
        price_repo: Optional["ITarifPlanPriceRepository"] = None,
        currency_service: Optional["CurrencyService"] = None,
    ):
        self._plan_repo = tarif_plan_repo
        self._price_repo = price_repo
        self._currency_service = currency_service

    def get_active_plans(self) -> List[TarifPlan]:
        """Get all active tariff plans."""
        return self._plan_repo.find_active()

    def get_plan_by_slug(self, slug: str) -> Optional[TarifPlan]:
        """Get tariff plan by URL slug."""
        return self._plan_repo.find_by_slug(slug)

    def get_plan_by_id(self, plan_id: int) -> Optional[TarifPlan]:
        """Get tariff plan by ID."""
        return self._plan_repo.find_by_id(plan_id)

    def get_price_in_currency(
        self,
        plan: TarifPlan,
        currency_id: int,
    ) -> Decimal:
        """
        Get plan price in specified currency.

        Uses fixed price if set, otherwise calculates from default.

        Args:
            plan: Tariff plan.
            currency_id: Target currency ID.

        Returns:
            Price in target currency.
        """
        if self._price_repo:
            # Check for fixed price
            fixed_price = self._price_repo.find_by_plan_and_currency(
                plan.id, currency_id
            )
            if fixed_price and not fixed_price.is_auto_calculated:
                return fixed_price.price

        # Calculate from default currency
        if self._currency_service:
            default = self._currency_service.get_default_currency()
            target = self._currency_service.get_currency_by_id(currency_id)
            if target:
                return self._currency_service.convert(
                    plan.price, default.code, target.code
                )

        return plan.price

    def get_plan_with_pricing(
        self,
        plan: TarifPlan,
        currency_code: str = "EUR",
        country_code: Optional[str] = None,
        tax_service: Optional["TaxService"] = None,
    ) -> dict:
        """
        Get plan details with currency-specific pricing and tax.

        Args:
            plan: Tariff plan.
            currency_code: Target currency code.
            country_code: Optional country for tax calculation.
            tax_service: Optional tax service for VAT.

        Returns:
            Plan dict with pricing details.
        """
        currency = self._currency_service.get_currency_by_code(currency_code)
        price = self.get_price_in_currency(plan, currency.id) if currency else plan.price

        result = {
            **plan.to_dict(),
            "display_price": price,
            "display_currency": currency_code,
        }

        # Add tax breakdown if country specified
        if tax_service and country_code:
            tax_breakdown = tax_service.get_tax_breakdown(price, country_code)
            result.update({
                "net_price": tax_breakdown["net_amount"],
                "tax_amount": tax_breakdown["tax_amount"],
                "gross_price": tax_breakdown["gross_amount"],
                "tax_rate": tax_breakdown["tax_rate"],
                "tax_name": tax_breakdown.get("tax_name"),
            })

        return result
```

---

### 3.4 SubscriptionService Implementation

**File:** `python/api/tests/unit/services/test_subscription_service.py`

```python
"""Tests for SubscriptionService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, timedelta


class TestSubscriptionServiceCreate:
    """Test cases for creating subscriptions."""

    def test_create_subscription_creates_inactive(self):
        """create_subscription should create inactive subscription."""
        from src.services import SubscriptionService
        from src.models import Subscription, TarifPlan, SubscriptionStatus, BillingPeriod

        mock_sub_repo = Mock()
        mock_plan_repo = Mock()

        plan = TarifPlan(
            id=1, name="Pro", billing_period=BillingPeriod.MONTHLY,
            price=Decimal("29.99"),
        )
        mock_plan_repo.find_by_id.return_value = plan
        mock_sub_repo.save.return_value = Subscription(
            id=1, user_id=1, tarif_plan_id=1, status=SubscriptionStatus.INACTIVE,
        )

        service = SubscriptionService(
            subscription_repo=mock_sub_repo,
            tarif_plan_repo=mock_plan_repo,
        )
        result = service.create_subscription(user_id=1, tarif_plan_id=1)

        assert result.status == SubscriptionStatus.INACTIVE
        mock_sub_repo.save.assert_called_once()


class TestSubscriptionServiceActivate:
    """Test cases for activating subscriptions."""

    def test_activate_subscription_sets_dates(self):
        """activate_subscription should set status and dates."""
        from src.services import SubscriptionService
        from src.models import Subscription, TarifPlan, SubscriptionStatus, BillingPeriod

        mock_sub_repo = Mock()
        mock_plan_repo = Mock()

        plan = TarifPlan(id=1, billing_period=BillingPeriod.MONTHLY)
        subscription = Subscription(
            id=1, user_id=1, tarif_plan_id=1, status=SubscriptionStatus.INACTIVE,
        )
        subscription.tarif_plan = plan

        mock_sub_repo.find_by_id.return_value = subscription
        mock_sub_repo.save.return_value = subscription

        service = SubscriptionService(
            subscription_repo=mock_sub_repo,
            tarif_plan_repo=mock_plan_repo,
        )
        result = service.activate_subscription(1)

        assert result.status == SubscriptionStatus.ACTIVE
        assert result.started_at is not None
        assert result.expires_at is not None


class TestSubscriptionServiceGetActive:
    """Test cases for getting active subscriptions."""

    def test_get_active_subscription_returns_valid(self):
        """get_active_subscription should return valid subscription."""
        from src.services import SubscriptionService
        from src.models import Subscription, SubscriptionStatus

        mock_sub_repo = Mock()
        subscription = Subscription(
            id=1, user_id=1, tarif_plan_id=1,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        mock_sub_repo.find_active_by_user_id.return_value = subscription

        service = SubscriptionService(subscription_repo=mock_sub_repo)
        result = service.get_active_subscription(user_id=1)

        assert result is not None
        assert result.is_valid is True
```

**File:** `python/api/src/services/subscription_service.py`

```python
"""Subscription service implementation."""
from datetime import datetime, timedelta
from typing import Optional, List
from src.interfaces import ISubscriptionService
from src.models import Subscription, TarifPlan, SubscriptionStatus, BillingPeriod


class SubscriptionService(ISubscriptionService):
    """
    Subscription lifecycle management service.
    """

    # Duration in days for each billing period
    PERIOD_DAYS = {
        BillingPeriod.MONTHLY: 30,
        BillingPeriod.QUARTERLY: 90,
        BillingPeriod.YEARLY: 365,
        BillingPeriod.ONE_TIME: 36500,  # ~100 years for lifetime
    }

    def __init__(
        self,
        subscription_repo: "ISubscriptionRepository",
        tarif_plan_repo: Optional["ITarifPlanRepository"] = None,
    ):
        self._subscription_repo = subscription_repo
        self._tarif_plan_repo = tarif_plan_repo

    def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self._subscription_repo.find_active_by_user_id(user_id)

    def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """Get all user subscriptions."""
        return self._subscription_repo.find_by_user_id(user_id)

    def create_subscription(
        self,
        user_id: int,
        tarif_plan_id: int,
    ) -> Subscription:
        """
        Create new subscription (inactive until payment).

        Args:
            user_id: User ID.
            tarif_plan_id: Tariff plan ID.

        Returns:
            Created subscription with inactive status.
        """
        # Verify plan exists
        if self._tarif_plan_repo:
            plan = self._tarif_plan_repo.find_by_id(tarif_plan_id)
            if not plan:
                raise ValueError(f"Tariff plan {tarif_plan_id} not found")
            if not plan.is_active:
                raise ValueError(f"Tariff plan {tarif_plan_id} is not active")

        subscription = Subscription(
            user_id=user_id,
            tarif_plan_id=tarif_plan_id,
            status=SubscriptionStatus.INACTIVE,
        )

        return self._subscription_repo.save(subscription)

    def activate_subscription(self, subscription_id: int) -> Subscription:
        """
        Activate subscription after payment.

        Sets status to active and calculates expiration date
        based on tariff plan billing period.
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Get plan for duration
        plan = subscription.tarif_plan
        duration_days = self.PERIOD_DAYS.get(plan.billing_period, 30)

        # Activate
        subscription.activate(duration_days)

        return self._subscription_repo.save(subscription)

    def cancel_subscription(self, subscription_id: int) -> Subscription:
        """Cancel subscription."""
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        subscription.cancel()
        return self._subscription_repo.save(subscription)

    def expire_subscription(self, subscription_id: int) -> Subscription:
        """Mark subscription as expired."""
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        subscription.expire()
        return self._subscription_repo.save(subscription)

    def extend_subscription(
        self,
        subscription_id: int,
        days: int,
    ) -> Subscription:
        """
        Extend subscription by specified days.

        Used for renewals or promotional extensions.
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        if subscription.expires_at:
            subscription.expires_at += timedelta(days=days)
        else:
            subscription.expires_at = datetime.utcnow() + timedelta(days=days)

        return self._subscription_repo.save(subscription)

    def check_and_expire_subscriptions(self) -> int:
        """
        Check for expired subscriptions and mark them.

        Returns count of newly expired subscriptions.
        Should be run periodically via cron/scheduler.
        """
        expiring = self._subscription_repo.find_expiring_before(datetime.utcnow())
        count = 0

        for subscription in expiring:
            if subscription.status == SubscriptionStatus.ACTIVE:
                subscription.expire()
                self._subscription_repo.save(subscription)
                count += 1

        return count
```

---

### 3.5 Tariff Plan Routes

**File:** `python/api/src/routes/tarif_plans.py`

```python
"""Tariff plan routes."""
from flask import Blueprint, request, jsonify
from dependency_injector.wiring import inject, Provide
from src.container import Container

tarif_plans_bp = Blueprint("tarif_plans", __name__, url_prefix="/tarif-plans")


@tarif_plans_bp.route("", methods=["GET"])
@inject
def list_plans(
    tarif_plan_service=Provide[Container.tarif_plan_service],
    currency_service=Provide[Container.currency_service],
    tax_service=Provide[Container.tax_service],
):
    """
    List active tariff plans.

    GET /api/v1/tarif-plans?currency=USD&country=DE

    Query params:
        currency: Currency code for pricing (default: EUR)
        country: Country code for tax calculation (optional)
    """
    currency_code = request.args.get("currency", "EUR").upper()
    country_code = request.args.get("country", "").upper() or None

    plans = tarif_plan_service.get_active_plans()

    result = []
    for plan in plans:
        plan_data = tarif_plan_service.get_plan_with_pricing(
            plan,
            currency_code=currency_code,
            country_code=country_code,
            tax_service=tax_service,
        )
        result.append(plan_data)

    return jsonify({
        "plans": result,
        "currency": currency_code,
        "country": country_code,
    }), 200


@tarif_plans_bp.route("/<slug>", methods=["GET"])
@inject
def get_plan(
    slug: str,
    tarif_plan_service=Provide[Container.tarif_plan_service],
    currency_service=Provide[Container.currency_service],
    tax_service=Provide[Container.tax_service],
):
    """
    Get single tariff plan by slug.

    GET /api/v1/tarif-plans/pro?currency=USD&country=DE
    """
    currency_code = request.args.get("currency", "EUR").upper()
    country_code = request.args.get("country", "").upper() or None

    plan = tarif_plan_service.get_plan_by_slug(slug)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    plan_data = tarif_plan_service.get_plan_with_pricing(
        plan,
        currency_code=currency_code,
        country_code=country_code,
        tax_service=tax_service,
    )

    return jsonify(plan_data), 200
```

---

### 3.6 User Subscription Routes

**File:** `python/api/src/routes/subscriptions.py`

```python
"""User subscription routes."""
from flask import Blueprint, jsonify, g
from dependency_injector.wiring import inject, Provide
from src.container import Container
from src.middleware.auth import require_auth

subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/user/subscriptions")


@subscriptions_bp.route("", methods=["GET"])
@require_auth
@inject
def list_subscriptions(
    subscription_service=Provide[Container.subscription_service],
):
    """
    List user's subscriptions.

    GET /api/v1/user/subscriptions
    Authorization: Bearer <token>
    """
    subscriptions = subscription_service.get_user_subscriptions(g.user_id)

    return jsonify({
        "subscriptions": [s.to_dict() for s in subscriptions],
    }), 200


@subscriptions_bp.route("/active", methods=["GET"])
@require_auth
@inject
def get_active_subscription(
    subscription_service=Provide[Container.subscription_service],
):
    """
    Get user's active subscription.

    GET /api/v1/user/subscriptions/active
    Authorization: Bearer <token>
    """
    subscription = subscription_service.get_active_subscription(g.user_id)

    if not subscription:
        return jsonify({"subscription": None}), 200

    return jsonify({
        "subscription": subscription.to_dict(),
    }), 200


@subscriptions_bp.route("/<int:subscription_id>/cancel", methods=["POST"])
@require_auth
@inject
def cancel_subscription(
    subscription_id: int,
    subscription_service=Provide[Container.subscription_service],
):
    """
    Cancel user's subscription.

    POST /api/v1/user/subscriptions/123/cancel
    Authorization: Bearer <token>
    """
    # Verify ownership
    subscription = subscription_service._subscription_repo.find_by_id(subscription_id)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    subscription = subscription_service.cancel_subscription(subscription_id)

    return jsonify({
        "subscription": subscription.to_dict(),
        "message": "Subscription cancelled. Access continues until expiration.",
    }), 200
```

---

## Verification Checklist

```bash
# Run all Sprint 3 tests
docker-compose run --rm python pytest tests/unit/services/test_*_service.py -v

# Test tariff plans endpoint
curl http://localhost:5000/api/v1/tarif-plans?currency=USD&country=DE

# Test with authentication
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' | jq -r '.token')

curl http://localhost:5000/api/v1/user/subscriptions \
  -H "Authorization: Bearer $TOKEN"
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| CurrencyService | [ ] | Exchange rate conversion |
| TaxService | [ ] | VAT/tax calculations |
| TarifPlanService | [ ] | Multi-currency pricing |
| SubscriptionService | [ ] | Lifecycle management |
| Tariff plan routes | [ ] | Public endpoints |
| Subscription routes | [ ] | User endpoints |

---

## Next Sprint

[Sprint 4: Payments](./sprint-4-payments.md) - Invoice and payment integration.
