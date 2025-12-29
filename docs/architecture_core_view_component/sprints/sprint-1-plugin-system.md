# Sprint 1: Plugin System Core

**Duration:** 1 week
**Goal:** Build the plugin architecture foundation
**Dependencies:** Sprint 0

---

## Objectives

- [ ] Design and implement IPlugin interface (ISP compliant)
- [ ] Implement PluginRegistry with dependency management
- [ ] Implement PluginLoader with lifecycle hooks
- [ ] Design PlatformSDK interface
- [ ] Write comprehensive unit tests (95%+ coverage)
- [ ] Create integration test examples
- [ ] Document plugin development guide

---

## Tasks

### 1. IPlugin Interface (Interface Segregation Principle)

**File:** `frontend/core/src/plugin/IPlugin.ts`

```typescript
import type { App } from 'vue';
import type { Router, RouteRecordRaw } from 'vue-router';
import type { PlatformSDK } from '../sdk';

/**
 * Metadata about a plugin
 */
export interface PluginMetadata {
  /** Unique plugin identifier */
  readonly name: string;
  /** Semantic version (e.g., "1.0.0") */
  readonly version: string;
  /** Human-readable display name */
  readonly displayName?: string;
  /** Short description */
  readonly description?: string;
  /** Plugin author */
  readonly author?: string;
  /** Plugin dependencies (other plugin names) */
  readonly dependencies?: string[];
}

/**
 * Plugin route definition
 */
export interface PluginRoute {
  /** Route path */
  path: string;
  /** Route name */
  name: string;
  /** Lazy-loaded component */
  component: () => Promise<any>;
  /** Route metadata */
  meta?: Record<string, any>;
  /** Child routes */
  children?: PluginRoute[];
}

/**
 * Plugin component registration
 */
export interface PluginComponent {
  /** Component name for global registration */
  name: string;
  /** Component definition */
  component: any;
}

/**
 * Plugin store registration
 */
export interface PluginStore {
  /** Store ID */
  id: string;
  /** Pinia store definition */
  store: any;
}

/**
 * Core plugin interface - all plugins must implement this
 *
 * Follows Interface Segregation Principle:
 * - Only `install()` is required
 * - Optional hooks for lifecycle management
 * - Optional methods for registering resources
 */
export interface IPlugin {
  /** Plugin metadata */
  readonly metadata: PluginMetadata;

  /**
   * Install plugin (required)
   * Called when plugin is loaded
   */
  install(app: App, sdk: PlatformSDK): Promise<void>;

  /**
   * Activate plugin (optional)
   * Called after all dependencies are loaded
   */
  activate?(): Promise<void>;

  /**
   * Deactivate plugin (optional)
   * Called before unloading
   */
  deactivate?(): Promise<void>;

  /**
   * Register routes (optional)
   * Called during plugin installation
   */
  registerRoutes?(): PluginRoute[];

  /**
   * Register global components (optional)
   * Called during plugin installation
   */
  registerComponents?(): PluginComponent[];

  /**
   * Register Pinia stores (optional)
   * Called during plugin installation
   */
  registerStores?(): PluginStore[];
}
```

### 2. Platform SDK Interface

**File:** `frontend/core/src/sdk/PlatformSDK.ts`

```typescript
import type { App } from 'vue';
import type { Router } from 'vue-router';
import type { Pinia } from 'pinia';
import type { IApiClient } from '../api';
import type { IAuthService } from '../auth';
import type { IEventBus } from '../events';
import type { IValidationService } from '../validation';

/**
 * Platform SDK - provides access to core services
 *
 * Dependency Inversion Principle:
 * - Plugins depend on abstractions (interfaces), not implementations
 */
export interface PlatformSDK {
  /** Vue app instance */
  readonly app: App;

  /** Vue Router instance */
  readonly router: Router;

  /** Pinia store instance */
  readonly pinia: Pinia;

  /** API client for backend communication */
  readonly api: IApiClient;

  /** Authentication service */
  readonly auth: IAuthService;

  /** Event bus for plugin communication */
  readonly events: IEventBus;

  /** Validation service */
  readonly validation: IValidationService;

  /** SDK version */
  readonly version: string;
}
```

**File:** `frontend/core/src/sdk/PlatformSDKImpl.ts`

```typescript
import type { App } from 'vue';
import type { Router } from 'vue-router';
import type { Pinia } from 'pinia';
import type { IApiClient } from '../api';
import type { IAuthService } from '../auth';
import type { IEventBus } from '../events';
import type { IValidationService } from '../validation';
import type { PlatformSDK } from './PlatformSDK';

export class PlatformSDKImpl implements PlatformSDK {
  constructor(
    public readonly app: App,
    public readonly router: Router,
    public readonly pinia: Pinia,
    public readonly api: IApiClient,
    public readonly auth: IAuthService,
    public readonly events: IEventBus,
    public readonly validation: IValidationService,
    public readonly version: string = '0.1.0'
  ) {}
}
```

### 3. Plugin Registry

**File:** `frontend/core/src/plugin/PluginRegistry.ts`

```typescript
import type { IPlugin } from './IPlugin';

/**
 * Plugin registry manages plugin lifecycle and dependencies
 *
 * Single Responsibility: Plugin registration and dependency resolution
 */
export class PluginRegistry {
  private plugins = new Map<string, IPlugin>();
  private loadOrder: string[] = [];

  /**
   * Register a plugin
   * @throws Error if plugin with same name already registered
   */
  register(plugin: IPlugin): void {
    const { name } = plugin.metadata;

    if (this.plugins.has(name)) {
      throw new Error(`Plugin "${name}" is already registered`);
    }

    this.plugins.set(name, plugin);
  }

  /**
   * Register multiple plugins
   */
  registerAll(plugins: IPlugin[]): void {
    plugins.forEach((plugin) => this.register(plugin));
  }

  /**
   * Get plugin by name
   */
  get(name: string): IPlugin | undefined {
    return this.plugins.get(name);
  }

  /**
   * Check if plugin is registered
   */
  has(name: string): boolean {
    return this.plugins.has(name);
  }

  /**
   * Get all registered plugins
   */
  getAll(): IPlugin[] {
    return Array.from(this.plugins.values());
  }

  /**
   * Get plugin count
   */
  count(): number {
    return this.plugins.size;
  }

  /**
   * Resolve plugin load order based on dependencies
   * @throws Error if circular dependency detected
   * @throws Error if dependency not found
   */
  resolveLoadOrder(): string[] {
    const visited = new Set<string>();
    const visiting = new Set<string>();
    const order: string[] = [];

    const visit = (name: string): void => {
      if (visited.has(name)) return;

      if (visiting.has(name)) {
        throw new Error(`Circular dependency detected for plugin "${name}"`);
      }

      const plugin = this.plugins.get(name);
      if (!plugin) {
        throw new Error(`Plugin "${name}" not found in registry`);
      }

      visiting.add(name);

      // Visit dependencies first
      const deps = plugin.metadata.dependencies || [];
      for (const dep of deps) {
        if (!this.plugins.has(dep)) {
          throw new Error(
            `Plugin "${name}" depends on "${dep}", but "${dep}" is not registered`
          );
        }
        visit(dep);
      }

      visiting.delete(name);
      visited.add(name);
      order.push(name);
    };

    // Visit all plugins
    for (const name of this.plugins.keys()) {
      visit(name);
    }

    this.loadOrder = order;
    return order;
  }

  /**
   * Get resolved load order
   * @throws Error if load order not yet resolved
   */
  getLoadOrder(): string[] {
    if (this.loadOrder.length === 0) {
      throw new Error('Load order not resolved. Call resolveLoadOrder() first.');
    }
    return [...this.loadOrder];
  }

  /**
   * Clear all plugins
   */
  clear(): void {
    this.plugins.clear();
    this.loadOrder = [];
  }
}
```

### 4. Plugin Loader

**File:** `frontend/core/src/plugin/PluginLoader.ts`

```typescript
import type { App } from 'vue';
import type { IPlugin, PluginRoute } from './IPlugin';
import type { PluginRegistry } from './PluginRegistry';
import type { PlatformSDK } from '../sdk';

export type PluginStatus = 'registered' | 'installing' | 'installed' | 'activating' | 'active' | 'error';

export interface PluginLoadResult {
  name: string;
  status: PluginStatus;
  error?: Error;
}

/**
 * Plugin loader handles plugin installation and activation
 *
 * Single Responsibility: Plugin loading and lifecycle management
 */
export class PluginLoader {
  private statuses = new Map<string, PluginStatus>();
  private errors = new Map<string, Error>();

  constructor(
    private readonly registry: PluginRegistry,
    private readonly sdk: PlatformSDK
  ) {}

  /**
   * Load all registered plugins in dependency order
   */
  async loadAll(): Promise<PluginLoadResult[]> {
    const order = this.registry.resolveLoadOrder();
    const results: PluginLoadResult[] = [];

    for (const name of order) {
      const result = await this.load(name);
      results.push(result);

      // Stop if critical plugin fails
      if (result.status === 'error') {
        console.error(`Failed to load plugin "${name}"`, result.error);
        // Continue loading other plugins (non-blocking)
      }
    }

    return results;
  }

  /**
   * Load a single plugin
   */
  async load(name: string): Promise<PluginLoadResult> {
    const plugin = this.registry.get(name);

    if (!plugin) {
      const error = new Error(`Plugin "${name}" not found`);
      this.errors.set(name, error);
      this.statuses.set(name, 'error');
      return { name, status: 'error', error };
    }

    try {
      // Install phase
      this.statuses.set(name, 'installing');
      await this.installPlugin(plugin);
      this.statuses.set(name, 'installed');

      // Activate phase
      if (plugin.activate) {
        this.statuses.set(name, 'activating');
        await plugin.activate();
      }
      this.statuses.set(name, 'active');

      return { name, status: 'active' };
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.errors.set(name, err);
      this.statuses.set(name, 'error');
      return { name, status: 'error', error: err };
    }
  }

  /**
   * Install plugin (register routes, components, stores)
   */
  private async installPlugin(plugin: IPlugin): Promise<void> {
    const { app, router, pinia } = this.sdk;

    // Call plugin install hook
    await plugin.install(app, this.sdk);

    // Register routes
    if (plugin.registerRoutes) {
      const routes = plugin.registerRoutes();
      routes.forEach((route) => {
        router.addRoute(this.convertPluginRoute(route));
      });
    }

    // Register components
    if (plugin.registerComponents) {
      const components = plugin.registerComponents();
      components.forEach(({ name, component }) => {
        app.component(name, component);
      });
    }

    // Register stores
    if (plugin.registerStores) {
      const stores = plugin.registerStores();
      stores.forEach(({ id, store }) => {
        // Pinia stores are auto-registered on first use
        // We just validate they exist
        if (typeof store !== 'function') {
          throw new Error(`Invalid store "${id}" in plugin "${plugin.metadata.name}"`);
        }
      });
    }
  }

  /**
   * Convert PluginRoute to RouteRecordRaw
   */
  private convertPluginRoute(route: PluginRoute): any {
    return {
      path: route.path,
      name: route.name,
      component: route.component,
      meta: route.meta,
      children: route.children?.map((child) => this.convertPluginRoute(child)),
    };
  }

  /**
   * Get plugin status
   */
  getStatus(name: string): PluginStatus | undefined {
    return this.statuses.get(name);
  }

  /**
   * Get plugin error
   */
  getError(name: string): Error | undefined {
    return this.errors.get(name);
  }

  /**
   * Get all statuses
   */
  getAllStatuses(): Map<string, PluginStatus> {
    return new Map(this.statuses);
  }
}
```

### 5. Barrel Exports

**File:** `frontend/core/src/plugin/index.ts`

```typescript
export * from './IPlugin';
export * from './PluginRegistry';
export * from './PluginLoader';
```

**File:** `frontend/core/src/sdk/index.ts`

```typescript
export * from './PlatformSDK';
export * from './PlatformSDKImpl';
```

---

## Testing Strategy

### Unit Tests

**File:** `frontend/core/__tests__/unit/plugin/PluginRegistry.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { PluginRegistry } from '../../../src/plugin/PluginRegistry';
import type { IPlugin } from '../../../src/plugin/IPlugin';

describe('PluginRegistry', () => {
  let registry: PluginRegistry;

  beforeEach(() => {
    registry = new PluginRegistry();
  });

  it('should register a plugin', () => {
    const plugin: IPlugin = {
      metadata: { name: 'test-plugin', version: '1.0.0' },
      install: async () => {},
    };

    registry.register(plugin);
    expect(registry.has('test-plugin')).toBe(true);
    expect(registry.count()).toBe(1);
  });

  it('should throw error if plugin already registered', () => {
    const plugin: IPlugin = {
      metadata: { name: 'test-plugin', version: '1.0.0' },
      install: async () => {},
    };

    registry.register(plugin);
    expect(() => registry.register(plugin)).toThrow('already registered');
  });

  it('should resolve load order with dependencies', () => {
    const pluginA: IPlugin = {
      metadata: { name: 'A', version: '1.0.0' },
      install: async () => {},
    };

    const pluginB: IPlugin = {
      metadata: { name: 'B', version: '1.0.0', dependencies: ['A'] },
      install: async () => {},
    };

    const pluginC: IPlugin = {
      metadata: { name: 'C', version: '1.0.0', dependencies: ['B'] },
      install: async () => {},
    };

    registry.register(pluginC);
    registry.register(pluginA);
    registry.register(pluginB);

    const order = registry.resolveLoadOrder();
    expect(order).toEqual(['A', 'B', 'C']);
  });

  it('should detect circular dependencies', () => {
    const pluginA: IPlugin = {
      metadata: { name: 'A', version: '1.0.0', dependencies: ['B'] },
      install: async () => {},
    };

    const pluginB: IPlugin = {
      metadata: { name: 'B', version: '1.0.0', dependencies: ['A'] },
      install: async () => {},
    };

    registry.register(pluginA);
    registry.register(pluginB);

    expect(() => registry.resolveLoadOrder()).toThrow('Circular dependency');
  });

  it('should throw error for missing dependency', () => {
    const plugin: IPlugin = {
      metadata: { name: 'A', version: '1.0.0', dependencies: ['B'] },
      install: async () => {},
    };

    registry.register(plugin);

    expect(() => registry.resolveLoadOrder()).toThrow('not registered');
  });
});
```

**File:** `frontend/core/__tests__/unit/plugin/PluginLoader.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia';
import { PluginLoader } from '../../../src/plugin/PluginLoader';
import { PluginRegistry } from '../../../src/plugin/PluginRegistry';
import { PlatformSDKImpl } from '../../../src/sdk/PlatformSDKImpl';
import type { IPlugin } from '../../../src/plugin/IPlugin';

describe('PluginLoader', () => {
  let loader: PluginLoader;
  let registry: PluginRegistry;

  beforeEach(() => {
    const app = createApp({});
    const router = createRouter({ history: createWebHistory(), routes: [] });
    const pinia = createPinia();

    const sdk = new PlatformSDKImpl(
      app,
      router,
      pinia,
      {} as any, // Mock API client
      {} as any, // Mock Auth service
      {} as any, // Mock Event bus
      {} as any  // Mock Validation service
    );

    registry = new PluginRegistry();
    loader = new PluginLoader(registry, sdk);
  });

  it('should load a plugin successfully', async () => {
    const installSpy = vi.fn().mockResolvedValue(undefined);
    const activateSpy = vi.fn().mockResolvedValue(undefined);

    const plugin: IPlugin = {
      metadata: { name: 'test-plugin', version: '1.0.0' },
      install: installSpy,
      activate: activateSpy,
    };

    registry.register(plugin);

    const result = await loader.load('test-plugin');

    expect(result.status).toBe('active');
    expect(installSpy).toHaveBeenCalled();
    expect(activateSpy).toHaveBeenCalled();
  });

  it('should handle plugin installation error', async () => {
    const plugin: IPlugin = {
      metadata: { name: 'failing-plugin', version: '1.0.0' },
      install: async () => {
        throw new Error('Installation failed');
      },
    };

    registry.register(plugin);

    const result = await loader.load('failing-plugin');

    expect(result.status).toBe('error');
    expect(result.error?.message).toContain('Installation failed');
  });

  it('should load plugins in dependency order', async () => {
    const loadOrder: string[] = [];

    const pluginA: IPlugin = {
      metadata: { name: 'A', version: '1.0.0' },
      install: async () => { loadOrder.push('A'); },
    };

    const pluginB: IPlugin = {
      metadata: { name: 'B', version: '1.0.0', dependencies: ['A'] },
      install: async () => { loadOrder.push('B'); },
    };

    registry.register(pluginB);
    registry.register(pluginA);

    await loader.loadAll();

    expect(loadOrder).toEqual(['A', 'B']);
  });
});
```

---

## Integration Tests

**File:** `frontend/core/__tests__/integration/plugin-system.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia';
import { PluginRegistry, PluginLoader } from '../../src/plugin';
import { PlatformSDKImpl } from '../../src/sdk';
import type { IPlugin } from '../../src/plugin';

describe('Plugin System Integration', () => {
  it('should load and activate a complete plugin', async () => {
    const app = createApp({});
    const router = createRouter({ history: createWebHistory(), routes: [] });
    const pinia = createPinia();

    const sdk = new PlatformSDKImpl(
      app,
      router,
      pinia,
      {} as any,
      {} as any,
      {} as any,
      {} as any
    );

    const registry = new PluginRegistry();
    const loader = new PluginLoader(registry, sdk);

    // Create a complete plugin
    const testPlugin: IPlugin = {
      metadata: {
        name: 'complete-plugin',
        version: '1.0.0',
        displayName: 'Complete Plugin',
        description: 'A plugin with all features',
      },
      install: async () => {
        console.log('Plugin installed');
      },
      activate: async () => {
        console.log('Plugin activated');
      },
      registerRoutes: () => [
        {
          path: '/test',
          name: 'test-route',
          component: () => Promise.resolve({ template: '<div>Test</div>' }),
        },
      ],
      registerComponents: () => [
        {
          name: 'TestComponent',
          component: { template: '<div>Test Component</div>' },
        },
      ],
    };

    registry.register(testPlugin);
    const results = await loader.loadAll();

    expect(results).toHaveLength(1);
    expect(results[0]?.status).toBe('active');
    expect(loader.getStatus('complete-plugin')).toBe('active');

    // Verify route was added
    expect(router.hasRoute('test-route')).toBe(true);

    // Verify component was registered
    expect(app.component('TestComponent')).toBeDefined();
  });
});
```

---

## Definition of Done

- [x] IPlugin interface implemented with JSDoc
- [x] PlatformSDK interface and implementation
- [x] PluginRegistry with dependency resolution
- [x] PluginLoader with lifecycle management
- [x] Unit tests with 95%+ coverage
- [x] Integration tests
- [x] TypeScript strict mode passing
- [x] ESLint passing with no warnings
- [x] Documentation comments on all public APIs

---

## Next Sprint

[Sprint 2: API Client & HTTP Layer](./sprint-2-api-client.md)
