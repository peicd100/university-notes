// Run against a full local MkDocs build using the existing Playwright installation.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { serve } = require('./browser_site_fixture.cjs');

async function check(browser, base, out, width) {
  const context = await browser.newContext({ viewport: { width, height: width < 600 ? 844 : 900 } });
  const page = await context.newPage();
  const errors = [];
  const requests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => requests.push(request.url()));
  await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin
    ? route.continue() : route.abort());
  try {
    // MkDocs serve keeps a live-reload request open after the page is ready.
    await page.goto(base, { waitUntil: 'load' });
    await page.waitForFunction(() => Boolean(document.querySelector('.peicd-search-controls')));
    await page.getByRole('heading', { name: '大學課程筆記' }).waitFor();
    assert(requests.every(url => !url.includes('search_index.json')));
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: path.join(out, 'home-' + width + '.png') });

    const course = page.locator('.library-course').filter({ has: page.locator('summary', { hasText: '離散' }) }).first();
    await course.locator('summary').click();
    assert(await course.getByRole('link', { name: 'L06', exact: true }).isVisible());
    await course.locator('summary').click();
    await page.locator('[data-library-search]').click();
    const query = page.locator('[data-md-component="search-query"]');
    const start = Date.now();
    await query.fill('雙射');
    await page.waitForFunction(() => window.__PEICD_SEARCH_LAZY_GUARD__.snapshot().info?.query === '雙射');
    const latency = Date.now() - start;
    await page.getByRole('combobox', { name: '搜尋學期與課程' }).selectOption('115-1/離散/');
    await page.waitForFunction(() => window.__PEICD_SEARCH_LAZY_GUARD__.snapshot().info?.scope === '115-1/離散/');
    const hit = page.locator('.md-search-result__link[href*="L06.html#"]').first();
    await hit.scrollIntoViewIfNeeded();
    const target = await hit.getAttribute('href');
    const scroll = await page.locator('.md-search__scrollwrap').evaluate(el => el.scrollTop);
    await hit.click();
    await page.waitForFunction(() => document.querySelector('#__search')?.checked === false
      && document.querySelector('.md-content__inner')?.contains(document.getElementById(decodeURIComponent(location.hash.slice(1)))));
    assert(page.url().endsWith(new URL(target, base).hash));
    await page.screenshot({ path: path.join(out, 'note-' + width + '.png') });
    if (width >= 1220) {
      const focus = page.getByRole('button', { name: '專注閱讀' });
      await focus.click();
      assert.equal(await focus.getAttribute('aria-pressed'), 'true');
      assert(!(await page.locator('.md-sidebar--primary').isVisible()));
      await focus.click();
      assert(await page.locator('.md-sidebar--primary').isVisible());
    } else {
      const toc = page.getByRole('button', { name: '打開目錄' });
      await toc.click();
      assert.equal(await page.locator('#peicd-mobile-toc-toggle').getAttribute('aria-expanded'), 'true');
      await page.locator('.peicd-toc-close').click();
    }
    await page.getByRole('button', { name: '返回搜尋結果' }).click();
    await page.waitForFunction(() => document.activeElement?.matches('.md-search-result__link'));
    assert.equal(await query.inputValue(), '雙射');
    assert.equal(await page.getByRole('combobox').inputValue(), '115-1/離散/');
    assert(Math.abs(await page.locator('.md-search__scrollwrap').evaluate(el => el.scrollTop) - scroll) <= 2);
    await page.screenshot({ animations: 'disabled', path: path.join(out, 'results-' + width + '.png') });
    await page.keyboard.press('Escape');
    await page.goBack();
    await page.waitForFunction(() => document.querySelector('.note-library') && document.querySelector('#__search')?.checked
      && document.activeElement?.matches('.md-search-result__link'));
    assert.equal(await query.inputValue(), '雙射');
    assert.equal(await page.getByRole('combobox').inputValue(), '115-1/離散/');
    assert(Math.abs(await page.locator('.md-search__scrollwrap').evaluate(el => el.scrollTop) - scroll) <= 2);
    const phrase = '反過來理解更容易';
    await query.fill('+"' + phrase + '" -不存在的詞 OR "absent fixture"');
    const precise = page.locator('.md-search-result__link[href*="L06.html#"]').filter({ hasText: phrase }).first();
    await precise.click();
    const marker = page.locator('.md-content__inner mark.peicd-search-hit').filter({ hasText: phrase }).first();
    await marker.waitFor();
    const aligned = () => page.waitForFunction(() => {
      const hit = document.querySelector('mark.peicd-search-hit');
      return hit && Math.abs(hit.getBoundingClientRect().top - document.querySelector('.md-header').offsetHeight - 12) < 3;
    });
    await aligned();
    await marker.evaluate(el => {
      const spacer = document.createElement('div');
      spacer.id = 'late-figure-test'; spacer.style.height = '240px';
      el.closest('p').before(spacer);
    });
    await aligned();
    await page.mouse.move(width / 2, 450);
    await page.mouse.wheel(0, 550);
    await page.waitForFunction(() => document.querySelector('mark.peicd-search-hit').getBoundingClientRect().bottom < 0);
    assert(!(await page.evaluate(() => window.__PEICD_PAGE_UX__.isAnchoring())));
    assert.deepEqual(errors, []);
    return { width, firstQueryMs: latency, restoredScroll: scroll, homeIndexRequests: 0 };
  } catch (error) {
    await page.screenshot({ path: path.join(out, 'failure-' + width + '.png') });
    console.error({ url: page.url(), errors, state: await page.evaluate(() => {
      const state = window.__PEICD_SEARCH_LAZY_GUARD__?.snapshot();
      return { checked: document.querySelector('#__search')?.checked, active: document.activeElement?.className,
        phase: state?.phase, query: state?.info?.query, scope: state?.info?.scope,
        saved: Object.entries(sessionStorage).filter(([key]) => key.startsWith('peicd-result-trip:'))
          .map(([, value]) => JSON.parse(value).origin), history: history.state };
    }) });
    throw error;
  } finally {
    await context.close();
  }
}

(async () => {
  const out = process.env.UX_ARTIFACTS_DIR;
  fs.mkdirSync(out, { recursive: true });
  const server = process.env.UX_BASE_URL ? { base: process.env.UX_BASE_URL, close: async () => {} }
    : await serve(process.env.UX_SITE_DIR);
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_EXE, headless: true });
  try {
    for (const width of [1440, 390]) console.log(await check(browser, server.base, out, width));
  } finally {
    await browser.close();
    await server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
