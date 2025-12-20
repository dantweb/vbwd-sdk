# Sprint 1: API Client SDK & Authentication

**Goal:** Build type-safe API client, authentication service, and event bus for plugin communication.

---

## Objectives

- [ ] API Client with TypeScript interfaces for all endpoints
- [ ] Axios interceptors for auth token management
- [ ] Authentication service with JWT
- [ ] Event Bus for plugin communication
- [ ] Validation service with Zod schemas
- [ ] LocalStorage/SessionStorage abstraction
- [ ] Error handling and normalization
- [ ] Unit tests for all services (90%+ coverage)

---

## Tasks

### 1.1 API Types Definition (TDD)

**File:** `src/core/api/types/auth.types.ts`

```typescript
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface User {
  id: number;
  email: string;
  role: 'user' | 'admin';
  status: 'pending' | 'active' | 'suspended' | 'deleted';
  createdAt: string;
}

export interface TokenRefreshResponse {
  accessToken: string;
  refreshToken: string;
}
```

**File:** `src/core/api/types/user.types.ts`

```typescript
export interface UserProfile {
  id: number;
  email: string;
  role: string;
  status: string;
}

export interface UserDetails {
  firstName: string;
  lastName: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  postalCode: string;
  country: string;
  phone: string;
}

export interface Subscription {
  id: number;
  userId: number;
  tarifPlanId: number;
  status: 'active' | 'inactive' | 'cancelled' | 'expired';
  startedAt: string;
  expiresAt: string;
  plan: TariffPlan;
}

export interface TariffPlan {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: number;
  currency: string;
  billingPeriod: 'monthly' | 'quarterly' | 'yearly' | 'one_time';
  features: string[];
  isActive: boolean;
}

export interface Invoice {
  id: number;
  invoiceNumber: string;
  amount: number;
  currency: string;
  status: 'invoiced' | 'paid' | 'expired' | 'cancelled';
  paymentMethod: 'paypal' | 'stripe' | 'manual';
  invoicedAt: string;
  paidAt?: string;
}
```

**File:** `src/core/api/types/checkout.types.ts`

```typescript
export interface CheckoutRequest {
  tarifPlanId: number;
  paymentMethod: 'paypal' | 'stripe';
  userDetails?: Partial<UserDetails>;
}

export interface CheckoutSession {
  sessionId: string;
  checkoutUrl: string;
  expiresAt: string;
}

export interface CheckoutConfirmation {
  subscriptionId: number;
  invoiceId: number;
  status: 'success' | 'pending' | 'failed';
}
```

---

### 1.2 API Client Interface

**File:** `src/core/api/IApiClient.ts`

```typescript
import type * as AuthTypes from './types/auth.types';
import type * as UserTypes from './types/user.types';
import type * as CheckoutTypes from './types/checkout.types';
import { AxiosRequestConfig } from 'axios';

export interface IApiClient {
  // Auth endpoints
  auth: {
    login(
      email: string,
      password: string
    ): Promise<AuthTypes.AuthResponse>;
    register(
      data: AuthTypes.RegisterRequest
    ): Promise<AuthTypes.AuthResponse>;
    logout(): Promise<void>;
    refreshToken(): Promise<AuthTypes.TokenRefreshResponse>;
  };

  // User endpoints
  user: {
    getProfile(): Promise<UserTypes.UserProfile>;
    updateProfile(
      data: Partial<UserTypes.UserProfile>
    ): Promise<UserTypes.UserProfile>;
    getDetails(): Promise<UserTypes.UserDetails>;
    updateDetails(
      data: Partial<UserTypes.UserDetails>
    ): Promise<UserTypes.UserDetails>;
    getSubscriptions(): Promise<UserTypes.Subscription[]>;
    getInvoices(): Promise<UserTypes.Invoice[]>;
  };

  // Tariff plans endpoints
  tariffs: {
    list(): Promise<UserTypes.TariffPlan[]>;
    get(slug: string): Promise<UserTypes.TariffPlan>;
  };

  // Checkout endpoints
  checkout: {
    create(
      data: CheckoutTypes.CheckoutRequest
    ): Promise<CheckoutTypes.CheckoutSession>;
    confirm(
      sessionId: string
    ): Promise<CheckoutTypes.CheckoutConfirmation>;
  };

  // Generic methods
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T>;
}
```

---

### 1.3 API Client Implementation (with tests)

**Test File:** `src/core/api/__tests__/ApiClient.spec.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from '../ApiClient';
import axios from 'axios';

vi.mock('axios');

describe('ApiClient', () => {
  let apiClient: ApiClient;

  beforeEach(() => {
    apiClient = new ApiClient('http://localhost:5000/api/v1');
  });

  describe('auth', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        data: {
          accessToken: 'token123',
          refreshToken: 'refresh123',
          user: { id: 1, email: 'test@test.com', role: 'user' },
        },
      };

      vi.mocked(axios.post).mockResolvedValueOnce(mockResponse);

      const result = await apiClient.auth.login(
        'test@test.com',
        'password'
      );

      expect(result).toEqual(mockResponse.data);
      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:5000/api/v1/auth/login',
        { email: 'test@test.com', password: 'password' },
        expect.any(Object)
      );
    });
  });

  describe('tariffs', () => {
    it('should fetch tariff plans', async () => {
      const mockPlans = [
        { id: 1, name: 'Basic', price: 9.99 },
        { id: 2, name: 'Premium', price: 19.99 },
      ];

      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockPlans });

      const result = await apiClient.tariffs.list();

      expect(result).toEqual(mockPlans);
    });
  });
});
```

**Implementation:** `src/core/api/ApiClient.ts`

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { IApiClient } from './IApiClient';
import type * as AuthTypes from './types/auth.types';
import type * as UserTypes from './types/user.types';
import type * as CheckoutTypes from './types/checkout.types';

export class ApiClient implements IApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor: Add auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor: Handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const { accessToken } = await this.auth.refreshToken();
            localStorage.setItem('accessToken', accessToken);

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${accessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth
  auth = {
    login: async (
      email: string,
      password: string
    ): Promise<AuthTypes.AuthResponse> => {
      const { data } = await this.client.post('/auth/login', {
        email,
        password,
      });
      return data;
    },

    register: async (
      reqData: AuthTypes.RegisterRequest
    ): Promise<AuthTypes.AuthResponse> => {
      const { data } = await this.client.post('/auth/register', reqData);
      return data;
    },

    logout: async (): Promise<void> => {
      await this.client.post('/auth/logout');
    },

    refreshToken: async (): Promise<AuthTypes.TokenRefreshResponse> => {
      const refreshToken = localStorage.getItem('refreshToken');
      const { data } = await this.client.post('/auth/refresh', {
        refreshToken,
      });
      return data;
    },
  };

  // User
  user = {
    getProfile: async (): Promise<UserTypes.UserProfile> => {
      const { data } = await this.client.get('/user/profile');
      return data;
    },

    updateProfile: async (
      profileData: Partial<UserTypes.UserProfile>
    ): Promise<UserTypes.UserProfile> => {
      const { data } = await this.client.put('/user/profile', profileData);
      return data;
    },

    getDetails: async (): Promise<UserTypes.UserDetails> => {
      const { data } = await this.client.get('/user/details');
      return data;
    },

    updateDetails: async (
      details: Partial<UserTypes.UserDetails>
    ): Promise<UserTypes.UserDetails> => {
      const { data} = await this.client.put('/user/details', details);
      return data;
    },

    getSubscriptions: async (): Promise<UserTypes.Subscription[]> => {
      const { data } = await this.client.get('/user/subscriptions');
      return data;
    },

    getInvoices: async (): Promise<UserTypes.Invoice[]> => {
      const { data } = await this.client.get('/user/invoices');
      return data;
    },
  };

  // Tariffs
  tariffs = {
    list: async (): Promise<UserTypes.TariffPlan[]> => {
      const { data } = await this.client.get('/tarif-plans');
      return data;
    },

    get: async (slug: string): Promise<UserTypes.TariffPlan> => {
      const { data } = await this.client.get(`/tarif-plans/${slug}`);
      return data;
    },
  };

  // Checkout
  checkout = {
    create: async (
      checkoutData: CheckoutTypes.CheckoutRequest
    ): Promise<CheckoutTypes.CheckoutSession> => {
      const { data } = await this.client.post('/checkout/create', checkoutData);
      return data;
    },

    confirm: async (
      sessionId: string
    ): Promise<CheckoutTypes.CheckoutConfirmation> => {
      const { data } = await this.client.post('/checkout/confirm', {
        sessionId,
      });
      return data;
    },
  };

  // Generic methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await this.client.get<T>(url, config);
    return data;
  }

  async post<T>(
    url: string,
    postData?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const { data } = await this.client.post<T>(url, postData, config);
    return data;
  }

  async put<T>(
    url: string,
    putData?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const { data } = await this.client.put<T>(url, putData, config);
    return data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await this.client.delete<T>(url, config);
    return data;
  }
}
```

---

### 1.4 Authentication Service

**File:** `src/core/auth/IAuthService.ts`

```typescript
import { ComputedRef } from 'vue';
import { User, RegisterRequest } from '../api/types/auth.types';

export interface IAuthService {
  // State
  isAuthenticated: ComputedRef<boolean>;
  currentUser: ComputedRef<User | null>;

  // Methods
  login(email: string, password: string): Promise<void>;
  register(data: RegisterRequest): Promise<void>;
  logout(): Promise<void>;
  refreshSession(): Promise<void>;

  // Token management
  getAccessToken(): string | null;
  setTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;

  // Permissions
  hasPermission(permission: string): boolean;
  hasRole(role: string): boolean;
  canAccessPlan(planSlug: string): boolean;
}
```

**File:** `src/core/auth/AuthService.ts` (Implementation with Pinia store)

```typescript
import { computed } from 'vue';
import { defineStore } from 'pinia';
import { IApiClient } from '../api/IApiClient';
import { IAuthService } from './IAuthService';
import { User, RegisterRequest } from '../api/types/auth.types';

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<User | null>(null);
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);

  const isAuthenticated = computed(() => !!accessToken.value);

  return {
    currentUser,
    accessToken,
    refreshToken,
    isAuthenticated,
  };
});

export class AuthService implements IAuthService {
  private store = useAuthStore();

  constructor(private apiClient: IApiClient) {
    this.loadTokensFromStorage();
  }

  get isAuthenticated() {
    return computed(() => this.store.isAuthenticated);
  }

  get currentUser() {
    return computed(() => this.store.currentUser);
  }

  async login(email: string, password: string): Promise<void> {
    const response = await this.apiClient.auth.login(email, password);

    this.setTokens(response.accessToken, response.refreshToken);
    this.store.currentUser = response.user;
  }

  async register(data: RegisterRequest): Promise<void> {
    const response = await this.apiClient.auth.register(data);

    this.setTokens(response.accessToken, response.refreshToken);
    this.store.currentUser = response.user;
  }

  async logout(): Promise<void> {
    await this.apiClient.auth.logout();
    this.clearTokens();
    this.store.currentUser = null;
  }

  async refreshSession(): Promise<void> {
    const response = await this.apiClient.auth.refreshToken();
    this.setTokens(response.accessToken, response.refreshToken);
  }

  getAccessToken(): string | null {
    return this.store.accessToken;
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.store.accessToken = accessToken;
    this.store.refreshToken = refreshToken;
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  }

  clearTokens(): void {
    this.store.accessToken = null;
    this.store.refreshToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  private loadTokensFromStorage(): void {
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');

    if (accessToken && refreshToken) {
      this.store.accessToken = accessToken;
      this.store.refreshToken = refreshToken;
    }
  }

  hasPermission(permission: string): boolean {
    // TODO: Implement permission checking
    return true;
  }

  hasRole(role: string): boolean {
    return this.store.currentUser?.role === role;
  }

  canAccessPlan(planSlug: string): boolean {
    // TODO: Check user's active subscriptions
    return true;
  }
}
```

---

### 1.5 Event Bus

**File:** `src/core/events/EventBus.ts`

```typescript
import { IEventBus } from './IEventBus';

export class EventBus implements IEventBus {
  private listeners: Map<string, Set<Function>> = new Map();

  emit<T = any>(event: string, payload?: T): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(payload));
    }
  }

  on<T = any>(event: string, handler: (payload: T) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }

    this.listeners.get(event)!.add(handler);

    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  once<T = any>(event: string, handler: (payload: T) => void): void {
    const wrapper = (payload: T) => {
      handler(payload);
      this.off(event, wrapper);
    };
    this.on(event, wrapper);
  }

  off(event: string, handler?: Function): void {
    if (!handler) {
      this.listeners.delete(event);
    } else {
      const handlers = this.listeners.get(event);
      if (handlers) {
        handlers.delete(handler);
      }
    }
  }
}

export enum PlatformEvents {
  USER_LOGGED_IN = 'user:logged-in',
  USER_LOGGED_OUT = 'user:logged-out',
  SUBSCRIPTION_CHANGED = 'subscription:changed',
  PAYMENT_COMPLETED = 'payment:completed',
  ROUTE_CHANGED = 'route:changed',
}
```

---

### 1.6 Update Platform SDK

**File:** `src/core/sdk/PlatformSDK.ts` (Updated)

```typescript
import { Router } from 'vue-router';
import { Component, App } from 'vue';
import { IApiClient } from '../api/IApiClient';
import { IAuthService } from '../auth/IAuthService';
import { IEventBus } from '../events/IEventBus';
import { ApiClient } from '../api/ApiClient';
import { AuthService } from '../auth/AuthService';
import { EventBus } from '../events/EventBus';

export interface PlatformSDK {
  apiClient: IApiClient;
  authService: IAuthService;
  eventBus: IEventBus;
  router: Router;
  registerGlobalComponent(name: string, component: Component): void;
  app: App;
}

export function createPlatformSDK(app: App, router: Router): PlatformSDK {
  const apiClient = new ApiClient(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
  );
  const authService = new AuthService(apiClient);
  const eventBus = new EventBus();

  // Make services available globally via provide/inject
  app.provide('apiClient', apiClient);
  app.provide('authService', authService);
  app.provide('eventBus', eventBus);

  return {
    apiClient,
    authService,
    eventBus,
    router,
    app,
    registerGlobalComponent(name: string, component: Component) {
      app.component(name, component);
    },
  };
}
```

---

## Testing Checklist

- [ ] All API client methods have unit tests
- [ ] Auth service can login/register/logout
- [ ] Tokens are persisted to localStorage
- [ ] Token refresh works on 401 responses
- [ ] Event bus can emit and listen to events
- [ ] All TypeScript types are correctly defined
- [ ] 90%+ code coverage on core services

---

## Definition of Done

- [ ] API Client fully implemented with all endpoints
- [ ] Authentication service with JWT management
- [ ] Event bus for plugin communication
- [ ] All services have comprehensive unit tests
- [ ] PlatformSDK provides all services to plugins
- [ ] Documentation updated
- [ ] All tests pass

---

## Next Sprint

**Sprint 2:** Wizard Plugin - File Upload & Validation
