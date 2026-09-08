async (page) => {
  await page.setViewportSize({ width: 1280, height: 820 });
  await page.goto("file:///Y:/github_note/university%20notes/site/md/114-2/%E7%A7%91%E6%8A%80_%E8%A8%88%E7%AE%97%E6%A9%9F%E7%B5%90%E6%A7%8B/%E6%9C%9F%E6%9C%AB%E8%80%83%E8%A4%87%E7%BF%92-ch4.2.html", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  return await page.evaluate(() => ({
    title: document.title,
    href: window.location.href,
    readyState: document.readyState,
    hasSecondary: Boolean(document.querySelector(".md-sidebar--secondary")),
    hasTocComponent: Boolean(document.querySelector(".md-sidebar--secondary [data-md-component='toc']")),
    hasDangerButton: Boolean(document.querySelector(".peicd-toc-control--danger")),
    secondaryClass: document.querySelector(".md-sidebar--secondary")?.className || "",
    scripts: Array.from(document.scripts).map((script) => script.src).filter((src) => src.includes("toc-fold") || src.includes("自定義")).slice(0, 5),
    errors: window.__peicdDebugErrors || null,
    bodyStart: document.body?.innerText?.slice(0, 300) || ""
  }));
}
