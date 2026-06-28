# Phase 4: User Management

**Goal**: Implement Users page (admin-only) with full CRUD and generate password/API key modals.

**Dependencies**: Phase 2 (Frontend Setup) + Phase 3 (Core Pages). Backend endpoints from Phase 1 must be available.

**Estimated Effort**: 1-2 days.

---

## Task 4.1: Users Page

**File**: `frontend/src/pages/UsersPage.vue`
**Route**: `/users` (admin only, enforced by router guard)

### 4.1.1: Page Layout

```
+---------------------------------------------------------------+
| Users                                                          |
|                                                  [+ Add User] |
+---------------------------------------------------------------+
| Users Table                                                    |
| +-----------------------------------------------------------+ |
| | Username | Role  | Status | API Key    | Created | Actions| |
| | admin    | admin | Active | pk_****1234| 2026-01 | [V][E] | |
| +-----------------------------------------------------------+ |
+---------------------------------------------------------------+
```

- Title "Users" + "Add User" button (primary, top-right)
- Users table via BaseTable

### 4.1.2: Data Flow

```typescript
import { ref, onMounted } from 'vue'
import { listUsers as fetchUsers } from '@/services/users'
import type { UserResponse } from '@/types'

const users = ref<UserResponse[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function loadUsers() {
  loading.value = true
  error.value = null
  try { users.value = await fetchUsers() }
  catch (e: any) { error.value = e.response?.data?.detail || 'Failed to load users' }
  finally { loading.value = false }
}
onMounted(loadUsers)
```

### 4.1.3: Table Columns

| Column | Key | Render |
|---|---|---|
| Username | username | font-medium, text |
| Role | role | BaseBadge: admin=info, user=neutral |
| Status | active | BaseBadge: active=success, inactive=danger |
| API Key | api_key | Masked `pk_****{last4}` + click-to-copy icon |
| Created | created_at | YYYY-MM-DD HH:mm |
| Actions | — | View (Eye), Edit (Pencil), Delete (Trash) icon buttons |

API key masking: `pk_` + first 4 asterisks + last 4 chars. Copy button writes full key to clipboard, shows "Copied!" toast.

### 4.1.4: States

| State | Behavior |
|---|---|
| Loading | 5 skeleton rows |
| Empty | "No users found." + Add User prompt |
| Error | Inline error banner + Retry |
| Data | Full table |

---

## Task 4.2: Create User Modal

**File**: `frontend/src/components/users/CreateUserModal.vue`

**Props**: `show: boolean`
**Emits**: `close`, `created(user: UserResponse)`

### Form

| Field | Component | Validation |
|---|---|---|
| Username | Text input | Required, max 50, a-z 0-9 underscore only |
| Role | Select dropdown | admin / user, default: user |

### Behavior

- Submit: `POST /api/v1/users` with `{ username, role }`
- Success: show created user (username + API key) in success state, emit `created`, auto-close after 3s
- Error: show inline error (e.g., "Username already taken")
- Username validation: only lowercase a-z, 0-9, underscore (match backend UserCreate validator)

### States

| State | Behavior |
|---|---|
| Form | Username + Role inputs, Create button |
| Submitting | Button loading, inputs disabled |
| Success | "User created" + show API key (copy button) + auto-close |
| Error | Inline error banner |

---

## Task 4.3: View User Modal

**File**: `frontend/src/components/users/ViewUserModal.vue`

**Props**: `userId: string | null`, `show: boolean`
**Emits**: `close`

Fetches user detail on open: `GET /api/v1/users/{id}`.

### Read-Only Fields

```
+---------------------------------------------------------------+
| User Details: admin                                      [X]   |
+---------------------------------------------------------------+
| Username:        admin                                        |
| Role:            [admin badge]                                |
| Status:          [Active badge]                               |
| API Key:         pk_abc123...xyz789  [Copy]                   |
| Webhook URL:     https://hooks.example.com/webhook            |
| Webhook Events:  job.completed, job.failed                    |
| Created:         2026-01-15 10:30:00                          |
+---------------------------------------------------------------+
```

Key-value display. API key: masked + copy button. Webhook fields: gray if null/empty.

### States

| State | Behavior |
|---|---|
| Loading | Skeleton key-value pairs |
| Error | "Failed to load user" + Close |
| Data | Full detail display |

---

## Task 4.4: Edit User Modal

**File**: `frontend/src/components/users/EditUserModal.vue`

**Props**: `userId: string | null`, `show: boolean`
**Emits**: `close`, `updated(user: UserResponse)`

Fetches user on open, pre-fills form.

### Editable Fields

| Field | Component | Notes |
|---|---|---|
| Username | Text input | pre-filled, same validation as create |
| Role | Select | admin/user |
| Active | Toggle switch | true/false |
| Webhook URL | Text input | URL, nullable |
| Webhook Events | Text input | comma-separated list, nullable |

### Behavior

- Submit: `PATCH /api/v1/users/{id}` with changed fields only
- Send only modified fields (track via dirty state per field)
- Success: emit `updated`, close
- Error: inline error

### States

| State | Behavior |
|---|---|
| Loading | Skeleton form |
| Form | Pre-filled editable fields, Save button |
| Submitting | Button loading, inputs disabled |
| Success | Close + refresh parent table |
| Error | Inline error banner |

---

## Task 4.5: Delete User

**File**: Inline in UsersPage (confirmation dialog)

Uses BaseModal as confirmation dialog:

```
+---------------------------------------------------------------+
| Delete User                                              [X]   |
+---------------------------------------------------------------+
| Are you sure you want to delete user "username"?              |
| This action cannot be undone.                                 |
|                                                               |
|                            [Cancel]   [Delete]                |
+---------------------------------------------------------------+
```

- Delete button: danger variant
- On confirm: `DELETE /api/v1/users/{id}`
- Success: remove from local array, close dialog
- Error: show inline error

---

## Task 4.6: Generate Password Modal

**File**: `frontend/src/components/users/GeneratePasswordModal.vue`

**Props**: `userId: string | null`, `show: boolean`
**Emits**: `close`

### Multi-Step Flow

**Step 1 - Confirmation**:

```
+---------------------------------------------------------------+
| Generate Password for "admin"                           [X]   |
+---------------------------------------------------------------+
| A random 16-character password will be generated and hashed.  |
| The plaintext password will be shown only once.               |
|                                                               |
|                         [Cancel]   [Generate]                 |
+---------------------------------------------------------------+
```

**Step 2 - Result**:

```
+---------------------------------------------------------------+
| Password Generated                                      [X]   |
+---------------------------------------------------------------+
| New password:                                                 |
| +-----------------------------------------------------------+ |
| | kX9$mP2vL5nQ8wRt                               [Copy]    | |
| +-----------------------------------------------------------+ |
|                                                               |
| ! Save this password now. It will not be shown again.         |
|                                                               |
|                                                  [Close]      |
+---------------------------------------------------------------+
```

### Behavior

- Generate: `POST /api/v1/users/{id}/generate-password`
- Result: display plaintext password in mono font, copy button, warning banner
- Close: emit close (password is gone from state)

---

## Task 4.7: Generate API Key Modal

**File**: `frontend/src/components/users/GenerateApiKeyModal.vue`

**Props**: `userId: string | null`, `show: boolean`
**Emits**: `close`

**Step 1 - Confirmation**:

```
+---------------------------------------------------------------+
| Regenerate API Key for "admin"                          [X]   |
+---------------------------------------------------------------+
| The old API key will be immediately invalidated.              |
| All services using the old key will stop working.             |
|                                                               |
|                         [Cancel]   [Regenerate]               |
+---------------------------------------------------------------+
```

**Step 2 - Result**:

```
+---------------------------------------------------------------+
| API Key Regenerated                                     [X]   |
+---------------------------------------------------------------+
| New API key:                                                  |
| +-----------------------------------------------------------+ |
| | pk_a1b2c3d4e5f6g7h8i9j0k1l2               [Copy]        | |
| +-----------------------------------------------------------+ |
|                                                               |
| ! Copy this key now. The old key is no longer valid.          |
|                                                               |
|                                                  [Close]      |
+---------------------------------------------------------------+
```

### Behavior

- Regenerate: `POST /api/v1/users/{id}/generate-api-key`
- Result: display new API key in mono font, copy button, warning banner
- Close: emit close, parent refreshes user list to get updated api_key

---

## Verification Checklist

- [ ] Users page loads only for admin (non-admin redirected)
- [ ] Users table shows all users with correct data
- [ ] API key is masked with asterisks, copy button works
- [ ] Create User modal: validates username, creates user, shows API key
- [ ] Create User modal: shows error on duplicate username
- [ ] View User modal: fetches and displays all user fields
- [ ] Edit User modal: pre-fills, saves only changed fields
- [ ] Edit User modal: validates username format
- [ ] Delete User: confirmation dialog, deletes on confirm
- [ ] Generate Password: shows password once, copy button works
- [ ] Generate Password: password is 16 characters
- [ ] Generate API Key: warns about invalidation, shows new key once
- [ ] Generate API Key: new key starts with "pk_"
- [ ] All modals close with X button or overlay click
- [ ] All loading/error/empty states render correctly
