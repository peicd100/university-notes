const { test, expect } = require("playwright/test");

test("plain details summary arrow does not overlap title text", async ({ page }) => {
  const consoleMessages = [];
  page.on("console", (msg) => {
    if (["error", "warning"].includes(msg.type())) {
      consoleMessages.push(`${msg.type()}: ${msg.text()}`);
    }
  });
  page.on("pageerror", (err) => consoleMessages.push(`pageerror: ${err.message}`));

  await page.goto("http://127.0.0.1:8765/md/114-2/%E9%9B%BB%E6%A9%9F_%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1/ch%205.html", { waitUntil: "networkidle" });
  await page.evaluate(() => document.documentElement.setAttribute("data-md-color-scheme", "slate"));

  if (await page.locator("details:not([class])").count() === 0) {
    await page.goto("http://127.0.0.1:8765/md/114-2/%E9%9B%BB%E6%A9%9F_%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1/ch%205.html", { waitUntil: "networkidle" });
    await page.evaluate(() => document.documentElement.setAttribute("data-md-color-scheme", "slate"));
  }

  const summary = page.locator("details:not([class]) > summary").first();
  await expect(summary).toBeVisible();
  await summary.scrollIntoViewIfNeeded();

  const result = await summary.evaluate((el) => {
    const summaryStyle = getComputedStyle(el);
    const beforeStyle = getComputedStyle(el, "::before");
    const range = document.createRange();
    const textNode = Array.from(el.childNodes).find(
      (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim(),
    );

    let textRect = null;
    if (textNode) {
      range.setStart(textNode, 0);
      range.setEnd(textNode, textNode.textContent.length);
      const rect = Array.from(range.getClientRects()).find((item) => item.width && item.height);
      if (rect) {
        textRect = { left: rect.left, right: rect.right, width: rect.width };
      }
    }

    const summaryRect = el.getBoundingClientRect();
    const expectedTextLeft =
      summaryRect.left +
      parseFloat(summaryStyle.paddingLeft) +
      parseFloat(beforeStyle.marginLeft) +
      parseFloat(beforeStyle.width) +
      parseFloat(beforeStyle.marginRight) +
      parseFloat(summaryStyle.gap);

    return {
      pageUrl: location.href,
      title: el.textContent.trim(),
      display: summaryStyle.display,
      gap: summaryStyle.gap,
      beforePosition: beforeStyle.position,
      beforeDisplay: beforeStyle.display,
      beforeWidth: beforeStyle.width,
      beforeHeight: beforeStyle.height,
      beforeMaskImage: beforeStyle.webkitMaskImage || beforeStyle.maskImage,
      expectedTextLeft,
      textRect,
      noOverlap: Boolean(textRect && textRect.left >= expectedTextLeft - 1),
    };
  });

  await page.screenshot({
    path: "Y:/github_note/university notes/.codex/codex/artifacts/details-summary-after.png",
    fullPage: false,
  });

  console.log(`DETAILS_SUMMARY_CHECK ${JSON.stringify({ ...result, consoleMessages })}`);
  expect(result.beforePosition).toBe("static");
  expect(result.beforeDisplay).toBe("block");
  expect(result.noOverlap).toBe(true);
});
