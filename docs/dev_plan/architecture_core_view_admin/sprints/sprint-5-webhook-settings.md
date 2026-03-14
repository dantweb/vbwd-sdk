# Sprint 5: Webhook Monitor & Settings

**Duration:** 1 week
**Goal:** Build webhook monitoring and system settings management for admin users to track integrations and configure platform settings.

## Overview

This sprint delivers the **Webhook Monitor & Settings Plugin** for the admin application, enabling administrators to:

- View webhook event logs
- Monitor webhook delivery status
- Retry failed webhook deliveries
- Configure webhook endpoints
- Manage system-wide settings
- Configure payment provider settings
- Manage email templates
- Set platform defaults

## Deliverables

- Webhook event log with filtering
- Webhook retry functionality
- Webhook endpoint management
- System settings interface
- Payment provider configuration
- Email template editor
- Unit tests (>90% coverage)
- E2E tests with Playwright
- Docker integration

---

## TDD Approach

Following Test-Driven Development:

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Clean up code while keeping tests green

Example TDD cycle for webhook retry:

```typescript
// Step 1: RED - Write failing test
it('should retry failed webhook', async () => {
  const result = await webhookService.retryWebhook(123);

  expect(result.status).toBe(WebhookStatus.PENDING);
  expect(result.retryCount).toBe(1);
});

// Step 2: GREEN - Implement minimal code
async retryWebhook(id: number): Promise<WebhookLog> {
  const response = await this.apiClient.post<WebhookLog>(
    `/api/v1/admin/webhooks/${id}/retry`
  );
  return response;
}

// Step 3: REFACTOR - Add validation, logging
```

---

## Architecture

Following **SOLID** principles:

### Directory Structure

```
frontend/admin/vue/src/plugins/webhook-settings/
├── index.ts                          # Plugin registration
├── routes/
│   └── webhookSettingsRoutes.ts      # Route definitions
├── views/
│   ├── WebhookLogView.vue            # Webhook log list
│   ├── WebhookDetailsView.vue        # Webhook event details
│   ├── WebhookConfigView.vue         # Webhook configuration
│   ├── SystemSettingsView.vue        # System settings
│   └── components/
│       ├── WebhookLogTable.vue       # Log table component
│       ├── WebhookRetryButton.vue    # Retry action
│       ├── SettingsForm.vue          # Settings form
│       └── PaymentProviderConfig.vue # Payment config
├── stores/
│   ├── webhookStore.ts               # Webhook state
│   ├── settingsStore.ts              # Settings state
│   └── __tests__/
│       ├── webhookStore.spec.ts
│       └── settingsStore.spec.ts
├── services/
│   ├── IWebhookService.ts            # Service interface (LSP)
│   ├── WebhookService.ts             # Implementation (DI)
│   ├── ISettingsService.ts           # Service interface (LSP)
│   ├── SettingsService.ts            # Implementation (DI)
│   └── __tests__/
│       ├── WebhookService.spec.ts
│       └── SettingsService.spec.ts
├── composables/
│   ├── useWebhookLog.ts              # Log logic (SRP)
│   ├── useSystemSettings.ts          # Settings logic (SRP)
│   └── __tests__/
│       ├── useWebhookLog.spec.ts
│       └── useSystemSettings.spec.ts
├── types/
│   ├── Webhook.ts                    # Domain models
│   └── Settings.ts
└── __tests__/
    └── e2e/
        ├── webhook-log.spec.ts
        ├── webhook-retry.spec.ts
        └── system-settings.spec.ts
```

---

## 1. Domain Models

### types/Webhook.ts

```typescript
export interface WebhookLog {
  id: number;
  eventType: WebhookEventType;
  provider: PaymentProvider;
  status: WebhookStatus;
  url: string;
  httpMethod: string;
  requestHeaders: Record<string, string>;
  requestBody: any;
  responseStatus: number | null;
  responseHeaders: Record<string, string> | null;
  responseBody: any | null;
  errorMessage: string | null;
  retryCount: number;
  nextRetryAt: string | null;
  deliveredAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export enum WebhookEventType {
  PAYMENT_SUCCEEDED = 'payment.succeeded',
  PAYMENT_FAILED = 'payment.failed',
  SUBSCRIPTION_CREATED = 'subscription.created',
  SUBSCRIPTION_UPDATED = 'subscription.updated',
  SUBSCRIPTION_CANCELLED = 'subscription.cancelled',
  INVOICE_CREATED = 'invoice.created',
  INVOICE_PAID = 'invoice.paid',
  REFUND_CREATED = 'refund.created'
}

export enum WebhookStatus {
  PENDING = 'pending',
  DELIVERED = 'delivered',
  FAILED = 'failed',
  RETRYING = 'retrying'
}

export enum PaymentProvider {
  STRIPE = 'stripe',
  PAYPAL = 'paypal'
}

export interface GetWebhookLogsParams {
  page?: number;
  limit?: number;
  eventType?: WebhookEventType;
  status?: WebhookStatus;
  provider?: PaymentProvider;
  startDate?: string;
  endDate?: string;
  sortBy?: 'createdAt' | 'deliveredAt';
  sortOrder?: 'asc' | 'desc';
}

export interface WebhookEndpoint {
  id: number;
  url: string;
  enabled: boolean;
  eventTypes: WebhookEventType[];
  secret: string;
  createdAt: string;
  updatedAt: string;
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

### types/Settings.ts

```typescript
export interface SystemSettings {
  id: number;
  siteName: string;
  siteUrl: string;
  supportEmail: string;
  defaultCurrency: string;
  defaultLanguage: string;
  timezone: string;
  enableRegistration: boolean;
  requireEmailVerification: boolean;
  sessionTimeout: number;  // minutes
  maxLoginAttempts: number;
  maintenanceMode: boolean;
  updatedAt: string;
  updatedBy: string;
}

export interface PaymentProviderSettings {
  id: number;
  provider: PaymentProvider;
  enabled: boolean;
  testMode: boolean;
  publicKey: string;
  secretKey: string;  // Masked in frontend
  webhookSecret: string;  // Masked in frontend
  config: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  bodyHtml: string;
  bodyText: string;
  variables: string[];  // Available template variables
  category: EmailCategory;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export enum EmailCategory {
  TRANSACTIONAL = 'transactional',
  MARKETING = 'marketing',
  SYSTEM = 'system'
}

export interface UpdateSystemSettingsData {
  siteName?: string;
  siteUrl?: string;
  supportEmail?: string;
  defaultCurrency?: string;
  defaultLanguage?: string;
  timezone?: string;
  enableRegistration?: boolean;
  requireEmailVerification?: boolean;
  sessionTimeout?: number;
  maxLoginAttempts?: number;
  maintenanceMode?: boolean;
}

export interface UpdatePaymentProviderData {
  enabled?: boolean;
  testMode?: boolean;
  publicKey?: string;
  secretKey?: string;
  webhookSecret?: string;
  config?: Record<string, any>;
}
```

---

## 2. Service Interfaces (LSP)

### services/IWebhookService.ts

```typescript
import type {
  WebhookLog,
  GetWebhookLogsParams,
  WebhookEndpoint,
  PaginatedResponse
} from '../types/Webhook';

export interface IWebhookService {
  /**
   * Get paginated webhook logs
   */
  getWebhookLogs(params: GetWebhookLogsParams): Promise<PaginatedResponse<WebhookLog>>;

  /**
   * Get webhook log by ID
   */
  getWebhookLogById(id: number): Promise<WebhookLog>;

  /**
   * Retry failed webhook delivery
   */
  retryWebhook(id: number): Promise<WebhookLog>;

  /**
   * Get webhook endpoints
   */
  getWebhookEndpoints(): Promise<WebhookEndpoint[]>;

  /**
   * Create webhook endpoint
   */
  createWebhookEndpoint(url: string, eventTypes: string[]): Promise<WebhookEndpoint>;

  /**
   * Delete webhook endpoint
   */
  deleteWebhookEndpoint(id: number): Promise<void>;
}
```

### services/ISettingsService.ts

```typescript
import type {
  SystemSettings,
  PaymentProviderSettings,
  EmailTemplate,
  UpdateSystemSettingsData,
  UpdatePaymentProviderData
} from '../types/Settings';

export interface ISettingsService {
  /**
   * Get system settings
   */
  getSystemSettings(): Promise<SystemSettings>;

  /**
   * Update system settings
   */
  updateSystemSettings(data: UpdateSystemSettingsData): Promise<SystemSettings>;

  /**
   * Get payment provider settings
   */
  getPaymentProviderSettings(provider: string): Promise<PaymentProviderSettings>;

  /**
   * Update payment provider settings
   */
  updatePaymentProviderSettings(
    provider: string,
    data: UpdatePaymentProviderData
  ): Promise<PaymentProviderSettings>;

  /**
   * Get email templates
   */
  getEmailTemplates(): Promise<EmailTemplate[]>;

  /**
   * Update email template
   */
  updateEmailTemplate(id: number, data: Partial<EmailTemplate>): Promise<EmailTemplate>;
}
```

---

## 3. Service Implementations (DI)

### services/WebhookService.ts

```typescript
import type { IApiClient } from '@vbwd/core-sdk';
import type { IWebhookService } from './IWebhookService';
import type {
  WebhookLog,
  GetWebhookLogsParams,
  WebhookEndpoint,
  PaginatedResponse
} from '../types/Webhook';

export class WebhookService implements IWebhookService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;  // Dependency Injection
  }

  async getWebhookLogs(params: GetWebhookLogsParams): Promise<PaginatedResponse<WebhookLog>> {
    const response = await this.apiClient.get<PaginatedResponse<WebhookLog>>(
      '/api/v1/admin/webhooks',
      { params }
    );
    return response;
  }

  async getWebhookLogById(id: number): Promise<WebhookLog> {
    const response = await this.apiClient.get<WebhookLog>(
      `/api/v1/admin/webhooks/${id}`
    );
    return response;
  }

  async retryWebhook(id: number): Promise<WebhookLog> {
    const response = await this.apiClient.post<WebhookLog>(
      `/api/v1/admin/webhooks/${id}/retry`
    );
    return response;
  }

  async getWebhookEndpoints(): Promise<WebhookEndpoint[]> {
    const response = await this.apiClient.get<WebhookEndpoint[]>(
      '/api/v1/admin/webhook-endpoints'
    );
    return response;
  }

  async createWebhookEndpoint(url: string, eventTypes: string[]): Promise<WebhookEndpoint> {
    // Validation
    if (!url || !this.isValidUrl(url)) {
      throw new Error('Valid URL is required');
    }

    if (!eventTypes || eventTypes.length === 0) {
      throw new Error('At least one event type is required');
    }

    const response = await this.apiClient.post<WebhookEndpoint>(
      '/api/v1/admin/webhook-endpoints',
      { url, eventTypes }
    );
    return response;
  }

  async deleteWebhookEndpoint(id: number): Promise<void> {
    await this.apiClient.delete(`/api/v1/admin/webhook-endpoints/${id}`);
  }

  // Private helper (SRP)
  private isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }
}
```

### services/SettingsService.ts

```typescript
import type { IApiClient } from '@vbwd/core-sdk';
import type { ISettingsService } from './ISettingsService';
import type {
  SystemSettings,
  PaymentProviderSettings,
  EmailTemplate,
  UpdateSystemSettingsData,
  UpdatePaymentProviderData
} from '../types/Settings';

export class SettingsService implements ISettingsService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;  // Dependency Injection
  }

  async getSystemSettings(): Promise<SystemSettings> {
    const response = await this.apiClient.get<SystemSettings>(
      '/api/v1/admin/settings/system'
    );
    return response;
  }

  async updateSystemSettings(data: UpdateSystemSettingsData): Promise<SystemSettings> {
    if (Object.keys(data).length === 0) {
      throw new Error('No data provided for update');
    }

    // Validate email if provided
    if (data.supportEmail && !this.isValidEmail(data.supportEmail)) {
      throw new Error('Invalid email address');
    }

    // Validate URL if provided
    if (data.siteUrl && !this.isValidUrl(data.siteUrl)) {
      throw new Error('Invalid site URL');
    }

    const response = await this.apiClient.put<SystemSettings>(
      '/api/v1/admin/settings/system',
      data
    );
    return response;
  }

  async getPaymentProviderSettings(provider: string): Promise<PaymentProviderSettings> {
    const response = await this.apiClient.get<PaymentProviderSettings>(
      `/api/v1/admin/settings/payment-providers/${provider}`
    );
    return response;
  }

  async updatePaymentProviderSettings(
    provider: string,
    data: UpdatePaymentProviderData
  ): Promise<PaymentProviderSettings> {
    if (Object.keys(data).length === 0) {
      throw new Error('No data provided for update');
    }

    const response = await this.apiClient.put<PaymentProviderSettings>(
      `/api/v1/admin/settings/payment-providers/${provider}`,
      data
    );
    return response;
  }

  async getEmailTemplates(): Promise<EmailTemplate[]> {
    const response = await this.apiClient.get<EmailTemplate[]>(
      '/api/v1/admin/settings/email-templates'
    );
    return response;
  }

  async updateEmailTemplate(id: number, data: Partial<EmailTemplate>): Promise<EmailTemplate> {
    if (Object.keys(data).length === 0) {
      throw new Error('No data provided for update');
    }

    const response = await this.apiClient.put<EmailTemplate>(
      `/api/v1/admin/settings/email-templates/${id}`,
      data
    );
    return response;
  }

  // Private helpers (SRP)
  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }
}
```

---

## 4. Service Unit Tests

### services/__tests__/WebhookService.spec.ts

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { IApiClient } from '@vbwd/core-sdk';
import { WebhookService } from '../WebhookService';
import { WebhookStatus, WebhookEventType } from '../../types/Webhook';

describe('WebhookService', () => {
  let webhookService: WebhookService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn()
    } as unknown as IApiClient;

    webhookService = new WebhookService(mockApiClient);
  });

  describe('getWebhookLogs', () => {
    it('should fetch webhook logs', async () => {
      const mockResponse = {
        data: [
          { id: 1, eventType: WebhookEventType.PAYMENT_SUCCEEDED, status: WebhookStatus.DELIVERED },
          { id: 2, eventType: WebhookEventType.PAYMENT_FAILED, status: WebhookStatus.FAILED }
        ],
        pagination: { page: 1, limit: 25, total: 2, totalPages: 1 }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      const result = await webhookService.getWebhookLogs({ page: 1, limit: 25 });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/webhooks', {
        params: { page: 1, limit: 25 }
      });
      expect(result.data).toHaveLength(2);
    });

    it('should filter by status', async () => {
      const mockResponse = {
        data: [{ id: 1, status: WebhookStatus.FAILED }],
        pagination: { page: 1, limit: 25, total: 1, totalPages: 1 }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      await webhookService.getWebhookLogs({ status: WebhookStatus.FAILED });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/webhooks', {
        params: { status: WebhookStatus.FAILED }
      });
    });
  });

  describe('retryWebhook', () => {
    it('should retry failed webhook', async () => {
      const mockResponse = {
        id: 1,
        status: WebhookStatus.PENDING,
        retryCount: 1
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      const result = await webhookService.retryWebhook(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/webhooks/1/retry');
      expect(result.status).toBe(WebhookStatus.PENDING);
      expect(result.retryCount).toBe(1);
    });
  });

  describe('createWebhookEndpoint', () => {
    it('should create webhook endpoint', async () => {
      const mockResponse = {
        id: 1,
        url: 'https://example.com/webhook',
        eventTypes: [WebhookEventType.PAYMENT_SUCCEEDED],
        enabled: true
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      const result = await webhookService.createWebhookEndpoint(
        'https://example.com/webhook',
        [WebhookEventType.PAYMENT_SUCCEEDED]
      );

      expect(result.id).toBe(1);
      expect(result.url).toBe('https://example.com/webhook');
    });

    it('should throw error if URL is invalid', async () => {
      await expect(
        webhookService.createWebhookEndpoint('invalid-url', [WebhookEventType.PAYMENT_SUCCEEDED])
      ).rejects.toThrow('Valid URL is required');
    });

    it('should throw error if no event types', async () => {
      await expect(
        webhookService.createWebhookEndpoint('https://example.com/webhook', [])
      ).rejects.toThrow('At least one event type is required');
    });
  });
});
```

### services/__tests__/SettingsService.spec.ts

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { IApiClient } from '@vbwd/core-sdk';
import { SettingsService } from '../SettingsService';
import type { UpdateSystemSettingsData } from '../../types/Settings';

describe('SettingsService', () => {
  let settingsService: SettingsService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn(),
      put: vi.fn()
    } as unknown as IApiClient;

    settingsService = new SettingsService(mockApiClient);
  });

  describe('getSystemSettings', () => {
    it('should fetch system settings', async () => {
      const mockSettings = {
        id: 1,
        siteName: 'VBWD Platform',
        siteUrl: 'https://vbwd.com',
        supportEmail: 'support@vbwd.com',
        defaultCurrency: 'USD'
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockSettings);

      const result = await settingsService.getSystemSettings();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/settings/system');
      expect(result.siteName).toBe('VBWD Platform');
    });
  });

  describe('updateSystemSettings', () => {
    it('should update system settings', async () => {
      const updateData: UpdateSystemSettingsData = {
        siteName: 'New Platform Name',
        supportEmail: 'newsupport@vbwd.com'
      };

      const mockResponse = {
        id: 1,
        ...updateData,
        updatedAt: '2025-12-20T10:00:00Z'
      };
      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      const result = await settingsService.updateSystemSettings(updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/api/v1/admin/settings/system', updateData);
      expect(result.siteName).toBe('New Platform Name');
    });

    it('should throw error if no data provided', async () => {
      await expect(settingsService.updateSystemSettings({})).rejects.toThrow(
        'No data provided for update'
      );
    });

    it('should throw error if email is invalid', async () => {
      await expect(
        settingsService.updateSystemSettings({ supportEmail: 'invalid-email' })
      ).rejects.toThrow('Invalid email address');
    });

    it('should throw error if URL is invalid', async () => {
      await expect(
        settingsService.updateSystemSettings({ siteUrl: 'not-a-url' })
      ).rejects.toThrow('Invalid site URL');
    });
  });

  describe('updatePaymentProviderSettings', () => {
    it('should update payment provider settings', async () => {
      const updateData = {
        enabled: true,
        testMode: false,
        publicKey: 'pk_live_123'
      };

      const mockResponse = {
        id: 1,
        provider: 'stripe',
        ...updateData,
        updatedAt: '2025-12-20T10:00:00Z'
      };
      vi.mocked(mockApiClient.put).mockResolvedValue(mockResponse);

      const result = await settingsService.updatePaymentProviderSettings('stripe', updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith(
        '/api/v1/admin/settings/payment-providers/stripe',
        updateData
      );
      expect(result.enabled).toBe(true);
    });
  });

  describe('getEmailTemplates', () => {
    it('should fetch email templates', async () => {
      const mockTemplates = [
        { id: 1, name: 'Welcome Email', subject: 'Welcome!', enabled: true },
        { id: 2, name: 'Password Reset', subject: 'Reset Password', enabled: true }
      ];
      vi.mocked(mockApiClient.get).mockResolvedValue(mockTemplates);

      const result = await settingsService.getEmailTemplates();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/settings/email-templates');
      expect(result).toHaveLength(2);
    });
  });
});
```

---

## 5. Store Implementations

### stores/webhookStore.ts

```typescript
import { defineStore } from 'pinia';
import type { IWebhookService } from '../services/IWebhookService';
import type {
  WebhookLog,
  GetWebhookLogsParams,
  WebhookEndpoint
} from '../types/Webhook';

interface WebhookState {
  logs: WebhookLog[];
  selectedLog: WebhookLog | null;
  endpoints: WebhookEndpoint[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  webhookService: IWebhookService | null;
}

export const useWebhookStore = defineStore('webhook', {
  state: (): WebhookState => ({
    logs: [],
    selectedLog: null,
    endpoints: [],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: 25,
      total: 0,
      totalPages: 0
    },
    webhookService: null
  }),

  getters: {
    failedLogs: (state) => state.logs.filter(log => log.status === 'failed'),
    deliveredLogs: (state) => state.logs.filter(log => log.status === 'delivered')
  },

  actions: {
    setWebhookService(service: IWebhookService) {
      this.webhookService = service;
    },

    async fetchWebhookLogs(params: GetWebhookLogsParams = {}) {
      if (!this.webhookService) {
        throw new Error('WebhookService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const response = await this.webhookService.getWebhookLogs({
          page: this.pagination.page,
          limit: this.pagination.limit,
          ...params
        });

        this.logs = response.data;
        this.pagination = response.pagination;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch webhook logs';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async retryWebhook(id: number) {
      if (!this.webhookService) {
        throw new Error('WebhookService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const updated = await this.webhookService.retryWebhook(id);

        // Update in list
        const index = this.logs.findIndex(log => log.id === id);
        if (index !== -1) {
          this.logs[index] = updated;
        }

        return updated;
      } catch (error: any) {
        this.error = error.message || 'Failed to retry webhook';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchWebhookEndpoints() {
      if (!this.webhookService) {
        throw new Error('WebhookService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const endpoints = await this.webhookService.getWebhookEndpoints();
        this.endpoints = endpoints;
        return endpoints;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch endpoints';
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
```

### stores/settingsStore.ts

```typescript
import { defineStore } from 'pinia';
import type { ISettingsService } from '../services/ISettingsService';
import type {
  SystemSettings,
  PaymentProviderSettings,
  EmailTemplate,
  UpdateSystemSettingsData
} from '../types/Settings';

interface SettingsState {
  systemSettings: SystemSettings | null;
  paymentProviders: Record<string, PaymentProviderSettings>;
  emailTemplates: EmailTemplate[];
  loading: boolean;
  error: string | null;
  settingsService: ISettingsService | null;
}

export const useSettingsStore = defineStore('settings', {
  state: (): SettingsState => ({
    systemSettings: null,
    paymentProviders: {},
    emailTemplates: [],
    loading: false,
    error: null,
    settingsService: null
  }),

  actions: {
    setSettingsService(service: ISettingsService) {
      this.settingsService = service;
    },

    async fetchSystemSettings() {
      if (!this.settingsService) {
        throw new Error('SettingsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const settings = await this.settingsService.getSystemSettings();
        this.systemSettings = settings;
        return settings;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch system settings';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateSystemSettings(data: UpdateSystemSettingsData) {
      if (!this.settingsService) {
        throw new Error('SettingsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const updated = await this.settingsService.updateSystemSettings(data);
        this.systemSettings = updated;
        return updated;
      } catch (error: any) {
        this.error = error.message || 'Failed to update settings';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchPaymentProviderSettings(provider: string) {
      if (!this.settingsService) {
        throw new Error('SettingsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const settings = await this.settingsService.getPaymentProviderSettings(provider);
        this.paymentProviders[provider] = settings;
        return settings;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch payment provider settings';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchEmailTemplates() {
      if (!this.settingsService) {
        throw new Error('SettingsService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const templates = await this.settingsService.getEmailTemplates();
        this.emailTemplates = templates;
        return templates;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch email templates';
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
```

---

## 6. E2E Tests

### __tests__/e2e/webhook-log.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Webhook Log', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should display webhook log list', async ({ page }) => {
    await page.goto('/admin/webhooks');
    await page.waitForSelector('[data-testid="webhook-log-table"]');

    await expect(page.locator('th:has-text("Event Type")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
    await expect(page.locator('th:has-text("Provider")')).toBeVisible();

    const rows = page.locator('[data-testid="webhook-log-row"]');
    await expect(rows).toHaveCountGreaterThan(0);
  });

  test('should filter logs by status', async ({ page }) => {
    await page.goto('/admin/webhooks');
    await page.waitForSelector('[data-testid="webhook-log-table"]');

    await page.selectOption('select[data-testid="status-filter"]', 'failed');
    await page.click('button:has-text("Apply Filters")');

    await page.waitForTimeout(500);

    const statusBadges = page.locator('[data-testid="webhook-status"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      const text = await statusBadges.nth(i).textContent();
      expect(text?.toLowerCase()).toContain('failed');
    }
  });

  test('should view webhook details', async ({ page }) => {
    await page.goto('/admin/webhooks');
    await page.waitForSelector('[data-testid="webhook-log-table"]');

    await page.click('[data-testid="webhook-log-row"]:first-child');

    await page.waitForSelector('[data-testid="webhook-details"]');
    await expect(page.locator('[data-testid="request-body"]')).toBeVisible();
    await expect(page.locator('[data-testid="response-body"]')).toBeVisible();
  });
});
```

### __tests__/e2e/webhook-retry.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Webhook Retry', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should retry failed webhook', async ({ page }) => {
    await page.goto('/admin/webhooks');
    await page.waitForSelector('[data-testid="webhook-log-table"]');

    // Filter for failed webhooks
    await page.selectOption('select[data-testid="status-filter"]', 'failed');
    await page.click('button:has-text("Apply Filters")');
    await page.waitForTimeout(500);

    // Click retry button on first failed webhook
    await page.click('[data-testid="retry-webhook-button"]:first-child');

    // Verify success message
    await page.waitForSelector('.toast:has-text("Webhook retry initiated")');

    // Status should change to "retrying" or "pending"
    const status = await page.locator('[data-testid="webhook-status"]:first-child').textContent();
    expect(status?.toLowerCase()).toMatch(/retrying|pending/);
  });
});
```

### __tests__/e2e/system-settings.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('System Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should display system settings form', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.waitForSelector('[data-testid="settings-form"]');

    await expect(page.locator('input[name="siteName"]')).toBeVisible();
    await expect(page.locator('input[name="supportEmail"]')).toBeVisible();
    await expect(page.locator('select[name="defaultCurrency"]')).toBeVisible();
  });

  test('should update system settings', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.waitForSelector('[data-testid="settings-form"]');

    // Update site name
    await page.fill('input[name="siteName"]', 'Updated Platform Name');

    // Save changes
    await page.click('button:has-text("Save Settings")');

    // Verify success message
    await page.waitForSelector('.toast:has-text("Settings updated")');

    // Reload and verify change persisted
    await page.reload();
    await page.waitForSelector('[data-testid="settings-form"]');

    const siteNameValue = await page.locator('input[name="siteName"]').inputValue();
    expect(siteNameValue).toBe('Updated Platform Name');
  });

  test('should show validation error for invalid email', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.waitForSelector('[data-testid="settings-form"]');

    await page.fill('input[name="supportEmail"]', 'invalid-email');
    await page.click('button:has-text("Save Settings")');

    await expect(page.locator('.error:has-text("email")')).toBeVisible();
  });
});
```

---

## 7. Docker Integration

```bash
# Run unit tests
docker-compose run --rm frontend npm run test:unit -- plugins/webhook-settings

# Run E2E tests
docker-compose run --rm frontend npm run test:e2e -- webhook- system-settings

# Run all tests with coverage
docker-compose run --rm frontend npm run test:coverage

# Watch mode
docker-compose run --rm frontend npm run test:unit:watch -- plugins/webhook-settings
```

---

## 8. Success Criteria

- [ ] Webhook log list with pagination
- [ ] Filter webhooks by status, event type, provider
- [ ] View webhook details (request/response)
- [ ] Retry failed webhook deliveries
- [ ] Webhook endpoint management
- [ ] System settings interface
- [ ] Payment provider configuration (Stripe, PayPal)
- [ ] Email template management
- [ ] Input validation and error handling
- [ ] Unit tests >90% coverage
- [ ] E2E tests cover all workflows
- [ ] All tests pass in Docker
- [ ] SOLID principles applied
- [ ] LSP compliance (service interfaces)
- [ ] Dependency Injection throughout
- [ ] Clean code (functions <20 lines)
- [ ] TypeScript strict mode
- [ ] Settings changes logged for audit

---

## Conclusion

All 5 sprints for the Admin application are now complete:

1. **Sprint 1**: User Management Plugin (2 weeks)
2. **Sprint 2**: Plan Management Plugin (2 weeks)
3. **Sprint 3**: Subscription & Invoice Management (2 weeks)
4. **Sprint 4**: Analytics Dashboard Plugin (2 weeks)
5. **Sprint 5**: Webhook Monitor & Settings (1 week)

**Total Duration**: 9 weeks

Each sprint follows:
- TDD methodology (Red-Green-Refactor)
- SOLID principles (SRP, OCP, LSP, ISP, DI)
- Clean code practices
- Dockerized environment
- >90% test coverage
- Full TypeScript type safety
