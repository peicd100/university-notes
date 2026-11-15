// Full-site UX acceptance. Explicit existing installations; no package downloads.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { serve } = require('./browser_site_fixture.cjs');
if (!process.env.UX_SITE_DIR || !process.env.UX_ARTIFACTS_DIR) throw new Error('Set UX_SITE_DIR and UX_ARTIFACTS_DIR');
const out = path.resolve(process.env.UX_ARTIFACTS_DIR);
fs.mkdirSync(out, { recursive: true });
const report = { scope: 'Local built site, headless Chromium; no real-device/physical-IME claims', sourceOverlay: process.env.UX_SOURCE_OVERLAY === '1', steps: {} };
const encodePath = value => value.split('/').map(encodeURIComponent).join('/');
(async () => {
  const server = await serve(process.env.UX_SITE_DIR);
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXE ? { executablePath: process.env.CHROMIUM_EXE } : {}) });
  let activePage;
  const checkpoint = () => fs.writeFileSync(path.join(out, 'partial.json'), JSON.stringify(report, null, 2) + '\n');
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    // These scenarios isolate local controls. Real CDN math runs separately.
    await context.route('**/*', route => new URL(route.request().url()).origin === new URL(server.base).origin ? route.continue() : route.abort());
    const page = await context.newPage(); activePage = page;
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    const course = server.base + encodePath('md/115-1/硬體描述語言/ch00.html');
    await page.goto(course, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('.md-sidebar--secondary .peicd-toc-head').count(), 1);
    assert.equal(await page.locator('.md-sidebar--secondary .peicd-toc-head [disabled]').count(), 0, 'SSR shell was replaced by live controls');
    await page.evaluate(() => { window.__uxWindow = true; });
    let toggles = page.locator('.peicd-folder-pathbar__toggle');
    await toggles.nth(1).click();
    const menu = page.locator('.peicd-folder-pathbar__item.is-open .peicd-folder-pathbar__menu');
    assert.equal(await menu.getAttribute('role'), null, 'disclosure uses ordinary links');
    await menu.locator('input').fill('L02');
    assert.equal(await menu.locator('li:not([hidden]) a').count(), 1);
    await menu.locator('li:not([hidden]) a').focus();
    await page.keyboard.press('Escape');
    assert.equal(await toggles.nth(1).evaluate(node => node === document.activeElement), true);
    await toggles.nth(1).click();
    const bounds = await menu.boundingBox();
    assert(bounds.x >= 0 && bounds.x + bounds.width <= 1441);
    await page.screenshot({ path: path.join(out, 'pathbar-desktop.png') });
    await menu.getByRole('link', { name: 'L02', exact: true }).click();
    await page.waitForURL(url => decodeURIComponent(url.pathname).endsWith('/L02.html'));
    assert.equal(await page.evaluate(() => window.__uxWindow), true);
    await page.setViewportSize({ width: 390, height: 844 });
    toggles = page.locator('.peicd-folder-pathbar__toggle');
    await toggles.nth(1).click();
    const mobileMenu = page.locator('.peicd-folder-pathbar__item.is-open .peicd-folder-pathbar__menu');
    const mobileBounds = await mobileMenu.boundingBox();
    assert(mobileBounds.x >= -1 && mobileBounds.x + mobileBounds.width <= 391);
    await page.screenshot({ path: path.join(out, 'pathbar-mobile.png') });
    await mobileMenu.getByRole('link', { name: 'L03', exact: true }).click();
    await page.waitForURL(url => decodeURIComponent(url.pathname).endsWith('/L03.html'));
    assert.equal(await page.evaluate(() => window.__uxWindow), true, 'mobile uses Material instant navigation');
    report.steps.pathbar = 'PASS: escaped SSR shell, filter, Esc focus, desktop/mobile bounds, real instant links'; checkpoint();

    await page.locator('label.md-header__button[for="__search"]').click();
    const input = page.locator('[data-md-component="search-query"]');
    await input.fill('a');
    await page.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'results' && __PEICD_SEARCH_LAZY_GUARD__.snapshot().info?.query === 'a');
    await page.waitForFunction(() => document.querySelectorAll('.md-search-result__item').length > 0);
    const first = await page.evaluate(() => ({ info: __PEICD_SEARCH_LAZY_GUARD__.snapshot().info,
      groups: document.querySelectorAll('.md-search-result__item').length,
      links: document.querySelectorAll('.md-search-result__link').length }));
    assert(first.groups <= 10 && first.links <= 40 && first.info.totalPages > 10);
    assert.equal(await page.locator('.peicd-search-controls').isVisible(), true);
    await page.locator('.peicd-search-controls').getByRole('button', { name: '下一批', exact: true }).click();
    await page.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'results' && __PEICD_SEARCH_LAZY_GUARD__.snapshot().info.offset === 10);
    const more = page.locator('.peicd-search-more').first();
    if (await more.count()) {
      await more.click();
      await page.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'results' && !!__PEICD_SEARCH_LAZY_GUARD__.snapshot().info.page);
      assert.equal(await page.locator('.md-search-result__item').count(), 1);
      assert((await page.locator('.md-search-result__link').count()) <= 11);
      await page.getByRole('button', { name: '返回全部文章' }).click();
      await page.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'results' && !__PEICD_SEARCH_LAZY_GUARD__.snapshot().info.page);
    }
    await page.getByRole('combobox', { name: '搜尋學期與課程' }).selectOption('115-1/離散/');
    await page.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'results' && __PEICD_SEARCH_LAZY_GUARD__.snapshot().info.scope === '115-1/離散/');
    const links = await page.locator('.md-search-result__link').evaluateAll(nodes => nodes.map(node => decodeURIComponent(node.href)));
    assert(links.length && links.every(href => href.includes('/115-1/離散/')));
    await page.screenshot({ path: path.join(out, 'search-filter-mobile.png') });
    report.steps.search = { status: 'PASS', initialGroups: first.groups, initialLinks: first.links, totalPages: first.info.totalPages, pagination: true, courseScope: true }; checkpoint();
    await input.press('Escape');

    await page.goto(server.base + encodePath('md/114-2/科技_計算機結構/ch 2.html'), { waitUntil: 'networkidle' });
    const image = page.locator('.md-content__inner img[data-peicd-full-src]').first();
    await image.waitFor(); await image.scrollIntoViewIfNeeded();
    const full = await image.getAttribute('data-peicd-full-src');
    const expected = new URL(full, page.url()).href;
    await image.focus(); await image.press('Enter');
    const viewer = page.locator('dialog.peicd-image-viewer:not(.peicd-mermaid-viewer)');
    await viewer.waitFor({ state: 'visible' });
    await page.waitForFunction(() => document.querySelector('dialog[open] img')?.naturalWidth > 0 && document.querySelector('dialog[open] img').style.transform.includes('scale'));
    assert.equal(await viewer.locator('img').getAttribute('src'), expected);
    const frames = await viewer.evaluate(async dialog => {
      let changes = 0;
      const observer = new MutationObserver(records => { changes += records.length; });
      observer.observe(dialog.querySelector('img'), { attributes: true, attributeFilter: ['style'] });
      for (let i = 0; i < 10; i++) dialog.querySelector('.peicd-image-viewer__stage').dispatchEvent(new WheelEvent('wheel', { deltaY: -10, bubbles: true, cancelable: true }));
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      observer.disconnect(); return changes;
    });
    assert(frames <= 2, `wheel updates were not coalesced: ${frames}`);
    await page.screenshot({ path: path.join(out, 'image-viewer-mobile.png') });
    await page.keyboard.press('Escape');
    assert.equal(await viewer.isVisible(), false);
    report.steps.images = { status: 'PASS', fullResolution: true, wheelStyleMutationsFor10Events: frames, keyboard: true }; checkpoint();

    await page.evaluate(() => {
      const host = document.createElement('div'); host.className = 'peicd-mermaid-host'; host.id = 'ux-svg';
      host.innerHTML = '<svg width="800" height="400" viewBox="0 0 800 400"><rect width="800" height="400" fill="#102030"/><text x="20" y="80" fill="white">SVG clarity fixture</text></svg>';
      document.querySelector('.md-content__inner').prepend(host); window.__svgIdentity = host.firstElementChild;
      dispatchEvent(new CustomEvent('peicd:mermaid-updated'));
    });
    await page.locator('#ux-svg').click();
    const svgViewer = page.locator('dialog.peicd-mermaid-viewer'); await svgViewer.waitFor({ state: 'visible' });
    await page.waitForFunction(() => document.querySelector('.peicd-mermaid-viewer__svg') && document.querySelector('.peicd-mermaid-viewer .peicd-image-viewer__canvas').style.transform.includes('scale'));
    const width = await svgViewer.locator('svg').evaluate(node => node.style.width);
    await svgViewer.evaluate(async dialog => {
      for (let i = 0; i < 10; i++) dialog.querySelector('.peicd-image-viewer__stage').dispatchEvent(new WheelEvent('wheel', { deltaY: -5, bubbles: true, cancelable: true }));
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    assert.equal(await svgViewer.locator('svg').evaluate(node => node.style.width), width, 'zoom does not rewrite SVG layout size every event');
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(() => document.querySelector('#ux-svg svg') === window.__svgIdentity), true);
    report.steps.mermaidViewer = 'PASS: transform-only scale and original SVG restored'; checkpoint();

    const failed = await context.newPage(); activePage = failed;
    await failed.setContent('<pre class="diagram"><code>graph TD; A-->B</code></pre>');
    await failed.evaluate(() => { window.__attempts = 0; window.mermaid = { initialize() {}, async render() {
      if (++window.__attempts === 1) throw new Error('synthetic render failure');
      return { svg: '<svg width="100" height="50" viewBox="0 0 100 50"><text y="20">Recovered</text></svg>' };
    } }; });
    await failed.addScriptTag({ path: path.resolve('theme/assets/pymdownx-extras/mermaid-render-fix.js') });
    await failed.getByRole('button', { name: '重試圖表' }).click();
    await failed.waitForFunction(() => document.querySelector('.peicd-mermaid-host')?.dataset.peicdMermaidState === 'rendered');
    assert.equal(await failed.evaluate(() => window.__attempts), 2);
    report.steps.mermaidRetry = 'PASS: visible source, explicit one-click retry, no retry loop'; checkpoint();
    await failed.close(); activePage = page;
    assert.deepEqual(errors, []); report.steps.pageErrors = errors;
    await context.close();

    const errorContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await errorContext.route('**/*', route => new URL(route.request().url()).origin === new URL(server.base).origin ? route.continue() : route.abort());
    const fallbackURL = url => /\/workers\/search\.[\w.-]+\.js$/.test(new URL(url).pathname);
    await errorContext.route(fallbackURL, route => route.abort());
    const errorPage = await errorContext.newPage(); activePage = errorPage;
    await errorPage.goto(course, { waitUntil: 'networkidle' });
    const errorInput = errorPage.locator('[data-md-component="search-query"]');
    await errorInput.focus(); await errorInput.fill('title:always');
    await errorPage.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'error');
    assert.equal(await errorPage.getByRole('button', { name: '重試', exact: true }).isVisible(), true);
    await errorContext.unroute(fallbackURL);
    await errorPage.getByRole('button', { name: '重試', exact: true }).click();
    await errorPage.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'results');
    report.steps.searchRetry = 'PASS: fallback error distinct from empty results, fresh fallback succeeds on manual retry'; checkpoint();
    await errorContext.close();

    const indexContext = await browser.newContext();
    await indexContext.route('**/search/search_index.json', route => route.abort(), { times: 1 });
    const indexPage = await indexContext.newPage(); activePage = indexPage;
    await indexPage.goto(course, { waitUntil: 'networkidle' });
    await indexPage.locator('[data-md-component="search-query"]').focus();
    await indexPage.locator('[data-md-component="search-query"]').fill('會第一直覺用一');
    await indexPage.waitForFunction(() => __PEICD_SEARCH_LAZY_GUARD__.snapshot().phase === 'error');
    await indexPage.getByRole('button', { name: '重試', exact: true }).click();
    await indexPage.waitForFunction(() => window.__PEICD_SEARCH_LAZY_GUARD__?.snapshot().phase === 'results' && window.__PEICD_SEARCH_LAZY_GUARD__.snapshot().info?.query === '會第一直覺用一');
    report.steps.indexRetry = 'PASS: failed initial download can recover through explicit reload preserving q'; checkpoint();
    await indexContext.close();
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.failure = error.message;
    if (activePage && !activePage.isClosed()) {
      try { await activePage.screenshot({ path: path.join(out, 'failure.png') });
        report.state = await activePage.evaluate(() => ({ url: location.href, search: window.__PEICD_SEARCH_LAZY_GUARD__?.snapshot(), focused: document.activeElement?.outerHTML.slice(0, 200) }));
      } catch (_) { /* Preserve the primary failure. */ }
    }
    fs.writeFileSync(path.join(out, 'failure.json'), JSON.stringify(report, null, 2) + '\n');
    throw error;
  } finally { await browser.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
