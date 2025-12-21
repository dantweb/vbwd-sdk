# Sprint 4: Event Bus & Validation

**Duration:** 1 week
**Goal:** Build event bus and validation service
**Dependencies:** Sprint 1

---

## Objectives

- [ ] Design IEventBus interface
- [ ] Implement EventBus with type-safe events
- [ ] Define PlatformEvents enum
- [ ] Design IValidationService interface
- [ ] Implement ValidationService with Zod
- [ ] Create common validation schemas
- [ ] Write comprehensive unit tests (95%+ coverage)

---

## Tasks

### 1. Event Types

**File:** `frontend/core/src/types/events.ts`

```typescript
import type { AuthUser } from './auth';
import type { Subscription, Invoice } from './api';

/**
 * Platform event types
 */
export enum PlatformEvents {
  // Auth events
  USER_LOGGED_IN = 'user:logged-in',
  USER_LOGGED_OUT = 'user:logged-out',
  USER_REGISTERED = 'user:registered',
  SESSION_EXPIRED = 'session:expired',

  // Subscription events
  SUBSCRIPTION_CREATED = 'subscription:created',
  SUBSCRIPTION_UPDATED = 'subscription:updated',
  SUBSCRIPTION_CANCELLED = 'subscription:cancelled',
  SUBSCRIPTION_EXPIRED = 'subscription:expired',

  // Checkout events
  CHECKOUT_STARTED = 'checkout:started',
  CHECKOUT_COMPLETED = 'checkout:completed',
  CHECKOUT_FAILED = 'checkout:failed',
  CHECKOUT_CANCELLED = 'checkout:cancelled',

  // Invoice events
  INVOICE_CREATED = 'invoice:created',
  INVOICE_PAID = 'invoice:paid',
  INVOICE_FAILED = 'invoice:failed',

  // UI events
  NOTIFICATION_SHOW = 'notification:show',
  NOTIFICATION_HIDE = 'notification:hide',
  MODAL_OPEN = 'modal:open',
  MODAL_CLOSE = 'modal:close',

  // Plugin events
  PLUGIN_LOADED = 'plugin:loaded',
  PLUGIN_ACTIVATED = 'plugin:activated',
  PLUGIN_DEACTIVATED = 'plugin:deactivated',
  PLUGIN_ERROR = 'plugin:error',
}

/**
 * Event payload types
 */
export interface EventPayloads {
  [PlatformEvents.USER_LOGGED_IN]: { user: AuthUser };
  [PlatformEvents.USER_LOGGED_OUT]: { userId: number };
  [PlatformEvents.USER_REGISTERED]: { user: AuthUser };
  [PlatformEvents.SESSION_EXPIRED]: Record<string, never>;

  [PlatformEvents.SUBSCRIPTION_CREATED]: { subscription: Subscription };
  [PlatformEvents.SUBSCRIPTION_UPDATED]: { subscription: Subscription };
  [PlatformEvents.SUBSCRIPTION_CANCELLED]: { subscriptionId: number };
  [PlatformEvents.SUBSCRIPTION_EXPIRED]: { subscriptionId: number };

  [PlatformEvents.CHECKOUT_STARTED]: { planId: number };
  [PlatformEvents.CHECKOUT_COMPLETED]: { subscription: Subscription };
  [PlatformEvents.CHECKOUT_FAILED]: { error: string };
  [PlatformEvents.CHECKOUT_CANCELLED]: Record<string, never>;

  [PlatformEvents.INVOICE_CREATED]: { invoice: Invoice };
  [PlatformEvents.INVOICE_PAID]: { invoice: Invoice };
  [PlatformEvents.INVOICE_FAILED]: { invoiceId: number; error: string };

  [PlatformEvents.NOTIFICATION_SHOW]: { message: string; type: 'success' | 'error' | 'warning' | 'info' };
  [PlatformEvents.NOTIFICATION_HIDE]: { id: string };
  [PlatformEvents.MODAL_OPEN]: { modalId: string };
  [PlatformEvents.MODAL_CLOSE]: { modalId: string };

  [PlatformEvents.PLUGIN_LOADED]: { pluginName: string };
  [PlatformEvents.PLUGIN_ACTIVATED]: { pluginName: string };
  [PlatformEvents.PLUGIN_DEACTIVATED]: { pluginName: string };
  [PlatformEvents.PLUGIN_ERROR]: { pluginName: string; error: Error };
}

/**
 * Event handler function type
 */
export type EventHandler<T = any> = (payload: T) => void | Promise<void>;
```

### 2. IEventBus Interface

**File:** `frontend/core/src/events/IEventBus.ts`

```typescript
import type { PlatformEvents, EventPayloads, EventHandler } from '../types/events';

/**
 * Event bus interface for decoupled communication
 */
export interface IEventBus {
  /**
   * Subscribe to an event
   * @returns Unsubscribe function
   */
  on<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>
  ): () => void;

  /**
   * Subscribe to an event (once)
   * @returns Unsubscribe function
   */
  once<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>
  ): () => void;

  /**
   * Unsubscribe from an event
   */
  off<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>
  ): void;

  /**
   * Emit an event
   */
  emit<E extends PlatformEvents>(event: E, payload: EventPayloads[E]): void;

  /**
   * Emit an event asynchronously
   */
  emitAsync<E extends PlatformEvents>(event: E, payload: EventPayloads[E]): Promise<void>;

  /**
   * Clear all listeners for an event
   */
  clear(event?: PlatformEvents): void;

  /**
   * Get listener count for an event
   */
  listenerCount(event: PlatformEvents): number;
}
```

### 3. EventBus Implementation

**File:** `frontend/core/src/events/EventBus.ts`

```typescript
import type { IEventBus } from './IEventBus';
import type { PlatformEvents, EventPayloads, EventHandler } from '../types/events';

interface EventListener {
  handler: EventHandler<any>;
  once: boolean;
}

export class EventBus implements IEventBus {
  private listeners = new Map<string, EventListener[]>();

  on<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>
  ): () => void {
    this.addEventListener(event, handler, false);
    return () => this.off(event, handler);
  }

  once<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>
  ): () => void {
    this.addEventListener(event, handler, true);
    return () => this.off(event, handler);
  }

  off<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>
  ): void {
    const listeners = this.listeners.get(event);
    if (!listeners) return;

    const index = listeners.findIndex((l) => l.handler === handler);
    if (index !== -1) {
      listeners.splice(index, 1);
    }

    if (listeners.length === 0) {
      this.listeners.delete(event);
    }
  }

  emit<E extends PlatformEvents>(event: E, payload: EventPayloads[E]): void {
    const listeners = this.listeners.get(event);
    if (!listeners || listeners.length === 0) return;

    // Create a copy to avoid issues if handlers modify the list
    const listenersCopy = [...listeners];

    for (const listener of listenersCopy) {
      try {
        listener.handler(payload);

        // Remove one-time listeners
        if (listener.once) {
          this.off(event, listener.handler);
        }
      } catch (error) {
        console.error(`Error in event handler for "${event}":`, error);
      }
    }
  }

  async emitAsync<E extends PlatformEvents>(
    event: E,
    payload: EventPayloads[E]
  ): Promise<void> {
    const listeners = this.listeners.get(event);
    if (!listeners || listeners.length === 0) return;

    // Create a copy to avoid issues if handlers modify the list
    const listenersCopy = [...listeners];

    for (const listener of listenersCopy) {
      try {
        await listener.handler(payload);

        // Remove one-time listeners
        if (listener.once) {
          this.off(event, listener.handler);
        }
      } catch (error) {
        console.error(`Error in async event handler for "${event}":`, error);
      }
    }
  }

  clear(event?: PlatformEvents): void {
    if (event) {
      this.listeners.delete(event);
    } else {
      this.listeners.clear();
    }
  }

  listenerCount(event: PlatformEvents): number {
    return this.listeners.get(event)?.length ?? 0;
  }

  private addEventListener<E extends PlatformEvents>(
    event: E,
    handler: EventHandler<EventPayloads[E]>,
    once: boolean
  ): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }

    this.listeners.get(event)!.push({ handler, once });
  }
}
```

### 4. Validation Schemas

**File:** `frontend/core/src/validation/schemas.ts`

```typescript
import { z } from 'zod';

/**
 * Common validation schemas
 */

export const emailSchema = z.string().email('Invalid email address');

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number');

export const nameSchema = z
  .string()
  .min(2, 'Name must be at least 2 characters')
  .max(50, 'Name must be at most 50 characters');

export const phoneSchema = z
  .string()
  .regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number');

// Login schema
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
});

// Register schema
export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  firstName: nameSchema,
  lastName: nameSchema,
  gdprConsent: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the terms and conditions' }),
  }),
});

// Profile update schema
export const updateProfileSchema = z.object({
  firstName: nameSchema.optional(),
  lastName: nameSchema.optional(),
  phone: phoneSchema.optional(),
});

// Checkout schema
export const checkoutSchema = z.object({
  planId: z.number().int().positive(),
  paymentMethod: z.enum(['stripe', 'paypal']),
  billingDetails: z.object({
    firstName: nameSchema,
    lastName: nameSchema,
    email: emailSchema,
    address: z.string().min(5, 'Address is required'),
    city: z.string().min(2, 'City is required'),
    country: z.string().length(2, 'Country code must be 2 characters'),
    zipCode: z.string().min(3, 'ZIP code is required'),
  }),
  successUrl: z.string().url(),
  cancelUrl: z.string().url(),
});
```

### 5. IValidationService Interface

**File:** `frontend/core/src/validation/IValidationService.ts`

```typescript
import type { z } from 'zod';

export interface ValidationResult<T = any> {
  success: boolean;
  data?: T;
  errors?: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface IValidationService {
  /**
   * Validate data against a schema
   */
  validate<T>(schema: z.ZodSchema<T>, data: unknown): ValidationResult<T>;

  /**
   * Validate data and throw on error
   */
  validateOrThrow<T>(schema: z.ZodSchema<T>, data: unknown): T;

  /**
   * Format Zod errors
   */
  formatErrors(error: z.ZodError): ValidationError[];
}
```

### 6. ValidationService Implementation

**File:** `frontend/core/src/validation/ValidationService.ts`

```typescript
import type { z } from 'zod';
import type { IValidationService, ValidationResult, ValidationError } from './IValidationService';

export class ValidationService implements IValidationService {
  validate<T>(schema: z.ZodSchema<T>, data: unknown): ValidationResult<T> {
    const result = schema.safeParse(data);

    if (result.success) {
      return {
        success: true,
        data: result.data,
      };
    }

    return {
      success: false,
      errors: this.formatErrors(result.error),
    };
  }

  validateOrThrow<T>(schema: z.ZodSchema<T>, data: unknown): T {
    return schema.parse(data);
  }

  formatErrors(error: z.ZodError): ValidationError[] {
    return error.errors.map((err) => ({
      field: err.path.join('.'),
      message: err.message,
    }));
  }
}
```

### 7. Barrel Exports

**File:** `frontend/core/src/events/index.ts`

```typescript
export * from './IEventBus';
export * from './EventBus';
```

**File:** `frontend/core/src/validation/index.ts`

```typescript
export * from './IValidationService';
export * from './ValidationService';
export * from './schemas';
```

---

## Testing Strategy

### Unit Tests

**File:** `frontend/core/__tests__/unit/events/EventBus.test.ts`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { EventBus } from '../../../src/events/EventBus';
import { PlatformEvents } from '../../../src/types/events';

describe('EventBus', () => {
  it('should emit and receive events', () => {
    const bus = new EventBus();
    const handler = vi.fn();

    bus.on(PlatformEvents.USER_LOGGED_IN, handler);
    bus.emit(PlatformEvents.USER_LOGGED_IN, {
      user: {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        status: 'active',
      },
    });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('should remove one-time listeners after emit', () => {
    const bus = new EventBus();
    const handler = vi.fn();

    bus.once(PlatformEvents.USER_LOGGED_IN, handler);
    bus.emit(PlatformEvents.USER_LOGGED_IN, {
      user: {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        status: 'active',
      },
    });
    bus.emit(PlatformEvents.USER_LOGGED_IN, {
      user: {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        status: 'active',
      },
    });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('should unsubscribe handlers', () => {
    const bus = new EventBus();
    const handler = vi.fn();

    const unsubscribe = bus.on(PlatformEvents.USER_LOGGED_IN, handler);
    unsubscribe();

    bus.emit(PlatformEvents.USER_LOGGED_IN, {
      user: {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        status: 'active',
      },
    });

    expect(handler).not.toHaveBeenCalled();
  });
});
```

**File:** `frontend/core/__tests__/unit/validation/ValidationService.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { ValidationService } from '../../../src/validation/ValidationService';
import { loginSchema, registerSchema } from '../../../src/validation/schemas';

describe('ValidationService', () => {
  const validationService = new ValidationService();

  it('should validate correct login data', () => {
    const data = {
      email: 'test@example.com',
      password: 'password123',
    };

    const result = validationService.validate(loginSchema, data);

    expect(result.success).toBe(true);
    expect(result.data).toEqual(data);
  });

  it('should fail validation for invalid email', () => {
    const data = {
      email: 'invalid-email',
      password: 'password123',
    };

    const result = validationService.validate(loginSchema, data);

    expect(result.success).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors?.[0]?.field).toBe('email');
  });

  it('should validate register data with GDPR consent', () => {
    const data = {
      email: 'test@example.com',
      password: 'Password123',
      firstName: 'Test',
      lastName: 'User',
      gdprConsent: true,
    };

    const result = validationService.validate(registerSchema, data);

    expect(result.success).toBe(true);
  });

  it('should fail without GDPR consent', () => {
    const data = {
      email: 'test@example.com',
      password: 'Password123',
      firstName: 'Test',
      lastName: 'User',
      gdprConsent: false,
    };

    const result = validationService.validate(registerSchema, data);

    expect(result.success).toBe(false);
    expect(result.errors?.some((e) => e.field === 'gdprConsent')).toBe(true);
  });
});
```

---

## Advanced EventBus Implementation

### 8. EventBus Integration with ApiClient

The ApiClient should emit events for all API operations to enable monitoring, logging, and reactive UI updates.

**File:** `frontend/core/src/api/ApiClient.ts`

```typescript
import type { IApiClient } from './IApiClient';
import type { IEventBus } from '../events/IEventBus';
import type { ApiConfig, ApiResponse } from '../types/api';

/**
 * API events for request lifecycle
 */
export const API_EVENTS = {
  REQUEST_START: 'api:request:start',
  REQUEST_SUCCESS: 'api:request:success',
  REQUEST_ERROR: 'api:request:error',
  REQUEST_COMPLETE: 'api:request:complete',
  UNAUTHORIZED: 'api:unauthorized',
  NETWORK_ERROR: 'api:network:error',
  TIMEOUT: 'api:timeout'
} as const;

export interface ApiRequestEvent {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  data?: any;
  timestamp: string;
  requestId: string;
}

export interface ApiResponseEvent extends ApiRequestEvent {
  status: number;
  duration: number;
  response?: any;
  error?: string;
}

export class ApiClient implements IApiClient {
  private baseURL: string;
  private headers: Record<string, string>;
  private readonly eventBus: IEventBus;

  constructor(config: ApiConfig, eventBus: IEventBus) {
    this.baseURL = config.baseURL;
    this.headers = config.headers || {};
    this.eventBus = eventBus;  // DI: EventBus injected
  }

  async get<T>(url: string): Promise<T> {
    return this.request<T>('GET', url);
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>('POST', url, data);
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>('PUT', url, data);
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    return this.request<T>('PATCH', url, data);
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>('DELETE', url);
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    url: string,
    data?: any
  ): Promise<T> {
    const requestId = this.generateRequestId();
    const startTime = Date.now();

    // Emit REQUEST_START event
    const requestEvent: ApiRequestEvent = {
      url,
      method,
      data,
      timestamp: new Date().toISOString(),
      requestId
    };

    this.eventBus.emit(API_EVENTS.REQUEST_START, requestEvent);

    try {
      const response = await fetch(`${this.baseURL}${url}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.headers,
        },
        body: data ? JSON.stringify(data) : undefined,
      });

      const duration = Date.now() - startTime;

      // Handle unauthorized
      if (response.status === 401) {
        this.eventBus.emit(API_EVENTS.UNAUTHORIZED, {
          ...requestEvent,
          status: 401,
          duration
        });
        throw new Error('Unauthorized');
      }

      // Parse response
      let responseData: T;
      const contentType = response.headers.get('content-type');

      if (contentType?.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text() as T;
      }

      if (!response.ok) {
        // Emit REQUEST_ERROR event
        this.eventBus.emit(API_EVENTS.REQUEST_ERROR, {
          ...requestEvent,
          status: response.status,
          duration,
          error: typeof responseData === 'string' ? responseData : 'Request failed'
        });

        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Emit REQUEST_SUCCESS event
      this.eventBus.emit(API_EVENTS.REQUEST_SUCCESS, {
        ...requestEvent,
        status: response.status,
        duration,
        response: responseData
      });

      // Emit REQUEST_COMPLETE event
      this.eventBus.emit(API_EVENTS.REQUEST_COMPLETE, {
        ...requestEvent,
        status: response.status,
        duration
      });

      return responseData;

    } catch (error: any) {
      const duration = Date.now() - startTime;

      // Emit appropriate error event
      if (error.name === 'AbortError' || error.message.includes('timeout')) {
        this.eventBus.emit(API_EVENTS.TIMEOUT, {
          ...requestEvent,
          status: 0,
          duration,
          error: error.message
        });
      } else if (!navigator.onLine || error.message.includes('Failed to fetch')) {
        this.eventBus.emit(API_EVENTS.NETWORK_ERROR, {
          ...requestEvent,
          status: 0,
          duration,
          error: 'Network error'
        });
      } else {
        this.eventBus.emit(API_EVENTS.REQUEST_ERROR, {
          ...requestEvent,
          status: 0,
          duration,
          error: error.message
        });
      }

      // Emit REQUEST_COMPLETE event
      this.eventBus.emit(API_EVENTS.REQUEST_COMPLETE, {
        ...requestEvent,
        status: 0,
        duration
      });

      throw error;
    }
  }

  setAuthToken(token: string): void {
    this.headers['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken(): void {
    delete this.headers['Authorization'];
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

### 9. Event-Driven Service Patterns

Services should emit domain events for state changes, enabling decoupled communication between components.

**Example: UserService with Events**

**File:** `frontend/user/vue/src/services/UserService.ts`

```typescript
import type { IApiClient } from '@core/api';
import type { IEventBus } from '@core/events';
import type { User, UpdateUserData } from '../types/user';

/**
 * User domain events
 */
export const USER_EVENTS = {
  PROFILE_UPDATING: 'user:profile:updating',
  PROFILE_UPDATED: 'user:profile:updated',
  PROFILE_UPDATE_FAILED: 'user:profile:update:failed',
  PASSWORD_CHANGING: 'user:password:changing',
  PASSWORD_CHANGED: 'user:password:changed',
  AVATAR_UPLOADING: 'user:avatar:uploading',
  AVATAR_UPLOADED: 'user:avatar:uploaded'
} as const;

export interface IUserService {
  updateProfile(userId: number, data: UpdateUserData): Promise<User>;
  changePassword(userId: number, oldPassword: string, newPassword: string): Promise<void>;
  uploadAvatar(userId: number, file: File): Promise<string>;
}

export class UserService implements IUserService {
  constructor(
    private readonly apiClient: IApiClient,
    private readonly eventBus: IEventBus  // DI: EventBus injected
  ) {}

  async updateProfile(userId: number, data: UpdateUserData): Promise<User> {
    // Emit event BEFORE API call
    this.eventBus.emit(USER_EVENTS.PROFILE_UPDATING, {
      userId,
      data,
      timestamp: new Date().toISOString()
    });

    try {
      const user = await this.apiClient.put<User>(
        `/api/v1/users/${userId}`,
        data
      );

      // Emit event AFTER successful update
      this.eventBus.emit(USER_EVENTS.PROFILE_UPDATED, {
        userId,
        user,
        timestamp: new Date().toISOString()
      });

      return user;

    } catch (error: any) {
      // Emit failure event
      this.eventBus.emit(USER_EVENTS.PROFILE_UPDATE_FAILED, {
        userId,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async changePassword(
    userId: number,
    oldPassword: string,
    newPassword: string
  ): Promise<void> {
    // Emit event BEFORE password change
    this.eventBus.emit(USER_EVENTS.PASSWORD_CHANGING, {
      userId,
      timestamp: new Date().toISOString()
    });

    try {
      await this.apiClient.post(
        `/api/v1/users/${userId}/change-password`,
        { oldPassword, newPassword }
      );

      // Emit event AFTER successful change
      this.eventBus.emit(USER_EVENTS.PASSWORD_CHANGED, {
        userId,
        timestamp: new Date().toISOString()
      });

    } catch (error: any) {
      throw error;
    }
  }

  async uploadAvatar(userId: number, file: File): Promise<string> {
    // Emit event BEFORE upload
    this.eventBus.emit(USER_EVENTS.AVATAR_UPLOADING, {
      userId,
      fileName: file.name,
      fileSize: file.size,
      timestamp: new Date().toISOString()
    });

    const formData = new FormData();
    formData.append('avatar', file);

    try {
      const response = await this.apiClient.post<{ avatarUrl: string }>(
        `/api/v1/users/${userId}/avatar`,
        formData
      );

      // Emit event AFTER successful upload
      this.eventBus.emit(USER_EVENTS.AVATAR_UPLOADED, {
        userId,
        avatarUrl: response.avatarUrl,
        timestamp: new Date().toISOString()
      });

      return response.avatarUrl;

    } catch (error: any) {
      throw error;
    }
  }
}
```

### 10. Plugin Integration Examples

Plugins should listen to events from the Core SDK and other plugins to react to state changes.

**Example: User Plugin Store with Event Listeners**

**File:** `frontend/user/vue/src/stores/userStore.ts`

```typescript
import { defineStore } from 'pinia';
import type { IEventBus } from '@core/events';
import type { User } from '../types/user';
import { USER_EVENTS } from '../services/UserService';
import { API_EVENTS } from '@core/api';

interface UserState {
  currentUser: User | null;
  loading: boolean;
  error: string | null;
  avatarUploadProgress: number;
  apiRequestsInProgress: number;
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    currentUser: null,
    loading: false,
    error: null,
    avatarUploadProgress: 0,
    apiRequestsInProgress: 0
  }),

  actions: {
    /**
     * Setup event listeners (called in plugin initialization)
     */
    setupEventListeners(eventBus: IEventBus): () => void {
      const unsubscribers: Array<() => void> = [];

      // Listen to profile updates
      unsubscribers.push(
        eventBus.on(USER_EVENTS.PROFILE_UPDATING, () => {
          this.loading = true;
          this.error = null;
        })
      );

      unsubscribers.push(
        eventBus.on(USER_EVENTS.PROFILE_UPDATED, (event) => {
          this.currentUser = event.user;
          this.loading = false;
        })
      );

      unsubscribers.push(
        eventBus.on(USER_EVENTS.PROFILE_UPDATE_FAILED, (event) => {
          this.error = event.error;
          this.loading = false;
        })
      );

      // Listen to avatar uploads
      unsubscribers.push(
        eventBus.on(USER_EVENTS.AVATAR_UPLOADING, () => {
          this.avatarUploadProgress = 0;
        })
      );

      unsubscribers.push(
        eventBus.on(USER_EVENTS.AVATAR_UPLOADED, (event) => {
          if (this.currentUser) {
            this.currentUser.avatarUrl = event.avatarUrl;
          }
          this.avatarUploadProgress = 100;
        })
      );

      // Listen to API events for global loading state
      unsubscribers.push(
        eventBus.on(API_EVENTS.REQUEST_START, (event) => {
          if (event.url.includes('/users/')) {
            this.apiRequestsInProgress++;
          }
        })
      );

      unsubscribers.push(
        eventBus.on(API_EVENTS.REQUEST_COMPLETE, (event) => {
          if (event.url.includes('/users/')) {
            this.apiRequestsInProgress--;
          }
        })
      );

      // Listen to unauthorized events (logout user)
      unsubscribers.push(
        eventBus.on(API_EVENTS.UNAUTHORIZED, () => {
          this.currentUser = null;
          // Could emit a logout event here
        })
      );

      // Return cleanup function
      return () => {
        unsubscribers.forEach(unsubscribe => unsubscribe());
      };
    }
  }
});
```

**Example: Analytics Plugin Listening to Events**

**File:** `frontend/admin/vue/src/plugins/analytics/stores/analyticsStore.ts`

```typescript
import { defineStore } from 'pinia';
import type { IEventBus } from '@core/events';
import { USER_EVENTS } from '@admin/user-management/services/UserService';
import { SUBSCRIPTION_EVENTS } from '@admin/subscription-management/services/SubscriptionService';
import { API_EVENTS } from '@core/api';

interface AnalyticsEvent {
  type: string;
  timestamp: string;
  metadata: Record<string, any>;
}

interface AnalyticsState {
  events: AnalyticsEvent[];
  metrics: {
    totalApiCalls: number;
    failedApiCalls: number;
    averageResponseTime: number;
    userActionsToday: number;
    subscriptionChangesToday: number;
  };
}

export const useAnalyticsStore = defineStore('analytics', {
  state: (): AnalyticsState => ({
    events: [],
    metrics: {
      totalApiCalls: 0,
      failedApiCalls: 0,
      averageResponseTime: 0,
      userActionsToday: 0,
      subscriptionChangesToday: 0
    }
  }),

  actions: {
    setupEventListeners(eventBus: IEventBus): () => void {
      const unsubscribers: Array<() => void> = [];

      // Track all API requests
      unsubscribers.push(
        eventBus.on(API_EVENTS.REQUEST_SUCCESS, (event) => {
          this.trackEvent('api_request_success', event);
          this.metrics.totalApiCalls++;
          this.updateAverageResponseTime(event.duration);
        })
      );

      unsubscribers.push(
        eventBus.on(API_EVENTS.REQUEST_ERROR, (event) => {
          this.trackEvent('api_request_error', event);
          this.metrics.failedApiCalls++;
        })
      );

      // Track user management events
      unsubscribers.push(
        eventBus.on(USER_EVENTS.STATUS_CHANGED, (event) => {
          this.trackEvent('user_status_changed', event);
          this.metrics.userActionsToday++;
        })
      );

      unsubscribers.push(
        eventBus.on(USER_EVENTS.SUSPENDED, (event) => {
          this.trackEvent('user_suspended', event);
          this.sendAlertToSlack('User suspended', event);
        })
      );

      // Track subscription events
      unsubscribers.push(
        eventBus.on(SUBSCRIPTION_EVENTS.CANCELLED, (event) => {
          this.trackEvent('subscription_cancelled', event);
          this.metrics.subscriptionChangesToday++;
          this.trackCancellationReason(event.reason);
        })
      );

      unsubscribers.push(
        eventBus.on(SUBSCRIPTION_EVENTS.PAYMENT_FAILED, (event) => {
          this.trackEvent('payment_failed', event);
          this.sendAlertToSlack('Payment failed', event);
        })
      );

      return () => {
        unsubscribers.forEach(unsubscribe => unsubscribe());
      };
    },

    trackEvent(type: string, metadata: Record<string, any>) {
      this.events.push({
        type,
        timestamp: new Date().toISOString(),
        metadata
      });

      // Keep only last 1000 events
      if (this.events.length > 1000) {
        this.events.shift();
      }
    },

    updateAverageResponseTime(duration: number) {
      const total = this.metrics.averageResponseTime * (this.metrics.totalApiCalls - 1);
      this.metrics.averageResponseTime = (total + duration) / this.metrics.totalApiCalls;
    },

    trackCancellationReason(reason: string) {
      // Implementation for tracking cancellation reasons
    },

    sendAlertToSlack(message: string, data: any) {
      // Implementation for Slack alerts
    }
  }
});
```

### 11. Advanced Testing Patterns

**Testing Services with EventBus**

**File:** `frontend/user/vue/__tests__/unit/services/UserService.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UserService, USER_EVENTS } from '../../../src/services/UserService';
import type { IApiClient } from '@core/api';
import type { IEventBus } from '@core/events';
import type { User } from '../../../src/types/user';

describe('UserService', () => {
  let userService: UserService;
  let mockApiClient: IApiClient;
  let mockEventBus: IEventBus;

  beforeEach(() => {
    // Create mock ApiClient
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      setAuthToken: vi.fn(),
      clearAuthToken: vi.fn()
    } as IApiClient;

    // Create mock EventBus
    mockEventBus = {
      on: vi.fn(() => vi.fn()),
      once: vi.fn(() => vi.fn()),
      off: vi.fn(),
      emit: vi.fn(),
      emitAsync: vi.fn(),
      clear: vi.fn(),
      listenerCount: vi.fn(() => 0)
    } as IEventBus;

    // Create service with mocked dependencies
    userService = new UserService(mockApiClient, mockEventBus);
  });

  describe('updateProfile', () => {
    it('should emit PROFILE_UPDATING event before API call', async () => {
      // Arrange
      const userId = 1;
      const updateData = { firstName: 'John', lastName: 'Doe' };
      const updatedUser: User = {
        id: userId,
        email: 'john@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        status: 'active'
      };

      vi.mocked(mockApiClient.put).mockResolvedValue(updatedUser);

      // Act
      await userService.updateProfile(userId, updateData);

      // Assert
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        USER_EVENTS.PROFILE_UPDATING,
        expect.objectContaining({
          userId,
          data: updateData
        })
      );
    });

    it('should emit PROFILE_UPDATED event after successful API call', async () => {
      // Arrange
      const userId = 1;
      const updateData = { firstName: 'John', lastName: 'Doe' };
      const updatedUser: User = {
        id: userId,
        email: 'john@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        status: 'active'
      };

      vi.mocked(mockApiClient.put).mockResolvedValue(updatedUser);

      // Act
      await userService.updateProfile(userId, updateData);

      // Assert
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        USER_EVENTS.PROFILE_UPDATED,
        expect.objectContaining({
          userId,
          user: updatedUser
        })
      );
    });

    it('should emit PROFILE_UPDATE_FAILED event on API error', async () => {
      // Arrange
      const userId = 1;
      const updateData = { firstName: 'John', lastName: 'Doe' };
      const error = new Error('Network error');

      vi.mocked(mockApiClient.put).mockRejectedValue(error);

      // Act & Assert
      await expect(userService.updateProfile(userId, updateData)).rejects.toThrow('Network error');

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        USER_EVENTS.PROFILE_UPDATE_FAILED,
        expect.objectContaining({
          userId,
          error: 'Network error'
        })
      );
    });

    it('should emit events in correct order', async () => {
      // Arrange
      const userId = 1;
      const updateData = { firstName: 'John', lastName: 'Doe' };
      const updatedUser: User = {
        id: userId,
        email: 'john@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        status: 'active'
      };

      vi.mocked(mockApiClient.put).mockResolvedValue(updatedUser);

      // Act
      await userService.updateProfile(userId, updateData);

      // Assert
      const emitCalls = vi.mocked(mockEventBus.emit).mock.calls;
      expect(emitCalls[0][0]).toBe(USER_EVENTS.PROFILE_UPDATING);
      expect(emitCalls[1][0]).toBe(USER_EVENTS.PROFILE_UPDATED);
    });
  });

  describe('changePassword', () => {
    it('should emit PASSWORD_CHANGING event before API call', async () => {
      // Arrange
      const userId = 1;
      const oldPassword = 'OldPassword123';
      const newPassword = 'NewPassword123';

      vi.mocked(mockApiClient.post).mockResolvedValue({});

      // Act
      await userService.changePassword(userId, oldPassword, newPassword);

      // Assert
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        USER_EVENTS.PASSWORD_CHANGING,
        expect.objectContaining({
          userId
        })
      );
    });

    it('should emit PASSWORD_CHANGED event after successful change', async () => {
      // Arrange
      const userId = 1;
      const oldPassword = 'OldPassword123';
      const newPassword = 'NewPassword123';

      vi.mocked(mockApiClient.post).mockResolvedValue({});

      // Act
      await userService.changePassword(userId, oldPassword, newPassword);

      // Assert
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        USER_EVENTS.PASSWORD_CHANGED,
        expect.objectContaining({
          userId
        })
      );
    });
  });
});
```

**Testing Event Listeners in Stores**

**File:** `frontend/user/vue/__tests__/unit/stores/userStore.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUserStore } from '../../../src/stores/userStore';
import type { IEventBus } from '@core/events';
import { USER_EVENTS } from '../../../src/services/UserService';
import { API_EVENTS } from '@core/api';

describe('userStore', () => {
  let mockEventBus: IEventBus;
  let eventHandlers: Map<string, Function>;

  beforeEach(() => {
    setActivePinia(createPinia());
    eventHandlers = new Map();

    // Create mock EventBus that captures event handlers
    mockEventBus = {
      on: vi.fn((event: string, handler: Function) => {
        eventHandlers.set(event, handler);
        return vi.fn(); // Return unsubscribe function
      }),
      once: vi.fn(() => vi.fn()),
      off: vi.fn(),
      emit: vi.fn(),
      emitAsync: vi.fn(),
      clear: vi.fn(),
      listenerCount: vi.fn(() => 0)
    } as any;
  });

  it('should update loading state on PROFILE_UPDATING event', () => {
    // Arrange
    const store = useUserStore();
    store.setupEventListeners(mockEventBus);

    // Act
    const handler = eventHandlers.get(USER_EVENTS.PROFILE_UPDATING);
    handler?.();

    // Assert
    expect(store.loading).toBe(true);
    expect(store.error).toBe(null);
  });

  it('should update currentUser on PROFILE_UPDATED event', () => {
    // Arrange
    const store = useUserStore();
    store.setupEventListeners(mockEventBus);

    const updatedUser = {
      id: 1,
      email: 'john@example.com',
      firstName: 'John',
      lastName: 'Doe',
      role: 'user',
      status: 'active'
    };

    // Act
    const handler = eventHandlers.get(USER_EVENTS.PROFILE_UPDATED);
    handler?.({ user: updatedUser });

    // Assert
    expect(store.currentUser).toEqual(updatedUser);
    expect(store.loading).toBe(false);
  });

  it('should update error state on PROFILE_UPDATE_FAILED event', () => {
    // Arrange
    const store = useUserStore();
    store.setupEventListeners(mockEventBus);

    const errorMessage = 'Failed to update profile';

    // Act
    const handler = eventHandlers.get(USER_EVENTS.PROFILE_UPDATE_FAILED);
    handler?.({ error: errorMessage });

    // Assert
    expect(store.error).toBe(errorMessage);
    expect(store.loading).toBe(false);
  });

  it('should track API requests in progress', () => {
    // Arrange
    const store = useUserStore();
    store.setupEventListeners(mockEventBus);

    // Act - Start request
    const startHandler = eventHandlers.get(API_EVENTS.REQUEST_START);
    startHandler?.({ url: '/api/v1/users/1' });

    // Assert
    expect(store.apiRequestsInProgress).toBe(1);

    // Act - Complete request
    const completeHandler = eventHandlers.get(API_EVENTS.REQUEST_COMPLETE);
    completeHandler?.({ url: '/api/v1/users/1' });

    // Assert
    expect(store.apiRequestsInProgress).toBe(0);
  });

  it('should clear currentUser on UNAUTHORIZED event', () => {
    // Arrange
    const store = useUserStore();
    store.currentUser = {
      id: 1,
      email: 'john@example.com',
      firstName: 'John',
      lastName: 'Doe',
      role: 'user',
      status: 'active'
    };
    store.setupEventListeners(mockEventBus);

    // Act
    const handler = eventHandlers.get(API_EVENTS.UNAUTHORIZED);
    handler?.();

    // Assert
    expect(store.currentUser).toBe(null);
  });

  it('should cleanup event listeners on unsubscribe', () => {
    // Arrange
    const store = useUserStore();
    const unsubscribe = store.setupEventListeners(mockEventBus);

    // Act
    unsubscribe();

    // Assert
    // Each event listener registration returns an unsubscribe function
    // We should have called on() for each event we listen to
    expect(mockEventBus.on).toHaveBeenCalled();
  });
});
```

### 12. Benefits of Event-Driven Architecture

**Decoupling**
- Components don't need direct references to each other
- Services emit events without knowing who listens
- Easy to add new listeners without modifying existing code

**Testability**
- Mock EventBus in tests to verify event emission
- Test event handlers independently
- No need for complex integration tests

**Auditability**
- All state changes emit events with timestamps
- Easy to implement audit logs
- Track user actions across the application

**Real-time Updates**
- Multiple components react to same event
- UI updates automatically when state changes
- WebSocket events can be integrated into the same system

**Maintainability**
- Clear separation of concerns (SRP)
- Easy to add new features by listening to existing events
- Follows Open/Closed Principle (OCP)

**Example Benefits in Action:**

```typescript
// ❌ BAD: Tight coupling
class UserService {
  constructor(
    private api: IApiClient,
    private userStore: UserStore,           // Tight coupling!
    private analyticsStore: AnalyticsStore, // Tight coupling!
    private toastService: ToastService      // Tight coupling!
  ) {}

  async updateProfile(userId: number, data: any) {
    const user = await this.api.put(`/users/${userId}`, data);
    this.userStore.setCurrentUser(user);          // Direct call
    this.analyticsStore.trackProfileUpdate(user); // Direct call
    this.toastService.success('Profile updated'); // Direct call
    return user;
  }
}

// ✅ GOOD: Event-driven, decoupled
class UserService {
  constructor(
    private api: IApiClient,
    private eventBus: IEventBus  // Only EventBus dependency!
  ) {}

  async updateProfile(userId: number, data: any) {
    this.eventBus.emit(USER_EVENTS.PROFILE_UPDATING, { userId, data });

    const user = await this.api.put(`/users/${userId}`, data);

    this.eventBus.emit(USER_EVENTS.PROFILE_UPDATED, { userId, user });

    return user;
  }
}

// Other components listen independently
userStore.setupEventListeners(eventBus);      // Updates UI
analyticsStore.setupEventListeners(eventBus); // Tracks metrics
toastPlugin.setupEventListeners(eventBus);    // Shows notifications
```

**SOLID Principles:**
- **SRP:** Services only handle business logic, emit events
- **OCP:** Add new listeners without modifying services
- **LSP:** IEventBus interface allows substitution (mock for testing)
- **ISP:** Focused event interfaces (USER_EVENTS, API_EVENTS)
- **DI:** EventBus injected via constructor

---

## Definition of Done

- [x] IEventBus interface with type-safe events
- [x] EventBus implementation
- [x] PlatformEvents enum defined
- [x] IValidationService interface
- [x] ValidationService with Zod
- [x] Common validation schemas
- [x] Unit tests with 95%+ coverage
- [x] TypeScript strict mode passing
- [x] ESLint passing
- [x] Documentation

---

## Next Sprint

[Sprint 5: Shared UI Components](./sprint-5-ui-components.md)
