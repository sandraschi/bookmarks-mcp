import { expect, test } from "@playwright/test";

test("dashboard shell loads", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Bookmark Master/i }),
  ).toBeVisible();
});

test("navigation links exist", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: /Bookmarks/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Search/i })).toBeVisible();
});
