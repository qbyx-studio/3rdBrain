const { test, expect } = require("@playwright/test");

test("desktop contents and long prompts stay readable inside their columns", async ({ page }) => {
  await page.setViewportSize({ width: 1848, height: 1000 });
  await page.goto("/");
  await page.locator(".md-content__inner").evaluate((content) => {
    content.innerHTML = `<h1>Layout fixture</h1><details class="note" open>
      <summary>Long prompt</summary><div class="highlight"><pre><code>${
        Array.from({ length: 100 }, (_, i) => `Line ${i}: ${"long-content ".repeat(20)}`).join("\n")
      }</code></pre></div></details>`;
  });
  await page.locator(".md-sidebar--secondary .md-nav__list").first().evaluate((list) => {
    list.innerHTML = Array.from({ length: 7 }, (_, i) =>
      `<li class="md-nav__item"><a class="md-nav__link"><span class="md-ellipsis">Readable contents heading ${i} with a long descriptive title</span></a></li>`
    ).join("");
  });

  const layout = await page.evaluate(() => {
    const toc = document.querySelector(".md-sidebar--secondary");
    const links = [...document.querySelectorAll(".md-nav--secondary .md-nav__link")];
    const details = document.querySelector("details.note");
    const pre = details.querySelector("pre");
    const detailBox = details.getBoundingClientRect();
    const preBox = pre.getBoundingClientRect();
    return {
      tocWidth: toc.getBoundingClientRect().width,
      tocLinksFit: links.every((link) => link.scrollWidth <= link.clientWidth + 1),
      tocLineHeight: parseFloat(getComputedStyle(links[0]).lineHeight),
      promptScrollsDown: pre.scrollHeight > pre.clientHeight,
      promptScrollsAcross: pre.scrollWidth > pre.clientWidth,
      promptOverflowY: getComputedStyle(pre).overflowY,
      promptOverflowX: getComputedStyle(pre).overflowX,
      promptContained: preBox.left >= detailBox.left && preBox.right <= detailBox.right + 1,
    };
  });
  expect(layout.tocWidth).toBeGreaterThanOrEqual(300);
  expect(layout.tocLinksFit).toBe(true);
  expect(layout.tocLineHeight).toBeGreaterThanOrEqual(18);
  expect(layout.promptScrollsDown).toBe(true);
  expect(layout.promptScrollsAcross).toBe(true);
  expect(layout.promptOverflowY).toBe("auto");
  expect(layout.promptOverflowX).toBe("auto");
  expect(layout.promptContained).toBe(true);
  await page.screenshot({ path: test.info().outputPath("layout-1848.png") });
});

test("reading layout stays inside phone, tablet, and desktop viewports", async ({ page }) => {
  for (const width of [375, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    const viewportFits = await page.evaluate(() =>
      document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1
    );
    expect(viewportFits).toBe(true);
  }
});
