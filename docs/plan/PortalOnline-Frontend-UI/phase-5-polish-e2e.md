# Phase 5: Polish & E2E Tests

**Goal**: Add loading states, error handling, responsive design, empty states to all pages. Set up Playwright E2E tests.

**Dependencies**: Phases 2 through 4 must be complete. All pages and modals implemented.

**Estimated Effort**: 1-2 days.

---

## Task 5.1: Global Loading & Error UX

### 5.1.1: Toast Notification System

**File**: `frontend/src/composables/useToast.ts`

Lightweight toast system (no library needed).

```typescript
import { ref } from 'vue'

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

const toasts = ref<Toast[]>([])
let nextId = 0

export function useToast() {
  function add(message: string, type: Toast['type'] = 'info', duration = 4000) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => remove(id), duration)
  }

  function remove(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, add, remove }
}
```

**File**: `frontend/src/components/ui/ToastContainer.vue`

- Fixed position: top-right (top-4 right-4), z-50
- Toast items stack vertically (gap-2)
- Types: success (green), error (red), info (blue), warning (amber)
- Auto-dismiss with progress bar
- Click to dismiss
- Enter/leave transitions (slide in from right)

### 5.1.2: API Error Handler

**File**: `frontend/src/utils/errors.ts`

```typescript
import type { AxiosError } from 'axios'

export function getErrorMessage(err: unknown, fallback = 'An error occurred'): string {
  const axiosErr = err as AxiosError<{ detail?: string }>
  if (axiosErr.response?.data?.detail) {
    return axiosErr.response.data.detail
  }
  if (axiosErr.message === 'Network Error') {
    return 'Connection error. Is the server running?'
  }
  if (axiosErr.response?.status === 403) {
    return 'You do not have permission to perform this action.'
  }
  if (axiosErr.response?.status === 404) {
    return 'Not found.'
  }
  if (axiosErr.response?.status === 409) {
    return 'A job with this keyword is already running or queued.'
  }
  if (axiosErr.response?.status && axiosErr.response.status >= 500) {
    return 'Server error. Please try again later.'
  }
  return fallback
}
```

### 5.1.3: Apply Error Handling to All Pages

**Pattern**: Each page imports `getErrorMessage` and `useToast`. On API error, calls `toast.add(getErrorMessage(err), 'error')`.

Pages to update:
- LoginPage: already has error state
- DashboardPage: add error toast on stats fetch failure
- ScrapePage: add error toast on job submit/cancel failure
- ResultsPage: add error toast on job list/action failure
- UsersPage: add error toast on user CRUD failure

### 5.1.4: Apply Loading States

Ensure every data-fetching component has:

| State | Pattern |
|---|---|
| Initial load | Full-page skeleton or spinner |
| Refetch | Inline loading indicator (subtle, not blocking) |
| Empty | Centered icon + text + optional CTA |
| Error | Inline banner + Retry button |

Components to check:
- DashboardPage: stat cards skeleton + table skeleton
- ScrapePage: form skeleton on resume check
- ResultsPage: table skeleton on fetch
- UsersPage: table skeleton on fetch
- JobDetailModal: leads table skeleton on open
- All modals: skeleton on data load

---

## Task 5.2: Responsive Design

### 5.2.1: Breakpoints

Use Tailwind responsive prefixes:
- `sm` (640px): Small tablets
- `md` (768px): Tablets
- `lg` (1024px): Desktop

### 5.2.2: Responsive Layout

**AppLayout**:
```
Desktop (lg):              Mobile (< md):
+-------+----------+       +-------------------+
|Header             |       | Header + hamburger|
+-------+----------+       +-------------------+
| Side  | Content  |       | Content           |
| bar   |          |       | (full width)      |
|       |          |       |                   |
+-------+----------+       +-------------------+
                            | Sidebar overlay   |
                            | (toggle via burger)|
                            +-------------------+
```

- Sidebar: `hidden md:block` on small screens. Toggle via hamburger menu button in AppHeader (only visible on mobile).
- Mobile sidebar: absolute positioned overlay with backdrop
- Header: stack on mobile (app name top, user info bottom)
- Content: full width on mobile, `md:flex-1` on desktop

### 5.2.3: Responsive Tables

**Strategy**: On mobile (< md), convert to card layout (each row becomes a card with label:value pairs). Use CSS:
```css
@media (max-width: 767px) {
  .responsive-table thead { display: none; }
  .responsive-table tr { display: block; margin-bottom: 1rem; }
  .responsive-table td { display: flex; justify-content: space-between; }
  .responsive-table td::before { content: attr(data-label); font-weight: 600; }
}
```

Tables to make responsive:
- Dashboard RecentJobsTable
- Scrape LiveResultsTable
- Results JobsTable
- Users UsersTable
- JobDetailModal leads table

### 5.2.4: Responsive Modals

On mobile (< md):
- Full screen width, bottom sheet style (rounded top corners)
- Max height 90vh, scrollable content

---

## Task 5.3: Empty States

### 5.3.1: Empty State Component

**File**: `frontend/src/components/ui/EmptyState.vue`

**Props**: `icon: string` (Lucide icon), `title: string`, `description: string`, `actionText?: string`, `actionLink?: string`

Centered layout: icon (w-16 h-16, text-gray-300), title (text-lg font-semibold text-gray-600), description (text-gray-400), optional action button.

### 5.3.2: Empty States Per Page

| Page | Condition | Icon | Title | Action |
|---|---|---|---|---|
| Dashboard | No jobs | `Search` | "No jobs yet" | "Start Scraping" -> /scrape |
| Scrape | Not applicable (form always visible) | — | — | — |
| Results | No jobs match filters | `Filter` | "No matching jobs" | "Clear filters" |
| Users | No users (impossible, admin always exists) | `Users` | "No users" | "Add User" -> opens modal |
| JobDetailModal | Job has no leads | `FileX` | "No leads found" | "Close" |

---

## Task 5.4: Date/Time Formatting

**File**: `frontend/src/utils/datetime.ts`

```typescript
export function formatRelative(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)

  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHr < 24) return `${diffHr}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  return formatAbsolute(dateStr)
}

export function formatAbsolute(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
```

Use `formatRelative` for recent items (created_at, started_at). Use `formatAbsolute` for detail views.

---

## Task 5.5: Status Badge Consistency

**File**: `frontend/src/utils/status.ts`

```typescript
import type { JobStatus } from '@/types'

export function statusVariant(status: JobStatus): 'info' | 'warning' | 'success' | 'danger' | 'neutral' {
  const map: Record<JobStatus, 'info' | 'warning' | 'success' | 'danger' | 'neutral'> = {
    queued: 'info', running: 'warning', completed: 'success',
    failed: 'danger', cancelled: 'neutral',
  }
  return map[status]
}

export function statusLabel(status: JobStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1)
}
```

Ensure ALL pages use these utilities via BaseBadge. No hardcoded variant strings.

---

## Task 5.6: Accessibility

### 5.6.1: Checklist

- [ ] All form inputs have `<label>` elements (or `aria-label`)
- [ ] All buttons have accessible text (not icon-only without `aria-label`)
- [ ] Modal focus trap (Tab/Shift+Tab cycles within modal)
- [ ] Modal opens with focus on first focusable element
- [ ] Modal closes on Escape key
- [ ] Color contrast ratios pass WCAG AA (4.5:1 for normal text)
- [ ] BaseBadge: color alone not the only indicator (text label always present)
- [ ] Toast notifications: `role="alert"` for screen readers
- [ ] Skip-to-content link (first focusable element)
- [ ] All interactive elements keyboard accessible (Enter/Space for buttons)

### 5.6.2: Focus Trap for Modals

In BaseModal, add focus trap behavior:

```typescript
// On mount: save previous focus, focus first input/button in modal
// On Tab: cycle between first and last focusable elements
// On Escape: emit close
// On unmount: restore previous focus
```

---

## Task 5.7: E2E Tests (Playwright)

### 5.7.1: Setup

```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium
```

### 5.7.2: Playwright Config

**File**: `frontend/playwright.config.ts`

```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

### 5.7.3: Test Scenarios

**File**: `frontend/e2e/login.spec.ts`

| Test | Description |
|---|---|
| `shows login form` | Visit `/login`, see username/password inputs and login button |
| `shows error on invalid credentials` | Submit wrong credentials, see error message |
| `redirects to dashboard on success` | Submit valid credentials, URL becomes `/dashboard` |
| `redirects authed user away from login` | Login, visit `/login`, redirected to `/dashboard` |

**File**: `frontend/e2e/dashboard.spec.ts`

| Test | Description |
|---|---|
| `shows stat cards` | Admin sees 3 stat cards with values |
| `shows recent jobs table` | Table visible with job rows or empty state |
| `shows dashboard after login` | Login flow -> dashboard loads |

**File**: `frontend/e2e/scrape.spec.ts`

| Test | Description |
|---|---|
| `shows scrape form` | Visit `/scrape`, see keyword + location inputs |
| `submits job successfully` | Fill keyword, click Start, see progress view |
| `shows cancel button during scraping` | After submit, cancel button visible |
| `shows error for empty keyword` | Submit empty, validation prevents |

**File**: `frontend/e2e/results.spec.ts`

| Test | Description |
|---|---|
| `shows jobs table` | Visit `/results`, see table with rows or empty state |
| `filters by status` | Select "completed", table updates |
| `searches by keyword` | Type keyword, table filters |
| `opens job detail modal` | Click View Details, modal opens with leads |

**File**: `frontend/e2e/users.spec.ts`

| Test | Description |
|---|---|
| `admin sees users page` | Login as admin, `/users` loads |
| `non-admin redirected` | Login as user, `/users` redirects to `/dashboard` |
| `shows users table` | Admin sees users list |
| `opens create user modal` | Click Add User, modal opens |
| `opens view user modal` | Click View, modal shows user details |

**File**: `frontend/e2e/layout.spec.ts`

| Test | Description |
|---|---|
| `sidebar navigation works` | Click each nav link, correct page loads |
| `logout works` | Click Logout, redirected to `/login` |
| `responsive layout` | Resize viewport to 375px, sidebar hidden, hamburger visible |

### 5.7.4: Test Fixtures

Create a test fixture that:
1. Seeds a test admin user + test regular user via API
2. Provides `adminPage` and `userPage` fixtures (pre-authenticated)

**Run**: `npx playwright test`

**Verify**: All E2E tests pass.

---

## Task 5.8: Backend SPA Catch-All

Ensure the FastAPI backend correctly serves `index.html` for all non-API routes (SPA client-side routing).

**File**: `portalonline_gmap_scraper/api/app.py`

After all API routes and static mounts:

```python
from fastapi.responses import FileResponse

@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Serve index.html for SPA client-side routing."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"detail": "Frontend not built. Run: cd frontend && npm run build"}
```

This must be registered AFTER all API routes so `/api/v1/*` takes priority.

---

## Task 5.9: Build & Deploy Script

**File**: `scripts/build-frontend.sh`

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/../frontend"
npm ci
npm run build
echo "Frontend built to ../portalonline_gmap_scraper/static/"
```

Make executable: `chmod +x scripts/build-frontend.sh`

---

## Verification Checklist

- [ ] Toasts appear on success/error actions across all pages
- [ ] Error messages are user-friendly (no raw Axios errors)
- [ ] All pages have loading skeletons (not blank screens)
- [ ] All pages have empty states with helpful text
- [ ] Responsive layout works at 375px, 768px, 1024px widths
- [ ] Mobile sidebar toggle (hamburger menu) works
- [ ] Mobile tables render as cards
- [ ] Modals are full-screen on mobile
- [ ] Relative timestamps display correctly ("2h ago", "just now")
- [ ] Status badges use consistent colors across all pages
- [ ] Keyboard navigation: Tab through all interactive elements
- [ ] Escape closes all modals
- [ ] Focus trapped inside open modals
- [ ] Skip-to-content link visible on first Tab
- [ ] All E2E tests pass: `npx playwright test`
- [ ] SPA fallback works: `/dashboard` serves index.html (not 404)
- [ ] `scripts/build-frontend.sh` produces output in static/
