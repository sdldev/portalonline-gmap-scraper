# Security & Safety Conventions

## Secrets Management
- Use `python-dotenv` to load configurations
- Use `config.py` as the single source of truth for runtime variables
- Never commit `.env` or hardcode credentials in code

## Browser Safety (Camoufox)
- Run strictly in headless mode (`HEADLESS=true`) by default on servers
- Disable WebGL/Images/Media to block tracking and save memory
- Suppress unhandled page errors to prevent process crashes

## Resource Safety
- Honor `MEM_LIMIT_MB` and `CPU_LIMIT_PERCENT`
- Respect `COOLDOWN_SEC` and `INTER_QUERY_COOLDOWN` to prevent bans
- Run scraping at a lower OS priority (`PROCESS_NICE=10`)
