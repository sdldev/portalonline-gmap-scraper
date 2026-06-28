# PRD: Backend REST API for PortalOnline GMap Scraper

## Problem Statement

Saat ini PortalOnline GMap Scraper hanya bisa dijalankan via CLI (`python -m portalonline_gmap_scraper.main`). Keterbatasan ini:

- **Tidak ada remote control**: User harus SSH ke VPS untuk menjalankan scraping.
- **Tidak ada monitoring real-time**: Tidak bisa melihat progress scraping dari jarak jauh.
- **Tidak ada manajemen job**: Tidak bisa menjadwalkan, membatalkan, atau melihat history scraping.
- **Tidak ada akses terstruktur ke hasil**: Hasil hanya file CSV di filesystem, tidak bisa di-query, di-filter, atau di-join dengan data lain.
- **Tidak ada persistence yang reliable**: File CSV mudah ter-overwrite, tidak ada indexing, tidak bisa query by keyword/date.
- **Tidak bisa diintegrasikan**: Aplikasi lain (dashboard, bot Telegram, dll) tidak bisa memicu scraping secara programatik.

Dengan menambahkan HTTP API backend di port 9988 dengan SQLite sebagai penyimpanan hasil, scraper menjadi layanan yang bisa dikontrol, dimonitor, dan diintegrasikan dari mana saja. Semua hasil scraping tersimpan secara permanen di database dan bisa di-query secara fleksibel.

## Goals and Success Metrics

**Primary Goal**: Menyediakan HTTP API yang meng-expose semua kemampuan scraper sebagai layanan async yang bisa dikontrol dan dimonitor secara real-time.

**Success Metrics**:
- API response time < 200ms untuk semua endpoint non-scraping
- Bisa menjalankan scraping job secara concurrent tanpa crash
- WebSocket/SSE progress update dengan latency < 2 detik
- Zero data loss: semua hasil scraping tersimpan permanen di SQLite dan bisa diakses kembali
- Query hasil scraping by keyword, date range, atau lokasi dalam < 100ms
- Lint & test pass rate: 100% (ruff + pytest)

## User Stories

### Must Have
1. **Sebagai user**, saya ingin memulai scraping job via HTTP POST agar bisa menjalankan scraper dari dashboard/bot tanpa SSH.
2. **Sebagai user**, saya ingin melihat status job saya sendiri (pending/queued/running/completed/failed) secara real-time agar tahu progress scraping dan posisi antrian.
3. **Sebagai user**, saya ingin membatalkan job saya sendiri yang sedang queued atau running agar bisa menghentikan scraping yang bermasalah.
4. **Sebagai user**, saya ingin mengambil hasil scraping milik saya dalam format JSON/CSV via HTTP agar bisa diolah oleh aplikasi lain.
5. **Sebagai user**, saya ingin melihat daftar job saya sendiri (history) agar bisa track aktivitas scraping sebelumnya.
6. **Sebagai admin**, saya ingin melihat semua job dari semua user agar bisa monitor aktivitas sistem secara keseluruhan.
7. **Sebagai admin**, saya ingin membatalkan job dari user manapun dan mengelola queue (reorder, remove) agar bisa menjaga stabilitas sistem.
8. **Sebagai admin**, saya ingin mengelola user accounts (create, disable, assign role) agar bisa mengontrol siapa yang bisa mengakses API.

### Should Have
6. **Sebagai operator**, saya ingin menerima progress update real-time (leads collected, URLs processed) via SSE/WebSocket agar bisa monitor scraping tanpa polling.
7. **Sebagai operator**, saya ingin melihat dan mengubah konfigurasi scraper via API agar tidak perlu edit .env manual.
8. **Sebagai operator**, saya ingin melihat health status sistem (RAM, CPU, active jobs) agar bisa monitor resource VPS.
9. **Sebagai operator**, saya ingin mencari dan filter hasil scraping berdasarkan keyword, lokasi, atau keberadaan phone/website agar bisa menemukan lead yang relevan dengan cepat.

### Nice to Have
10. **Sebagai operator**, saya ingin menjadwalkan scraping berulang (cron-like) agar scraping otomatis berjalan berkala.
11. **Sebagai operator**, saya ingin export hasil ke Google Sheets/CSV download agar mudah dibagikan ke tim.
12. **Sebagai operator**, saya ingin memiliki UI form input keyword (frontend) yang memanggil API backend agar tidak perlu mengingat parameter API.

## Requirements

### Functional Requirements

#### FR-0: Users & Roles

Sistem memiliki dua role: **admin** dan **user**. Setiap request harus terautentikasi dengan API key yang terikat ke user.

**Role Definitions**:

| Permission | admin | user |
|---|---|---|
| Submit job | Ya | Ya (ke queue) |
| View own jobs | Ya | Ya |
| View all jobs | Ya | Tidak |
| Cancel own job | Ya | Ya (hanya queued/running) |
| Cancel any job | Ya | Tidak |
| View own results | Ya | Ya |
| View all results | Ya | Tidak |
| Manage queue (reorder/remove) | Ya | Tidak |
| Manage users (CRUD) | Ya | Tidak |
| View/update system config | Ya | Tidak |
| View system health | Ya | Ya (terbatas) |

**API Endpoints untuk User Management** (admin only):
- `POST /api/users` -- Buat user baru
  - Body: `{ "username": "operator1", "role": "user", "api_key": "optional-custom-key" }`
  - Response: `{ "user_id": "uuid", "username": "operator1", "role": "user", "api_key": "auto-generated-if-empty" }`
- `GET /api/users` -- List semua user (admin only)
- `GET /api/users/{user_id}` -- Detail user
- `PATCH /api/users/{user_id}` -- Update user (role, status)
  - Body: `{ "role": "admin" }` atau `{ "active": false }` (disable user)
- `DELETE /api/users/{user_id}` -- Hapus user (admin only)
- `GET /api/users/me` -- Lihat profil sendiri (bisa diakses semua role)

**Authentication Flow**:
1. User mendaftar ke admin untuk mendapatkan API key
2. Admin membuat user via `POST /api/users`, sistem generate API key
3. User menggunakan API key di header `X-API-Key` untuk setiap request
4. Server validasi API key, identifikasi user_id dan role
5. Middleware cek permission berdasarkan role sebelum proses request

**Default Admin**: Saat pertama kali server start tanpa ada user di database, otomatis buat admin default dengan API key dari env var `ADMIN_API_KEY`.

#### FR-1: Job Management API (Keyword Input via Parameters + Queue System)

Input keyword scraping dilakukan melalui parameter HTTP. Saat ini via API call, ke depan akan dibuatkan UI form input yang memanggil endpoint yang sama.

**Queue System (Waiting List)**:
Karena Camoufox hanya bisa menjalankan 1 scraping job pada satu waktu, sistem menggunakan FIFO queue:
- Jika tidak ada job yang sedang berjalan: job baru langsung dijalankan (`status: running`)
- Jika ada job yang sedang berjalan: job baru masuk waiting list (`status: queued`) dengan posisi antrian
- Ketika job selesai (completed/failed/cancelled): job pertama di queue otomatis dijalankan
- User bisa melihat posisi antrian job mereka via `GET /api/jobs/{job_id}`
- Admin bisa mengelola queue: reorder prioritas atau hapus dari queue

**Status flow**: `queued` -> `running` -> `completed` / `failed` / `cancelled`

- `POST /api/jobs` -- Buat dan jalankan scraping job baru
  - Body:
    ```json
    {
      "keyword": "restoran",
      "location": "lampung",
      "target": 50,
      "smart": true,
      "category_variations": ["rumah makan", "resto", "warung makan"]
    }
    ```
  - Parameter:
    - `keyword` (required, string) -- Kata kunci utama pencarian (e.g., "restoran", "hotel", "bengkel")
    - `location` (optional, string) -- Lokasi target pencarian (e.g., "lampung", "jakarta selatan")
    - `target` (optional, int, default=25) -- Jumlah lead yang ingin dikumpulkan
    - `smart` (optional, bool, default=true) -- Gunakan smart search dengan keyword variations
    - `category_variations` (optional, string[]) -- Custom keyword variations. Jika tidak diisi, menggunakan default dari `CATEGORY_VARIATIONS` di config.py
  - Response (langsung jalan): `{ "job_id": "uuid", "status": "running", "query": "restoran di lampung", "queue_position": null }`
  - Response (masuk queue): `{ "job_id": "uuid", "status": "queued", "query": "restoran di lampung", "queue_position": 3 }`
  - **Catatan untuk UI mendatang**: Form input akan memiliki field keyword, location, target, dan toggle smart search. Field category_variations bisa diisi manual atau auto-suggested berdasarkan keyword.
- `GET /api/jobs` -- List semua job dengan filter dan pagination
  - Query params: `status`, `page`, `limit`, `keyword` (filter by keyword)
  - **User**: hanya melihat job milik sendiri
  - **Admin**: melihat semua job dari semua user, bisa filter by `user_id`
- `GET /api/jobs/{job_id}` -- Detail job termasuk progress, posisi queue, dan hasil
  - Response termasuk `queue_position` (integer, hanya ada jika status=queued) dan `estimated_wait_minutes`
- `DELETE /api/jobs/{job_id}` -- Batalkan job
  - **User**: hanya bisa batalkan job milik sendiri
  - **Admin**: bisa batalkan job dari user manapun
- `GET /api/jobs/{job_id}/results` -- Ambil hasil scraping (JSON/CSV)
  - Query param: `format=json|csv`
- `GET /api/queue` -- Lihat status queue saat ini (admin: semua, user: hanya posisi sendiri)
  - Response: `{ "active_job": { "job_id": "...", "user": "...", "keyword": "...", "started_at": "..." }, "queue": [ { "job_id": "...", "user": "...", "keyword": "...", "position": 1 }, ... ] }`
- `PATCH /api/queue/{job_id}` -- Reorder queue (admin only)
  - Body: `{ "position": 1 }` (pindahkan ke posisi tertentu)
- `DELETE /api/queue/{job_id}` -- Hapus dari queue (admin only, cancel + remove)

#### FR-2: Real-time Progress (SSE)
- `GET /api/jobs/{job_id}/stream` -- Server-Sent Events stream
  - Events: `progress` (leads collected count), `status_change`, `error`, `completed`
  - Heartbeat setiap 15 detik untuk keep-alive

#### FR-3: Configuration API
- `GET /api/config` -- Lihat konfigurasi saat ini (tanpa secrets)
- `PATCH /api/config` -- Update konfigurasi runtime (berlaku untuk job berikutnya)
  - Body: `{ "batch_size": 10, "cooldown_sec": 5 }`

#### FR-4: System Health
- `GET /api/health` -- Health check endpoint (200 OK / 503)
- `GET /api/system` -- Resource monitoring (RAM, CPU, active jobs, uptime)

#### FR-5: Results Management (SQLite-backed)
Semua hasil scraping tersimpan di SQLite (`data/scraper.db`). Endpoint berikut menyediakan akses terstruktur ke data:

- `GET /api/v1/results` -- List semua hasil scraping dengan filter dan pagination
  - Query params: `keyword`, `job_id`, `phone_not_null` (bool), `rating_min` (float), `review_count_min` (int), `page`, `limit`
  - Default pagination: `page=1`, `limit=50`, max `limit=500`
  - Response: `{ "results": [...], "total": 150, "page": 1, "limit": 50 }`
- `GET /api/v1/results/{result_id}` -- Detail satu lead berdasarkan ID
- `GET /api/v1/results/stats` -- Statistik agregat
  - Response: `{ "total_leads": 500, "unique_keywords": 12, "leads_with_phone": 380, "leads_with_website": 120, "leads_with_rating": 350, "avg_rating": "4.2" }`
- `GET /api/v1/results/export` -- Export hasil ke CSV/JSON
  - Query params: `format=csv|json`, `keyword`, `job_id`
- `GET /api/v1/results/search` -- Full-text search leads
  - Query params: `q` (search term), `fields=name,address,phone`
  - Mencari di kolom name, address, phone (default), bisa ditambah rating/review_count

#### FR-6: Graceful Shutdown & Startup Recovery

Sistem harus aman terhadap restart server (deploy update, VPS reboot, crash).

**Startup Sequence** (saat `server.py` dijalankan):
1. Inisialisasi SQLite: create tables if not exists, set WAL mode
2. Cek/create default admin dari `ADMIN_API_KEY` env var
3. Mark orphan jobs: semua job dengan `status=running` di DB di-set ke `failed` dengan error `"Server restarted"`
4. Restore queue: rebuild in-memory queue dari DB (`status=queued`, ORDER BY `queue_position ASC`)
5. Start Uvicorn server

**Shutdown Handling** (SIGTERM/SIGINT):
1. Stop accepting new requests (return 503)
2. Cancel active scraping job gracefully (set `status=failed`, error `"Server shutting down"`)
3. Tunggu SSE connections close (timeout 5 detik)
4. Close SQLite connection pool
5. Exit

**Implication**: In-memory state (JobManager) harus bisa di-reconstruct dari SQLite. Semua state penting harus persist ke DB sebelum dianggap committed.

#### FR-7: Job Timeout

Setiap job memiliki batas durasi maksimal untuk mencegah queue stuck.

- Config: `MAX_JOB_DURATION_MINUTES` (default: 30)
- Jika job melebihi timeout:
  1. Cancel scraping yang sedang berjalan
  2. Set job `status=failed`, `error="Job timeout after {N} minutes"`
  3. Simpan partial results yang sudah di-scrape ke SQLite
  4. Dequeue job berikutnya
- Timeout dihitung dari `started_at` sampai sekarang
- Dapat dikonfigurasi per-job via parameter `timeout_minutes` di `POST /api/v1/jobs` (max: 120 menit)

#### FR-8: Lead Deduplication Across Jobs

Bisnis yang sama bisa di-scrape dari keyword berbeda (e.g., "restoran lampung" vs "rumah makan lampung"). Sistem harus mencegah duplikat.

**Dedup Strategy**:
- Natural key: `name + address` (normalized, lowercase, tanpa plus code)
- Sama seperti `_dedup_key()` yang sudah ada di `scraper.py`
- Sebelum insert lead baru, cek apakah sudah ada di tabel `leads` dengan `name` dan `address` yang sama
- Jika duplikat: skip insert, log sebagai `debug`
- Tidak perlu UNIQUE constraint (karena normalisasi berbeda dari raw data), gunakan application-level check

**Implication**: `GET /api/v1/results` harus support dedup view (default: hide duplicates) dan raw view (show all, including duplicates from different jobs).

#### FR-9: Disk Space Guard

SQLite dan leads akan terus bertambah. Sistem harus mencegah crash karena disk penuh.

- Monitor disk space di `GET /api/v1/system` endpoint
- Reject job baru jika disk usage > 90% dengan error `DISK_SPACE_LOW`
- Warning di health endpoint jika disk usage > 80%
- Config: `DISK_USAGE_WARN_PERCENT` (default: 80), `DISK_USAGE_LIMIT_PERCENT` (default: 90)

#### FR-10: Cleanup & Data Retention Policy

Data lama harus di-cleanup secara otomatis untuk mencegah pembengkakan database.

- Config: `DATA_RETENTION_DAYS` (default: 90)
- Auto-cleanup: scheduled task setiap hari jam 03:00, hapus:
  - Jobs yang `completed_at` lebih tua dari retention period
  - Leads yang `scraped_at` lebih tua dari retention period (CASCADE dari job delete)
- Manual cleanup: `POST /api/v1/admin/cleanup` (admin only)
  - Body: `{ "older_than_days": 30 }` (optional, default: gunakan config)
  - Response: `{ "deleted_jobs": 45, "deleted_leads": 1200, "db_size_before_mb": 150, "db_size_after_mb": 80 }`
- Auto VACUUM: setelah cleanup, jalankan `PRAGMA incremental_vacuum` untuk reclaim space
- `GET /api/v1/admin/db-stats` (admin only): database size, table row counts, last vacuum time

#### FR-11: Duplicate Job Detection

User tidak boleh submit job yang sama berulang-ulang.

- Saat `POST /api/v1/jobs`, cek apakah user sudah punya job dengan `keyword + location` yang sama dan status `queued` atau `running`
- Jika ya: reject dengan error code `DUPLICATE_JOB`
- Error response:
  ```json
  {
    "success": false,
    "error": {
      "code": "DUPLICATE_JOB",
      "message": "You already have an active or queued job for 'restoran' in 'lampung'.",
      "existing_job_id": "uuid-of-existing-job"
    }
  }
  ```
- Tidak berlaku untuk admin (admin boleh submit duplikat)

#### FR-12: Audit Logging

Setiap aksi signifikan harus tercatat untuk debugging dan security audit.

**Tabel `audit_logs`**:
```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES users(user_id),
    action      TEXT NOT NULL,          -- create_job, cancel_job, update_config, create_user, delete_user, etc.
    target_type TEXT,                   -- job, user, config, queue
    target_id   TEXT,                   -- ID dari target (job_id, user_id, dll)
    details     TEXT,                   -- JSON: detail perubahan
    ip_address  TEXT,
    created_at  TEXT NOT NULL           -- ISO 8601
);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);
```

**Actions yang di-log**:
- `create_job`, `cancel_job`, `complete_job`, `fail_job`
- `create_user`, `update_user`, `delete_user`
- `update_config`
- `queue_reorder`, `queue_remove`
- `cleanup`

**Admin endpoint**:
- `GET /api/v1/admin/audit-logs` -- List audit logs dengan filter
  - Query params: `user_id`, `action`, `target_type`, `from_date`, `to_date`, `page`, `limit`

#### FR-13: Webhook Notification on Job Complete

User bisa menerima notifikasi otomatis saat job selesai.

- `POST /api/v1/users/me/webhook` -- Set webhook URL
  - Body: `{ "url": "https://example.com/webhook", "events": ["job.completed", "job.failed"] }`
- `GET /api/v1/users/me/webhook` -- Lihat webhook config
- `DELETE /api/v1/users/me/webhook` -- Hapus webhook

**Webhook Payload** (POST ke URL user):
```json
{
  "event": "job.completed",
  "timestamp": "2026-06-28T10:30:00Z",
  "job_id": "uuid",
  "keyword": "restoran",
  "location": "lampung",
  "leads_collected": 42,
  "status": "completed"
}
```

**Delivery**:
- Retry 3x dengan exponential backoff (1s, 5s, 30s)
- Timeout 10 detik per attempt
- Log delivery status ke audit_logs
- Jika semua retry gagal: log warning, tidak block job completion

#### FR-14: Input Sanitization

Semua input dari user harus di-sanitasi sebelum disimpan atau digunakan.

| Field | Rules | Max Length | Blocked Characters |
|---|---|---|---|
| `keyword` | alphanumeric + spasi + dash | 200 | `<`, `>`, `"`, `'`, `;`, `--`, `/*` |
| `location` | alphanumeric + spasi + koma + titik | 100 | sama seperti keyword |
| `username` | alphanumeric + underscore only | 50 | semua selain `a-z0-9_` |
| `api_key` | alphanumeric + dash | 64 | semua selain `a-z0-9-` |
| `category_variations[]` | alphanumeric + spasi | 100 per item, max 10 items | sama seperti keyword |

- Pydantic `pattern` validation untuk username dan api_key
- Custom validator untuk keyword dan location (strip blocked characters)
- Semua string di-trim whitespace sebelum simpan

### Non-Functional Requirements

- **NFR-1: Performance** -- API harus lightweight, tidak boleh lebih dari 50MB RAM idle. Menggunakan framework async (FastAPI + uvicorn).
- **NFR-2: Concurrency** -- Hanya boleh 1 scraping job berjalan pada satu waktu (Camoufox limitation). Job lain masuk waiting list (FIFO queue) dengan status `queued` dan posisi antrian yang transparan. SQLite menggunakan WAL mode sehingga read tidak blocking write.
- **NFR-3: Reliability** -- Job yang crash harus dicatat sebagai `failed` dengan error message, tidak menghang server. Hasil partial (leads yang sudah di-scrape sebelum crash) tetap tersimpan di SQLite. Server restart tidak kehilangan queue state (reconstruct dari DB).
- **NFR-4: Security** -- User authentication via `X-API-Key` header yang terikat ke user_id dan role. Role-based access control (RBAC): admin punya akses penuh, user hanya akses milik sendiri. Rate limiting: 60 req/menit per user (admin exempt). Input sanitization untuk semua user input. CORS whitelist untuk production.
- **NFR-5: VPS Friendly** -- Total footprint (server + browser) harus di bawah 2GB RAM. SQLite database file harus di-compact secara berkala (VACUUM) untuk mencegah pembengkakan file. Disk space monitoring dan auto-cleanup data lama.
- **NFR-6: Observability** -- Structured logging (JSON) untuk semua request dan job lifecycle. Audit trail untuk semua aksi signifikan (create/cancel job, user management, config changes). Log rotation untuk mencegah log file membesar.
- **NFR-7: Availability** -- Server harus bisa dijalankan sebagai systemd service dengan auto-restart. Graceful shutdown: cancel active job, close connections, exit bersih. Startup recovery: restore queue, mark orphan jobs.

## Technical Considerations

### Architecture & Dependencies

```
                          +------------------+
                          |   Uvicorn        |
                          |   (port 9988)    |
                          +--------+---------+
                                   |
                          +--------v---------+
                          |   FastAPI App    |
                          |   - Routes       |
                          |   - Auth (RBAC)  |
                          |   - SSE handler  |
                          +--------+---------+
                                   |
                 +-----------------+-----------------+
                 |                                    |
        +--------v---------+              +-----------v-----------+
        |  Job Manager     |              |  SQLite Store         |
        |  (in-memory      |              |  data/scraper.db      |
        |   queue + asyncio)              |  - users table        |
        |  - FIFO queue    |              |  - jobs table         |
        |  - waiting list   |              |  - leads table        |
        +--------+---------+              |  - WAL mode           |
                 |                        +-----------+-----------+
                 |                                    |
                 |              +---------------------+
                 |              |
        +--------v---------+   |  (write leads after
        |  Scraper Engine  |   |   each batch completes)
        |  (existing        |<-+
        |   scraper.py)     |
        +------------------+
```

**Dependencies baru** (ditambahkan ke `pyproject.toml`):

```toml
dependencies = [
    # ... existing deps ...
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.0.0",
    "aiosqlite>=0.20.0",    # async wrapper untuk sqlite3 (built-in Python)
    "httpx>=0.27.0",         # async HTTP client untuk webhook delivery
]
```

**Environment Variables baru** (ditambahkan ke `.env`):

```env
# API Server
API_HOST=0.0.0.0
API_PORT=9988
ADMIN_API_KEY=your-admin-secret-key-here
CORS_ORIGINS=*                    # Comma-separated origins, * untuk dev

# Job Settings
MAX_JOB_DURATION_MINUTES=30       # Timeout per scraping job
DATA_RETENTION_DAYS=90            # Auto-cleanup data lebih tua dari ini
DISK_USAGE_WARN_PERCENT=80        # Warning threshold
DISK_USAGE_LIMIT_PERCENT=90       # Reject job baru jika disk di atas ini

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60          # Max request per user per menit
```

**Framework choice**: FastAPI karena:
- Native async support (cocok dengan scraper yang sudah async)
- Built-in SSE support
- Auto-generated OpenAPI docs (`/docs`)
- Pydantic validation
- Lightweight footprint

### Data Model

```python
# models.py

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z0-9_]+$")
    role: UserRole = Field(default=UserRole.USER)
    api_key: str | None = Field(default=None, description="Custom API key. Auto-generated if empty.")

class UserResponse(BaseModel):
    user_id: str
    username: str
    role: UserRole
    active: bool = True
    created_at: datetime

class UserUpdate(BaseModel):
    role: UserRole | None = None
    active: bool | None = None

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200, description="Kata kunci utama pencarian")
    location: str | None = Field(default=None, max_length=100, description="Lokasi target")
    target: int = Field(default=25, ge=0, le=500)
    smart: bool = Field(default=True)
    category_variations: list[str] | None = Field(default=None, description="Custom keyword variations")
    batch_size: int | None = Field(default=None, ge=1, le=50)
    cooldown_sec: float | None = Field(default=None, ge=0)

class JobResponse(BaseModel):
    job_id: str
    user_id: str               # Pemilik job
    query: str                 # Derived: "{keyword} di {location}" or "{keyword}"
    keyword: str
    location: str | None
    status: JobStatus
    target: int
    smart: bool
    queue_position: int | None = None  # Posisi di queue (hanya jika status=queued)
    estimated_wait_minutes: float | None = None  # Estimasi waktu tunggu
    leads_collected: int = 0
    leads_total: int = 0
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

class JobProgress(BaseModel):
    job_id: str
    status: JobStatus
    leads_collected: int
    leads_total: int
    current_query: str | None = None
    phase: str = "collecting"  # collecting | processing | done

class LeadResult(BaseModel):
    id: int | None = None
    job_id: str
    keyword: str
    name: str
    address: str
    phone: str
    website: str
    rating: str = "N/A"         # Star rating (e.g., "4.5") or "N/A"
    review_count: str = "N/A"   # Number of reviews (e.g., "123") or "N/A"
    scraped_at: datetime | None = None

class QueueStatus(BaseModel):
    active_job: JobResponse | None = None
    queue: list[JobResponse] = []
    total_queued: int = 0

class QueueReorder(BaseModel):
    position: int = Field(..., ge=1, description="Posisi baru dalam queue (1 = next)")

class SystemHealth(BaseModel):
    status: str  # healthy | degraded | unhealthy
    uptime_seconds: float
    active_jobs: int
    queued_jobs: int
    ram_available_mb: int
    cpu_percent: float

class ConfigUpdate(BaseModel):
    batch_size: int | None = None
    cooldown_sec: float | None = None
    mem_limit_mb: int | None = None
    cpu_limit_percent: int | None = None
    max_retries: int | None = None
    headless: bool | None = None

class AuditLog(BaseModel):
    id: int | None = None
    user_id: str
    action: str             # create_job, cancel_job, update_config, dll
    target_type: str | None = None  # job, user, config, queue
    target_id: str | None = None
    details: str | None = None  # JSON string
    ip_address: str | None = None
    created_at: datetime

class WebhookConfig(BaseModel):
    url: str = Field(..., max_length=500)
    events: list[str] = Field(default=["job.completed", "job.failed"])

class WebhookPayload(BaseModel):
    event: str
    timestamp: datetime
    job_id: str
    keyword: str
    location: str | None
    leads_collected: int
    status: str

class CleanupRequest(BaseModel):
    older_than_days: int | None = Field(default=None, ge=1, le=365)

class CleanupResponse(BaseModel):
    deleted_jobs: int
    deleted_leads: int
    deleted_audit_logs: int
    db_size_before_mb: float
    db_size_after_mb: float

class DbStats(BaseModel):
    db_size_mb: float
    jobs_count: int
    leads_count: int
    users_count: int
    audit_logs_count: int
    last_vacuum_at: datetime | None = None
```

### SQLite Database Schema

Semua hasil scraping, metadata job, dan user accounts disimpan di SQLite (`data/scraper.db`). SQLite dipilih karena zero-config, file-based, dan mendukung WAL mode untuk concurrent read.

```sql
-- Tabel users: menyimpan user accounts dan API keys
CREATE TABLE IF NOT EXISTS users (
    user_id      TEXT PRIMARY KEY,
    username     TEXT NOT NULL UNIQUE,
    role         TEXT NOT NULL DEFAULT 'user',  -- admin|user
    api_key      TEXT NOT NULL UNIQUE,          -- API key untuk autentikasi
    active       INTEGER NOT NULL DEFAULT 1,    -- 0=disabled, 1=active
    webhook_url  TEXT,                          -- Webhook URL untuk notifikasi (nullable)
    webhook_events TEXT DEFAULT '["job.completed","job.failed"]',  -- JSON array of event names
    created_at   TEXT NOT NULL                   -- ISO 8601
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Tabel jobs: menyimpan metadata setiap scraping job
CREATE TABLE IF NOT EXISTS jobs (
    job_id       TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(user_id),  -- Pemilik job
    keyword      TEXT NOT NULL,           -- keyword asli dari input
    location     TEXT,                    -- lokasi target (nullable)
    query        TEXT NOT NULL,           -- query final: "keyword di location" atau "keyword"
    status       TEXT NOT NULL DEFAULT 'queued',  -- queued|running|completed|failed|cancelled
    target       INTEGER NOT NULL DEFAULT 25,
    smart        INTEGER NOT NULL DEFAULT 1,      -- 0=false, 1=true
    queue_position INTEGER,               -- Posisi dalam queue (nullable, hanya untuk queued)
    leads_collected INTEGER NOT NULL DEFAULT 0,
    leads_total  INTEGER NOT NULL DEFAULT 0,
    error        TEXT,                    -- error message jika failed
    created_at   TEXT NOT NULL,           -- ISO 8601
    started_at   TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_keyword ON jobs(keyword);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_queue_position ON jobs(queue_position) WHERE status = 'queued';

-- Tabel leads: menyimpan setiap hasil scraping
CREATE TABLE IF NOT EXISTS leads (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id       TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    user_id      TEXT NOT NULL REFERENCES users(user_id),  -- Pemilik lead (denormalized untuk query cepat)
    keyword      TEXT NOT NULL,           -- keyword yang menghasilkan lead ini
    name         TEXT NOT NULL,
    address      TEXT NOT NULL DEFAULT '',
    phone        TEXT NOT NULL DEFAULT 'N/A',
    website      TEXT NOT NULL DEFAULT 'N/A',
    rating       TEXT NOT NULL DEFAULT 'N/A',  -- Star rating (e.g., "4.5") or "N/A"
    review_count TEXT NOT NULL DEFAULT 'N/A',  -- Number of reviews (e.g., "123") or "N/A"
    scraped_at   TEXT NOT NULL            -- ISO 8601
);

CREATE INDEX IF NOT EXISTS idx_leads_job_id ON leads(job_id);
CREATE INDEX IF NOT EXISTS idx_leads_user_id ON leads(user_id);
CREATE INDEX IF NOT EXISTS idx_leads_keyword ON leads(keyword);
CREATE INDEX IF NOT EXISTS idx_leads_name ON leads(name);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_rating ON leads(rating);
CREATE INDEX IF NOT EXISTS idx_leads_review_count ON leads(review_count);
```

**Queue & Waiting List Logic**:
- Saat submit job: cek apakah ada job dengan status `running`
  - Jika tidak ada: set job `status = running`, langsung jalankan scraper
  - Jika ada: set job `status = queued`, hitung `queue_position` (MAX(queue_position) + 1)
- Saat job selesai: ambil job pertama dari queue (ORDER BY queue_position ASC), set `status = running`, reindex posisi sisanya
- Saat cancel job yang sedang `queued`: reindex posisi job lain di queue
- Saat cancel job yang sedang `running`: langsung dequeue job berikutnya (jika ada)

**Keuntungan SQLite vs CSV**:
- Query fleksibel: `SELECT * FROM leads WHERE keyword='hotel' AND phone != 'N/A'`
- Indexing: pencarian by keyword, nama, phone, rating dalam milidetik
- Relasi: leads terikat ke job_id, bisa trace asal setiap lead
- Dedup: mudah cek duplikat sebelum insert (`UNIQUE` constraint atau query)
- Concurrent read: WAL mode membolehkan banyak reader bersamaan
- Zero config: tidak perlu server database terpisah
- Filter by rating: `SELECT * FROM leads WHERE rating != 'N/A' AND CAST(rating AS REAL) >= 4.0`

### API Route Structure

```
portalonline_gmap_scraper/
    api/
        __init__.py
        app.py            # FastAPI app factory (CORS, lifespan)
        routes/
            __init__.py
            auth.py         # /api/v1/auth endpoints
            users.py        # /api/v1/users endpoints
            jobs.py         # /api/v1/jobs endpoints
            queue.py        # /api/v1/queue endpoints
            results.py      # /api/v1/results endpoints
            config.py       # /api/v1/config endpoint
            health.py       # /api/v1/health, /api/v1/system
            admin.py        # /api/v1/admin/* endpoints
        middleware/
            __init__.py
            auth.py         # API key + RBAC middleware
            rate_limit.py   # Per-user rate limiter
            sanitize.py     # Input sanitization validators
        models.py           # Pydantic models
        job_manager.py      # Job queue, lifecycle, timeout, graceful shutdown
        store.py            # SQLite persistence (users, jobs, leads, audit_logs)
        sse.py              # SSE streaming helper
        webhook.py          # Webhook delivery service
        cleanup.py          # Data retention & cleanup scheduler
    server.py               # Uvicorn entry point (port 9988, startup recovery)
    deploy/
        portalonline-scraper.service  # systemd service file
```

### Job Manager Architecture

```python
# job_manager.py (sketch)

class JobManager:
    """Manages scraping job lifecycle with FIFO queue and user context."""

    _active_job: str | None          # Only 1 running job at a time
    _queue: asyncio.Queue[Job]       # FIFO queue for pending jobs (ordered by queue_position)
    _jobs: dict[str, Job]            # All jobs by ID (in-memory cache)
    _progress: dict[str, JobProgress]  # Real-time progress
    _subscribers: dict[str, list]    # SSE subscribers per job
    _lock: asyncio.Lock              # Ensure single active job
    _store: SQLiteStore              # SQLite persistence layer

    async def submit(self, job_create: JobCreate, user_id: str) -> JobResponse:
        """
        Submit new job for a user.
        - If no active job: start immediately (status=running)
        - If job running: add to queue (status=queued, with position)
        """

    async def cancel(self, job_id: str, user_id: str, is_admin: bool) -> bool:
        """
        Cancel a job. User can only cancel own jobs, admin can cancel any.
        - If cancelling queued job: remove from queue, reindex positions
        - If cancelling running job: stop scraper, dequeue next job
        """

    async def get_queue_status(self, user_id: str, is_admin: bool) -> QueueStatus:
        """
        Get current queue status.
        - Admin: sees all queued jobs
        - User: sees own position in queue only
        """

    async def reorder_queue(self, job_id: str, new_position: int) -> bool:
        """Admin only: move job to new position in queue."""

    async def get_progress(self, job_id: str) -> JobProgress:
        """Get current progress for a job."""

    async def subscribe(self, job_id: str) -> AsyncGenerator:
        """SSE generator for real-time updates."""

    async def _dequeue_next(self) -> Job | None:
        """Called when a job finishes. Starts next job in queue if any."""
        # 1. Get job with lowest queue_position where status='queued'
        # 2. Set status='running', clear queue_position, set started_at
        # 3. Reindex remaining queue positions
        # 4. Start scraper for this job

    async def _on_leads_batch(self, job_id: str, leads: list[dict]):
        """Callback: write leads batch to SQLite after each scraping batch."""
        await self._store.insert_leads(job_id, leads)

    async def _on_job_complete(self, job_id: str, status: str):
        """Callback: update job status in SQLite, then dequeue next job."""
        await self._store.update_job_status(job_id, status)
        await self._dequeue_next()
```

**Concurrency model (Queue & Waiting List)**:
- Single active scraping job (Camoufox constraint)
- FIFO queue system: `queued` -> `running` -> `completed/failed`
- Auto-dequeue: ketika job selesai, job pertama di queue otomatis dimulai
- Queue position tracking: setiap job yang masuk queue mendapat posisi (1, 2, 3, ...)
- Queue reindex: saat job di-cancel atau selesai, posisi sisanya di-reindex
- Cancellation: mengirim signal ke scraper untuk stop (via asyncio.Event)
- User isolation: user hanya bisa lihat/batalkan job milik sendiri, admin bisa semua

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Camoufox crash saat scraping, server hang | Medium | High | Wrap scraping di try/except, timeout 10 menit per job, force kill jika hang |
| Memory leak dari multiple jobs | Medium | High | Restart browser antar job, GC collect setelah setiap job selesai |
| SSE connection leak (client disconnect tanpa close) | Medium | Medium | Heartbeat + client timeout detection, cleanup stale connections |
| SQLite lock contention saat concurrent read/write | Low | Medium | Gunakan WAL mode, write hanya saat job selesai |
| Port 9988 conflict dengan service lain | Low | Low | Configurable port via env var `API_PORT` |

## Design and UX Notes

### API Response Format
Semua response mengikuti format konsisten:
```json
{
    "success": true,
    "data": { ... },
    "message": "Job created successfully"
}
```
Error:
```json
{
    "success": false,
    "error": {
        "code": "JOB_QUEUED",
        "message": "Another job is running. Your job has been added to the queue at position 3.",
        "queue_position": 3
    }
}
```

Other error codes:
- `UNAUTHORIZED` -- API key tidak valid atau tidak ditemukan
- `FORBIDDEN` -- Role tidak punya akses ke endpoint ini
- `JOB_ALREADY_RUNNING` -- Job user ini sudah running (user tidak boleh punya 2 running job)
- `JOB_NOT_FOUND` -- Job tidak ditemukan
- `USER_NOT_FOUND` -- User tidak ditemukan
- `USER_DISABLED` -- User account sudah di-disable

### OpenAPI Docs
- Auto-generated di `http://localhost:9988/docs` (Swagger UI)
- Alternative di `http://localhost:9988/redoc`

### SSE Event Format
```
event: progress
data: {"job_id":"abc123","leads_collected":15,"leads_total":50,"phase":"processing"}

event: status_change
data: {"job_id":"abc123","status":"completed","leads_collected":42}

event: heartbeat
data: {"timestamp":"2026-06-28T10:00:00Z"}
```

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Scope creep ke full web UI | High | High | PRD ini hanya backend API. Frontend terpisah. |
| Over-engineering untuk tool yang sederhana | Medium | Medium | Mulai dari MVP: job CRUD + queue + results + health. SSE dan config bisa phase 2. |
| Dependency conflict dengan camoufox | Low | Medium | Pin versi dependencies, test di CI |
| Queue starvation: job besar block queue lama | Medium | High | Set max target per job (500), estimasi wait time, admin bisa reorder, job timeout 30 menit |
| User bypass queue dengan submit banyak job | Medium | Medium | Limit 1 active/queued job per user, duplicate job detection, sisanya reject |
| SQLite lock contention saat concurrent write | Low | Medium | Gunakan WAL mode, write hanya saat batch/job selesai |
| Disk penuh karena leads terakumulasi | Medium | High | Disk space guard (reject >90%), auto-cleanup retention 90 hari, VACUUM berkala |
| Server restart kehilangan queue state | Medium | High | Startup recovery: reconstruct queue dari SQLite, mark orphan running jobs as failed |
| Camoufox hang block queue selamanya | Medium | High | Job timeout 30 menit (configurable), auto-cancel + dequeue next |
| Webhook endpoint user down/malicious | Low | Low | Timeout 10s, max 3 retry, log delivery status, tidak block job completion |
| Audit log table tumbuh terlalu besar | Low | Medium | Retention policy: auto-cleanup audit logs > 90 hari |

## Launch Plan

### Phase 1: MVP (Week 1-2)
- FastAPI app skeleton + uvicorn server di port 9988 (API versioning: `/api/v1/`)
- SQLite schema creation (`data/scraper.db`, users + jobs + leads + audit_logs tables, WAL mode)
- User management: `POST /api/v1/users`, `GET /api/v1/users/me` (admin only untuk CRUD)
- API key + RBAC middleware (admin/user role check)
- Auto-create default admin dari `ADMIN_API_KEY` env var saat first boot
- Input sanitization (Pydantic validators untuk semua input)
- `POST /api/v1/jobs` dengan parameter `keyword`, `location`, `target`, `smart`
- Job queue system: otomatis masuk waiting list jika ada job running
- Duplicate job detection (reject jika user sudah punya job sama yang queued/running)
- Job timeout (default 30 menit, configurable per-job)
- `GET /api/v1/jobs/{id}` dengan `queue_position` dan `estimated_wait_minutes`
- `GET /api/v1/queue` (admin: semua, user: posisi sendiri)
- `GET /api/v1/jobs/{id}/results` (JSON output dari SQLite, filtered by user)
- `GET /api/v1/health`
- Integrasi dengan existing `scrape()` / `scrape_smart()`
- Auto-write leads ke SQLite setelah setiap batch scraping selesai (dengan dedup check)
- Auto-dequeue job berikutnya setelah job selesai
- Graceful shutdown (SIGTERM handler: cancel job, close DB, exit)
- Startup recovery (restore queue, mark orphan jobs as failed)
- Unit tests untuk semua endpoint + SQLite store + queue logic

### Phase 2: Monitoring, Audit & Cleanup (Week 3)
- `GET /api/v1/jobs` (list + pagination + filter by keyword, user_id for admin)
- `DELETE /api/v1/jobs/{id}` (cancel with RBAC: user own jobs, admin any job)
- `PATCH /api/v1/queue/{job_id}` (admin: reorder queue)
- `DELETE /api/v1/queue/{job_id}` (admin: remove from queue)
- `GET /api/v1/system` (resource monitoring + disk space)
- `GET /api/v1/results` dengan filter (keyword, phone_not_null, search, dedup view)
- `GET /api/v1/results/stats` (agregat statistik)
- `GET /api/v1/results/export` (CSV/JSON export dari SQLite)
- Audit logging: `GET /api/v1/admin/audit-logs` (admin only)
- Data retention: auto-cleanup job/leads > 90 hari, manual `POST /api/v1/admin/cleanup`
- `GET /api/v1/admin/db-stats` (database size, row counts)
- Per-user rate limiting (60 req/min, admin exempt)

### Phase 3: Real-time, Webhook & Production (Week 4)
- SSE streaming (`GET /api/v1/jobs/{id}/stream`)
- `GET /api/v1/config` + `PATCH /api/v1/config` (admin only)
- CORS configuration (`CORSMORS_ORIGINS` env var)
- Webhook notification: `POST/GET/DELETE /api/v1/users/me/webhook`
- Structured JSON logging dengan log rotation
- systemd service file untuk production deployment
- Disk space guard (reject job jika disk > 90%)
- Persiapan endpoint untuk UI form input keyword (validation refinement)
- Integration test: full lifecycle (create user -> submit job -> queue -> scrape -> results -> webhook)

### Monitoring
- Health check endpoint untuk uptime monitoring (UptimeRobot, dll)
- Log scraping job lifecycle ke stdout (bisa di-redirect ke log aggregator)
- Alert jika RAM > 80% atau job gagal berulang

## Open Questions

| Question | Owner | Due |
|----------|-------|-----|
| Apakah perlu authentication selain API key? (JWT, OAuth?) | PM | - |
| Apakah perlu support multiple scraper instances (horizontal scaling)? | Engineering | - |
| Database: SQLite cukup atau perlu PostgreSQL untuk production? | Engineering | - |
| UI form keyword: Vue/Svelte/Astro? Deploy terpisah atau serve dari FastAPI? | PM + Engineering | - |
| Apakah category_variations perlu bisa di-manage via API (CRUD)? | PM | - |
| Apakah dedup lintas user juga diperlukan? (lead milik user A = lead milik user B) | PM | - |
| Apakah webhook perlu support custom headers (auth token)? | Engineering | - |
| Berapa banyak concurrent SSE connections yang di-support? | Engineering | - |

---

## Ringkasan Teknis untuk Engineering

### File yang perlu dibuat baru:
1. `portalonline_gmap_scraper/api/__init__.py`
2. `portalonline_gmap_scraper/api/app.py` -- FastAPI app factory (CORS, lifespan, mount routes)
3. `portalonline_gmap_scraper/api/models.py` -- Pydantic request/response models (User, Job, Queue, Lead, Audit)
4. `portalonline_gmap_scraper/api/job_manager.py` -- Job queue & lifecycle manager (FIFO queue, timeout, dedup, graceful shutdown)
5. `portalonline_gmap_scraper/api/store.py` -- SQLite persistence layer (users + jobs + leads + audit_logs tables, dedup logic)
6. `portalonline_gmap_scraper/api/sse.py` -- SSE streaming helper
7. `portalonline_gmap_scraper/api/webhook.py` -- Webhook delivery service (retry, timeout, logging)
8. `portalonline_gmap_scraper/api/cleanup.py` -- Data retention & cleanup scheduler
9. `portalonline_gmap_scraper/api/routes/__init__.py`
10. `portalonline_gmap_scraper/api/routes/auth.py` -- Login/API key validation endpoint
11. `portalonline_gmap_scraper/api/routes/users.py` -- User management endpoints (admin only)
12. `portalonline_gmap_scraper/api/routes/jobs.py` -- Job CRUD endpoints (with RBAC, dedup, timeout)
13. `portalonline_gmap_scraper/api/routes/queue.py` -- Queue management endpoints (admin: full, user: view only)
14. `portalonline_gmap_scraper/api/routes/results.py` -- Results endpoints (SQLite-backed, dedup view, filtered by user)
15. `portalonline_gmap_scraper/api/routes/config.py` -- Config endpoints (admin only)
16. `portalonline_gmap_scraper/api/routes/health.py` -- Health/system endpoints (disk space, RAM, CPU)
17. `portalonline_gmap_scraper/api/routes/admin.py` -- Admin endpoints (audit logs, cleanup, db-stats)
18. `portalonline_gmap_scraper/api/middleware/__init__.py`
19. `portalonline_gmap_scraper/api/middleware/auth.py` -- API key + RBAC middleware
20. `portalonline_gmap_scraper/api/middleware/rate_limit.py` -- Per-user rate limiter
21. `portalonline_gmap_scraper/api/middleware/sanitize.py` -- Input sanitization validators
22. `portalonline_gmap_scraper/server.py` -- Uvicorn entry point + graceful shutdown handler
23. `deploy/portalonline-scraper.service` -- systemd service file
24. `data/` -- Directory for SQLite database file (gitignored)

### File yang perlu dimodifikasi:
1. `pyproject.toml` -- Tambah dependencies (fastapi, uvicorn, pydantic, aiosqlite, httpx for webhooks)
2. `portalonline_gmap_scraper/__init__.py` -- Export API module
3. `portalonline_gmap_scraper/config.py` -- Tambah API config vars
4. `.gitignore` -- Tambah `data/` directory

### File test baru:
1. `tests/test_api_models.py` -- Pydantic model validation tests (User, Job, Queue, Lead, Audit)
2. `tests/test_job_manager.py` -- Job lifecycle + queue logic + timeout + dedup tests (mocked scraper)
3. `tests/test_store.py` -- SQLite store CRUD tests (in-memory DB, users + jobs + leads + audit_logs)
4. `tests/test_routes_users.py` -- User management endpoint tests (admin RBAC)
5. `tests/test_routes_jobs.py` -- HTTP endpoint tests (TestClient, user isolation, duplicate detection)
6. `tests/test_routes_queue.py` -- Queue management endpoint tests
7. `tests/test_routes_health.py` -- Health endpoint tests (disk space, resource monitoring)
8. `tests/test_routes_results.py` -- Results endpoint tests (SQLite-backed, dedup view, filtered by user)
9. `tests/test_routes_admin.py` -- Admin endpoint tests (audit logs, cleanup, db-stats)
10. `tests/test_auth.py` -- API key + RBAC middleware tests
11. `tests/test_rate_limit.py` -- Rate limiter tests
12. `tests/test_webhook.py` -- Webhook delivery tests (mocked HTTP)
13. `tests/test_sanitize.py` -- Input sanitization tests
14. `tests/test_startup_recovery.py` -- Startup recovery + graceful shutdown tests

### Urutan implementasi:
1. Tambah dependencies ke `pyproject.toml`, jalankan `uv sync`
2. Buat `models.py` (Pydantic models: User, Job, Queue, Lead, Audit, Webhook)
3. Buat `store.py` (SQLite layer: users + jobs + leads + audit_logs tables, dedup, queue operations)
4. Buat `middleware/auth.py` (API key validation + RBAC)
5. Buat `middleware/sanitize.py` (input sanitization)
6. Buat `middleware/rate_limit.py` (per-user rate limiter)
7. Buat `job_manager.py` (core logic: job lifecycle + FIFO queue + timeout + graceful shutdown)
8. Buat `webhook.py` (webhook delivery service)
9. Buat `cleanup.py` (data retention scheduler)
10. Buat `routes/users.py` (admin user management)
11. Buat `routes/jobs.py` (job CRUD with user isolation + dedup)
12. Buat `routes/queue.py` (queue status + admin reorder)
13. Buat `routes/results.py` + `routes/health.py` + `routes/config.py` + `routes/admin.py`
14. Buat `sse.py` (SSE streaming)
15. Buat `app.py` (FastAPI factory, mount routes + middleware + CORS + lifespan)
16. Buat `server.py` (Uvicorn entry point, startup recovery, graceful shutdown, auto-create default admin)
17. Buat `deploy/portalonline-scraper.service` (systemd service file)
18. Update `config.py` dengan semua API config vars
19. Update `.gitignore` dengan `data/`
20. Tulis tests untuk setiap layer
21. Integration test: full lifecycle (create user -> submit job -> queue -> scrape -> results -> webhook)
