# Phase 3: Core Pages (Dashboard, Scrape, Results)

**Goal**: Implement the three main authenticated pages: Dashboard with stats, Scrape with SSE live progress, Results with filters and actions.

**Dependencies**: Phase 2 (Frontend Setup) must be complete. Login page, AppLayout, base UI components, stores, and services must be available.

**Estimated Effort**: 3-4 days.

---

## Pre-Flight: Backend Gap

### User-Scoped Dashboard Stats

`GET /api/v1/admin/stats` is admin-only (Phase 1). Regular users need their own dashboard stats. **Add this endpoint in Phase 1 follow-up** (or as the first task of Phase 3):

**New endpoint**: `GET /api/v1/users/me/stats`

```json
{
  "total_jobs": 15,
  "total_leads": 340,
  "active_jobs": 1,
  "queued_jobs": 2,
  "recent_jobs": [...]
}
```

**Alternative** (no backend change): Frontend composes user stats from existing endpoints:
- `GET /api/v1/jobs?limit=10` -> recent_jobs
- `GET /api/v1/results/stats` -> total_leads
- Count manually: `total_jobs` from jobs response, `active_jobs` from filter, `queued_jobs` from filter

**Decision**: Use the composition approach first (no backend change needed). If too slow, add a dedicated `/users/me/stats` endpoint later.

### SSE Token Auth

Phase 2 Task 2.11 covers this. Ensure `GET /api/v1/jobs/{id}/stream?token=<jwt>` works before building the live progress UI.

---

## Task 3.1: Dashboard Page

**File**: `frontend/src/pages/DashboardPage.vue`

**Route**: `/dashboard`

### 3.1.1: Data Fetching

Admin vs user stats composition:

```typescript
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getStats } from '@/services/auth'
import { listJobs } from '@/services/jobs'
import type { DashboardStats } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const error = ref<string | null>(null)
const stats = ref<DashboardStats | null>(null)

onMounted(async () => {
  try {
    if (auth.isAdmin) {
      stats.value = await getStats()
    } else {
      const [jobsPage] = await Promise.all([listJobs({ limit: 10 })])
      stats.value = {
        total_users: 0,
        total_jobs: jobsPage.total,
        total_leads: 0,
        active_jobs: jobsPage.jobs.filter(j => j.status === 'running').length,
        queued_jobs: jobsPage.jobs.filter(j => j.status === 'queued').length,
        recent_jobs: jobsPage.jobs.slice(0, 10).map(j => ({
          job_id: j.job_id, keyword: j.keyword, location: j.location,
          status: j.status, leads_collected: j.leads_collected,
          leads_total: j.leads_total, created_at: j.created_at,
        })),
      }
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
})
```

### 3.1.2: Layout

Three stat cards in a row (grid-cols-3 gap-4), then Recent Jobs table below.

### 3.1.3: StatCard Component

**File**: `frontend/src/components/dashboard/StatCard.vue`

**Props**: `icon: string`, `label: string`, `value: string | number`, `loading: boolean`

Card with icon (left, w-10 h-10, rounded-lg, bg-primary/10), value (text-2xl font-bold), label (text-sm text-gray-500). Loading: skeleton pulse. Hidden when value is 0 and label is "Total Users" for non-admin.

**Icons by card**:
| Card | Lucide Icon |
|---|---|
| Total Users | `Users` |
| Total Jobs | `Briefcase` |
| Total Leads | `Database` |

### 3.1.4: RecentJobsTable Component

**File**: `frontend/src/components/dashboard/RecentJobsTable.vue`

**Props**: `jobs: RecentJob[]`, `loading: boolean`

Uses BaseTable. Columns: Job ID (mono, 8 chars), Keyword, Status (BaseBadge), Leads (collected/total), Created (relative: "2h ago" or absolute). Click row -> `router.push('/results?keyword=' + job.keyword)`.

### 3.1.5: Page States

| State | Behavior |
|---|---|
| **Loading** | 3 skeleton stat cards + 5 skeleton table rows |
| **Empty** | Stats show 0. Table: "No jobs yet. Start from the Scrape page." with link to `/scrape` |
| **Error** | Inline error banner + Retry button |
| **Data** | Stat cards + recent jobs table |

**Verify**: Admin sees Total Users card, non-admin does not. Stats correct. Table shows last 10. Loading/empty/error states render. Click row navigates to Results.

---

## Task 3.2: Scrape Page

**File**: `frontend/src/pages/ScrapePage.vue`

**Route**: `/scrape`

### 3.2.1: ScrapeForm Component

**File**: `frontend/src/components/scrape/ScrapeForm.vue`

**Props**: `disabled: boolean`
**Emits**: `submit(keyword: string, location: string)`

Form with:
- Keyword input (required, max 200, autofocus)
- Location input (optional, max 100)
- Submit button (primary, disabled when `disabled` prop true)
- Enter submits
- Disabled state: "A job is already running" message

### 3.2.2: ProgressBar Component

**File**: `frontend/src/components/scrape/ProgressBar.vue`

**Props**: `collected: number`, `total: number`, `status: JobStatus`, `keyword: string`, `location: string`

Bar (h-3, bg-gray-200, rounded-full) with fill animation (bg-primary running, bg-success completed, bg-danger failed). Percentage text. Status text contextual:

| Status | Text |
|---|---|
| queued | "Waiting in queue..." |
| running | "Scraping: {keyword} in {location}..." |
| completed | "Completed! {collected} leads found." |
| failed | "Failed: check job details" |
| cancelled | "Cancelled" |

### 3.2.3: LiveResultsTable Component

**File**: `frontend/src/components/scrape/LiveResultsTable.vue`

**Props**: `leads: LeadResponse[]`

Columns: #, Name, Address, Phone, Website. New leads prepend to top with fade-in transition. Empty state: "Waiting for results..." (gray centered text).

### 3.2.4: SSE Composable

**File**: `frontend/src/composables/useJobStream.ts`

```typescript
import { ref, onUnmounted } from 'vue'
import type { SSEProgress, LeadResponse, JobStatus } from '@/types'
import { getJobStreamUrl } from '@/services/jobs'

export function useJobStream() {
  const leads = ref<LeadResponse[]>([])
  const collected = ref(0)
  const total = ref(0)
  const status = ref<JobStatus>('queued')
  const connected = ref(false)
  const error = ref<string | null>(null)
  let eventSource: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0

  function connect(jobId: string) {
    close()
    const url = getJobStreamUrl(jobId)
    eventSource = new EventSource(url)
    eventSource.onopen = () => { connected.value = true; reconnectAttempts = 0 }
    eventSource.onmessage = (event) => {
      const data: SSEProgress = JSON.parse(event.data)
      switch (data.event) {
        case 'progress':
          if (data.leads_collected != null) collected.value = data.leads_collected
          if (data.total_leads != null) total.value = data.total_leads
          if (data.lead) leads.value.unshift(data.lead)
          break
        case 'status_change':
          if (data.new) status.value = data.new
          break
        case 'completed':
          if (data.status) status.value = data.status
          close()
          break
      }
    }
    eventSource.onerror = () => {
      connected.value = false
      close()
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 16000)
      reconnectAttempts++
      reconnectTimer = setTimeout(() => connect(jobId), delay)
    }
  }

  function close() {
    eventSource?.close()
    eventSource = null
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  }

  onUnmounted(close)

  return { leads, collected, total, status, connected, error, connect, close }
}
```

### 3.2.5: ScrapePage State Machine

```
IDLE -> SUBMITTING -> SCRAPING -> DONE
  ^        |             |          |
  |    409 DUPLICATE ----|          |
  |        |             |          |
  +---error+        cancel -> CANCELLED
```

**On mount**: Check for active jobs from current user (`GET /api/v1/jobs?status=running&status=queued`). If found, resume SSE.

**Verify**:
- Form submits job successfully
- SSE connection starts, progress bar updates
- Live leads table fills in real-time
- Cancel button stops job and SSE
- Duplicate job (409) shows existing job progress
- Page refresh resumes SSE for active job
- Loading/error/empty states handled

---

## Task 3.3: Results Page

**File**: `frontend/src/pages/ResultsPage.vue`

**Route**: `/results`

### 3.3.1: ResultFilters Component

**File**: `frontend/src/components/results/ResultFilters.vue`

**Emits**: `filter(filters)`

| Filter | Component | Notes |
|---|---|---|
| Search | Text input, debounced 300ms | LIKE match on keyword |
| User | Select dropdown | Admin only. Fetches from GET /api/v1/users |
| Status | Select dropdown | all, queued, running, completed, failed, cancelled |

URL query sync: filters stored in `route.query` for shareable URLs.

### 3.3.2: JobsTable Component

**File**: `frontend/src/components/results/JobsTable.vue`

Uses BaseTable. Columns: Job ID (mono, truncated, copy button), User (admin only), Keyword, Location, Status (BaseBadge), Leads (collected/total), Created (relative time), Actions.

### 3.3.3: Actions Column

| Job Status | Actions |
|---|---|
| queued / running | View Process (-> `/scrape?job_id=X`), Cancel |
| completed | View Details, Export CSV, Delete |
| failed | View Details, Delete |
| cancelled | View Details, Delete |

- **View Process**: `router.push('/scrape?job_id=X')`
- **Cancel**: Confirm dialog -> `cancelJob(id)` -> refresh
- **View Details**: Open JobDetailModal
- **Export CSV**: `window.open('/api/v1/jobs/{id}/results?format=csv')`
- **Delete**: Confirm dialog -> `DELETE /api/v1/jobs/{id}` -> refresh

### 3.3.4: JobDetailModal Component

**File**: `frontend/src/components/results/JobDetailModal.vue`

Fetches leads on open via `getJobResults(job_id)`. Shows:
- Job metadata header (keyword, location, status badge, lead counts, timestamps)
- Leads table (Name, Address, Phone, Website, Rating + review count)
- Footer: Export CSV, Delete Job, Close

States: Loading (skeleton), Empty ("No leads found"), Error ("Failed to load" + Retry), Data (full table).

### 3.3.5: Pagination

Bottom of page: Previous/Next buttons + "Page X of Y" text. 20 per page.

**Verify**:
- Filters work: search, status, user (admin)
- URL query params sync with filters
- Jobs table columns correct
- Actions context-sensitive
- JobDetailModal shows leads
- Export CSV downloads file
- Cancel/Delete with confirmation dialogs
- Pagination works with correct page counts
- Loading/empty/error states render
