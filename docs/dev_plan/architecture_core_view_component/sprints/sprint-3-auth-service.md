# Sprint 3: Authentication Service

**Duration:** 1 week
**Goal:** Build authentication and session management
**Dependencies:** Sprint 2

---

## Objectives

- [ ] Design IAuthService interface
- [ ] Implement AuthService with JWT management
- [ ] Create authStore (Pinia)
- [ ] Implement session persistence
- [ ] Implement role checking
- [ ] Write comprehensive unit tests (95%+ coverage)

---

## Tasks

### 1. Auth Types

**File:** `frontend/core/src/types/auth.ts`

```typescript
export interface AuthUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: 'user' | 'admin';
  status: 'active' | 'suspended';
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
}
```

### 2. IAuthService Interface

**File:** `frontend/core/src/auth/IAuthService.ts`

```typescript
import type { LoginRequest, RegisterRequest, AuthResponse, ChangePasswordRequest } from '../types/api';
import type { AuthUser } from '../types/auth';

export interface IAuthService {
  // Authentication
  login(request: LoginRequest): Promise<AuthResponse>;
  register(request: RegisterRequest): Promise<AuthResponse>;
  logout(): Promise<void>;

  // Session management
  isAuthenticated(): boolean;
  getCurrentUser(): AuthUser | null;
  getAccessToken(): string | null;
  getRefreshToken(): string | null;

  // Token management
  setTokens(accessToken: string, refreshToken: string, expiresIn: number): void;
  clearTokens(): void;
  isTokenExpired(): boolean;

  // Authorization
  hasRole(role: string): boolean;
  hasAnyRole(roles: string[]): boolean;
  isAdmin(): boolean;

  // Session persistence
  restoreSession(): Promise<boolean>;
  saveSession(): void;
}
```

### 3. AuthService Implementation

**File:** `frontend/core/src/auth/AuthService.ts`

```typescript
import type { IAuthService } from './IAuthService';
import type { IApiClient } from '../api';
import type { LoginRequest, RegisterRequest, AuthResponse, ChangePasswordRequest } from '../types/api';
import type { AuthUser, AuthTokens } from '../types/auth';

export class AuthService implements IAuthService {
  private user: AuthUser | null = null;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private expiresAt: number | null = null;

  constructor(private readonly apiClient: IApiClient) {
    this.restoreSession();
  }

  // ========================================
  // Authentication
  // ========================================

  async login(request: LoginRequest): Promise<AuthResponse> {
    const response = await this.apiClient.auth.login(request);
    this.handleAuthResponse(response);
    return response;
  }

  async register(request: RegisterRequest): Promise<AuthResponse> {
    const response = await this.apiClient.auth.register(request);
    this.handleAuthResponse(response);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.apiClient.auth.logout();
    } finally {
      this.clearTokens();
    }
  }

  // ========================================
  // Session Management
  // ========================================

  isAuthenticated(): boolean {
    return this.user !== null && this.accessToken !== null && !this.isTokenExpired();
  }

  getCurrentUser(): AuthUser | null {
    return this.user;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  // ========================================
  // Token Management
  // ========================================

  setTokens(accessToken: string, refreshToken: string, expiresIn: number): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.expiresAt = Date.now() + expiresIn * 1000;

    // Update API client tokens
    this.apiClient.setAccessToken(accessToken);
    this.apiClient.setRefreshToken(refreshToken);

    this.saveSession();
  }

  clearTokens(): void {
    this.user = null;
    this.accessToken = null;
    this.refreshToken = null;
    this.expiresAt = null;

    // Clear API client tokens
    this.apiClient.clearTokens();

    // Clear localStorage
    localStorage.removeItem('auth:user');
    localStorage.removeItem('auth:accessToken');
    localStorage.removeItem('auth:refreshToken');
    localStorage.removeItem('auth:expiresAt');
  }

  isTokenExpired(): boolean {
    if (!this.expiresAt) return true;
    return Date.now() >= this.expiresAt;
  }

  // ========================================
  // Authorization
  // ========================================

  hasRole(role: string): boolean {
    return this.user?.role === role;
  }

  hasAnyRole(roles: string[]): boolean {
    return roles.some((role) => this.hasRole(role));
  }

  isAdmin(): boolean {
    return this.hasRole('admin');
  }

  // ========================================
  // Session Persistence
  // ========================================

  async restoreSession(): Promise<boolean> {
    try {
      const userJson = localStorage.getItem('auth:user');
      const accessToken = localStorage.getItem('auth:accessToken');
      const refreshToken = localStorage.getItem('auth:refreshToken');
      const expiresAt = localStorage.getItem('auth:expiresAt');

      if (!userJson || !accessToken || !refreshToken || !expiresAt) {
        return false;
      }

      this.user = JSON.parse(userJson) as AuthUser;
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      this.expiresAt = parseInt(expiresAt, 10);

      // Update API client tokens
      this.apiClient.setAccessToken(accessToken);
      this.apiClient.setRefreshToken(refreshToken);

      // Check if token is expired
      if (this.isTokenExpired()) {
        // Try to refresh
        try {
          const response = await this.apiClient.auth.refreshToken({ refreshToken });
          this.handleAuthResponse(response);
          return true;
        } catch {
          this.clearTokens();
          return false;
        }
      }

      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  saveSession(): void {
    if (this.user && this.accessToken && this.refreshToken && this.expiresAt) {
      localStorage.setItem('auth:user', JSON.stringify(this.user));
      localStorage.setItem('auth:accessToken', this.accessToken);
      localStorage.setItem('auth:refreshToken', this.refreshToken);
      localStorage.setItem('auth:expiresAt', this.expiresAt.toString());
    }
  }

  // ========================================
  // Private Helpers
  // ========================================

  private handleAuthResponse(response: AuthResponse): void {
    this.user = response.user;
    this.setTokens(response.accessToken, response.refreshToken, response.expiresIn);
  }
}
```

### 4. Auth Store (Pinia)

**File:** `frontend/core/src/auth/authStore.ts`

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { IAuthService } from './IAuthService';
import type { LoginRequest, RegisterRequest, AuthResponse } from '../types/api';
import type { AuthUser } from '../types/auth';

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<AuthUser | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Injected service (set during plugin installation)
  let authService: IAuthService | null = null;

  // Getters
  const isAuthenticated = computed(() => authService?.isAuthenticated() ?? false);
  const isAdmin = computed(() => authService?.isAdmin() ?? false);
  const userRole = computed(() => user.value?.role ?? null);

  // Actions
  async function login(request: LoginRequest): Promise<void> {
    if (!authService) throw new Error('AuthService not initialized');

    loading.value = true;
    error.value = null;

    try {
      const response = await authService.login(request);
      user.value = response.user;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function register(request: RegisterRequest): Promise<void> {
    if (!authService) throw new Error('AuthService not initialized');

    loading.value = true;
    error.value = null;

    try {
      const response = await authService.register(request);
      user.value = response.user;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Registration failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function logout(): Promise<void> {
    if (!authService) throw new Error('AuthService not initialized');

    loading.value = true;
    error.value = null;

    try {
      await authService.logout();
      user.value = null;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Logout failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function restoreSession(): Promise<boolean> {
    if (!authService) return false;

    const restored = await authService.restoreSession();
    if (restored) {
      user.value = authService.getCurrentUser();
    }
    return restored;
  }

  function hasRole(role: string): boolean {
    return authService?.hasRole(role) ?? false;
  }

  function hasAnyRole(roles: string[]): boolean {
    return authService?.hasAnyRole(roles) ?? false;
  }

  function setAuthService(service: IAuthService): void {
    authService = service;
  }

  function clearError(): void {
    error.value = null;
  }

  return {
    // State
    user,
    loading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
    userRole,
    // Actions
    login,
    register,
    logout,
    restoreSession,
    hasRole,
    hasAnyRole,
    setAuthService,
    clearError,
  };
});
```

### 5. Barrel Exports

**File:** `frontend/core/src/auth/index.ts`

```typescript
export * from './IAuthService';
export * from './AuthService';
export * from './authStore';
```

---

## Testing Strategy

### Unit Tests

**File:** `frontend/core/__tests__/unit/auth/AuthService.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AuthService } from '../../../src/auth/AuthService';
import type { IApiClient } from '../../../src/api';
import type { AuthResponse } from '../../../src/types/api';

describe('AuthService', () => {
  let authService: AuthService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      auth: {
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      },
      setAccessToken: vi.fn(),
      setRefreshToken: vi.fn(),
      clearTokens: vi.fn(),
    } as any;

    authService = new AuthService(mockApiClient);
    localStorage.clear();
  });

  it('should login successfully', async () => {
    const response: AuthResponse = {
      user: {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      expiresIn: 3600,
    };

    vi.mocked(mockApiClient.auth.login).mockResolvedValue(response);

    await authService.login({ email: 'test@example.com', password: 'password' });

    expect(authService.isAuthenticated()).toBe(true);
    expect(authService.getCurrentUser()?.email).toBe('test@example.com');
  });

  it('should check admin role', async () => {
    const response: AuthResponse = {
      user: {
        id: 1,
        email: 'admin@example.com',
        firstName: 'Admin',
        lastName: 'User',
        role: 'admin',
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      expiresIn: 3600,
    };

    vi.mocked(mockApiClient.auth.login).mockResolvedValue(response);

    await authService.login({ email: 'admin@example.com', password: 'password' });

    expect(authService.isAdmin()).toBe(true);
    expect(authService.hasRole('admin')).toBe(true);
  });

  it('should restore session from localStorage', async () => {
    const user = {
      id: 1,
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'user' as const,
      status: 'active' as const,
    };

    localStorage.setItem('auth:user', JSON.stringify(user));
    localStorage.setItem('auth:accessToken', 'access-token');
    localStorage.setItem('auth:refreshToken', 'refresh-token');
    localStorage.setItem('auth:expiresAt', (Date.now() + 3600000).toString());

    const restored = await authService.restoreSession();

    expect(restored).toBe(true);
    expect(authService.isAuthenticated()).toBe(true);
  });

  it('should clear tokens on logout', async () => {
    vi.mocked(mockApiClient.auth.logout).mockResolvedValue();

    await authService.logout();

    expect(authService.isAuthenticated()).toBe(false);
    expect(authService.getCurrentUser()).toBeNull();
    expect(mockApiClient.clearTokens).toHaveBeenCalled();
  });
});
```

---

## Definition of Done

- [x] IAuthService interface implemented
- [x] AuthService with JWT management
- [x] authStore (Pinia) with reactive state
- [x] Session persistence with localStorage
- [x] Role checking utilities
- [x] Unit tests with 95%+ coverage
- [x] TypeScript strict mode passing
- [x] ESLint passing
- [x] Documentation

---

## Next Sprint

[Sprint 4: Event Bus & Validation](./sprint-4-events-validation.md)
