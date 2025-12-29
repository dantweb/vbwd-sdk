# Sprint 6: User Cabinet

**Priority:** MEDIUM
**Duration:** 2-3 days
**Focus:** User profile management, subscription view, and invoice history

> **Core Requirements:** See [sprint-plan.md](./sprint-plan.md) for mandatory TDD-first, SOLID, DI, Clean Code, and No Over-Engineering requirements.

---

## 6.1 Profile Management

### Problem
No user profile editing functionality.

### Requirements
- View profile information
- Edit name, email, avatar
- Change password
- Delete account option

### TDD Tests First

**File:** `tests/unit/services/test_profile_service.py`
```python
class TestProfileService:
    def test_get_profile_returns_user_data(self):
        """Profile endpoint returns user data."""
        pass

    def test_update_profile_changes_name(self):
        """Name update persists to database."""
        pass

    def test_update_profile_validates_email_format(self):
        """Invalid email rejected."""
        pass

    def test_change_password_requires_current_password(self):
        """Password change needs current password."""
        pass

    def test_change_password_hashes_new_password(self):
        """New password is properly hashed."""
        pass

    def test_delete_account_anonymizes_data(self):
        """Account deletion anonymizes user data."""
        pass
```

### Backend Implementation

**File:** `src/services/profile_service.py`
```python
from dataclasses import dataclass
from typing import Optional
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService

@dataclass
class ProfileUpdateData:
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None

@dataclass
class ProfileResult:
    success: bool
    user: Optional[User] = None
    error: Optional[str] = None

class ProfileService:
    def __init__(
        self,
        user_repository: UserRepository,
        auth_service: AuthService
    ):
        self.user_repo = user_repository
        self.auth_service = auth_service

    def get_profile(self, user_id: str) -> ProfileResult:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ProfileResult(success=False, error="User not found")
        return ProfileResult(success=True, user=user)

    def update_profile(self, user_id: str, data: ProfileUpdateData) -> ProfileResult:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ProfileResult(success=False, error="User not found")

        if data.email and data.email != user.email:
            # Check if email is already taken
            existing = self.user_repo.get_by_email(data.email)
            if existing:
                return ProfileResult(success=False, error="Email already in use")
            user.email = data.email

        if data.name:
            user.name = data.name

        if data.avatar_url:
            user.avatar_url = data.avatar_url

        self.user_repo.update(user)
        return ProfileResult(success=True, user=user)

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> ProfileResult:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ProfileResult(success=False, error="User not found")

        if not self.auth_service.verify_password(current_password, user.password_hash):
            return ProfileResult(success=False, error="Current password incorrect")

        user.password_hash = self.auth_service.hash_password(new_password)
        self.user_repo.update(user)
        return ProfileResult(success=True, user=user)

    def delete_account(self, user_id: str) -> ProfileResult:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ProfileResult(success=False, error="User not found")

        # Anonymize user data (GDPR compliance)
        user.email = f"deleted_{user_id}@deleted.local"
        user.name = "Deleted User"
        user.avatar_url = None
        user.deleted_at = datetime.utcnow()
        user.is_active = False

        self.user_repo.update(user)
        return ProfileResult(success=True)
```

**File:** `src/routes/profile.py`
```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.profile_service import ProfileService, ProfileUpdateData

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    service: ProfileService = current_app.container.profile_service()
    result = service.get_profile(user_id)

    if result.success:
        return jsonify({
            "id": str(result.user.id),
            "name": result.user.name,
            "email": result.user.email,
            "avatar_url": result.user.avatar_url,
            "created_at": result.user.created_at.isoformat()
        })
    return jsonify({"error": result.error}), 404

@profile_bp.route("/", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()

    service: ProfileService = current_app.container.profile_service()
    result = service.update_profile(user_id, ProfileUpdateData(
        name=data.get("name"),
        email=data.get("email"),
        avatar_url=data.get("avatar_url")
    ))

    if result.success:
        return jsonify({"message": "Profile updated"})
    return jsonify({"error": result.error}), 400

@profile_bp.route("/password", methods=["PUT"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()

    service: ProfileService = current_app.container.profile_service()
    result = service.change_password(
        user_id,
        data.get("current_password"),
        data.get("new_password")
    )

    if result.success:
        return jsonify({"message": "Password changed"})
    return jsonify({"error": result.error}), 400

@profile_bp.route("/", methods=["DELETE"])
@jwt_required()
def delete_account():
    user_id = get_jwt_identity()
    service: ProfileService = current_app.container.profile_service()
    result = service.delete_account(user_id)

    if result.success:
        return jsonify({"message": "Account deleted"})
    return jsonify({"error": result.error}), 400
```

### Frontend Implementation

**File:** `vbwd-frontend/user/vue/src/views/Profile.vue`
```vue
<template>
  <div class="profile-page">
    <h1>Profile Settings</h1>

    <Card>
      <template #header>
        <h2>Personal Information</h2>
      </template>

      <form @submit.prevent="saveProfile">
        <FormField label="Name" :error="errors.name">
          <Input v-model="form.name" placeholder="Your name" />
        </FormField>

        <FormField label="Email" :error="errors.email">
          <Input v-model="form.email" type="email" placeholder="Your email" />
        </FormField>

        <FormField label="Avatar URL" :error="errors.avatar_url">
          <Input v-model="form.avatar_url" placeholder="https://..." />
        </FormField>

        <div class="form-actions">
          <Button type="submit" :loading="saving">Save Changes</Button>
        </div>
      </form>
    </Card>

    <Card class="mt-4">
      <template #header>
        <h2>Change Password</h2>
      </template>

      <form @submit.prevent="changePassword">
        <FormField label="Current Password" :error="passwordErrors.current">
          <Input v-model="passwordForm.current" type="password" />
        </FormField>

        <FormField label="New Password" :error="passwordErrors.new">
          <Input v-model="passwordForm.new" type="password" />
        </FormField>

        <FormField label="Confirm Password" :error="passwordErrors.confirm">
          <Input v-model="passwordForm.confirm" type="password" />
        </FormField>

        <div class="form-actions">
          <Button type="submit" :loading="changingPassword">Change Password</Button>
        </div>
      </form>
    </Card>

    <Card class="mt-4 danger-zone">
      <template #header>
        <h2>Danger Zone</h2>
      </template>

      <p>Deleting your account is permanent and cannot be undone.</p>
      <Button variant="danger" @click="showDeleteModal = true">
        Delete Account
      </Button>
    </Card>

    <Modal v-model="showDeleteModal" title="Delete Account">
      <p>Are you sure you want to delete your account? This action cannot be undone.</p>
      <template #footer>
        <Button variant="ghost" @click="showDeleteModal = false">Cancel</Button>
        <Button variant="danger" @click="deleteAccount" :loading="deleting">
          Delete Account
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useProfileStore } from '../stores/profile';
import { Button, Input, Card, Modal, FormField } from '@vbwd/core-sdk';

const profileStore = useProfileStore();

const form = ref({ name: '', email: '', avatar_url: '' });
const errors = ref({});
const saving = ref(false);

const passwordForm = ref({ current: '', new: '', confirm: '' });
const passwordErrors = ref({});
const changingPassword = ref(false);

const showDeleteModal = ref(false);
const deleting = ref(false);

onMounted(async () => {
  await profileStore.fetchProfile();
  form.value = { ...profileStore.profile };
});

async function saveProfile() {
  saving.value = true;
  errors.value = {};
  try {
    await profileStore.updateProfile(form.value);
  } catch (e) {
    errors.value = e.errors || {};
  } finally {
    saving.value = false;
  }
}

async function changePassword() {
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    passwordErrors.value = { confirm: 'Passwords do not match' };
    return;
  }

  changingPassword.value = true;
  passwordErrors.value = {};
  try {
    await profileStore.changePassword(
      passwordForm.value.current,
      passwordForm.value.new
    );
    passwordForm.value = { current: '', new: '', confirm: '' };
  } catch (e) {
    passwordErrors.value = e.errors || { current: e.message };
  } finally {
    changingPassword.value = false;
  }
}

async function deleteAccount() {
  deleting.value = true;
  try {
    await profileStore.deleteAccount();
    // Redirect to login after deletion
  } finally {
    deleting.value = false;
    showDeleteModal.value = false;
  }
}
</script>
```

---

## 6.2 Subscription View/Management

### Requirements
- View current subscription
- View plan features
- See usage limits
- Upgrade/downgrade options
- Cancel subscription

### Backend Implementation

**File:** `src/routes/subscription.py` (additions)
```python
@subscription_bp.route("/current", methods=["GET"])
@jwt_required()
def get_current_subscription():
    user_id = get_jwt_identity()
    service: SubscriptionService = current_app.container.subscription_service()
    subscription = service.get_active_subscription(user_id)

    if not subscription:
        return jsonify({"subscription": None})

    return jsonify({
        "subscription": {
            "id": str(subscription.id),
            "plan": {
                "id": str(subscription.tarif_plan.id),
                "name": subscription.tarif_plan.name,
                "features": subscription.tarif_plan.features,
                "limits": subscription.tarif_plan.limits
            },
            "status": subscription.status.value,
            "current_period_start": subscription.start_date.isoformat(),
            "current_period_end": subscription.end_date.isoformat() if subscription.end_date else None,
            "cancel_at_period_end": subscription.cancel_at_period_end
        }
    })

@subscription_bp.route("/usage", methods=["GET"])
@jwt_required()
def get_usage():
    user_id = get_jwt_identity()
    guard: FeatureGuard = current_app.container.feature_guard()
    usage = guard.get_feature_limits(user_id)
    return jsonify({"usage": usage})
```

### Frontend Implementation

**File:** `vbwd-frontend/user/vue/src/views/Subscription.vue`
```vue
<template>
  <div class="subscription-page">
    <h1>Your Subscription</h1>

    <Card v-if="subscription">
      <template #header>
        <div class="plan-header">
          <h2>{{ subscription.plan.name }}</h2>
          <Badge :variant="statusVariant">{{ subscription.status }}</Badge>
        </div>
      </template>

      <div class="plan-details">
        <div class="billing-period">
          <p><strong>Current Period:</strong></p>
          <p>{{ formatDate(subscription.current_period_start) }} - {{ formatDate(subscription.current_period_end) }}</p>
        </div>

        <div v-if="subscription.cancel_at_period_end" class="cancellation-notice">
          <Alert variant="warning">
            Your subscription will end on {{ formatDate(subscription.current_period_end) }}
          </Alert>
        </div>

        <h3>Plan Features</h3>
        <ul class="features-list">
          <li v-for="feature in subscription.plan.features" :key="feature">
            <span class="check">✓</span> {{ feature }}
          </li>
        </ul>
      </div>

      <template #footer>
        <Button variant="ghost" @click="showCancelModal = true" v-if="!subscription.cancel_at_period_end">
          Cancel Subscription
        </Button>
        <Button @click="$router.push('/plans')">
          {{ subscription.cancel_at_period_end ? 'Reactivate' : 'Change Plan' }}
        </Button>
      </template>
    </Card>

    <Card v-else>
      <p>You don't have an active subscription.</p>
      <Button @click="$router.push('/plans')">View Plans</Button>
    </Card>

    <!-- Usage Section -->
    <Card class="mt-4" v-if="Object.keys(usage).length">
      <template #header>
        <h2>Usage This Period</h2>
      </template>

      <div class="usage-grid">
        <div v-for="(data, feature) in usage" :key="feature" class="usage-item">
          <p class="usage-label">{{ formatFeatureName(feature) }}</p>
          <div class="usage-bar">
            <div
              class="usage-fill"
              :style="{ width: `${(data.used / data.limit) * 100}%` }"
              :class="{ 'usage-warning': data.remaining < data.limit * 0.2 }"
            />
          </div>
          <p class="usage-text">{{ data.used }} / {{ data.limit }} ({{ data.remaining }} remaining)</p>
        </div>
      </div>
    </Card>

    <Modal v-model="showCancelModal" title="Cancel Subscription">
      <p>Are you sure you want to cancel? You'll lose access to premium features at the end of your billing period.</p>
      <template #footer>
        <Button variant="ghost" @click="showCancelModal = false">Keep Subscription</Button>
        <Button variant="danger" @click="cancelSubscription" :loading="cancelling">
          Confirm Cancellation
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useSubscriptionStore } from '../stores/subscription';
import { Button, Card, Badge, Alert, Modal } from '@vbwd/core-sdk';

const store = useSubscriptionStore();

const subscription = computed(() => store.subscription);
const usage = computed(() => store.usage);
const showCancelModal = ref(false);
const cancelling = ref(false);

const statusVariant = computed(() => {
  const status = subscription.value?.status;
  if (status === 'active') return 'success';
  if (status === 'past_due') return 'warning';
  if (status === 'cancelled') return 'danger';
  return 'default';
});

onMounted(() => {
  store.fetchSubscription();
  store.fetchUsage();
});

function formatDate(date: string) {
  return new Date(date).toLocaleDateString();
}

function formatFeatureName(name: string) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

async function cancelSubscription() {
  cancelling.value = true;
  try {
    await store.cancelSubscription();
    showCancelModal.value = false;
  } finally {
    cancelling.value = false;
  }
}
</script>
```

---

## 6.3 Invoice History & Download

### Requirements
- List all invoices
- Download invoice PDF
- Filter by date range
- Pagination

### Backend Implementation

**File:** `src/routes/invoices.py`
```python
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

invoices_bp = Blueprint("invoices", __name__)

@invoices_bp.route("/", methods=["GET"])
@jwt_required()
def list_invoices():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    service: InvoiceService = current_app.container.invoice_service()
    result = service.list_invoices(user_id, page, per_page)

    return jsonify({
        "invoices": [
            {
                "id": str(inv.id),
                "number": inv.number,
                "amount": inv.amount,
                "currency": inv.currency,
                "status": inv.status,
                "created_at": inv.created_at.isoformat(),
                "pdf_url": f"/api/v1/invoices/{inv.id}/pdf"
            }
            for inv in result.items
        ],
        "total": result.total,
        "page": page,
        "per_page": per_page
    })

@invoices_bp.route("/<invoice_id>/pdf", methods=["GET"])
@jwt_required()
def download_invoice_pdf(invoice_id):
    user_id = get_jwt_identity()
    service: InvoiceService = current_app.container.invoice_service()

    result = service.get_invoice_pdf(invoice_id, user_id)
    if not result.success:
        return jsonify({"error": result.error}), 404

    return send_file(
        result.pdf_bytes,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"invoice_{result.invoice_number}.pdf"
    )
```

### Frontend Implementation

**File:** `vbwd-frontend/user/vue/src/views/Invoices.vue`
```vue
<template>
  <div class="invoices-page">
    <h1>Invoice History</h1>

    <Card>
      <Table :columns="columns" :data="invoices" :loading="loading">
        <template #cell-status="{ row }">
          <Badge :variant="row.status === 'paid' ? 'success' : 'warning'">
            {{ row.status }}
          </Badge>
        </template>
        <template #cell-actions="{ row }">
          <Button variant="link" @click="downloadInvoice(row.id)">
            Download PDF
          </Button>
        </template>
      </Table>

      <Pagination
        v-model:page="page"
        :total="total"
        :per-page="perPage"
        @change="fetchInvoices"
      />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useInvoiceStore } from '../stores/invoices';
import { Card, Table, Badge, Button, Pagination } from '@vbwd/core-sdk';

const store = useInvoiceStore();

const invoices = ref([]);
const loading = ref(false);
const page = ref(1);
const perPage = ref(10);
const total = ref(0);

const columns = [
  { key: 'number', label: 'Invoice #' },
  { key: 'created_at', label: 'Date', format: 'date' },
  { key: 'amount', label: 'Amount', format: 'currency' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
];

onMounted(() => fetchInvoices());

async function fetchInvoices() {
  loading.value = true;
  try {
    const result = await store.fetchInvoices(page.value, perPage.value);
    invoices.value = result.invoices;
    total.value = result.total;
  } finally {
    loading.value = false;
  }
}

async function downloadInvoice(id: string) {
  await store.downloadInvoicePdf(id);
}
</script>
```

---

## 6.4 Plan Upgrade/Downgrade UI

### Requirements
- View all available plans
- Compare plans
- Upgrade/downgrade flow
- Proration display

### Frontend Implementation

**File:** `vbwd-frontend/user/vue/src/views/Plans.vue`
```vue
<template>
  <div class="plans-page">
    <h1>Choose Your Plan</h1>

    <div class="plans-grid">
      <Card
        v-for="plan in plans"
        :key="plan.id"
        :class="['plan-card', { 'current': currentPlanId === plan.id }]"
      >
        <template #header>
          <h2>{{ plan.name }}</h2>
          <p class="price">
            <span class="amount">${{ plan.price }}</span>
            <span class="period">/month</span>
          </p>
        </template>

        <ul class="features">
          <li v-for="feature in plan.features" :key="feature">
            <span class="check">✓</span> {{ feature }}
          </li>
        </ul>

        <template #footer>
          <Badge v-if="currentPlanId === plan.id" variant="info">Current Plan</Badge>
          <Button
            v-else
            @click="selectPlan(plan)"
            :variant="plan.price > currentPlanPrice ? 'primary' : 'secondary'"
          >
            {{ plan.price > currentPlanPrice ? 'Upgrade' : 'Downgrade' }}
          </Button>
        </template>
      </Card>
    </div>

    <Modal v-model="showConfirmModal" title="Confirm Plan Change">
      <div v-if="selectedPlan">
        <p>You're changing from <strong>{{ currentPlanName }}</strong> to <strong>{{ selectedPlan.name }}</strong>.</p>

        <div v-if="proration" class="proration-details">
          <p><strong>Today's charge:</strong> ${{ proration.amount }}</p>
          <p class="hint">This is prorated for the remaining days in your billing period.</p>
        </div>
      </div>

      <template #footer>
        <Button variant="ghost" @click="showConfirmModal = false">Cancel</Button>
        <Button @click="confirmPlanChange" :loading="changing">
          Confirm Change
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { usePlansStore } from '../stores/plans';
import { useSubscriptionStore } from '../stores/subscription';
import { Card, Badge, Button, Modal } from '@vbwd/core-sdk';

const plansStore = usePlansStore();
const subscriptionStore = useSubscriptionStore();

const plans = computed(() => plansStore.plans);
const currentPlanId = computed(() => subscriptionStore.subscription?.plan.id);
const currentPlanName = computed(() => subscriptionStore.subscription?.plan.name || 'Free');
const currentPlanPrice = computed(() => subscriptionStore.subscription?.plan.price || 0);

const selectedPlan = ref(null);
const showConfirmModal = ref(false);
const proration = ref(null);
const changing = ref(false);

onMounted(() => {
  plansStore.fetchPlans();
});

async function selectPlan(plan) {
  selectedPlan.value = plan;
  // Calculate proration
  proration.value = await plansStore.calculateProration(plan.id);
  showConfirmModal.value = true;
}

async function confirmPlanChange() {
  changing.value = true;
  try {
    await subscriptionStore.changePlan(selectedPlan.value.id);
    showConfirmModal.value = false;
    // Refresh subscription data
    await subscriptionStore.fetchSubscription();
  } finally {
    changing.value = false;
  }
}
</script>

<style scoped>
.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.plan-card.current {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.price {
  margin-top: 0.5rem;
}

.price .amount {
  font-size: 2rem;
  font-weight: 700;
}

.price .period {
  color: var(--color-text-muted);
}

.features {
  list-style: none;
  padding: 0;
}

.features li {
  padding: 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.check {
  color: var(--color-success);
}
</style>
```

---

## Checklist

### 6.1 Profile Management
- [ ] Tests for ProfileService
- [ ] ProfileService implemented
- [ ] Profile routes created
- [ ] Profile.vue component
- [ ] Password change working
- [ ] Account deletion working
- [ ] All tests pass

### 6.2 Subscription View
- [ ] Subscription routes
- [ ] Usage endpoint
- [ ] Subscription.vue component
- [ ] Usage display
- [ ] Cancel flow working

### 6.3 Invoice History
- [ ] Invoice routes
- [ ] PDF download endpoint
- [ ] Invoices.vue component
- [ ] Pagination working

### 6.4 Plan Change UI
- [ ] Plans.vue component
- [ ] Proration calculation
- [ ] Upgrade flow
- [ ] Downgrade flow
- [ ] Confirmation modal

---

## Verification Commands

```bash
# Run profile tests
docker-compose --profile test run --rm test pytest tests/unit/services/test_profile_service.py -v

# Test frontend
cd vbwd-frontend/user/vue
npm run dev

# Check profile routes
curl http://localhost:5000/api/v1/profile -H "Authorization: Bearer $TOKEN"
```
