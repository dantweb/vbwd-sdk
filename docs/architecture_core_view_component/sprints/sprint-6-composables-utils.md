# Sprint 6: Composables & Utilities

**Duration:** 1 week
**Goal:** Build shared composables and utilities
**Dependencies:** Sprint 2, Sprint 3, Sprint 4

---

## Objectives

- [ ] Create useApi composable
- [ ] Create useAuth composable
- [ ] Create useForm composable
- [ ] Create useNotification composable
- [ ] Build format utilities (date, currency, number)
- [ ] Build storage utilities (localStorage wrapper)
- [ ] Write unit tests (90%+ coverage)

---

## Composables

### 1. useApi Composable

**File:** `frontend/core/src/composables/useApi.ts`

```typescript
import { ref, type Ref } from 'vue';
import { useApiClient } from './useApiClient';
import type { ApiError } from '../types/api';

export interface UseApiReturn<T> {
  data: Ref<T | null>;
  error: Ref<ApiError | null>;
  loading: Ref<boolean>;
  execute: () => Promise<void>;
  reset: () => void;
}

export function useApi<T>(
  apiCall: () => Promise<T>,
  options: { immediate?: boolean } = {}
): UseApiReturn<T> {
  const data = ref<T | null>(null);
  const error = ref<ApiError | null>(null);
  const loading = ref(false);

  async function execute(): Promise<void> {
    loading.value = true;
    error.value = null;

    try {
      data.value = await apiCall();
    } catch (err) {
      error.value = err as ApiError;
    } finally {
      loading.value = false;
    }
  }

  function reset(): void {
    data.value = null;
    error.value = null;
    loading.value = false;
  }

  if (options.immediate) {
    execute();
  }

  return {
    data: data as Ref<T | null>,
    error,
    loading,
    execute,
    reset,
  };
}
```

### 2. useAuth Composable

**File:** `frontend/core/src/composables/useAuth.ts`

```typescript
import { computed } from 'vue';
import { useAuthStore } from '../auth/authStore';

export function useAuth() {
  const authStore = useAuthStore();

  const user = computed(() => authStore.user);
  const isAuthenticated = computed(() => authStore.isAuthenticated);
  const isAdmin = computed(() => authStore.isAdmin);
  const loading = computed(() => authStore.loading);

  return {
    user,
    isAuthenticated,
    isAdmin,
    loading,
    login: authStore.login,
    register: authStore.register,
    logout: authStore.logout,
    hasRole: authStore.hasRole,
    hasAnyRole: authStore.hasAnyRole,
  };
}
```

### 3. useForm Composable

**File:** `frontend/core/src/composables/useForm.ts`

```typescript
import { ref, computed, type Ref } from 'vue';
import type { z } from 'zod';
import { useValidationService } from './useValidationService';
import type { ValidationError } from '../validation';

export interface UseFormReturn<T> {
  values: Ref<T>;
  errors: Ref<Record<string, string>>;
  isValid: Ref<boolean>;
  isSubmitting: Ref<boolean>;
  setValues: (newValues: Partial<T>) => void;
  setFieldValue: (field: keyof T, value: any) => void;
  validate: () => boolean;
  handleSubmit: (onSubmit: (values: T) => Promise<void>) => Promise<void>;
  reset: () => void;
}

export function useForm<T extends Record<string, any>>(
  initialValues: T,
  schema: z.ZodSchema<T>
): UseFormReturn<T> {
  const validation = useValidationService();

  const values = ref<T>({ ...initialValues }) as Ref<T>;
  const errors = ref<Record<string, string>>({});
  const isSubmitting = ref(false);

  const isValid = computed(() => Object.keys(errors.value).length === 0);

  function setValues(newValues: Partial<T>): void {
    values.value = { ...values.value, ...newValues };
    validate();
  }

  function setFieldValue(field: keyof T, value: any): void {
    values.value[field] = value;
    validateField(field);
  }

  function validate(): boolean {
    const result = validation.validate(schema, values.value);

    if (result.success) {
      errors.value = {};
      return true;
    }

    errors.value = result.errors!.reduce(
      (acc, err) => {
        acc[err.field] = err.message;
        return acc;
      },
      {} as Record<string, string>
    );

    return false;
  }

  function validateField(field: keyof T): void {
    try {
      schema.shape[field].parse(values.value[field]);
      delete errors.value[field as string];
    } catch (err: any) {
      errors.value[field as string] = err.errors[0]?.message || 'Invalid value';
    }
  }

  async function handleSubmit(onSubmit: (values: T) => Promise<void>): Promise<void> {
    if (!validate()) return;

    isSubmitting.value = true;
    try {
      await onSubmit(values.value);
    } finally {
      isSubmitting.value = false;
    }
  }

  function reset(): void {
    values.value = { ...initialValues };
    errors.value = {};
    isSubmitting.value = false;
  }

  return {
    values,
    errors,
    isValid,
    isSubmitting,
    setValues,
    setFieldValue,
    validate,
    handleSubmit,
    reset,
  };
}
```

### 4. useNotification Composable

**File:** `frontend/core/src/composables/useNotification.ts`

```typescript
import { useEventBus } from './useEventBus';
import { PlatformEvents } from '../types/events';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface NotificationOptions {
  message: string;
  type?: NotificationType;
  duration?: number;
}

export function useNotification() {
  const eventBus = useEventBus();

  function show(options: NotificationOptions): void {
    eventBus.emit(PlatformEvents.NOTIFICATION_SHOW, {
      message: options.message,
      type: options.type || 'info',
    });
  }

  function success(message: string): void {
    show({ message, type: 'success' });
  }

  function error(message: string): void {
    show({ message, type: 'error' });
  }

  function warning(message: string): void {
    show({ message, type: 'warning' });
  }

  function info(message: string): void {
    show({ message, type: 'info' });
  }

  return {
    show,
    success,
    error,
    warning,
    info,
  };
}
```

---

## Utilities

### 1. Format Utilities

**File:** `frontend/core/src/utils/format.ts`

```typescript
/**
 * Format date to locale string
 */
export function formatDate(date: Date | string, locale = 'en-US'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString(locale);
}

/**
 * Format date with time
 */
export function formatDateTime(date: Date | string, locale = 'en-US'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString(locale);
}

/**
 * Format currency
 */
export function formatCurrency(
  amount: number,
  currency = 'USD',
  locale = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number, locale = 'en-US'): string {
  return new Intl.NumberFormat(locale).format(num);
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Truncate string
 */
export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return `${str.slice(0, length)}...`;
}
```

### 2. Storage Utilities

**File:** `frontend/core/src/utils/storage.ts`

```typescript
/**
 * Type-safe localStorage wrapper
 */
export class Storage {
  private prefix: string;

  constructor(prefix = 'vbwd_') {
    this.prefix = prefix;
  }

  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(this.prefix + key);
      if (item === null) return defaultValue ?? null;
      return JSON.parse(item) as T;
    } catch {
      return defaultValue ?? null;
    }
  }

  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(this.prefix + key, JSON.stringify(value));
    } catch (error) {
      console.error('Storage.set error:', error);
    }
  }

  remove(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }

  clear(): void {
    const keys = Object.keys(localStorage);
    keys.forEach((key) => {
      if (key.startsWith(this.prefix)) {
        localStorage.removeItem(key);
      }
    });
  }

  has(key: string): boolean {
    return localStorage.getItem(this.prefix + key) !== null;
  }
}

export const storage = new Storage();
```

---

## Barrel Exports

**File:** `frontend/core/src/composables/index.ts`

```typescript
export * from './useApi';
export * from './useAuth';
export * from './useForm';
export * from './useNotification';
```

**File:** `frontend/core/src/utils/index.ts`

```typescript
export * from './format';
export * from './storage';
```

---

## Definition of Done

- [x] useApi, useAuth, useForm, useNotification composables
- [x] Format utilities (date, currency, number, file size)
- [x] Storage utilities (type-safe localStorage wrapper)
- [x] Unit tests (90%+ coverage)
- [x] TypeScript strict mode passing
- [x] ESLint passing
- [x] JSDoc documentation

---

## Next Sprint

[Sprint 7: Access Control System](./sprint-7-access-control.md)
