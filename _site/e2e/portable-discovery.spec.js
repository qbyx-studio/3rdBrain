const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

test("fresh 3rdBrain uses one engine in the header and full Discover page", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".md-nav--primary a.md-nav__link").first()).toContainText(
    "Discover 3rdBrain by Qbyx Studio"
  );

  await page.locator(".md-search__input").fill("Tool Index");
  await expect(page.locator("[data-testid='quick-result']").first()).toContainText("Tool Index");
  await page.getByRole("link", { name: /view all in discover/i }).click();

  await expect(page).toHaveURL(/\/discover\/?\?q=Tool\+Index/);
  await expect(page.getByRole("heading", { name: "Discover 3rdBrain by Qbyx Studio" })).toBeVisible();
  await expect(page.getByRole("searchbox", { name: "Search this knowledge base" })).toHaveValue(
    "Tool Index"
  );
  await expect(page.locator(".md-search__input")).toHaveValue("");
  await expect(page.locator("#__search")).not.toBeChecked();
  await expect(page.locator(".po-quick-search")).toBeHidden();
  await expect(page.locator("[data-testid='result-card']").first()).toContainText("Tool Index");
});

test("opening a quick result clears and closes header search on the destination", async ({ page }) => {
  await page.goto("/");
  const globalSearch = page.locator(".md-search__input");
  await globalSearch.fill("Tool Index");

  const result = page.locator("[data-testid='quick-result']").first();
  await expect(result).toContainText("Tool Index");
  await result.evaluate((link) =>
    link.addEventListener("click", (event) => event.preventDefault(), { once: true })
  );
  await result.click();

  await expect(globalSearch).toHaveValue("");
  await expect(page.locator("#__search")).not.toBeChecked();
  await expect(page.locator(".po-quick-search")).toBeHidden();

  await globalSearch.fill("Tool Index");
  await page.locator("[data-testid='quick-result']").first().click();

  await expect(page).toHaveURL(/\/tool-index\/$/);
  await expect(globalSearch).toHaveValue("");
  await expect(page.locator("#__search")).not.toBeChecked();
  await expect(page.locator(".po-quick-search")).toBeHidden();
});

test("fresh Discover is readable, wide, and free of serious automated a11y findings", async ({ page }) => {
  await page.setViewportSize({ width: 1848, height: 1000 });
  await page.goto("/discover/");
  await expect(page.locator("[data-testid='result-card']").first()).toBeVisible();

  const scale = await page.evaluate(() => ({
    input: parseFloat(getComputedStyle(document.querySelector("#po-discovery-query")).fontSize),
    label: parseFloat(getComputedStyle(document.querySelector(".po-discovery__label")).fontSize),
    title: parseFloat(getComputedStyle(document.querySelector(".po-discovery-title")).fontSize),
    resultTitle: parseFloat(getComputedStyle(document.querySelector(".po-result h2")).fontSize),
    resultBody: parseFloat(getComputedStyle(document.querySelector(".po-result p:not(.po-result__breadcrumb)")).fontSize),
    resultMeta: parseFloat(getComputedStyle(document.querySelector(".po-result__meta")).fontSize),
    canvas: document.querySelector(".md-content__inner").getBoundingClientRect().width,
    primaryGap: document.querySelector(".md-content__inner").getBoundingClientRect().left -
      document.querySelector(".md-sidebar--primary .md-sidebar__inner").getBoundingClientRect().right,
    secondaryGap: document.querySelector(".md-sidebar--secondary .md-sidebar__inner").getBoundingClientRect().left -
      document.querySelector(".md-content__inner").getBoundingClientRect().right,
  }));
  expect(Math.abs(scale.input - scale.label)).toBeLessThanOrEqual(1);
  expect(scale.title).toBeLessThanOrEqual(28);
  expect(scale.input).toBeLessThanOrEqual(15);
  expect(scale.resultTitle).toBeLessThanOrEqual(19);
  expect(scale.resultBody).toBeLessThanOrEqual(15);
  expect(scale.resultMeta).toBeLessThanOrEqual(12.5);
  expect(scale.canvas).toBeGreaterThanOrEqual(1000);
  expect(scale.canvas).toBeLessThanOrEqual(1050);
  // Approved desktop gutter: 147.4px baseline increased by 30% on both sides.
  expect(scale.primaryGap).toBeGreaterThanOrEqual(191.5);
  expect(scale.primaryGap).toBeLessThanOrEqual(192);
  expect(scale.secondaryGap).toBeGreaterThanOrEqual(191.5);
  expect(scale.secondaryGap).toBeLessThanOrEqual(192);
  expect(Math.abs(scale.primaryGap - scale.secondaryGap)).toBeLessThanOrEqual(1);

  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact)
    )
  ).toEqual([]);
});

test("optional local meaning model reranks a remembered-intent query", async ({ page }) => {
  test.skip(process.env.SEMANTIC_E2E !== "1", "downloads the browser model only in the semantic release gate");
  test.setTimeout(120_000);
  await page.goto("/discover/");
  await page.getByRole("searchbox", { name: "Search this knowledge base" }).fill(
    "the page where every useful utility is collected"
  );
  await expect(page.locator("[data-testid='match-reason']").filter({ hasText: "Meaning match" }).first())
    .toBeVisible({ timeout: 110_000 });
});
