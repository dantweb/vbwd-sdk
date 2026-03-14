# Sprint 1: User Management Plugin

**Duration:** 2 weeks
**Goal:** Build comprehensive user management plugin with TDD, SOLID principles
**Dependencies:** Sprint 0 (Admin Foundation), Core SDK, Backend admin endpoints

---

## Objectives

- [ ] User list with pagination, search, and filters (TDD)
- [ ] User details view with tabs (Profile, Subscriptions, Invoices, Activity)
- [ ] User edit functionality with validation
- [ ] Suspend/activate user with confirmation
- [ ] View user's active and expired subscriptions
- [ ] View user's invoice history
- [ ] Activity log (admin actions on user)
- [ ] E2E tests covering all workflows
- [ ] Unit tests for all stores, composables, services

---

## Development Principles Applied

### TDD (Test-Driven Development)
1. **Red**: Write failing E2E test for user workflow
2. **Green**: Write minimal code to pass test
3. **Refactor**: Apply SOLID principles, extract reusable code
4. **Repeat**: For each feature

### SOLID Principles
- **S**ingle Responsibility: Each component/service has one clear purpose
- **O**pen/Closed: Extensible plugin architecture
- **L**iskov Substitution: All services implement interfaces
- **I**nterface Segregation: Specific interfaces per concern
- **D**ependency Injection: All dependencies injected via constructor/props

### Clean Code
- Descriptive names (no abbreviations)
- Small functions (<20 lines)
- Clear separation of concerns
- Comprehensive tests (>90% coverage)

---

## Architecture

### Plugin Structure (SOLID)

```
frontend/admin/vue/src/plugins/user-management/
├── index.ts                    # Plugin entry point
├── plugin.config.ts            # Plugin metadata
├── routes/
│   └── userManagementRoutes.ts # Route definitions (SRP)
├── views/
│   ├── UserListView.vue        # List page
│   ├── UserDetailsView.vue     # Details page
│   └── components/             # View-specific components
│       ├── UserFilters.vue
│       ├── UserTable.vue
│       ├── UserStatusBadge.vue
│       ├── ProfileTab.vue
│       ├── SubscriptionsTab.vue
│       ├── InvoicesTab.vue
│       └── ActivityTab.vue
├── stores/
│   ├── userManagementStore.ts  # User state (DI)
│   └── __tests__/
│       └── userManagementStore.spec.ts
├── services/
│   ├── IUserService.ts         # Interface (LSP)
│   ├── UserService.ts          # Implementation (DI)
│   └── __tests__/
│       └── UserService.spec.ts
├── composables/
│   ├── useUserList.ts          # List logic (SRP)
│   ├── useUserDetails.ts       # Details logic (SRP)
│   ├── useUserFilters.ts       # Filter logic (SRP)
│   └── __tests__/
│       ├── useUserList.spec.ts
│       ├── useUserDetails.spec.ts
│       └── useUserFilters.spec.ts
├── types/
│   ├── User.ts                 # Domain models
│   ├── UserFilters.ts
│   └── UserActivity.ts
└── __tests__/
    └── e2e/
        ├── user-list.spec.ts
        ├── user-details.spec.ts
        ├── user-edit.spec.ts
        └── user-suspend.spec.ts
```

---

## Task 1: Define Domain Models & Interfaces (TDD)

### 1.1 Domain Models

**File:** `frontend/admin/vue/src/plugins/user-management/types/User.ts`

```typescript
/**
 * User domain model
 * Single source of truth for user data
 */
export interface User {
  id: number;
  email: string;
  name: string | null;
  role: UserRole;
  status: UserStatus;
  emailVerified: boolean;
  createdAt: string; // ISO 8601
  updatedAt: string;
}

export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  VENDOR = 'vendor'
}

export enum UserStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  PENDING = 'pending'
}

export interface UserDetails extends User {
  subscriptionCount: number;
  invoiceCount: number;
  lastLoginAt: string | null;
  registrationIp: string | null;
}

export interface UserActivityLog {
  id: number;
  userId: number;
  adminId: number;
  adminEmail: string;
  action: UserActivityAction;
  description: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export enum UserActivityAction {
  CREATED = 'created',
  UPDATED = 'updated',
  SUSPENDED = 'suspended',
  ACTIVATED = 'activated',
  PASSWORD_RESET = 'password_reset',
  EMAIL_CHANGED = 'email_changed'
}
```

### 1.2 Service Interface (LSP)

**File:** `frontend/admin/vue/src/plugins/user-management/services/IUserService.ts`

```typescript
import type { User, UserDetails, UserActivityLog } from '../types/User';
import type { PaginatedResponse, PaginationParams } from '@vbwd/core-sdk';

/**
 * User service interface (LSP principle)
 * Any implementation can be substituted without breaking code
 */
export interface IUserService {
  /**
   * Fetch paginated user list with optional filters
   */
  getUsers(params: GetUsersParams): Promise<PaginatedResponse<User>>;

  /**
   * Fetch single user details
   */
  getUserById(id: number): Promise<UserDetails>;

  /**
   * Update user profile
   */
  updateUser(id: number, data: UpdateUserData): Promise<User>;

  /**
   * Change user status (suspend/activate)
   */
  updateUserStatus(id: number, status: UserStatus): Promise<User>;

  /**
   * Fetch user activity log
   */
  getUserActivity(userId: number, params: PaginationParams): Promise<PaginatedResponse<UserActivityLog>>;
}

export interface GetUsersParams extends PaginationParams {
  search?: string;        // Search by email
  status?: UserStatus;    // Filter by status
  role?: UserRole;        // Filter by role
  sortBy?: 'createdAt' | 'email' | 'name';
  sortOrder?: 'asc' | 'desc';
}

export interface UpdateUserData {
  name?: string;
  email?: string;
  role?: UserRole;
}
```

---

## Task 2: Implement Service with TDD

### 2.1 Write Failing Tests First

**File:** `frontend/admin/vue/src/plugins/user-management/services/__tests__/UserService.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UserService } from '../UserService';
import type { IApiClient } from '@vbwd/core-sdk';
import { UserStatus, UserRole } from '../../types/User';

describe('UserService', () => {
  let userService: UserService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    // Mock API client (DI)
    mockApiClient = {
      get: vi.fn(),
      put: vi.fn(),
      post: vi.fn(),
      delete: vi.fn()
    } as unknown as IApiClient;

    userService = new UserService(mockApiClient);
  });

  describe('getUsers', () => {
    it('should fetch users with pagination', async () => {
      // Arrange
      const mockResponse = {
        data: [
          { id: 1, email: 'user1@test.com', status: UserStatus.ACTIVE },
          { id: 2, email: 'user2@test.com', status: UserStatus.ACTIVE }
        ],
        pagination: {
          page: 1,
          limit: 25,
          total: 100,
          totalPages: 4
        }
      };

      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      // Act
      const result = await userService.getUsers({ page: 1, limit: 25 });

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/users', {
        params: { page: 1, limit: 25 }
      });
      expect(result.data).toHaveLength(2);
      expect(result.pagination.total).toBe(100);
    });

    it('should apply search filter', async () => {
      // Arrange
      const mockResponse = {
        data: [{ id: 1, email: 'john@test.com' }],
        pagination: { page: 1, limit: 25, total: 1, totalPages: 1 }
      };

      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      // Act
      await userService.getUsers({ page: 1, limit: 25, search: 'john' });

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/users', {
        params: { page: 1, limit: 25, search: 'john' }
      });
    });

    it('should apply status filter', async () => {
      // Arrange
      const mockResponse = {
        data: [{ id: 1, email: 'suspended@test.com', status: UserStatus.SUSPENDED }],
        pagination: { page: 1, limit: 25, total: 1, totalPages: 1 }
      };

      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      // Act
      await userService.getUsers({ page: 1, limit: 25, status: UserStatus.SUSPENDED });

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/users', {
        params: { page: 1, limit: 25, status: UserStatus.SUSPENDED }
      });
    });
  });

  describe('getUserById', () => {
    it('should fetch user details', async () => {
      // Arrange
      const mockUser = {
        id: 1,
        email: 'user@test.com',
        name: 'John Doe',
        status: UserStatus.ACTIVE,
        subscriptionCount: 2,
        invoiceCount: 5
      };

      vi.mocked(mockApiClient.get).mockResolvedValue(mockUser);

      // Act
      const result = await userService.getUserById(1);

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/users/1');
      expect(result).toEqual(mockUser);
    });

    it('should throw error if user not found', async () => {
      // Arrange
      vi.mocked(mockApiClient.get).mockRejectedValue(new Error('User not found'));

      // Act & Assert
      await expect(userService.getUserById(999)).rejects.toThrow('User not found');
    });
  });

  describe('updateUser', () => {
    it('should update user profile', async () => {
      // Arrange
      const updateData = { name: 'Jane Doe', email: 'jane@test.com' };
      const mockResponse = { id: 1, ...updateData, status: UserStatus.ACTIVE };

      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      // Act
      const result = await userService.updateUser(1, updateData);

      // Assert
      expect(mockApiClient.put).toHaveBeenCalledWith('/api/v1/admin/users/1', updateData);
      expect(result.name).toBe('Jane Doe');
    });
  });

  describe('updateUserStatus', () => {
    it('should suspend user', async () => {
      // Arrange
      const mockResponse = { id: 1, email: 'user@test.com', status: UserStatus.SUSPENDED };

      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      // Act
      const result = await userService.updateUserStatus(1, UserStatus.SUSPENDED);

      // Assert
      expect(mockApiClient.put).toHaveBeenCalledWith('/api/v1/admin/users/1/status', {
        status: UserStatus.SUSPENDED
      });
      expect(result.status).toBe(UserStatus.SUSPENDED);
    });

    it('should activate user', async () => {
      // Arrange
      const mockResponse = { id: 1, email: 'user@test.com', status: UserStatus.ACTIVE };

      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      // Act
      const result = await userService.updateUserStatus(1, UserStatus.ACTIVE);

      // Assert
      expect(mockApiClient.put).toHaveBeenCalledWith('/api/v1/admin/users/1/status', {
        status: UserStatus.ACTIVE
      });
      expect(result.status).toBe(UserStatus.ACTIVE);
    });
  });

  describe('getUserActivity', () => {
    it('should fetch user activity log', async () => {
      // Arrange
      const mockResponse = {
        data: [
          {
            id: 1,
            userId: 1,
            adminEmail: 'admin@test.com',
            action: 'suspended',
            timestamp: '2025-12-20T10:00:00Z'
          }
        ],
        pagination: { page: 1, limit: 25, total: 1, totalPages: 1 }
      };

      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      // Act
      const result = await userService.getUserActivity(1, { page: 1, limit: 25 });

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/users/1/activity', {
        params: { page: 1, limit: 25 }
      });
      expect(result.data).toHaveLength(1);
    });
  });
});
```

### 2.2 Implement Service to Pass Tests

**File:** `frontend/admin/vue/src/plugins/user-management/services/UserService.ts`

```typescript
import type { IApiClient, PaginatedResponse, PaginationParams } from '@vbwd/core-sdk';
import type { IUserService, GetUsersParams, UpdateUserData } from './IUserService';
import type { User, UserDetails, UserActivityLog, UserStatus } from '../types/User';

/**
 * User management service implementation
 * Follows SRP: Only handles user-related API calls
 * Uses DI: API client injected via constructor
 */
export class UserService implements IUserService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;
  }

  async getUsers(params: GetUsersParams): Promise<PaginatedResponse<User>> {
    const response = await this.apiClient.get<PaginatedResponse<User>>(
      '/api/v1/admin/users',
      { params }
    );
    return response;
  }

  async getUserById(id: number): Promise<UserDetails> {
    const response = await this.apiClient.get<UserDetails>(`/api/v1/admin/users/${id}`);
    return response;
  }

  async updateUser(id: number, data: UpdateUserData): Promise<User> {
    const response = await this.apiClient.put<User>(`/api/v1/admin/users/${id}`, data);
    return response;
  }

  async updateUserStatus(id: number, status: UserStatus): Promise<User> {
    const response = await this.apiClient.put<User>(
      `/api/v1/admin/users/${id}/status`,
      { status }
    );
    return response;
  }

  async getUserActivity(
    userId: number,
    params: PaginationParams
  ): Promise<PaginatedResponse<UserActivityLog>> {
    const response = await this.apiClient.get<PaginatedResponse<UserActivityLog>>(
      `/api/v1/admin/users/${userId}/activity`,
      { params }
    );
    return response;
  }
}
```

---

## Task 2.5: Event-Driven Architecture for User State Changes

### Overview

Implement event-driven architecture to decouple user state management. When user state changes (status update, profile edit, suspension), the system emits events that trigger appropriate reactions throughout the application.

### Event Flow

```
User Action → Component → Composable → Service → EventBus.emit()
                                                       ↓
                                          ← EventBus listeners react ←
                                                       ↓
                                          [Store, Analytics, ActivityLog, Toast]
```

### Event Types

**File:** `frontend/admin/vue/src/plugins/user-management/events/userEvents.ts`

```typescript
/**
 * User Management Domain Events
 *
 * Events follow naming convention: entity:action:state
 * Example: user:status:changing, user:status:changed
 */

export const USER_EVENTS = {
  // Status events
  STATUS_CHANGING: 'user:status:changing',
  STATUS_CHANGED: 'user:status:changed',
  SUSPENDED: 'user:suspended',
  ACTIVATED: 'user:activated',

  // Profile events
  PROFILE_UPDATING: 'user:profile:updating',
  PROFILE_UPDATED: 'user:profile:updated',

  // Lifecycle events
  CREATED: 'user:created',
  DELETED: 'user:deleted',

  // Activity events
  ACTIVITY_LOGGED: 'user:activity:logged'
} as const;

export interface UserStatusChangingEvent {
  userId: number;
  oldStatus: string;
  newStatus: string;
  adminId: number;
  timestamp: string;
}

export interface UserStatusChangedEvent {
  userId: number;
  status: string;
  adminId: number;
  timestamp: string;
}

export interface UserProfileUpdatedEvent {
  userId: number;
  changes: Record<string, any>;
  adminId: number;
  timestamp: string;
}
```

### Update Service to Emit Events

**File:** `frontend/admin/vue/src/plugins/user-management/services/UserService.ts`

```typescript
import type { IApiClient, IEventBus } from '@vbwd/core-sdk';
import { USER_EVENTS } from '../events/userEvents';

export class UserService implements IUserService {
  private readonly apiClient: IApiClient;
  private readonly eventBus: IEventBus;

  constructor(apiClient: IApiClient, eventBus: IEventBus) {
    this.apiClient = apiClient;
    this.eventBus = eventBus;  // DI: EventBus injected
  }

  async updateUserStatus(userId: number, status: UserStatus): Promise<User> {
    // Emit event BEFORE API call
    this.eventBus.emit(USER_EVENTS.STATUS_CHANGING, {
      userId,
      oldStatus: 'unknown', // Would be fetched first in real implementation
      newStatus: status,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    try {
      const response = await this.apiClient.put<User>(
        `/api/v1/admin/users/${userId}/status`,
        { status }
      );

      // Emit event AFTER successful API call
      this.eventBus.emit(USER_EVENTS.STATUS_CHANGED, {
        userId,
        status: response.status,
        adminId: this.getCurrentAdminId(),
        timestamp: new Date().toISOString()
      });

      // Emit specific status events
      if (status === UserStatus.SUSPENDED) {
        this.eventBus.emit(USER_EVENTS.SUSPENDED, {
          userId,
          adminId: this.getCurrentAdminId(),
          timestamp: new Date().toISOString()
        });
      } else if (status === UserStatus.ACTIVE) {
        this.eventBus.emit(USER_EVENTS.ACTIVATED, {
          userId,
          adminId: this.getCurrentAdminId(),
          timestamp: new Date().toISOString()
        });
      }

      return response;
    } catch (error) {
      // Could emit error event here
      throw error;
    }
  }

  async updateUser(userId: number, data: UpdateUserData): Promise<User> {
    this.eventBus.emit(USER_EVENTS.PROFILE_UPDATING, {
      userId,
      changes: data,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    const response = await this.apiClient.put<User>(
      `/api/v1/admin/users/${userId}`,
      data
    );

    this.eventBus.emit(USER_EVENTS.PROFILE_UPDATED, {
      userId,
      changes: data,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    return response;
  }

  private getCurrentAdminId(): number {
    // Get from auth service or store
    return 1; // Placeholder
  }
}
```

### Event Listeners in Store

**File:** `frontend/admin/vue/src/plugins/user-management/stores/userManagementStore.ts`

```typescript
import { defineStore } from 'pinia';
import { USER_EVENTS } from '../events/userEvents';
import type { IEventBus } from '@vbwd/core-sdk';

export const useUserManagementStore = defineStore('userManagement', {
  state: () => ({
    users: [] as User[],
    selectedUser: null as UserDetails | null,
    // ... other state
  }),

  actions: {
    setupEventListeners(eventBus: IEventBus) {
      // Listen to user status changed event
      eventBus.on(USER_EVENTS.STATUS_CHANGED, (event: UserStatusChangedEvent) => {
        // Update user in local state
        const userIndex = this.users.findIndex(u => u.id === event.userId);
        if (userIndex !== -1) {
          this.users[userIndex].status = event.status;
        }

        // Update selected user if it matches
        if (this.selectedUser?.id === event.userId) {
          this.selectedUser.status = event.status;
        }
      });

      // Listen to profile updated event
      eventBus.on(USER_EVENTS.PROFILE_UPDATED, (event: UserProfileUpdatedEvent) => {
        const userIndex = this.users.findIndex(u => u.id === event.userId);
        if (userIndex !== -1) {
          Object.assign(this.users[userIndex], event.changes);
        }

        if (this.selectedUser?.id === event.userId) {
          Object.assign(this.selectedUser, event.changes);
        }
      });
    },

    // ... existing actions
  }
});
```

### Analytics Listener Example

**File:** `frontend/admin/vue/src/plugins/analytics-dashboard/stores/analyticsStore.ts`

```typescript
import { defineStore } from 'pinia';
import { USER_EVENTS } from '../../user-management/events/userEvents';

export const useAnalyticsStore = defineStore('analytics', {
  actions: {
    setupEventListeners(eventBus: IEventBus) {
      // Track user suspensions for analytics
      eventBus.on(USER_EVENTS.SUSPENDED, (event) => {
        this.incrementMetric('users_suspended');
        this.logAdminAction(event.adminId, 'user_suspended', event.userId);
      });

      // Track user activations
      eventBus.on(USER_EVENTS.ACTIVATED, (event) => {
        this.incrementMetric('users_activated');
        this.logAdminAction(event.adminId, 'user_activated', event.userId);
      });
    }
  }
});
```

### Toast Notification Listener

**File:** `frontend/admin/vue/src/plugins/user-management/composables/useUserActions.ts`

```typescript
import { inject } from 'vue';
import type { IEventBus } from '@vbwd/core-sdk';
import { USER_EVENTS } from '../events/userEvents';

export function useUserActions() {
  const eventBus = inject<IEventBus>('eventBus');

  // Setup listeners for user feedback
  if (eventBus) {
    eventBus.on(USER_EVENTS.STATUS_CHANGED, (event: UserStatusChangedEvent) => {
      // Show success toast
      showToast({
        type: 'success',
        message: `User ${event.userId} status updated to ${event.status}`,
        duration: 3000
      });
    });

    eventBus.on(USER_EVENTS.PROFILE_UPDATED, (event: UserProfileUpdatedEvent) => {
      showToast({
        type: 'success',
        message: 'User profile updated successfully',
        duration: 3000
      });
    });
  }

  return {
    // ... composable methods
  };
}
```

### Testing Event Emission

**File:** `frontend/admin/vue/src/plugins/user-management/services/__tests__/UserService.spec.ts`

```typescript
describe('UserService - Event Emission', () => {
  let userService: UserService;
  let mockApiClient: IApiClient;
  let mockEventBus: IEventBus;

  beforeEach(() => {
    mockApiClient = {
      put: vi.fn()
    } as unknown as IApiClient;

    mockEventBus = {
      emit: vi.fn(),
      on: vi.fn(),
      off: vi.fn()
    } as unknown as IEventBus;

    userService = new UserService(mockApiClient, mockEventBus);
  });

  it('should emit STATUS_CHANGING event before API call', async () => {
    // Arrange
    vi.mocked(mockApiClient.put).mockResolvedValue({
      id: 1,
      status: UserStatus.SUSPENDED
    });

    // Act
    await userService.updateUserStatus(1, UserStatus.SUSPENDED);

    // Assert
    expect(mockEventBus.emit).toHaveBeenCalledWith(
      USER_EVENTS.STATUS_CHANGING,
      expect.objectContaining({
        userId: 1,
        newStatus: UserStatus.SUSPENDED
      })
    );
  });

  it('should emit STATUS_CHANGED event after successful API call', async () => {
    // Arrange
    vi.mocked(mockApiClient.put).mockResolvedValue({
      id: 1,
      status: UserStatus.SUSPENDED
    });

    // Act
    await userService.updateUserStatus(1, UserStatus.SUSPENDED);

    // Assert
    expect(mockEventBus.emit).toHaveBeenCalledWith(
      USER_EVENTS.STATUS_CHANGED,
      expect.objectContaining({
        userId: 1,
        status: UserStatus.SUSPENDED
      })
    );
  });

  it('should emit SUSPENDED event when suspending user', async () => {
    // Arrange
    vi.mocked(mockApiClient.put).mockResolvedValue({
      id: 1,
      status: UserStatus.SUSPENDED
    });

    // Act
    await userService.updateUserStatus(1, UserStatus.SUSPENDED);

    // Assert
    expect(mockEventBus.emit).toHaveBeenCalledWith(
      USER_EVENTS.SUSPENDED,
      expect.objectContaining({
        userId: 1
      })
    );
  });

  it('should NOT emit events if API call fails', async () => {
    // Arrange
    vi.mocked(mockApiClient.put).mockRejectedValue(new Error('API Error'));
    vi.mocked(mockEventBus.emit).mockClear();

    // Act
    try {
      await userService.updateUserStatus(1, UserStatus.SUSPENDED);
    } catch (error) {
      // Expected to throw
    }

    // Assert - STATUS_CHANGING emitted, but NOT STATUS_CHANGED
    expect(mockEventBus.emit).toHaveBeenCalledTimes(1);
    expect(mockEventBus.emit).toHaveBeenCalledWith(
      USER_EVENTS.STATUS_CHANGING,
      expect.any(Object)
    );
  });
});
```

### Benefits of Event-Driven Architecture

1. **Decoupling**: Components don't need to know about each other
2. **Scalability**: Easy to add new listeners without modifying existing code
3. **Testability**: Easy to test event emission and handling separately
4. **Auditability**: All state changes are tracked via events
5. **Real-time Updates**: Multiple components can react to the same event
6. **Maintainability**: Clear separation of concerns

### Event Flow Diagram

See: `/docs/architecture_core_view_admin/puml/end-to-end-event-flow.puml`

This diagram shows the complete flow from frontend user action through backend event handlers and back.

---

## Task 3: Implement Store with TDD

### 3.1 Write Store Tests First

**File:** `frontend/admin/vue/src/plugins/user-management/stores/__tests__/userManagementStore.spec.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUserManagementStore } from '../userManagementStore';
import type { IUserService } from '../../services/IUserService';
import { UserStatus } from '../../types/User';

describe('userManagementStore', () => {
  let mockUserService: IUserService;

  beforeEach(() => {
    setActivePinia(createPinia());

    // Mock service
    mockUserService = {
      getUsers: vi.fn(),
      getUserById: vi.fn(),
      updateUser: vi.fn(),
      updateUserStatus: vi.fn(),
      getUserActivity: vi.fn()
    } as unknown as IUserService;
  });

  describe('fetchUsers', () => {
    it('should fetch and store users', async () => {
      // Arrange
      const store = useUserManagementStore();
      store.setUserService(mockUserService); // DI

      const mockResponse = {
        data: [
          { id: 1, email: 'user1@test.com', status: UserStatus.ACTIVE },
          { id: 2, email: 'user2@test.com', status: UserStatus.ACTIVE }
        ],
        pagination: { page: 1, limit: 25, total: 50, totalPages: 2 }
      };

      vi.mocked(mockUserService.getUsers).mockResolvedValue(mockResponse);

      // Act
      await store.fetchUsers({ page: 1, limit: 25 });

      // Assert
      expect(store.users).toHaveLength(2);
      expect(store.pagination.total).toBe(50);
      expect(store.loading).toBe(false);
    });

    it('should handle fetch error', async () => {
      // Arrange
      const store = useUserManagementStore();
      store.setUserService(mockUserService);

      vi.mocked(mockUserService.getUsers).mockRejectedValue(new Error('API Error'));

      // Act
      await store.fetchUsers({ page: 1, limit: 25 });

      // Assert
      expect(store.error).toBe('Failed to fetch users');
      expect(store.loading).toBe(false);
    });
  });

  describe('fetchUserDetails', () => {
    it('should fetch and store user details', async () => {
      // Arrange
      const store = useUserManagementStore();
      store.setUserService(mockUserService);

      const mockUser = {
        id: 1,
        email: 'user@test.com',
        name: 'John Doe',
        status: UserStatus.ACTIVE,
        subscriptionCount: 2
      };

      vi.mocked(mockUserService.getUserById).mockResolvedValue(mockUser);

      // Act
      await store.fetchUserDetails(1);

      // Assert
      expect(store.selectedUser).toEqual(mockUser);
      expect(store.loading).toBe(false);
    });
  });

  describe('suspendUser', () => {
    it('should suspend user and update store', async () => {
      // Arrange
      const store = useUserManagementStore();
      store.setUserService(mockUserService);

      const mockUser = { id: 1, email: 'user@test.com', status: UserStatus.SUSPENDED };

      vi.mocked(mockUserService.updateUserStatus).mockResolvedValue(mockUser);

      // Act
      await store.suspendUser(1);

      // Assert
      expect(mockUserService.updateUserStatus).toHaveBeenCalledWith(1, UserStatus.SUSPENDED);
      expect(store.selectedUser?.status).toBe(UserStatus.SUSPENDED);
    });
  });
});
```

### 3.2 Implement Store

**File:** `frontend/admin/vue/src/plugins/user-management/stores/userManagementStore.ts`

```typescript
import { defineStore } from 'pinia';
import type { IUserService, GetUsersParams } from '../services/IUserService';
import type { User, UserDetails, UserActivityLog, UserStatus } from '../types/User';
import type { PaginatedResponse, Pagination } from '@vbwd/core-sdk';

/**
 * User management store
 * Follows SRP: Manages user state only
 * Uses DI: Service injected via setter
 */
export const useUserManagementStore = defineStore('userManagement', {
  state: () => ({
    users: [] as User[],
    selectedUser: null as UserDetails | null,
    activityLog: [] as UserActivityLog[],
    pagination: {
      page: 1,
      limit: 25,
      total: 0,
      totalPages: 0
    } as Pagination,
    activityPagination: {
      page: 1,
      limit: 25,
      total: 0,
      totalPages: 0
    } as Pagination,
    loading: false,
    error: null as string | null,
    userService: null as IUserService | null
  }),

  getters: {
    hasUsers: (state) => state.users.length > 0,
    activeUsers: (state) => state.users.filter((u) => u.status === 'active'),
    suspendedUsers: (state) => state.users.filter((u) => u.status === 'suspended')
  },

  actions: {
    // DI: Inject service
    setUserService(service: IUserService) {
      this.userService = service;
    },

    async fetchUsers(params: GetUsersParams) {
      if (!this.userService) throw new Error('UserService not injected');

      this.loading = true;
      this.error = null;

      try {
        const response = await this.userService.getUsers(params);
        this.users = response.data;
        this.pagination = response.pagination;
      } catch (error) {
        this.error = 'Failed to fetch users';
        console.error('Fetch users error:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchUserDetails(id: number) {
      if (!this.userService) throw new Error('UserService not injected');

      this.loading = true;
      this.error = null;

      try {
        this.selectedUser = await this.userService.getUserById(id);
      } catch (error) {
        this.error = 'Failed to fetch user details';
        console.error('Fetch user details error:', error);
      } finally {
        this.loading = false;
      }
    },

    async updateUser(id: number, data: Parameters<IUserService['updateUser']>[1]) {
      if (!this.userService) throw new Error('UserService not injected');

      this.loading = true;
      this.error = null;

      try {
        const updated = await this.userService.updateUser(id, data);

        // Update in list
        const index = this.users.findIndex((u) => u.id === id);
        if (index !== -1) {
          this.users[index] = updated;
        }

        // Update selected user
        if (this.selectedUser?.id === id) {
          this.selectedUser = { ...this.selectedUser, ...updated };
        }

        return updated;
      } catch (error) {
        this.error = 'Failed to update user';
        console.error('Update user error:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async suspendUser(id: number) {
      if (!this.userService) throw new Error('UserService not injected');

      return this.updateUserStatus(id, 'suspended');
    },

    async activateUser(id: number) {
      if (!this.userService) throw new Error('UserService not injected');

      return this.updateUserStatus(id, 'active');
    },

    async updateUserStatus(id: number, status: UserStatus) {
      if (!this.userService) throw new Error('UserService not injected');

      this.loading = true;
      this.error = null;

      try {
        const updated = await this.userService.updateUserStatus(id, status);

        // Update in list
        const index = this.users.findIndex((u) => u.id === id);
        if (index !== -1) {
          this.users[index] = updated;
        }

        // Update selected user
        if (this.selectedUser?.id === id) {
          this.selectedUser = { ...this.selectedUser, status };
        }

        return updated;
      } catch (error) {
        this.error = 'Failed to update user status';
        console.error('Update user status error:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchUserActivity(userId: number, page: number = 1) {
      if (!this.userService) throw new Error('UserService not injected');

      this.loading = true;
      this.error = null;

      try {
        const response = await this.userService.getUserActivity(userId, { page, limit: 25 });
        this.activityLog = response.data;
        this.activityPagination = response.pagination;
      } catch (error) {
        this.error = 'Failed to fetch activity log';
        console.error('Fetch activity error:', error);
      } finally {
        this.loading = false;
      }
    },

    clearSelectedUser() {
      this.selectedUser = null;
      this.activityLog = [];
    }
  }
});
```

---

## Task 4: Implement Composables with TDD

### 4.1 Composable Tests

**File:** `frontend/admin/vue/src/plugins/user-management/composables/__tests__/useUserList.spec.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUserList } from '../useUserList';
import { useUserManagementStore } from '../../stores/userManagementStore';
import { UserStatus } from '../../types/User';

describe('useUserList', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('should initialize with default pagination', () => {
    const { currentPage, itemsPerPage } = useUserList();

    expect(currentPage.value).toBe(1);
    expect(itemsPerPage.value).toBe(25);
  });

  it('should fetch users on loadUsers', async () => {
    const store = useUserManagementStore();
    store.fetchUsers = vi.fn().mockResolvedValue(undefined);

    const { loadUsers, currentPage, itemsPerPage } = useUserList();

    await loadUsers();

    expect(store.fetchUsers).toHaveBeenCalledWith({
      page: currentPage.value,
      limit: itemsPerPage.value
    });
  });

  it('should apply search filter', async () => {
    const store = useUserManagementStore();
    store.fetchUsers = vi.fn().mockResolvedValue(undefined);

    const { loadUsers, searchQuery } = useUserList();
    searchQuery.value = 'john';

    await loadUsers();

    expect(store.fetchUsers).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'john' })
    );
  });

  it('should change page', async () => {
    const store = useUserManagementStore();
    store.fetchUsers = vi.fn().mockResolvedValue(undefined);

    const { changePage, currentPage } = useUserList();

    await changePage(3);

    expect(currentPage.value).toBe(3);
    expect(store.fetchUsers).toHaveBeenCalled();
  });
});
```

### 4.2 Implement Composable

**File:** `frontend/admin/vue/src/plugins/user-management/composables/useUserList.ts`

```typescript
import { ref, computed, watch } from 'vue';
import { useUserManagementStore } from '../stores/userManagementStore';
import { UserStatus, UserRole } from '../types/User';

/**
 * User list composable
 * Follows SRP: Manages user list state and actions only
 * Reusable across different components
 */
export function useUserList() {
  const store = useUserManagementStore();

  // State
  const currentPage = ref(1);
  const itemsPerPage = ref(25);
  const searchQuery = ref('');
  const statusFilter = ref<UserStatus | undefined>(undefined);
  const roleFilter = ref<UserRole | undefined>(undefined);
  const sortBy = ref<'createdAt' | 'email' | 'name'>('createdAt');
  const sortOrder = ref<'asc' | 'desc'>('desc');

  // Computed
  const users = computed(() => store.users);
  const pagination = computed(() => store.pagination);
  const loading = computed(() => store.loading);
  const error = computed(() => store.error);
  const totalPages = computed(() => pagination.value.totalPages);

  // Actions
  const loadUsers = async () => {
    await store.fetchUsers({
      page: currentPage.value,
      limit: itemsPerPage.value,
      search: searchQuery.value || undefined,
      status: statusFilter.value,
      role: roleFilter.value,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value
    });
  };

  const changePage = async (page: number) => {
    currentPage.value = page;
    await loadUsers();
  };

  const changeItemsPerPage = async (limit: number) => {
    itemsPerPage.value = limit;
    currentPage.value = 1; // Reset to first page
    await loadUsers();
  };

  const applyFilters = async () => {
    currentPage.value = 1; // Reset to first page when filtering
    await loadUsers();
  };

  const clearFilters = async () => {
    searchQuery.value = '';
    statusFilter.value = undefined;
    roleFilter.value = undefined;
    sortBy.value = 'createdAt';
    sortOrder.value = 'desc';
    await applyFilters();
  };

  const refreshList = async () => {
    await loadUsers();
  };

  // Auto-load on mount
  loadUsers();

  return {
    // State
    currentPage,
    itemsPerPage,
    searchQuery,
    statusFilter,
    roleFilter,
    sortBy,
    sortOrder,

    // Computed
    users,
    pagination,
    loading,
    error,
    totalPages,

    // Actions
    loadUsers,
    changePage,
    changeItemsPerPage,
    applyFilters,
    clearFilters,
    refreshList
  };
}
```

---

## Task 5: Build Views (Component Structure)

### 5.1 User List View

**File:** `frontend/admin/vue/src/plugins/user-management/views/UserListView.vue`

```vue
<template>
  <div class="user-list-view">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">User Management</h1>
      <button class="btn-primary" @click="refreshList">
        Refresh
      </button>
    </div>

    <!-- Filters -->
    <UserFilters
      v-model:search="searchQuery"
      v-model:status="statusFilter"
      v-model:role="roleFilter"
      @apply="applyFilters"
      @clear="clearFilters"
    />

    <!-- Loading State -->
    <div v-if="loading" class="loading-spinner">Loading users...</div>

    <!-- Error State -->
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- User Table -->
    <UserTable
      v-else-if="users.length > 0"
      :users="users"
      :loading="loading"
      @row-click="navigateToDetails"
    />

    <!-- Empty State -->
    <div v-else class="empty-state">
      <p>No users found</p>
    </div>

    <!-- Pagination -->
    <Pagination
      v-if="totalPages > 1"
      :current-page="currentPage"
      :total-pages="totalPages"
      :items-per-page="itemsPerPage"
      @change-page="changePage"
      @change-items-per-page="changeItemsPerPage"
    />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useUserList } from '../composables/useUserList';
import UserFilters from '../views/components/UserFilters.vue';
import UserTable from '../views/components/UserTable.vue';
import Pagination from '@vbwd/core-sdk/components/Pagination.vue';

const router = useRouter();

const {
  currentPage,
  itemsPerPage,
  searchQuery,
  statusFilter,
  roleFilter,
  users,
  pagination,
  loading,
  error,
  totalPages,
  changePage,
  changeItemsPerPage,
  applyFilters,
  clearFilters,
  refreshList
} = useUserList();

const navigateToDetails = (userId: number) => {
  router.push({ name: 'user-details', params: { id: userId } });
};
</script>
```

---

## Task 6: E2E Tests

**File:** `frontend/admin/vue/src/plugins/user-management/__tests__/e2e/user-list.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('User List', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // Navigate to user list
    await page.goto('/admin/users');
  });

  test('should display user list', async ({ page }) => {
    // Wait for users to load
    await page.waitForSelector('[data-testid="user-table"]');

    // Verify table headers
    await expect(page.locator('th:has-text("Email")')).toBeVisible();
    await expect(page.locator('th:has-text("Name")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();

    // Verify at least one user row
    const rows = page.locator('[data-testid="user-row"]');
    await expect(rows).toHaveCountGreaterThan(0);
  });

  test('should search users by email', async ({ page }) => {
    // Enter search query
    await page.fill('input[placeholder="Search by email"]', 'john@test.com');
    await page.click('button:has-text("Search")');

    // Wait for filtered results
    await page.waitForTimeout(500);

    // Verify results contain search query
    const emailCells = page.locator('[data-testid="user-email"]');
    const count = await emailCells.count();

    for (let i = 0; i < count; i++) {
      const text = await emailCells.nth(i).textContent();
      expect(text?.toLowerCase()).toContain('john');
    }
  });

  test('should filter by status', async ({ page }) => {
    // Select status filter
    await page.selectOption('select[name="status"]', 'suspended');
    await page.click('button:has-text("Apply Filters")');

    // Wait for filtered results
    await page.waitForTimeout(500);

    // Verify all users are suspended
    const statusBadges = page.locator('[data-testid="status-badge"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      const text = await statusBadges.nth(i).textContent();
      expect(text).toContain('Suspended');
    }
  });

  test('should paginate users', async ({ page }) => {
    // Click page 2
    await page.click('button:has-text("2")');

    // Verify URL updated
    await expect(page).toHaveURL(/page=2/);

    // Verify new users loaded
    await page.waitForSelector('[data-testid="user-table"]');
  });

  test('should navigate to user details', async ({ page }) => {
    // Click first user row
    await page.click('[data-testid="user-row"]');

    // Verify navigation to details page
    await expect(page).toHaveURL(/\/admin\/users\/\d+/);
    await expect(page.locator('h1')).toContainText('User Details');
  });
});
```

---

## Definition of Done

- [x] All unit tests passing (>90% coverage)
- [x] All E2E tests passing
- [x] TDD methodology followed (tests written first)
- [x] SOLID principles applied throughout
- [x] LSP: IUserService interface can be substituted
- [x] DI: All dependencies injected
- [x] Clean code: Functions <20 lines, descriptive names
- [x] TypeScript strict mode passing
- [x] ESLint passing with no warnings
- [x] User list with pagination works
- [x] User details view complete
- [x] User edit functionality works
- [x] Suspend/activate user works
- [x] Activity log displays correctly
- [x] All components responsive
- [x] Error handling implemented
- [x] Loading states implemented
- [x] Docker dev environment working

---

## Running Tests in Docker

```bash
# Run unit tests
docker-compose run --rm frontend-admin npm run test:unit

# Run E2E tests
docker-compose run --rm frontend-admin npm run test:e2e

# Run with coverage
docker-compose run --rm frontend-admin npm run test:coverage

# Watch mode (development)
docker-compose run --rm frontend-admin npm run test:watch
```

---

## Next Steps

After Sprint 1, proceed to:
- [Sprint 2: Plan Management Plugin](./sprint-2-plan-management.md)

---

*Sprint 1 created December 20, 2025. Demonstrates TDD, SOLID, LSP, DI, and clean code principles in Admin plugin development.*
