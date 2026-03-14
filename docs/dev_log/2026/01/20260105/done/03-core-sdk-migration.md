# Sprint: Core SDK Migration (ApiClient + Auth + EventBus)

**Date:** 2026-01-05
**Priority:** High
**Type:** Refactoring - Infrastructure

---

## Objective

Migrate admin and user apps to use core SDK's shared infrastructure:
1. **ApiClient** - Replace local api.ts with core's ApiClient
2. **Auth Store** - Replace local auth.ts with core's auth store
3. **EventBus** - Integrate for frontend-to-backend event communication

---

## Background

Current state:
- Admin app has local `api/index.ts` and `stores/auth.ts`
- User app has local API and auth implementations
- EventBus exists in core but is not used

Target state:
- Both apps use `@vbwd/view-component` ApiClient
- Both apps use `@vbwd/view-component` auth store
- EventBus integrated for FE→BE event communication

---

## Phase 1: ApiClient Migration

### 1.1 Review Core ApiClient

**Location:** `vbwd-frontend/core/src/api/`

- [ ] Review `ApiClient.ts` implementation
- [ ] Review `IApiClient.ts` interface
- [ ] Identify missing endpoints needed by admin/user apps
- [ ] Add any missing admin endpoints (`/api/v1/admin/*`)

### 1.2 Extend ApiClient for Admin Endpoints

```typescript
// core/src/api/ApiClient.ts

export class ApiClient implements IApiClient {
  // Existing methods...

  // Admin endpoints
  admin = {
    users: {
      list: (params) => this.get('/admin/users', params),
      get: (id) => this.get(`/admin/users/${id}`),
      update: (id, data) => this.put(`/admin/users/${id}`, data),
      suspend: (id) => this.put(`/admin/users/${id}/status`, { status: 'suspended' }),
    },
    plans: {
      list: () => this.get('/admin/tarif-plans'),
      create: (data) => this.post('/admin/tarif-plans', data),
      update: (id, data) => this.put(`/admin/tarif-plans/${id}`, data),
    },
    // ... other admin endpoints
  };
}
```

### 1.3 Migrate Admin App

**Location:** `vbwd-frontend/admin/vue/`

- [ ] Update imports in all files using local api.ts
- [ ] Replace `import { api } from '@/api'` with `import { apiClient } from '@vbwd/view-component'`
- [ ] Update API calls to use new interface
- [ ] Remove local `src/api/index.ts`
- [ ] Update tests to mock core's ApiClient
- [ ] Verify all 71 unit tests pass
- [ ] Verify all 108 E2E tests pass

### 1.4 Migrate User App

**Location:** `vbwd-frontend/user/vue/`

- [ ] Same migration steps as admin app
- [ ] Verify tests pass

---

## Phase 2: Auth Store Migration

### 2.1 Review Core Auth Store

**Location:** `vbwd-frontend/core/src/auth/`

- [ ] Review `authStore.ts` implementation
- [ ] Review `IAuthService.ts` interface
- [ ] Identify admin-specific features (role checks, admin token)
- [ ] Plan extension points if needed

### 2.2 Extend Auth Store for Admin Features

```typescript
// core/src/auth/authStore.ts

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    refreshToken: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    // Add more role-based getters
  },

  actions: {
    async login(credentials) { /* ... */ },
    async logout() { /* ... */ },
    async refreshToken() { /* ... */ },
    // Admin-specific actions
    async adminLogin(credentials) { /* ... */ },
  },
});
```

### 2.3 Migrate Admin App

- [ ] Update imports: `import { useAuthStore } from '@vbwd/view-component'`
- [ ] Verify admin role checks work (`isAdmin` getter)
- [ ] Update localStorage key if different (`admin_token` vs `token`)
- [ ] Remove local `src/stores/auth.ts`
- [ ] Update tests
- [ ] Verify login/logout flows work

### 2.4 Migrate User App

- [ ] Same migration steps
- [ ] Verify tests pass

---

## Phase 3: EventBus Integration

### 3.1 Design Event Schema

Define events for frontend-to-backend communication:

```typescript
// core/src/events/events.ts

export interface PlatformEvents {
  // User events
  'user:registered': { userId: string; email: string };
  'user:login': { userId: string; timestamp: Date };
  'user:logout': { userId: string };

  // Subscription events
  'subscription:created': { subscriptionId: string; planId: string; userId: string };
  'subscription:cancelled': { subscriptionId: string; reason: string };
  'subscription:upgraded': { subscriptionId: string; fromPlan: string; toPlan: string };

  // Payment events
  'payment:initiated': { invoiceId: string; amount: number; currency: string };
  'payment:completed': { invoiceId: string; paymentId: string };
  'payment:failed': { invoiceId: string; error: string };

  // Admin events
  'admin:user_suspended': { userId: string; adminId: string; reason: string };
  'admin:plan_created': { planId: string; adminId: string };
}
```

### 3.2 Backend Event Receiver

**Location:** `vbwd-backend/src/`

- [ ] Create `/api/v1/events` endpoint to receive frontend events
- [ ] Implement event handler that routes to appropriate services
- [ ] Add authentication/validation for event endpoint
- [ ] Integrate with existing event system in backend

```python
# backend route
@bp.route('/events', methods=['POST'])
@jwt_required()
def receive_event():
    event_type = request.json.get('type')
    event_data = request.json.get('data')

    event_dispatcher.dispatch(event_type, event_data)
    return jsonify({'status': 'received'}), 200
```

### 3.3 Frontend EventBus Setup

- [ ] Configure EventBus to send events to backend
- [ ] Add event batching for performance (optional)
- [ ] Add retry logic for failed event delivery
- [ ] Add offline queue (optional)

```typescript
// core/src/events/EventBus.ts

export class EventBus {
  private apiClient: IApiClient;

  async emit<T extends keyof PlatformEvents>(
    type: T,
    data: PlatformEvents[T]
  ): Promise<void> {
    // Emit locally for frontend listeners
    this.localEmit(type, data);

    // Send to backend
    await this.apiClient.post('/events', { type, data });
  }
}
```

### 3.4 Integrate in Apps

- [ ] Initialize EventBus in main.ts
- [ ] Emit events at key user actions
- [ ] Add event emission in stores (subscription, payment actions)

```typescript
// Example in subscriptions store
async cancelSubscription(id: string, reason: string) {
  await apiClient.admin.subscriptions.cancel(id);

  eventBus.emit('subscription:cancelled', {
    subscriptionId: id,
    reason,
  });
}
```

---

## Phase 4: Testing & Verification

### 4.1 Unit Tests

- [ ] Update all mocks to use core SDK interfaces
- [ ] Add tests for EventBus integration
- [ ] Verify all existing tests pass

### 4.2 Integration Tests

- [ ] Test ApiClient with real backend
- [ ] Test auth flows end-to-end
- [ ] Test event delivery to backend

### 4.3 E2E Tests

- [ ] Run full E2E suite against real backend
- [ ] Verify no regressions

---

## Files to Modify

### Admin App
- `src/main.ts` - Initialize core SDK
- `src/stores/*.ts` - Update API imports
- `src/views/*.vue` - Update API/auth imports
- Remove: `src/api/index.ts`, `src/stores/auth.ts`

### User App
- Similar changes

### Core SDK
- `src/api/ApiClient.ts` - Add admin endpoints
- `src/auth/authStore.ts` - Add admin features
- `src/events/EventBus.ts` - Add backend sending
- `src/events/events.ts` - Define event types

### Backend
- `src/routes/events.py` - New event receiver endpoint
- `src/services/event_service.py` - Event processing

---

## Acceptance Criteria

1. [ ] Admin app uses core's ApiClient (no local api.ts)
2. [ ] Admin app uses core's auth store (no local auth.ts)
3. [ ] User app uses core's ApiClient and auth store
4. [ ] EventBus sends events to backend
5. [ ] Backend receives and processes frontend events
6. [ ] All 71 unit tests pass
7. [ ] All 108 E2E tests pass
8. [ ] No functionality regression

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking changes in API interface | Feature flag to switch between old/new |
| Auth token storage differences | Support both keys during migration |
| Event delivery failures | Retry queue, graceful degradation |

---

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: ApiClient | Medium |
| Phase 2: Auth Store | Medium |
| Phase 3: EventBus | High |
| Phase 4: Testing | Medium |

---

*Created: 2026-01-05*
