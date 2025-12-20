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
