# Sprint 2: Wizard Plugin - File Upload & Validation

**Goal:** Build the first plugin with multi-step wizard for file upload, validation, and GDPR consent.

---

## Objectives

- [ ] Wizard plugin implementing IPlugin interface
- [ ] Step 1: File upload with drag & drop (images only)
- [ ] Step 2: Email input with GDPR consent
- [ ] Client-side and server-side validation
- [ ] Zod schemas for validation
- [ ] Wizard state management (Pinia)
- [ ] Navigation between steps with validation
- [ ] Playwright E2E test for complete wizard flow
- [ ] Responsive design with Tailwind CSS

---

## Tasks

### 2.1 Wizard Plugin Structure

```
src/plugins/wizard/
├── index.ts                      # Plugin entry (implements IPlugin)
├── routes.ts                     # Route definitions
├── store/
│   ├── wizardStore.ts            # Wizard state management
│   ├── wizardStore.spec.ts       # Store unit tests
│   └── types.ts                  # Store types
├── components/
│   ├── WizardContainer.vue       # Main container with progress
│   ├── WizardStep.vue            # Generic step wrapper
│   ├── steps/
│   │   ├── StepUpload.vue        # Step 1: File upload
│   │   └── StepGdpr.vue          # Step 2: Email & GDPR
│   └── shared/
│       ├── FileUpload.vue        # Drag & drop file upload
│       ├── ProgressBar.vue       # Step progress indicator
│       └── ValidationError.vue   # Error display component
├── composables/
│   ├── useWizard.ts              # Wizard navigation logic
│   ├── useFileUpload.ts          # File handling & validation
│   └── useValidation.ts          # Form validation
├── schemas/
│   └── validation.schemas.ts     # Zod validation schemas
└── __tests__/
    └── e2e/
        └── wizard-flow.spec.ts   # Playwright E2E test
```

---

### 2.2 Validation Schemas (Zod)

**File:** `src/plugins/wizard/schemas/validation.schemas.ts`

```typescript
import { z } from 'zod';

// Step 1: File Upload
export const fileUploadSchema = z.object({
  files: z
    .array(
      z.object({
        name: z.string(),
        size: z.number().max(5 * 1024 * 1024, 'File must be less than 5MB'),
        type: z.string().refine((type) => type.startsWith('image/'), {
          message: 'Only image files are allowed',
        }),
      })
    )
    .min(1, 'At least one file is required')
    .max(5, 'Maximum 5 files allowed'),
  description: z.string().optional(),
});

// Step 2: GDPR & Email
export const gdprSchema = z.object({
  email: z.string().email('Invalid email address'),
  gdprConsent: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the privacy policy' }),
  }),
});

export type FileUploadData = z.infer<typeof fileUploadSchema>;
export type GdprData = z.infer<typeof gdprSchema>;
```

---

### 2.3 Wizard Store (Pinia)

**File:** `src/plugins/wizard/store/wizardStore.ts`

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { FileUploadData, GdprData } from '../schemas/validation.schemas';

export interface WizardState {
  currentStep: number;
  step1Data: Partial<FileUploadData>;
  step2Data: Partial<GdprData>;
  isValidating: boolean;
  errors: Record<string, string[]>;
}

export const useWizardStore = defineStore('wizard', () => {
  // State
  const currentStep = ref(1);
  const step1Data = ref<Partial<FileUploadData>>({});
  const step2Data = ref<Partial<GdprData>>({});
  const isValidating = ref(false);
  const errors = ref<Record<string, string[]>>({});

  // Computed
  const totalSteps = computed(() => 2); // Will increase in Sprint 3
  const canGoNext = computed(() => {
    if (currentStep.value === 1) {
      return step1Data.value.files && step1Data.value.files.length > 0;
    }
    if (currentStep.value === 2) {
      return step2Data.value.email && step2Data.value.gdprConsent === true;
    }
    return false;
  });

  const canGoBack = computed(() => currentStep.value > 1);

  const progress = computed(() => (currentStep.value / totalSteps.value) * 100);

  // Actions
  function nextStep() {
    if (canGoNext.value && currentStep.value < totalSteps.value) {
      currentStep.value++;
    }
  }

  function prevStep() {
    if (canGoBack.value) {
      currentStep.value--;
      errors.value = {};
    }
  }

  function goToStep(step: number) {
    if (step >= 1 && step <= totalSteps.value) {
      currentStep.value = step;
    }
  }

  function updateStep1(data: Partial<FileUploadData>) {
    step1Data.value = { ...step1Data.value, ...data };
  }

  function updateStep2(data: Partial<GdprData>) {
    step2Data.value = { ...step2Data.value, ...data };
  }

  function setErrors(newErrors: Record<string, string[]>) {
    errors.value = newErrors;
  }

  function reset() {
    currentStep.value = 1;
    step1Data.value = {};
    step2Data.value = {};
    errors.value = {};
    isValidating.value = false;
  }

  return {
    // State
    currentStep,
    step1Data,
    step2Data,
    isValidating,
    errors,

    // Computed
    totalSteps,
    canGoNext,
    canGoBack,
    progress,

    // Actions
    nextStep,
    prevStep,
    goToStep,
    updateStep1,
    updateStep2,
    setErrors,
    reset,
  };
});
```

---

### 2.4 Wizard Composable

**File:** `src/plugins/wizard/composables/useWizard.ts`

```typescript
import { useWizardStore } from '../store/wizardStore';
import { fileUploadSchema, gdprSchema } from '../schemas/validation.schemas';
import { useApi } from '@/core/api';

export function useWizard() {
  const store = useWizardStore();
  const api = useApi();

  async function validateCurrentStep(): Promise<boolean> {
    store.isValidating = true;
    store.setErrors({});

    try {
      if (store.currentStep === 1) {
        fileUploadSchema.parse(store.step1Data);
        return true;
      } else if (store.currentStep === 2) {
        gdprSchema.parse(store.step2Data);
        return true;
      }
      return false;
    } catch (error: any) {
      if (error.errors) {
        const errors: Record<string, string[]> = {};
        error.errors.forEach((err: any) => {
          const field = err.path.join('.');
          if (!errors[field]) {
            errors[field] = [];
          }
          errors[field].push(err.message);
        });
        store.setErrors(errors);
      }
      return false;
    } finally {
      store.isValidating = false;
    }
  }

  async function goNext() {
    const isValid = await validateCurrentStep();
    if (isValid) {
      store.nextStep();
    }
  }

  function goBack() {
    store.prevStep();
  }

  return {
    store,
    validateCurrentStep,
    goNext,
    goBack,
  };
}
```

---

### 2.5 File Upload Component

**File:** `src/plugins/wizard/components/shared/FileUpload.vue`

```vue
<template>
  <div
    class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors"
    :class="{ 'border-primary-500 bg-primary-50': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInput"
      type="file"
      multiple
      accept="image/*"
      class="hidden"
      @change="handleFileInput"
    />

    <div v-if="files.length === 0">
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
      <p class="mt-2 text-sm text-gray-600">
        Drag and drop your images here, or
        <button
          type="button"
          class="text-primary-600 hover:text-primary-500"
          @click="$refs.fileInput.click()"
        >
          browse
        </button>
      </p>
      <p class="text-xs text-gray-500 mt-1">
        PNG, JPG, GIF up to 5MB (Max 5 files)
      </p>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="(file, index) in files"
        :key="index"
        class="flex items-center justify-between p-3 bg-white rounded-md shadow-sm"
      >
        <div class="flex items-center space-x-3">
          <img
            v-if="file.preview"
            :src="file.preview"
            :alt="file.name"
            class="w-12 h-12 object-cover rounded"
          />
          <div class="text-left">
            <p class="text-sm font-medium text-gray-900">{{ file.name }}</p>
            <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
          </div>
        </div>
        <button
          type="button"
          class="text-red-600 hover:text-red-500"
          @click="removeFile(index)"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <button
        v-if="files.length < 5"
        type="button"
        class="mt-4 text-sm text-primary-600 hover:text-primary-500"
        @click="$refs.fileInput.click()"
      >
        + Add more files
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

interface FileWithPreview extends File {
  preview?: string;
}

const props = defineProps<{
  modelValue: FileWithPreview[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', files: FileWithPreview[]): void;
}>();

const files = ref<FileWithPreview[]>(props.modelValue);
const isDragging = ref(false);

watch(
  () => props.modelValue,
  (newFiles) => {
    files.value = newFiles;
  }
);

function handleDrop(e: DragEvent) {
  isDragging.value = false;
  const droppedFiles = Array.from(e.dataTransfer?.files || []);
  addFiles(droppedFiles);
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement;
  const selectedFiles = Array.from(target.files || []);
  addFiles(selectedFiles);
}

function addFiles(newFiles: File[]) {
  const validFiles = newFiles.filter((file) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert(`${file.name} is not an image file`);
      return false;
    }
    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert(`${file.name} is larger than 5MB`);
      return false;
    }
    return true;
  });

  // Add preview URLs
  const filesWithPreview: FileWithPreview[] = validFiles.map((file) => {
    const fileWithPreview = file as FileWithPreview;
    fileWithPreview.preview = URL.createObjectURL(file);
    return fileWithPreview;
  });

  const totalFiles = [...files.value, ...filesWithPreview].slice(0, 5);
  files.value = totalFiles;
  emit('update:modelValue', totalFiles);
}

function removeFile(index: number) {
  const file = files.value[index];
  if (file.preview) {
    URL.revokeObjectURL(file.preview);
  }
  files.value.splice(index, 1);
  emit('update:modelValue', files.value);
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
</script>
```

---

### 2.6 Wizard Container Component

**File:** `src/plugins/wizard/components/WizardContainer.vue`

```vue
<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <!-- Progress Bar -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700"
          >Step {{ store.currentStep }} of {{ store.totalSteps }}</span
        >
        <span class="text-sm text-gray-500">{{ Math.round(store.progress) }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-primary-600 h-2 rounded-full transition-all duration-300"
          :style="{ width: store.progress + '%' }"
        />
      </div>
    </div>

    <!-- Step Content -->
    <div class="bg-white rounded-lg shadow-md p-8">
      <slot :name="`step-${store.currentStep}`" />

      <!-- Navigation Buttons -->
      <div class="flex justify-between mt-8">
        <button
          v-if="store.canGoBack"
          type="button"
          class="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          @click="goBack"
        >
          Back
        </button>
        <div v-else />

        <button
          type="button"
          class="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!store.canGoNext || store.isValidating"
          @click="goNext"
        >
          {{ store.currentStep === store.totalSteps ? 'Submit' : 'Next' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useWizard } from '../composables/useWizard';

const { store, goNext, goBack } = useWizard();
</script>
```

---

### 2.7 E2E Test (Playwright)

**File:** `tests/e2e/flows/wizard.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Wizard Flow', () => {
  test('user can complete file upload wizard', async ({ page }) => {
    // Go to wizard
    await page.goto('/wizard');

    // Step 1: Upload files
    await expect(page.locator('h1')).toContainText('Upload Images');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([
      'tests/fixtures/sample-image-1.jpg',
      'tests/fixtures/sample-image-2.jpg',
    ]);

    // Verify files are displayed
    await expect(page.locator('text=sample-image-1.jpg')).toBeVisible();
    await expect(page.locator('text=sample-image-2.jpg')).toBeVisible();

    // Click Next
    await page.click('button:has-text("Next")');

    // Step 2: Email & GDPR
    await expect(page.locator('h1')).toContainText('Your Information');

    await page.fill('input[type="email"]', 'test@example.com');
    await page.check('input[type="checkbox"]'); // GDPR consent

    // Verify Next button is enabled
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled();

    // Click Next
    await nextButton.click();

    // Should see confirmation or next step
    await expect(page).toHaveURL(/\/wizard\/step-3/);
  });

  test('validates file upload', async ({ page }) => {
    await page.goto('/wizard');

    // Try to proceed without files
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeDisabled();
  });

  test('validates GDPR consent', async ({ page }) => {
    await page.goto('/wizard');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(['tests/fixtures/sample-image-1.jpg']);

    // Go to step 2
    await page.click('button:has-text("Next")');

    // Fill email but not GDPR
    await page.fill('input[type="email"]', 'test@example.com');

    // Next should be disabled
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeDisabled();
  });

  test('can navigate back and forth', async ({ page }) => {
    await page.goto('/wizard');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(['tests/fixtures/sample-image-1.jpg']);

    // Go forward
    await page.click('button:has-text("Next")');

    // Go back
    await page.click('button:has-text("Back")');

    // Should be on step 1
    await expect(page.locator('text=Upload Images')).toBeVisible();

    // File should still be there
    await expect(page.locator('text=sample-image-1.jpg')).toBeVisible();
  });
});
```

---

### 2.8 Plugin Registration

**File:** `src/plugins/wizard/index.ts`

```typescript
import { App } from 'vue';
import { IPlugin, PluginRoute } from '@core/plugin/IPlugin';
import { PlatformSDK } from '@core/sdk/PlatformSDK';
import { useWizardStore } from './store/wizardStore';

export class WizardPlugin implements IPlugin {
  readonly name = 'wizard';
  readonly version = '1.0.0';

  async install(app: App, sdk: PlatformSDK): Promise<void> {
    // Register routes
    const routes = this.registerRoutes();
    routes.forEach((route) => {
      sdk.router.addRoute(route);
    });

    // Register store
    app.use(useWizardStore);
  }

  registerRoutes(): PluginRoute[] {
    return [
      {
        path: '/wizard',
        name: 'wizard',
        component: () => import('./components/WizardContainer.vue'),
        meta: {
          title: 'Upload Wizard',
        },
      },
    ];
  }
}
```

---

## Testing Checklist

- [ ] Unit tests for wizardStore (90%+ coverage)
- [ ] File upload validates size and type
- [ ] Drag & drop works correctly
- [ ] Email validation works
- [ ] GDPR checkbox is required
- [ ] Navigation between steps works
- [ ] State persists when going back
- [ ] E2E test covers full wizard flow
- [ ] Responsive design on mobile

---

## Definition of Done

- [ ] Wizard plugin implements IPlugin interface
- [ ] Step 1 (file upload) fully functional
- [ ] Step 2 (GDPR) fully functional
- [ ] Zod validation for all fields
- [ ] Store manages wizard state
- [ ] E2E test with Playwright passes
- [ ] Responsive design
- [ ] All tests pass (unit + E2E)
- [ ] Documentation updated

---

## Next Sprint

**Sprint 3:** Tariff Plans & Checkout Flow
