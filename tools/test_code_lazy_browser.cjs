const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict'), fs = require('node:fs');
const { serve } = require('./browser_site_fixture.cjs');
if (!process.env.CODE_SITE_DIR || !process.env.CODE_RESULT) throw new Error('Set CODE_SITE_DIR and CODE_RESULT');
(async () => {
  const server = await serve(process.env.CODE_SITE_DIR), browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXE ? { executablePath: process.env.CHROMIUM_EXE } : {}) });
  const result = {};
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } }), errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const plain = server.base + 'plain.html';
    await page.goto(plain, { waitUntil: 'networkidle' });
    result.totalBlocks = await page.locator('pre > code').count();
    result.initialMounted = await page.locator('[data-clipboard-target]').count();
    assert.equal(result.totalBlocks, 60); assert(result.initialMounted < 10);
    const last = page.locator('.highlight').last();
    await last.scrollIntoViewIfNeeded();
    await last.locator('[data-clipboard-target]').waitFor();
    const hash = await last.locator('code > [id]').first().getAttribute('id');
    const lineText = node => {
      let text = node.textContent;
      for (let next = node.nextSibling; next; next = next.nextSibling) {
        if (next.nodeType === 1 && next.id?.startsWith('__codelineno-')) break;
        text += next.textContent;
      }
      return text;
    };
    await page.evaluate(() => {
      // Emulate ClipboardJS's execCommand boundary, never touch the OS clipboard.
      document.execCommand = command => {
        if (command === 'copy') { window.__testCopy = getSelection().toString(); return true; }
        return false;
      };
    });
    await last.locator('[data-clipboard-target]').click();
    assert.match(await page.evaluate(() => window.__testCopy), /block 59/);
    assert.match(await page.evaluate(() => window.__testCopy), /copy remains complete/);
    result.copy = 'PASS: complete code selected; OS clipboard untouched';
    await page.goto('about:blank');
    await page.goto(plain + '#' + hash, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('[data-clipboard-target]').count(), 60);
    assert.equal(await page.evaluate(() => JSON.parse(document.querySelector('#__config').textContent).features.includes('content.lazy')), false);
    assert.match(await page.locator('[id="' + hash + '"]').evaluate(lineText), /block 59/);
    result.directLineAnchor = 'PASS: conservative eager path preserves numeric line identity';
    await page.goto(plain, { waitUntil: 'networkidle' });
    await page.evaluate(() => { window.__windowToken = 'plain'; });
    await page.locator('.md-content__inner').getByRole('link', { name: 'Annotation page', exact: true }).click();
    await page.waitForURL(url => url.pathname.endsWith('/annotated.html'));
    assert.equal(await page.evaluate(() => window.__windowToken), undefined);
    assert.equal(await page.evaluate(() => JSON.parse(document.querySelector('#__config').textContent).features.includes('content.lazy')), false);
    await page.waitForFunction(() => document.querySelector('.md-annotation'));
    assert.match(await page.locator('.md-content__inner').innerText(), /Annotation text remains available/);
    result.annotationNavigation = 'PASS: native annotation setup, conservative full navigation only for compatibility pages';
    await page.evaluate(() => { window.__windowToken = 'annotation'; });
    await page.getByRole('link', { name: 'Return to plain', exact: true }).click();
    await page.waitForURL(url => url.pathname.endsWith('/plain.html'));
    assert.equal(await page.evaluate(() => window.__windowToken), undefined);
    assert.equal(await page.evaluate(() => JSON.parse(document.querySelector('#__config').textContent).features.includes('content.lazy')), true);
    result.lazyRestored = true;
    await page.evaluate(() => { window.__PEICD_SEARCH_TARGET__ = { path: location.pathname, hash: '#hidden-target', query: 'needleterm' }; });
    await page.getByRole('link', { name: 'Open hidden section', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('#hidden-target')?.closest('details').open &&
      document.querySelector('mark.peicd-search-hit')?.textContent === 'needleterm');
    result.searchLanding = 'PASS: collapsed details opened and bounded text highlight applied';
    await page.evaluate(hash => {
      const link = document.createElement('a'); link.href = '#' + hash; link.textContent = 'Jump to last code line';
      document.querySelector('.md-content__inner').prepend(link); window.__windowToken = 'lazy';
    }, hash);
    await page.getByRole('link', { name: 'Jump to last code line' }).click();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.evaluate(() => window.__windowToken), undefined);
    assert.equal(await page.locator('[data-clipboard-target]').count(), 60);
    assert.match(await page.locator('[id="' + hash + '"]').evaluate(lineText), /block 59/);
    result.samePageLineAnchor = true;
    const before = await page.locator('pre > code').allTextContents();
    await page.emulateMedia({ media: 'print' });
    assert.deepEqual(await page.locator('pre > code').allTextContents(), before);
    assert.equal(await page.locator('pre > code:visible').count(), 60);
    result.print = 'PASS: all server-rendered code remains present and visible';
    assert.deepEqual(errors, []); result.pageErrors = errors;
    fs.writeFileSync(process.env.CODE_RESULT, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify(result, null, 2));
  } finally { await browser.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
