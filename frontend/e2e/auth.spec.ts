import { test, expect } from "@playwright/test"

test.describe("Authentication", () => {
  test("login page loads", async ({ page }) => {
    await page.goto("/login")
    await expect(page.locator("h1")).toContainText("PortalOnline")
    await expect(page.locator("#username")).toBeVisible()
    await expect(page.locator("#password")).toBeVisible()
  })

  test("login with invalid credentials shows error", async ({ page }) => {
    await page.goto("/login")
    await page.fill("#username", "wrong")
    await page.fill("#password", "wrong")
    await page.click('button[type="submit"]')
    await expect(page.locator(".bg-red-50")).toBeVisible({ timeout: 5000 })
  })

  test("redirects to login when not authenticated", async ({ page }) => {
    await page.goto("/dashboard")
    await expect(page).toHaveURL(/\/login/)
  })
})
