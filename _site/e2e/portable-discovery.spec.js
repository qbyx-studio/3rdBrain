const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

test("fresh PromptOS uses one engine in the header and full Discover page", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".md-nav--primary a.md-nav__link").first()).toContainText(
    "Discover PromptOS by Qbyx"
  );

  await page.locator(".md-search__input").fill("Tool Index");
  await expect(page.locator("[data-testid='quick-result']").first()).toContainText("Tool Index");
  await page.getByRole("link", { name: /view all in discover/i }).click();

  await expect(page).toHaveURL(/\/discover\/?\?q=Tool\+Index/);
  await expect(page.getByRole("heading", { name: "Discover PromptOS by Qbyx" })).toBeVisible();
  await expect(page.getByRole("searchbox", { name: "Search this knowledge base" })).toHaveValue(
    "Tool Index"
  );
  await expect(page.locator("[data-testid='result-card']").first()).toContainText("Tool Index");
});

test("fresh Discover is readable, wide, and free of serious automated a11y findings", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/discover/");
  await expect(page.locator("[data-testid='result-card']").first()).toBeVisible();

  const scale = await page.evaluate(() => ({
    input: parseFloat(getComputedStyle(document.querySelector("#po-discovery-query")).fontSize),
    label: parseFloat(getComputedStyle(document.querySelector(".po-discovery__label")).fontSize),
    canvas: document.querySelector(".md-content__inner").getBoundingClientRect().width,
  }));
  expect(Math.abs(scale.input - scale.label)).toBeLessThanOrEqual(1);
  expect(scale.canvas).toBeGreaterThanOrEqual(820);

  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact)
    )
  ).toEqual([]);
});
