# Sprint Report: CLI Plugin Manager

**Sprint:** 02-cli-plugin-manager
**Date Completed:** 2026-01-05
**Status:** Done

---

## Summary

Implemented a command-line interface (CLI) for managing plugins in VBWD frontend applications. The CLI is available in both admin and user apps, providing a unified way to list, install, uninstall, activate, and deactivate plugins.

---

## Deliverables

### 1. Core CLI Module (`vbwd-frontend/core/src/cli/`)

| File | Description |
|------|-------------|
| `types.ts` | TypeScript interfaces for plugin configuration |
| `config.ts` | Read/write utilities for plugins.json |
| `PluginManagerCLI.ts` | Main CLI class with all commands |
| `index.ts` | Barrel exports for the CLI module |

### 2. Admin App Integration (`vbwd-frontend/admin/vue/`)

| File | Description |
|------|-------------|
| `bin/plugin-manager.ts` | CLI entry point |
| `plugins.json` | Plugin configuration file |
| `package.json` | Added `plugin` script and `tsx` dependency |

### 3. User App Integration (`vbwd-frontend/user/`)

| File | Description |
|------|-------------|
| `bin/plugin-manager.ts` | CLI entry point |
| `plugins.json` | Plugin configuration file |
| `package.json` | Added `plugin` script and `tsx` dependency |

---

## CLI Commands

```bash
# List all plugins with their status
npm run plugin list

# Install a plugin from local plugins directory
npm run plugin install <name>

# Uninstall a plugin (removes from config, keeps files)
npm run plugin uninstall <name>

# Activate an installed plugin
npm run plugin activate <name>

# Deactivate a plugin without removing it
npm run plugin deactivate <name>

# Show help message
npm run plugin help

# Show version
npm run plugin version
```

---

## Example Usage

```bash
$ npm run plugin list

VBWD Plugin Manager v1.0.0

NAME                VERSION     STATUS        DESCRIPTION
──────────────────────────────────────────────────────────────────────
stripe-payment      1.2.0       active        Stripe payment provider
paypal-payment      1.1.0       inactive      PayPal payment provider

Total: 2 plugins (1 active, 1 inactive)
```

```bash
$ npm run plugin install stripe-payment

Installing stripe-payment...
  Found plugin version: 1.2.0
  Installed to /path/to/src/plugins/stripe-payment
  Updated plugins.json

Plugin installed successfully.
Run 'npm run plugin activate stripe-payment' to enable.
```

---

## Technical Details

### plugins.json Schema

```json
{
  "plugins": {
    "plugin-name": {
      "enabled": true,
      "version": "1.0.0",
      "installedAt": "2026-01-05T10:30:00.000Z",
      "source": "local"
    }
  }
}
```

### Architecture Decision

The CLI imports directly from core source files rather than the built dist package. This is necessary because:

1. Vite externalizes Node.js modules (fs, path) for browser compatibility
2. The CLI runs in Node.js context with tsx
3. Direct source imports allow full Node.js API access

```typescript
// Import from source directly for Node.js CLI
import { PluginManagerCLI } from '../../../core/src/cli/PluginManagerCLI';
import { PluginRegistry } from '../../../core/src/plugins/PluginRegistry';
```

---

## Files Changed

### Created
- `vbwd-frontend/core/src/cli/types.ts`
- `vbwd-frontend/core/src/cli/config.ts`
- `vbwd-frontend/core/src/cli/PluginManagerCLI.ts`
- `vbwd-frontend/core/src/cli/index.ts`
- `vbwd-frontend/admin/vue/bin/plugin-manager.ts`
- `vbwd-frontend/admin/vue/plugins.json`
- `vbwd-frontend/user/bin/plugin-manager.ts`
- `vbwd-frontend/user/plugins.json`

### Modified
- `vbwd-frontend/core/src/index.ts` - Added CLI export
- `vbwd-frontend/admin/vue/package.json` - Added plugin script and tsx
- `vbwd-frontend/user/package.json` - Added plugin script and tsx

---

## Testing

All CLI commands tested successfully:

| Command | Status |
|---------|--------|
| `npm run plugin list` | Passed |
| `npm run plugin help` | Passed |
| `npm run plugin version` | Passed |
| `npm run plugin install <name>` | Passed (correctly reports missing plugin) |

---

## Future Improvements

1. **NPM Registry Support**: Currently only supports local plugins; NPM download not yet implemented
2. **Hot Reload**: Activate/deactivate could support hot reload in dev mode
3. **Plugin Info**: Add `plugin info <name>` for detailed plugin information
4. **Plugin Update**: Add `plugin update <name>` for updating plugins
5. **Plugin Search**: Add `plugin search <query>` to search plugin registry

---

## Related Documentation

- Architecture: `docs/architecture_core_view_component/README.md`
- Sprint Definition: `docs/devlog/20260105/done/02-cli-plugin-manager.md`

---

*Report generated: 2026-01-05*
