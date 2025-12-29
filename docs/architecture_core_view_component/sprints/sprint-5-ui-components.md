# Sprint 5: Shared UI Components

**Duration:** 2 weeks
**Goal:** Build reusable UI component library
**Dependencies:** Sprint 1

---

## Objectives

- [ ] Build form components (Button, Input, Checkbox, Select)
- [ ] Build Modal and Dialog components
- [ ] Build Table component with sorting and pagination
- [ ] Build Toast notification system
- [ ] Build Loading states
- [ ] Style with Tailwind CSS
- [ ] Ensure WCAG 2.1 AA accessibility
- [ ] Write component tests (90%+ coverage)

---

## Components to Build

### 1. Button Component
- Variants: primary, secondary, danger, ghost
- Sizes: sm, md, lg
- States: default, hover, active, disabled, loading
- Icons support

### 2. Input Component
- Types: text, email, password, number, tel
- States: default, error, disabled
- Label and error message support
- Prefix/suffix icons

### 3. Select Component
- Single and multi-select
- Search functionality
- Custom options rendering
- Keyboard navigation

### 4. Checkbox & Radio
- Styled with Tailwind
- Accessible labels
- Indeterminate state (checkbox)

### 5. Modal Component
- Backdrop with blur
- Close on ESC or backdrop click
- Focus trap
- Animations

### 6. Table Component
- Sortable columns
- Pagination
- Row selection
- Loading state
- Empty state

### 7. Toast Notifications
- Types: success, error, warning, info
- Auto-dismiss with timer
- Queue management
- Position: top-right, top-left, bottom-right, bottom-left

### 8. Loading Components
- Spinner
- Skeleton loaders
- Progress bar

---

## File Structure

```
src/components/
├── button/
│   ├── Button.vue
│   ├── Button.test.ts
│   └── index.ts
├── input/
│   ├── Input.vue
│   ├── Input.test.ts
│   └── index.ts
├── select/
│   ├── Select.vue
│   ├── Select.test.ts
│   └── index.ts
├── checkbox/
│   ├── Checkbox.vue
│   └── index.ts
├── modal/
│   ├── Modal.vue
│   ├── useModal.ts
│   └── index.ts
├── table/
│   ├── Table.vue
│   ├── TableColumn.vue
│   ├── useTable.ts
│   └── index.ts
├── toast/
│   ├── Toast.vue
│   ├── ToastContainer.vue
│   ├── useToast.ts
│   └── index.ts
├── loading/
│   ├── Spinner.vue
│   ├── Skeleton.vue
│   ├── ProgressBar.vue
│   └── index.ts
└── index.ts
```

---

## Example: Button Component

**File:** `frontend/core/src/components/button/Button.vue`

```vue
<template>
  <button
    :type="type"
    :class="buttonClasses"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="button-spinner">
      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </span>
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
});

const emit = defineEmits<{
  click: [event: MouseEvent];
}>();

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';

  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const disabled = props.disabled || props.loading ? 'opacity-50 cursor-not-allowed' : '';

  return `${base} ${variants[props.variant]} ${sizes[props.size]} ${disabled}`;
});

function handleClick(event: MouseEvent): void {
  if (!props.disabled && !props.loading) {
    emit('click', event);
  }
}
</script>
```

---

## Accessibility Requirements

- All form inputs must have associated labels
- Keyboard navigation support (Tab, Enter, ESC)
- ARIA attributes for screen readers
- Focus management in modals and dialogs
- Color contrast ratio 4.5:1 minimum
- Focus indicators visible and clear

---

## Definition of Done

- [x] All 8 component categories implemented
- [x] Tailwind CSS styling
- [x] WCAG 2.1 AA compliant
- [x] Component tests (90%+ coverage)
- [x] Storybook documentation (optional)
- [x] TypeScript strict mode passing
- [x] ESLint passing

---

## Next Sprint

[Sprint 6: Composables & Utilities](./sprint-6-composables-utils.md)
