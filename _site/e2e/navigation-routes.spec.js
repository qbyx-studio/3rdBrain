const { test, expect } = require("@playwright/test");

test("every clickable primary-sidebar route resolves", async ({ page, request }) => {
  await page.goto("/");
  const hrefs = await page.locator(".md-nav--primary a[href]").evaluateAll((links) =>
    [...new Set(links.map((link) => link.href.split("#")[0]))]
  );

  expect(hrefs.length).toBeGreaterThan(5);
  for (const href of hrefs) {
    const response = await request.get(href);
    expect(response.status(), href).toBeLessThan(400);
  }
});
