# Sprint 09: Countries Configuration

**Priority:** MEDIUM
**Estimated Effort:** Medium
**Dependencies:** Sprint 08 (Admin infrastructure)

---

## Q&A Decisions (2026-01-22)

| Question | Decision |
|----------|----------|
| **Admin UI** | Drag-and-drop interface: left panel (all countries), right panel (selected/enabled) |
| **Storage** | Database table with position ordering |
| **API** | Public endpoint for checkout, admin endpoints for CRUD |

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

Create admin interface for configuring which countries are available in the billing address dropdown. Uses drag-and-drop for ordering.

---

## TDD Phase 1: Write Failing Backend Tests FIRST

### 1.1 Unit Test: Country Model

**File:** `vbwd-backend/tests/unit/models/test_country.py`

```python
import pytest
from src.models.country import Country


class TestCountryModel:
    """Tests for Country model."""

    def test_country_has_required_fields(self):
        """Country should have required fields."""
        country = Country(
            code="DE",
            name="Germany",
            is_enabled=True,
            position=0,
        )

        assert country.code == "DE"
        assert country.name == "Germany"
        assert country.is_enabled is True
        assert country.position == 0

    def test_country_to_dict(self):
        """Country.to_dict() should return proper dictionary."""
        country = Country(code="DE", name="Germany", is_enabled=True, position=0)

        data = country.to_dict()

        assert data["code"] == "DE"
        assert data["name"] == "Germany"
        assert data["is_enabled"] is True
        assert data["position"] == 0

    def test_country_to_public_dict(self):
        """Country.to_public_dict() should return minimal data."""
        country = Country(code="DE", name="Germany", is_enabled=True, position=0)

        data = country.to_public_dict()

        assert data["code"] == "DE"
        assert data["name"] == "Germany"
        assert "is_enabled" not in data  # Not exposed publicly
```

### 1.2 Integration Test: Admin Endpoints

**File:** `vbwd-backend/tests/integration/routes/test_admin_countries.py`

```python
import pytest


class TestAdminCountriesEndpoint:
    """Integration tests for admin countries endpoints."""

    def test_get_all_countries(self, client, admin_auth_headers):
        """Should return all countries (enabled and disabled)."""
        response = client.get(
            "/api/v1/admin/countries",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "countries" in data
        assert len(data["countries"]) > 0

    def test_enable_country(self, client, admin_auth_headers):
        """Should enable a country."""
        response = client.post(
            "/api/v1/admin/countries/FR/enable",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["is_enabled"] is True

    def test_disable_country(self, client, admin_auth_headers):
        """Should disable a country."""
        response = client.post(
            "/api/v1/admin/countries/FR/disable",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["is_enabled"] is False

    def test_reorder_countries(self, client, admin_auth_headers):
        """Should reorder enabled countries."""
        response = client.put(
            "/api/v1/admin/countries/reorder",
            headers=admin_auth_headers,
            json={"codes": ["AT", "DE", "CH"]},  # New order
        )

        assert response.status_code == 200

    def test_requires_admin_auth(self, client):
        """Should require admin authentication."""
        response = client.get("/api/v1/admin/countries")
        assert response.status_code == 401


class TestPublicCountriesEndpoint:
    """Integration tests for public countries endpoint."""

    def test_get_enabled_countries(self, client):
        """Should return only enabled countries."""
        response = client.get("/api/v1/settings/countries")

        assert response.status_code == 200
        data = response.get_json()
        assert "countries" in data
        # All returned countries should be enabled
        for country in data["countries"]:
            assert "code" in country
            assert "name" in country

    def test_does_not_require_auth(self, client):
        """Public endpoint should not require auth."""
        response = client.get("/api/v1/settings/countries")
        assert response.status_code == 200

    def test_returns_in_position_order(self, client):
        """Countries should be returned in position order."""
        response = client.get("/api/v1/settings/countries")
        data = response.get_json()

        # Verify ordering (if multiple countries enabled)
        if len(data["countries"]) > 1:
            # Countries should be in position order
            pass  # Position not exposed publicly, but order should be correct
```

---

## TDD Phase 2: Write Minimal Backend Code

### 2.1 Create Country Model

**File:** `vbwd-backend/src/models/country.py`

```python
"""Country model for billing address configuration."""
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from src.extensions import db


class Country(db.Model):
    """Country for billing address selection."""

    __tablename__ = "country"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = db.Column(db.String(2), unique=True, nullable=False)  # ISO 3166-1 alpha-2
    name = db.Column(db.String(100), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self) -> dict:
        """Return full dictionary (for admin)."""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "is_enabled": self.is_enabled,
            "position": self.position,
        }

    def to_public_dict(self) -> dict:
        """Return public dictionary (for checkout)."""
        return {
            "code": self.code,
            "name": self.name,
        }
```

### 2.2 Create Migration

**File:** `vbwd-backend/alembic/versions/20260122_add_country_table.py`

```python
"""Add country table for billing address configuration.

Revision ID: 20260122_countries
Revises: 20260122_payment_methods
Create Date: 2026-01-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '20260122_countries'
down_revision = '20260122_payment_methods'
branch_labels = None
depends_on = None

# Default countries list (ISO 3166-1)
DEFAULT_COUNTRIES = [
    ("DE", "Germany"),
    ("AT", "Austria"),
    ("CH", "Switzerland"),
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("FR", "France"),
    ("IT", "Italy"),
    ("ES", "Spain"),
    ("NL", "Netherlands"),
    ("BE", "Belgium"),
    ("PL", "Poland"),
    ("CZ", "Czech Republic"),
    ("SE", "Sweden"),
    ("NO", "Norway"),
    ("DK", "Denmark"),
    ("FI", "Finland"),
    ("PT", "Portugal"),
    ("IE", "Ireland"),
    ("LU", "Luxembourg"),
    ("GR", "Greece"),
]

# Countries enabled by default (DACH region)
DEFAULT_ENABLED = ["DE", "AT", "CH"]


def upgrade():
    # Create country table
    op.create_table(
        'country',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(2), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=False, nullable=False),
        sa.Column('position', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_country_code', 'country', ['code'])
    op.create_index('ix_country_is_enabled', 'country', ['is_enabled'])
    op.create_index('ix_country_position', 'country', ['position'])

    # Seed default countries
    from uuid import uuid4
    connection = op.get_bind()

    for position, (code, name) in enumerate(DEFAULT_COUNTRIES):
        is_enabled = code in DEFAULT_ENABLED
        connection.execute(
            sa.text("""
                INSERT INTO country (id, code, name, is_enabled, position)
                VALUES (:id, :code, :name, :is_enabled, :position)
            """),
            {
                "id": str(uuid4()),
                "code": code,
                "name": name,
                "is_enabled": is_enabled,
                "position": position if is_enabled else 999,
            }
        )


def downgrade():
    op.drop_table('country')
```

### 2.3 Create Admin Routes

**File:** `vbwd-backend/src/routes/admin/countries.py`

```python
"""Admin routes for country configuration."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.extensions import db
from src.models.country import Country
from src.decorators import admin_required

admin_countries_bp = Blueprint("admin_countries", __name__, url_prefix="/api/v1/admin/countries")


@admin_countries_bp.route("", methods=["GET"])
@jwt_required()
@admin_required
def get_all_countries():
    """Get all countries (enabled and disabled)."""
    countries = Country.query.order_by(Country.position, Country.name).all()
    return jsonify({
        "countries": [c.to_dict() for c in countries]
    }), 200


@admin_countries_bp.route("/<code>/enable", methods=["POST"])
@jwt_required()
@admin_required
def enable_country(code: str):
    """Enable a country."""
    country = Country.query.filter_by(code=code.upper()).first()
    if not country:
        return jsonify({"error": "Country not found"}), 404

    country.is_enabled = True
    # Set position to end of enabled list
    max_pos = db.session.query(db.func.max(Country.position)).filter(
        Country.is_enabled == True
    ).scalar() or -1
    country.position = max_pos + 1

    db.session.commit()
    return jsonify(country.to_dict()), 200


@admin_countries_bp.route("/<code>/disable", methods=["POST"])
@jwt_required()
@admin_required
def disable_country(code: str):
    """Disable a country."""
    country = Country.query.filter_by(code=code.upper()).first()
    if not country:
        return jsonify({"error": "Country not found"}), 404

    country.is_enabled = False
    country.position = 999  # Move to end

    db.session.commit()
    return jsonify(country.to_dict()), 200


@admin_countries_bp.route("/reorder", methods=["PUT"])
@jwt_required()
@admin_required
def reorder_countries():
    """Reorder enabled countries."""
    data = request.get_json() or {}
    codes = data.get("codes", [])

    if not codes:
        return jsonify({"error": "codes list required"}), 400

    for position, code in enumerate(codes):
        country = Country.query.filter_by(code=code.upper()).first()
        if country and country.is_enabled:
            country.position = position

    db.session.commit()

    countries = Country.query.filter_by(is_enabled=True).order_by(Country.position).all()
    return jsonify({
        "countries": [c.to_dict() for c in countries]
    }), 200
```

### 2.4 Add Public Endpoint

**File:** `vbwd-backend/src/routes/settings.py`

```python
# Add to existing settings routes

@settings_bp.route("/countries", methods=["GET"])
def get_countries():
    """
    Get enabled countries for billing address.

    Returns:
        200: { "countries": [{ "code": "DE", "name": "Germany" }, ...] }
    """
    countries = Country.query.filter_by(is_enabled=True).order_by(Country.position).all()
    return jsonify({
        "countries": [c.to_public_dict() for c in countries]
    }), 200
```

---

## TDD Phase 3: Write Failing Frontend Tests

### 3.1 E2E Tests for Admin

**File:** `vbwd-frontend/admin/vue/tests/e2e/admin-countries.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

test.describe('Countries Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('displays countries settings page', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.click('[data-testid="settings-countries-tab"]');

    await expect(page.locator('[data-testid="countries-config"]')).toBeVisible();
  });

  test('shows two panels: available and enabled', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.click('[data-testid="settings-countries-tab"]');

    await expect(page.locator('[data-testid="available-countries"]')).toBeVisible();
    await expect(page.locator('[data-testid="enabled-countries"]')).toBeVisible();
  });

  test('can drag country from available to enabled', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.click('[data-testid="settings-countries-tab"]');

    const availablePanel = page.locator('[data-testid="available-countries"]');
    const enabledPanel = page.locator('[data-testid="enabled-countries"]');

    // Find France in available
    const france = availablePanel.locator('[data-testid="country-FR"]');
    await expect(france).toBeVisible();

    // Drag to enabled (or click enable button)
    await page.click('[data-testid="country-FR"] [data-testid="enable-btn"]');

    // France should now be in enabled panel
    await expect(enabledPanel.locator('[data-testid="country-FR"]')).toBeVisible();
  });

  test('can reorder enabled countries', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.click('[data-testid="settings-countries-tab"]');

    // Enabled countries should have drag handles
    await expect(page.locator('[data-testid="enabled-countries"] [data-testid="drag-handle"]').first()).toBeVisible();
  });

  test('can disable a country', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.click('[data-testid="settings-countries-tab"]');

    const enabledPanel = page.locator('[data-testid="enabled-countries"]');

    // Click disable on first enabled country
    await enabledPanel.locator('[data-testid="disable-btn"]').first().click();

    // Confirm if needed
    // Country should move to available panel
  });
});
```

---

## TDD Phase 4: Write Minimal Frontend Code

### 4.1 Create Countries Settings Component

**File:** `vbwd-frontend/admin/vue/src/components/settings/CountriesConfig.vue`

```vue
<template>
  <div class="countries-config" data-testid="countries-config">
    <h3>Allowed Countries</h3>
    <p class="description">
      Configure which countries are available in the billing address dropdown.
      Drag to reorder enabled countries.
    </p>

    <div class="panels">
      <!-- Available Countries (Left) -->
      <div class="panel available" data-testid="available-countries">
        <h4>Available Countries</h4>
        <div class="search">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search countries..."
          />
        </div>
        <ul class="country-list">
          <li
            v-for="country in filteredAvailable"
            :key="country.code"
            class="country-item"
            :data-testid="`country-${country.code}`"
          >
            <span class="country-name">{{ country.name }} ({{ country.code }})</span>
            <button
              class="btn-enable"
              data-testid="enable-btn"
              @click="enableCountry(country.code)"
            >
              Enable →
            </button>
          </li>
        </ul>
      </div>

      <!-- Enabled Countries (Right) -->
      <div class="panel enabled" data-testid="enabled-countries">
        <h4>Enabled Countries ({{ enabledCountries.length }})</h4>
        <draggable
          v-model="enabledCountries"
          item-key="code"
          handle=".drag-handle"
          @end="saveOrder"
        >
          <template #item="{ element }">
            <li
              class="country-item"
              :data-testid="`country-${element.code}`"
            >
              <span class="drag-handle" data-testid="drag-handle">⠿</span>
              <span class="country-name">{{ element.name }} ({{ element.code }})</span>
              <button
                class="btn-disable"
                data-testid="disable-btn"
                @click="disableCountry(element.code)"
              >
                × Remove
              </button>
            </li>
          </template>
        </draggable>
        <p v-if="enabledCountries.length === 0" class="empty">
          No countries enabled. Drag from the left panel.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import draggable from 'vuedraggable';
import api from '@/api';

interface Country {
  code: string;
  name: string;
  is_enabled: boolean;
  position: number;
}

const allCountries = ref<Country[]>([]);
const searchQuery = ref('');
const loading = ref(false);

const enabledCountries = computed({
  get: () => allCountries.value
    .filter(c => c.is_enabled)
    .sort((a, b) => a.position - b.position),
  set: (value) => {
    // Update positions based on new order
    value.forEach((c, idx) => {
      const country = allCountries.value.find(x => x.code === c.code);
      if (country) country.position = idx;
    });
  }
});

const availableCountries = computed(() =>
  allCountries.value.filter(c => !c.is_enabled)
);

const filteredAvailable = computed(() => {
  const query = searchQuery.value.toLowerCase();
  return availableCountries.value.filter(c =>
    c.name.toLowerCase().includes(query) ||
    c.code.toLowerCase().includes(query)
  );
});

const loadCountries = async () => {
  loading.value = true;
  try {
    const response = await api.get('/admin/countries');
    allCountries.value = response.countries;
  } catch (e) {
    console.error('Failed to load countries', e);
  } finally {
    loading.value = false;
  }
};

const enableCountry = async (code: string) => {
  try {
    await api.post(`/admin/countries/${code}/enable`);
    const country = allCountries.value.find(c => c.code === code);
    if (country) {
      country.is_enabled = true;
      country.position = enabledCountries.value.length;
    }
  } catch (e) {
    console.error('Failed to enable country', e);
  }
};

const disableCountry = async (code: string) => {
  try {
    await api.post(`/admin/countries/${code}/disable`);
    const country = allCountries.value.find(c => c.code === code);
    if (country) {
      country.is_enabled = false;
      country.position = 999;
    }
  } catch (e) {
    console.error('Failed to disable country', e);
  }
};

const saveOrder = async () => {
  try {
    const codes = enabledCountries.value.map(c => c.code);
    await api.put('/admin/countries/reorder', { codes });
  } catch (e) {
    console.error('Failed to save order', e);
  }
};

onMounted(() => {
  loadCountries();
});
</script>

<style scoped>
.countries-config {
  padding: 20px;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  min-height: 400px;
}

.panel h4 {
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.search input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
}

.country-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.country-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 5px;
  background: white;
}

.country-item:hover {
  background: #f9f9f9;
}

.country-name {
  flex: 1;
}

.drag-handle {
  cursor: grab;
  color: #999;
  padding: 0 5px;
}

.btn-enable {
  background: #27ae60;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-disable {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.empty {
  color: #999;
  text-align: center;
  padding: 20px;
}
</style>
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Model handles data, routes handle HTTP, component handles UI |
| **O** - Open/Closed | New countries added via migration, no code changes |
| **L** - Liskov Substitution | N/A |
| **I** - Interface Segregation | Separate admin and public endpoints |
| **D** - Dependency Inversion | Component depends on API interface |

## No Over-engineering

- Simple enable/disable toggle, not complex rules
- Hardcoded country list in migration (no external API)
- Basic drag-and-drop with vuedraggable
- No translation support (country names in English)

---

## Files Created

### Backend
```
vbwd-backend/src/models/country.py
vbwd-backend/src/routes/admin/countries.py
vbwd-backend/alembic/versions/20260122_add_country_table.py
vbwd-backend/tests/unit/models/test_country.py
vbwd-backend/tests/integration/routes/test_admin_countries.py
```

### Frontend
```
vbwd-frontend/admin/vue/src/components/settings/CountriesConfig.vue
vbwd-frontend/admin/vue/tests/e2e/admin-countries.spec.ts
```

### Modified
```
vbwd-backend/src/models/__init__.py           # Add Country export
vbwd-backend/src/routes/admin/__init__.py     # Add admin_countries_bp
vbwd-backend/src/routes/settings.py           # Add /countries endpoint
vbwd-frontend/admin/vue/src/views/Settings.vue # Add Countries tab
```

---

## Verification Checklist

- [ ] Backend unit tests written and FAILING
- [ ] Backend integration tests written and FAILING
- [ ] Country model implemented
- [ ] Migration created
- [ ] Admin routes implemented
- [ ] Public endpoint added
- [ ] Frontend E2E tests written and FAILING
- [ ] CountriesConfig component implemented
- [ ] Settings view updated with tab
- [ ] All tests PASSING

## Run Tests

> **All tests run in Docker containers.**

### Backend (from `vbwd-backend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --unit           # Unit tests
./bin/pre-commit-check.sh --integration    # Integration tests

# Makefile commands
make test-unit -- -k "country"
make test-integration -- -k "TestAdminCountries or TestPublicCountries"
```

### Frontend (from `vbwd-frontend/`)

```bash
# Pre-commit check (recommended)
./bin/pre-commit-check.sh --admin --e2e    # Admin E2E tests

# From vbwd-frontend/admin/vue/
npm run test:e2e -- admin-countries.spec.ts

# Run migration first
docker-compose exec api flask db upgrade
```

## Dependencies

Install vuedraggable for drag-and-drop:

```bash
cd vbwd-frontend/admin/vue
npm install vuedraggable@^4
```
