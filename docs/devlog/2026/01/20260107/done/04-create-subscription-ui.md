# Sprint Task 04: Add Create Subscription UI

**Priority:** High
**Type:** Feature
**Estimated Effort:** Medium-High

---

## Objective

Allow admins to manually create subscriptions for users through the UI.

---

## Implementation

### New View: SubscriptionCreate.vue

Route: `/admin/subscriptions/create`

---

## Form Fields

### Required
- **User** - Select from existing users (dropdown/search)
- **Plan** - Select from existing plans (dropdown)
- **Status** - pending | active | cancelled | expired

### Optional
- **Start Date** - defaults to now
- **End Date** - calculated from plan duration or manual
- **Notes** - admin notes

---

## Backend Endpoint

`POST /api/v1/admin/subscriptions`

Request body:
```json
{
  "user_id": "uuid",
  "plan_id": "uuid",
  "status": "active",
  "start_date": "2026-01-07",
  "end_date": "2026-02-07"
}
```

---

## UI Flow

1. Admin clicks "Create Subscription" on Subscriptions page
2. Navigate to `/admin/subscriptions/create`
3. Select user (searchable dropdown)
4. Select plan (shows plan details: name, price, duration)
5. Set status
6. Optionally adjust dates
7. Click "Create"
8. Success: Toast + redirect to SubscriptionDetails
9. Error: Toast with error message

---

## Related Changes

### Subscriptions.vue
- Add "Create Subscription" button
- `data-testid="create-subscription-button"`

### Router
- Add route for `/admin/subscriptions/create`

### Store (subscriptions.ts)
- Add `createSubscription` action

---

## Acceptance Criteria

- [ ] Create Subscription button on Subscriptions page
- [ ] SubscriptionCreate.vue with form
- [ ] User selection dropdown (with search)
- [ ] Plan selection dropdown (shows details)
- [ ] Status selection
- [ ] Date pickers for start/end
- [ ] API integration
- [ ] Success/error toasts
- [ ] Redirect after creation
- [ ] data-testid attributes

---

*Created: 2026-01-07*
