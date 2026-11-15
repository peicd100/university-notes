// Real built-site regression: repeated search selection and late layout shifts.
// NAV_CASE=repeat|layout; NAV_OUT captures checkpoint/terminal evidence.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE);
const { serve } = require('./browser_site_fixture.cjs');
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const site = process.env.UX_SITE_DIR || '.peicd100/codex/tmp/website-ux-20261115/build-4/site';
const out = process.env.NAV_OUT || '.peicd100/codex/tmp/search-navigation-fix-20261115/browser';
const which = process.env.NAV_CASE || 'all';
const articlePath = 'md/115-1/' + encodeURIComponent('硬體描述語言') + '/L03.html';
const targetId = '3-traffic-light紅綠燈直覺';
fs.mkdirSync(out, { recursive: true });
const result = { case: which, realCDN: process.env.NAV_ALLOW_CDN === '1', sourceOverlay: process.env.UX_SOURCE_OVERLAY === '1', pageErrors: [], cycles: [], shifts: [], history: [], runtimes: [] };
const save = (name, data) => fs.writeFileSync(path.join(out, name), JSON.stringify(data, null, 2));
async function openSearch(page, query) {
  const input = page.locator('[data-md-component="search-query"]');
  const toggle = page.locator('label.md-header__button[for="__search"]');
  if (await toggle.isVisible()) await toggle.click(); else await input.focus();
  await input.fill(query);
}
(async () => {
  save('checkpoint.json', { pid: process.pid, started: new Date().toISOString(), site, which, sourceOverlay: result.sourceOverlay,
    scriptSha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex') });
  const server = await serve(site);
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_EXE });
  try {
    for (const width of (process.env.NAV_WIDTH ? [Number(process.env.NAV_WIDTH)] : [1440, 390])) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      // Default deterministic failure mode; optional real MathJax CDN smoke.
      await context.route('**/*', r => {
        const url = new URL(r.request().url());
        return url.origin === new URL(server.base).origin || (result.realCDN && url.hostname === 'cdn.jsdelivr.net') ? r.continue() : r.abort();
      });
      await context.addInitScript(() => {
        window.__viewportCalls = []; window.__navigationSelections = [];
        document.addEventListener('click', event => {
          if (event.target.closest?.('[data-md-component="search-result"] a[href]')) {
            __navigationSelections.push({ y: scrollY, stateY: history.state?.y, hash: location.hash });
          }
        }, true);
        const original = window.scrollTo.bind(window);
        window.scrollTo = (...args) => { __viewportCalls.push({ time: performance.now(), args }); return original(...args); };
      });
      const page = await context.newPage(); page.setDefaultTimeout(12000);
      page.on('pageerror', e => result.pageErrors.push(e.message));
      if (which !== 'layout') {
        await page.goto(server.base + 'blog/index.html', { waitUntil: 'networkidle' });
        for (let cycle = 1; cycle <= 4; cycle++) {
          const chosenId = cycle === 4 ? '4-目前先不要超前學什麼' : targetId;
          await openSearch(page, cycle === 4 ? '目前先不要超前' : 'Traffic Light');
          const link = page.locator(cycle === 4 ? '.md-search-result__link[href*="L03.html#4-"]' : '.md-search-result__link[href*="L03.html#3-traffic-light"]').first();
          await link.waitFor({ state: 'visible' });
          if (cycle === 3) { await link.focus(); await page.keyboard.press('Enter'); } else await link.click();
          await page.waitForURL(url => decodeURIComponent(url.pathname).endsWith('md/115-1/硬體描述語言/L03.html'));
          await page.waitForFunction(() => window.__PEICD_MATH__);
          await page.waitForTimeout(500);
          const snapshot = await page.evaluate(({ cycle, targetId }) => ({ cycle,
            closed: !document.querySelector('#__search').checked,
            hash: decodeURIComponent(location.hash), historyY: history.state?.y, scrollY,
            beforeClick: __navigationSelections.at(-1),
            top: document.getElementById(targetId).getBoundingClientRect().top,
            identity: document.querySelector('.md-content__inner').dataset.navigationTest || null,
            marks: document.getElementById(targetId).querySelectorAll('mark.peicd-search-hit').length
          }), { cycle, targetId: chosenId });
          result.cycles.push({ width, ...snapshot });
          assert(snapshot.closed, `width ${width}, search ${cycle}: result must close search`);
          assert.equal(snapshot.hash, '#' + chosenId, 'requested anchor must not be overwritten by TOC tracking');
          if (cycle === 4) assert(snapshot.marks > 0, 'second query on same math page refreshes landing highlights');
          if (cycle > 1) assert.equal(snapshot.identity, 'same-root', 'same-page result retains content/MathJax DOM');
          await page.evaluate(() => { document.querySelector('.md-content__inner').dataset.navigationTest = 'same-root'; });
        }
        if (result.realCDN) {
          await page.waitForFunction(() => window.MathJax?.version === '3.2.2' && document.querySelector('.md-content__inner mjx-container'));
          assert(await page.evaluate(() => window.__PEICD_MATH__.renderAll()), 'compact real MathJax fixture renders successfully');
          await page.waitForTimeout(160);
          result.runtimes.push(await page.evaluate(width => ({ width, mathVersion: MathJax.version,
            math: document.querySelectorAll('.md-content__inner mjx-container').length,
            diagramInputs: document.querySelectorAll('pre.diagram,.peicd-mermaid-host').length,
            diagrams: document.querySelectorAll('.peicd-mermaid-host.is-rendered').length
          }), width));
        }
        const latest = result.cycles.at(-1);
        // Search focus may change the viewport. Observe Material's actual saved
        // state at selection, not an older screenshot before opening search.
        const priorY = latest.beforeClick.stateY;
        const forwardY = await page.evaluate(() => history.state?.y);
        await page.goBack(); await page.waitForTimeout(250);
        const back = await page.evaluate(() => ({ y: scrollY, stateY: history.state?.y, restoring: window.__PEICD_PAGE_UX__?.isRestoring() }));
        result.history.push({ width, direction: 'back', expected: priorY, ...back });
        assert(Math.abs(back.y - priorY) <= 2, 'Back retains Material saved scroll offset');
        await page.goForward(); await page.waitForTimeout(250);
        const forward = await page.evaluate(() => ({ y: scrollY, stateY: history.state?.y }));
        result.history.push({ width, direction: 'forward', expected: forwardY, ...forward });
        assert(Math.abs(forward.y - forwardY) <= 2, 'Forward retains Material saved scroll offset');
        result.cycles.push({ width, historyOffsetRestoration: true });
      }
      if (which !== 'repeat') {
        await page.goto(server.base + articlePath + '#' + encodeURIComponent(targetId), { waitUntil: 'networkidle' });
        await page.waitForFunction(() => window.__PEICD_MATH__);
        await page.waitForTimeout(600);
        await page.evaluate(targetId => {
          const root = document.querySelector('.md-content__inner'), target = document.getElementById(targetId);
          // Worst-case fixture: native anchoring unavailable (e.g. excluded math regions).
          // Production CSS is not changed. Only the explicit navigation must be maintained.
          root.style.overflowAnchor = 'none';
          const spacer = document.createElement('div'); spacer.id = 'late-layout-fixture';
          spacer.style.overflowAnchor = 'none'; target.before(spacer);
          window.__landingPaints = [];
          window.__landingProbe = new ResizeObserver(() => {
            if (window.__PEICD_PAGE_UX__?.isAnchoring()) __landingPaints.push({
              top: target.getBoundingClientRect().top,
              offset: (document.querySelector('.md-header')?.offsetHeight || 56) + 12
            });
          });
          __landingProbe.observe(root);
          const offset = (document.querySelector('.md-header')?.offsetHeight || 56) + 12;
          window.scrollTo({ top: target.getBoundingClientRect().top + scrollY - offset, behavior: 'instant' });
        }, targetId);
        for (const height of [280, 40, 390, 0]) {
          await page.evaluate(height => { document.getElementById('late-layout-fixture').style.height = height + 'px'; }, height);
          await page.waitForTimeout(140);
          const snapshot = await page.evaluate(targetId => ({
            top: document.getElementById(targetId).getBoundingClientRect().top,
            offset: (document.querySelector('.md-header')?.offsetHeight || 56) + 12,
            hash: decodeURIComponent(location.hash)
          }), targetId);
          result.shifts.push({ width, height, ...snapshot });
          assert(Math.abs(snapshot.top - snapshot.offset) <= 3, `width ${width}: late layout ${height} moved destination to ${snapshot.top}`);
          assert.equal(snapshot.hash, '#' + targetId);
        }
        const paints = await page.evaluate(() => __landingPaints);
        assert(paints.length >= 4 && paints.every(p => Math.abs(p.top - p.offset) <= 3), 'correct before paint, not one frame after every resize');
        result.shifts.push({ width, beforePaintCorrections: paints.length, maxDrift: Math.max(...paints.map(p => Math.abs(p.top - p.offset))) });
        const settled = await page.evaluate(() => __viewportCalls.length);
        await page.waitForTimeout(350);
        assert.equal(await page.evaluate(() => __viewportCalls.length), settled, 'no polling or repeated viewport scroll when layout is stable');
        await page.mouse.move(width / 2, 500); await page.mouse.wheel(0, 600); await page.waitForTimeout(180);
        const manual = await page.evaluate(() => ({ y: scrollY, calls: __viewportCalls.length }));
        await page.evaluate(() => { document.getElementById('late-layout-fixture').style.height = '240px'; });
        await page.waitForTimeout(220);
        const after = await page.evaluate(() => ({ y: scrollY, calls: __viewportCalls.length }));
        assert(Math.abs(after.y - manual.y) <= 2, 'do not pull reader back after manual scrolling');
        assert.equal(after.calls, manual.calls, 'no viewport correction after user intent');
        result.shifts.push({ width, manualScrollRespected: true });
        await page.evaluate(targetId => window.__PEICD_PAGE_UX__.navigateToHash('#' + targetId), targetId);
        await page.waitForTimeout(80); await page.keyboard.press('PageDown'); await page.waitForTimeout(420);
        const keyboard = await page.evaluate(() => ({ y: scrollY, calls: __viewportCalls.length }));
        await page.evaluate(() => { document.getElementById('late-layout-fixture').style.height = '80px'; });
        await page.waitForTimeout(220);
        assert.equal(await page.evaluate(() => __viewportCalls.length), keyboard.calls, 'keyboard scroll cancels viewport correction');
        assert(Math.abs(await page.evaluate(() => scrollY) - keyboard.y) <= 2);
        result.shifts.push({ width, keyboardScrollRespected: true });
        await page.evaluate(targetId => {
          // Integration boundary: Danger owns its link and cancels native bubbling.
          const link = document.createElement('a'); link.className = 'peicd-danger-link';
          link.id = 'custom-scroll-owner'; link.href = '#' + targetId; link.textContent = 'Custom danger owner';
          link.addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); window.__customOwnerRan = true; });
          document.querySelector('.md-content__inner').prepend(link);
        }, targetId);
        await page.locator('#custom-scroll-owner').click();
        assert(await page.evaluate(() => __customOwnerRan && !__PEICD_PAGE_UX__.isAnchoring()), 'do not seize Danger custom-scroll ownership');
        result.shifts.push({ width, customScrollOwnerRespected: true });
      }
      await context.close();
    }
    assert.deepEqual(result.pageErrors, []);
    result.status = 'PASS';
  } catch (error) {
    result.status = 'FAIL'; result.failure = error.message; process.exitCode = 1;
  } finally {
    await browser.close(); await server.close(); save('result.json', result);
    save('terminal.json', { status: result.status, completed: new Date().toISOString() });
    console.log(JSON.stringify({ status: result.status, case: which, cycles: result.cycles.length, shifts: result.shifts.length, failure: result.failure }, null, 2));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
