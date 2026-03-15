# Sprint 7: Booking Management Plugin

**Goal:** Build booking management plugin for creating, viewing, and managing bookings with event-driven architecture.

**Dependencies:** Sprint 1 (API Client), Sprint 4 (User Cabinet), Sprint 6 (Ticket Management), Core SDK Sprint 4 (EventBus)

---

## Objectives

- [ ] Booking Management plugin (implements IPlugin)
- [ ] Protected routes with auth guard
- [ ] Create new bookings with availability check
- [ ] View all bookings (pending, confirmed, completed, cancelled)
- [ ] Booking details with confirmation code
- [ ] Booking cancellation with refund handling
- [ ] Event-driven architecture integration
- [ ] Calendar view for bookings
- [ ] E2E tests for booking features

---

## Tasks

### 7.1 Booking Management Plugin Structure

```
src/plugins/booking-management/
├── index.ts                       # Plugin entry with IPlugin
├── routes.ts                      # Protected booking routes
├── services/
│   ├── BookingService.ts          # Booking operations with EventBus
│   └── IBookingService.ts         # Service interface (LSP)
├── stores/
│   └── bookingStore.ts            # Booking state with event listeners
├── composables/
│   └── useBookings.ts             # Composable for booking logic
├── components/
│   ├── BookingList.vue            # List of all bookings
│   ├── BookingCard.vue            # Individual booking card
│   ├── BookingDetails.vue         # Full booking details view
│   ├── BookingCalendar.vue        # Calendar view
│   ├── CreateBookingForm.vue      # Multi-step booking form
│   ├── BookingConfirmation.vue    # Confirmation display
│   └── CancelBookingDialog.vue    # Cancellation dialog
├── types/
│   └── booking.types.ts           # Booking TypeScript types
└── __tests__/
    ├── unit/
    │   ├── BookingService.test.ts
    │   └── bookingStore.test.ts
    └── e2e/
        └── booking-management.spec.ts
```

---

### 7.2 Booking Types

**File:** `src/plugins/booking-management/types/booking.types.ts`

```typescript
/**
 * Booking domain types for user app.
 */

export enum BookingStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show'
}

export interface Booking {
  id: number;
  userId: number;
  resourceType: string;
  resourceId: number;
  resourceName: string;
  status: BookingStatus;
  startTime: string;
  endTime: string;
  price: string;
  currency: string;
  confirmationCode?: string;
  location?: string;
  notes?: string;
  createdAt: string;
  confirmedAt?: string;
  completedAt?: string;
  cancelledAt?: string;
  cancellationReason?: string;
  refundAmount?: string;
}

export interface BookingSlot {
  startTime: string;
  endTime: string;
  available: boolean;
  price: string;
  currency: string;
}

export interface CreateBookingRequest {
  resourceType: string;
  resourceId: number;
  startTime: string;
  endTime: string;
  notes?: string;
}

export interface ConfirmBookingRequest {
  bookingId: number;
  paymentId?: number;
}

export interface CancelBookingRequest {
  bookingId: number;
  reason?: string;
}

export interface BookingFilters {
  status?: BookingStatus;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export interface AvailabilityQuery {
  resourceType: string;
  resourceId: number;
  date: string;
}
```

---

### 7.3 Booking Service with EventBus

**File:** `src/plugins/booking-management/services/IBookingService.ts`

```typescript
/**
 * Booking service interface (LSP).
 */
import type {
  Booking,
  BookingSlot,
  CreateBookingRequest,
  ConfirmBookingRequest,
  CancelBookingRequest,
  AvailabilityQuery
} from '../types/booking.types';

export interface IBookingService {
  /**
   * Get all bookings for current user.
   */
  getMyBookings(): Promise<Booking[]>;

  /**
   * Get booking by ID.
   */
  getBookingById(bookingId: number): Promise<Booking>;

  /**
   * Check availability for a resource.
   */
  checkAvailability(query: AvailabilityQuery): Promise<BookingSlot[]>;

  /**
   * Create a new booking.
   */
  createBooking(request: CreateBookingRequest): Promise<Booking>;

  /**
   * Confirm a pending booking.
   */
  confirmBooking(request: ConfirmBookingRequest): Promise<Booking>;

  /**
   * Cancel a booking.
   */
  cancelBooking(request: CancelBookingRequest): Promise<Booking>;
}
```

**File:** `src/plugins/booking-management/services/BookingService.ts`

```typescript
/**
 * Booking service implementation with event-driven architecture.
 */
import type { IApiClient } from '@core/api';
import type { IEventBus } from '@core/events';
import type { IBookingService } from './IBookingService';
import type {
  Booking,
  BookingSlot,
  CreateBookingRequest,
  ConfirmBookingRequest,
  CancelBookingRequest,
  AvailabilityQuery
} from '../types/booking.types';

/**
 * Booking domain events.
 */
export const BOOKING_EVENTS = {
  CREATION_STARTED: 'booking:creation:started',
  CREATED: 'booking:created',
  CREATION_FAILED: 'booking:creation:failed',
  CONFIRMATION_REQUESTED: 'booking:confirmation:requested',
  CONFIRMED: 'booking:confirmed',
  CONFIRMATION_FAILED: 'booking:confirmation:failed',
  CANCELLATION_REQUESTED: 'booking:cancellation:requested',
  CANCELLED: 'booking:cancelled',
  CANCELLATION_FAILED: 'booking:cancellation:failed',
  AVAILABILITY_CHECKED: 'booking:availability:checked'
} as const;

export interface BookingCreatedEvent {
  bookingId: number;
  userId: number;
  resourceType: string;
  resourceId: number;
  startTime: string;
  endTime: string;
  price: string;
  timestamp: string;
}

export interface BookingConfirmedEvent {
  bookingId: number;
  userId: number;
  confirmationCode: string;
  timestamp: string;
}

export interface BookingCancelledEvent {
  bookingId: number;
  userId: number;
  refundAmount?: string;
  reason?: string;
  timestamp: string;
}

export class BookingService implements IBookingService {
  constructor(
    private readonly apiClient: IApiClient,
    private readonly eventBus: IEventBus
  ) {}

  async getMyBookings(): Promise<Booking[]> {
    return this.apiClient.get<Booking[]>('/api/v1/bookings');
  }

  async getBookingById(bookingId: number): Promise<Booking> {
    return this.apiClient.get<Booking>(`/api/v1/bookings/${bookingId}`);
  }

  async checkAvailability(query: AvailabilityQuery): Promise<BookingSlot[]> {
    const slots = await this.apiClient.get<BookingSlot[]>(
      `/api/v1/bookings/availability`,
      { params: query }
    );

    // Emit event for analytics
    this.eventBus.emit(BOOKING_EVENTS.AVAILABILITY_CHECKED, {
      resourceType: query.resourceType,
      resourceId: query.resourceId,
      date: query.date,
      availableSlots: slots.filter(s => s.available).length,
      timestamp: new Date().toISOString()
    });

    return slots;
  }

  async createBooking(request: CreateBookingRequest): Promise<Booking> {
    // Emit event BEFORE creation
    this.eventBus.emit(BOOKING_EVENTS.CREATION_STARTED, {
      resourceType: request.resourceType,
      resourceId: request.resourceId,
      startTime: request.startTime,
      endTime: request.endTime,
      timestamp: new Date().toISOString()
    });

    try {
      const booking = await this.apiClient.post<Booking>(
        '/api/v1/bookings',
        request
      );

      // Emit event AFTER successful creation
      this.eventBus.emit(BOOKING_EVENTS.CREATED, {
        bookingId: booking.id,
        userId: booking.userId,
        resourceType: booking.resourceType,
        resourceId: booking.resourceId,
        startTime: booking.startTime,
        endTime: booking.endTime,
        price: booking.price,
        timestamp: new Date().toISOString()
      } as BookingCreatedEvent);

      return booking;

    } catch (error: any) {
      // Emit failure event
      this.eventBus.emit(BOOKING_EVENTS.CREATION_FAILED, {
        resourceType: request.resourceType,
        resourceId: request.resourceId,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async confirmBooking(request: ConfirmBookingRequest): Promise<Booking> {
    // Emit event BEFORE confirmation
    this.eventBus.emit(BOOKING_EVENTS.CONFIRMATION_REQUESTED, {
      bookingId: request.bookingId,
      paymentId: request.paymentId,
      timestamp: new Date().toISOString()
    });

    try {
      const booking = await this.apiClient.post<Booking>(
        `/api/v1/bookings/${request.bookingId}/confirm`,
        { paymentId: request.paymentId }
      );

      // Emit event AFTER successful confirmation
      this.eventBus.emit(BOOKING_EVENTS.CONFIRMED, {
        bookingId: booking.id,
        userId: booking.userId,
        confirmationCode: booking.confirmationCode!,
        timestamp: new Date().toISOString()
      } as BookingConfirmedEvent);

      return booking;

    } catch (error: any) {
      // Emit failure event
      this.eventBus.emit(BOOKING_EVENTS.CONFIRMATION_FAILED, {
        bookingId: request.bookingId,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async cancelBooking(request: CancelBookingRequest): Promise<Booking> {
    // Emit event BEFORE cancellation
    this.eventBus.emit(BOOKING_EVENTS.CANCELLATION_REQUESTED, {
      bookingId: request.bookingId,
      reason: request.reason,
      timestamp: new Date().toISOString()
    });

    try {
      const booking = await this.apiClient.post<Booking>(
        `/api/v1/bookings/${request.bookingId}/cancel`,
        { reason: request.reason }
      );

      // Emit event AFTER successful cancellation
      this.eventBus.emit(BOOKING_EVENTS.CANCELLED, {
        bookingId: booking.id,
        userId: booking.userId,
        refundAmount: booking.refundAmount,
        reason: request.reason,
        timestamp: new Date().toISOString()
      } as BookingCancelledEvent);

      return booking;

    } catch (error: any) {
      // Emit failure event
      this.eventBus.emit(BOOKING_EVENTS.CANCELLATION_FAILED, {
        bookingId: request.bookingId,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }
}
```

---

### 7.4 Booking Store with Event Listeners

**File:** `src/plugins/booking-management/stores/bookingStore.ts`

```typescript
/**
 * Booking store with event-driven architecture.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { IEventBus } from '@core/events';
import type { Booking, BookingStatus, BookingFilters, BookingSlot } from '../types/booking.types';
import { BOOKING_EVENTS } from '../services/BookingService';

export const useBookingStore = defineStore('bookings', () => {
  // State
  const bookings = ref<Booking[]>([]);
  const selectedBooking = ref<Booking | null>(null);
  const availableSlots = ref<BookingSlot[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<BookingFilters>({});

  // Computed
  const confirmedBookings = computed(() =>
    bookings.value.filter(b => b.status === 'confirmed')
  );

  const pendingBookings = computed(() =>
    bookings.value.filter(b => b.status === 'pending')
  );

  const pastBookings = computed(() =>
    bookings.value.filter(b =>
      b.status === 'completed' || b.status === 'cancelled' || b.status === 'no_show'
    )
  );

  const upcomingBookings = computed(() => {
    const now = new Date();
    return confirmedBookings.value.filter(b =>
      new Date(b.startTime) > now
    ).sort((a, b) =>
      new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
    );
  });

  const filteredBookings = computed(() => {
    let result = bookings.value;

    if (filters.value.status) {
      result = result.filter(b => b.status === filters.value.status);
    }

    if (filters.value.dateFrom) {
      result = result.filter(b =>
        new Date(b.startTime) >= new Date(filters.value.dateFrom!)
      );
    }

    if (filters.value.dateTo) {
      result = result.filter(b =>
        new Date(b.startTime) <= new Date(filters.value.dateTo!)
      );
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase();
      result = result.filter(b =>
        b.resourceName.toLowerCase().includes(search) ||
        b.confirmationCode?.toLowerCase().includes(search)
      );
    }

    return result;
  });

  /**
   * Setup event listeners for bookings.
   */
  function setupEventListeners(eventBus: IEventBus): () => void {
    const unsubscribers: Array<() => void> = [];

    // Listen to booking creation
    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CREATION_STARTED, () => {
        loading.value = true;
        error.value = null;
      })
    );

    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CREATED, (event: any) => {
        loading.value = false;
        // Booking will be loaded via refresh
      })
    );

    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CREATION_FAILED, (event: any) => {
        error.value = event.error;
        loading.value = false;
      })
    );

    // Listen to booking confirmation
    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CONFIRMATION_REQUESTED, () => {
        loading.value = true;
        error.value = null;
      })
    );

    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CONFIRMED, (event: any) => {
        // Update booking in list
        const index = bookings.value.findIndex(b => b.id === event.bookingId);
        if (index !== -1) {
          bookings.value[index].status = 'confirmed';
          bookings.value[index].confirmationCode = event.confirmationCode;
        }

        // Update selected booking
        if (selectedBooking.value?.id === event.bookingId) {
          selectedBooking.value.status = 'confirmed';
          selectedBooking.value.confirmationCode = event.confirmationCode;
        }

        loading.value = false;
      })
    );

    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CONFIRMATION_FAILED, (event: any) => {
        error.value = event.error;
        loading.value = false;
      })
    );

    // Listen to booking cancellation
    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CANCELLATION_REQUESTED, () => {
        loading.value = true;
        error.value = null;
      })
    );

    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CANCELLED, (event: any) => {
        // Update booking in list
        const index = bookings.value.findIndex(b => b.id === event.bookingId);
        if (index !== -1) {
          bookings.value[index].status = 'cancelled';
          bookings.value[index].refundAmount = event.refundAmount;
        }

        // Update selected booking
        if (selectedBooking.value?.id === event.bookingId) {
          selectedBooking.value.status = 'cancelled';
          selectedBooking.value.refundAmount = event.refundAmount;
        }

        loading.value = false;
      })
    );

    unsubscribers.push(
      eventBus.on(BOOKING_EVENTS.CANCELLATION_FAILED, (event: any) => {
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
  function setBookings(newBookings: Booking[]) {
    bookings.value = newBookings;
  }

  function setSelectedBooking(booking: Booking | null) {
    selectedBooking.value = booking;
  }

  function setAvailableSlots(slots: BookingSlot[]) {
    availableSlots.value = slots;
  }

  function setFilters(newFilters: BookingFilters) {
    filters.value = { ...filters.value, ...newFilters };
  }

  function clearFilters() {
    filters.value = {};
  }

  return {
    // State
    bookings,
    selectedBooking,
    availableSlots,
    loading,
    error,
    filters,

    // Computed
    confirmedBookings,
    pendingBookings,
    pastBookings,
    upcomingBookings,
    filteredBookings,

    // Actions
    setBookings,
    setSelectedBooking,
    setAvailableSlots,
    setFilters,
    clearFilters,
    setupEventListeners
  };
});
```

---

### 7.5 Booking Composable

**File:** `src/plugins/booking-management/composables/useBookings.ts`

```typescript
/**
 * Composable for booking operations.
 */
import { useBookingStore } from '../stores/bookingStore';
import { useApi } from '@core/api';
import type {
  CreateBookingRequest,
  ConfirmBookingRequest,
  CancelBookingRequest,
  AvailabilityQuery
} from '../types/booking.types';

export function useBookings() {
  const bookingStore = useBookingStore();
  const api = useApi();

  /**
   * Load all bookings for current user.
   */
  async function loadBookings() {
    bookingStore.loading = true;
    bookingStore.error = null;

    try {
      const bookings = await api.bookings.getMyBookings();
      bookingStore.setBookings(bookings);
    } catch (err: any) {
      bookingStore.error = err.message;
      throw err;
    } finally {
      bookingStore.loading = false;
    }
  }

  /**
   * Load single booking by ID.
   */
  async function loadBooking(bookingId: number) {
    bookingStore.loading = true;
    bookingStore.error = null;

    try {
      const booking = await api.bookings.getBookingById(bookingId);
      bookingStore.setSelectedBooking(booking);
    } catch (err: any) {
      bookingStore.error = err.message;
      throw err;
    } finally {
      bookingStore.loading = false;
    }
  }

  /**
   * Check availability for a resource.
   */
  async function checkAvailability(query: AvailabilityQuery) {
    bookingStore.loading = true;
    bookingStore.error = null;

    try {
      const slots = await api.bookings.checkAvailability(query);
      bookingStore.setAvailableSlots(slots);
      return slots;
    } catch (err: any) {
      bookingStore.error = err.message;
      throw err;
    } finally {
      bookingStore.loading = false;
    }
  }

  /**
   * Create a new booking.
   */
  async function createBooking(request: CreateBookingRequest) {
    return await api.bookings.createBooking(request);
  }

  /**
   * Confirm a pending booking.
   */
  async function confirmBooking(request: ConfirmBookingRequest) {
    return await api.bookings.confirmBooking(request);
  }

  /**
   * Cancel a booking.
   */
  async function cancelBooking(request: CancelBookingRequest) {
    return await api.bookings.cancelBooking(request);
  }

  return {
    loadBookings,
    loadBooking,
    checkAvailability,
    createBooking,
    confirmBooking,
    cancelBooking
  };
}
```

---

### 7.6 Booking List Component

**File:** `src/plugins/booking-management/components/BookingList.vue`

```vue
<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-bold">My Bookings</h2>
      <button
        @click="handleCreateBooking"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        New Booking
      </button>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200">
      <nav class="-mb-px flex space-x-8">
        <button
          @click="activeTab = 'upcoming'"
          :class="[
            'py-4 px-1 border-b-2 font-medium text-sm',
            activeTab === 'upcoming'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]"
        >
          Upcoming ({{ upcomingBookings.length }})
        </button>
        <button
          @click="activeTab = 'pending'"
          :class="[
            'py-4 px-1 border-b-2 font-medium text-sm',
            activeTab === 'pending'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]"
        >
          Pending ({{ pendingBookings.length }})
        </button>
        <button
          @click="activeTab = 'past'"
          :class="[
            'py-4 px-1 border-b-2 font-medium text-sm',
            activeTab === 'past'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]"
        >
          Past
        </button>
      </nav>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-gray-500">Loading bookings...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-800">{{ error }}</p>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="displayedBookings.length === 0"
      class="text-center py-12 bg-gray-50 rounded-md"
    >
      <p class="text-gray-500">No bookings found</p>
    </div>

    <!-- Booking cards -->
    <div v-else class="space-y-4">
      <BookingCard
        v-for="booking in displayedBookings"
        :key="booking.id"
        :booking="booking"
        @confirm="handleConfirm"
        @cancel="handleCancel"
        @view-details="handleViewDetails"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useBookingStore } from '../stores/bookingStore';
import { useBookings } from '../composables/useBookings';
import BookingCard from './BookingCard.vue';
import type { Booking } from '../types/booking.types';

const router = useRouter();
const bookingStore = useBookingStore();
const { loadBookings, confirmBooking, cancelBooking } = useBookings();

const activeTab = ref<'upcoming' | 'pending' | 'past'>('upcoming');

// Computed
const loading = computed(() => bookingStore.loading);
const error = computed(() => bookingStore.error);
const upcomingBookings = computed(() => bookingStore.upcomingBookings);
const pendingBookings = computed(() => bookingStore.pendingBookings);
const pastBookings = computed(() => bookingStore.pastBookings);

const displayedBookings = computed(() => {
  switch (activeTab.value) {
    case 'upcoming':
      return upcomingBookings.value;
    case 'pending':
      return pendingBookings.value;
    case 'past':
      return pastBookings.value;
    default:
      return [];
  }
});

// Methods
function handleCreateBooking() {
  router.push('/bookings/create');
}

async function handleConfirm(booking: Booking) {
  try {
    await confirmBooking({ bookingId: booking.id });
    await loadBookings();
  } catch (err) {
    console.error('Failed to confirm booking:', err);
  }
}

async function handleCancel(booking: Booking) {
  try {
    await cancelBooking({ bookingId: booking.id });
    await loadBookings();
  } catch (err) {
    console.error('Failed to cancel booking:', err);
  }
}

function handleViewDetails(booking: Booking) {
  router.push(`/bookings/${booking.id}`);
}

// Lifecycle
onMounted(() => {
  loadBookings();
});
</script>
```

---

### 7.7 Create Booking Form Component

**File:** `src/plugins/booking-management/components/CreateBookingForm.vue`

```vue
<template>
  <div class="max-w-2xl mx-auto">
    <h2 class="text-2xl font-bold mb-6">Create New Booking</h2>

    <div class="bg-white rounded-lg shadow-md p-6">
      <!-- Step 1: Select Resource -->
      <div v-if="step === 1" class="space-y-4">
        <h3 class="text-lg font-semibold">Select Resource</h3>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Resource Type
          </label>
          <select
            v-model="form.resourceType"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Select type...</option>
            <option value="room">Room</option>
            <option value="equipment">Equipment</option>
            <option value="service">Service</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Resource
          </label>
          <select
            v-model="form.resourceId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Select resource...</option>
            <!-- Resources would be loaded based on type -->
          </select>
        </div>

        <button
          @click="nextStep"
          :disabled="!form.resourceType || !form.resourceId"
          class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300"
        >
          Next: Select Date & Time
        </button>
      </div>

      <!-- Step 2: Select Date & Time -->
      <div v-if="step === 2" class="space-y-4">
        <h3 class="text-lg font-semibold">Select Date & Time</h3>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Date
          </label>
          <input
            v-model="selectedDate"
            type="date"
            :min="minDate"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="loadAvailability"
          />
        </div>

        <!-- Available time slots -->
        <div v-if="availableSlots.length > 0" class="space-y-2">
          <p class="text-sm font-medium text-gray-700">Available Times:</p>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="slot in availableSlots"
              :key="slot.startTime"
              @click="selectSlot(slot)"
              :disabled="!slot.available"
              :class="[
                'px-3 py-2 border rounded-md text-sm',
                selectedSlot === slot
                  ? 'bg-blue-600 text-white border-blue-600'
                  : slot.available
                  ? 'border-gray-300 hover:border-blue-500'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              ]"
            >
              {{ formatTime(slot.startTime) }}
            </button>
          </div>
        </div>

        <div class="flex gap-2">
          <button
            @click="prevStep"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Back
          </button>
          <button
            @click="nextStep"
            :disabled="!selectedSlot"
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300"
          >
            Next: Confirm
          </button>
        </div>
      </div>

      <!-- Step 3: Confirm & Create -->
      <div v-if="step === 3" class="space-y-4">
        <h3 class="text-lg font-semibold">Confirm Booking</h3>

        <div class="bg-gray-50 rounded-md p-4 space-y-2">
          <div class="flex justify-between">
            <span class="text-gray-600">Resource:</span>
            <span class="font-medium">{{ form.resourceType }} #{{ form.resourceId }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Date & Time:</span>
            <span class="font-medium">
              {{ formatDateTime(selectedSlot?.startTime) }}
            </span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Price:</span>
            <span class="font-medium">
              {{ selectedSlot?.price }} {{ selectedSlot?.currency }}
            </span>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Notes (optional)
          </label>
          <textarea
            v-model="form.notes"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="Any special requests or notes..."
          ></textarea>
        </div>

        <div class="flex gap-2">
          <button
            @click="prevStep"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Back
          </button>
          <button
            @click="handleCreateBooking"
            :disabled="loading"
            class="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300"
          >
            {{ loading ? 'Creating...' : 'Create Booking' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useBookingStore } from '../stores/bookingStore';
import { useBookings } from '../composables/useBookings';
import type { BookingSlot, CreateBookingRequest } from '../types/booking.types';

const router = useRouter();
const bookingStore = useBookingStore();
const { checkAvailability, createBooking } = useBookings();

const step = ref(1);
const selectedDate = ref('');
const selectedSlot = ref<BookingSlot | null>(null);

const form = ref<CreateBookingRequest>({
  resourceType: '',
  resourceId: 0,
  startTime: '',
  endTime: '',
  notes: ''
});

const loading = computed(() => bookingStore.loading);
const availableSlots = computed(() => bookingStore.availableSlots);

const minDate = computed(() => {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return tomorrow.toISOString().split('T')[0];
});

async function loadAvailability() {
  if (!selectedDate.value) return;

  await checkAvailability({
    resourceType: form.value.resourceType,
    resourceId: form.value.resourceId,
    date: selectedDate.value
  });
}

function selectSlot(slot: BookingSlot) {
  selectedSlot.value = slot;
  form.value.startTime = slot.startTime;
  form.value.endTime = slot.endTime;
}

async function handleCreateBooking() {
  try {
    const booking = await createBooking(form.value);
    router.push(`/bookings/${booking.id}`);
  } catch (err) {
    console.error('Failed to create booking:', err);
  }
}

function nextStep() {
  if (step.value < 3) step.value++;
}

function prevStep() {
  if (step.value > 1) step.value--;
}

function formatTime(dateTime: string): string {
  return new Date(dateTime).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDateTime(dateTime?: string): string {
  if (!dateTime) return '';
  return new Date(dateTime).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short'
  });
}
</script>
```

---

### 7.8 Plugin Registration

**File:** `src/plugins/booking-management/index.ts`

```typescript
/**
 * Booking Management Plugin.
 *
 * Implements IPlugin interface for plugin architecture.
 */
import type { Plugin } from '@core/plugin';
import type { IEventBus } from '@core/events';
import { bookingRoutes } from './routes';
import { useBookingStore } from './stores/bookingStore';

export const BookingManagementPlugin: Plugin = {
  name: 'booking-management',
  version: '1.0.0',

  install(app, options) {
    // Register routes
    if (options.router) {
      bookingRoutes.forEach(route => {
        options.router.addRoute(route);
      });
    }

    // Setup event listeners
    if (options.eventBus) {
      const bookingStore = useBookingStore();
      const unsubscribe = bookingStore.setupEventListeners(options.eventBus);

      // Store cleanup function for plugin deactivation
      app.config.globalProperties.$bookingCleanup = unsubscribe;
    }
  },

  uninstall(app) {
    // Cleanup event listeners
    if (app.config.globalProperties.$bookingCleanup) {
      app.config.globalProperties.$bookingCleanup();
    }
  }
};
```

---

## Testing Strategy

### Unit Tests

**File:** `src/plugins/booking-management/__tests__/unit/BookingService.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BookingService, BOOKING_EVENTS } from '../../services/BookingService';
import type { IApiClient } from '@core/api';
import type { IEventBus } from '@core/events';

describe('BookingService', () => {
  let bookingService: BookingService;
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

    bookingService = new BookingService(mockApiClient, mockEventBus);
  });

  describe('createBooking', () => {
    it('should emit CREATION_STARTED before API call', async () => {
      const booking = { id: 1, status: 'pending' };
      vi.mocked(mockApiClient.post).mockResolvedValue(booking);

      await bookingService.createBooking({
        resourceType: 'room',
        resourceId: 1,
        startTime: '2025-01-01T10:00:00Z',
        endTime: '2025-01-01T11:00:00Z'
      });

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        BOOKING_EVENTS.CREATION_STARTED,
        expect.objectContaining({
          resourceType: 'room',
          resourceId: 1
        })
      );
    });

    it('should emit CREATED after successful creation', async () => {
      const booking = {
        id: 1,
        userId: 123,
        resourceType: 'room',
        resourceId: 1,
        status: 'pending',
        startTime: '2025-01-01T10:00:00Z',
        endTime: '2025-01-01T11:00:00Z',
        price: '50.00',
        currency: 'USD'
      };
      vi.mocked(mockApiClient.post).mockResolvedValue(booking);

      await bookingService.createBooking({
        resourceType: 'room',
        resourceId: 1,
        startTime: '2025-01-01T10:00:00Z',
        endTime: '2025-01-01T11:00:00Z'
      });

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        BOOKING_EVENTS.CREATED,
        expect.objectContaining({
          bookingId: 1,
          resourceType: 'room'
        })
      );
    });

    it('should emit CREATION_FAILED on error', async () => {
      const error = new Error('Creation failed');
      vi.mocked(mockApiClient.post).mockRejectedValue(error);

      await expect(
        bookingService.createBooking({
          resourceType: 'room',
          resourceId: 1,
          startTime: '2025-01-01T10:00:00Z',
          endTime: '2025-01-01T11:00:00Z'
        })
      ).rejects.toThrow('Creation failed');

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        BOOKING_EVENTS.CREATION_FAILED,
        expect.objectContaining({
          error: 'Creation failed'
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
npm run test:unit -- booking-management

# Run E2E tests
npm run test:e2e -- booking-management

# Build
npm run build

# Type check
npm run type-check
```

---

## Deliverables

| Item | Status | Notes |
|------|--------|-------|
| Booking types | [ ] | TypeScript interfaces |
| BookingService with EventBus | [ ] | Event-driven service |
| Booking store with listeners | [ ] | Reactive state |
| Booking composables | [ ] | Reusable logic |
| BookingList component | [ ] | Main view with tabs |
| BookingCard component | [ ] | Card display |
| BookingCalendar component | [ ] | Calendar view |
| CreateBookingForm | [ ] | Multi-step form |
| CancelBookingDialog | [ ] | Cancellation flow |
| Plugin registration | [ ] | IPlugin implementation |
| Unit tests | [ ] | 95%+ coverage |
| E2E tests | [ ] | User flows |

---

## Complete Event-Driven Architecture Summary

**All Sprints Complete!** 🎉

The project now has comprehensive event-driven architecture across:

**Frontend (Admin App):**
- User management with status changes
- Subscription lifecycle with cancellations
- Invoice management with refunds

**Frontend (User App):**
- Ticket management with activation
- Booking management with confirmation/cancellation

**Frontend (Core SDK):**
- EventBus infrastructure
- ApiClient with event emission
- Validation service

**Backend:**
- EventDispatcher infrastructure
- User state event handlers
- Subscription & invoice event handlers
- Ticket & booking event handlers

**Benefits Achieved:**
- ✅ Decoupled, maintainable code
- ✅ Complete audit trails with timestamps
- ✅ Real-time UI updates
- ✅ Easy testing with mocked dependencies
- ✅ SOLID principles throughout
- ✅ Extensibility without modifying existing code

---

**Project Ready for Implementation!** 🚀
