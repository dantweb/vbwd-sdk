# Sprint 5: UI Components & Plugins

**Priority:** MEDIUM
**Duration:** 2 days
**Focus:** Create shared UI component library and integrate plugins

> **Core Requirements:** See [sprint-plan.md](./sprint-plan.md) for mandatory TDD-first, SOLID, DI, Clean Code, and No Over-Engineering requirements.

---

## 5.1 Shared Component Library

### Problem
User and Admin apps have duplicate UI components.

### Requirements
- Common button, input, modal components
- Consistent styling via CSS variables
- TypeScript support
- Storybook documentation (optional)

### Implementation

**File Structure:**
```
vbwd-frontend/core/src/components/
  ui/
    Button.vue
    Input.vue
    Modal.vue
    Card.vue
    Badge.vue
    Alert.vue
    Spinner.vue
    Table.vue
    Pagination.vue
    Dropdown.vue
  forms/
    FormField.vue
    FormGroup.vue
    FormError.vue
  layout/
    Container.vue
    Row.vue
    Col.vue
  index.ts
```

**File:** `vbwd-frontend/core/src/components/ui/Button.vue`
```vue
<template>
  <button
    :type="type"
    :class="buttonClasses"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <Spinner v-if="loading" class="btn-spinner" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import Spinner from './Spinner.vue';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'link';
type ButtonSize = 'sm' | 'md' | 'lg';

const props = withDefaults(defineProps<{
  type?: 'button' | 'submit' | 'reset';
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  block?: boolean;
}>(), {
  type: 'button',
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  block: false,
});

defineEmits<{
  click: [event: MouseEvent];
}>();

const buttonClasses = computed(() => [
  'btn',
  `btn-${props.variant}`,
  `btn-${props.size}`,
  {
    'btn-block': props.block,
    'btn-loading': props.loading,
  }
]);
</script>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: var(--btn-padding-y, 0.5rem) var(--btn-padding-x, 1rem);
  font-size: var(--btn-font-size, 1rem);
  font-weight: 500;
  border-radius: var(--btn-border-radius, 0.375rem);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: var(--color-text);
}

.btn-danger {
  background-color: var(--color-danger);
  color: white;
}

.btn-ghost {
  background-color: transparent;
  border-color: var(--color-border);
}

.btn-link {
  background-color: transparent;
  color: var(--color-primary);
  text-decoration: underline;
}

.btn-sm { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
.btn-lg { padding: 0.75rem 1.5rem; font-size: 1.125rem; }

.btn-block { width: 100%; }

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner {
  width: 1em;
  height: 1em;
}
</style>
```

**File:** `vbwd-frontend/core/src/components/ui/Input.vue`
```vue
<template>
  <div :class="['input-wrapper', { 'has-error': error }]">
    <label v-if="label" :for="inputId" class="input-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    <div class="input-container">
      <span v-if="$slots.prefix" class="input-prefix">
        <slot name="prefix" />
      </span>
      <input
        :id="inputId"
        v-model="modelValue"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :class="inputClasses"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @blur="$emit('blur', $event)"
        @focus="$emit('focus', $event)"
      />
      <span v-if="$slots.suffix" class="input-suffix">
        <slot name="suffix" />
      </span>
    </div>
    <p v-if="error" class="input-error">{{ error }}</p>
    <p v-else-if="hint" class="input-hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue';

type InputSize = 'sm' | 'md' | 'lg';

const props = withDefaults(defineProps<{
  modelValue?: string;
  type?: string;
  label?: string;
  placeholder?: string;
  hint?: string;
  error?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  size?: InputSize;
}>(), {
  modelValue: '',
  type: 'text',
  size: 'md',
  disabled: false,
  readonly: false,
  required: false,
});

defineEmits<{
  'update:modelValue': [value: string];
  blur: [event: FocusEvent];
  focus: [event: FocusEvent];
}>();

const inputId = useId();

const inputClasses = computed(() => [
  'input',
  `input-${props.size}`,
  {
    'input-error': props.error,
    'input-disabled': props.disabled,
  }
]);
</script>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.input-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.required {
  color: var(--color-danger);
}

.input-container {
  display: flex;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--input-border-radius, 0.375rem);
  overflow: hidden;
}

.input {
  flex: 1;
  padding: var(--input-padding-y, 0.5rem) var(--input-padding-x, 0.75rem);
  border: none;
  outline: none;
  font-size: 1rem;
  background: transparent;
}

.input:focus {
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.input-sm { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
.input-lg { padding: 0.75rem 1rem; font-size: 1.125rem; }

.has-error .input-container {
  border-color: var(--color-danger);
}

.input-error {
  color: var(--color-danger);
  font-size: 0.75rem;
}

.input-hint {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}
</style>
```

**File:** `vbwd-frontend/core/src/components/ui/Modal.vue`
```vue
<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="closeOnOverlay && close()">
        <div :class="['modal', `modal-${size}`]" role="dialog" aria-modal="true">
          <header v-if="title || $slots.header" class="modal-header">
            <slot name="header">
              <h3 class="modal-title">{{ title }}</h3>
            </slot>
            <button v-if="closable" class="modal-close" @click="close" aria-label="Close">
              &times;
            </button>
          </header>

          <div class="modal-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { watch } from 'vue';

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

const props = withDefaults(defineProps<{
  modelValue: boolean;
  title?: string;
  size?: ModalSize;
  closable?: boolean;
  closeOnOverlay?: boolean;
  closeOnEsc?: boolean;
}>(), {
  size: 'md',
  closable: true,
  closeOnOverlay: true,
  closeOnEsc: true,
});

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  close: [];
}>();

const close = () => {
  emit('update:modelValue', false);
  emit('close');
};

// Handle ESC key
watch(() => props.modelValue, (isOpen) => {
  if (isOpen && props.closeOnEsc) {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: var(--modal-border-radius, 0.5rem);
  box-shadow: var(--shadow-lg);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-sm { width: 300px; }
.modal-md { width: 500px; }
.modal-lg { width: 800px; }
.modal-xl { width: 1140px; }
.modal-full { width: 95vw; height: 95vh; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  opacity: 0.5;
}

.modal-close:hover {
  opacity: 1;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.95);
}
</style>
```

**File:** `vbwd-frontend/core/src/components/index.ts`
```typescript
// UI Components
export { default as Button } from './ui/Button.vue';
export { default as Input } from './ui/Input.vue';
export { default as Modal } from './ui/Modal.vue';
export { default as Card } from './ui/Card.vue';
export { default as Badge } from './ui/Badge.vue';
export { default as Alert } from './ui/Alert.vue';
export { default as Spinner } from './ui/Spinner.vue';
export { default as Table } from './ui/Table.vue';
export { default as Pagination } from './ui/Pagination.vue';
export { default as Dropdown } from './ui/Dropdown.vue';

// Form Components
export { default as FormField } from './forms/FormField.vue';
export { default as FormGroup } from './forms/FormGroup.vue';
export { default as FormError } from './forms/FormError.vue';

// Layout Components
export { default as Container } from './layout/Container.vue';
export { default as Row } from './layout/Row.vue';
export { default as Col } from './layout/Col.vue';

// Feature Components
export { default as FeatureGate } from './FeatureGate.vue';
```

---

## 5.2 Plugin Integration in User App

### Problem
User app is monolithic without plugin architecture.

### Requirements
- Plugin registration system
- Dynamic component loading
- Plugin configuration
- Event hooks for plugins

### Implementation

**File:** `vbwd-frontend/user/vue/src/plugins/index.ts`
```typescript
import type { App } from 'vue';
import { eventBus } from '@vbwd/core-sdk';

interface PluginDefinition {
  name: string;
  version: string;
  install: (app: App, options?: Record<string, any>) => void;
  routes?: any[];
  components?: Record<string, any>;
}

const registeredPlugins: Map<string, PluginDefinition> = new Map();

export function registerPlugin(plugin: PluginDefinition): void {
  if (registeredPlugins.has(plugin.name)) {
    console.warn(`Plugin ${plugin.name} already registered`);
    return;
  }

  registeredPlugins.set(plugin.name, plugin);
  eventBus.emit('plugin:registered', { name: plugin.name, version: plugin.version });
}

export function installPlugins(app: App, options: Record<string, any> = {}): void {
  for (const [name, plugin] of registeredPlugins) {
    try {
      plugin.install(app, options[name]);
      eventBus.emit('plugin:installed', { name });
    } catch (error) {
      console.error(`Failed to install plugin ${name}:`, error);
      eventBus.emit('plugin:error', { name, error });
    }
  }
}

export function getPluginRoutes(): any[] {
  const routes: any[] = [];
  for (const plugin of registeredPlugins.values()) {
    if (plugin.routes) {
      routes.push(...plugin.routes);
    }
  }
  return routes;
}

export { registeredPlugins };
```

**File:** `vbwd-frontend/user/vue/src/main.ts`
```typescript
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { installPlugins } from './plugins';

// Import Core SDK components
import { Button, Input, Modal } from '@vbwd/core-sdk';

const app = createApp(App);

// Register global components from Core SDK
app.component('VButton', Button);
app.component('VInput', Input);
app.component('VModal', Modal);

// Install plugins
installPlugins(app);

app.use(createPinia());
app.use(router);
app.mount('#app');
```

---

## 5.3 Plugin Integration in Admin App

### Problem
Admin app has same monolithic issue.

### Implementation

Similar to User App with admin-specific plugins:
- User management plugin
- Subscription management plugin
- Analytics plugin

**File:** `vbwd-frontend/admin/vue/src/plugins/userManagement.ts`
```typescript
import type { App } from 'vue';
import type { PluginDefinition } from './index';

export const userManagementPlugin: PluginDefinition = {
  name: 'user-management',
  version: '1.0.0',

  routes: [
    {
      path: '/users',
      name: 'users',
      component: () => import('../views/users/UserList.vue'),
      meta: { roles: ['admin'] }
    },
    {
      path: '/users/:id',
      name: 'user-detail',
      component: () => import('../views/users/UserDetail.vue'),
      meta: { roles: ['admin'] }
    }
  ],

  install(app: App) {
    // Register plugin-specific components
    app.component('UserCard', () => import('../components/users/UserCard.vue'));
    app.component('UserForm', () => import('../components/users/UserForm.vue'));
  }
};
```

---

## 5.4 Component Documentation

### Requirements
- Component API documentation
- Usage examples
- Props/events reference

### Implementation (Optional - Storybook)

**Install Storybook:**
```bash
cd vbwd-frontend/core
npx storybook@latest init --type vue3
```

**File:** `vbwd-frontend/core/src/components/ui/Button.stories.ts`
```typescript
import type { Meta, StoryObj } from '@storybook/vue3';
import Button from './Button.vue';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger', 'ghost', 'link'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    default: 'Click me',
  },
};

export const Loading: Story = {
  args: {
    variant: 'primary',
    loading: true,
    default: 'Loading...',
  },
};

export const AllVariants: Story = {
  render: () => ({
    components: { Button },
    template: `
      <div style="display: flex; gap: 1rem;">
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="danger">Danger</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="link">Link</Button>
      </div>
    `,
  }),
};
```

---

## Checklist

### 5.1 Shared Component Library
- [ ] Button component
- [ ] Input component
- [ ] Modal component
- [ ] Card component
- [ ] Badge component
- [ ] Alert component
- [ ] Spinner component
- [ ] Table component
- [ ] Pagination component
- [ ] Dropdown component
- [ ] Form components
- [ ] Layout components
- [ ] All exported from index.ts
- [ ] TypeScript types

### 5.2 User App Plugins
- [ ] Plugin registration system
- [ ] Plugin installation
- [ ] Route registration
- [ ] Core SDK components imported
- [ ] Event hooks working

### 5.3 Admin App Plugins
- [ ] Plugin registration system
- [ ] User management plugin
- [ ] Subscription management plugin
- [ ] Analytics plugin
- [ ] Core SDK components imported

### 5.4 Documentation
- [ ] Storybook setup (optional)
- [ ] Component stories
- [ ] Props documentation
- [ ] Usage examples

---

## Verification Commands

```bash
# Build Core SDK
cd vbwd-frontend/core
npm run build

# Test component exports
node -e "const c = require('./dist'); console.log(Object.keys(c))"

# Run Storybook (if installed)
npm run storybook

# Test User App with components
cd ../user/vue
npm run dev
```
