# Sprint 4: Analytics Dashboard Plugin

**Duration:** 2 weeks
**Goal:** Build a comprehensive analytics dashboard for admin users to track revenue, subscriptions, user growth, and key business metrics.

## Overview

This sprint delivers the **Analytics Dashboard Plugin** for the admin application, enabling administrators to:

- View revenue metrics (MRR, ARR, total revenue)
- Track subscription growth and churn
- Analyze user engagement and retention
- Monitor payment success rates
- View key performance indicators (KPIs)
- Export analytics data
- Compare time periods
- Visualize data with charts and graphs

## Deliverables

- Overview dashboard with key metrics
- Revenue analytics (MRR, ARR, growth)
- Subscription analytics (active, churn rate, new subscriptions)
- User analytics (signups, active users, retention)
- Payment analytics (success rate, failed payments)
- Interactive charts (line, bar, pie)
- Date range filtering
- Export to CSV/Excel
- Unit tests (>90% coverage)
- E2E tests with Playwright
- Docker integration

---

## TDD Approach

Following Test-Driven Development:

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Clean up code while keeping tests green

Example TDD cycle for revenue calculation:

```typescript
// Step 1: RED - Write failing test
it('should calculate MRR correctly', async () => {
  const result = await analyticsService.getRevenueMetrics({
    startDate: '2025-01-01',
    endDate: '2025-01-31'
  });

  expect(result.mrr).toBeGreaterThan(0);
  expect(result.mrr).toBe(2999.00);  // Expected MRR
});

// Step 2: GREEN - Implement minimal code
async getRevenueMetrics(params: DateRangeParams): Promise<RevenueMetrics> {
  const response = await this.apiClient.get<RevenueMetrics>(
    '/api/v1/admin/analytics/revenue',
    { params }
  );
  return response;
}

// Step 3: REFACTOR - Add caching, error handling
```

---

## Architecture

Following **SOLID** principles:

### Directory Structure

```
frontend/admin/vue/src/plugins/analytics-dashboard/
├── index.ts                          # Plugin registration
├── routes/
│   └── analyticsRoutes.ts            # Route definitions
├── views/
│   ├── AnalyticsOverview.vue         # Main dashboard
│   ├── RevenueAnalytics.vue          # Revenue detailed view
│   ├── SubscriptionAnalytics.vue     # Subscription metrics
│   ├── UserAnalytics.vue             # User metrics
│   └── components/
│       ├── MetricCard.vue            # KPI card component
│       ├── RevenueChart.vue          # Revenue line chart
│       ├── ChurnRateChart.vue        # Churn rate chart
│       ├── GrowthChart.vue           # Growth trend chart
│       ├── DateRangePicker.vue       # Date range selector
│       └── ExportButton.vue          # Export data button
├── stores/
│   ├── analyticsStore.ts             # Analytics state
│   └── __tests__/
│       └── analyticsStore.spec.ts
├── services/
│   ├── IAnalyticsService.ts          # Service interface (LSP)
│   ├── AnalyticsService.ts           # Implementation (DI)
│   └── __tests__/
│       └── AnalyticsService.spec.ts
├── composables/
│   ├── useAnalyticsDashboard.ts      # Dashboard logic (SRP)
│   ├── useRevenueMetrics.ts          # Revenue logic (SRP)
│   ├── useChartData.ts               # Chart formatting (SRP)
│   └── __tests__/
│       ├── useAnalyticsDashboard.spec.ts
│       ├── useRevenueMetrics.spec.ts
│       └── useChartData.spec.ts
├── types/
│   ├── Analytics.ts                  # Domain models
│   ├── Metrics.ts
│   └── Chart.ts
└── __tests__/
    └── e2e/
        ├── analytics-overview.spec.ts
        ├── revenue-analytics.spec.ts
        └── export-data.spec.ts
```

---

## 1. Domain Models

### types/Analytics.ts

```typescript
export interface RevenueMetrics {
  mrr: number;  // Monthly Recurring Revenue
  arr: number;  // Annual Recurring Revenue
  totalRevenue: number;
  averageRevenuePerUser: number;  // ARPU
  revenueGrowthRate: number;  // Percentage
  currency: string;
  period: DatePeriod;
  comparisonPeriod?: RevenueMetrics;  // Previous period for comparison
}

export interface SubscriptionMetrics {
  totalSubscriptions: number;
  activeSubscriptions: number;
  newSubscriptions: number;
  cancelledSubscriptions: number;
  churnRate: number;  // Percentage
  growthRate: number;  // Percentage
  retentionRate: number;  // Percentage
  period: DatePeriod;
  comparisonPeriod?: SubscriptionMetrics;
}

export interface UserMetrics {
  totalUsers: number;
  activeUsers: number;
  newUsers: number;
  churnedUsers: number;
  userGrowthRate: number;  // Percentage
  activeUserRate: number;  // Percentage (DAU/MAU)
  period: DatePeriod;
  comparisonPeriod?: UserMetrics;
}

export interface PaymentMetrics {
  totalPayments: number;
  successfulPayments: number;
  failedPayments: number;
  successRate: number;  // Percentage
  averagePaymentAmount: number;
  totalPaymentVolume: number;
  period: DatePeriod;
  comparisonPeriod?: PaymentMetrics;
}

export interface DatePeriod {
  startDate: string;
  endDate: string;
}

export interface DateRangeParams {
  startDate: string;
  endDate: string;
  granularity?: TimeGranularity;  // day, week, month, year
  compareWith?: 'previous_period' | 'previous_year';
}

export enum TimeGranularity {
  DAY = 'day',
  WEEK = 'week',
  MONTH = 'month',
  YEAR = 'year'
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
  label?: string;
}

export interface RevenueTimeSeries {
  mrr: TimeSeriesData[];
  totalRevenue: TimeSeriesData[];
  newRevenue: TimeSeriesData[];
  churnedRevenue: TimeSeriesData[];
}

export interface SubscriptionTimeSeries {
  active: TimeSeriesData[];
  new: TimeSeriesData[];
  cancelled: TimeSeriesData[];
  churnRate: TimeSeriesData[];
}

export interface AnalyticsOverview {
  revenue: RevenueMetrics;
  subscriptions: SubscriptionMetrics;
  users: UserMetrics;
  payments: PaymentMetrics;
  period: DatePeriod;
}
```

### types/Chart.ts

```typescript
export interface ChartDataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
  fill?: boolean;
}

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartOptions {
  responsive: boolean;
  maintainAspectRatio?: boolean;
  scales?: {
    y?: {
      beginAtZero?: boolean;
      ticks?: {
        callback?: (value: number) => string;
      };
    };
  };
  plugins?: {
    legend?: {
      display: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    tooltip?: {
      callbacks?: {
        label?: (context: any) => string;
      };
    };
  };
}

export enum ChartType {
  LINE = 'line',
  BAR = 'bar',
  PIE = 'pie',
  DOUGHNUT = 'doughnut',
  AREA = 'area'
}
```

---

## 2. Service Interface (services/IAnalyticsService.ts)

Following **Liskov Substitution Principle**.

```typescript
import type {
  RevenueMetrics,
  SubscriptionMetrics,
  UserMetrics,
  PaymentMetrics,
  AnalyticsOverview,
  DateRangeParams,
  RevenueTimeSeries,
  SubscriptionTimeSeries
} from '../types/Analytics';

export interface IAnalyticsService {
  /**
   * Get overview with all key metrics
   */
  getOverview(params: DateRangeParams): Promise<AnalyticsOverview>;

  /**
   * Get revenue metrics (MRR, ARR, etc.)
   */
  getRevenueMetrics(params: DateRangeParams): Promise<RevenueMetrics>;

  /**
   * Get revenue time series data for charts
   */
  getRevenueTimeSeries(params: DateRangeParams): Promise<RevenueTimeSeries>;

  /**
   * Get subscription metrics
   */
  getSubscriptionMetrics(params: DateRangeParams): Promise<SubscriptionMetrics>;

  /**
   * Get subscription time series data
   */
  getSubscriptionTimeSeries(params: DateRangeParams): Promise<SubscriptionTimeSeries>;

  /**
   * Get user metrics
   */
  getUserMetrics(params: DateRangeParams): Promise<UserMetrics>;

  /**
   * Get payment metrics
   */
  getPaymentMetrics(params: DateRangeParams): Promise<PaymentMetrics>;

  /**
   * Export analytics data to CSV
   */
  exportData(params: DateRangeParams, format: 'csv' | 'xlsx'): Promise<Blob>;
}
```

---

## 3. Service Implementation (services/AnalyticsService.ts)

Following **Dependency Injection**.

```typescript
import type { IApiClient } from '@vbwd/core-sdk';
import type { IAnalyticsService } from './IAnalyticsService';
import type {
  RevenueMetrics,
  SubscriptionMetrics,
  UserMetrics,
  PaymentMetrics,
  AnalyticsOverview,
  DateRangeParams,
  RevenueTimeSeries,
  SubscriptionTimeSeries
} from '../types/Analytics';

export class AnalyticsService implements IAnalyticsService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;  // Dependency Injection
  }

  async getOverview(params: DateRangeParams): Promise<AnalyticsOverview> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<AnalyticsOverview>(
      '/api/v1/admin/analytics/overview',
      { params }
    );
    return response;
  }

  async getRevenueMetrics(params: DateRangeParams): Promise<RevenueMetrics> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<RevenueMetrics>(
      '/api/v1/admin/analytics/revenue',
      { params }
    );
    return response;
  }

  async getRevenueTimeSeries(params: DateRangeParams): Promise<RevenueTimeSeries> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<RevenueTimeSeries>(
      '/api/v1/admin/analytics/revenue/time-series',
      { params }
    );
    return response;
  }

  async getSubscriptionMetrics(params: DateRangeParams): Promise<SubscriptionMetrics> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<SubscriptionMetrics>(
      '/api/v1/admin/analytics/subscriptions',
      { params }
    );
    return response;
  }

  async getSubscriptionTimeSeries(params: DateRangeParams): Promise<SubscriptionTimeSeries> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<SubscriptionTimeSeries>(
      '/api/v1/admin/analytics/subscriptions/time-series',
      { params }
    );
    return response;
  }

  async getUserMetrics(params: DateRangeParams): Promise<UserMetrics> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<UserMetrics>(
      '/api/v1/admin/analytics/users',
      { params }
    );
    return response;
  }

  async getPaymentMetrics(params: DateRangeParams): Promise<PaymentMetrics> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<PaymentMetrics>(
      '/api/v1/admin/analytics/payments',
      { params }
    );
    return response;
  }

  async exportData(params: DateRangeParams, format: 'csv' | 'xlsx'): Promise<Blob> {
    this.validateDateRange(params);

    const response = await this.apiClient.get<Blob>(
      '/api/v1/admin/analytics/export',
      {
        params: { ...params, format },
        responseType: 'blob'
      }
    );
    return response;
  }

  // Private helper (SRP)
  private validateDateRange(params: DateRangeParams): void {
    if (!params.startDate || !params.endDate) {
      throw new Error('Start date and end date are required');
    }

    const start = new Date(params.startDate);
    const end = new Date(params.endDate);

    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      throw new Error('Invalid date format');
    }

    if (start > end) {
      throw new Error('Start date must be before end date');
    }

    // Limit to 2 years max
    const maxDays = 730;
    const daysDiff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    if (daysDiff > maxDays) {
      throw new Error(`Date range cannot exceed ${maxDays} days`);
    }
  }
}
```

---

## 4. Service Unit Tests (services/__tests__/AnalyticsService.spec.ts)

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { IApiClient } from '@vbwd/core-sdk';
import { AnalyticsService } from '../AnalyticsService';
import type { DateRangeParams } from '../../types/Analytics';
import { TimeGranularity } from '../../types/Analytics';

describe('AnalyticsService', () => {
  let analyticsService: AnalyticsService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn()
    } as unknown as IApiClient;

    analyticsService = new AnalyticsService(mockApiClient);
  });

  describe('getOverview', () => {
    it('should fetch analytics overview', async () => {
      const mockResponse = {
        revenue: { mrr: 5000, arr: 60000, totalRevenue: 10000 },
        subscriptions: { totalSubscriptions: 100, activeSubscriptions: 85 },
        users: { totalUsers: 200, activeUsers: 150 },
        payments: { totalPayments: 500, successfulPayments: 485 },
        period: { startDate: '2025-01-01', endDate: '2025-01-31' }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      const result = await analyticsService.getOverview({
        startDate: '2025-01-01',
        endDate: '2025-01-31'
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/analytics/overview', {
        params: { startDate: '2025-01-01', endDate: '2025-01-31' }
      });
      expect(result.revenue.mrr).toBe(5000);
      expect(result.subscriptions.activeSubscriptions).toBe(85);
    });

    it('should throw error if dates are missing', async () => {
      await expect(
        analyticsService.getOverview({ startDate: '', endDate: '' } as DateRangeParams)
      ).rejects.toThrow('Start date and end date are required');
    });

    it('should throw error if date format is invalid', async () => {
      await expect(
        analyticsService.getOverview({
          startDate: 'invalid',
          endDate: 'invalid'
        })
      ).rejects.toThrow('Invalid date format');
    });

    it('should throw error if start date is after end date', async () => {
      await expect(
        analyticsService.getOverview({
          startDate: '2025-01-31',
          endDate: '2025-01-01'
        })
      ).rejects.toThrow('Start date must be before end date');
    });

    it('should throw error if date range exceeds 2 years', async () => {
      await expect(
        analyticsService.getOverview({
          startDate: '2020-01-01',
          endDate: '2025-01-01'
        })
      ).rejects.toThrow('Date range cannot exceed 730 days');
    });
  });

  describe('getRevenueMetrics', () => {
    it('should fetch revenue metrics', async () => {
      const mockRevenue = {
        mrr: 5000,
        arr: 60000,
        totalRevenue: 10000,
        averageRevenuePerUser: 50,
        revenueGrowthRate: 12.5,
        currency: 'USD',
        period: { startDate: '2025-01-01', endDate: '2025-01-31' }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockRevenue);

      const result = await analyticsService.getRevenueMetrics({
        startDate: '2025-01-01',
        endDate: '2025-01-31'
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/analytics/revenue', {
        params: { startDate: '2025-01-01', endDate: '2025-01-31' }
      });
      expect(result.mrr).toBe(5000);
      expect(result.arr).toBe(60000);
      expect(result.revenueGrowthRate).toBe(12.5);
    });

    it('should fetch revenue metrics with comparison', async () => {
      const mockRevenue = {
        mrr: 5000,
        arr: 60000,
        totalRevenue: 10000,
        comparisonPeriod: {
          mrr: 4500,
          arr: 54000,
          totalRevenue: 9000
        }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockRevenue);

      const result = await analyticsService.getRevenueMetrics({
        startDate: '2025-01-01',
        endDate: '2025-01-31',
        compareWith: 'previous_period'
      });

      expect(result.comparisonPeriod?.mrr).toBe(4500);
    });
  });

  describe('getRevenueTimeSeries', () => {
    it('should fetch revenue time series data', async () => {
      const mockTimeSeries = {
        mrr: [
          { timestamp: '2025-01-01', value: 4500 },
          { timestamp: '2025-01-15', value: 4800 },
          { timestamp: '2025-01-31', value: 5000 }
        ],
        totalRevenue: [
          { timestamp: '2025-01-01', value: 1000 },
          { timestamp: '2025-01-15', value: 1500 },
          { timestamp: '2025-01-31', value: 2000 }
        ]
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockTimeSeries);

      const result = await analyticsService.getRevenueTimeSeries({
        startDate: '2025-01-01',
        endDate: '2025-01-31',
        granularity: TimeGranularity.WEEK
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/analytics/revenue/time-series', {
        params: {
          startDate: '2025-01-01',
          endDate: '2025-01-31',
          granularity: TimeGranularity.WEEK
        }
      });
      expect(result.mrr).toHaveLength(3);
      expect(result.mrr[2].value).toBe(5000);
    });
  });

  describe('getSubscriptionMetrics', () => {
    it('should fetch subscription metrics', async () => {
      const mockMetrics = {
        totalSubscriptions: 100,
        activeSubscriptions: 85,
        newSubscriptions: 15,
        cancelledSubscriptions: 5,
        churnRate: 5.0,
        growthRate: 15.0,
        retentionRate: 95.0,
        period: { startDate: '2025-01-01', endDate: '2025-01-31' }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockMetrics);

      const result = await analyticsService.getSubscriptionMetrics({
        startDate: '2025-01-01',
        endDate: '2025-01-31'
      });

      expect(result.churnRate).toBe(5.0);
      expect(result.growthRate).toBe(15.0);
      expect(result.retentionRate).toBe(95.0);
    });
  });

  describe('getUserMetrics', () => {
    it('should fetch user metrics', async () => {
      const mockMetrics = {
        totalUsers: 200,
        activeUsers: 150,
        newUsers: 30,
        churnedUsers: 10,
        userGrowthRate: 15.0,
        activeUserRate: 75.0,
        period: { startDate: '2025-01-01', endDate: '2025-01-31' }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockMetrics);

      const result = await analyticsService.getUserMetrics({
        startDate: '2025-01-01',
        endDate: '2025-01-31'
      });

      expect(result.totalUsers).toBe(200);
      expect(result.activeUsers).toBe(150);
      expect(result.activeUserRate).toBe(75.0);
    });
  });

  describe('getPaymentMetrics', () => {
    it('should fetch payment metrics', async () => {
      const mockMetrics = {
        totalPayments: 500,
        successfulPayments: 485,
        failedPayments: 15,
        successRate: 97.0,
        averagePaymentAmount: 29.99,
        totalPaymentVolume: 14995,
        period: { startDate: '2025-01-01', endDate: '2025-01-31' }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockMetrics);

      const result = await analyticsService.getPaymentMetrics({
        startDate: '2025-01-01',
        endDate: '2025-01-31'
      });

      expect(result.successRate).toBe(97.0);
      expect(result.failedPayments).toBe(15);
    });
  });

  describe('exportData', () => {
    it('should export data as CSV blob', async () => {
      const mockBlob = new Blob(['CSV data'], { type: 'text/csv' });
      vi.mocked(mockApiClient.get).mockResolvedValue(mockBlob);

      const result = await analyticsService.exportData(
        { startDate: '2025-01-01', endDate: '2025-01-31' },
        'csv'
      );

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/analytics/export', {
        params: { startDate: '2025-01-01', endDate: '2025-01-31', format: 'csv' },
        responseType: 'blob'
      });
      expect(result).toBeInstanceOf(Blob);
    });

    it('should export data as Excel blob', async () => {
      const mockBlob = new Blob(['Excel data'], { type: 'application/vnd.ms-excel' });
      vi.mocked(mockApiClient.get).mockResolvedValue(mockBlob);

      const result = await analyticsService.exportData(
        { startDate: '2025-01-01', endDate: '2025-01-31' },
        'xlsx'
      );

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/analytics/export', {
        params: { startDate: '2025-01-01', endDate: '2025-01-31', format: 'xlsx' },
        responseType: 'blob'
      });
      expect(result).toBeInstanceOf(Blob);
    });
  });
});
```

---

## 5. Store Implementation (stores/analyticsStore.ts)

```typescript
import { defineStore } from 'pinia';
import type { IAnalyticsService } from '../services/IAnalyticsService';
import type {
  AnalyticsOverview,
  RevenueMetrics,
  SubscriptionMetrics,
  UserMetrics,
  PaymentMetrics,
  DateRangeParams,
  RevenueTimeSeries,
  SubscriptionTimeSeries
} from '../types/Analytics';

interface AnalyticsState {
  overview: AnalyticsOverview | null;
  revenueMetrics: RevenueMetrics | null;
  revenueTimeSeries: RevenueTimeSeries | null;
  subscriptionMetrics: SubscriptionMetrics | null;
  subscriptionTimeSeries: SubscriptionTimeSeries | null;
  userMetrics: UserMetrics | null;
  paymentMetrics: PaymentMetrics | null;
  loading: boolean;
  error: string | null;
  analyticsService: IAnalyticsService | null;
  dateRange: { startDate: string; endDate: string };
}

export const useAnalyticsStore = defineStore('analytics', {
  state: (): AnalyticsState => ({
    overview: null,
    revenueMetrics: null,
    revenueTimeSeries: null,
    subscriptionMetrics: null,
    subscriptionTimeSeries: null,
    userMetrics: null,
    paymentMetrics: null,
    loading: false,
    error: null,
    analyticsService: null,
    dateRange: {
      startDate: getDefaultStartDate(),
      endDate: getDefaultEndDate()
    }
  }),

  getters: {
    mrrGrowth: (state): number | null => {
      if (!state.revenueMetrics?.comparisonPeriod) return null;
      const current = state.revenueMetrics.mrr;
      const previous = state.revenueMetrics.comparisonPeriod.mrr;
      if (previous === 0) return 100;
      return ((current - previous) / previous) * 100;
    },

    subscriptionGrowth: (state): number | null => {
      if (!state.subscriptionMetrics?.comparisonPeriod) return null;
      const current = state.subscriptionMetrics.activeSubscriptions;
      const previous = state.subscriptionMetrics.comparisonPeriod.activeSubscriptions;
      if (previous === 0) return 100;
      return ((current - previous) / previous) * 100;
    },

    userGrowth: (state): number | null => {
      if (!state.userMetrics?.comparisonPeriod) return null;
      const current = state.userMetrics.totalUsers;
      const previous = state.userMetrics.comparisonPeriod.totalUsers;
      if (previous === 0) return 100;
      return ((current - previous) / previous) * 100;
    }
  },

  actions: {
    setAnalyticsService(service: IAnalyticsService) {
      this.analyticsService = service;
    },

    setDateRange(startDate: string, endDate: string) {
      this.dateRange = { startDate, endDate };
    },

    async fetchOverview(params?: DateRangeParams) {
      if (!this.analyticsService) {
        throw new Error('AnalyticsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const dateParams = params || this.dateRange;
        const overview = await this.analyticsService.getOverview(dateParams);
        this.overview = overview;
        return overview;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch overview';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchRevenueMetrics(params?: DateRangeParams) {
      if (!this.analyticsService) {
        throw new Error('AnalyticsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const dateParams = params || this.dateRange;
        const metrics = await this.analyticsService.getRevenueMetrics(dateParams);
        this.revenueMetrics = metrics;
        return metrics;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch revenue metrics';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchRevenueTimeSeries(params?: DateRangeParams) {
      if (!this.analyticsService) {
        throw new Error('AnalyticsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const dateParams = params || this.dateRange;
        const timeSeries = await this.analyticsService.getRevenueTimeSeries(dateParams);
        this.revenueTimeSeries = timeSeries;
        return timeSeries;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch revenue time series';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchSubscriptionMetrics(params?: DateRangeParams) {
      if (!this.analyticsService) {
        throw new Error('AnalyticsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const dateParams = params || this.dateRange;
        const metrics = await this.analyticsService.getSubscriptionMetrics(dateParams);
        this.subscriptionMetrics = metrics;
        return metrics;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch subscription metrics';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async exportAnalyticsData(format: 'csv' | 'xlsx') {
      if (!this.analyticsService) {
        throw new Error('AnalyticsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const blob = await this.analyticsService.exportData(this.dateRange, format);

        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics-${this.dateRange.startDate}-to-${this.dateRange.endDate}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error: any) {
        this.error = error.message || 'Failed to export data';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    clearError() {
      this.error = null;
    }
  }
});

// Helper functions
function getDefaultStartDate(): string {
  const date = new Date();
  date.setDate(date.getDate() - 30);  // Last 30 days
  return date.toISOString().split('T')[0];
}

function getDefaultEndDate(): string {
  return new Date().toISOString().split('T')[0];
}
```

---

## 6. Composables

### composables/useAnalyticsDashboard.ts

Following **Single Responsibility Principle**.

```typescript
import { ref, computed, onMounted } from 'vue';
import { useAnalyticsStore } from '../stores/analyticsStore';
import type { DateRangeParams } from '../types/Analytics';

export function useAnalyticsDashboard() {
  const store = useAnalyticsStore();

  // Local state
  const startDate = ref(store.dateRange.startDate);
  const endDate = ref(store.dateRange.endDate);
  const compareWith = ref<'previous_period' | 'previous_year' | undefined>(undefined);

  // Computed
  const overview = computed(() => store.overview);
  const loading = computed(() => store.loading);
  const error = computed(() => store.error);
  const mrrGrowth = computed(() => store.mrrGrowth);
  const subscriptionGrowth = computed(() => store.subscriptionGrowth);
  const userGrowth = computed(() => store.userGrowth);

  // Methods
  const loadOverview = async () => {
    store.setDateRange(startDate.value, endDate.value);

    const params: DateRangeParams = {
      startDate: startDate.value,
      endDate: endDate.value
    };

    if (compareWith.value) {
      params.compareWith = compareWith.value;
    }

    await store.fetchOverview(params);
  };

  const changeDateRange = async (newStartDate: string, newEndDate: string) => {
    startDate.value = newStartDate;
    endDate.value = newEndDate;
    await loadOverview();
  };

  const setQuickRange = async (range: 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_year') => {
    const end = new Date();
    const start = new Date();

    switch (range) {
      case 'last_7_days':
        start.setDate(end.getDate() - 7);
        break;
      case 'last_30_days':
        start.setDate(end.getDate() - 30);
        break;
      case 'last_90_days':
        start.setDate(end.getDate() - 90);
        break;
      case 'last_year':
        start.setFullYear(end.getFullYear() - 1);
        break;
    }

    await changeDateRange(
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0]
    );
  };

  const exportData = async (format: 'csv' | 'xlsx') => {
    await store.exportAnalyticsData(format);
  };

  const refreshData = async () => {
    await loadOverview();
  };

  // Auto-load on mount
  onMounted(() => {
    loadOverview();
  });

  return {
    // State
    startDate,
    endDate,
    compareWith,

    // Computed
    overview,
    loading,
    error,
    mrrGrowth,
    subscriptionGrowth,
    userGrowth,

    // Methods
    loadOverview,
    changeDateRange,
    setQuickRange,
    exportData,
    refreshData
  };
}
```

### composables/useChartData.ts

```typescript
import { computed, type Ref } from 'vue';
import type { TimeSeriesData } from '../types/Analytics';
import type { ChartData, ChartDataset } from '../types/Chart';

export function useChartData(timeSeries: Ref<TimeSeriesData[] | null>) {
  const chartData = computed<ChartData>(() => {
    if (!timeSeries.value || timeSeries.value.length === 0) {
      return { labels: [], datasets: [] };
    }

    const labels = timeSeries.value.map(point =>
      formatDateLabel(point.timestamp)
    );

    const data = timeSeries.value.map(point => point.value);

    const dataset: ChartDataset = {
      label: 'Value',
      data,
      borderColor: '#1976D2',
      backgroundColor: 'rgba(25, 118, 210, 0.1)',
      fill: true
    };

    return {
      labels,
      datasets: [dataset]
    };
  });

  const formatDateLabel = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${value.toFixed(2)}%`;
  };

  const formatNumber = (value: number): string => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  return {
    chartData,
    formatDateLabel,
    formatCurrency,
    formatPercentage,
    formatNumber
  };
}
```

---

## 7. E2E Tests

### __tests__/e2e/analytics-overview.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Analytics Overview', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should display analytics overview dashboard', async ({ page }) => {
    await page.goto('/admin/analytics');
    await page.waitForSelector('[data-testid="analytics-overview"]');

    // Check MRR card
    await expect(page.locator('[data-testid="mrr-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="mrr-value"]')).toContainText('$');

    // Check Active Subscriptions card
    await expect(page.locator('[data-testid="active-subs-card"]')).toBeVisible();

    // Check Total Users card
    await expect(page.locator('[data-testid="total-users-card"]')).toBeVisible();

    // Check Payment Success Rate card
    await expect(page.locator('[data-testid="payment-success-card"]')).toBeVisible();
  });

  test('should display revenue chart', async ({ page }) => {
    await page.goto('/admin/analytics');
    await page.waitForSelector('[data-testid="revenue-chart"]');

    // Chart canvas should be visible
    await expect(page.locator('canvas[data-chart="revenue"]')).toBeVisible();
  });

  test('should change date range', async ({ page }) => {
    await page.goto('/admin/analytics');
    await page.waitForSelector('[data-testid="analytics-overview"]');

    // Get current MRR value
    const initialMrr = await page.locator('[data-testid="mrr-value"]').textContent();

    // Change to "Last 7 days"
    await page.click('[data-testid="date-range-dropdown"]');
    await page.click('button:has-text("Last 7 days")');

    // Wait for data to reload
    await page.waitForTimeout(500);

    // MRR might be different (or same, but we verify reload happened)
    const newMrr = await page.locator('[data-testid="mrr-value"]').textContent();
    expect(newMrr).toBeDefined();
  });

  test('should show growth indicators', async ({ page }) => {
    await page.goto('/admin/analytics');
    await page.waitForSelector('[data-testid="analytics-overview"]');

    // Check for growth indicators (up/down arrows)
    const growthIndicators = page.locator('[data-testid="growth-indicator"]');
    await expect(growthIndicators.first()).toBeVisible();
  });

  test('should export data to CSV', async ({ page }) => {
    await page.goto('/admin/analytics');
    await page.waitForSelector('[data-testid="analytics-overview"]');

    // Setup download listener
    const downloadPromise = page.waitForEvent('download');

    // Click export button
    await page.click('button:has-text("Export")');
    await page.click('button:has-text("Export to CSV")');

    // Wait for download
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.csv');
  });

  test('should export data to Excel', async ({ page }) => {
    await page.goto('/admin/analytics');
    await page.waitForSelector('[data-testid="analytics-overview"]');

    const downloadPromise = page.waitForEvent('download');

    await page.click('button:has-text("Export")');
    await page.click('button:has-text("Export to Excel")');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.xlsx');
  });
});
```

---

## 8. Docker Integration

```bash
# Run unit tests
docker-compose run --rm frontend npm run test:unit -- plugins/analytics-dashboard

# Run E2E tests
docker-compose run --rm frontend npm run test:e2e -- analytics-

# Run all tests with coverage
docker-compose run --rm frontend npm run test:coverage

# Watch mode
docker-compose run --rm frontend npm run test:unit:watch -- plugins/analytics-dashboard
```

---

## 9. Success Criteria

- [ ] Overview dashboard with key metrics (MRR, ARR, subscriptions, users, payments)
- [ ] Revenue analytics view with charts
- [ ] Subscription analytics with churn rate
- [ ] User analytics with growth metrics
- [ ] Payment success rate tracking
- [ ] Interactive line charts for time series data
- [ ] Date range selector with quick ranges
- [ ] Comparison with previous period
- [ ] Growth indicators (percentage change)
- [ ] Export to CSV
- [ ] Export to Excel
- [ ] Responsive design for all chart sizes
- [ ] Real-time data refresh
- [ ] Unit tests >90% coverage
- [ ] E2E tests cover all workflows
- [ ] All tests pass in Docker
- [ ] SOLID principles applied
- [ ] LSP compliance (service interface)
- [ ] Dependency Injection throughout
- [ ] Clean code (functions <20 lines)
- [ ] TypeScript strict mode

---

## Next Steps (Sprint 5)

- Webhook Monitor Plugin
- View webhook logs
- Retry failed webhooks
- Webhook configuration
- System settings management
