# Sprint 03: Backend Token Bundles Model & API

**Date:** 2026-01-12
**Priority:** High
**Type:** Backend Implementation
**Section:** Token Bundles Feature

## Goal

Create the backend infrastructure for Token Bundles - upsell products that allow users to purchase additional tokens alongside their subscriptions.

## Token Bundles Concept

Token bundles are purchasable token packages:
- **Example 1:** 1000 TKN for $5
- **Example 2:** 10000 TKN for $50

Admins create bundles via the admin dashboard. Users can purchase bundles to add tokens to their balance.

## Clarified Requirements

| Aspect | Decision |
|--------|----------|
| **Currency** | Uses system default currency only (no currency_id field needed) |
| **Purchase type** | Multiple purchases allowed - users can buy same bundle repeatedly |
| **Currency model** | Already exists: `vbwd-backend/src/models/currency.py` |

## Core Requirements

### Methodology
- **TDD-First**: Write unit tests BEFORE implementation
- **SOLID Principles**: Repository pattern, service layer
- **Clean Code**: Type hints, docstrings
- **No Over-engineering**: Only build what's required

### Test Execution

```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
make test-unit
make test-integration
```

### Definition of Done
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Model created with proper fields
- [ ] Migration created and tested
- [ ] API endpoints functional
- [ ] Backend rebuilt with `make up-build` in vbwd-backend/
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

### Build & Deploy

After implementation, rebuild the backend:

```bash
# From vbwd-backend/
cd ~/dantweb/vbwd-sdk/vbwd-backend
make up-build

# Or from project root
cd ~/dantweb/vbwd-sdk
cd vbwd-backend && docker-compose up -d --build
```

Backend API available at: http://localhost:5000

---

## Tasks

### Task 3.1: Backend - TokenBundle Model

**Goal:** Create SQLAlchemy model for token bundles

**Model Fields:**
```python
class TokenBundle(BaseModel):
    __tablename__ = 'token_bundles'

    # Primary fields
    name = Column(String(255), nullable=False)           # "1000 Tokens"
    description = Column(Text, nullable=True)            # Optional description
    token_amount = Column(Integer, nullable=False)       # 1000
    price = Column(Numeric(10, 2), nullable=False)       # 5.00 (in default currency)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)              # For ordering in UI

    # Note: Uses system default currency, no currency_id field needed
    # Inherited from BaseModel: id, created_at, updated_at, version
```

**Files to Create:**
- `src/models/token_bundle.py`

**Files to Modify:**
- `src/models/__init__.py` (export model)

**Acceptance Criteria:**
- [ ] Model has all required fields
- [ ] No currency_id (uses default currency)
- [ ] to_dict() method implemented
- [ ] Model exported from __init__.py

---

### Task 3.2: Backend - Database Migration

**Goal:** Create Alembic migration for token_bundles table

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose exec api flask db migrate -m "Add token_bundles table"
docker-compose exec api flask db upgrade
```

**Table Schema:**
```sql
CREATE TABLE token_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    token_amount INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,  -- in default currency
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_token_bundles_active ON token_bundles(is_active);
```

**Acceptance Criteria:**
- [ ] Migration file created
- [ ] Migration applies without errors
- [ ] Table exists with correct schema
- [ ] Indexes created

---

### Task 3.3: Backend - TokenBundle Repository

**Goal:** Create repository for TokenBundle data access

**Repository Methods:**
```python
class TokenBundleRepository:
    def get_all(self, include_inactive: bool = False) -> List[TokenBundle]
    def get_by_id(self, bundle_id: UUID) -> Optional[TokenBundle]
    def get_active(self) -> List[TokenBundle]
    def create(self, data: dict) -> TokenBundle
    def update(self, bundle_id: UUID, data: dict) -> Optional[TokenBundle]
    def delete(self, bundle_id: UUID) -> bool
    def count(self, include_inactive: bool = False) -> int
```

**Files to Create:**
- `src/repositories/token_bundle_repository.py`

**Files to Modify:**
- `src/repositories/__init__.py` (export repository)

**Acceptance Criteria:**
- [ ] All CRUD methods implemented
- [ ] Pagination support in get_all
- [ ] Active/inactive filtering

---

### Task 3.4: Backend - TokenBundle Service

**Goal:** Create service layer for TokenBundle business logic

**Service Methods:**
```python
class TokenBundleService:
    def list_bundles(self, page: int, per_page: int, include_inactive: bool = False) -> dict
    def get_bundle(self, bundle_id: UUID) -> dict
    def create_bundle(self, data: dict) -> dict
    def update_bundle(self, bundle_id: UUID, data: dict) -> dict
    def delete_bundle(self, bundle_id: UUID) -> bool
    def toggle_active(self, bundle_id: UUID) -> dict
```

**Files to Create:**
- `src/services/token_bundle_service.py`

**Files to Modify:**
- `src/services/__init__.py` (export service)
- `src/containers.py` (register with DI container)

**Acceptance Criteria:**
- [ ] All business logic methods implemented
- [ ] Proper error handling
- [ ] Validation of inputs
- [ ] Currency validation

---

### Task 3.5: Backend - Admin API Endpoints

**Goal:** Create admin API routes for token bundles

**Endpoints:**
```
GET    /api/v1/admin/token-bundles           # List all bundles (paginated)
GET    /api/v1/admin/token-bundles/:id       # Get single bundle
POST   /api/v1/admin/token-bundles           # Create bundle
PUT    /api/v1/admin/token-bundles/:id       # Update bundle
DELETE /api/v1/admin/token-bundles/:id       # Delete bundle
```

**Request/Response Examples:**

**GET /api/v1/admin/token-bundles**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "1000 Tokens",
      "description": "Starter token pack",
      "token_amount": 1000,
      "price": "5.00",
      "currency": {
        "id": "uuid",
        "code": "USD",
        "symbol": "$"
      },
      "is_active": true,
      "sort_order": 1,
      "created_at": "2026-01-12T10:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

**POST /api/v1/admin/token-bundles**
```json
{
  "name": "1000 Tokens",
  "description": "Starter token pack",
  "token_amount": 1000,
  "price": 5.00,
  "currency_id": "uuid",
  "is_active": true,
  "sort_order": 1
}
```

**Files to Create:**
- `src/routes/admin/token_bundles.py`

**Files to Modify:**
- `src/routes/admin/__init__.py` (register blueprint)

**Acceptance Criteria:**
- [ ] All endpoints functional
- [ ] Proper authentication (admin only)
- [ ] Input validation
- [ ] Error responses

---

### Task 3.6: Backend - Unit Tests

**Goal:** Write unit tests for TokenBundle feature

**Test Coverage:**
- [ ] Model to_dict() method
- [ ] Repository CRUD operations
- [ ] Service layer methods
- [ ] API endpoint responses

**Test Files:**
- `tests/unit/models/test_token_bundle.py`
- `tests/unit/repositories/test_token_bundle_repository.py`
- `tests/unit/services/test_token_bundle_service.py`
- `tests/unit/routes/admin/test_token_bundles.py`

**Commands:**
```bash
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose run --rm test pytest tests/unit/ -v -k token_bundle
```

**Acceptance Criteria:**
- [ ] Tests written for all components
- [ ] All tests passing
- [ ] Good coverage of edge cases

---

## API Reference

### List Token Bundles
```
GET /api/v1/admin/token-bundles?page=1&per_page=20&include_inactive=false
Authorization: Bearer <admin_token>

Response 200:
{
  "items": [...],
  "total": 10,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

### Get Token Bundle
```
GET /api/v1/admin/token-bundles/:id
Authorization: Bearer <admin_token>

Response 200:
{
  "id": "uuid",
  "name": "1000 Tokens",
  ...
}
```

### Create Token Bundle
```
POST /api/v1/admin/token-bundles
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "1000 Tokens",
  "token_amount": 1000,
  "price": 5.00,
  "currency_id": "uuid"
}

Response 201:
{
  "id": "uuid",
  "name": "1000 Tokens",
  ...
}
```

### Update Token Bundle
```
PUT /api/v1/admin/token-bundles/:id
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "price": 6.00
}

Response 200:
{
  "id": "uuid",
  "name": "Updated Name",
  ...
}
```

### Delete Token Bundle
```
DELETE /api/v1/admin/token-bundles/:id
Authorization: Bearer <admin_token>

Response 204: No Content
```

---

## Files Summary

### Create
- `src/models/token_bundle.py`
- `src/repositories/token_bundle_repository.py`
- `src/services/token_bundle_service.py`
- `src/routes/admin/token_bundles.py`
- `tests/unit/models/test_token_bundle.py`
- `tests/unit/repositories/test_token_bundle_repository.py`
- `tests/unit/services/test_token_bundle_service.py`
- `tests/unit/routes/admin/test_token_bundles.py`
- Migration file (auto-generated)

### Modify
- `src/models/__init__.py`
- `src/repositories/__init__.py`
- `src/services/__init__.py`
- `src/containers.py`
- `src/routes/admin/__init__.py`

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 3.1 TokenBundle Model | ⏳ Pending | |
| 3.2 Database Migration | ⏳ Pending | |
| 3.3 TokenBundle Repository | ⏳ Pending | |
| 3.4 TokenBundle Service | ⏳ Pending | |
| 3.5 Admin API Endpoints | ⏳ Pending | |
| 3.6 Unit Tests | ⏳ Pending | |
