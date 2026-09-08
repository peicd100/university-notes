async (page) => {
  const url = "http://127.0.0.1:8765/md/114-2/%E7%A7%91%E6%8A%80_%E8%A8%88%E7%AE%97%E6%A9%9F%E7%B5%90%E6%A7%8B/%E6%9C%9F%E6%9C%AB%E8%80%83%E8%A4%87%E7%BF%92-ch4.2.html";
  const screenshotPath = "Y:/github_note/university notes/.codex/codex/artifacts/danger-toc-toolbar-after.png";
  const consoleMessages = [];

  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      consoleMessages.push(`${message.type()}: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    consoleMessages.push(`pageerror: ${error.message}`);
  });

  await page.setViewportSize({ width: 1280, height: 820 });
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForSelector(".md-sidebar--secondary.peicd-toc-sidebar .peicd-toc-control--danger", { timeout: 10000 });

  const buttonMetrics = await page.evaluate(() => (
    Array.from(document.querySelectorAll(".md-sidebar--secondary.peicd-toc-sidebar .peicd-toc-control")).map((button) => ({
      text: button.textContent.trim(),
      width: Number(button.getBoundingClientRect().width.toFixed(2)),
      clientWidth: button.clientWidth,
      scrollWidth: button.scrollWidth,
      textFits: button.scrollWidth <= button.clientWidth + 1
    }))
  ));

  await page.click(".md-sidebar--secondary.peicd-toc-sidebar .peicd-toc-control--danger");
  await page.waitForFunction(() => document.querySelector(".md-sidebar--secondary")?.dataset.peicdTocView === "danger");
  const afterFirstDanger = await page.evaluate(() => ({
    view: document.querySelector(".md-sidebar--secondary")?.dataset.peicdTocView || "",
    dangerPressed: document.querySelector(".peicd-toc-control--danger")?.getAttribute("aria-pressed") || "",
    dangerListDisplay: getComputedStyle(document.querySelector(".peicd-danger-list")).display,
    normalVisibleLinks: Array.from(document.querySelectorAll('[data-md-component="toc"] > .md-nav__list:not(.peicd-danger-list) a.md-nav__link')).filter((link) => getComputedStyle(link).display !== "none" && link.getClientRects().length > 0).length
  }));

  await page.click(".md-sidebar--secondary.peicd-toc-sidebar .peicd-toc-control--danger");
  await page.waitForTimeout(100);
  const afterSecondDanger = await page.evaluate(() => ({
    view: document.querySelector(".md-sidebar--secondary")?.dataset.peicdTocView || "",
    dangerPressed: document.querySelector(".peicd-toc-control--danger")?.getAttribute("aria-pressed") || ""
  }));

  await page.click(".peicd-danger-link");
  await page.waitForTimeout(450);
  const afterDangerLink = await page.evaluate(() => ({
    view: document.querySelector(".md-sidebar--secondary")?.dataset.peicdTocView || "",
    hash: window.location.hash,
    currentDangerLabels: Array.from(document.querySelectorAll(".peicd-danger-current-label")).filter((label) => !label.hidden && label.getClientRects().length > 0).length,
    normalVisibleLinks: Array.from(document.querySelectorAll('[data-md-component="toc"] > .md-nav__list:not(.peicd-danger-list) a.md-nav__link')).filter((link) => getComputedStyle(link).display !== "none" && link.getClientRects().length > 0).length
  }));

  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector(".md-sidebar--secondary.peicd-toc-sidebar .peicd-toc-control--danger", { timeout: 10000 });
  const afterReloadOnDangerHash = await page.evaluate(() => ({
    view: document.querySelector(".md-sidebar--secondary")?.dataset.peicdTocView || "",
    hash: window.location.hash,
    dangerPressed: document.querySelector(".peicd-toc-control--danger")?.getAttribute("aria-pressed") || ""
  }));

  await page.screenshot({ path: screenshotPath, fullPage: false });

  return {
    buttonMetrics,
    afterFirstDanger,
    afterSecondDanger,
    afterDangerLink,
    afterReloadOnDangerHash,
    screenshotPath,
    consoleMessages: consoleMessages.slice(0, 10)
  };
}
