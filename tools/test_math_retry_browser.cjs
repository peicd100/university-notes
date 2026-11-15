// One deliberate CDN failure, then explicit reload and real MathJax 3.2.2 recovery.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs'), assert = require('node:assert/strict');
const { serve } = require('./browser_site_fixture.cjs');
if (!process.env.UX_SITE_DIR || !process.env.MATH_RESULT) throw new Error('Set UX_SITE_DIR and MATH_RESULT');
(async () => {
  const server = await serve(process.env.UX_SITE_DIR), browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXE ? { executablePath: process.env.CHROMIUM_EXE } : {}) });
  try {
    const context = await browser.newContext();
    await context.addInitScript(() => { window.__nativePrintCalls = 0; window.print = () => { __nativePrintCalls++; }; });
    await context.route('https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js', route => route.abort(), { times: 1 });
    const page = await context.newPage();
    const url = server.base + 'md/114-2/' + encodeURIComponent('電機_作業系統') + '/' + encodeURIComponent('期中考重點.html');
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '重新載入公式' }).waitFor();
    assert((await page.locator('.md-content__inner .arithmatex').first().textContent()).trim().length > 0);
    await page.getByRole('button', { name: '重新載入公式' }).click();
    await page.waitForFunction(() => window.__PEICD_MATH__ && !document.querySelector('.peicd-math-error'));
    await page.evaluate(() => __PEICD_MATH__.renderAll());
    await page.waitForFunction(() => document.querySelector('.md-content__inner .arithmatex > mjx-container'), null, { timeout: 45000 });
    assert.equal(await page.locator('.peicd-math-error').count(), 0);
    await page.evaluate(() => window.print());
    assert.equal(await page.evaluate(() => window.__nativePrintCalls), 1);
    const result = { actualRuntime: 'MathJax 3.2.2 CDN', failureSourcePreserved: true, explicitReloadRecovery: true,
      rendered: await page.locator('.md-content__inner .arithmatex > mjx-container').count(), printAfterRender: true,
      scope: 'Headless browser; native print stubbed, no OS print dialog' };
    fs.writeFileSync(process.env.MATH_RESULT, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify(result, null, 2));
  } finally { await browser.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
