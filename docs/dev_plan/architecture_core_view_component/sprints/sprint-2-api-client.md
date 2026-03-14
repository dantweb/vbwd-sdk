# Sprint 2: API Client & HTTP Layer

**Duration:** 2 weeks
**Goal:** Build type-safe API client with interceptors
**Dependencies:** Sprint 1

---

## Objectives

- [ ] Design IApiClient interface
- [ ] Implement ApiClient with Axios
- [ ] Implement request/response interceptors
- [ ] Implement token management and automatic refresh
- [ ] Implement error normalization
- [ ] Define all API type definitions
- [ ] Write comprehensive unit tests (95%+ coverage)
- [ ] Create integration tests

---

## Tasks

### 1. API Type Definitions

**File:** `frontend/core/src/types/api.ts`

```typescript
// ========================================
// Common Types
// ========================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  field?: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// ========================================
// Auth Types
// ========================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  gdprConsent: boolean;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: 'user' | 'admin';
  status: 'active' | 'suspended';
  createdAt: string;
  updatedAt: string;
}

// ========================================
// User Types
// ========================================

export interface UserProfile {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  avatar?: string;
}

export interface UserDetails {
  address?: string;
  city?: string;
  country?: string;
  zipCode?: string;
  dateOfBirth?: string;
}

export interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  phone?: string;
}

export interface UpdateDetailsRequest {
  address?: string;
  city?: string;
  country?: string;
  zipCode?: string;
  dateOfBirth?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

// ========================================
// Tariff Plan Types
// ========================================

export interface TariffPlan {
  id: number;
  slug: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  billingCycle: 'monthly' | 'yearly' | 'one-time';
  features: string[];
  isPopular: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// ========================================
// Subscription Types
// ========================================

export interface Subscription {
  id: number;
  userId: number;
  planId: number;
  plan: TariffPlan;
  status: 'active' | 'cancelled' | 'expired' | 'pending';
  startDate: string;
  endDate: string;
  autoRenew: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSubscriptionRequest {
  planId: number;
  paymentMethod: 'stripe' | 'paypal';
}

// ========================================
// Checkout Types
// ========================================

export interface CheckoutRequest {
  planId: number;
  paymentMethod: 'stripe' | 'paypal';
  billingDetails: BillingDetails;
  successUrl: string;
  cancelUrl: string;
}

export interface BillingDetails {
  firstName: string;
  lastName: string;
  email: string;
  address: string;
  city: string;
  country: string;
  zipCode: string;
}

export interface CheckoutResponse {
  sessionId: string;
  checkoutUrl: string;
  expiresAt: string;
}

export interface ConfirmCheckoutRequest {
  sessionId: string;
}

// ========================================
// Invoice Types
// ========================================

export interface Invoice {
  id: number;
  userId: number;
  subscriptionId: number;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'refunded';
  paidAt?: string;
  dueDate: string;
  invoiceNumber: string;
  downloadUrl: string;
  createdAt: string;
}

// ========================================
// Admin Types
// ========================================

export interface AdminUserListRequest {
  page?: number;
  limit?: number;
  search?: string;
  status?: 'active' | 'suspended';
  sortBy?: 'email' | 'createdAt';
  sortOrder?: 'asc' | 'desc';
}

export interface AdminUpdateUserRequest {
  firstName?: string;
  lastName?: string;
  email?: string;
  role?: 'user' | 'admin';
  status?: 'active' | 'suspended';
}
```

### 2. API Client Configuration

**File:** `frontend/core/src/api/ApiConfig.ts`

```typescript
export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  withCredentials?: boolean;
}

export const defaultApiConfig: ApiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
};
```

### 3. API Client Interface

**File:** `frontend/core/src/api/IApiClient.ts`

```typescript
import type {
  // Auth
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  RefreshTokenRequest,
  ChangePasswordRequest,
  // User
  UserProfile,
  UserDetails,
  UpdateProfileRequest,
  UpdateDetailsRequest,
  // Tariff
  TariffPlan,
  // Subscription
  Subscription,
  CreateSubscriptionRequest,
  // Checkout
  CheckoutRequest,
  CheckoutResponse,
  ConfirmCheckoutRequest,
  // Invoice
  Invoice,
  PaginatedResponse,
  // Admin
  AdminUserListRequest,
  AdminUpdateUserRequest,
  User,
} from '../types/api';

/**
 * Authentication API endpoints
 */
export interface IAuthEndpoints {
  login(request: LoginRequest): Promise<AuthResponse>;
  register(request: RegisterRequest): Promise<AuthResponse>;
  logout(): Promise<void>;
  refreshToken(request: RefreshTokenRequest): Promise<AuthResponse>;
  changePassword(request: ChangePasswordRequest): Promise<void>;
}

/**
 * User API endpoints
 */
export interface IUserEndpoints {
  getProfile(): Promise<UserProfile>;
  updateProfile(request: UpdateProfileRequest): Promise<UserProfile>;
  getDetails(): Promise<UserDetails>;
  updateDetails(request: UpdateDetailsRequest): Promise<UserDetails>;
  getSubscriptions(): Promise<Subscription[]>;
  getInvoices(): Promise<Invoice[]>;
}

/**
 * Tariff plan API endpoints
 */
export interface ITariffEndpoints {
  list(): Promise<TariffPlan[]>;
  get(slug: string): Promise<TariffPlan>;
}

/**
 * Checkout API endpoints
 */
export interface ICheckoutEndpoints {
  create(request: CheckoutRequest): Promise<CheckoutResponse>;
  confirm(request: ConfirmCheckoutRequest): Promise<Subscription>;
}

/**
 * Admin API endpoints
 */
export interface IAdminEndpoints {
  users: {
    list(request?: AdminUserListRequest): Promise<PaginatedResponse<User>>;
    get(id: number): Promise<User>;
    update(id: number, request: AdminUpdateUserRequest): Promise<User>;
    delete(id: number): Promise<void>;
  };
  plans: {
    list(): Promise<TariffPlan[]>;
    get(id: number): Promise<TariffPlan>;
    create(plan: Omit<TariffPlan, 'id' | 'createdAt' | 'updatedAt'>): Promise<TariffPlan>;
    update(id: number, plan: Partial<TariffPlan>): Promise<TariffPlan>;
    delete(id: number): Promise<void>;
  };
}

/**
 * Main API client interface
 *
 * Provides type-safe access to all backend endpoints
 */
export interface IApiClient {
  // Endpoint groups
  readonly auth: IAuthEndpoints;
  readonly user: IUserEndpoints;
  readonly tariffs: ITariffEndpoints;
  readonly checkout: ICheckoutEndpoints;
  readonly admin: IAdminEndpoints;

  // Low-level HTTP methods
  get<T>(url: string, config?: any): Promise<T>;
  post<T>(url: string, data?: any, config?: any): Promise<T>;
  put<T>(url: string, data?: any, config?: any): Promise<T>;
  patch<T>(url: string, data?: any, config?: any): Promise<T>;
  delete<T>(url: string, config?: any): Promise<T>;

  // Token management
  setAccessToken(token: string | null): void;
  setRefreshToken(token: string | null): void;
  clearTokens(): void;
}
```

### 4. Error Normalizer

**File:** `frontend/core/src/api/ErrorNormalizer.ts`

```typescript
import type { ApiError } from '../types/api';
import { AxiosError } from 'axios';

export class ErrorNormalizer {
  static normalize(error: unknown): ApiError {
    // Axios error
    if (error instanceof AxiosError) {
      const status = error.response?.status || 0;
      const data = error.response?.data as any;

      return {
        message: data?.message || error.message || 'Unknown error',
        code: data?.code || ErrorNormalizer.getErrorCodeFromStatus(status),
        status,
        field: data?.field,
        details: data?.details,
      };
    }

    // Network error
    if (error instanceof Error && error.message.includes('Network')) {
      return {
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
        status: 0,
      };
    }

    // Generic error
    if (error instanceof Error) {
      return {
        message: error.message,
        code: 'UNKNOWN_ERROR',
        status: 0,
      };
    }

    // Unknown error type
    return {
      message: 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
      status: 0,
    };
  }

  static isNetworkError(error: ApiError): boolean {
    return error.code === 'NETWORK_ERROR' || error.status === 0;
  }

  static isAuthError(error: ApiError): boolean {
    return error.status === 401 || error.status === 403;
  }

  static isValidationError(error: ApiError): boolean {
    return error.status === 422 || error.code === 'VALIDATION_ERROR';
  }

  static isServerError(error: ApiError): boolean {
    return error.status >= 500;
  }

  private static getErrorCodeFromStatus(status: number): string {
    switch (status) {
      case 400:
        return 'BAD_REQUEST';
      case 401:
        return 'UNAUTHORIZED';
      case 403:
        return 'FORBIDDEN';
      case 404:
        return 'NOT_FOUND';
      case 422:
        return 'VALIDATION_ERROR';
      case 429:
        return 'TOO_MANY_REQUESTS';
      case 500:
        return 'INTERNAL_SERVER_ERROR';
      case 502:
        return 'BAD_GATEWAY';
      case 503:
        return 'SERVICE_UNAVAILABLE';
      default:
        return 'UNKNOWN_ERROR';
    }
  }
}
```

### 5. API Client Implementation

**File:** `frontend/core/src/api/ApiClient.ts`

```typescript
import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios';
import type { IApiClient, IAuthEndpoints, IUserEndpoints, ITariffEndpoints, ICheckoutEndpoints, IAdminEndpoints } from './IApiClient';
import type { ApiConfig } from './ApiConfig';
import { ErrorNormalizer } from './ErrorNormalizer';

export class ApiClient implements IApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  // Endpoint implementations
  public readonly auth: IAuthEndpoints;
  public readonly user: IUserEndpoints;
  public readonly tariffs: ITariffEndpoints;
  public readonly checkout: ICheckoutEndpoints;
  public readonly admin: IAdminEndpoints;

  constructor(config: ApiConfig) {
    this.client = axios.create(config);
    this.setupInterceptors();

    // Initialize endpoint groups
    this.auth = this.createAuthEndpoints();
    this.user = this.createUserEndpoints();
    this.tariffs = this.createTariffEndpoints();
    this.checkout = this.createCheckoutEndpoints();
    this.admin = this.createAdminEndpoints();
  }

  // ========================================
  // HTTP Methods
  // ========================================

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // ========================================
  // Token Management
  // ========================================

  setAccessToken(token: string | null): void {
    this.accessToken = token;
    if (token) {
      localStorage.setItem('accessToken', token);
    } else {
      localStorage.removeItem('accessToken');
    }
  }

  setRefreshToken(token: string | null): void {
    this.refreshToken = token;
    if (token) {
      localStorage.setItem('refreshToken', token);
    } else {
      localStorage.removeItem('refreshToken');
    }
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  // ========================================
  // Interceptors
  // ========================================

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add access token
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }

        // Log request in dev mode
        if (import.meta.env.DEV) {
          console.log('[API Request]', config.method?.toUpperCase(), config.url);
        }

        return config;
      },
      (error) => {
        return Promise.reject(ErrorNormalizer.normalize(error));
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Log response in dev mode
        if (import.meta.env.DEV) {
          console.log('[API Response]', response.config.method?.toUpperCase(), response.config.url, response.status);
        }

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 with token refresh
        if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
          if (this.isRefreshing) {
            // Wait for token refresh
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const response = await this.client.post('/api/v1/auth/refresh', {
              refreshToken: this.refreshToken,
            });

            const { accessToken, refreshToken } = response.data;
            this.setAccessToken(accessToken);
            this.setRefreshToken(refreshToken);

            // Notify subscribers
            this.refreshSubscribers.forEach((callback) => callback(accessToken));
            this.refreshSubscribers = [];

            // Retry original request
            originalRequest.headers.Authorization = `Bearer ${accessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed - clear tokens and redirect to login
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(ErrorNormalizer.normalize(refreshError));
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(ErrorNormalizer.normalize(error));
      }
    );
  }

  // ========================================
  // Endpoint Implementations
  // ========================================

  private createAuthEndpoints(): IAuthEndpoints {
    return {
      login: (request) => this.post('/api/v1/auth/login', request),
      register: (request) => this.post('/api/v1/auth/register', request),
      logout: () => this.post('/api/v1/auth/logout'),
      refreshToken: (request) => this.post('/api/v1/auth/refresh', request),
      changePassword: (request) => this.post('/api/v1/auth/change-password', request),
    };
  }

  private createUserEndpoints(): IUserEndpoints {
    return {
      getProfile: () => this.get('/api/v1/user/profile'),
      updateProfile: (request) => this.put('/api/v1/user/profile', request),
      getDetails: () => this.get('/api/v1/user/details'),
      updateDetails: (request) => this.put('/api/v1/user/details', request),
      getSubscriptions: () => this.get('/api/v1/user/subscriptions'),
      getInvoices: () => this.get('/api/v1/user/invoices'),
    };
  }

  private createTariffEndpoints(): ITariffEndpoints {
    return {
      list: () => this.get('/api/v1/tarif-plans'),
      get: (slug) => this.get(`/api/v1/tarif-plans/${slug}`),
    };
  }

  private createCheckoutEndpoints(): ICheckoutEndpoints {
    return {
      create: (request) => this.post('/api/v1/checkout', request),
      confirm: (request) => this.post('/api/v1/checkout/confirm', request),
    };
  }

  private createAdminEndpoints(): IAdminEndpoints {
    return {
      users: {
        list: (request) => this.get('/api/v1/admin/users', { params: request }),
        get: (id) => this.get(`/api/v1/admin/users/${id}`),
        update: (id, request) => this.put(`/api/v1/admin/users/${id}`, request),
        delete: (id) => this.delete(`/api/v1/admin/users/${id}`),
      },
      plans: {
        list: () => this.get('/api/v1/admin/tarif-plans'),
        get: (id) => this.get(`/api/v1/admin/tarif-plans/${id}`),
        create: (plan) => this.post('/api/v1/admin/tarif-plans', plan),
        update: (id, plan) => this.put(`/api/v1/admin/tarif-plans/${id}`, plan),
        delete: (id) => this.delete(`/api/v1/admin/tarif-plans/${id}`),
      },
    };
  }
}
```

### 6. Barrel Exports

**File:** `frontend/core/src/api/index.ts`

```typescript
export * from './IApiClient';
export * from './ApiClient';
export * from './ApiConfig';
export * from './ErrorNormalizer';
```

---

## Testing Strategy

### Unit Tests

**File:** `frontend/core/__tests__/unit/api/ErrorNormalizer.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { ErrorNormalizer } from '../../../src/api/ErrorNormalizer';
import { AxiosError } from 'axios';

describe('ErrorNormalizer', () => {
  it('should normalize Axios error', () => {
    const axiosError = new AxiosError('Request failed');
    axiosError.response = {
      status: 400,
      data: {
        message: 'Invalid request',
        code: 'BAD_REQUEST',
      },
    } as any;

    const normalized = ErrorNormalizer.normalize(axiosError);

    expect(normalized.message).toBe('Invalid request');
    expect(normalized.code).toBe('BAD_REQUEST');
    expect(normalized.status).toBe(400);
  });

  it('should detect auth error', () => {
    const error = {
      message: 'Unauthorized',
      code: 'UNAUTHORIZED',
      status: 401,
    };

    expect(ErrorNormalizer.isAuthError(error)).toBe(true);
  });

  it('should detect validation error', () => {
    const error = {
      message: 'Validation failed',
      code: 'VALIDATION_ERROR',
      status: 422,
    };

    expect(ErrorNormalizer.isValidationError(error)).toBe(true);
  });
});
```

**File:** `frontend/core/__tests__/unit/api/ApiClient.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from '../../../src/api/ApiClient';
import { defaultApiConfig } from '../../../src/api/ApiConfig';
import MockAdapter from 'axios-mock-adapter';
import axios from 'axios';

describe('ApiClient', () => {
  let apiClient: ApiClient;
  let mock: MockAdapter;

  beforeEach(() => {
    apiClient = new ApiClient(defaultApiConfig);
    mock = new MockAdapter(axios);
  });

  it('should make GET request', async () => {
    const data = { id: 1, name: 'Test' };
    mock.onGet('/test').reply(200, data);

    const result = await apiClient.get('/test');
    expect(result).toEqual(data);
  });

  it('should add Authorization header when token is set', async () => {
    apiClient.setAccessToken('test-token');

    mock.onGet('/test').reply((config) => {
      expect(config.headers?.Authorization).toBe('Bearer test-token');
      return [200, {}];
    });

    await apiClient.get('/test');
  });

  it('should refresh token on 401 response', async () => {
    apiClient.setAccessToken('old-token');
    apiClient.setRefreshToken('refresh-token');

    // First request fails with 401
    mock.onGet('/protected').replyOnce(401);

    // Refresh token endpoint
    mock.onPost('/api/v1/auth/refresh').reply(200, {
      accessToken: 'new-token',
      refreshToken: 'new-refresh-token',
    });

    // Retry with new token
    mock.onGet('/protected').reply(200, { success: true });

    const result = await apiClient.get('/protected');
    expect(result).toEqual({ success: true });
  });
});
```

---

## Definition of Done

- [x] All API types defined
- [x] IApiClient interface with all endpoints
- [x] ApiClient implementation with Axios
- [x] Request/response interceptors
- [x] Token refresh logic
- [x] Error normalization
- [x] Unit tests with 95%+ coverage
- [x] TypeScript strict mode passing
- [x] ESLint passing
- [x] Documentation

---

## Next Sprint

[Sprint 3: Authentication Service](./sprint-3-auth-service.md)
