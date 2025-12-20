# VBWD-SDK as a SaaS Platform

**Document:** SaaS Implementation Architecture
**Status:** Planning
**License:** CC0 1.0 Universal (Public Domain)

---

## Executive Summary

This document describes how VBWD-SDK can be deployed and operated as a **Software-as-a-Service (SaaS)** platform, enabling multiple independent customers (tenants) to use the subscription and booking management system without deploying their own infrastructure.

---

## 1. SaaS Architecture Overview

### 1.1 Multi-Tenant Architecture

```
+-------------------------------------------------------------------------+
|                        VBWD-SDK SaaS Platform                            |
+-------------------------------------------------------------------------+
|                                                                          |
|   +-------------------+  +-------------------+  +-------------------+    |
|   |   Tenant A        |  |   Tenant B        |  |   Tenant C        |    |
|   |   (Medical Clinic)|  |   (Law Firm)      |  |   (Online School) |    |
|   +-------------------+  +-------------------+  +-------------------+    |
|           |                      |                      |                |
|           +----------------------+----------------------+                |
|                                  |                                       |
|   +--------------------------------------------------------------+      |
|   |                    Shared Infrastructure                      |      |
|   |  +------------+  +------------+  +------------+  +----------+ |      |
|   |  | API Gateway|  | Auth      |  | Payment    |  | Email    | |      |
|   |  |            |  | Service   |  | Service    |  | Service  | |      |
|   |  +------------+  +------------+  +------------+  +----------+ |      |
|   +--------------------------------------------------------------+      |
|                                  |                                       |
|   +--------------------------------------------------------------+      |
|   |                       Data Layer                              |      |
|   |  +-------------------+  +-------------------+                 |      |
|   |  | Tenant Database   |  | Shared Database   |                 |      |
|   |  | (per-tenant data) |  | (platform config) |                 |      |
|   |  +-------------------+  +-------------------+                 |      |
|   +--------------------------------------------------------------+      |
|                                                                          |
+-------------------------------------------------------------------------+
```

### 1.2 Multi-Tenancy Strategies

| Strategy | Description | Isolation | Cost | Complexity |
|----------|-------------|-----------|------|------------|
| **Shared Database** | All tenants in one DB with tenant_id | Low | Low | Low |
| **Schema per Tenant** | Separate schema per tenant | Medium | Medium | Medium |
| **Database per Tenant** | Dedicated DB per tenant | High | High | High |

**Recommended Approach:** Hybrid model with shared infrastructure and logical data isolation.

---

## 2. Tenant Data Model

### 2.1 Tenant Entity

```sql
CREATE TABLE tenants (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    -- Identification
    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,

    -- Business Info
    business_type ENUM('medical', 'legal', 'education', 'consulting', 'other') NOT NULL,
    description TEXT,

    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    custom_domain VARCHAR(255),

    -- Configuration
    timezone VARCHAR(50) DEFAULT 'UTC',
    currency VARCHAR(3) DEFAULT 'EUR',
    locale VARCHAR(10) DEFAULT 'en',

    -- Subscription Tier
    plan_id BIGINT REFERENCES saas_plans(id),
    subscription_status ENUM('trial', 'active', 'suspended', 'cancelled') DEFAULT 'trial',
    trial_ends_at DATETIME,

    -- Limits (based on plan)
    max_users INT DEFAULT 5,
    max_bookings_per_month INT DEFAULT 100,
    max_events INT DEFAULT 10,
    storage_limit_mb INT DEFAULT 1024,

    -- Billing
    billing_email VARCHAR(255),
    billing_address JSON,
    payment_method_id VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_tenant_code (tenant_code),
    INDEX idx_custom_domain (custom_domain),
    INDEX idx_subscription_status (subscription_status)
);
```

### 2.2 Tenant-Aware Entities

All existing entities gain a `tenant_id` foreign key:

```sql
-- Users belong to tenants
ALTER TABLE users ADD COLUMN tenant_id BIGINT REFERENCES tenants(id);
ALTER TABLE users ADD INDEX idx_user_tenant (tenant_id, email);

-- Rooms belong to tenants
ALTER TABLE rooms ADD COLUMN tenant_id BIGINT REFERENCES tenants(id);

-- Events belong to tenants
ALTER TABLE events ADD COLUMN tenant_id BIGINT REFERENCES tenants(id);

-- All other entities follow the same pattern
```

### 2.3 SaaS Plans (Platform Subscription)

```sql
CREATE TABLE saas_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,

    -- Pricing
    monthly_price DECIMAL(10,2) NOT NULL,
    yearly_price DECIMAL(10,2),

    -- Limits
    max_users INT NOT NULL,
    max_bookings_per_month INT NOT NULL,
    max_events INT NOT NULL,
    max_tickets_per_event INT NOT NULL,
    storage_limit_mb INT NOT NULL,

    -- Features
    custom_domain BOOLEAN DEFAULT FALSE,
    white_label BOOLEAN DEFAULT FALSE,
    api_access BOOLEAN DEFAULT FALSE,
    priority_support BOOLEAN DEFAULT FALSE,
    analytics_dashboard BOOLEAN DEFAULT FALSE,
    custom_integrations BOOLEAN DEFAULT FALSE,

    -- Display
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Example Plans
INSERT INTO saas_plans (name, slug, monthly_price, max_users, max_bookings_per_month, max_events, max_tickets_per_event, storage_limit_mb, custom_domain, white_label, api_access) VALUES
('Starter', 'starter', 29.00, 3, 100, 5, 50, 1024, FALSE, FALSE, FALSE),
('Professional', 'professional', 79.00, 10, 500, 25, 200, 5120, TRUE, FALSE, TRUE),
('Business', 'business', 199.00, 50, 2000, 100, 1000, 20480, TRUE, TRUE, TRUE),
('Enterprise', 'enterprise', 499.00, -1, -1, -1, -1, 102400, TRUE, TRUE, TRUE);
```

---

## 3. Tenant Isolation

### 3.1 Request Context

Every API request includes tenant context:

```python
from flask import g, request
from functools import wraps

class TenantContext:
    """Global tenant context for current request"""

    @staticmethod
    def get_current_tenant():
        return getattr(g, 'current_tenant', None)

    @staticmethod
    def set_current_tenant(tenant):
        g.current_tenant = tenant


def require_tenant(f):
    """Decorator to ensure tenant context is set"""
    @wraps(f)
    def decorated(*args, **kwargs):
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required'}), 400
        return f(*args, **kwargs)
    return decorated


class TenantMiddleware:
    """Middleware to resolve tenant from request"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Resolve tenant from subdomain or header
        host = environ.get('HTTP_HOST', '')
        tenant = self._resolve_tenant(host)

        if tenant:
            environ['tenant'] = tenant

        return self.app(environ, start_response)

    def _resolve_tenant(self, host):
        # Option 1: Subdomain-based (tenant.vbwd-platform.com)
        if '.vbwd-platform.com' in host:
            subdomain = host.split('.')[0]
            return Tenant.query.filter_by(tenant_code=subdomain).first()

        # Option 2: Custom domain (clinic.example.com)
        return Tenant.query.filter_by(custom_domain=host).first()
```

### 3.2 Query Scoping

All queries are automatically scoped to current tenant:

```python
from sqlalchemy import event

class TenantScopedQuery:
    """Base query class that automatically filters by tenant"""

    def __init__(self, entities, session=None):
        super().__init__(entities, session)
        self._add_tenant_filter()

    def _add_tenant_filter(self):
        tenant = TenantContext.get_current_tenant()
        if tenant:
            for entity in self._entities:
                if hasattr(entity, 'tenant_id'):
                    self.filter(entity.tenant_id == tenant.id)


# Automatic tenant_id assignment on insert
@event.listens_for(Base, 'before_insert', propagate=True)
def set_tenant_id(mapper, connection, target):
    if hasattr(target, 'tenant_id') and target.tenant_id is None:
        tenant = TenantContext.get_current_tenant()
        if tenant:
            target.tenant_id = tenant.id
```

### 3.3 Data Isolation Verification

```python
class TenantIsolationService:
    """Service to verify and enforce tenant data isolation"""

    @staticmethod
    def verify_access(entity, tenant_id: int) -> bool:
        """Verify entity belongs to tenant"""
        if hasattr(entity, 'tenant_id'):
            return entity.tenant_id == tenant_id
        return True

    @staticmethod
    def verify_user_access(user_id: int, tenant_id: int) -> bool:
        """Verify user belongs to tenant"""
        user = User.query.get(user_id)
        return user and user.tenant_id == tenant_id

    @staticmethod
    def cross_tenant_check(query_result, tenant_id: int):
        """Verify query results don't leak across tenants"""
        for entity in query_result:
            if not TenantIsolationService.verify_access(entity, tenant_id):
                raise SecurityException("Cross-tenant data access detected")
```

---

## 4. White-Label Customization

### 4.1 Branding Configuration

```python
class TenantBranding:
    """Tenant branding configuration"""

    def __init__(self, tenant):
        self.tenant = tenant

    def get_css_variables(self) -> dict:
        """Generate CSS custom properties for tenant branding"""
        return {
            '--primary-color': self.tenant.primary_color or '#3B82F6',
            '--secondary-color': self.tenant.secondary_color or '#10B981',
            '--logo-url': self.tenant.logo_url or '/default-logo.svg',
            '--font-family': self.tenant.font_family or 'Inter, sans-serif',
        }

    def get_email_template_vars(self) -> dict:
        """Variables for email templates"""
        return {
            'company_name': self.tenant.name,
            'logo_url': self.tenant.logo_url,
            'primary_color': self.tenant.primary_color,
            'support_email': self.tenant.support_email,
            'website_url': self._get_tenant_url(),
        }

    def _get_tenant_url(self) -> str:
        if self.tenant.custom_domain:
            return f"https://{self.tenant.custom_domain}"
        return f"https://{self.tenant.tenant_code}.vbwd-platform.com"
```

### 4.2 Custom Domain Setup

```python
class CustomDomainService:
    """Manage custom domains for tenants"""

    @staticmethod
    def verify_domain(domain: str, tenant_id: int) -> dict:
        """Verify domain ownership via DNS TXT record"""
        verification_token = f"vbwd-verify={tenant_id}-{secrets.token_hex(16)}"

        # Check if TXT record exists
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'TXT')
            for rdata in answers:
                if verification_token in str(rdata):
                    return {'verified': True, 'domain': domain}
        except:
            pass

        return {
            'verified': False,
            'required_txt_record': verification_token,
            'instructions': f"Add TXT record: {verification_token}"
        }

    @staticmethod
    def configure_ssl(domain: str):
        """Configure SSL certificate via Let's Encrypt"""
        # Integration with cert-manager or ACME client
        pass
```

---

## 5. SaaS Billing & Metering

### 5.1 Usage Tracking

```python
class UsageTracker:
    """Track tenant resource usage"""

    @staticmethod
    def track_booking(tenant_id: int):
        """Track booking creation"""
        redis_client.incr(f"usage:{tenant_id}:bookings:{current_month()}")

    @staticmethod
    def track_ticket_sale(tenant_id: int, quantity: int):
        """Track ticket sales"""
        redis_client.incrby(f"usage:{tenant_id}:tickets:{current_month()}", quantity)

    @staticmethod
    def track_storage(tenant_id: int, bytes_added: int):
        """Track storage usage"""
        redis_client.incrby(f"usage:{tenant_id}:storage", bytes_added)

    @staticmethod
    def get_usage(tenant_id: int) -> dict:
        """Get current usage for tenant"""
        month = current_month()
        return {
            'bookings_this_month': int(redis_client.get(f"usage:{tenant_id}:bookings:{month}") or 0),
            'tickets_this_month': int(redis_client.get(f"usage:{tenant_id}:tickets:{month}") or 0),
            'storage_bytes': int(redis_client.get(f"usage:{tenant_id}:storage") or 0),
            'users_count': User.query.filter_by(tenant_id=tenant_id).count(),
            'events_count': Event.query.filter_by(tenant_id=tenant_id).count(),
        }

    @staticmethod
    def check_limits(tenant_id: int, resource: str) -> bool:
        """Check if tenant is within usage limits"""
        tenant = Tenant.query.get(tenant_id)
        usage = UsageTracker.get_usage(tenant_id)

        limits = {
            'bookings': (usage['bookings_this_month'], tenant.max_bookings_per_month),
            'users': (usage['users_count'], tenant.max_users),
            'events': (usage['events_count'], tenant.max_events),
            'storage': (usage['storage_bytes'], tenant.storage_limit_mb * 1024 * 1024),
        }

        current, limit = limits.get(resource, (0, -1))
        return limit == -1 or current < limit
```

### 5.2 SaaS Subscription Billing

```python
class SaaSBillingService:
    """Handle SaaS subscription billing"""

    def __init__(self, payment_provider):
        self.provider = payment_provider

    def create_subscription(self, tenant: Tenant, plan: SaaSPlan) -> dict:
        """Create subscription for tenant"""
        # Create Stripe subscription
        subscription = self.provider.create_subscription(
            customer_id=tenant.stripe_customer_id,
            price_id=plan.stripe_price_id,
            metadata={'tenant_id': tenant.id}
        )

        # Update tenant
        tenant.plan_id = plan.id
        tenant.subscription_status = 'active'
        tenant.stripe_subscription_id = subscription.id

        # Apply plan limits
        tenant.max_users = plan.max_users
        tenant.max_bookings_per_month = plan.max_bookings_per_month
        tenant.max_events = plan.max_events
        tenant.storage_limit_mb = plan.storage_limit_mb

        db.session.commit()

        return {'subscription_id': subscription.id, 'status': 'active'}

    def handle_subscription_webhook(self, event: dict):
        """Handle Stripe subscription webhooks"""
        event_type = event['type']
        subscription = event['data']['object']
        tenant_id = subscription['metadata']['tenant_id']

        tenant = Tenant.query.get(tenant_id)

        if event_type == 'customer.subscription.updated':
            tenant.subscription_status = subscription['status']
        elif event_type == 'customer.subscription.deleted':
            tenant.subscription_status = 'cancelled'
            tenant.plan_id = None
        elif event_type == 'invoice.payment_failed':
            tenant.subscription_status = 'suspended'
            self._notify_payment_failed(tenant)

        db.session.commit()
```

---

## 6. API Gateway & Routing

### 6.1 Tenant-Aware Routing

```python
# API Blueprint with tenant context
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.before_request
def before_request():
    """Set tenant context before each request"""
    tenant = resolve_tenant_from_request(request)
    if not tenant:
        return jsonify({'error': 'Invalid tenant'}), 400

    TenantContext.set_current_tenant(tenant)

    # Check subscription status
    if tenant.subscription_status == 'suspended':
        return jsonify({'error': 'Account suspended. Please update payment method.'}), 402

    if tenant.subscription_status == 'cancelled':
        return jsonify({'error': 'Account cancelled'}), 403


def resolve_tenant_from_request(request):
    """Resolve tenant from request"""
    # Priority 1: X-Tenant-ID header (for API clients)
    tenant_id = request.headers.get('X-Tenant-ID')
    if tenant_id:
        return Tenant.query.filter_by(tenant_code=tenant_id, is_active=True).first()

    # Priority 2: Subdomain
    host = request.host
    if '.vbwd-platform.com' in host:
        subdomain = host.split('.')[0]
        return Tenant.query.filter_by(tenant_code=subdomain, is_active=True).first()

    # Priority 3: Custom domain
    return Tenant.query.filter_by(custom_domain=host, is_active=True).first()
```

### 6.2 Rate Limiting per Tenant

```python
from flask_limiter import Limiter

def get_tenant_rate_limit_key():
    """Rate limit key based on tenant + user"""
    tenant = TenantContext.get_current_tenant()
    user = get_current_user()
    if tenant and user:
        return f"tenant:{tenant.id}:user:{user.id}"
    elif tenant:
        return f"tenant:{tenant.id}"
    return request.remote_addr

limiter = Limiter(
    key_func=get_tenant_rate_limit_key,
    default_limits=["1000 per hour", "100 per minute"]
)

# Plan-based rate limits
def get_plan_rate_limit():
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return "100 per minute"

    plan_limits = {
        'starter': "200 per minute",
        'professional': "500 per minute",
        'business': "1000 per minute",
        'enterprise': "5000 per minute",
    }

    return plan_limits.get(tenant.plan.slug, "100 per minute")
```

---

## 7. Deployment Architecture

### 7.1 Kubernetes Deployment

```yaml
# Kubernetes deployment for SaaS platform
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vbwd-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vbwd-api
  template:
    metadata:
      labels:
        app: vbwd-api
    spec:
      containers:
      - name: api
        image: vbwd/api:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: vbwd-api
spec:
  selector:
    app: vbwd-api
  ports:
  - port: 80
    targetPort: 5000
---
# Ingress for subdomain routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vbwd-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - "*.vbwd-platform.com"
    secretName: wildcard-tls
  rules:
  - host: "*.vbwd-platform.com"
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: vbwd-api
            port:
              number: 80
```

### 7.2 Database Scaling

```
+------------------------------------------------------------------+
|                      Database Architecture                         |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------------+    +------------------------+          |
|  |   Primary (Write)      |    |   Read Replicas        |          |
|  |   MySQL 8.0            |--->|   MySQL 8.0 (x3)       |          |
|  |   m5.xlarge            |    |   m5.large             |          |
|  +------------------------+    +------------------------+          |
|                                                                    |
|  +------------------------+                                        |
|  |   Redis Cluster        |    Cache layer for:                   |
|  |   (Session, Cache)     |    - Session data                     |
|  |   r5.large (x3)        |    - Usage metrics                    |
|  +------------------------+    - Rate limiting                    |
|                                                                    |
|  +------------------------+                                        |
|  |   Elasticsearch        |    Search layer for:                  |
|  |   (Search, Logs)       |    - Full-text search                 |
|  |   m5.large (x3)        |    - Audit logs                       |
|  +------------------------+                                        |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 8. Security Considerations

### 8.1 Tenant Data Security

| Layer | Security Measure |
|-------|-----------------|
| **Application** | Tenant ID validation on every query |
| **Database** | Row-level security policies |
| **Network** | VPC isolation, private subnets |
| **Encryption** | AES-256 at rest, TLS 1.3 in transit |
| **Audit** | Complete audit trail per tenant |

### 8.2 Compliance Features

```python
class ComplianceService:
    """GDPR and compliance features"""

    @staticmethod
    def export_tenant_data(tenant_id: int) -> dict:
        """Export all tenant data (GDPR data portability)"""
        return {
            'tenant': Tenant.query.get(tenant_id).to_dict(),
            'users': [u.to_dict() for u in User.query.filter_by(tenant_id=tenant_id).all()],
            'bookings': [b.to_dict() for b in Booking.query.filter_by(tenant_id=tenant_id).all()],
            'events': [e.to_dict() for e in Event.query.filter_by(tenant_id=tenant_id).all()],
            'tickets': [t.to_dict() for t in Ticket.query.filter_by(tenant_id=tenant_id).all()],
            'export_date': datetime.utcnow().isoformat(),
        }

    @staticmethod
    def delete_tenant_data(tenant_id: int):
        """Complete tenant data deletion (GDPR right to erasure)"""
        # Delete in order respecting foreign keys
        TicketScan.query.filter(Ticket.tenant_id == tenant_id).delete()
        Ticket.query.filter_by(tenant_id=tenant_id).delete()
        Event.query.filter_by(tenant_id=tenant_id).delete()
        Booking.query.filter_by(tenant_id=tenant_id).delete()
        User.query.filter_by(tenant_id=tenant_id).delete()
        Tenant.query.filter_by(id=tenant_id).delete()

        db.session.commit()
```

---

## 9. SaaS Pricing Model

### 9.1 Recommended Tiers

| Plan | Monthly Price | Users | Bookings/mo | Events | Features |
|------|--------------|-------|-------------|--------|----------|
| **Starter** | $29 | 3 | 100 | 5 | Basic features |
| **Professional** | $79 | 10 | 500 | 25 | Custom domain, API access |
| **Business** | $199 | 50 | 2,000 | 100 | White-label, Analytics |
| **Enterprise** | $499+ | Unlimited | Unlimited | Unlimited | Custom integrations, SLA |

### 9.2 Add-on Revenue

| Add-on | Price | Description |
|--------|-------|-------------|
| Additional Users | $5/user/mo | Beyond plan limit |
| Additional Storage | $0.10/GB/mo | Beyond plan limit |
| SMS Notifications | $0.05/SMS | Booking/event reminders |
| Priority Support | $49/mo | 4-hour response SLA |
| Custom Integration | $500 setup | One-time setup fee |

---

## 10. Implementation Roadmap

### Phase 1: Multi-Tenancy Foundation (4 weeks)
- [ ] Tenant data model and migrations
- [ ] Tenant context middleware
- [ ] Query scoping implementation
- [ ] Basic tenant management API

### Phase 2: Tenant Onboarding (3 weeks)
- [ ] Self-service registration
- [ ] Onboarding wizard
- [ ] Initial data seeding
- [ ] Email verification

### Phase 3: Billing Integration (3 weeks)
- [ ] SaaS plan management
- [ ] Stripe subscription integration
- [ ] Usage tracking
- [ ] Limit enforcement

### Phase 4: White-Label Features (2 weeks)
- [ ] Branding configuration
- [ ] Custom domain support
- [ ] Email template customization

### Phase 5: Admin Portal (3 weeks)
- [ ] Platform admin dashboard
- [ ] Tenant management
- [ ] Usage analytics
- [ ] Support ticket system

---

## Related Documentation

- [Backend Architecture](./architecture_backend/README.md)
- [Payment Architecture](./architecture_backend/payment-architecture.md)
- [Marketplace Architecture](./README_MARKET.md)
- [Booking & Ticket System](./architecture_backend/booking-ticket-system.md)
