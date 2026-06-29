# Frontend Testing Conventions (Playwright E2E)

## File Organization
- Tests live in `frontend/e2e/` directory
- Test files: `*.spec.ts`
- Group related tests with `test.describe("Feature", () => { ... })`

## Test Structure
- Framework: Playwright (`@playwright/test`)
- Use `test("description", async ({ page }) => { ... })` pattern
- Arrange → Act → Assert: setup page state, perform action, verify result
- Use semantic locators: `page.locator("h1")`, `page.locator("#id")`, `page.locator(".class")`

## Assertions
- `expect(page.locator(...)).toBeVisible()`
- `expect(page.locator(...)).toContainText("...")`
- `expect(page).toHaveURL(/pattern/)`
- Always set explicit `timeout` for async assertions on dynamic content

## Configuration
- Config file: `frontend/playwright.config.ts`
- `webServer` starts backend Python server automatically
- `baseURL` points to backend URL (Vite proxies `/api`)
- `projects`: chromium only (no cross-browser for now)
- CI mode (`CI=true`): retries=2, workers=1

## Execution
```bash
cd frontend && npx playwright test           # Run all e2e
cd frontend && npx playwright test --ui      # Interactive UI mode
cd frontend && npx playwright test auth.spec.ts  # Single file
```

## Mocking & Fixtures
- Playwright starts real backend server via `webServer` config — no mocking needed
- `page.goto("/path")` uses `baseURL` for URL resolution
