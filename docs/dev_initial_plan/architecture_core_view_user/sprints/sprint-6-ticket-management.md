# Sprint 6: Ticket Management Plugin

**Goal:** Build ticket management plugin for viewing, activating, and redeeming tickets with event-driven architecture.

**Dependencies:** Sprint 1 (API Client), Sprint 4 (User Cabinet), Core SDK Sprint 4 (EventBus)

---

## Objectives

- [ ] Ticket Management plugin (implements IPlugin)
- [ ] Protected routes with auth guard
- [ ] View all tickets (active, pending, redeemed, expired)
- [ ] Ticket details with QR code display
- [ ] Ticket activation functionality
- [ ] Event-driven architecture integration
- [ ] Responsive ticket cards
- [ ] E2E tests for ticket features

---

## Tasks

### 6.1 Ticket Management Plugin Structure

```
src/plugins/ticket-management/
├── index.ts                       # Plugin entry with IPlugin
├── routes.ts                      # Protected ticket routes
├── services/
│   ├── TicketService.ts           # Ticket operations with EventBus
│   └── ITicketService.ts          # Service interface (LSP)
├── stores/
│   └── ticketStore.ts             # Ticket state with event listeners
├── composables/
│   └── useTickets.ts              # Composable for ticket logic
├── components/
│   ├── TicketList.vue             # List of all tickets
│   ├── TicketCard.vue             # Individual ticket card
│   ├── TicketDetails.vue          # Full ticket details view
│   ├── TicketQRCode.vue           # QR code display
│   ├── TicketFilters.vue          # Filter by status
│   └── ActivateTicketDialog.vue   # Ticket activation dialog
├── types/
│   └── ticket.types.ts            # Ticket TypeScript types
└── __tests__/
    ├── unit/
    │   ├── TicketService.test.ts
    │   └── ticketStore.test.ts
    └── e2e/
        └── ticket-management.spec.ts
```

---

### 6.2 Ticket Types

**File:** `src/plugins/ticket-management/types/ticket.types.ts`

```typescript
/**
 * Ticket domain types for user app.
 */

export enum TicketStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  REDEEMED = 'redeemed',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled'
}

export interface Ticket {
  id: number;
  userId: number;
  bookingId?: number;
  ticketTypeId: number;
  ticketType: TicketType;
  status: TicketStatus;
  price: string;
  currency: string;
  activationCode?: string;
  qrCodeUrl?: string;
  createdAt: string;
  activatedAt?: string;
  redeemedAt?: string;
  validUntil?: string;
  expiredAt?: string;
}

export interface TicketType {
  id: number;
  name: string;
  description: string;
  category: string;
  validityPeriodDays?: number;
}

export interface ActivateTicketRequest {
  ticketId: number;
  activationCode?: string;
}

export interface TicketFilters {
  status?: TicketStatus;
  search?: string;
}
```

---

### 6.3 Ticket Service with EventBus

**File:** `src/plugins/ticket-management/services/ITicketService.ts`

```typescript
/**
 * Ticket service interface (LSP).
 */
import type { Ticket, ActivateTicketRequest } from '../types/ticket.types';

export interface ITicketService {
  /**
   * Get all tickets for current user.
   */
  getMyTickets(): Promise<Ticket[]>;

  /**
   * Get ticket by ID.
   */
  getTicketById(ticketId: number): Promise<Ticket>;

  /**
   * Activate a ticket.
   */
  activateTicket(request: ActivateTicketRequest): Promise<Ticket>;

  /**
   * Download ticket as PDF.
   */
  downloadTicketPDF(ticketId: number): Promise<Blob>;
}
```

**File:** `src/plugins/ticket-management/services/TicketService.ts`

```typescript
/**
 * Ticket service implementation with event-driven architecture.
 */
import type { IApiClient } from '@core/api';
import type { IEventBus } from '@core/events';
import type { ITicketService } from './ITicketService';
import type { Ticket, ActivateTicketRequest } from '../types/ticket.types';

/**
 * Ticket domain events.
 */
export const TICKET_EVENTS = {
  ACTIVATION_REQUESTED: 'ticket:activation:requested',
  ACTIVATED: 'ticket:activated',
  ACTIVATION_FAILED: 'ticket:activation:failed',
  QR_CODE_DISPLAYED: 'ticket:qr:displayed',
  PDF_DOWNLOADED: 'ticket:pdf:downloaded',
  REDEEMED: 'ticket:redeemed'
} as const;

export interface TicketActivationRequestedEvent {
  ticketId: number;
  userId: number;
  timestamp: string;
}

export interface TicketActivatedEvent {
  ticketId: number;
  userId: number;
  activationCode: string;
  qrCodeUrl: string;
  timestamp: string;
}

export class TicketService implements ITicketService {
  constructor(
    private readonly apiClient: IApiClient,
    private readonly eventBus: IEventBus
  ) {}

  async getMyTickets(): Promise<Ticket[]> {
    return this.apiClient.get<Ticket[]>('/api/v1/tickets');
  }

  async getTicketById(ticketId: number): Promise<Ticket> {
    return this.apiClient.get<Ticket>(`/api/v1/tickets/${ticketId}`);
  }

  async activateTicket(request: ActivateTicketRequest): Promise<Ticket> {
    // Emit event BEFORE activation
    this.eventBus.emit(TICKET_EVENTS.ACTIVATION_REQUESTED, {
      ticketId: request.ticketId,
      userId: 0, // Will be set from auth context
      timestamp: new Date().toISOString()
    } as TicketActivationRequestedEvent);

    try {
      const ticket = await this.apiClient.post<Ticket>(
        `/api/v1/tickets/${request.ticketId}/activate`,
        { activationCode: request.activationCode }
      );

      // Emit event AFTER successful activation
      this.eventBus.emit(TICKET_EVENTS.ACTIVATED, {
        ticketId: ticket.id,
        userId: ticket.userId,
        activationCode: ticket.activationCode!,
        qrCodeUrl: ticket.qrCodeUrl!,
        timestamp: new Date().toISOString()
      } as TicketActivatedEvent);

      return ticket;

    } catch (error: any) {
      // Emit failure event
      this.eventBus.emit(TICKET_EVENTS.ACTIVATION_FAILED, {
        ticketId: request.ticketId,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async downloadTicketPDF(ticketId: number): Promise<Blob> {
    const blob = await this.apiClient.get<Blob>(
      `/api/v1/tickets/${ticketId}/pdf`,
      { responseType: 'blob' }
    );

    // Emit event for analytics
    this.eventBus.emit(TICKET_EVENTS.PDF_DOWNLOADED, {
      ticketId,
      timestamp: new Date().toISOString()
    });

    return blob;
  }
}
```

---

### 6.4 Ticket Store with Event Listeners

**File:** `src/plugins/ticket-management/stores/ticketStore.ts`

```typescript
/**
 * Ticket store with event-driven architecture.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { IEventBus } from '@core/events';
import type { Ticket, TicketStatus, TicketFilters } from '../types/ticket.types';
import { TICKET_EVENTS } from '../services/TicketService';

export const useTicketStore = defineStore('tickets', () => {
  // State
  const tickets = ref<Ticket[]>([]);
  const selectedTicket = ref<Ticket | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<TicketFilters>({});

  // Computed
  const activeTickets = computed(() =>
    tickets.value.filter(t => t.status === 'active')
  );

  const pendingTickets = computed(() =>
    tickets.value.filter(t => t.status === 'pending')
  );

  const expiredTickets = computed(() =>
    tickets.value.filter(t => t.status === 'expired' || t.status === 'redeemed')
  );

  const filteredTickets = computed(() => {
    let result = tickets.value;

    if (filters.value.status) {
      result = result.filter(t => t.status === filters.value.status);
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase();
      result = result.filter(t =>
        t.ticketType.name.toLowerCase().includes(search) ||
        t.activationCode?.toLowerCase().includes(search)
      );
    }

    return result;
  });

  /**
   * Setup event listeners for tickets.
   */
  function setupEventListeners(eventBus: IEventBus): () => void {
    const unsubscribers: Array<() => void> = [];

    // Listen to ticket activation
    unsubscribers.push(
      eventBus.on(TICKET_EVENTS.ACTIVATION_REQUESTED, () => {
        loading.value = true;
        error.value = null;
      })
    );

    unsubscribers.push(
      eventBus.on(TICKET_EVENTS.ACTIVATED, (event: any) => {
        // Update ticket in list
        const index = tickets.value.findIndex(t => t.id === event.ticketId);
        if (index !== -1) {
          tickets.value[index].status = 'active';
          tickets.value[index].activationCode = event.activationCode;
          tickets.value[index].qrCodeUrl = event.qrCodeUrl;
          tickets.value[index].activatedAt = event.timestamp;
        }

        // Update selected ticket
        if (selectedTicket.value?.id === event.ticketId) {
          selectedTicket.value.status = 'active';
          selectedTicket.value.activationCode = event.activationCode;
          selectedTicket.value.qrCodeUrl = event.qrCodeUrl;
          selectedTicket.value.activatedAt = event.timestamp;
        }

        loading.value = false;
      })
    );

    unsubscribers.push(
      eventBus.on(TICKET_EVENTS.ACTIVATION_FAILED, (event: any) => {
        error.value = event.error;
        loading.value = false;
      })
    );

    // Return cleanup function
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  }

  /**
   * Actions.
   */
  function setTickets(newTickets: Ticket[]) {
    tickets.value = newTickets;
  }

  function setSelectedTicket(ticket: Ticket | null) {
    selectedTicket.value = ticket;
  }

  function setFilters(newFilters: TicketFilters) {
    filters.value = { ...filters.value, ...newFilters };
  }

  function clearFilters() {
    filters.value = {};
  }

  return {
    // State
    tickets,
    selectedTicket,
    loading,
    error,
    filters,

    // Computed
    activeTickets,
    pendingTickets,
    expiredTickets,
    filteredTickets,

    // Actions
    setTickets,
    setSelectedTicket,
    setFilters,
    clearFilters,
    setupEventListeners
  };
});
```

---

### 6.5 Ticket Composable

**File:** `src/plugins/ticket-management/composables/useTickets.ts`

```typescript
/**
 * Composable for ticket operations.
 */
import { useTicketStore } from '../stores/ticketStore';
import { useApi } from '@core/api';
import type { ActivateTicketRequest } from '../types/ticket.types';

export function useTickets() {
  const ticketStore = useTicketStore();
  const api = useApi();

  /**
   * Load all tickets for current user.
   */
  async function loadTickets() {
    ticketStore.loading = true;
    ticketStore.error = null;

    try {
      const tickets = await api.tickets.getMyTickets();
      ticketStore.setTickets(tickets);
    } catch (err: any) {
      ticketStore.error = err.message;
      throw err;
    } finally {
      ticketStore.loading = false;
    }
  }

  /**
   * Load single ticket by ID.
   */
  async function loadTicket(ticketId: number) {
    ticketStore.loading = true;
    ticketStore.error = null;

    try {
      const ticket = await api.tickets.getTicketById(ticketId);
      ticketStore.setSelectedTicket(ticket);
    } catch (err: any) {
      ticketStore.error = err.message;
      throw err;
    } finally {
      ticketStore.loading = false;
    }
  }

  /**
   * Activate a ticket.
   */
  async function activateTicket(request: ActivateTicketRequest) {
    return await api.tickets.activateTicket(request);
  }

  /**
   * Download ticket as PDF.
   */
  async function downloadTicketPDF(ticketId: number) {
    const blob = await api.tickets.downloadTicketPDF(ticketId);

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ticket-${ticketId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  return {
    loadTickets,
    loadTicket,
    activateTicket,
    downloadTicketPDF
  };
}
```

---

### 6.6 Ticket List Component

**File:** `src/plugins/ticket-management/components/TicketList.vue`

```vue
<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-bold">My Tickets</h2>
      <button
        @click="refreshTickets"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        Refresh
      </button>
    </div>

    <!-- Filters -->
    <TicketFilters @filter-change="handleFilterChange" />

    <!-- Loading -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-gray-500">Loading tickets...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-800">{{ error }}</p>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="filteredTickets.length === 0"
      class="text-center py-12 bg-gray-50 rounded-md"
    >
      <p class="text-gray-500">No tickets found</p>
    </div>

    <!-- Ticket cards -->
    <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <TicketCard
        v-for="ticket in filteredTickets"
        :key="ticket.id"
        :ticket="ticket"
        @activate="handleActivate"
        @view-details="handleViewDetails"
      />
    </div>

    <!-- Activate dialog -->
    <ActivateTicketDialog
      v-if="showActivateDialog"
      :ticket="selectedTicket"
      @close="showActivateDialog = false"
      @activated="handleTicketActivated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useTicketStore } from '../stores/ticketStore';
import { useTickets } from '../composables/useTickets';
import TicketCard from './TicketCard.vue';
import TicketFilters from './TicketFilters.vue';
import ActivateTicketDialog from './ActivateTicketDialog.vue';
import type { Ticket, TicketFilters } from '../types/ticket.types';

const router = useRouter();
const ticketStore = useTicketStore();
const { loadTickets } = useTickets();

const showActivateDialog = ref(false);
const selectedTicket = ref<Ticket | null>(null);

// Computed
const loading = computed(() => ticketStore.loading);
const error = computed(() => ticketStore.error);
const filteredTickets = computed(() => ticketStore.filteredTickets);

// Methods
async function refreshTickets() {
  await loadTickets();
}

function handleFilterChange(filters: TicketFilters) {
  ticketStore.setFilters(filters);
}

function handleActivate(ticket: Ticket) {
  selectedTicket.value = ticket;
  showActivateDialog.value = true;
}

function handleViewDetails(ticket: Ticket) {
  router.push(`/tickets/${ticket.id}`);
}

function handleTicketActivated() {
  showActivateDialog.value = false;
  refreshTickets();
}

// Lifecycle
onMounted(() => {
  loadTickets();
});
</script>
```

---

### 6.7 Ticket QR Code Component

**File:** `src/plugins/ticket-management/components/TicketQRCode.vue`

```vue
<template>
  <div class="flex flex-col items-center space-y-4">
    <div v-if="qrCodeUrl" class="bg-white p-4 rounded-lg shadow-md">
      <img
        :src="qrCodeUrl"
        :alt="`QR Code for ticket ${ticketId}`"
        class="w-64 h-64"
      />
    </div>

    <div class="text-center">
      <p class="text-sm text-gray-600 mb-2">Activation Code</p>
      <p class="text-2xl font-mono font-bold">{{ activationCode }}</p>
    </div>

    <button
      @click="handleDownloadPDF"
      class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Download PDF
    </button>
  </div>
</template>

<script setup lang="ts">
import { useTickets } from '../composables/useTickets';

interface Props {
  ticketId: number;
  qrCodeUrl: string;
  activationCode: string;
}

const props = defineProps<Props>();
const { downloadTicketPDF } = useTickets();

async function handleDownloadPDF() {
  await downloadTicketPDF(props.ticketId);
}
</script>
```

---

### 6.8 Plugin Registration

**File:** `src/plugins/ticket-management/index.ts`

```typescript
/**
 * Ticket Management Plugin.
 *
 * Implements IPlugin interface for plugin architecture.
 */
import type { Plugin } from '@core/plugin';
import type { IEventBus } from '@core/events';
import { ticketRoutes } from './routes';
import { useTicketStore } from './stores/ticketStore';

export const TicketManagementPlugin: Plugin = {
  name: 'ticket-management',
  version: '1.0.0',

  install(app, options) {
    // Register routes
    if (options.router) {
      ticketRoutes.forEach(route => {
        options.router.addRoute(route);
      });
    }

    // Setup event listeners
    if (options.eventBus) {
      const ticketStore = useTicketStore();
      const unsubscribe = ticketStore.setupEventListeners(options.eventBus);

      // Store cleanup function for plugin deactivation
      app.config.globalProperties.$ticketCleanup = unsubscribe;
    }
  },

  uninstall(app) {
    // Cleanup event listeners
    if (app.config.globalProperties.$ticketCleanup) {
      app.config.globalProperties.$ticketCleanup();
    }
  }
};
```

---

## Testing Strategy

### Unit Tests

**File:** `src/plugins/ticket-management/__tests__/unit/TicketService.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TicketService, TICKET_EVENTS } from '../../services/TicketService';
import type { IApiClient } from '@core/api';
import type { IEventBus } from '@core/events';

describe('TicketService', () => {
  let ticketService: TicketService;
  let mockApiClient: IApiClient;
  let mockEventBus: IEventBus;

  beforeEach(() => {
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn()
    } as any;

    mockEventBus = {
      emit: vi.fn(),
      on: vi.fn(() => vi.fn())
    } as any;

    ticketService = new TicketService(mockApiClient, mockEventBus);
  });

  describe('activateTicket', () => {
    it('should emit ACTIVATION_REQUESTED before API call', async () => {
      const ticket = { id: 1, status: 'active', activationCode: 'ABC123' };
      vi.mocked(mockApiClient.post).mockResolvedValue(ticket);

      await ticketService.activateTicket({ ticketId: 1 });

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        TICKET_EVENTS.ACTIVATION_REQUESTED,
        expect.objectContaining({ ticketId: 1 })
      );
    });

    it('should emit ACTIVATED after successful activation', async () => {
      const ticket = {
        id: 1,
        userId: 123,
        status: 'active',
        activationCode: 'ABC123',
        qrCodeUrl: 'https://example.com/qr/abc123'
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(ticket);

      await ticketService.activateTicket({ ticketId: 1 });

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        TICKET_EVENTS.ACTIVATED,
        expect.objectContaining({
          ticketId: 1,
          activationCode: 'ABC123'
        })
      );
    });

    it('should emit ACTIVATION_FAILED on error', async () => {
      const error = new Error('Activation failed');
      vi.mocked(mockApiClient.post).mockRejectedValue(error);

      await expect(
        ticketService.activateTicket({ ticketId: 1 })
      ).rejects.toThrow('Activation failed');

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        TICKET_EVENTS.ACTIVATION_FAILED,
        expect.objectContaining({
          ticketId: 1,
          error: 'Activation failed'
        })
      );
    });
  });
});
```

---

## Verification Checklist

```bash
# Run unit tests
npm run test:unit -- ticket-management

# Run E2E tests
npm run test:e2e -- ticket-management

# Build
npm run build

# Type check
npm run type-check
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Ticket types | [ ] | TypeScript interfaces |
| TicketService with EventBus | [ ] | Event-driven service |
| Ticket store with listeners | [ ] | Reactive state |
| Ticket composables | [ ] | Reusable logic |
| TicketList component | [ ] | Main view |
| TicketCard component | [ ] | Card display |
| TicketQRCode component | [ ] | QR code display |
| ActivateTicketDialog | [ ] | Activation flow |
| Plugin registration | [ ] | IPlugin implementation |
| Unit tests | [ ] | 95%+ coverage |
| E2E tests | [ ] | User flows |

---

## Event-Driven Benefits

**Decoupling:**
- TicketService emits events, doesn't know about stores
- Store listens to events, updates state automatically
- Easy to add analytics, logging, etc.

**Real-time Updates:**
- UI updates automatically when events fire
- Multiple components can react to same event
- Consistent state across application

**Testability:**
- Mock EventBus in tests
- Verify event emission without integration tests
- Test components independently

---

## Next Sprint

[Sprint 7: Booking Management Plugin](./sprint-7-booking-management.md) - Event-driven booking system for user app.
