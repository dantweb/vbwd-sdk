# Task 05: Align User Update API

**Priority:** High
**Type:** Backend
**Estimate:** Small

## Problem

The frontend `UserEdit.vue` sends data that doesn't match what the backend expects.

### Frontend Sends (stores/users.ts)
```typescript
// updateUser
PUT /admin/users/:id
{ is_active: boolean, name: string }

// updateUserRoles
PUT /admin/users/:id/roles
{ roles: string[] }
```

### Backend Expects (routes/admin/users.py)
```python
# update_user (line 184)
PUT /admin/users/:id
{ status: "active"|"suspended", role: "user"|"admin" }

# updateUserRoles - NOT IMPLEMENTED
```

## Solution Options

### Option A: Update Backend to Match Frontend (Recommended)
Modify `routes/admin/users.py` to:
1. Accept `is_active` and convert to `status`
2. Accept `name` and update `UserDetails.first_name/last_name`
3. Add new endpoint `PUT /admin/users/:id/roles` for multi-role support

### Option B: Update Frontend to Match Backend
Modify `stores/users.ts` and `UserEdit.vue` to:
1. Send `status` instead of `is_active`
2. Remove `name` field (or handle differently)
3. Send single `role` instead of `roles[]`

## Implementation (Option A)

### File: `vbwd-backend/src/routes/admin/users.py`

1. **Update `update_user` function (line 184):**
```python
@admin_users_bp.route('/<user_id>', methods=['PUT'])
@require_auth
@require_admin
def update_user(user_id):
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}

    # Handle is_active -> status conversion
    if 'is_active' in data:
        user.status = UserStatus.ACTIVE if data['is_active'] else UserStatus.SUSPENDED

    # Handle legacy status field
    if 'status' in data:
        try:
            user.status = UserStatus(data['status'])
        except ValueError:
            return jsonify({'error': f"Invalid status: {data['status']}"}), 400

    # Handle name -> UserDetails
    if 'name' in data and data['name']:
        parts = data['name'].strip().split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        if user.details:
            user.details.first_name = first_name
            user.details.last_name = last_name
        else:
            user_details = UserDetails()
            user_details.user_id = user.id
            user_details.first_name = first_name
            user_details.last_name = last_name
            db.session.add(user_details)

    # Handle role (single)
    if 'role' in data:
        try:
            user.role = UserRole(data['role'])
        except ValueError:
            return jsonify({'error': f"Invalid role: {data['role']}"}), 400

    saved_user = user_repo.save(user)
    return jsonify({'user': saved_user.to_dict()}), 200
```

2. **Add `update_user_roles` endpoint:**
```python
@admin_users_bp.route('/<user_id>/roles', methods=['PUT'])
@require_auth
@require_admin
def update_user_roles(user_id):
    """Update user roles (multi-role support)."""
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    roles = data.get('roles', [])

    if not roles:
        return jsonify({'error': 'At least one role is required'}), 400

    # For now, use the first role (single-role model)
    # TODO: Implement multi-role support in User model
    try:
        user.role = UserRole(roles[0])
    except ValueError:
        return jsonify({'error': f"Invalid role: {roles[0]}"}), 400

    saved_user = user_repo.save(user)
    return jsonify({
        'user': saved_user.to_dict(),
        'message': 'Roles updated'
    }), 200
```

## Testing

```bash
# Test update user
curl -X PUT http://localhost:5000/api/v1/admin/users/<id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true, "name": "John Doe"}'

# Test update roles
curl -X PUT http://localhost:5000/api/v1/admin/users/<id>/roles \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"roles": ["admin", "user"]}'
```

## Acceptance Criteria

- [ ] `PUT /admin/users/:id` accepts `is_active` boolean
- [ ] `PUT /admin/users/:id` accepts `name` string and updates UserDetails
- [ ] `PUT /admin/users/:id/roles` endpoint exists and works
- [ ] Existing tests still pass
- [ ] E2E edit user flow works end-to-end
