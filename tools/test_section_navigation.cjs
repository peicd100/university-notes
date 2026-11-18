// Run against a local MkDocs build to exercise the theme's normal entry points.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { serve } = require('./browser_site_fixture.cjs');
if (!process.env.UX_SITE_DIR || !process.env.UX_ARTIFACTS_DIR) throw new Error('Set UX_SITE_DIR and UX_ARTIFACTS_DIR');
const out = path.resolve(process.env.UX_ARTIFACTS_DIR);
fs.mkdirSync(out, { recursive: true });

async function settled(page) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function aligned(page, id) {
  const position = await page.locator('#' + id).evaluate(heading => {
    const header = document.querySelector('[data-md-component="header"]');
    const offset = Math.max(0, header?.getBoundingClientRect().bottom || 0) + 12;
    return { top: heading.getBoundingClientRect().top, offset: Math.max(offset, parseFloat(getComputedStyle(heading).scrollMarginTop) || 0) };
  });
  assert(Math.abs(position.top - position.offset) <= 3, JSON.stringify({ id, ...position }));
}

(async () => {
  const server = await serve(process.env.UX_SITE_DIR);
  const browser = await chromium.launch({ headless: true });
  const results = {};
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const errors = [];
    await context.route('**/*', route => route.request().url().startsWith(server.base) ? route.continue() : route.abort());
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    for (const width of [1440, 768, 390]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(server.base, { waitUntil: 'networkidle' });
      const navigation = page.locator('[data-peicd-section-jump]');
      const up = navigation.getByRole('button', { name: '上一個 H2' });
      const down = navigation.getByRole('button', { name: '下一個 H2' });
      await navigation.waitFor({ state: 'visible' });
      assert.equal(await navigation.count(), 1);
      assert.equal(await up.locator('svg').count(), 1);
      assert.equal(await down.locator('svg').count(), 1);
      assert.equal(await up.isDisabled(), true);
      await down.click(); await settled(page); await aligned(page, 'first');
      assert.equal(await up.isDisabled(), true);
      await down.click(); await settled(page); await aligned(page, 'second');
      await up.focus(); await page.keyboard.press('Enter'); await settled(page); await aligned(page, 'first');
      // Rapid requests use the last destination even when the page ends before an H2 can align.
      await down.evaluate(button => { button.click(); button.click(); button.click(); });
      await settled(page);
      assert.equal(await down.isDisabled(), true);
      await up.click(); await settled(page); await aligned(page, 'third');
      await page.evaluate(() => window.scrollBy({ top: 150, behavior: 'instant' }));
      await settled(page);
      await up.click(); await settled(page); await aligned(page, 'third');
      const box = await navigation.boundingBox();
      assert(box.x >= width - 90 && box.x + box.width <= width);
      assert(Math.abs(box.y + box.height / 2 - 450) <= 2);
      const buttonBox = await up.boundingBox();
      assert.equal(buttonBox.width, 33);
      assert.equal(buttonBox.width, buttonBox.height);
      assert.equal(await up.evaluate(button => getComputedStyle(button).borderRadius), '9px');
      for (const selector of ['[data-peicd-scroll-top]', '[data-peicd-scroll-bottom]']) {
        const scale = await page.locator(selector).evaluate(button => {
          const box = button.getBoundingClientRect();
          return { x: box.width / button.offsetWidth, y: box.height / button.offsetHeight };
        });
        assert(Math.abs(scale.x - 0.75) < 0.01 && Math.abs(scale.y - 0.75) < 0.01, JSON.stringify({ selector, scale }));
      }
      const top = page.locator('[data-peicd-scroll-top]');
      const topButton = await top.boundingBox();
      const bottomButton = await page.locator('[data-peicd-scroll-bottom]').boundingBox();
      const headerBottom = await page.locator('[data-md-component="header"]').evaluate(header => header.getBoundingClientRect().bottom);
      assert(Math.abs(topButton.x - bottomButton.x) <= 1);
      assert(Math.abs(topButton.width - bottomButton.width) <= 1);
      assert(Math.abs(topButton.height - bottomButton.height) <= 1);
      assert(Math.abs(topButton.y - headerBottom - (900 - bottomButton.y - bottomButton.height)) <= 2);
      assert.equal(await top.innerText(), '');
      assert.equal(await top.locator('svg').count(), 1);
      assert.equal(await page.locator('[data-md-component="top"]').count(), 0);
      assert.equal(await top.evaluate(button => getComputedStyle(button).opacity), '1');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.screenshot({ path: path.join(out, 'section-buttons-' + width + '.png') });
      results[width] = 'PASS: H2 navigation, keyboard, repeated clicks, manual scroll, 1.5x controls, rounded arrows and symmetric icon-only top/bottom controls';
    }
    await page.locator('[data-peicd-scroll-bottom]').click();
    await page.waitForFunction(() => scrollY >= document.scrollingElement.scrollHeight - innerHeight - 3);
    assert.equal(await page.locator('[data-peicd-scroll-top]').isVisible(), true);
    await page.locator('[data-peicd-scroll-top]').click();
    await page.waitForFunction(() => scrollY <= 2);
    assert.equal(await page.locator('[data-peicd-scroll-top]').isVisible(), true);
    await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'instant' }));
    await settled(page);
    assert.equal(await page.locator('[data-peicd-scroll-top]').evaluate(button => getComputedStyle(button).opacity), '1');
    await page.locator('[data-peicd-scroll-top]').focus();
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => scrollY <= 2);
    results.topAndBottom = 'PASS: click and keyboard actions, top remains visible at start/end and while scrolling down';
    // Material instant navigation keeps the current JS window and rebinds fresh buttons.
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(server.base, { waitUntil: 'networkidle' });
    await page.evaluate(() => { window.__sectionWindow = true; });
    await page.locator('article').getByRole('link', { name: 'Empty page', exact: true }).click();
    await page.waitForURL(url => url.pathname.endsWith('/empty.html'));
    await settled(page);
    assert.equal(await page.evaluate(() => window.__sectionWindow), true);
    assert.equal(await page.locator('[data-peicd-section-jump]').isVisible(), false);
    assert.equal(await page.locator('[data-peicd-scroll-top]').isVisible(), true);
    assert.equal(await page.locator('[data-peicd-scroll-top]').count(), 1);
    await page.locator('article').getByRole('link', { name: 'Back', exact: true }).click();
    await page.waitForURL(url => !url.pathname.endsWith('/empty.html'));
    await page.locator('[data-peicd-section-jump]').waitFor({ state: 'visible' });
    assert.equal(await page.locator('[data-peicd-section-jump]').count(), 1);
    await page.locator('[data-peicd-section-direction="down"]').click();
    await settled(page); await aligned(page, 'first');
    assert.equal(await page.evaluate(() => window.__sectionWindow), true);
    results.instantNavigation = 'PASS: empty page hides controls, return navigation rebinds, one group per page';
    assert.deepEqual(await page.locator('article .admonition :is(h4,h5,h6)').evaluateAll(nodes => nodes.map(node => node.tagName)), ['H4', 'H5', 'H6']);
    assert.equal(await page.locator('article details h4').textContent(), 'Details title');
    results.blockHeadings = 'PASS: actual theme build includes corrected H4/H5 and nested H6';
    await page.goto(server.base + 'L06.html', { waitUntil: 'networkidle' });
    await page.locator('[data-peicd-section-jump]').waitFor({ state: 'visible' });
    const targets = await page.locator('article h2').evaluateAll(nodes => nodes.filter(node => node.getClientRects().length).slice(0, 3).map(node => node.id));
    assert(targets.length === 3);
    for (const id of targets) {
      await page.locator('[data-peicd-section-direction="down"]').click();
      await settled(page); await aligned(page, id);
    }
    assert.equal(await page.locator('[data-peicd-scroll-bottom]').count(), 1);
    await page.emulateMedia({ media: 'print' });
    assert.equal(await page.locator('[data-peicd-section-jump]').isVisible(), false);
    assert.equal(await page.locator('[data-peicd-scroll-top]').isVisible(), false);
    assert.equal(await page.locator('[data-peicd-scroll-bottom]').isVisible(), false);
    results.actualL06 = 'PASS: actual note, first three H2 destinations, existing bottom control and print suppression';
    assert.deepEqual(errors, []);
    results.pageErrors = errors;
    fs.writeFileSync(path.join(out, 'section-navigation-results.json'), JSON.stringify(results, null, 2) + '\n');
    console.log(JSON.stringify(results, null, 2));
  } finally {
    await browser.close();
    await server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
