# Sprint 0: Foundation

**Goal:** Establish TypeScript + Vue.js 3 project structure, plugin system core, and testing infrastructure.

---

## Objectives

- [ ] Project setup with Vite + TypeScript
- [ ] Plugin system core (IPlugin, PluginRegistry, PluginLoader)
- [ ] DI container setup with provide/inject
- [ ] Base interfaces (ISP compliance)
- [ ] Testing infrastructure (Vitest + Playwright)
- [ ] Tailwind CSS configuration
- [ ] ESLint + Prettier setup
- [ ] CI pipeline configuration

---

## Tasks

### 0.1 Project Initialization

**Commands:**

```bash
# Create Vue.js + TypeScript project
npm create vite@latest frontend/user/vue -- --template vue-ts

cd frontend/user/vue

# Install dependencies
npm install vue-router@4 pinia@2 axios zod

# Install dev dependencies
npm install -D \
  @playwright/test \
  vitest \
  @vitest/ui \
  @vue/test-utils \
  happy-dom \
  tailwindcss \
  postcss \
  autoprefixer \
  eslint \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin \
  prettier \
  eslint-config-prettier \
  eslint-plugin-vue

# Initialize Tailwind
npx tailwindcss init -p
```

**File:** `package.json` (additional scripts)

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "test": "npm run test:unit && npm run test:e2e",
    "test:unit": "vitest",
    "test:unit:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "format": "prettier --write src/"
  }
}
```

---

### 0.2 TypeScript Configuration

**File:** `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,

    /* Paths */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@core/*": ["./src/core/*"],
      "@plugins/*": ["./src/plugins/*"],
      "@shared/*": ["./src/shared/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**File:** `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@core': fileURLToPath(new URL('./src/core', import.meta.url)),
      '@plugins': fileURLToPath(new URL('./src/plugins', import.meta.url)),
      '@shared': fileURLToPath(new URL('./src/shared', import.meta.url)),
    },
  },
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
});
```

---

### 0.3 Plugin System Core

#### Test First (TDD)

**File:** `src/core/plugin/__tests__/PluginRegistry.spec.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { PluginRegistry } from '../PluginRegistry';
import { IPlugin } from '../IPlugin';
import { createApp } from 'vue';

describe('PluginRegistry', () => {
  let registry: PluginRegistry;

  beforeEach(() => {
    registry = new PluginRegistry();
  });

  it('should register a plugin', () => {
    const mockPlugin: IPlugin = {
      name: 'test-plugin',
      version: '1.0.0',
      install: async () => {},
    };

    registry.register(mockPlugin);

    expect(registry.getPlugin('test-plugin')).toBe(mockPlugin);
  });

  it('should throw error on duplicate plugin registration', () => {
    const mockPlugin: IPlugin = {
      name: 'test-plugin',
      version: '1.0.0',
      install: async () => {},
    };

    registry.register(mockPlugin);

    expect(() => registry.register(mockPlugin)).toThrow(
      'Plugin test-plugin is already registered'
    );
  });

  it('should validate plugin dependencies', () => {
    const pluginA: IPlugin = {
      name: 'plugin-a',
      version: '1.0.0',
      install: async () => {},
    };

    const pluginB: IPlugin = {
      name: 'plugin-b',
      version: '1.0.0',
      dependencies: ['plugin-a'],
      install: async () => {},
    };

    registry.register(pluginA);
    registry.register(pluginB);

    expect(registry.getPlugin('plugin-b')).toBe(pluginB);
  });

  it('should throw error on missing dependencies', () => {
    const plugin: IPlugin = {
      name: 'plugin-b',
      version: '1.0.0',
      dependencies: ['missing-plugin'],
      install: async () => {},
    };

    expect(() => registry.register(plugin)).toThrow(
      'Plugin plugin-b requires missing-plugin'
    );
  });
});
```

#### Implementation

**File:** `src/core/plugin/IPlugin.ts`

```typescript
import { App, Component } from 'vue';
import { RouteRecordRaw } from 'vue-router';
import { StoreDefinition } from 'pinia';
import { PlatformSDK } from '../sdk/PlatformSDK';

export interface IPlugin {
  // Metadata
  readonly name: string;
  readonly version: string;
  readonly dependencies?: string[];

  // Lifecycle hooks
  install(app: App, sdk: PlatformSDK): Promise<void>;
  activate?(): Promise<void>;
  deactivate?(): Promise<void>;

  // Optional capabilities
  registerRoutes?(): PluginRoute[];
  registerComponents?(): PluginComponent[];
  registerStores?(): PluginStore[];
}

export interface PluginRoute {
  path: string;
  name?: string;
  component: Component;
  meta?: {
    requiresAuth?: boolean;
    requiredPlan?: string[];
    permissions?: string[];
    title?: string;
  };
  children?: PluginRoute[];
}

export interface PluginComponent {
  name: string;
  component: Component;
  slot?: string; // Extension point name
}

export interface PluginStore {
  id: string;
  store: StoreDefinition;
}
```

**File:** `src/core/plugin/PluginRegistry.ts`

```typescript
import { App } from 'vue';
import { IPlugin } from './IPlugin';
import { PlatformSDK } from '../sdk/PlatformSDK';

export class PluginRegistry {
  private plugins: Map<string, IPlugin> = new Map();
  private loadedPlugins: Set<string> = new Set();

  register(plugin: IPlugin): void {
    // Check if already registered
    if (this.plugins.has(plugin.name)) {
      throw new Error(`Plugin ${plugin.name} is already registered`);
    }

    // Validate dependencies
    if (plugin.dependencies) {
      for (const dep of plugin.dependencies) {
        if (!this.plugins.has(dep)) {
          throw new Error(`Plugin ${plugin.name} requires ${dep}`);
        }
      }
    }

    this.plugins.set(plugin.name, plugin);
  }

  async loadPlugin(name: string, app: App, sdk: PlatformSDK): Promise<void> {
    const plugin = this.plugins.get(name);

    if (!plugin) {
      throw new Error(`Plugin ${name} is not registered`);
    }

    if (this.loadedPlugins.has(name)) {
      console.warn(`Plugin ${name} is already loaded`);
      return;
    }

    // Load dependencies first
    if (plugin.dependencies) {
      for (const dep of plugin.dependencies) {
        await this.loadPlugin(dep, app, sdk);
      }
    }

    // Install plugin
    await plugin.install(app, sdk);

    // Activate if method exists
    if (plugin.activate) {
      await plugin.activate();
    }

    this.loadedPlugins.add(name);
  }

  async loadAll(app: App, sdk: PlatformSDK): Promise<void> {
    for (const [name] of this.plugins) {
      await this.loadPlugin(name, app, sdk);
    }
  }

  getPlugin(name: string): IPlugin | undefined {
    return this.plugins.get(name);
  }

  isLoaded(name: string): boolean {
    return this.loadedPlugins.has(name);
  }

  getLoadedPlugins(): string[] {
    return Array.from(this.loadedPlugins);
  }
}
```

---

### 0.4 Platform SDK Stub

**File:** `src/core/sdk/PlatformSDK.ts`

```typescript
import { Router } from 'vue-router';
import { Component, App } from 'vue';

export interface PlatformSDK {
  // Core services (will be implemented in Sprint 1)
  apiClient: any; // TODO: Replace with IApiClient
  authService: any; // TODO: Replace with IAuthService
  validationService: any; // TODO: Replace with IValidationService
  eventBus: any; // TODO: Replace with IEventBus

  // Router access
  router: Router;

  // Component registration
  registerGlobalComponent(name: string, component: Component): void;

  // Get Vue app instance
  app: App;
}

export function createPlatformSDK(app: App, router: Router): PlatformSDK {
  return {
    apiClient: null,
    authService: null,
    validationService: null,
    eventBus: null,
    router,
    app,
    registerGlobalComponent(name: string, component: Component) {
      app.component(name, component);
    },
  };
}
```

---

### 0.5 Tailwind CSS Setup

**File:** `tailwind.config.ts`

```typescript
import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
```

**File:** `src/style.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply text-gray-900 bg-white;
  }
}
```

---

### 0.6 Vitest Configuration

**File:** `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/**/*.spec.ts',
        'src/**/*.test.ts',
        '**/*.config.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@core': fileURLToPath(new URL('./src/core', import.meta.url)),
      '@plugins': fileURLToPath(new URL('./src/plugins', import.meta.url)),
      '@shared': fileURLToPath(new URL('./src/shared', import.meta.url)),
    },
  },
});
```

---

### 0.7 Playwright Configuration

**File:** `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:8080',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

### 0.8 Application Entry Point

**File:** `src/main.ts`

```typescript
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';
import { PluginRegistry } from '@core/plugin/PluginRegistry';
import { createPlatformSDK } from '@core/sdk/PlatformSDK';

import './style.css';

async function bootstrap() {
  const app = createApp(App);

  // Setup Pinia
  const pinia = createPinia();
  app.use(pinia);

  // Setup Router (empty for now, plugins will add routes)
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/',
        name: 'home',
        component: () => import('./views/Home.vue'),
      },
    ],
  });

  app.use(router);

  // Create Platform SDK
  const sdk = createPlatformSDK(app, router);

  // Setup Plugin Registry
  const pluginRegistry = new PluginRegistry();

  // Register plugins here (will be added in later sprints)
  // pluginRegistry.register(new WizardPlugin());
  // pluginRegistry.register(new UserCabinetPlugin());

  // Load all plugins
  await pluginRegistry.loadAll(app, sdk);

  // Mount app
  app.mount('#app');
}

bootstrap();
```

---

### 0.9 ESLint + Prettier Configuration

**File:** `.eslintrc.cjs`

```javascript
module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier',
  ],
  parser: 'vue-eslint-parser',
  parserOptions: {
    ecmaVersion: 'latest',
    parser: '@typescript-eslint/parser',
    sourceType: 'module',
  },
  plugins: ['vue', '@typescript-eslint'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': 'error',
    'vue/multi-word-component-names': 'off',
  },
};
```

**File:** `.prettierrc.json`

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "arrowParens": "always"
}
```

---

## Testing Checklist

- [ ] Run `npm install` successfully
- [ ] Run `npm run dev` and see app at http://localhost:8080
- [ ] Run `npm run test:unit` and all tests pass
- [ ] Run `npm run lint` with no errors
- [ ] Verify TypeScript strict mode with `npm run build`
- [ ] PluginRegistry can register and load plugins
- [ ] PlatformSDK is available in plugins

---

## Definition of Done

- [x] Project structure created with Vite + TypeScript
- [x] Plugin system core interfaces defined (IPlugin)
- [x] PluginRegistry implemented with tests
- [x] PlatformSDK stub created
- [x] Tailwind CSS configured
- [x] Vitest + Playwright configured
- [x] ESLint + Prettier configured
- [x] All tests pass
- [x] Application runs without errors
- [x] Documentation updated

---

## Next Sprint

**Sprint 1:** API Client SDK & Authentication Service
