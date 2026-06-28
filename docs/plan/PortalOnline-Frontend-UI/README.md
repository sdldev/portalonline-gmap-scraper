# PortalOnline Frontend UI - Implementation Plans

Breakdown of [PRD-frontend-ui.md](../../PRD-frontend-ui.md) into 5 implementation phases.

---

## Phases

| # | Phase | Description | File | Effort |
|---|---|---|---|---|
| 1 | Backend Auth + API | JWT auth, password hashing, dashboard stats, user management endpoints | [phase-1-backend-auth-api.md](phase-1-backend-auth-api.md) | 2-3 days |
| 2 | Frontend Setup | Scaffold Vue 3 + Vite, router, stores, API client, login page, app layout, base components | [phase-2-frontend-setup.md](phase-2-frontend-setup.md) | 2-3 days |
| 3 | Core Pages | Dashboard (stats), Scrape (form + SSE live progress), Results (jobs table + filters + actions) | [phase-3-core-pages.md](phase-3-core-pages.md) | 3-4 days |
| 4 | User Management | Users page (admin CRUD), create/edit/view/delete modals, generate password, generate API key | [phase-4-user-management.md](phase-4-user-management.md) | 1-2 days |
| 5 | Polish & E2E | Loading states, error handling, responsive design, accessibility, Playwright E2E tests | [phase-5-polish-e2e.md](phase-5-polish-e2e.md) | 1-2 days |

**Total estimated effort**: 9-14 days

---

## Dependency Graph

```
Phase 1 (Backend Auth + API)
  |
  v
Phase 2 (Frontend Setup - scaffold, login, layout, base components)
  |
  v
Phase 3 (Core Pages - Dashboard, Scrape, Results)
  |
  +---> Phase 4 (User Management - Users page + modals)
  |
  +---> Phase 5 (Polish & E2E Tests)
```

- **Phase 1**: Pure backend, no frontend dependency. Can start immediately.
- **Phase 2**: Needs Phase 1 API endpoints (`/auth/login`, `/auth/logout`).
- **Phase 3**: Needs Phase 2 (router, stores, base components, AppLayout).
- **Phase 4**: Needs Phase 2 + Phase 3 (base components, modals pattern established in Phase 3).
- **Phase 5**: Needs Phases 3 + 4 (all pages built before polishing).

Phases 4 and 5 can run in parallel after Phase 3 is complete.

---

## New Backend Endpoints (Phase 1)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | None | Username + password -> JWT token |
| POST | `/api/v1/auth/logout` | User | Invalidate session (optional) |
| GET | `/api/v1/admin/stats` | Admin | Dashboard aggregate counts |
| POST | `/api/v1/users/{id}/generate-password` | Admin | Generate random 16-char password |
| POST | `/api/v1/users/{id}/generate-api-key` | Admin | Regenerate API key |

---

## Frontend Page Map

| URL | Page | Auth | Admin Only | Phase |
|---|---|---|---|---|
| `/login` | LoginPage | No | No | 2 |
| `/dashboard` | DashboardPage | Yes | No | 3 |
| `/scrape` | ScrapePage | Yes | No | 3 |
| `/results` | ResultsPage | Yes | No | 3 |
| `/users` | UsersPage | Yes | Yes | 4 |

---

## Component Tree

```
App.vue
├── LoginPage.vue                              [Phase 2]
└── AppLayout.vue                              [Phase 2]
    ├── AppHeader.vue                          [Phase 2]
    ├── AppSidebar.vue                         [Phase 2]
    └── <router-view>
        ├── DashboardPage.vue                  [Phase 3]
        │   ├── StatCard.vue                   [Phase 3]
        │   └── RecentJobsTable.vue            [Phase 3]
        ├── ScrapePage.vue                     [Phase 3]
        │   ├── ScrapeForm.vue                 [Phase 3]
        │   ├── ProgressBar.vue                [Phase 3]
        │   └── LiveResultsTable.vue           [Phase 3]
        ├── ResultsPage.vue                    [Phase 3]
        │   ├── ResultFilters.vue              [Phase 3]
        │   ├── JobsTable.vue                  [Phase 3]
        │   └── JobDetailModal.vue             [Phase 3]
        └── UsersPage.vue                      [Phase 4]
            ├── CreateUserModal.vue            [Phase 4]
            ├── ViewUserModal.vue              [Phase 4]
            ├── EditUserModal.vue              [Phase 4]
            ├── GeneratePasswordModal.vue      [Phase 4]
            └── GenerateApiKeyModal.vue        [Phase 4]

Shared (all phases):
├── BaseButton.vue                             [Phase 2]
├── BaseModal.vue                              [Phase 2]
├── BaseTable.vue                              [Phase 2]
├── BaseBadge.vue                              [Phase 2]
├── BaseCard.vue                               [Phase 2]
├── EmptyState.vue                             [Phase 5]
└── ToastContainer.vue                         [Phase 5]
```

---

## Verification Summary

After completing all 5 phases, verify end-to-end:

1. **Start backend**: `.venv/bin/python -m portalonline_gmap_scraper.server`
2. **Seed admin user**: `.venv/bin/python manage.py seed`
3. **Build frontend**: `cd frontend && npm run build`
4. **Visit**: `http://localhost:8000` -> Login page
5. **Login**: admin credentials -> Dashboard with stats
6. **Scrape**: Submit keyword -> Live progress -> Completed
7. **Results**: View results, export CSV, delete job
8. **Users**: Create user, view/edit/delete, generate password + API key
9. **Logout**: Return to login page
10. **E2E**: `cd frontend && npx playwright test` - all pass
