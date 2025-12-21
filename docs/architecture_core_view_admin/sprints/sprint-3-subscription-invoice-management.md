# Sprint 3: Subscription & Invoice Management

**Duration:** 2 weeks
**Goal:** Build comprehensive subscription and invoice management functionality for admin users to view, manage, and control user subscriptions and billing.

## Overview

This sprint delivers the **Subscription & Invoice Management Plugin** for the admin application, enabling administrators to:

- View all user subscriptions (active, expired, cancelled)
- Manage subscription lifecycle (cancel, renew, upgrade/downgrade)
- View and generate invoices
- Process refunds
- View payment history
- Handle failed payments
- Export invoice data

## Deliverables

- Subscription list view with advanced filtering
- Subscription details view with full history
- Invoice list and detail views
- Invoice generation and PDF export
- Refund processing interface
- Payment history timeline
- Failed payment management
- Unit tests (>90% coverage)
- E2E tests with Playwright
- Docker integration

---

## TDD Approach

Following Test-Driven Development:

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Clean up code while keeping tests green

Example TDD cycle for subscription cancellation:

```typescript
// Step 1: RED - Write failing test
it('should cancel subscription', async () => {
  const result = await subscriptionService.cancelSubscription(123, {
    reason: 'customer_request',
    immediate: false
  });

  expect(result.status).toBe(SubscriptionStatus.CANCELLED);
  expect(result.cancelledAt).toBeDefined();
});

// Step 2: GREEN - Implement minimal code
async cancelSubscription(id: number, data: CancelSubscriptionData): Promise<Subscription> {
  const response = await this.apiClient.post<Subscription>(
    `/api/v1/admin/subscriptions/${id}/cancel`,
    data
  );
  return response;
}

// Step 3: REFACTOR - Add validation, error handling, logging
```

---

## Architecture

Following **SOLID** principles:

### Directory Structure

```
frontend/admin/vue/src/plugins/subscription-invoice-management/
├── index.ts                          # Plugin registration
├── routes/
│   └── subscriptionInvoiceRoutes.ts  # Route definitions
├── views/
│   ├── SubscriptionListView.vue      # Subscription list
│   ├── SubscriptionDetailsView.vue   # Subscription details
│   ├── InvoiceListView.vue           # Invoice list
│   ├── InvoiceDetailsView.vue        # Invoice details
│   └── components/
│       ├── SubscriptionCard.vue      # Subscription display
│       ├── PaymentTimeline.vue       # Payment history
│       ├── InvoiceTable.vue          # Invoice table
│       ├── RefundModal.vue           # Refund processing
│       └── SubscriptionActions.vue   # Cancel/renew actions
├── stores/
│   ├── subscriptionStore.ts          # Subscription state
│   ├── invoiceStore.ts               # Invoice state
│   └── __tests__/
│       ├── subscriptionStore.spec.ts
│       └── invoiceStore.spec.ts
├── services/
│   ├── ISubscriptionService.ts       # Service interface (LSP)
│   ├── SubscriptionService.ts        # Implementation (DI)
│   ├── IInvoiceService.ts            # Service interface (LSP)
│   ├── InvoiceService.ts             # Implementation (DI)
│   └── __tests__/
│       ├── SubscriptionService.spec.ts
│       └── InvoiceService.spec.ts
├── composables/
│   ├── useSubscriptionList.ts        # List logic (SRP)
│   ├── useSubscriptionDetails.ts     # Details logic (SRP)
│   ├── useInvoiceList.ts             # Invoice list (SRP)
│   └── __tests__/
│       ├── useSubscriptionList.spec.ts
│       ├── useSubscriptionDetails.spec.ts
│       └── useInvoiceList.spec.ts
├── types/
│   ├── Subscription.ts               # Domain models
│   ├── Invoice.ts
│   └── Payment.ts
└── __tests__/
    └── e2e/
        ├── subscription-list.spec.ts
        ├── subscription-actions.spec.ts
        ├── invoice-list.spec.ts
        └── refund-processing.spec.ts
```

---

## 1. Domain Models

### types/Subscription.ts

```typescript
export interface Subscription {
  id: number;
  userId: number;
  planId: number;
  status: SubscriptionStatus;
  startDate: string;
  endDate: string | null;
  cancelledAt: string | null;
  cancellationReason: string | null;
  renewalDate: string | null;
  trialEndDate: string | null;
  paymentProvider: PaymentProvider;
  providerSubscriptionId: string;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  createdAt: string;
  updatedAt: string;

  // Relationships
  user?: {
    id: number;
    email: string;
    name: string;
  };
  plan?: {
    id: number;
    name: string;
    amount: number;
    currency: string;
    billingPeriod: string;
  };
}

export enum SubscriptionStatus {
  ACTIVE = 'active',
  TRIALING = 'trialing',
  PAST_DUE = 'past_due',
  CANCELLED = 'cancelled',
  EXPIRED = 'expired',
  PAUSED = 'paused'
}

export enum PaymentProvider {
  STRIPE = 'stripe',
  PAYPAL = 'paypal'
}

export interface GetSubscriptionsParams {
  page?: number;
  limit?: number;
  status?: SubscriptionStatus;
  userId?: number;
  planId?: number;
  provider?: PaymentProvider;
  sortBy?: 'createdAt' | 'endDate' | 'renewalDate';
  sortOrder?: 'asc' | 'desc';
  search?: string;  // Search by user email
}

export interface CancelSubscriptionData {
  reason: string;
  immediate: boolean;  // Cancel now or at period end
  refundAmount?: number;  // Partial refund
}

export interface UpdateSubscriptionData {
  planId?: number;  // Change plan (upgrade/downgrade)
  endDate?: string;  // Extend or shorten
  status?: SubscriptionStatus;
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

### types/Invoice.ts

```typescript
export interface Invoice {
  id: number;
  userId: number;
  subscriptionId: number | null;
  invoiceNumber: string;
  amount: number;
  currency: string;
  taxAmount: number;
  totalAmount: number;
  status: InvoiceStatus;
  dueDate: string;
  paidAt: string | null;
  voidedAt: string | null;
  paymentProvider: PaymentProvider;
  providerInvoiceId: string;
  pdfUrl: string | null;
  createdAt: string;
  updatedAt: string;

  // Relationships
  user?: {
    id: number;
    email: string;
    name: string;
  };
  subscription?: {
    id: number;
    planName: string;
  };
  lineItems?: InvoiceLineItem[];
}

export enum InvoiceStatus {
  DRAFT = 'draft',
  OPEN = 'open',
  PAID = 'paid',
  VOID = 'void',
  UNCOLLECTIBLE = 'uncollectible'
}

export interface InvoiceLineItem {
  id: number;
  description: string;
  quantity: number;
  unitAmount: number;
  amount: number;
  currency: string;
}

export interface GetInvoicesParams {
  page?: number;
  limit?: number;
  status?: InvoiceStatus;
  userId?: number;
  subscriptionId?: number;
  sortBy?: 'createdAt' | 'dueDate' | 'amount';
  sortOrder?: 'asc' | 'desc';
  search?: string;  // Search by invoice number or user email
}

export interface CreateInvoiceData {
  userId: number;
  subscriptionId?: number;
  amount: number;
  currency: string;
  taxAmount?: number;
  dueDate: string;
  lineItems: Omit<InvoiceLineItem, 'id'>[];
}
```

### types/Payment.ts

```typescript
export interface Payment {
  id: number;
  userId: number;
  subscriptionId: number | null;
  invoiceId: number | null;
  amount: number;
  currency: string;
  status: PaymentStatus;
  paymentMethod: string;
  paymentProvider: PaymentProvider;
  providerPaymentId: string;
  failureReason: string | null;
  refundedAmount: number;
  createdAt: string;
  updatedAt: string;
}

export enum PaymentStatus {
  PENDING = 'pending',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
  REFUNDED = 'refunded',
  PARTIALLY_REFUNDED = 'partially_refunded'
}

export interface RefundData {
  amount: number;  // Amount to refund (can be partial)
  reason: string;
  notifyCustomer: boolean;
}

export interface GetPaymentsParams {
  page?: number;
  limit?: number;
  status?: PaymentStatus;
  userId?: number;
  subscriptionId?: number;
  sortBy?: 'createdAt' | 'amount';
  sortOrder?: 'asc' | 'desc';
}
```

---

## 2. Service Interfaces (LSP)

### services/ISubscriptionService.ts

```typescript
import type {
  Subscription,
  GetSubscriptionsParams,
  CancelSubscriptionData,
  UpdateSubscriptionData,
  PaginatedResponse
} from '../types/Subscription';
import type { Payment, GetPaymentsParams } from '../types/Payment';

export interface ISubscriptionService {
  /**
   * Get paginated list of subscriptions
   */
  getSubscriptions(params: GetSubscriptionsParams): Promise<PaginatedResponse<Subscription>>;

  /**
   * Get subscription by ID with full details
   */
  getSubscriptionById(id: number): Promise<Subscription>;

  /**
   * Cancel subscription
   */
  cancelSubscription(id: number, data: CancelSubscriptionData): Promise<Subscription>;

  /**
   * Update subscription (change plan, extend, etc.)
   */
  updateSubscription(id: number, data: UpdateSubscriptionData): Promise<Subscription>;

  /**
   * Reactivate cancelled subscription
   */
  reactivateSubscription(id: number): Promise<Subscription>;

  /**
   * Get payment history for subscription
   */
  getSubscriptionPayments(id: number, params: GetPaymentsParams): Promise<PaginatedResponse<Payment>>;

  /**
   * Retry failed payment
   */
  retryPayment(subscriptionId: number): Promise<Payment>;
}
```

### services/IInvoiceService.ts

```typescript
import type {
  Invoice,
  GetInvoicesParams,
  CreateInvoiceData,
  PaginatedResponse
} from '../types/Invoice';
import type { RefundData, Payment } from '../types/Payment';

export interface IInvoiceService {
  /**
   * Get paginated list of invoices
   */
  getInvoices(params: GetInvoicesParams): Promise<PaginatedResponse<Invoice>>;

  /**
   * Get invoice by ID with full details
   */
  getInvoiceById(id: number): Promise<Invoice>;

  /**
   * Create new invoice
   */
  createInvoice(data: CreateInvoiceData): Promise<Invoice>;

  /**
   * Void invoice
   */
  voidInvoice(id: number): Promise<Invoice>;

  /**
   * Mark invoice as paid
   */
  markInvoiceAsPaid(id: number): Promise<Invoice>;

  /**
   * Download invoice PDF
   */
  downloadInvoicePdf(id: number): Promise<Blob>;

  /**
   * Get payment for invoice
   */
  getInvoicePayment(invoiceId: number): Promise<Payment>;

  /**
   * Process refund for payment
   */
  processRefund(paymentId: number, data: RefundData): Promise<Payment>;
}
```

---

## 3. Service Implementations (DI)

### services/SubscriptionService.ts

```typescript
import type { IApiClient } from '@vbwd/core-sdk';
import type { ISubscriptionService } from './ISubscriptionService';
import type {
  Subscription,
  GetSubscriptionsParams,
  CancelSubscriptionData,
  UpdateSubscriptionData,
  PaginatedResponse
} from '../types/Subscription';
import type { Payment, GetPaymentsParams } from '../types/Payment';

export class SubscriptionService implements ISubscriptionService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;  // Dependency Injection
  }

  async getSubscriptions(params: GetSubscriptionsParams): Promise<PaginatedResponse<Subscription>> {
    const response = await this.apiClient.get<PaginatedResponse<Subscription>>(
      '/api/v1/admin/subscriptions',
      { params }
    );
    return response;
  }

  async getSubscriptionById(id: number): Promise<Subscription> {
    const response = await this.apiClient.get<Subscription>(
      `/api/v1/admin/subscriptions/${id}`
    );
    return response;
  }

  async cancelSubscription(id: number, data: CancelSubscriptionData): Promise<Subscription> {
    // Validation
    this.validateCancellationData(data);

    const response = await this.apiClient.post<Subscription>(
      `/api/v1/admin/subscriptions/${id}/cancel`,
      data
    );
    return response;
  }

  async updateSubscription(id: number, data: UpdateSubscriptionData): Promise<Subscription> {
    if (Object.keys(data).length === 0) {
      throw new Error('No data provided for update');
    }

    const response = await this.apiClient.put<Subscription>(
      `/api/v1/admin/subscriptions/${id}`,
      data
    );
    return response;
  }

  async reactivateSubscription(id: number): Promise<Subscription> {
    const response = await this.apiClient.post<Subscription>(
      `/api/v1/admin/subscriptions/${id}/reactivate`
    );
    return response;
  }

  async getSubscriptionPayments(
    id: number,
    params: GetPaymentsParams
  ): Promise<PaginatedResponse<Payment>> {
    const response = await this.apiClient.get<PaginatedResponse<Payment>>(
      `/api/v1/admin/subscriptions/${id}/payments`,
      { params }
    );
    return response;
  }

  async retryPayment(subscriptionId: number): Promise<Payment> {
    const response = await this.apiClient.post<Payment>(
      `/api/v1/admin/subscriptions/${subscriptionId}/retry-payment`
    );
    return response;
  }

  // Private helper (SRP)
  private validateCancellationData(data: CancelSubscriptionData): void {
    if (!data.reason || data.reason.trim().length === 0) {
      throw new Error('Cancellation reason is required');
    }

    if (data.refundAmount !== undefined && data.refundAmount < 0) {
      throw new Error('Refund amount cannot be negative');
    }
  }
}
```

### services/InvoiceService.ts

```typescript
import type { IApiClient } from '@vbwd/core-sdk';
import type { IInvoiceService } from './IInvoiceService';
import type {
  Invoice,
  GetInvoicesParams,
  CreateInvoiceData,
  PaginatedResponse
} from '../types/Invoice';
import type { RefundData, Payment } from '../types/Payment';

export class InvoiceService implements IInvoiceService {
  private readonly apiClient: IApiClient;

  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;  // Dependency Injection
  }

  async getInvoices(params: GetInvoicesParams): Promise<PaginatedResponse<Invoice>> {
    const response = await this.apiClient.get<PaginatedResponse<Invoice>>(
      '/api/v1/admin/invoices',
      { params }
    );
    return response;
  }

  async getInvoiceById(id: number): Promise<Invoice> {
    const response = await this.apiClient.get<Invoice>(
      `/api/v1/admin/invoices/${id}`
    );
    return response;
  }

  async createInvoice(data: CreateInvoiceData): Promise<Invoice> {
    // Validation
    this.validateInvoiceData(data);

    const response = await this.apiClient.post<Invoice>(
      '/api/v1/admin/invoices',
      data
    );
    return response;
  }

  async voidInvoice(id: number): Promise<Invoice> {
    const response = await this.apiClient.post<Invoice>(
      `/api/v1/admin/invoices/${id}/void`
    );
    return response;
  }

  async markInvoiceAsPaid(id: number): Promise<Invoice> {
    const response = await this.apiClient.post<Invoice>(
      `/api/v1/admin/invoices/${id}/mark-paid`
    );
    return response;
  }

  async downloadInvoicePdf(id: number): Promise<Blob> {
    const response = await this.apiClient.get<Blob>(
      `/api/v1/admin/invoices/${id}/pdf`,
      {
        responseType: 'blob'
      }
    );
    return response;
  }

  async getInvoicePayment(invoiceId: number): Promise<Payment> {
    const response = await this.apiClient.get<Payment>(
      `/api/v1/admin/invoices/${invoiceId}/payment`
    );
    return response;
  }

  async processRefund(paymentId: number, data: RefundData): Promise<Payment> {
    // Validation
    this.validateRefundData(data);

    const response = await this.apiClient.post<Payment>(
      `/api/v1/admin/payments/${paymentId}/refund`,
      data
    );
    return response;
  }

  // Private helpers (SRP)
  private validateInvoiceData(data: CreateInvoiceData): void {
    if (!data.userId || data.userId <= 0) {
      throw new Error('Valid user ID is required');
    }

    if (!data.amount || data.amount <= 0) {
      throw new Error('Invoice amount must be greater than 0');
    }

    if (!data.currency || data.currency.length !== 3) {
      throw new Error('Valid 3-letter currency code is required');
    }

    if (!data.lineItems || data.lineItems.length === 0) {
      throw new Error('At least one line item is required');
    }

    // Validate line items sum to total
    const lineItemsTotal = data.lineItems.reduce((sum, item) => sum + item.amount, 0);
    if (Math.abs(lineItemsTotal - data.amount) > 0.01) {
      throw new Error('Line items must sum to invoice amount');
    }
  }

  private validateRefundData(data: RefundData): void {
    if (!data.amount || data.amount <= 0) {
      throw new Error('Refund amount must be greater than 0');
    }

    if (!data.reason || data.reason.trim().length === 0) {
      throw new Error('Refund reason is required');
    }
  }
}
```

---

## 3.5. Event-Driven Architecture for Subscriptions & Invoices

### Overview

Implement event-driven architecture for subscription lifecycle and invoice state changes. Events enable real-time updates, audit trails, analytics tracking, and automated workflows.

### Subscription Events

**File:** `frontend/admin/vue/src/plugins/subscription-invoice-management/events/subscriptionEvents.ts`

```typescript
/**
 * Subscription Domain Events
 *
 * Events track subscription lifecycle: creation, cancellation, renewal, payment failures
 */

export const SUBSCRIPTION_EVENTS = {
  // Lifecycle events
  CREATED: 'subscription:created',
  CANCELLED: 'subscription:cancelled',
  CANCELLING: 'subscription:cancelling',
  REACTIVATED: 'subscription:reactivated',
  EXPIRED: 'subscription:expired',

  // Payment events
  PAYMENT_SUCCEEDED: 'subscription:payment:succeeded',
  PAYMENT_FAILED: 'subscription:payment:failed',
  PAYMENT_RETRYING: 'subscription:payment:retrying',

  // Status events
  STATUS_CHANGED: 'subscription:status:changed',
  PLAN_CHANGED: 'subscription:plan:changed',

  // Renewal events
  RENEWED: 'subscription:renewed',
  RENEWAL_FAILED: 'subscription:renewal:failed'
} as const;

export interface SubscriptionCreatedEvent {
  subscriptionId: number;
  userId: number;
  planId: number;
  timestamp: string;
}

export interface SubscriptionCancelledEvent {
  subscriptionId: number;
  userId: number;
  reason: string;
  immediate: boolean;
  refundAmount?: number;
  adminId: number;
  timestamp: string;
}

export interface SubscriptionPaymentFailedEvent {
  subscriptionId: number;
  userId: number;
  amount: number;
  currency: string;
  failureReason: string;
  retryCount: number;
  timestamp: string;
}

export interface SubscriptionStatusChangedEvent {
  subscriptionId: number;
  oldStatus: string;
  newStatus: string;
  adminId?: number;
  timestamp: string;
}
```

### Invoice Events

**File:** `frontend/admin/vue/src/plugins/subscription-invoice-management/events/invoiceEvents.ts`

```typescript
/**
 * Invoice Domain Events
 *
 * Events track invoice lifecycle: creation, payment, void, refunds
 */

export const INVOICE_EVENTS = {
  // Lifecycle events
  CREATED: 'invoice:created',
  PAID: 'invoice:paid',
  VOIDED: 'invoice:voided',
  SENT: 'invoice:sent',

  // Payment events
  PAYMENT_RECEIVED: 'invoice:payment:received',
  PAYMENT_FAILED: 'invoice:payment:failed',

  // Refund events
  REFUND_PROCESSING: 'invoice:refund:processing',
  REFUND_COMPLETED: 'invoice:refund:completed',
  REFUND_FAILED: 'invoice:refund:failed',

  // Status events
  STATUS_CHANGED: 'invoice:status:changed'
} as const;

export interface InvoiceCreatedEvent {
  invoiceId: number;
  userId: number;
  subscriptionId?: number;
  amount: number;
  currency: string;
  adminId?: number;
  timestamp: string;
}

export interface InvoicePaidEvent {
  invoiceId: number;
  userId: number;
  amount: number;
  paymentMethod: string;
  timestamp: string;
}

export interface RefundProcessingEvent {
  paymentId: number;
  invoiceId: number;
  amount: number;
  reason: string;
  adminId: number;
  timestamp: string;
}

export interface RefundCompletedEvent {
  paymentId: number;
  invoiceId: number;
  amount: number;
  providerRefundId: string;
  adminId: number;
  timestamp: string;
}
```

### Update Subscription Service to Emit Events

**File:** `frontend/admin/vue/src/plugins/subscription-invoice-management/services/SubscriptionService.ts`

```typescript
import type { IApiClient, IEventBus } from '@vbwd/core-sdk';
import { SUBSCRIPTION_EVENTS } from '../events/subscriptionEvents';

export class SubscriptionService implements ISubscriptionService {
  constructor(
    private apiClient: IApiClient,
    private eventBus: IEventBus
  ) {}

  async cancelSubscription(
    id: number,
    data: CancelSubscriptionData
  ): Promise<Subscription> {
    // Emit event BEFORE cancellation
    this.eventBus.emit(SUBSCRIPTION_EVENTS.CANCELLING, {
      subscriptionId: id,
      reason: data.reason,
      immediate: data.immediate,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    try {
      const response = await this.apiClient.post<Subscription>(
        `/api/v1/admin/subscriptions/${id}/cancel`,
        data
      );

      // Emit event AFTER successful cancellation
      this.eventBus.emit(SUBSCRIPTION_EVENTS.CANCELLED, {
        subscriptionId: id,
        userId: response.userId,
        reason: data.reason,
        immediate: data.immediate,
        refundAmount: data.refundAmount,
        adminId: this.getCurrentAdminId(),
        timestamp: new Date().toISOString()
      });

      // Emit status changed event
      this.eventBus.emit(SUBSCRIPTION_EVENTS.STATUS_CHANGED, {
        subscriptionId: id,
        oldStatus: 'active',
        newStatus: response.status,
        adminId: this.getCurrentAdminId(),
        timestamp: new Date().toISOString()
      });

      return response;
    } catch (error) {
      // Could emit cancellation failed event
      throw error;
    }
  }

  async retryPayment(subscriptionId: number): Promise<Payment> {
    this.eventBus.emit(SUBSCRIPTION_EVENTS.PAYMENT_RETRYING, {
      subscriptionId,
      timestamp: new Date().toISOString()
    });

    try {
      const payment = await this.apiClient.post<Payment>(
        `/api/v1/admin/subscriptions/${subscriptionId}/retry-payment`
      );

      if (payment.status === 'succeeded') {
        this.eventBus.emit(SUBSCRIPTION_EVENTS.PAYMENT_SUCCEEDED, {
          subscriptionId,
          paymentId: payment.id,
          amount: payment.amount,
          timestamp: new Date().toISOString()
        });
      } else if (payment.status === 'failed') {
        this.eventBus.emit(SUBSCRIPTION_EVENTS.PAYMENT_FAILED, {
          subscriptionId,
          amount: payment.amount,
          failureReason: payment.failureReason || 'Unknown',
          timestamp: new Date().toISOString()
        });
      }

      return payment;
    } catch (error) {
      throw error;
    }
  }

  async reactivateSubscription(id: number): Promise<Subscription> {
    const response = await this.apiClient.post<Subscription>(
      `/api/v1/admin/subscriptions/${id}/reactivate`
    );

    this.eventBus.emit(SUBSCRIPTION_EVENTS.REACTIVATED, {
      subscriptionId: id,
      userId: response.userId,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    return response;
  }

  private getCurrentAdminId(): number {
    return 1; // Get from auth service
  }
}
```

### Update Invoice Service to Emit Events

**File:** `frontend/admin/vue/src/plugins/subscription-invoice-management/services/InvoiceService.ts`

```typescript
import type { IApiClient, IEventBus } from '@vbwd/core-sdk';
import { INVOICE_EVENTS } from '../events/invoiceEvents';

export class InvoiceService implements IInvoiceService {
  constructor(
    private apiClient: IApiClient,
    private eventBus: IEventBus
  ) {}

  async createInvoice(data: CreateInvoiceData): Promise<Invoice> {
    const response = await this.apiClient.post<Invoice>(
      '/api/v1/admin/invoices',
      data
    );

    this.eventBus.emit(INVOICE_EVENTS.CREATED, {
      invoiceId: response.id,
      userId: data.userId,
      subscriptionId: data.subscriptionId,
      amount: data.amount,
      currency: data.currency,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    return response;
  }

  async processRefund(paymentId: number, data: RefundData): Promise<Payment> {
    // Emit event BEFORE processing
    this.eventBus.emit(INVOICE_EVENTS.REFUND_PROCESSING, {
      paymentId,
      invoiceId: data.invoiceId, // Assuming we have this
      amount: data.amount,
      reason: data.reason,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    try {
      const payment = await this.apiClient.post<Payment>(
        `/api/v1/admin/payments/${paymentId}/refund`,
        data
      );

      // Emit event AFTER successful refund
      this.eventBus.emit(INVOICE_EVENTS.REFUND_COMPLETED, {
        paymentId,
        invoiceId: data.invoiceId,
        amount: data.amount,
        providerRefundId: payment.providerRefundId || 'N/A',
        adminId: this.getCurrentAdminId(),
        timestamp: new Date().toISOString()
      });

      return payment;
    } catch (error: any) {
      // Emit failure event
      this.eventBus.emit(INVOICE_EVENTS.REFUND_FAILED, {
        paymentId,
        amount: data.amount,
        error: error.message,
        adminId: this.getCurrentAdminId(),
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async voidInvoice(id: number): Promise<Invoice> {
    const response = await this.apiClient.post<Invoice>(
      `/api/v1/admin/invoices/${id}/void`
    );

    this.eventBus.emit(INVOICE_EVENTS.VOIDED, {
      invoiceId: id,
      adminId: this.getCurrentAdminId(),
      timestamp: new Date().toISOString()
    });

    return response;
  }

  private getCurrentAdminId(): number {
    return 1; // Get from auth service
  }
}
```

### Event Listeners in Stores

**File:** `frontend/admin/vue/src/plugins/subscription-invoice-management/stores/subscriptionStore.ts`

```typescript
import { defineStore } from 'pinia';
import { SUBSCRIPTION_EVENTS } from '../events/subscriptionEvents';
import type { IEventBus } from '@vbwd/core-sdk';

export const useSubscriptionStore = defineStore('subscription', {
  actions: {
    setupEventListeners(eventBus: IEventBus) {
      // Listen to subscription cancelled event
      eventBus.on(SUBSCRIPTION_EVENTS.CANCELLED, (event: SubscriptionCancelledEvent) => {
        // Update subscription in local state
        const index = this.subscriptions.findIndex(s => s.id === event.subscriptionId);
        if (index !== -1) {
          this.subscriptions[index].status = 'cancelled';
          this.subscriptions[index].cancelledAt = event.timestamp;
        }

        // Update selected subscription
        if (this.selectedSubscription?.id === event.subscriptionId) {
          this.selectedSubscription.status = 'cancelled';
          this.selectedSubscription.cancelledAt = event.timestamp;
        }

        // Show notification
        console.log(`Subscription ${event.subscriptionId} cancelled. Reason: ${event.reason}`);
      });

      // Listen to payment failed event
      eventBus.on(SUBSCRIPTION_EVENTS.PAYMENT_FAILED, (event: SubscriptionPaymentFailedEvent) => {
        // Update subscription status to past_due
        const index = this.subscriptions.findIndex(s => s.id === event.subscriptionId);
        if (index !== -1) {
          this.subscriptions[index].status = 'past_due';
        }

        // Could trigger notification to admin
        console.warn(`Payment failed for subscription ${event.subscriptionId}: ${event.failureReason}`);
      });

      // Listen to reactivated event
      eventBus.on(SUBSCRIPTION_EVENTS.REACTIVATED, (event) => {
        const index = this.subscriptions.findIndex(s => s.id === event.subscriptionId);
        if (index !== -1) {
          this.subscriptions[index].status = 'active';
          this.subscriptions[index].cancelledAt = null;
        }
      });
    }
  }
});
```

**File:** `frontend/admin/vue/src/plugins/subscription-invoice-management/stores/invoiceStore.ts`

```typescript
import { defineStore } from 'pinia';
import { INVOICE_EVENTS } from '../events/invoiceEvents';
import type { IEventBus } from '@vbwd/core-sdk';

export const useInvoiceStore = defineStore('invoice', {
  actions: {
    setupEventListeners(eventBus: IEventBus) {
      // Listen to invoice created event
      eventBus.on(INVOICE_EVENTS.CREATED, (event: InvoiceCreatedEvent) => {
        console.log(`Invoice ${event.invoiceId} created for user ${event.userId}`);
      });

      // Listen to refund completed event
      eventBus.on(INVOICE_EVENTS.REFUND_COMPLETED, (event: RefundCompletedEvent) => {
        // Could update invoice/payment status in local state
        console.log(`Refund completed for payment ${event.paymentId}: $${event.amount}`);
      });

      // Listen to refund failed event
      eventBus.on(INVOICE_EVENTS.REFUND_FAILED, (event) => {
        // Show error notification
        console.error(`Refund failed for payment ${event.paymentId}: ${event.error}`);
      });
    }
  }
});
```

### Analytics Listener for Subscriptions

**File:** `frontend/admin/vue/src/plugins/analytics-dashboard/stores/analyticsStore.ts`

```typescript
import { defineStore } from 'pinia';
import { SUBSCRIPTION_EVENTS } from '../../subscription-invoice-management/events/subscriptionEvents';
import { INVOICE_EVENTS } from '../../subscription-invoice-management/events/invoiceEvents';

export const useAnalyticsStore = defineStore('analytics', {
  actions: {
    setupEventListeners(eventBus: IEventBus) {
      // Track subscription cancellations
      eventBus.on(SUBSCRIPTION_EVENTS.CANCELLED, (event: SubscriptionCancelledEvent) => {
        this.incrementMetric('subscriptions_cancelled');
        this.trackCancellationReason(event.reason);
        this.updateChurnRate();
      });

      // Track subscription reactivations
      eventBus.on(SUBSCRIPTION_EVENTS.REACTIVATED, (event) => {
        this.incrementMetric('subscriptions_reactivated');
        this.updateRetentionRate();
      });

      // Track payment failures
      eventBus.on(SUBSCRIPTION_EVENTS.PAYMENT_FAILED, (event: SubscriptionPaymentFailedEvent) => {
        this.incrementMetric('payment_failures');
        this.trackFailureReason(event.failureReason);
      });

      // Track refunds
      eventBus.on(INVOICE_EVENTS.REFUND_COMPLETED, (event: RefundCompletedEvent) => {
        this.incrementMetric('refunds_processed');
        this.addToRefundedRevenue(event.amount);
      });
    }
  }
});
```

### Testing Event Emission

**File:** `services/__tests__/SubscriptionService.spec.ts`

```typescript
describe('SubscriptionService - Event Emission', () => {
  let service: SubscriptionService;
  let mockApiClient: IApiClient;
  let mockEventBus: IEventBus;

  beforeEach(() => {
    mockApiClient = {
      post: vi.fn()
    } as unknown as IApiClient;

    mockEventBus = {
      emit: vi.fn(),
      on: vi.fn(),
      off: vi.fn()
    } as unknown as IEventBus;

    service = new SubscriptionService(mockApiClient, mockEventBus);
  });

  it('should emit CANCELLING event before API call', async () => {
    vi.mocked(mockApiClient.post).mockResolvedValue({
      id: 1,
      status: 'cancelled'
    });

    await service.cancelSubscription(1, {
      reason: 'customer_request',
      immediate: false
    });

    expect(mockEventBus.emit).toHaveBeenCalledWith(
      SUBSCRIPTION_EVENTS.CANCELLING,
      expect.objectContaining({
        subscriptionId: 1,
        reason: 'customer_request'
      })
    );
  });

  it('should emit CANCELLED event after successful cancellation', async () => {
    vi.mocked(mockApiClient.post).mockResolvedValue({
      id: 1,
      userId: 123,
      status: 'cancelled'
    });

    await service.cancelSubscription(1, {
      reason: 'customer_request',
      immediate: false
    });

    expect(mockEventBus.emit).toHaveBeenCalledWith(
      SUBSCRIPTION_EVENTS.CANCELLED,
      expect.objectContaining({
        subscriptionId: 1,
        userId: 123,
        reason: 'customer_request'
      })
    );
  });

  it('should emit PAYMENT_FAILED event when retry fails', async () => {
    vi.mocked(mockApiClient.post).mockResolvedValue({
      id: 456,
      status: 'failed',
      failureReason: 'Insufficient funds'
    });

    await service.retryPayment(1);

    expect(mockEventBus.emit).toHaveBeenCalledWith(
      SUBSCRIPTION_EVENTS.PAYMENT_FAILED,
      expect.objectContaining({
        subscriptionId: 1,
        failureReason: 'Insufficient funds'
      })
    );
  });

  it('should emit REACTIVATED event after successful reactivation', async () => {
    vi.mocked(mockApiClient.post).mockResolvedValue({
      id: 1,
      userId: 123,
      status: 'active'
    });

    await service.reactivateSubscription(1);

    expect(mockEventBus.emit).toHaveBeenCalledWith(
      SUBSCRIPTION_EVENTS.REACTIVATED,
      expect.objectContaining({
        subscriptionId: 1,
        userId: 123
      })
    );
  });
});
```

### Backend Event Flow

When frontend emits events and makes API calls, the backend also uses event-driven architecture:

```
Frontend Service.cancelSubscription()
  ↓
  emit(SUBSCRIPTION_EVENTS.CANCELLING) // Frontend event
  ↓
  POST /api/v1/admin/subscriptions/1/cancel
  ↓
Backend Flask Route
  ↓
  EventDispatcher.emit(SubscriptionCancellationRequestedEvent) // Backend event
  ↓
SubscriptionCancellationHandler
  ↓
  - Update subscription status
  - Calculate refund
  - Log admin action
  - Send notification
  ↓
  emit(SubscriptionCancelledEvent) // Backend event
  ↓
Response to Frontend
  ↓
  emit(SUBSCRIPTION_EVENTS.CANCELLED) // Frontend event
  ↓
All Frontend Listeners React
  - Store updates state
  - Analytics tracks metric
  - Toast shows success
  - Activity log refreshes
```

### Benefits

1. **Decoupling**: Subscription, invoice, and analytics modules are independent
2. **Real-time Updates**: All components react immediately to state changes
3. **Audit Trail**: Every subscription/invoice action is tracked via events
4. **Analytics**: Automatic metric tracking without tight coupling
5. **Testability**: Easy to test event emission and handling separately
6. **Extensibility**: New features can listen to existing events

### Event Flow Diagrams

- `/docs/architecture_core_view_admin/puml/sprint-3-subscription-lifecycle.puml`
- `/docs/architecture_core_view_admin/puml/sprint-3-refund-processing-flow.puml`
- `/docs/architecture_core_view_admin/puml/end-to-end-event-flow.puml`

---

## 4. Service Unit Tests

### services/__tests__/SubscriptionService.spec.ts

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { IApiClient } from '@vbwd/core-sdk';
import { SubscriptionService } from '../SubscriptionService';
import { SubscriptionStatus } from '../../types/Subscription';

describe('SubscriptionService', () => {
  let subscriptionService: SubscriptionService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn()
    } as unknown as IApiClient;

    subscriptionService = new SubscriptionService(mockApiClient);
  });

  describe('getSubscriptions', () => {
    it('should fetch subscriptions with pagination', async () => {
      const mockResponse = {
        data: [
          { id: 1, userId: 1, status: SubscriptionStatus.ACTIVE },
          { id: 2, userId: 2, status: SubscriptionStatus.TRIALING }
        ],
        pagination: { page: 1, limit: 25, total: 2, totalPages: 1 }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      const result = await subscriptionService.getSubscriptions({ page: 1, limit: 25 });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/subscriptions', {
        params: { page: 1, limit: 25 }
      });
      expect(result.data).toHaveLength(2);
    });

    it('should filter by status', async () => {
      const mockResponse = {
        data: [{ id: 1, status: SubscriptionStatus.ACTIVE }],
        pagination: { page: 1, limit: 25, total: 1, totalPages: 1 }
      };
      vi.mocked(mockApiClient.get).mockResolvedValue(mockResponse);

      await subscriptionService.getSubscriptions({ status: SubscriptionStatus.ACTIVE });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/subscriptions', {
        params: { status: SubscriptionStatus.ACTIVE }
      });
    });
  });

  describe('cancelSubscription', () => {
    it('should cancel subscription immediately', async () => {
      const mockResponse = {
        id: 1,
        status: SubscriptionStatus.CANCELLED,
        cancelledAt: '2025-12-20T10:00:00Z'
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      const result = await subscriptionService.cancelSubscription(1, {
        reason: 'customer_request',
        immediate: true
      });

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/v1/admin/subscriptions/1/cancel',
        { reason: 'customer_request', immediate: true }
      );
      expect(result.status).toBe(SubscriptionStatus.CANCELLED);
    });

    it('should throw error if reason is empty', async () => {
      await expect(
        subscriptionService.cancelSubscription(1, {
          reason: '',
          immediate: true
        })
      ).rejects.toThrow('Cancellation reason is required');
    });

    it('should throw error if refund amount is negative', async () => {
      await expect(
        subscriptionService.cancelSubscription(1, {
          reason: 'test',
          immediate: true,
          refundAmount: -10
        })
      ).rejects.toThrow('Refund amount cannot be negative');
    });
  });

  describe('reactivateSubscription', () => {
    it('should reactivate cancelled subscription', async () => {
      const mockResponse = {
        id: 1,
        status: SubscriptionStatus.ACTIVE,
        cancelledAt: null
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      const result = await subscriptionService.reactivateSubscription(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/subscriptions/1/reactivate');
      expect(result.status).toBe(SubscriptionStatus.ACTIVE);
    });
  });

  describe('retryPayment', () => {
    it('should retry failed payment', async () => {
      const mockPayment = {
        id: 1,
        status: 'succeeded',
        amount: 29.99
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockPayment);

      const result = await subscriptionService.retryPayment(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/subscriptions/1/retry-payment');
      expect(result.status).toBe('succeeded');
    });
  });
});
```

### services/__tests__/InvoiceService.spec.ts

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { IApiClient } from '@vbwd/core-sdk';
import { InvoiceService } from '../InvoiceService';
import { InvoiceStatus } from '../../types/Invoice';
import type { CreateInvoiceData } from '../../types/Invoice';

describe('InvoiceService', () => {
  let invoiceService: InvoiceService;
  let mockApiClient: IApiClient;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn()
    } as unknown as IApiClient;

    invoiceService = new InvoiceService(mockApiClient);
  });

  describe('createInvoice', () => {
    it('should create new invoice', async () => {
      const invoiceData: CreateInvoiceData = {
        userId: 1,
        amount: 29.99,
        currency: 'USD',
        dueDate: '2025-12-25',
        lineItems: [
          { description: 'Premium Plan', quantity: 1, unitAmount: 29.99, amount: 29.99, currency: 'USD' }
        ]
      };

      const mockResponse = {
        id: 1,
        ...invoiceData,
        status: InvoiceStatus.OPEN,
        invoiceNumber: 'INV-001'
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      const result = await invoiceService.createInvoice(invoiceData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/invoices', invoiceData);
      expect(result.id).toBe(1);
      expect(result.status).toBe(InvoiceStatus.OPEN);
    });

    it('should throw error if userId is invalid', async () => {
      const invalidData: CreateInvoiceData = {
        userId: 0,  // Invalid
        amount: 29.99,
        currency: 'USD',
        dueDate: '2025-12-25',
        lineItems: []
      };

      await expect(invoiceService.createInvoice(invalidData)).rejects.toThrow(
        'Valid user ID is required'
      );
    });

    it('should throw error if amount is invalid', async () => {
      const invalidData: CreateInvoiceData = {
        userId: 1,
        amount: -10,  // Invalid
        currency: 'USD',
        dueDate: '2025-12-25',
        lineItems: []
      };

      await expect(invoiceService.createInvoice(invalidData)).rejects.toThrow(
        'Invoice amount must be greater than 0'
      );
    });

    it('should throw error if currency is invalid', async () => {
      const invalidData: CreateInvoiceData = {
        userId: 1,
        amount: 29.99,
        currency: 'US',  // Invalid (not 3 letters)
        dueDate: '2025-12-25',
        lineItems: []
      };

      await expect(invoiceService.createInvoice(invalidData)).rejects.toThrow(
        'Valid 3-letter currency code is required'
      );
    });

    it('should throw error if no line items', async () => {
      const invalidData: CreateInvoiceData = {
        userId: 1,
        amount: 29.99,
        currency: 'USD',
        dueDate: '2025-12-25',
        lineItems: []  // Invalid
      };

      await expect(invoiceService.createInvoice(invalidData)).rejects.toThrow(
        'At least one line item is required'
      );
    });

    it('should throw error if line items don\'t sum to total', async () => {
      const invalidData: CreateInvoiceData = {
        userId: 1,
        amount: 29.99,
        currency: 'USD',
        dueDate: '2025-12-25',
        lineItems: [
          { description: 'Item', quantity: 1, unitAmount: 10, amount: 10, currency: 'USD' }  // Doesn't match total
        ]
      };

      await expect(invoiceService.createInvoice(invalidData)).rejects.toThrow(
        'Line items must sum to invoice amount'
      );
    });
  });

  describe('processRefund', () => {
    it('should process full refund', async () => {
      const mockResponse = {
        id: 1,
        status: 'refunded',
        refundedAmount: 29.99
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(mockResponse);

      const result = await invoiceService.processRefund(1, {
        amount: 29.99,
        reason: 'customer_request',
        notifyCustomer: true
      });

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/admin/payments/1/refund', {
        amount: 29.99,
        reason: 'customer_request',
        notifyCustomer: true
      });
      expect(result.status).toBe('refunded');
    });

    it('should throw error if refund amount is invalid', async () => {
      await expect(
        invoiceService.processRefund(1, {
          amount: -10,  // Invalid
          reason: 'test',
          notifyCustomer: false
        })
      ).rejects.toThrow('Refund amount must be greater than 0');
    });

    it('should throw error if reason is empty', async () => {
      await expect(
        invoiceService.processRefund(1, {
          amount: 10,
          reason: '',  // Invalid
          notifyCustomer: false
        })
      ).rejects.toThrow('Refund reason is required');
    });
  });

  describe('downloadInvoicePdf', () => {
    it('should download PDF as blob', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });
      vi.mocked(mockApiClient.get).mockResolvedValue(mockBlob);

      const result = await invoiceService.downloadInvoicePdf(1);

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/admin/invoices/1/pdf', {
        responseType: 'blob'
      });
      expect(result).toBeInstanceOf(Blob);
    });
  });
});
```

---

## 5. Store Implementations

### stores/subscriptionStore.ts

```typescript
import { defineStore } from 'pinia';
import type { ISubscriptionService } from '../services/ISubscriptionService';
import type {
  Subscription,
  GetSubscriptionsParams,
  CancelSubscriptionData,
  UpdateSubscriptionData
} from '../types/Subscription';
import type { Payment, GetPaymentsParams } from '../types/Payment';

interface SubscriptionState {
  subscriptions: Subscription[];
  selectedSubscription: Subscription | null;
  payments: Payment[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  subscriptionService: ISubscriptionService | null;
}

export const useSubscriptionStore = defineStore('subscription', {
  state: (): SubscriptionState => ({
    subscriptions: [],
    selectedSubscription: null,
    payments: [],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: 25,
      total: 0,
      totalPages: 0
    },
    subscriptionService: null
  }),

  getters: {
    activeSubscriptions: (state) =>
      state.subscriptions.filter(sub => sub.status === 'active'),

    cancelledSubscriptions: (state) =>
      state.subscriptions.filter(sub => sub.status === 'cancelled'),

    expiredSubscriptions: (state) =>
      state.subscriptions.filter(sub => sub.status === 'expired'),

    failedPayments: (state) =>
      state.payments.filter(payment => payment.status === 'failed')
  },

  actions: {
    setSubscriptionService(service: ISubscriptionService) {
      this.subscriptionService = service;
    },

    async fetchSubscriptions(params: GetSubscriptionsParams = {}) {
      if (!this.subscriptionService) {
        throw new Error('SubscriptionService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const response = await this.subscriptionService.getSubscriptions({
          page: this.pagination.page,
          limit: this.pagination.limit,
          ...params
        });

        this.subscriptions = response.data;
        this.pagination = response.pagination;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch subscriptions';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchSubscriptionById(id: number) {
      if (!this.subscriptionService) {
        throw new Error('SubscriptionService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const subscription = await this.subscriptionService.getSubscriptionById(id);
        this.selectedSubscription = subscription;
        return subscription;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch subscription';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async cancelSubscription(id: number, data: CancelSubscriptionData) {
      if (!this.subscriptionService) {
        throw new Error('SubscriptionService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const cancelled = await this.subscriptionService.cancelSubscription(id, data);

        // Update in list
        const index = this.subscriptions.findIndex(s => s.id === id);
        if (index !== -1) {
          this.subscriptions[index] = cancelled;
        }

        // Update selected
        if (this.selectedSubscription?.id === id) {
          this.selectedSubscription = cancelled;
        }

        return cancelled;
      } catch (error: any) {
        this.error = error.message || 'Failed to cancel subscription';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async reactivateSubscription(id: number) {
      if (!this.subscriptionService) {
        throw new Error('SubscriptionService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const reactivated = await this.subscriptionService.reactivateSubscription(id);

        // Update in list
        const index = this.subscriptions.findIndex(s => s.id === id);
        if (index !== -1) {
          this.subscriptions[index] = reactivated;
        }

        // Update selected
        if (this.selectedSubscription?.id === id) {
          this.selectedSubscription = reactivated;
        }

        return reactivated;
      } catch (error: any) {
        this.error = error.message || 'Failed to reactivate subscription';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchSubscriptionPayments(id: number, params: GetPaymentsParams = {}) {
      if (!this.subscriptionService) {
        throw new Error('SubscriptionService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const response = await this.subscriptionService.getSubscriptionPayments(id, params);
        this.payments = response.data;
        return response;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch payments';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async retryPayment(subscriptionId: number) {
      if (!this.subscriptionService) {
        throw new Error('SubscriptionService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const payment = await this.subscriptionService.retryPayment(subscriptionId);

        // Add to payments list
        this.payments.unshift(payment);

        return payment;
      } catch (error: any) {
        this.error = error.message || 'Failed to retry payment';
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

### stores/invoiceStore.ts

```typescript
import { defineStore } from 'pinia';
import type { IInvoiceService } from '../services/IInvoiceService';
import type {
  Invoice,
  GetInvoicesParams,
  CreateInvoiceData
} from '../types/Invoice';
import type { RefundData, Payment } from '../types/Payment';

interface InvoiceState {
  invoices: Invoice[];
  selectedInvoice: Invoice | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  invoiceService: IInvoiceService | null;
}

export const useInvoiceStore = defineStore('invoice', {
  state: (): InvoiceState => ({
    invoices: [],
    selectedInvoice: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: 25,
      total: 0,
      totalPages: 0
    },
    invoiceService: null
  }),

  getters: {
    paidInvoices: (state) => state.invoices.filter(inv => inv.status === 'paid'),
    openInvoices: (state) => state.invoices.filter(inv => inv.status === 'open'),
    voidInvoices: (state) => state.invoices.filter(inv => inv.status === 'void')
  },

  actions: {
    setInvoiceService(service: IInvoiceService) {
      this.invoiceService = service;
    },

    async fetchInvoices(params: GetInvoicesParams = {}) {
      if (!this.invoiceService) {
        throw new Error('InvoiceService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const response = await this.invoiceService.getInvoices({
          page: this.pagination.page,
          limit: this.pagination.limit,
          ...params
        });

        this.invoices = response.data;
        this.pagination = response.pagination;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch invoices';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchInvoiceById(id: number) {
      if (!this.invoiceService) {
        throw new Error('InvoiceService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const invoice = await this.invoiceService.getInvoiceById(id);
        this.selectedInvoice = invoice;
        return invoice;
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch invoice';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async createInvoice(data: CreateInvoiceData) {
      if (!this.invoiceService) {
        throw new Error('InvoiceService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const invoice = await this.invoiceService.createInvoice(data);
        this.invoices.unshift(invoice);
        this.pagination.total += 1;
        return invoice;
      } catch (error: any) {
        this.error = error.message || 'Failed to create invoice';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async voidInvoice(id: number) {
      if (!this.invoiceService) {
        throw new Error('InvoiceService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const voided = await this.invoiceService.voidInvoice(id);

        // Update in list
        const index = this.invoices.findIndex(inv => inv.id === id);
        if (index !== -1) {
          this.invoices[index] = voided;
        }

        // Update selected
        if (this.selectedInvoice?.id === id) {
          this.selectedInvoice = voided;
        }

        return voided;
      } catch (error: any) {
        this.error = error.message || 'Failed to void invoice';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async downloadInvoicePdf(id: number) {
      if (!this.invoiceService) {
        throw new Error('InvoiceService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const blob = await this.invoiceService.downloadInvoicePdf(id);

        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `invoice-${id}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error: any) {
        this.error = error.message || 'Failed to download PDF';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async processRefund(paymentId: number, data: RefundData) {
      if (!this.invoiceService) {
        throw new Error('InvoiceService not injected');
      }

      this.loading = true;
      this.error = null;

      try {
        const payment = await this.invoiceService.processRefund(paymentId, data);
        return payment;
      } catch (error: any) {
        this.error = error.message || 'Failed to process refund';
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

### __tests__/e2e/subscription-list.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Subscription List', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should display subscription list', async ({ page }) => {
    await page.goto('/admin/subscriptions');
    await page.waitForSelector('[data-testid="subscription-table"]');

    await expect(page.locator('th:has-text("User")')).toBeVisible();
    await expect(page.locator('th:has-text("Plan")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();

    const rows = page.locator('[data-testid="subscription-row"]');
    await expect(rows).toHaveCountGreaterThan(0);
  });

  test('should filter subscriptions by status', async ({ page }) => {
    await page.goto('/admin/subscriptions');
    await page.waitForSelector('[data-testid="subscription-table"]');

    await page.selectOption('select[data-testid="status-filter"]', 'active');
    await page.click('button:has-text("Apply Filters")');

    await page.waitForTimeout(500);

    const statusBadges = page.locator('[data-testid="subscription-status"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      const text = await statusBadges.nth(i).textContent();
      expect(text?.toLowerCase()).toContain('active');
    }
  });

  test('should navigate to subscription details', async ({ page }) => {
    await page.goto('/admin/subscriptions');
    await page.waitForSelector('[data-testid="subscription-table"]');

    await page.click('[data-testid="subscription-row"]:first-child');

    await page.waitForURL(/\/admin\/subscriptions\/\d+/);
    await expect(page.locator('h1')).toContainText('Subscription Details');
  });
});
```

### __tests__/e2e/refund-processing.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Refund Processing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('input[name="email"]', 'admin@test.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin/dashboard');
  });

  test('should process full refund', async ({ page }) => {
    await page.goto('/admin/invoices');
    await page.waitForSelector('[data-testid="invoice-table"]');

    // Find paid invoice
    await page.click('[data-testid="invoice-row"][data-status="paid"]:first-child');

    // Click refund button
    await page.click('button:has-text("Refund")');

    // Fill refund modal
    await page.fill('input[name="refundAmount"]', '29.99');
    await page.fill('textarea[name="refundReason"]', 'Customer request');
    await page.check('input[name="notifyCustomer"]');

    // Submit refund
    await page.click('button:has-text("Process Refund")');

    // Verify success
    await page.waitForSelector('.toast:has-text("Refund processed")');

    // Verify payment status updated
    await expect(page.locator('[data-testid="payment-status"]')).toContainText('refunded');
  });

  test('should process partial refund', async ({ page }) => {
    await page.goto('/admin/invoices');
    await page.waitForSelector('[data-testid="invoice-table"]');

    await page.click('[data-testid="invoice-row"][data-status="paid"]:first-child');
    await page.click('button:has-text("Refund")');

    // Partial refund (half)
    await page.fill('input[name="refundAmount"]', '14.99');
    await page.fill('textarea[name="refundReason"]', 'Partial service');

    await page.click('button:has-text("Process Refund")');

    await page.waitForSelector('.toast:has-text("Refund processed")');
    await expect(page.locator('[data-testid="payment-status"]')).toContainText('partially_refunded');
  });

  test('should show validation error for invalid refund amount', async ({ page }) => {
    await page.goto('/admin/invoices/1');
    await page.click('button:has-text("Refund")');

    await page.fill('input[name="refundAmount"]', '-10');  // Invalid
    await page.fill('textarea[name="refundReason"]', 'Test');

    await page.click('button:has-text("Process Refund")');

    await expect(page.locator('.error:has-text("amount")')).toBeVisible();
  });
});
```

---

## 7. Docker Integration

```bash
# Run unit tests
docker-compose run --rm frontend npm run test:unit -- plugins/subscription-invoice-management

# Run E2E tests
docker-compose run --rm frontend npm run test:e2e -- subscription- invoice- refund-

# Run all tests with coverage
docker-compose run --rm frontend npm run test:coverage

# Watch mode
docker-compose run --rm frontend npm run test:unit:watch -- plugins/subscription-invoice-management
```

---

## 8. Success Criteria

- [ ] Subscription list with filtering and pagination
- [ ] Subscription details with full history
- [ ] Cancel subscription (immediate or at period end)
- [ ] Reactivate cancelled subscription
- [ ] Upgrade/downgrade subscription plan
- [ ] Payment history timeline
- [ ] Retry failed payments
- [ ] Invoice list with advanced filtering
- [ ] Invoice details view
- [ ] Create manual invoices
- [ ] Void invoices
- [ ] Download invoice PDFs
- [ ] Process full refunds
- [ ] Process partial refunds
- [ ] Refund validation and error handling
- [ ] Unit tests >90% coverage
- [ ] E2E tests cover all workflows
- [ ] All tests pass in Docker
- [ ] SOLID principles applied
- [ ] LSP compliance (service interfaces)
- [ ] Dependency Injection throughout
- [ ] Clean code (functions <20 lines)
- [ ] TypeScript strict mode

---

## Next Steps (Sprint 4)

- Analytics Dashboard Plugin
- Revenue metrics and charts
- Subscription growth tracking
- Churn analysis
- User engagement metrics
