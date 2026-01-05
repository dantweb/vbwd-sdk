# Sprint: CLI Plugin Manager

**Date:** 2026-01-05
**Priority:** Medium
**Type:** Feature - Infrastructure

---

## Objective

Implement a CLI tool for managing plugins in applications that extend view-core (admin, user).

---

## Requirements

### Commands

| Command | Description |
|---------|-------------|
| `plugin list` | List all registered plugins with status (active/inactive), version, description |
| `plugin install <name>` | Install a plugin from npm registry or local path |
| `plugin uninstall <name>` | Remove a plugin from the application |
| `plugin activate <name>` | Activate an installed plugin |
| `plugin deactivate <name>` | Deactivate a plugin without removing it |
| `plugin help` | Show help and available commands |

### Expected Output

```bash
$ npm run plugin list

VBWD Plugin Manager v1.0.0

NAME              VERSION   STATUS      DESCRIPTION
────────────────────────────────────────────────────────────
stripe-payment    1.2.0     active      Stripe payment provider
paypal-payment    1.1.0     inactive    PayPal payment provider
mailchimp         0.9.0     active      Mailchimp email integration

Total: 3 plugins (2 active, 1 inactive)
```

```bash
$ npm run plugin install @vbwd/stripe-payment

Installing @vbwd/stripe-payment...
✓ Downloaded package
✓ Verified integrity
✓ Installed to src/plugins/stripe-payment
✓ Updated plugins.json

Plugin installed successfully. Run 'npm run plugin activate stripe-payment' to enable.
```

---

## Tasks

### Phase 1: Core SDK - PluginManagerCLI Class

**Location:** `vbwd-frontend/core/src/cli/`

- [ ] Create `PluginManagerCLI.ts` class
- [ ] Implement `list()` method - reads registry and plugins.json
- [ ] Implement `install(name)` method - downloads/copies plugin
- [ ] Implement `uninstall(name)` method - removes plugin directory
- [ ] Implement `activate(name)` method - updates plugins.json
- [ ] Implement `deactivate(name)` method - updates plugins.json
- [ ] Implement `help()` method - shows usage
- [ ] Add CLI argument parser (commander.js or yargs)
- [ ] Export from core package index

### Phase 2: Configuration File

**File:** `plugins.json`

- [ ] Define schema for plugins.json
- [ ] Implement read/write utilities
- [ ] Add validation for plugin entries
- [ ] Handle missing/corrupted config file gracefully

```json
{
  "$schema": "./plugins.schema.json",
  "plugins": {
    "stripe-payment": {
      "enabled": true,
      "version": "1.2.0",
      "installedAt": "2026-01-05T10:30:00Z"
    }
  }
}
```

### Phase 3: Admin App Integration

**Location:** `vbwd-frontend/admin/vue/`

- [ ] Create `bin/plugin-manager.ts`
- [ ] Add npm script: `"plugin": "ts-node bin/plugin-manager.ts"`
- [ ] Initialize plugins.json with empty config
- [ ] Update app startup to read plugins.json and activate plugins
- [ ] Test all commands

### Phase 4: User App Integration

**Location:** `vbwd-frontend/user/vue/`

- [ ] Create `bin/plugin-manager.ts`
- [ ] Add npm script: `"plugin": "ts-node bin/plugin-manager.ts"`
- [ ] Initialize plugins.json
- [ ] Update app startup
- [ ] Test all commands

---

## Technical Design

### PluginManagerCLI Class

```typescript
// core/src/cli/PluginManagerCLI.ts

import { IPluginRegistry } from '../plugins/types';

interface PluginManagerOptions {
  pluginsDir: string;      // Default: './src/plugins'
  configFile: string;      // Default: './plugins.json'
  registry?: string;       // npm registry URL (optional)
}

interface PluginConfig {
  enabled: boolean;
  version: string;
  installedAt: string;
  source?: string;         // npm package or local path
}

interface PluginsJson {
  plugins: Record<string, PluginConfig>;
}

export class PluginManagerCLI {
  constructor(
    private registry: IPluginRegistry,
    private options: PluginManagerOptions
  ) {}

  async run(args: string[]): Promise<void> {
    const [command, ...params] = args;

    switch (command) {
      case 'list':
        return this.list();
      case 'install':
        return this.install(params[0]);
      case 'uninstall':
        return this.uninstall(params[0]);
      case 'activate':
        return this.activate(params[0]);
      case 'deactivate':
        return this.deactivate(params[0]);
      case 'help':
      default:
        return this.help();
    }
  }

  async list(): Promise<void> { /* ... */ }
  async install(name: string): Promise<void> { /* ... */ }
  async uninstall(name: string): Promise<void> { /* ... */ }
  async activate(name: string): Promise<void> { /* ... */ }
  async deactivate(name: string): Promise<void> { /* ... */ }
  help(): void { /* ... */ }
}
```

### App Integration

```typescript
// admin/vue/bin/plugin-manager.ts
#!/usr/bin/env ts-node

import { PluginManagerCLI, PluginRegistry } from '@vbwd/view-component';

const registry = new PluginRegistry();
const cli = new PluginManagerCLI(registry, {
  pluginsDir: './src/plugins',
  configFile: './plugins.json'
});

cli.run(process.argv.slice(2))
  .catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
```

### App Startup Integration

```typescript
// admin/vue/src/main.ts

import { loadPluginConfig } from '@vbwd/view-component';

async function bootstrap() {
  // ... existing setup ...

  // Load plugin configuration
  const pluginConfig = await loadPluginConfig('./plugins.json');

  // Register and activate enabled plugins
  for (const [name, config] of Object.entries(pluginConfig.plugins)) {
    if (config.enabled) {
      const plugin = await import(`./plugins/${name}`);
      registry.register(plugin.default);
      await registry.activate(name);
    }
  }

  // ... continue with app mount ...
}
```

---

## Dependencies

- `commander` or `yargs` - CLI argument parsing
- `chalk` - Terminal colors (optional)
- `ora` - Spinners for async operations (optional)

---

## Acceptance Criteria

1. [ ] `npm run plugin list` shows all plugins with status
2. [ ] `npm run plugin install <name>` installs from npm or local path
3. [ ] `npm run plugin uninstall <name>` removes plugin cleanly
4. [ ] `npm run plugin activate <name>` enables plugin
5. [ ] `npm run plugin deactivate <name>` disables plugin
6. [ ] `npm run plugin help` shows usage documentation
7. [ ] plugins.json persists configuration
8. [ ] App loads plugins based on plugins.json at startup
9. [ ] Works in both admin and user apps

---

## Notes

- Install/uninstall requires app restart
- Activate/deactivate could support hot reload in dev mode (future)
- Consider adding `plugin info <name>` for detailed plugin information
- Consider adding `plugin update <name>` for updates

---

*Created: 2026-01-05*
