# Sprint 2: Plan Management Plugin

**Duration:** 2 weeks
**Goal:** Build a comprehensive plan management plugin for admin users to create, edit, and manage tariff plans with multi-currency support.

## Overview

This sprint delivers the **Plan Management Plugin** for the admin application, enabling administrators to:

- View all tariff plans (active and inactive)
- Create new plans with pricing, features, and limits
- Edit existing plans
- Activate/deactivate plans
- Manage multi-currency pricing
- Define plan features and resource limits

## Deliverables

- Plan list view with filtering and sorting
- Plan creation form with validation
- Plan editor with full CRUD operations
- Multi-currency pricing management
- Feature and limit configuration
- Activate/deactivate functionality
- Unit tests (>90% coverage)
- E2E tests with Playwright
- Docker integration

---

## TDD Approach

Following Test-Driven Development:

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Clean up code while keeping tests green

Example TDD cycle for plan creation:

```typescript
// Step 1: RED - Write failing test
it('should create a new plan', async () => {
  const newPlan: CreatePlanData = {
    name: 'Premium',
    description: 'Premium features',
    type: PlanType.SUBSCRIPTION,
    billingPeriod: BillingPeriod.MONTHLY,
    pricing: [
      { currency: Currency.USD, amount: 29.99 },
      { currency: Currency.EUR, amount: 26.99 }
    ],
    features: ['feature_1', 'feature_2'],
    limits: { maxUsers: 10, maxStorage: 100 }
  };

  const result = await planService.createPlan(newPlan);

  expect(result.id).toBeDefined();
  expect(result.name).toBe('Premium');
});

// Step 2: GREEN - Implement minimal code
async createPlan(data: CreatePlanData): Promise<TariffPlan> {
  const response = await this.apiClient.post<TariffPlan>(
    '/api/v1/admin/plans',
    data
  );
  return response;
}

// Step 3: REFACTOR - Add validation, error handling
```

---

## Architecture

Following **SOLID** principles:

### Directory Structure

```
frontend/admin/vue/src/plugins/plan-management/
├── index.ts                          # Plugin registration
├── routes/
│   └── planManagementRoutes.ts       # Route definitions
├── views/
│   ├── PlanListView.vue              # Plan list with filters
│   ├── PlanEditorView.vue            # Create/Edit plan
│   └── components/
│       ├── PlanCard.vue              # Plan display card
│       ├── PlanForm.vue              # Plan form component
│       ├── PricingEditor.vue         # Multi-currency pricing
│       ├── FeatureEditor.vue         # Feature management
│       └── LimitEditor.vue           # Resource limits
├── stores/
│   ├── planManagementStore.ts        # Pinia store
│   └── __tests__/
│       └── planManagementStore.spec.ts
├── services/
│   ├── IPlanService.ts               # Service interface (LSP)
│   ├── PlanService.ts                # Implementation (DI)
│   └── __tests__/
│       └── PlanService.spec.ts
├── composables/
│   ├── usePlanList.ts                # List logic (SRP)
│   ├── usePlanEditor.ts              # Editor logic (SRP)
│   └── __tests__/
│       ├── usePlanList.spec.ts
│       └── usePlanEditor.spec.ts
├── types/
│   ├── TariffPlan.ts                 # Domain models
│   ├── Pricing.ts
│   └── PlanFeature.ts
└── __tests__/
    └── e2e/
        ├── plan-list.spec.ts
        ├── plan-creation.spec.ts
        └── plan-editing.spec.ts
```

---

## 1. Domain Models (types/TariffPlan.ts)

Following **clean code** principles: clear naming, type safety.

```typescript
export interface TariffPlan {
  id: number;
  name: string;
  description: string;
  type: PlanType;
  billingPeriod: BillingPeriod;
  pricing: PlanPricing[];
  features: string[];
  limits: PlanLimits;
  status: PlanStatus;
  isPopular: boolean;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export enum PlanType {
  SUBSCRIPTION = 'subscription',
  ONE_TIME = 'one_time',
  FREEMIUM = 'freemium'
}

export enum BillingPeriod {
  MONTHLY = 'monthly',
  YEARLY = 'yearly',
  LIFETIME = 'lifetime'
}

export enum PlanStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived'
}

export interface PlanPricing {
  currency: Currency;
  amount: number;
  stripeProductId?: string;
  stripePriceId?: string;
  paypalPlanId?: string;
}

export enum Currency {
  USD = 'USD',
  EUR = 'EUR',
  GBP = 'GBP',
  UAH = 'UAH'
}

export interface PlanLimits {
  maxUsers?: number;
  maxStorage?: number;
  maxApiCalls?: number;
  maxProjects?: number;
}

export interface PlanFeature {
  id: string;
  name: string;
  description: string;
  category: FeatureCategory;
  enabled: boolean;
}

export enum FeatureCategory {
  CORE = 'core',
  ADVANCED = 'advanced',
  PREMIUM = 'premium'
}

// Request/Response types

export interface GetPlansParams {
  page?: number;
  limit?: number;
  status?: PlanStatus;
  type?: PlanType;
  sortBy?: 'name' | 'createdAt' | 'sortOrder';
  sortOrder?: 'asc' | 'desc';
}

export interface CreatePlanData {
  name: string;
  description: string;
  type: PlanType;
  billingPeriod: BillingPeriod;
  pricing: Omit<PlanPricing, 'stripeProductId' | 'stripePriceId' | 'paypalPlanId'>[];
  features: string[];
  limits: PlanLimits;
  isPopular?: boolean;
  sortOrder?: number;
}

export interface UpdatePlanData extends Partial<CreatePlanData> {
  status?: PlanStatus;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

---

## 2. Service Interface (services/IPlanService.ts)

Following **Liskov Substitution Principle**: Any implementation of `IPlanService` can be substituted.

```typescript
import type {
  TariffPlan,
  GetPlansParams,
  CreatePlanData,
  UpdatePlanData,
  PlanStatus,
  PaginatedResponse,
  PlanFeature
} from '../types/TariffPlan';

export interface IPlanService {
  /**
   * Get paginated list of plans
   */
  getPlans(params: GetPlansParams): Promise<PaginatedResponse<TariffPlan>>;

  /**
   * Get plan by ID
   */
  getPlanById(id: number): Promise<TariffPlan>;

  /**
   * Create new plan
   */
  createPlan(data: CreatePlanData): Promise<TariffPlan>;

  /**
   * Update existing plan
   */
  updatePlan(id: number, data: UpdatePlanData): Promise<TariffPlan>;

  /**
   * Update plan status (activate/deactivate)
   */
  updatePlanStatus(id: number, status: PlanStatus): Promise<TariffPlan>;

  /**
   * Delete plan (soft delete)
   */
  deletePlan(id: number): Promise<void>;

  /**
   * Get available features
   */
  getAvailableFeatures(): Promise<PlanFeature[]>;

  /**
   * Sync plan with payment provider (Stripe/PayPal)
   */
  syncPlanWithProvider(id: number, provider: 'stripe' | 'paypal'): Promise<TariffPlan>;
}
```

---

## 3. Service Implementation (services/PlanService.ts)

Following **Dependency Injection**: `IApiClient` injected via constructor.

```typescript
import type { IApiClient } from '@vbwd/core-sdk';
import type { IPlanService } from './IPlanService';
import type {
  TariffPlan,
  GetPlansParams,
  CreatePlanData,
  UpdatePlanData,
  PlanStatus,
  PaginatedResponse,
  PlanFeature
} from '../types/TariffPlan';

export class PlanService implements IPlanService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;  // Dependency Injection
  }

  async getPlans(params: GetPlansParams): Promise<PaginatedResponse<TariffPlan>> {
    const response = await this.apiClient.get<PaginatedResponse<TariffPlan>>(
      '/api/v1/admin/plans',
      { params }
    );
    return response;
  }

  async getPlanById(id: number): Promise<TariffPlan> {
    const response = await this.apiClient.get<TariffPlan>(
      `/api/v1/admin/plans/${id}`
    );
    return response;
  }

  async createPlan(data: CreatePlanData): Promise<TariffPlan> {
    // Validation
    this.validatePlanData(data);

    const response = await this.apiClient.post<TariffPlan>(
      '/api/v1/admin/plans',
      data
    );
    return response;
  }

  async updatePlan(id: number, data: UpdatePlanData): Promise<TariffPlan> {
    if (Object.keys(data).length === 0) {
      throw new Error('No data provided for update');
    }

    const response = await this.apiClient.put<TariffPlan>(
      `/api/v1/admin/plans/${id}`,
      data
    );
    return response;
  }

  async updatePlanStatus(id: number, status: PlanStatus): Promise<TariffPlan> {
    const response = await this.apiClient.put<TariffPlan>(
      `/api/v1/admin/plans/${id}/status`,
      { status }
    );
    return response;
  }

  async deletePlan(id: number): Promise<void> {
    await this.apiClient.delete(`/api/v1/admin/plans/${id}`);
  }

  async getAvailableFeatures(): Promise<PlanFeature[]> {
    const response = await this.apiClient.get<PlanFeature[]>(
      '/api/v1/admin/plans/features'
    );
    return response;
  }

  async syncPlanWithProvider(
    id: number,
    provider: 'stripe' | 'paypal'
  ): Promise<TariffPlan> {
    const response = await this.apiClient.post<TariffPlan>(
      `/api/v1/admin/plans/${id}/sync/${provider}`
    );
    return response;
  }

  // Private helper (SRP - single responsibility for validation)
  private validatePlanData(data: CreatePlanData): void {
    if (!data.name || data.name.trim().length === 0) {
      throw new Error('Plan name is required');
    }

    if (!data.pricing || data.pricing.length === 0) {
      throw new Error('At least one pricing option is required');
    }

    for (const price of data.pricing) {
      if (price.amount <= 0) {
        throw new Error(`Invalid amount for ${price.currency}: must be > 0`);
      }
    }

    if (!data.features || data.features.length === 0) {
      throw new Error('At least one feature is required');
    }
  }
}
```

---

## 4. Service Unit Tests (services/__tests__/PlanService.spec.ts)

Following **TDD**: Write tests first, then implementation.

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { IApiClient } from '@vbwd/core-sdk';
import { PlanService } from '../PlanService';
import type { CreatePlanData, UpdatePlanData, PlanStatus } from '../../types/TariffPlan';
import { PlanType, BillingPeriod, Currency } from '../../types/TariffPlan';

describe('PlanService', () => {
  let planService: PlanService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    } as unknown as IApiClient;

    planService = new PlanService(mockApiClient);  // DI in test
  });

  describe('getPlans', () => {
    it('should fetch plans with pagination', async () => {
      // Arrange
      const mockResponse = {
        data: [
          { id: 1, name: 'Basic', type: PlanType.SUBSCRIPTION },
          { id: 2, name: 'Premium', type: PlanType.SUBSCRIPTION }
        ],
        pagination: { page: 1, limit: 25, total: 2, totalPages: 1 }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      // Act
      const result = await planService.getPlans({ page: 1, limit: 25 });

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/plans', {
        params: { page: 1, limit: 25 }
      });
      expect(result.data).toHaveLength(2);
      expect(result.pagination.total).toBe(2);
    });

    it('should filter plans by status', async () => {
      // Arrange
      const mockResponse = {
        data: [{ id: 1, name: 'Basic', status: 'active' }],
        pagination: { page: 1, limit: 25, total: 1, totalPages: 1 }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      // Act
      await planService.getPlans({ status: 'active' as PlanStatus });

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/plans', {
        params: { status: 'active' }
      });
    });
  });

  describe('getPlanById', () => {
    it('should fetch plan by ID', async () => {
      // Arrange
      const mockPlan = {
        id: 1,
        name: 'Premium',
        type: PlanType.SUBSCRIPTION,
        pricing: [{ currency: Currency.USD, amount: 29.99 }]
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockPlan);

      // Act
      const result = await planService.getPlanById(1);

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/plans/1');
      expect(result.id).toBe(1);
      expect(result.name).toBe('Premium');
    });
  });

  describe('createPlan', () => {
    it('should create a new plan', async () => {
      // Arrange
      const newPlan: CreatePlanData = {
        name: 'Premium',
        description: 'Premium features',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [
          { currency: Currency.USD, amount: 29.99 },
          { currency: Currency.EUR, amount: 26.99 }
        ],
        features: ['feature_1', 'feature_2'],
        limits: { maxUsers: 10, maxStorage: 100 }
      };

      const mockResponse = { id: 1, ...newPlan, status: 'active', createdAt: '2025-12-20' };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      // Act
      const result = await planService.createPlan(newPlan);

      // Assert
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/plans', newPlan);
      expect(result.id).toBe(1);
      expect(result.name).toBe('Premium');
      expect(result.pricing).toHaveLength(2);
    });

    it('should throw error if name is empty', async () => {
      // Arrange
      const invalidPlan: CreatePlanData = {
        name: '',  // Invalid
        description: 'Test',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [{ currency: Currency.USD, amount: 29.99 }],
        features: ['feature_1'],
        limits: {}
      };

      // Act & Assert
      await expect(planService.createPlan(invalidPlan)).rejects.toThrow('Plan name is required');
    });

    it('should throw error if no pricing provided', async () => {
      // Arrange
      const invalidPlan: CreatePlanData = {
        name: 'Test',
        description: 'Test',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [],  // Invalid
        features: ['feature_1'],
        limits: {}
      };

      // Act & Assert
      await expect(planService.createPlan(invalidPlan)).rejects.toThrow(
        'At least one pricing option is required'
      );
    });

    it('should throw error if pricing amount is invalid', async () => {
      // Arrange
      const invalidPlan: CreatePlanData = {
        name: 'Test',
        description: 'Test',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [{ currency: Currency.USD, amount: -10 }],  // Invalid
        features: ['feature_1'],
        limits: {}
      };

      // Act & Assert
      await expect(planService.createPlan(invalidPlan)).rejects.toThrow('Invalid amount');
    });

    it('should throw error if no features provided', async () => {
      // Arrange
      const invalidPlan: CreatePlanData = {
        name: 'Test',
        description: 'Test',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [{ currency: Currency.USD, amount: 29.99 }],
        features: [],  // Invalid
        limits: {}
      };

      // Act & Assert
      await expect(planService.createPlan(invalidPlan)).rejects.toThrow(
        'At least one feature is required'
      );
    });
  });

  describe('updatePlan', () => {
    it('should update plan', async () => {
      // Arrange
      const updateData: UpdatePlanData = {
        name: 'Premium Plus',
        description: 'Updated description'
      };

      const mockResponse = { id: 1, ...updateData, status: 'active' };
      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      // Act
      const result = await planService.updatePlan(1, updateData);

      // Assert
      expect(mockApiClient.put).toHaveBeenCalledWith('/api/v1/admin/plans/1', updateData);
      expect(result.name).toBe('Premium Plus');
    });

    it('should throw error if no data provided', async () => {
      // Act & Assert
      await expect(planService.updatePlan(1, {})).rejects.toThrow(
        'No data provided for update'
      );
    });
  });

  describe('updatePlanStatus', () => {
    it('should update plan status', async () => {
      // Arrange
      const mockResponse = { id: 1, name: 'Premium', status: 'inactive' };
      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      // Act
      const result = await planService.updatePlanStatus(1, 'inactive' as PlanStatus);

      // Assert
      expect(mockApiClient.put).toHaveBeenCalledWith('/api/v1/admin/plans/1/status', {
        status: 'inactive'
      });
      expect(result.status).toBe('inactive');
    });
  });

  describe('deletePlan', () => {
    it('should delete plan', async () => {
      // Arrange
      vi.mocked(mockApiClient.delete).mockResolvedValue(undefined);

      // Act
      await planService.deletePlan(1);

      // Assert
      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/v1/admin/plans/1');
    });
  });

  describe('getAvailableFeatures', () => {
    it('should fetch available features', async () => {
      // Arrange
      const mockFeatures = [
        { id: 'feature_1', name: 'Feature 1', enabled: true },
        { id: 'feature_2', name: 'Feature 2', enabled: false }
      ];
      vi.mocked(mockApiClient.get).mockResolvedValue(mockFeatures);

      // Act
      const result = await planService.getAvailableFeatures();

      // Assert
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/plans/features');
      expect(result).toHaveLength(2);
    });
  });

  describe('syncPlanWithProvider', () => {
    it('should sync plan with Stripe', async () => {
      // Arrange
      const mockResponse = {
        id: 1,
        name: 'Premium',
        pricing: [
          {
            currency: Currency.USD,
            amount: 29.99,
            stripeProductId: 'prod_123',
            stripePriceId: 'price_123'
          }
        ]
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      // Act
      const result = await planService.syncPlanWithProvider(1, 'stripe');

      // Assert
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/plans/1/sync/stripe');
      expect(result.pricing[0].stripeProductId).toBe('prod_123');
    });

    it('should sync plan with PayPal', async () => {
      // Arrange
      const mockResponse = {
        id: 1,
        name: 'Premium',
        pricing: [
          {
            currency: Currency.USD,
            amount: 29.99,
            paypalPlanId: 'P-123'
          }
        ]
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      // Act
      const result = await planService.syncPlanWithProvider(1, 'paypal');

      // Assert
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/plans/1/sync/paypal');
      expect(result.pricing[0].paypalPlanId).toBe('P-123');
    });
  });
});
```

**Test Coverage:** >90% (all methods, error cases, validation logic)

---

## 5. Store Implementation (stores/planManagementStore.ts)

Following **Dependency Injection**: Service injected via setter.

```typescript
import { defineStore } from 'pinia';
import type { IPlanService } from '../services/IPlanService';
import type {
  TariffPlan,
  GetPlansParams,
  CreatePlanData,
  UpdatePlanData,
  PlanStatus,
  PlanFeature
} from '../types/TariffPlan';

interface PlanManagementState {
  plans: TariffPlan[];
  selectedPlan: TariffPlan | null;
  availableFeatures: PlanFeature[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  planService: IPlanService | null;  // DI
}

export const usePlanManagementStore = defineStore('planManagement', {
  state: (): PlanManagementState => ({
    plans: [],
    selectedPlan: null,
    availableFeatures: [],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: 25,
      total: 0,
      totalPages: 0
    },
    planService: null
  }),

  getters: {
    activePlans: (state) => state.plans.filter(plan => plan.status === 'active'),
    inactivePlans: (state) => state.plans.filter(plan => plan.status === 'inactive'),

    isPlanFormValid: (state) => (plan: CreatePlanData): boolean => {
      return !!(
        plan.name &&
        plan.name.trim().length > 0 &&
        plan.pricing &&
        plan.pricing.length > 0 &&
        plan.features &&
        plan.features.length > 0
      );
    }
  },

  actions: {
    // Inject service (DI)
    setPlanService(service: IPlanService) {
      this.planService = service;
    },

    async fetchPlans(params: GetPlansParams = {}) {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const response = await this.planService.getPlans({
          page: this.pagination.page,
          limit: this.pagination.limit,
          ...params
        });

        this.plans = response.data;
        this.pagination = response.pagination;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch plans';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchPlanById(id: number) {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const plan = await this.planService.getPlanById(id);
        this.selectedPlan = plan;
        return plan;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch plan';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async createPlan(data: CreatePlanData) {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const newPlan = await this.planService.createPlan(data);
        this.plans.unshift(newPlan);  // Add to beginning of list
        this.pagination.total += 1;
        return newPlan;
      } catch (error: any) {
        this.error = error.message || 'Failed to create plan';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updatePlan(id: number, data: UpdatePlanData) {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const updatedPlan = await this.planService.updatePlan(id, data);

        // Update in list
        const index = this.plans.findIndex(p => p.id === id);
        if (index !== -1) {
          this.plans[index] = updatedPlan;
        }

        // Update selected if it's the same plan
        if (this.selectedPlan?.id === id) {
          this.selectedPlan = updatedPlan;
        }

        return updatedPlan;
      } catch (error: any) {
        this.error = error.message || 'Failed to update plan';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updatePlanStatus(id: number, status: PlanStatus) {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const updatedPlan = await this.planService.updatePlanStatus(id, status);

        // Update in list
        const index = this.plans.findIndex(p => p.id === id);
        if (index !== -1) {
          this.plans[index] = updatedPlan;
        }

        return updatedPlan;
      } catch (error: any) {
        this.error = error.message || 'Failed to update plan status';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deletePlan(id: number) {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        await this.planService.deletePlan(id);

        // Remove from list
        this.plans = this.plans.filter(p => p.id !== id);
        this.pagination.total -= 1;

        // Clear selected if it's the same plan
        if (this.selectedPlan?.id === id) {
          this.selectedPlan = null;
        }
      } catch (error: any) {
        this.error = error.message || 'Failed to delete plan';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchAvailableFeatures() {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const features = await this.planService.getAvailableFeatures();
        this.availableFeatures = features;
        return features;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch features';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async syncPlanWithProvider(id: number, provider: 'stripe' | 'paypal') {
      if (!this.planService) {
        throw new Error('PlanService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const syncedPlan = await this.planService.syncPlanWithProvider(id, provider);

        // Update in list
        const index = this.plans.findIndex(p => p.id === id);
        if (index !== -1) {
          this.plans[index] = syncedPlan;
        }

        // Update selected if it's the same plan
        if (this.selectedPlan?.id === id) {
          this.selectedPlan = syncedPlan;
        }

        return syncedPlan;
      } catch (error: any) {
        this.error = error.message || `Failed to sync plan with ${provider}`;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    setPage(page: number) {
      this.pagination.page = page;
    },

    setLimit(limit: number) {
      this.pagination.limit = limit;
      this.pagination.page = 1;  // Reset to first page
    },

    clearError() {
      this.error = null;
    },

    clearSelectedPlan() {
      this.selectedPlan = null;
    }
  }
});
```

---

## 6. Store Unit Tests (stores/__tests__/planManagementStore.spec.ts)

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { usePlanManagementStore } from '../planManagementStore';
import type { IPlanService } from '../../services/IPlanService';
import type { CreatePlanData } from '../../types/TariffPlan';
import { PlanType, BillingPeriod, Currency, PlanStatus } from '../../types/TariffPlan';

describe('planManagementStore', () => {
  let store: ReturnType<typeof usePlanManagementStore>;
  let mockPlanService: IPlanService;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = usePlanManagementStore();

    mockPlanService = {
      getPlans: vi.fn(),
      getPlanById: vi.fn(),
      createPlan: vi.fn(),
      updatePlan: vi.fn(),
      updatePlanStatus: vi.fn(),
      deletePlan: vi.fn(),
      getAvailableFeatures: vi.fn(),
      syncPlanWithProvider: vi.fn()
    } as unknown as IPlanService;

    store.setPlanService(mockPlanService);
  });

  describe('fetchPlans', () => {
    it('should fetch plans and update state', async () => {
      // Arrange
      const mockResponse = {
        data: [
          { id: 1, name: 'Basic', status: PlanStatus.ACTIVE },
          { id: 2, name: 'Premium', status: PlanStatus.ACTIVE }
        ],
        pagination: { page: 1, limit: 25, total: 2, totalPages: 1 }
      };
      vi.mocked(mockPlanService.getPlans).mockResolvedValue(mockResponse);

      // Act
      await store.fetchPlans();

      // Assert
      expect(store.plans).toHaveLength(2);
      expect(store.pagination.total).toBe(2);
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it('should handle fetch error', async () => {
      // Arrange
      vi.mocked(mockPlanService.getPlans).mockRejectedValue(new Error('Network error'));

      // Act & Assert
      await expect(store.fetchPlans()).rejects.toThrow('Network error');
      expect(store.error).toBe('Network error');
      expect(store.loading).toBe(false);
    });
  });

  describe('fetchPlanById', () => {
    it('should fetch plan by ID', async () => {
      // Arrange
      const mockPlan = { id: 1, name: 'Premium', status: PlanStatus.ACTIVE };
      vi.mocked(mockPlanService.getPlanById).mockResolvedValue(mockPlan);

      // Act
      await store.fetchPlanById(1);

      // Assert
      expect(store.selectedPlan).toEqual(mockPlan);
      expect(mockPlanService.getPlanById).toHaveBeenCalledWith(1);
    });
  });

  describe('createPlan', () => {
    it('should create new plan and add to list', async () => {
      // Arrange
      const newPlan: CreatePlanData = {
        name: 'Enterprise',
        description: 'Enterprise features',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.YEARLY,
        pricing: [{ currency: Currency.USD, amount: 99.99 }],
        features: ['feature_1'],
        limits: { maxUsers: 100 }
      };

      const mockResponse = { id: 3, ...newPlan, status: PlanStatus.ACTIVE, createdAt: '2025-12-20' };
      vi.mocked(mockPlanService.createPlan).mockResolvedValue(mockResponse);

      // Act
      const result = await store.createPlan(newPlan);

      // Assert
      expect(result.id).toBe(3);
      expect(store.plans).toHaveLength(1);
      expect(store.plans[0].name).toBe('Enterprise');
      expect(store.pagination.total).toBe(1);
    });

    it('should handle creation error', async () => {
      // Arrange
      const newPlan: CreatePlanData = {
        name: 'Test',
        description: 'Test',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [{ currency: Currency.USD, amount: 9.99 }],
        features: ['feature_1'],
        limits: {}
      };
      vi.mocked(mockPlanService.createPlan).mockRejectedValue(new Error('Validation failed'));

      // Act & Assert
      await expect(store.createPlan(newPlan)).rejects.toThrow('Validation failed');
      expect(store.error).toBe('Validation failed');
    });
  });

  describe('updatePlan', () => {
    it('should update plan in list', async () => {
      // Arrange
      store.plans = [
        { id: 1, name: 'Basic', status: PlanStatus.ACTIVE },
        { id: 2, name: 'Premium', status: PlanStatus.ACTIVE }
      ] as any;

      const updatedPlan = { id: 1, name: 'Basic Plus', status: PlanStatus.ACTIVE };
      vi.mocked(mockPlanService.updatePlan).mockResolvedValue(updatedPlan as any);

      // Act
      await store.updatePlan(1, { name: 'Basic Plus' });

      // Assert
      expect(store.plans[0].name).toBe('Basic Plus');
    });

    it('should update selected plan if it matches', async () => {
      // Arrange
      store.selectedPlan = { id: 1, name: 'Basic', status: PlanStatus.ACTIVE } as any;

      const updatedPlan = { id: 1, name: 'Basic Plus', status: PlanStatus.ACTIVE };
      vi.mocked(mockPlanService.updatePlan).mockResolvedValue(updatedPlan as any);

      // Act
      await store.updatePlan(1, { name: 'Basic Plus' });

      // Assert
      expect(store.selectedPlan?.name).toBe('Basic Plus');
    });
  });

  describe('updatePlanStatus', () => {
    it('should update plan status', async () => {
      // Arrange
      store.plans = [
        { id: 1, name: 'Basic', status: PlanStatus.ACTIVE }
      ] as any;

      const updatedPlan = { id: 1, name: 'Basic', status: PlanStatus.INACTIVE };
      vi.mocked(mockPlanService.updatePlanStatus).mockResolvedValue(updatedPlan as any);

      // Act
      await store.updatePlanStatus(1, PlanStatus.INACTIVE);

      // Assert
      expect(store.plans[0].status).toBe(PlanStatus.INACTIVE);
    });
  });

  describe('deletePlan', () => {
    it('should remove plan from list', async () => {
      // Arrange
      store.plans = [
        { id: 1, name: 'Basic', status: PlanStatus.ACTIVE },
        { id: 2, name: 'Premium', status: PlanStatus.ACTIVE }
      ] as any;
      store.pagination.total = 2;

      vi.mocked(mockPlanService.deletePlan).mockResolvedValue(undefined);

      // Act
      await store.deletePlan(1);

      // Assert
      expect(store.plans).toHaveLength(1);
      expect(store.plans[0].id).toBe(2);
      expect(store.pagination.total).toBe(1);
    });

    it('should clear selected plan if deleted', async () => {
      // Arrange
      store.selectedPlan = { id: 1, name: 'Basic', status: PlanStatus.ACTIVE } as any;
      vi.mocked(mockPlanService.deletePlan).mockResolvedValue(undefined);

      // Act
      await store.deletePlan(1);

      // Assert
      expect(store.selectedPlan).toBeNull();
    });
  });

  describe('getters', () => {
    it('should filter active plans', () => {
      // Arrange
      store.plans = [
        { id: 1, name: 'Basic', status: PlanStatus.ACTIVE },
        { id: 2, name: 'Premium', status: PlanStatus.INACTIVE },
        { id: 3, name: 'Enterprise', status: PlanStatus.ACTIVE }
      ] as any;

      // Act
      const active = store.activePlans;

      // Assert
      expect(active).toHaveLength(2);
      expect(active[0].name).toBe('Basic');
      expect(active[1].name).toBe('Enterprise');
    });

    it('should filter inactive plans', () => {
      // Arrange
      store.plans = [
        { id: 1, name: 'Basic', status: PlanStatus.ACTIVE },
        { id: 2, name: 'Premium', status: PlanStatus.INACTIVE },
        { id: 3, name: 'Enterprise', status: PlanStatus.ACTIVE }
      ] as any;

      // Act
      const inactive = store.inactivePlans;

      // Assert
      expect(inactive).toHaveLength(1);
      expect(inactive[0].name).toBe('Premium');
    });

    it('should validate plan form data', () => {
      // Valid plan
      const validPlan: CreatePlanData = {
        name: 'Test',
        description: 'Test',
        type: PlanType.SUBSCRIPTION,
        billingPeriod: BillingPeriod.MONTHLY,
        pricing: [{ currency: Currency.USD, amount: 9.99 }],
        features: ['feature_1'],
        limits: {}
      };

      expect(store.isPlanFormValid(validPlan)).toBe(true);

      // Invalid - no name
      const invalidPlan1 = { ...validPlan, name: '' };
      expect(store.isPlanFormValid(invalidPlan1)).toBe(false);

      // Invalid - no pricing
      const invalidPlan2 = { ...validPlan, pricing: [] };
      expect(store.isPlanFormValid(invalidPlan2)).toBe(false);

      // Invalid - no features
      const invalidPlan3 = { ...validPlan, features: [] };
      expect(store.isPlanFormValid(invalidPlan3)).toBe(false);
    });
  });

  describe('syncPlanWithProvider', () => {
    it('should sync plan with Stripe', async () => {
      // Arrange
      store.plans = [{ id: 1, name: 'Premium', status: PlanStatus.ACTIVE }] as any;

      const syncedPlan = {
        id: 1,
        name: 'Premium',
        pricing: [{ currency: Currency.USD, amount: 29.99, stripeProductId: 'prod_123' }]
      };
      vi.mocked(mockPlanService.syncPlanWithProvider).mockResolvedValue(syncedPlan as any);

      // Act
      await store.syncPlanWithProvider(1, 'stripe');

      // Assert
      expect(mockPlanService.syncPlanWithProvider).toHaveBeenCalledWith(1, 'stripe');
      expect(store.plans[0].pricing[0].stripeProductId).toBe('prod_123');
    });
  });

  describe('fetchAvailableFeatures', () => {
    it('should fetch and store available features', async () => {
      // Arrange
      const mockFeatures = [
        { id: 'feature_1', name: 'Feature 1', enabled: true },
        { id: 'feature_2', name: 'Feature 2', enabled: false }
      ];
      vi.mocked(mockPlanService.getAvailableFeatures).mockResolvedValue(mockFeatures as any);

      // Act
      await store.fetchAvailableFeatures();

      // Assert
      expect(store.availableFeatures).toHaveLength(2);
      expect(store.availableFeatures[0].id).toBe('feature_1');
    });
  });
});
```

---

## 7. Composables

Following **Single Responsibility Principle**: Each composable has one clear purpose.

### composables/usePlanList.ts

```typescript
import { ref, computed, watch } from 'vue';
import { usePlanManagementStore } from '../stores/planManagementStore';
import type { GetPlansParams, PlanStatus, PlanType } from '../types/TariffPlan';

export function usePlanList() {
  const store = usePlanManagementStore();

  // Local state
  const currentPage = ref(1);
  const itemsPerPage = ref(25);
  const searchQuery = ref('');
  const statusFilter = ref<PlanStatus | undefined>(undefined);
  const typeFilter = ref<PlanType | undefined>(undefined);
  const sortBy = ref<'name' | 'createdAt' | 'sortOrder'>('createdAt');
  const sortOrder = ref<'asc' | 'desc'>('desc');

  // Computed
  const plans = computed(() => store.plans);
  const loading = computed(() => store.loading);
  const error = computed(() => store.error);
  const pagination = computed(() => store.pagination);
  const hasPlans = computed(() => plans.value.length > 0);

  // Methods
  const loadPlans = async () => {
    const params: GetPlansParams = {
      page: currentPage.value,
      limit: itemsPerPage.value,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value
    };

    if (statusFilter.value) {
      params.status = statusFilter.value;
    }

    if (typeFilter.value) {
      params.type = typeFilter.value;
    }

    await store.fetchPlans(params);
  };

  const changePage = async (page: number) => {
    currentPage.value = page;
    await loadPlans();
  };

  const changeItemsPerPage = async (limit: number) => {
    itemsPerPage.value = limit;
    currentPage.value = 1;  // Reset to first page
    await loadPlans();
  };

  const applyFilters = async () => {
    currentPage.value = 1;  // Reset to first page
    await loadPlans();
  };

  const clearFilters = async () => {
    statusFilter.value = undefined;
    typeFilter.value = undefined;
    searchQuery.value = '';
    currentPage.value = 1;
    await loadPlans();
  };

  const changeSorting = async (newSortBy: 'name' | 'createdAt' | 'sortOrder', newSortOrder?: 'asc' | 'desc') => {
    sortBy.value = newSortBy;
    if (newSortOrder) {
      sortOrder.value = newSortOrder;
    } else {
      // Toggle order if same column
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    }
    await loadPlans();
  };

  const refreshPlans = async () => {
    await loadPlans();
  };

  return {
    // State
    currentPage,
    itemsPerPage,
    searchQuery,
    statusFilter,
    typeFilter,
    sortBy,
    sortOrder,

    // Computed
    plans,
    loading,
    error,
    pagination,
    hasPlans,

    // Methods
    loadPlans,
    changePage,
    changeItemsPerPage,
    applyFilters,
    clearFilters,
    changeSorting,
    refreshPlans
  };
}
```

### composables/usePlanEditor.ts

```typescript
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { usePlanManagementStore } from '../stores/planManagementStore';
import type { TariffPlan, CreatePlanData, UpdatePlanData, PlanStatus } from '../types/TariffPlan';

export function usePlanEditor(planId?: number) {
  const store = usePlanManagementStore();
  const router = useRouter();

  // Local state
  const isEditMode = ref(!!planId);
  const isSaving = ref(false);
  const validationErrors = ref<Record<string, string>>({});

  // Computed
  const plan = computed(() => store.selectedPlan);
  const loading = computed(() => store.loading);
  const error = computed(() => store.error);
  const availableFeatures = computed(() => store.availableFeatures);

  // Methods
  const loadPlan = async () => {
    if (!planId) return;

    try {
      await store.fetchPlanById(planId);
    } catch (err: any) {
      console.error('Failed to load plan:', err);
    }
  };

  const loadAvailableFeatures = async () => {
    try {
      await store.fetchAvailableFeatures();
    } catch (err: any) {
      console.error('Failed to load features:', err);
    }
  };

  const savePlan = async (data: CreatePlanData | UpdatePlanData) => {
    isSaving.value = true;
    validationErrors.value = {};

    try {
      let savedPlan: TariffPlan;

      if (isEditMode.value && planId) {
        savedPlan = await store.updatePlan(planId, data as UpdatePlanData);
      } else {
        savedPlan = await store.createPlan(data as CreatePlanData);
      }

      // Navigate to plan list on success
      router.push('/admin/plans');

      return savedPlan;
    } catch (err: any) {
      // Handle validation errors from backend
      if (err.response?.data?.errors) {
        validationErrors.value = err.response.data.errors;
      }
      throw err;
    } finally {
      isSaving.value = false;
    }
  };

  const updateStatus = async (status: PlanStatus) => {
    if (!planId) return;

    try {
      await store.updatePlanStatus(planId, status);
    } catch (err: any) {
      console.error('Failed to update status:', err);
      throw err;
    }
  };

  const deletePlan = async () => {
    if (!planId) return;

    try {
      await store.deletePlan(planId);
      router.push('/admin/plans');
    } catch (err: any) {
      console.error('Failed to delete plan:', err);
      throw err;
    }
  };

  const syncWithStripe = async () => {
    if (!planId) return;

    try {
      await store.syncPlanWithProvider(planId, 'stripe');
    } catch (err: any) {
      console.error('Failed to sync with Stripe:', err);
      throw err;
    }
  };

  const syncWithPayPal = async () => {
    if (!planId) return;

    try {
      await store.syncPlanWithProvider(planId, 'paypal');
    } catch (err: any) {
      console.error('Failed to sync with PayPal:', err);
      throw err;
    }
  };

  const cancel = () => {
    router.push('/admin/plans');
  };

  const clearError = () => {
    store.clearError();
    validationErrors.value = {};
  };

  return {
    // State
    isEditMode,
    isSaving,
    validationErrors,

    // Computed
    plan,
    loading,
    error,
    availableFeatures,

    // Methods
    loadPlan,
    loadAvailableFeatures,
    savePlan,
    updateStatus,
    deletePlan,
    syncWithStripe,
    syncWithPayPal,
    cancel,
    clearError
  };
}
```

---

## 8. E2E Tests with Playwright

### __tests__/e2e/plan-list.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Plan List', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should display plan list', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Check table headers
    await expect(page.locator('th:has-text("Name")')).toBeVisible();
    await expect(page.locator('th:has-text("Type")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
    await expect(page.locator('th:has-text("Pricing")')).toBeVisible();

    // Check at least one plan exists
    const rows = page.locator('[data-testid="plan-row"]');
    await expect(rows).toHaveCountGreaterThan(0);
  });

  test('should filter plans by status', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Select "Active" filter
    await page.selectOption('select[data-testid="status-filter"]', 'active');
    await page.click('button:has-text("Apply Filters")');

    // Wait for table to update
    await page.waitForTimeout(500);

    // Verify all visible plans are active
    const statusBadges = page.locator('[data-testid="plan-status"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      const text = await statusBadges.nth(i).textContent();
      expect(text?.toLowerCase()).toContain('active');
    }
  });

  test('should filter plans by type', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Select "Subscription" filter
    await page.selectOption('select[data-testid="type-filter"]', 'subscription');
    await page.click('button:has-text("Apply Filters")');

    await page.waitForTimeout(500);

    // Verify all visible plans are subscriptions
    const typeBadges = page.locator('[data-testid="plan-type"]');
    const count = await typeBadges.count();

    for (let i = 0; i < count; i++) {
      const text = await typeBadges.nth(i).textContent();
      expect(text?.toLowerCase()).toContain('subscription');
    }
  });

  test('should navigate to plan details on row click', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Click first plan row
    await page.click('[data-testid="plan-row"]:first-child');

    // Should navigate to plan editor
    await page.waitForURL(/\/admin\/plans\/\d+/);
    await expect(page.locator('h1')).toContainText('Edit Plan');
  });

  test('should paginate plans', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Check if pagination exists (only if more than 25 plans)
    const nextButton = page.locator('button:has-text("Next")');

    if (await nextButton.isVisible()) {
      // Get first plan name
      const firstPlanName = await page.locator('[data-testid="plan-name"]:first-child').textContent();

      // Click next page
      await nextButton.click();
      await page.waitForTimeout(500);

      // First plan should be different
      const newFirstPlanName = await page.locator('[data-testid="plan-name"]:first-child').textContent();
      expect(newFirstPlanName).not.toBe(firstPlanName);
    }
  });

  test('should sort plans by name', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Click name header to sort
    await page.click('th:has-text("Name")');
    await page.waitForTimeout(500);

    // Get all plan names
    const planNames = await page.locator('[data-testid="plan-name"]').allTextContents();

    // Verify sorted ascending
    const sortedNames = [...planNames].sort();
    expect(planNames).toEqual(sortedNames);
  });

  test('should navigate to create plan page', async ({ page }) => {
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');

    // Click "Create Plan" button
    await page.click('button:has-text("Create Plan")');

    // Should navigate to plan creation page
    await page.waitForURL('/admin/plans/new');
    await expect(page.locator('h1')).toContainText('Create Plan');
  });
});
```

### __tests__/e2e/plan-creation.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Plan Creation', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');

    // Navigate to create plan page
    await page.goto('/admin/plans/new');
    await page.waitForSelector('form[data-testid="plan-form"]');
  });

  test('should create a new subscription plan', async ({ page }) => {
    // Fill basic info
    await page.fill('input[name="name"]', 'E2E Test Plan');
    await page.fill('textarea[name="description"]', 'Plan created by E2E test');
    await page.selectOption('select[name="type"]', 'subscription');
    await page.selectOption('select[name="billingPeriod"]', 'monthly');

    // Add pricing
    await page.click('button:has-text("Add Price")');
    await page.selectOption('select[name="pricing[0].currency"]', 'USD');
    await page.fill('input[name="pricing[0].amount"]', '29.99');

    // Add features
    await page.click('button:has-text("Add Feature")');
    await page.selectOption('select[name="features[0]"]', 'feature_1');

    // Set limits
    await page.fill('input[name="limits.maxUsers"]', '10');
    await page.fill('input[name="limits.maxStorage"]', '100');

    // Submit form
    await page.click('button[type="submit"]:has-text("Create Plan")');

    // Should navigate to plan list
    await page.waitForURL('/admin/plans');

    // Verify plan appears in list
    await expect(page.locator('[data-testid="plan-name"]:has-text("E2E Test Plan")')).toBeVisible();
  });

  test('should show validation errors for empty name', async ({ page }) => {
    // Leave name empty and try to submit
    await page.fill('textarea[name="description"]', 'Test');
    await page.selectOption('select[name="type"]', 'subscription');
    await page.click('button[type="submit"]');

    // Should show validation error
    await expect(page.locator('.error:has-text("name")')).toBeVisible();
  });

  test('should show validation error for invalid price', async ({ page }) => {
    await page.fill('input[name="name"]', 'Test Plan');
    await page.selectOption('select[name="type"]', 'subscription');

    // Add pricing with invalid amount
    await page.click('button:has-text("Add Price")');
    await page.selectOption('select[name="pricing[0].currency"]', 'USD');
    await page.fill('input[name="pricing[0].amount"]', '-10');

    await page.click('button[type="submit"]');

    // Should show validation error
    await expect(page.locator('.error:has-text("amount")')).toBeVisible();
  });

  test('should add multiple pricing options', async ({ page }) => {
    await page.fill('input[name="name"]', 'Multi-Currency Plan');
    await page.selectOption('select[name="type"]', 'subscription');

    // Add USD price
    await page.click('button:has-text("Add Price")');
    await page.selectOption('select[name="pricing[0].currency"]', 'USD');
    await page.fill('input[name="pricing[0].amount"]', '29.99');

    // Add EUR price
    await page.click('button:has-text("Add Price")');
    await page.selectOption('select[name="pricing[1].currency"]', 'EUR');
    await page.fill('input[name="pricing[1].amount"]', '26.99');

    // Verify both prices are visible
    await expect(page.locator('select[name="pricing[0].currency"]')).toHaveValue('USD');
    await expect(page.locator('select[name="pricing[1].currency"]')).toHaveValue('EUR');
  });

  test('should remove pricing option', async ({ page }) => {
    await page.fill('input[name="name"]', 'Test Plan');
    await page.selectOption('select[name="type"]', 'subscription');

    // Add two prices
    await page.click('button:has-text("Add Price")');
    await page.click('button:has-text("Add Price")');

    // Remove first price
    await page.click('[data-testid="remove-price-0"]');

    // Should have only one price input
    await expect(page.locator('select[name^="pricing"]')).toHaveCount(1);
  });

  test('should cancel plan creation', async ({ page }) => {
    await page.fill('input[name="name"]', 'Test Plan');

    // Click cancel button
    await page.click('button:has-text("Cancel")');

    // Should navigate back to plan list
    await page.waitForURL('/admin/plans');
  });
});
```

### __tests__/e2e/plan-editing.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Plan Editing', () => {
  let planId: number;

  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');

    // Navigate to first plan in list
    await page.goto('/admin/plans');
    await page.waitForSelector('[data-testid="plan-table"]');
    await page.click('[data-testid="plan-row"]:first-child');

    // Extract plan ID from URL
    const url = page.url();
    const match = url.match(/\/admin\/plans\/(\d+)/);
    planId = match ? parseInt(match[1]) : 0;

    await page.waitForSelector('form[data-testid="plan-form"]');
  });

  test('should edit plan name', async ({ page }) => {
    // Change name
    const newName = `Updated Plan ${Date.now()}`;
    await page.fill('input[name="name"]', newName);

    // Save changes
    await page.click('button[type="submit"]:has-text("Save")');

    // Should navigate back to list
    await page.waitForURL('/admin/plans');

    // Verify name updated
    await expect(page.locator(`[data-testid="plan-name"]:has-text("${newName}")`)).toBeVisible();
  });

  test('should update plan status', async ({ page }) => {
    // Click "Deactivate" button
    await page.click('button:has-text("Deactivate")');

    // Confirm in dialog
    await page.click('button:has-text("Confirm")');

    // Wait for status update
    await page.waitForTimeout(500);

    // Verify status badge changed
    await expect(page.locator('[data-testid="plan-status"]:has-text("inactive")')).toBeVisible();

    // Button text should change to "Activate"
    await expect(page.locator('button:has-text("Activate")')).toBeVisible();
  });

  test('should sync plan with Stripe', async ({ page }) => {
    // Click "Sync with Stripe" button
    await page.click('button:has-text("Sync with Stripe")');

    // Wait for sync to complete
    await page.waitForSelector('.toast:has-text("Synced with Stripe")');

    // Verify Stripe IDs are displayed
    await expect(page.locator('[data-testid="stripe-product-id"]')).toBeVisible();
  });

  test('should sync plan with PayPal', async ({ page }) => {
    // Click "Sync with PayPal" button
    await page.click('button:has-text("Sync with PayPal")');

    // Wait for sync to complete
    await page.waitForSelector('.toast:has-text("Synced with PayPal")');

    // Verify PayPal IDs are displayed
    await expect(page.locator('[data-testid="paypal-plan-id"]')).toBeVisible();
  });

  test('should delete plan', async ({ page }) => {
    // Click "Delete" button
    await page.click('button:has-text("Delete")');

    // Confirm deletion
    await page.click('button:has-text("Confirm Delete")');

    // Should navigate to plan list
    await page.waitForURL('/admin/plans');

    // Verify plan no longer exists (would need plan name or ID to check)
    // For now just verify we're on the list page
    await expect(page.locator('[data-testid="plan-table"]')).toBeVisible();
  });

  test('should add new feature to existing plan', async ({ page }) => {
    // Scroll to features section
    await page.locator('section:has-text("Features")').scrollIntoViewIfNeeded();

    // Add feature
    await page.click('button:has-text("Add Feature")');

    // Select feature from dropdown
    const featureSelects = page.locator('select[name^="features"]');
    const lastIndex = (await featureSelects.count()) - 1;
    await featureSelects.nth(lastIndex).selectOption('feature_new');

    // Save
    await page.click('button[type="submit"]:has-text("Save")');

    // Verify saved
    await page.waitForURL('/admin/plans');
  });

  test('should update plan limits', async ({ page }) => {
    // Update limits
    await page.fill('input[name="limits.maxUsers"]', '100');
    await page.fill('input[name="limits.maxStorage"]', '500');

    // Save
    await page.click('button[type="submit"]:has-text("Save")');

    // Navigate back to edit page
    await page.waitForURL('/admin/plans');
    await page.goto(`/admin/plans/${planId}`);

    // Verify limits were saved
    await expect(page.locator('input[name="limits.maxUsers"]')).toHaveValue('100');
    await expect(page.locator('input[name="limits.maxStorage"]')).toHaveValue('500');
  });
});
```

---

## 9. Docker Integration

### Run Tests in Docker

```bash
# Run unit tests
docker-compose run --rm frontend npm run test:unit -- plugins/plan-management

# Run E2E tests
docker-compose run --rm frontend npm run test:e2e -- plan-

# Run all tests with coverage
docker-compose run --rm frontend npm run test:coverage

# Run tests in watch mode (development)
docker-compose run --rm frontend npm run test:unit:watch -- plugins/plan-management
```

### CI/CD Integration

```yaml
# .github/workflows/test-plan-management.yml
name: Test Plan Management Plugin

on:
  push:
    paths:
      - 'frontend/admin/vue/src/plugins/plan-management/**'
  pull_request:
    paths:
      - 'frontend/admin/vue/src/plugins/plan-management/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build containers
        run: docker-compose build frontend

      - name: Run unit tests
        run: |
          docker-compose run --rm frontend npm run test:unit -- plugins/plan-management --coverage

      - name: Run E2E tests
        run: |
          docker-compose up -d
          docker-compose run --rm frontend npm run test:e2e -- plan-
          docker-compose down

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

---

## 10. Success Criteria

- [ ] Plan list displays all plans with pagination
- [ ] Create plan form with full validation
- [ ] Edit plan functionality (name, description, pricing, features, limits)
- [ ] Activate/deactivate plans
- [ ] Delete plans (soft delete)
- [ ] Multi-currency pricing support (USD, EUR, GBP, UAH)
- [ ] Feature management (add/remove features)
- [ ] Resource limits configuration
- [ ] Sync with Stripe (create products/prices)
- [ ] Sync with PayPal (create plans)
- [ ] Unit tests >90% coverage
- [ ] E2E tests cover all workflows
- [ ] All tests pass in Docker
- [ ] SOLID principles applied throughout
- [ ] LSP compliance (IPlanService interface)
- [ ] Dependency Injection in all services
- [ ] Clean code (functions <20 lines, descriptive names)
- [ ] TypeScript strict mode with no errors
- [ ] Documentation complete

---

## Next Steps (Sprint 3)

- Subscription Management: View user subscriptions
- Invoice Management: Generate and send invoices
- Payment history tracking
- Refund functionality
- Subscription lifecycle management (renewals, cancellations)
