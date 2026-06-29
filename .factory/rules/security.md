# Security & Safety Conventions

## Secrets Management (Both Projects)
- Never commit `.env` or hardcode credentials in code
- Use environment variables as the single source of truth for all secrets
- Backend: `python-dotenv` + `config.py` for runtime config
- Frontend: no API keys, tokens, or secrets in source code (use backend endpoints)

## Backend: Browser Safety (Camoufox)
- Run strictly in headless mode (`HEADLESS=true`) by default on servers
- Disable WebGL to block tracking, save memory
- Suppress unhandled page errors to prevent process crashes

## Backend: Resource Safety
- Honor `MEM_LIMIT_MB` and `CPU_LIMIT_PERCENT`
- Respect `COOLDOWN_SEC` and `INTER_QUERY_COOLDOWN` to prevent bans
- Run scraping at a lower OS priority (`PROCESS_NICE=10`)

## Frontend: API & Data Safety
- No hardcoded API keys, tokens, or secrets in frontend source code
- Auth token stored in `localStorage` -- use `Authorization: Bearer` header for API calls
- Vite dev server proxies `/api` to backend -- no CORS issues in development
- Never trust client-side validation alone -- backend must re-validate all input

## Frontend: XSS & Injection Prevention
- Vue automatically escapes `{{ }}` template bindings -- do NOT use `v-html` with user input
- Sanitize any dynamically rendered content
- Avoid `eval()`, `new Function()`, or dynamic code execution
