# Phase 2: Frontend Setup

**Goal**: Scaffold Vue 3 + Vite + TypeScript frontend project, implement login page, app layout, and base UI components.

**Dependencies**: Phase 1 (Backend Auth + API) must be complete. The `/api/v1/auth/login` and `/api/v1/auth/logout` endpoints must be available.

**Estimated Effort**: 2-3 days.

---

## Task 2.1: Scaffold Vue 3 + Vite + TypeScript Project

**Location**: `frontend/` (at project root, sibling to `portalonline_gmap_scraper/`)

### 2.1.1: Create Project

```bash
cd /home/indatech/Documents/BOT/portalonline-gmap-scraper
npm create vite@latest frontend -- --template vue-ts
cd frontend
```

### 2.1.2: Install Dependencies

```bash
npm install vue-router@4 pinia axios
npm install -D tailwindcss @tailwindcss/vite lucide-vue-next
```

### 2.1.3: Configure Vite

**File**: `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../portalonline_gmap_scraper/static',
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
```

**Notes**:
- Dev proxy `/api` -> `http://localhost:8000` (FastAPI backend)
- Build output goes to `portalonline_gmap_scraper/static/` for FastAPI `StaticFiles` serving
- Tailwind CSS configured via `@tailwindcss/vite` plugin (no PostCSS config needed)

### 2.1.4: Configure Path Alias in tsconfig

**File**: `frontend/tsconfig.json`

Add compilerOptions:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### 2.1.5: Configure Tailwind CSS

**File**: `frontend/src/assets/main.css`

```css
@import "tailwindcss";

@theme {
  --color-primary: #2563eb;
  --color-primary-dark: #1d4ed8;
  --color-danger: #dc2626;
  --color-danger-dark: #b91c1c;
  --color-success: #16a34a;
  --color-warning: #d97706;
}
```

### 2.1.6: Verify Scaffold

```bash
cd frontend && npm run dev
# Visit http://localhost:5173 - should show default Vite + Vue page
```

**Verify**: `npm run build` produces files in `portalonline_gmap_scraper/static/`

---

## Task 2.2: TypeScript Types

**File**: `frontend/src/types/index.ts`

All shared TypeScript types matching the backend API models:

```typescript
// ── Auth ──
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: UserInfo
}

export interface UserInfo {
  user_id: string
  username: string
  role: 'admin' | 'user'
}

// ── Dashboard ──
export interface DashboardStats {
  total_users: number
  total_jobs: number
  total_leads: number
  active_jobs: number
  queued_jobs: number
  recent_jobs: RecentJob[]
}

export interface RecentJob {
  job_id: string
  keyword: string
  location: string | null
  status: JobStatus
  leads_collected: number
  leads_total: number
  created_at: string
}

// ── Job ──
export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface JobCreate {
  keyword: string
  location?: string
  target?: number
  smart?: boolean
}

export interface JobResponse {
  job_id: string
  user_id: string
  username: string
  keyword: string
  location: string | null
  query: string
  status: JobStatus
  target: number
  smart: boolean
  queue_position: number | null
  leads_collected: number
  leads_total: number
  error: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface JobsPage {
  jobs: JobResponse[]
  total: number
  page: number
  limit: number
  pages: number
}

// ── SSE ──
export interface SSEProgress {
  event: 'progress' | 'status_change' | 'completed' | 'connected' | 'heartbeat'
  leads_collected?: number
  total_leads?: number
  lead?: LeadResponse
  old?: JobStatus
  new?: JobStatus
  status?: JobStatus
  job_id?: string
}

// ── Lead ──
export interface LeadResponse {
  id: number
  job_id: string
  user_id: string
  keyword: string
  name: string
  address: string
  phone: string
  website: string
  rating: string
  review_count: string
  scraped_at: string
}

// ── User Management ──
export interface UserResponse {
  user_id: string
  username: string
  role: 'admin' | 'user'
  api_key: string
  active: boolean
  webhook_url: string | null
  webhook_events: string | null
  created_at: string
}

export interface UserCreate {
  username: string
  role?: string
}

export interface UserUpdate {
  username?: string
  role?: string
  active?: boolean
  webhook_url?: string | null
  webhook_events?: string[] | null
}

export interface GeneratePasswordResponse {
  password: string
  message: string
}

export interface GenerateApiKeyResponse {
  api_key: string
  message: string
}
```

**Verify**: `npx vue-tsc --noEmit` passes

---

## Task 2.3: API Client Setup

### 2.3.1: Axios Instance

**File**: `frontend/src/services/api.ts`

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
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
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### 2.3.2: Auth Service

**File**: `frontend/src/services/auth.ts`

```typescript
import api from './api'
import type { LoginRequest, LoginResponse, DashboardStats } from '@/types'

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const resp = await api.post<LoginResponse>('/auth/login', data)
  return resp.data
}

export async function logout(): Promise<{ success: boolean }> {
  const resp = await api.post<{ success: boolean }>('/auth/logout')
  return resp.data
}

export async function getStats(): Promise<DashboardStats> {
  const resp = await api.get<DashboardStats>('/admin/stats')
  return resp.data
}
```

### 2.3.3: Jobs Service

**File**: `frontend/src/services/jobs.ts`

```typescript
import api from './api'
import type { JobCreate, JobResponse, JobsPage, LeadResponse } from '@/types'

export async function submitJob(data: JobCreate): Promise<JobResponse> {
  const resp = await api.post<JobResponse>('/jobs', data)
  return resp.data
}

export async function listJobs(params: {
  page?: number; limit?: number; status?: string; keyword?: string; user_id?: string
} = {}): Promise<JobsPage> {
  const resp = await api.get<JobsPage>('/jobs', { params })
  return resp.data
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const resp = await api.get<JobResponse>(`/jobs/${jobId}`)
  return resp.data
}

export async function cancelJob(jobId: string): Promise<{ success: boolean }> {
  const resp = await api.delete(`/jobs/${jobId}`)
  return resp.data
}

export async function getJobResults(
  jobId: string, format: 'json' | 'csv' = 'json'
): Promise<{ results: LeadResponse[]; total: number }> {
  const resp = await api.get(`/jobs/${jobId}/results`, { params: { format } })
  return resp.data
}

export function getJobStreamUrl(jobId: string): string {
  const token = localStorage.getItem('token')
  return `/api/v1/jobs/${jobId}/stream?token=${token}`
}
```

### 2.3.4: Users Service

**File**: `frontend/src/services/users.ts`

```typescript
import api from './api'
import type {
  UserResponse, UserCreate, UserUpdate,
  GeneratePasswordResponse, GenerateApiKeyResponse,
} from '@/types'

export async function listUsers(): Promise<UserResponse[]> {
  const resp = await api.get<UserResponse[]>('/users')
  return resp.data
}

export async function getUser(userId: string): Promise<UserResponse> {
  const resp = await api.get<UserResponse>(`/users/${userId}`)
  return resp.data
}

export async function createUser(data: UserCreate): Promise<UserResponse> {
  const resp = await api.post<UserResponse>('/users', data)
  return resp.data
}

export async function updateUser(userId: string, data: UserUpdate): Promise<UserResponse> {
  const resp = await api.patch<UserResponse>(`/users/${userId}`, data)
  return resp.data
}

export async function deleteUser(userId: string): Promise<{ success: boolean }> {
  const resp = await api.delete(`/users/${userId}`)
  return resp.data
}

export async function generatePassword(userId: string): Promise<GeneratePasswordResponse> {
  const resp = await api.post<GeneratePasswordResponse>(`/users/${userId}/generate-password`)
  return resp.data
}

export async function generateApiKey(userId: string): Promise<GenerateApiKeyResponse> {
  const resp = await api.post<GenerateApiKeyResponse>(`/users/${userId}/generate-api-key`)
  return resp.data
}
```

**Verify**: `npx vue-tsc --noEmit` passes for all service files.

---

## Task 2.4: Pinia Auth Store

**File**: `frontend/src/stores/auth.ts`

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types'
import * as authService from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(
    JSON.parse(localStorage.getItem('user') || 'null')
  )

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const resp = await authService.login({ username, password })
    token.value = resp.token
    user.value = resp.user
    localStorage.setItem('token', resp.token)
    localStorage.setItem('user', JSON.stringify(resp.user))
  }

  function logout() {
    authService.logout().catch(() => {})
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, isAdmin, login, logout }
})
```

**Verify**: Store compiles. Can be imported in components.

---

## Task 2.5: Vue Router Setup

**File**: `frontend/src/router/index.ts`

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { public: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/pages/DashboardPage.vue'),
    },
    {
      path: '/scrape',
      name: 'scrape',
      component: () => import('@/pages/ScrapePage.vue'),
    },
    {
      path: '/results',
      name: 'results',
      component: () => import('@/pages/ResultsPage.vue'),
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('@/pages/UsersPage.vue'),
      meta: { adminOnly: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (auth.isAuthenticated) return next('/dashboard')
    return next()
  }

  if (!auth.isAuthenticated) return next('/login')
  if (to.meta.adminOnly && !auth.isAdmin) return next('/dashboard')
  return next()
})

export default router
```

**Route behavior**:

| Route | Auth | Admin | Redirect |
|---|---|---|---|
| `/login` | No | No | `/dashboard` if authed |
| `/dashboard` | Yes | No | `/login` if unauthed |
| `/scrape` | Yes | No | `/login` if unauthed |
| `/results` | Yes | No | `/login` if unauthed |
| `/users` | Yes | Yes | `/dashboard` if non-admin |
| `/*` | - | - | `/dashboard` |

**Verify**: Router compiles. Guards redirect correctly.

---

## Task 2.6: Login Page

**File**: `frontend/src/pages/LoginPage.vue`

Full implementation with these states:

| State | Behavior |
|---|---|
| **Default** | Empty form, Login button enabled |
| **Loading** | Button disabled + spinner, inputs disabled |
| **Error** | Red error banner above form (invalid credentials or connection error) |
| **Already authed** | Auto-redirect to `/dashboard` |

**Key behaviors**:
- On mount: clear stale localStorage token/user (prevents stale redirect loop)
- Submit: call `authStore.login(username, password)`, then `router.push('/dashboard')`
- Error 401: "Invalid username or password"
- Network error: "Connection error. Is the server running?"
- Enter key submits form (both inputs)

**Layout**: Centered card (min-h-screen flex justify-center items-center bg-gray-50). Card: white bg, shadow-xl, rounded-xl, p-8, w-96 max-w-full.

**Form fields**:
- PortalOnline heading + subtitle
- Username input (autofocus, autocomplete="username")
- Password input (type="password", autocomplete="current-password")
- Login button (primary, full width)

**Verify**:
- Page renders centered login card
- Invalid credentials -> error message
- Valid credentials -> redirect to `/dashboard`
- Already authed -> auto-redirect to `/dashboard`

---

## Task 2.7: App Layout Components

### 2.7.1: AppHeader

**File**: `frontend/src/components/layout/AppHeader.vue`

```
+---------------------------------------------------------------+
| [PortalOnline]                       [admin v] [  Logout  ]   |
+---------------------------------------------------------------+
```

- Left: App name "PortalOnline" (text-xl, font-bold)
- Right: username + role Badge + "Logout" button (danger variant, size sm)
- Logout: calls `authStore.logout()`, `router.push('/login')`
- Fixed height: h-14, border-b, bg-white, shadow-sm, flex items-center px-6

### 2.7.2: AppSidebar

**File**: `frontend/src/components/layout/AppSidebar.vue`

```
+------------------+
| [>] Dashboard    |
| [>] Scrape       |
| [>] Results      |
| [>] Users (admin)|
+------------------+
```

- Nav links with Lucide icons (LayoutDashboard, Search, FileText, Users)
- Active link: bg-primary/10, text-primary, border-r-2 border-primary
- Inactive link: text-gray-600, hover:bg-gray-100
- Width: w-56, full height, bg-white, border-r
- Users link: `v-if="authStore.isAdmin"`
- Uses `router-link` with `active-class`

### 2.7.3: AppLayout

**File**: `frontend/src/components/layout/AppLayout.vue`

```
+---------------------------------------------------------------+
| AppHeader (h-14, sticky top)                                  |
+--------------------------+------------------------------------+
| AppSidebar (w-56)        | <router-view />                   |
|                          | (p-6, overflow-y-auto)             |
+--------------------------+------------------------------------+
```

- Full height: `h-screen flex flex-col`
- Body: `flex flex-1 overflow-hidden`
- Main: `flex-1 overflow-y-auto p-6 bg-gray-50`

**Verify**: Layout renders. Sidebar navigation works. Users hidden for non-admin.

---

## Task 2.8: Base UI Components

### 2.8.1: BaseButton

**File**: `frontend/src/components/ui/BaseButton.vue`

**Props**: `variant: 'primary' | 'danger' | 'ghost'`, `disabled: boolean`, `loading: boolean`, `size: 'sm' | 'md'`

| Variant | Classes |
|---|---|
| primary | bg-primary text-white hover:bg-primary-dark |
| danger | bg-red-600 text-white hover:bg-red-700 |
| ghost | text-gray-700 hover:bg-gray-100 |

Loading state: Spinner (Lucide Loader2 with animate-spin) + dimmed, click disabled.
Slot: default for button text.

### 2.8.2: BaseModal

**File**: `frontend/src/components/ui/BaseModal.vue`

**Props**: `show: boolean`, `title: string`, `size: 'sm' | 'md' | 'lg'`

- `<Teleport to="body">`
- Overlay: fixed inset-0 bg-black/50 z-50, click emits `@close`
- Card: centered, white bg, rounded-xl, shadow-2xl, max-h-[90vh] overflow-y-auto
- Header: title (text-lg font-semibold) + close X button
- Body: `<slot />`, Footer: `<slot name="footer" />`
- `<Transition>` with fade+scale

### 2.8.3: BaseTable

**File**: `frontend/src/components/ui/BaseTable.vue`

**Props**: `columns: Column[]` (each: `key, label, width?, sortable?`), `rows: Record<string, any>[]`, `loading: boolean`, `emptyText: string`

States:
- **Loading**: 5 skeleton rows (gray animate-pulse bars)
- **Empty**: centered icon + emptyText
- **Data**: rows with border-b, hover:bg-gray-50

Slots: `#cell-{key}` scoped slot for custom cell rendering.

### 2.8.4: BaseBadge

**File**: `frontend/src/components/ui/BaseBadge.vue`

**Props**: `variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral'`, `text: string`

| Variant | Classes |
|---|---|
| success | bg-green-100 text-green-800 |
| warning | bg-amber-100 text-amber-800 |
| danger | bg-red-100 text-red-800 |
| info | bg-blue-100 text-blue-800 |
| neutral | bg-gray-100 text-gray-700 |

**Utility** (`frontend/src/utils/status.ts`):
```typescript
import type { JobStatus } from '@/types'

export function statusVariant(status: JobStatus): 'info' | 'warning' | 'success' | 'danger' | 'neutral' {
  const map: Record<JobStatus, 'info' | 'warning' | 'success' | 'danger' | 'neutral'> = {
    queued: 'info', running: 'warning', completed: 'success',
    failed: 'danger', cancelled: 'neutral',
  }
  return map[status]
}
```

### 2.8.5: BaseCard

**File**: `frontend/src/components/ui/BaseCard.vue`

**Props**: `title?: string`

- White bg, border, rounded-xl, shadow-sm
- Optional title header with bottom border (text-lg font-semibold px-6 py-4)
- Body slot (p-6)

---

## Task 2.9: App Entry Point

### 2.9.1: main.ts

**File**: `frontend/src/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

### 2.9.2: App.vue

**File**: `frontend/src/App.vue`

```vue
<template>
  <router-view />
</template>
```

Router determines: LoginPage (full-screen, no layout) or AppLayout wrapping authenticated pages.

### 2.9.3: index.html

**File**: `frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PortalOnline - GMap Scraper</title>
  </head>
  <body class="bg-gray-50 text-gray-900 antialiased">
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

---

## Task 2.10: Backend - Serve Frontend Static Files

**File**: `portalonline_gmap_scraper/api/app.py` (modify `create_app()`)

Add after all API routes are registered, before returning app:

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists() and static_dir.is_dir():
    # Mount assets subdirectory first for hashed filenames
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    # Root mount with SPA fallback
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
```

**Critical ordering**: API routes (`/api/v1/*`) must be registered BEFORE static mount so they take priority. The `html=True` enables SPA fallback (serves `index.html` for unknown paths).

**Verify**: `npm run build`, start server, visit `http://localhost:8000` -> shows login page. API calls to `/api/v1/*` still work.

---

## Task 2.11: SSE Token Passing

SSE (EventSource) does not support custom headers. Pass JWT token as query parameter.

**Backend modification** - `portalonline_gmap_scraper/api/routes/sse.py`:

In `stream_job_progress()`, support `token` query param as auth fallback:

```python
from ..middleware.auth import verify_token  # new function from Phase 1

@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    request: Request,
    token: str | None = Query(None),
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
```

If `token` query param present, verify it and use that user. Otherwise fall through to `verify_api_key`/`verify_jwt` header auth.

**Frontend** - `frontend/src/services/jobs.ts` already returns URL with token:
```typescript
export function getJobStreamUrl(jobId: string): string {
  const token = localStorage.getItem('token')
  return `/api/v1/jobs/${jobId}/stream?token=${token}`
}
```

---

## Verification Checklist

- [ ] `npm create vite@latest` succeeds (Vue + TS template)
- [ ] `npm install` installs all deps (vue-router, pinia, axios, tailwindcss, lucide-vue-next)
- [ ] `npm run dev` starts on :5173, proxy forwards `/api` to :8000
- [ ] `npm run build` outputs to `portalonline_gmap_scraper/static/`
- [ ] `npx vue-tsc --noEmit` zero TypeScript errors
- [ ] Login page renders at `/login` (centered form card)
- [ ] Login success: redirects to `/dashboard`
- [ ] Login failure: red error message shown
- [ ] Login loading: spinner + disabled inputs
- [ ] Logout: clears token, redirects to `/login`
- [ ] AppLayout: header + sidebar + content renders
- [ ] Sidebar: all 4 nav links work, active highlight visible
- [ ] Users link hidden for non-admin role
- [ ] Unauthenticated access -> redirect to `/login`
- [ ] Non-admin `/users` -> redirect to `/dashboard`
- [ ] BaseButton: all variants render, loading spinner works
- [ ] BaseModal: opens/closes, overlay click closes
- [ ] BaseTable: data, loading, empty states render
- [ ] BaseBadge: all 5 variant colors render
- [ ] BaseCard: renders with/without title
- [ ] FastAPI serves static build at `http://localhost:8000/`
- [ ] API routes still work alongside static file serving
