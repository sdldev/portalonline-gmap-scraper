# PRD: PortalOnline Frontend UI

## Problem Statement

PortalOnline GMap Scraper currently has only a backend API with no user interface. Operators must use curl/CLI to run scraping, monitor progress, and manage users. This is difficult for non-technical users and slows down the operational workflow.

## Goals

1. Provide a web UI that allows operators to run, monitor, and manage scraping without CLI.
2. Display real-time statistics (user count, job count, lead count) on the dashboard.
3. Support live scraping progress via SSE.
4. Provide complete user management (CRUD, generate password, generate API key).

## Success Metrics

| Metric | Target |
|---|---|
| Operator can scrape without CLI | 100% workflow via UI |
| Dashboard load time | < 2s |
| Live progress update latency | < 2s (SSE) |
| User management without CLI | Full CRUD via UI |

## User Stories

| ID | Role | Story | Priority |
|---|---|---|---|
| US-01 | Admin | Login with username + password | P0 |
| US-02 | Admin | View dashboard statistics (users, jobs, leads) | P0 |
| US-03 | Admin/User | Submit scraping job via form | P0 |
| US-04 | Admin/User | View live scraping progress | P0 |
| US-05 | Admin/User | Cancel a running job | P0 |
| US-06 | Admin/User | Search and filter scraping results | P0 |
| US-07 | Admin/User | Export results to CSV | P0 |
| US-08 | Admin | Manage users (CRUD, generate password, generate API key) | P0 |
| US-09 | Admin/User | Logout | P0 |

---

## Page Specifications

### 1. Login Page

**URL**: `/login`

**Layout**:
- Centered card with username + password form
- "Login" button
- Error message when credentials are invalid

**Behavior**:
- Submit POST `/api/v1/auth/login` with `{ username, password }`
- Response: JWT token + user info
- Token stored in localStorage, sent via `Authorization: Bearer <token>` header on every request
- Redirect to `/dashboard` after successful login
- If token expired/invalid, redirect to `/login`

**API Required (NEW)**:
```
POST /api/v1/auth/login
Request:  { "username": "admin", "password": "secret" }
Response: { "token": "eyJ...", "user": { "user_id", "username", "role" } }

POST /api/v1/auth/logout
Header:   Authorization: Bearer <token>
Response: { "success": true }
```

---

### 2. Dashboard Page

**URL**: `/dashboard`

**Layout**:
- Header: app name + user info + logout button
- Sidebar: navigation (Dashboard, Scrape, Results, Users)
- Main content: 3 stat cards + recent jobs table (admin sees all data; regular user sees own data only)

**Stat Cards**:

| Card | Value | Icon |
|---|---|---|
| Total Users | `count(users)` (admin only) | Users icon |
| Total Jobs | `count(jobs)` | Jobs icon |
| Total Leads | `count(leads)` | Leads icon |

**Recent Jobs Table** (last 10, scoped to user for non-admin):

| Column | Source |
|---|---|
| Job ID | `job_id` |
| Keyword | `keyword` |
| Status | `status` (badge: queued / running / completed / failed / cancelled) |
| Leads | `leads_collected / leads_total` |
| Created | `created_at` |

**API Required (NEW)**:
```
GET /api/v1/admin/stats
Header:   Authorization: Bearer <token>
Response: {
  "total_users": 5,
  "total_jobs": 120,
  "total_leads": 3400,
  "active_jobs": 1,
  "queued_jobs": 3,
  "recent_jobs": [
    { "job_id", "keyword", "status", "leads_collected", "leads_total", "created_at" }
  ]
}
```

---

### 3. Scrape Page

**URL**: `/scrape`

**Layout**:
- Form area (top):
  - Input: **Keyword** (required, text, max 200 chars)
  - Input: **Location** (optional, text, max 100 chars)
  - Button: **Scrape** (primary, disabled when a job is already running)
  - Button: **Cancel** (danger, disabled when no active job from current session)
- Progress area (below form, visible while scraping is running):
  - Progress bar: `leads_collected / leads_total`
  - Status text: "Scraping: {keyword} in {location}..."
  - Live leads table: name, address, phone, website (updated via SSE)

**Behavior**:
- Click **Scrape**: POST `/api/v1/jobs` then switch to progress view
- Progress view: connect to SSE `GET /api/v1/jobs/{id}/stream`
- SSE events:
  - `progress`: update progress bar + append lead to live table
  - `status_change`: update status badge
  - `completed`: show "Done" + link to Results
- Click **Cancel**: DELETE `/api/v1/jobs/{id}` then stop SSE, reset form
- If a job is already queued/running, display that job (cannot submit a new one until it finishes)

**API Used (EXISTING)**:
```
POST /api/v1/jobs              → Submit job
GET  /api/v1/jobs/{id}/stream  → SSE live progress
DELETE /api/v1/jobs/{id}       → Cancel job
```

---

### 4. Results Page

**URL**: `/results`

**Layout**:
- Search bar + filters (top)
- Jobs table (main content)
- Pagination (bottom)

**Search & Filters**:

| Filter | Type | API Param |
|---|---|---|
| Search | text input | `keyword` (LIKE match on job keyword) |
| User | dropdown (admin only, shows all users) | `user_id` |
| Status | dropdown: all/queued/running/completed/failed/cancelled | `status` |

**Jobs Table Columns**:

| Column | Source |
|---|---|
| Job ID | `job_id` |
| User | `username` |
| Keyword | `keyword` |
| Location | `location` |
| Status | `status` (badge) |
| Leads | `leads_collected / leads_total` |
| Created | `created_at` |
| Actions | (see below) |

**Actions Column** (context-sensitive):

| Job Status | Actions |
|---|---|
| `queued` / `running` | **View Process** - navigate to `/scrape` (show live progress), **Cancel Job** |
| `completed` / `failed` / `cancelled` | **View Details** - modal/page: leads list + export CSV + delete job |

**Job Detail View** (modal or sub-page):
- Leads table: name, address, phone, website, rating, reviews
- Button: **Export CSV** - `GET /api/v1/jobs/{id}/results?format=csv`
- Button: **Delete Job** - confirmation dialog then `DELETE /api/v1/jobs/{id}`

**API Used (EXISTING)**:
```
GET /api/v1/jobs?status=&keyword=&user_id=&page=&limit=  → List jobs
GET /api/v1/jobs/{id}                                      → Job detail
GET /api/v1/jobs/{id}/results?format=csv                   → Export CSV
DELETE /api/v1/jobs/{id}                                   → Delete/cancel job
```

---

### 5. Users Page

**URL**: `/users` (admin only)

**Layout**:
- Button: **Add User** (top right)
- Users table (main content)

**Users Table Columns**:

| Column | Source |
|---|---|
| Username | `username` |
| Role | `role` (badge: admin/user) |
| Status | `active` (badge: active/inactive) |
| API Key | `api_key` (masked: `pk_****1234`, click to copy) |
| Created | `created_at` |
| Actions | View, Edit, Delete |

**Actions**:

| Action | Behavior |
|---|---|
| **View** | Modal: read-only user detail (all fields) |
| **Edit** | Modal: edit username, role, active status, webhook_url, webhook_events |
| **Delete** | Confirmation dialog then `DELETE /api/v1/users/{id}` |
| **Generate Password** | Modal: generate random password, hash and store, show plaintext once |
| **Generate API Key** | Modal: generate new API key, show once, replace old key |

**Modals**:

**View Modal**:
```
Username:     admin
Role:         admin
Status:       Active
API Key:      pk_abc123xyz789 (copy button)
Webhook URL:  https://example.com/hook
Created:      2026-01-15 10:30:00
```

**Edit Modal**:
- Form: username, role (dropdown), active (toggle), webhook_url, webhook_events
- Button: Save - `PATCH /api/v1/users/{id}`

**Generate Password Modal**:
- Button: "Generate" produces a random 16-char password
- Show password once (copy button)
- Warning: "Save this password now. It will not be shown again."
- Button: Confirm - `POST /api/v1/users/{id}/generate-password`

**Generate API Key Modal**:
- Confirmation: "The old API key will be replaced. Continue?"
- Button: Confirm - `POST /api/v1/users/{id}/generate-api-key`
- Show new API key once (copy button)

**API Required (NEW)**:
```
POST /api/v1/users/{id}/generate-password
Response: { "password": "randomP@ss123", "message": "Password updated" }

POST /api/v1/users/{id}/generate-api-key
Response: { "api_key": "pk_newkey123...", "message": "API key regenerated" }
```

**API Used (EXISTING)**:
```
GET    /api/v1/users           → List users
GET    /api/v1/users/{id}      → User detail
POST   /api/v1/users           → Create user
PATCH  /api/v1/users/{id}      → Update user
DELETE /api/v1/users/{id}      → Delete user
```

---

### 6. Logout

**Behavior**:
- Click logout button in the header
- `POST /api/v1/auth/logout` (invalidate token on server, optional)
- Clear localStorage (token + user info)
- Redirect to `/login`

---

## Database Changes

### Migration: Add `password_hash` to `users`

Current `users` table has no password field. Add it:

```sql
ALTER TABLE users ADD COLUMN password_hash TEXT;
```

**Updated `users` schema**:
```sql
CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT,                            -- NEW: bcrypt hash
    role           TEXT NOT NULL DEFAULT 'user',
    api_key        TEXT NOT NULL UNIQUE,
    active         INTEGER NOT NULL DEFAULT 1,
    webhook_url    TEXT,
    webhook_events TEXT DEFAULT '["job.completed","job.failed"]',
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);  -- NEW
```

**Notes**:
- `password_hash` is nullable for backward compatibility (existing users can have their password set via generate-password)
- Hash uses bcrypt via the `bcrypt` library
- Index on `username` for login lookup performance

---

## New API Endpoints

### Authentication

#### `POST /api/v1/auth/login`

```json
// Request
{ "username": "admin", "password": "secret123" }

// Response 200
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "user_id": "abc123",
    "username": "admin",
    "role": "admin"
  }
}

// Response 401
{ "detail": "Invalid credentials" }
```

**Implementation**:
- Lookup user by username
- Verify password with `bcrypt.checkpw()`
- Generate JWT token (HS256, expiry 24h)
- Token payload: `{ "user_id", "username", "role", "exp" }`
- Log audit: `auth.login`

#### `POST /api/v1/auth/logout`

```json
// Header: Authorization: Bearer <token>
// Response 200
{ "success": true }
```

**Implementation**:
- Optional: add token to a blacklist (or simply let it expire)
- Log audit: `auth.logout`

### Dashboard Stats

#### `GET /api/v1/admin/stats`

```json
// Header: Authorization: Bearer <token>
// Response 200
{
  "total_users": 5,
  "total_jobs": 120,
  "total_leads": 3400,
  "active_jobs": 1,
  "queued_jobs": 3,
  "recent_jobs": [
    {
      "job_id": "abc123",
      "keyword": "restaurant",
      "location": "Jakarta",
      "status": "completed",
      "leads_collected": 45,
      "leads_total": 50,
      "created_at": "2026-06-28T10:00:00"
    }
  ]
}
```

**Implementation**:
- Aggregate queries: `COUNT(*)` from users, jobs, leads
- `active_jobs`: `WHERE status = 'running'`
- `queued_jobs`: `WHERE status = 'queued'`
- `recent_jobs`: `ORDER BY created_at DESC LIMIT 10`
- Admin-only endpoint; regular users can call `GET /api/v1/system` for their own stats

### User Management (New)

#### `POST /api/v1/users/{user_id}/generate-password`

```json
// Header: Authorization: Bearer <token> (admin)
// Response 200
{
  "password": "kX9$mP2vL5nQ8wRt",
  "message": "Password updated. Save it now, it won't be shown again."
}
```

**Implementation**:
- Generate random 16-char password (uppercase, lowercase, digits, symbols)
- Hash with bcrypt
- Update `users.password_hash`
- Log audit: `user.generate_password`

#### `POST /api/v1/users/{user_id}/generate-api-key`

```json
// Header: Authorization: Bearer <token> (admin)
// Response 200
{
  "api_key": "pk_newkey123abc456def",
  "message": "API key regenerated. Old key is now invalid."
}
```

**Implementation**:
- Generate new API key: `pk_` + random 24 hex chars
- Update `users.api_key`
- Log audit: `user.generate_api_key`
- Old API key immediately invalidated

### Auth Middleware Update

Current auth middleware uses `X-API-Key` header. Add JWT support:

```python
async def verify_auth(request: Request, db) -> dict:
    # 1. Try JWT first (Authorization: Bearer <token>)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await get_user_by_id(db, payload["user_id"])
        if user and user["active"]:
            return user

    # 2. Fallback to API key (X-API-Key)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = await get_user_by_api_key(db, api_key)
        if user and user["active"]:
            return user

    raise HTTPException(401, "Authentication required")
```

**Backward compatible**: API key auth continues to work; JWT is added for the UI.

---

## Technical Architecture

### Frontend Stack

| Component | Technology |
|---|---|
| Framework | Vue 3 + TypeScript |
| Build Tool | Vite |
| CSS | Tailwind CSS |
| State Management | Pinia |
| Router | Vue Router |
| HTTP Client | Axios |
| Icons | Lucide Vue |

### Project Structure (Frontend)

```
frontend/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppSidebar.vue
│   │   │   └── AppLayout.vue
│   │   ├── ui/
│   │   │   ├── BaseModal.vue
│   │   │   ├── BaseTable.vue
│   │   │   ├── BaseBadge.vue
│   │   │   ├── BaseButton.vue
│   │   │   └── BaseCard.vue
│   │   ├── dashboard/
│   │   │   ├── StatCard.vue
│   │   │   └── RecentJobsTable.vue
│   │   ├── scrape/
│   │   │   ├── ScrapeForm.vue
│   │   │   ├── ProgressBar.vue
│   │   │   └── LiveResultsTable.vue
│   │   ├── results/
│   │   │   ├── JobsTable.vue
│   │   │   ├── JobDetailModal.vue
│   │   │   └── ResultFilters.vue
│   │   └── users/
│   │       ├── UsersTable.vue
│   │       ├── UserViewModal.vue
│   │       ├── UserEditModal.vue
│   │       ├── GeneratePasswordModal.vue
│   │       └── GenerateApiKeyModal.vue
│   ├── pages/
│   │   ├── LoginPage.vue
│   │   ├── DashboardPage.vue
│   │   ├── ScrapePage.vue
│   │   ├── ResultsPage.vue
│   │   └── UsersPage.vue
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── jobs.ts
│   │   └── users.ts
│   ├── services/
│   │   ├── api.ts          (axios instance + interceptors)
│   │   ├── auth.ts
│   │   ├── jobs.ts
│   │   ├── results.ts
│   │   └── users.ts
│   ├── types/
│   │   └── index.ts
│   ├── router/
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### API Client Pattern

```typescript
// services/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### SSE Client Pattern

```typescript
// composables/useJobStream.ts
export function useJobStream(jobId: string) {
  const token = localStorage.getItem('token')
  const eventSource = new EventSource(
    `/api/v1/jobs/${jobId}/stream`,
    { headers: { Authorization: `Bearer ${token}` } }
  )

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // Handle: progress, status_change, completed
  }

  return { eventSource, close: () => eventSource.close() }
}
```

---

## Navigation & Routing

```
/login          → LoginPage (public)
/dashboard      → DashboardPage (auth required)
/scrape         → ScrapePage (auth required)
/results        → ResultsPage (auth required)
/users          → UsersPage (admin only)
```

**Route Guards**:
- Unauthenticated users redirect to `/login`
- Non-admin accessing `/users` redirect to `/dashboard`

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| SSE connection drops | Medium | Medium | Auto-reconnect with exponential backoff |
| JWT secret leaked | Low | High | Use env var `JWT_SECRET`, rotate periodically |
| Large leads table performance | Medium | Medium | Pagination (50/page), virtual scroll for live result table |
| Password exposed in transit | Low | High | Show once on screen, never log, hash immediately before storing |
| API key backward compatibility | Low | Low | Support both JWT and X-API-Key in middleware |

## Open Questions

1. **Frontend hosting**: Serve from FastAPI (static files) or separate server?
   - Recommendation: Serve from FastAPI via `StaticFiles` middleware for simplicity
2. **JWT expiry**: 24h reasonable, or do we need refresh tokens?
   - Recommendation: 24h expiry, no refresh (re-login for simplicity)
3. **User self-registration**: Needed or admin-only user creation?
   - Recommendation: Admin-only (matches current flow)
4. **Branding**: Logo, colors, app name customization needed?
   - Recommendation: Default Tailwind theme, customize later

---

## Implementation Phases

### Phase 1: Backend Auth + API
- [ ] Add `password_hash` column to users table
- [ ] Add `bcrypt` and `PyJWT` dependencies
- [ ] Implement `POST /api/v1/auth/login` (JWT)
- [ ] Implement `POST /api/v1/auth/logout`
- [ ] Update auth middleware (JWT + API key dual support)
- [ ] Implement `GET /api/v1/admin/stats`
- [ ] Implement `POST /api/v1/users/{id}/generate-password`
- [ ] Implement `POST /api/v1/users/{id}/generate-api-key`
- [ ] Tests for all new endpoints

### Phase 2: Frontend Setup
- [ ] Scaffold Vue 3 + Vite + Tailwind project
- [ ] Setup router, stores, API client
- [ ] Implement login page
- [ ] Implement app layout (header, sidebar)

### Phase 3: Core Pages
- [ ] Dashboard page (stats + recent jobs)
- [ ] Scrape page (form + SSE live progress)
- [ ] Results page (table + filters + actions)

### Phase 4: User Management
- [ ] Users table
- [ ] View/Edit/Delete modals
- [ ] Generate password modal
- [ ] Generate API key modal

### Phase 5: Polish
- [ ] Loading states, error handling
- [ ] Responsive design
- [ ] Empty states, edge cases
- [ ] E2E tests

---

## Appendix: API Endpoint Summary

### Existing (unchanged)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/health` | None | Health check |
| GET | `/api/v1/system` | User | System info |
| GET | `/api/v1/config` | Admin | Get config |
| PATCH | `/api/v1/config` | Admin | Update config |
| GET | `/api/v1/users` | Admin | List users |
| GET | `/api/v1/users/me` | User | Own profile |
| GET | `/api/v1/users/{id}` | Admin | User detail |
| POST | `/api/v1/users` | Admin | Create user |
| PATCH | `/api/v1/users/{id}` | Admin | Update user |
| DELETE | `/api/v1/users/{id}` | Admin | Delete user |
| POST | `/api/v1/jobs` | User | Submit job |
| GET | `/api/v1/jobs` | User | List jobs |
| GET | `/api/v1/jobs/{id}` | User | Job detail |
| DELETE | `/api/v1/jobs/{id}` | User | Cancel job |
| GET | `/api/v1/jobs/{id}/results` | User | Job results (JSON/CSV) |
| GET | `/api/v1/jobs/{id}/stream` | User | SSE progress stream |
| GET | `/api/v1/results` | User | List leads |
| GET | `/api/v1/results/stats` | User | Lead stats |
| GET | `/api/v1/results/export` | User | Export leads |
| GET | `/api/v1/results/search` | User | Search leads |
| GET | `/api/v1/results/{id}` | User | Single lead |
| GET | `/api/v1/queue` | User | Queue status |
| PATCH | `/api/v1/queue/{id}` | Admin | Reorder queue |
| DELETE | `/api/v1/queue/{id}` | Admin | Remove from queue |
| GET | `/api/v1/admin/audit-logs` | Admin | Audit logs |
| POST | `/api/v1/admin/cleanup` | Admin | Trigger cleanup |
| GET | `/api/v1/admin/db-stats` | Admin | DB stats |

### New

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | None | Login (username + password -> JWT) |
| POST | `/api/v1/auth/logout` | User | Logout |
| GET | `/api/v1/admin/stats` | Admin | Dashboard statistics |
| POST | `/api/v1/users/{id}/generate-password` | Admin | Generate random password |
| POST | `/api/v1/users/{id}/generate-api-key` | Admin | Regenerate API key |

### Modified

| Component | Change |
|---|---|
| `users` table | Add `password_hash TEXT` column + `idx_users_username` index |
| Auth middleware | Support JWT (`Authorization: Bearer`) in addition to `X-API-Key` |
| `store.py` | Add `update_password_hash()`, `get_user_by_username()` functions |
| `models.py` | Add `LoginRequest`, `LoginResponse`, `DashboardStats`, `PasswordGenerateResponse`, `ApiKeyGenerateResponse` |
