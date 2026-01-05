# Architectural Decision Record: Plugin System vs Flat Structure

**Date:** 2026-01-05
**Status:** DECIDED
**Decision Makers:** Project Owner

---

## Context

The VBWD-SDK project has a fully implemented plugin system in `frontend/core/src/plugins/` with:
- `PluginRegistry` - registration, lifecycle, dependency resolution
- `PlatformSDK` - provides routes, components, stores to plugins
- `IPlugin` interface with install/activate/deactivate/uninstall hooks

However, the admin and user applications use a flat `src/views/` structure for core features instead of the plugin architecture.

### The Question

Should we:
1. Keep flat structure for all features?
2. Migrate all features to plugin architecture?
3. Use a hybrid approach?

---

## Decision

**HYBRID ARCHITECTURE**: Flat structure for core features, plugin system for extensibility.

### What Uses Flat Structure (`src/views/`, `src/stores/`)

Core business features that every installation needs:
- **User Management** - Users.vue, UserDetails.vue, users.ts store
- **Plan Management** - Plans.vue, PlanForm.vue, planAdmin.ts store
- **Subscription Management** - Subscriptions.vue, SubscriptionDetails.vue
- **Invoice Management** - Invoices.vue, InvoiceDetails.vue
- **Analytics** - Dashboard.vue, Analytics.vue
- **Webhooks** - Webhooks.vue, WebhookDetails.vue
- **Settings** - Settings.vue

### What Uses Plugin System (`src/plugins/`)

Features that vary between installations or need dynamic loading:
- **Payment Providers** - Stripe, PayPal, custom payment integrations
- **Value-Added Services** - CRM integrations, email marketing, analytics providers
- **Custom Extensions** - Deployment-specific functionality

---

## Rationale

### Why NOT plugins for core features?

1. **Simplicity**: Core features are required by every installation. Making them plugins adds unnecessary complexity.

2. **Performance**: Plugins have lifecycle overhead (registration, installation, activation). Core features don't need this.

3. **Development Speed**: Flat structure is faster to develop and debug. No plugin boilerplate.

4. **Code Organization**: Core features don't need to be swapped out or disabled. They're foundational.

### Why USE plugins for integrations?

1. **Variability**: Payment providers vary between deployments. Plugin architecture allows easy swapping.

2. **Optional Features**: Not all installations need Stripe or PayPal. Plugins can be enabled/disabled.

3. **Isolation**: Third-party integrations should be isolated from core code.

4. **Extension Points**: Custom deployments can add functionality without modifying core.

---

## Consequences

### Positive

- Simpler codebase for 90% of development work
- Plugin system remains available for extensibility
- Clear separation between core and optional features
- Easier onboarding for new developers

### Negative

- Need to maintain two patterns (flat + plugins)
- Architecture docs needed updating (done)
- Core SDK plugin examples less prominent

### Neutral

- Admin app continues using local api.ts and auth.ts (acceptable)
- Core SDK's ApiClient and auth store available but not required

---

## Implementation

### Directory Structure (Admin App)

```
src/
├── views/           # Core features (flat)
│   ├── Users.vue
│   ├── Plans.vue
│   └── ...
├── stores/          # Core stores (flat)
│   ├── users.ts
│   ├── planAdmin.ts
│   └── ...
└── plugins/         # Extension plugins
    ├── payments/
    │   ├── stripe/
    │   └── paypal/
    └── integrations/
```

### Updated Documentation

- `docs/architecture_core_view_admin/README.md` - Updated with new structure
- `docs/architecture_core_view_component/README.md` - Clarified plugin usage

---

## Related

- Previous discussions in devlog 2026-01-02
- Sprint ticket: `01-architectural-deviations-and-e2e-improvements.md`

---

*Documented: 2026-01-05*
