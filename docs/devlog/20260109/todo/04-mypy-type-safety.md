# Sprint 04: Mypy Type Safety - Complete Type Coverage

**Date:** 2026-01-09
**Priority:** Medium
**Type:** Code Quality / Technical Debt
**Section:** Backend Static Analysis

## Goal

Achieve full Mypy type compliance by fixing the remaining 55 type errors across the backend codebase. This includes installing missing type stubs, fixing architectural type patterns, and adding proper null checks for Optional values.

## Current State

After initial cleanup (Sprint 03.5):
- **Flake8**: All critical checks pass (F401, F841, E712, E722, F541)
- **Mypy**: 55 errors remaining (down from 100+)
- **Unit Tests**: 477 passing

## Error Categories

### Category 1: Library Stubs (6 errors)
Missing type stubs for third-party libraries.

**Errors:**
- `src/utils/redis_client.py:2` - redis library stubs
- `src/sdk/idempotency_service.py:7` - redis library stubs
- `src/routes/admin/subscriptions.py:4` - dateutil library stubs

**Fix:** Install type stubs
```bash
pip install types-redis types-python-dateutil
# Add to requirements.txt
```

### Category 2: Architectural Patterns (40+ errors)

#### 2.1 Flask Container Attribute (5 errors)
Flask app doesn't know about custom `container` attribute from dependency-injector.

**Files:**
- `src/decorators/permissions.py:30, 73, 116, 160, 205`
- `src/app.py:121`

**Fix Options:**
1. Use `cast()` to tell Mypy about the attribute
2. Create a custom Flask subclass with type hints
3. Use `# type: ignore` comments (not recommended)

#### 2.2 SQLAlchemy Model Types (7+ errors)
`db.Model` base class not recognized by Mypy.

**Files:**
- `src/models/base.py:15`
- `src/repositories/base.py:54, 56, 58, 60, 62, 67`

**Fix Options:**
1. Use `flask-sqlalchemy-stubs` package
2. Add explicit type annotations with Protocol
3. Use TypeVar bounds properly

#### 2.3 Repository Generic T Attribute (7 errors)
Generic type T doesn't have `id` and `version` attributes.

**Files:**
- `src/repositories/base.py:54-67`

**Fix:** Define a Protocol or TypeVar with proper bounds:
```python
from typing import Protocol

class HasIdAndVersion(Protocol):
    id: Any
    version: int

T = TypeVar('T', bound=HasIdAndVersion)
```

#### 2.4 Liskov Substitution Violations (8 errors)
Handler `handle()` methods take specific event types instead of `DomainEvent`.

**Files:**
- `src/handlers/payment_handlers.py:39, 95, 140, 183`

**Fix Options:**
1. Change signature to `handle(self, event: DomainEvent)` and cast inside
2. Use Generic handlers with TypeVar
3. Use `@overload` decorators

#### 2.5 SQLAlchemy Column vs Value Types (6 errors)
`Column[UUID]` being passed where `UUID` expected.

**Files:**
- `src/services/auth_service.py:66, 68, 94, 104`
- `src/services/password_reset_service.py:78, 86, 140`

**Fix:** Access `.value` or use proper attribute access

#### 2.6 RelationshipProperty Iteration (3 errors)
Iterating over SQLAlchemy relationships.

**Files:**
- `src/models/role.py:64, 73`
- `src/repositories/role_repository.py:33`

**Fix:** Properly type relationship returns

#### 2.7 Repository Constructor Arguments (1 error)
Wrong argument order in repository constructor.

**Files:**
- `src/repositories/tax_repository.py:17`

**Fix:** Correct constructor call order

### Category 3: Optional Handling (9 errors)

#### 3.1 Handler Optional Arguments
Passing Optional values to functions expecting non-Optional.

**Files:**
- `src/handlers/payment_handlers.py:51, 68, 189, 207`
- `src/handlers/password_reset_handler.py:83, 120, 144`

**Fix:** Add null checks before calling:
```python
if event.amount is not None:
    adapter.create_payment_intent(amount=event.amount, ...)
```

#### 3.2 Route Optional Returns
Calling methods on potentially None values.

**Files:**
- `src/routes/subscriptions.py:114, 157, 200, 258, 316`

**Fix:** Add null checks:
```python
subscription = service.get(id)
if subscription is None:
    return jsonify({"error": "Not found"}), 404
return jsonify(subscription.to_dict())
```

#### 3.3 Missing Method Errors
Repository missing expected methods.

**Files:**
- `src/services/feature_guard.py:51, 82, 118, 151`

**Fix:** Add missing `get_active_subscription` method to `SubscriptionRepository`

---

## Tasks

### Task 4.1: Install Type Stubs

**Goal:** Install missing type stub packages

**Steps:**
1. Add to `requirements.txt`:
   ```
   types-redis>=4.0.0
   types-python-dateutil>=2.8.0
   ```
2. Run `pip install -r requirements.txt`
3. Rebuild Docker image

**Expected Result:** 6 errors resolved

---

### Task 4.2: Fix Flask Container Typing

**Goal:** Properly type the Flask container attribute

**Approach:** Create typed access pattern

**Files to Modify:**
- `src/decorators/permissions.py`
- `src/app.py`

**Implementation:**
```python
from typing import TYPE_CHECKING, cast
from flask import current_app

if TYPE_CHECKING:
    from src.container import Container

def get_container() -> "Container":
    return cast("Container", current_app.container)
```

**Expected Result:** 6 errors resolved

---

### Task 4.3: Fix Repository Base Types

**Goal:** Add proper type bounds for repository generic

**Files to Modify:**
- `src/repositories/base.py`
- `src/models/base.py`

**Implementation:**
```python
from typing import Protocol, TypeVar

class BaseModelProtocol(Protocol):
    id: Any
    version: int

T = TypeVar('T', bound=BaseModelProtocol)
```

**Expected Result:** 7+ errors resolved

---

### Task 4.4: Fix Handler Liskov Violations

**Goal:** Make handler signatures compatible with interface

**Files to Modify:**
- `src/handlers/payment_handlers.py`
- `src/events/domain.py`

**Approach:** Use Union type in interface or cast in handlers

**Expected Result:** 8 errors resolved

---

### Task 4.5: Fix Optional Handling in Handlers

**Goal:** Add null checks for Optional values

**Files to Modify:**
- `src/handlers/payment_handlers.py`
- `src/handlers/password_reset_handler.py`

**Implementation:** Add defensive checks:
```python
if event.provider is None:
    return EventResult.error_result("Provider is required")
```

**Expected Result:** 7 errors resolved

---

### Task 4.6: Fix Route Optional Returns

**Goal:** Handle None returns from service methods

**Files to Modify:**
- `src/routes/subscriptions.py`

**Implementation:** Add null checks before calling methods

**Expected Result:** 5 errors resolved

---

### Task 4.7: Add Missing Repository Method

**Goal:** Add `get_active_subscription` to SubscriptionRepository

**Files to Modify:**
- `src/repositories/subscription_repository.py`

**Expected Result:** 4 errors resolved

---

### Task 4.8: Fix Remaining Type Issues

**Goal:** Address any remaining type errors

**Files to Modify:** Various

**Expected Result:** All Mypy errors resolved

---

## Definition of Done

- [ ] `types-redis` and `types-python-dateutil` installed
- [ ] All 55 Mypy errors resolved
- [ ] `mypy src/ --ignore-missing-imports` passes with 0 errors
- [ ] All unit tests still passing (477 tests)
- [ ] All integration tests passing
- [ ] No new Flake8 errors introduced
- [ ] Docker image rebuilt and tested
- [ ] Sprint moved to `/done` folder
- [ ] Completion report created in `/reports`

## Test Execution

```bash
# Run Mypy
cd ~/dantweb/vbwd-sdk/vbwd-backend
docker-compose run --rm test mypy src/ --ignore-missing-imports

# Run full pre-commit check
make pre-commit

# Run unit tests only
make test-unit
```

## Estimated Effort

| Task | Complexity | Errors Fixed |
|------|------------|--------------|
| 4.1 Install Stubs | Low | 6 |
| 4.2 Flask Container | Medium | 6 |
| 4.3 Repository Types | High | 7+ |
| 4.4 Handler Liskov | High | 8 |
| 4.5 Optional Handlers | Medium | 7 |
| 4.6 Route Optional | Low | 5 |
| 4.7 Missing Method | Low | 4 |
| 4.8 Remaining | Medium | ~12 |
| **Total** | | **55** |

## Related Files

- `src/repositories/base.py` - Repository base class
- `src/handlers/payment_handlers.py` - Payment event handlers
- `src/events/domain.py` - Event handler interface
- `src/decorators/permissions.py` - Permission decorators
- `src/models/base.py` - Base SQLAlchemy model
