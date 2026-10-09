// End-to-end search regression against a built MkDocs site under a Pages subpath.
// PLAYWRIGHT_MODULE / CHROMIUM_EXE select existing installations.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { performance } = require('node:perf_hooks');
const { LiteralSearch } = require('../theme/assets/pymdownx-extras/search-core.js');
const site = path.resolve(process.env.SEARCH_SITE_DIR || 'site');
const artifacts = path.resolve(process.env.SEARCH_ARTIFACTS_DIR || '.peicd100/codex/tmp/search-run');
const prefix = '/university-notes/';
const phrase = '會第一直覺用一';
const articlePath = 'md/Verilog/' + encodeURIComponent('雙邊緣觸發') + '.html';
const isTarget = href => {
  const url = new URL(href);
  return url.pathname.endsWith('/' + articlePath) && decodeURIComponent(url.hash) === '#解題';
};
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.xml': 'application/xml', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.woff2': 'font/woff2' };

async function startServer() {
  const server = http.createServer((req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      if (!pathname.startsWith(prefix)) { res.writeHead(404); res.end(); return; }
      const relative = decodeURIComponent(pathname.slice(prefix.length));
      let file = path.resolve(site, relative || 'index.html');
      if (!file.startsWith(site + path.sep)) { res.writeHead(403); res.end(); return; }
      if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
      if (path.basename(file) === 'sitemap.xml') {
        // Like mkdocs serve, point sitemap entries at this server, including its
        // ephemeral port. Material's hostname normalization does not fix ports.
        const xml = fs.readFileSync(file, 'utf8').replaceAll('https://peicd100.github.io/university-notes/', `http://${req.headers.host}${prefix}`);
        res.end(xml);
      } else fs.createReadStream(file).pipe(res);
    } catch (_) { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return { server, base: `http://127.0.0.1:${server.address().port}${prefix}` };
}

async function waitForPhrase(page) {
  await page.waitForFunction(value => [...document.querySelectorAll('.md-search-result__list mark')]
    .some(mark => mark.textContent === value), phrase);
  const first = page.locator('.md-search-result__item').first();
  const hrefs = await first.locator('a.md-search-result__link').evaluateAll(anchors => anchors.map(anchor => anchor.href));
  assert.ok(hrefs.some(isTarget), 'first result must contain the exact target section');
}

(async () => {
  fs.mkdirSync(artifacts, { recursive: true });
  const index = JSON.parse(fs.readFileSync(path.join(site, 'search/search_index.json'), 'utf8'));
  const start = performance.now(), engine = new LiteralSearch(index.docs);
  const result = { sections: index.docs.length, literalSetupMs: +(performance.now() - start).toFixed(2), timings: {} };
  for (const query of [phrase, '雙邊緣 posedge', 'ＡＬＷＡＹＳ 第一直覺', '中文', 'a']) {
    const before = performance.now(), found = engine.search(query);
    result.timings[query] = { ms: +(performance.now() - before).toFixed(2), pages: found.items.length };
    if (query === phrase || query === '雙邊緣 posedge') assert.ok(isTarget('https://example.test/' + found.items[0][0].location));
  }
  const { server, base } = await startServer();
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXE ? { executablePath: process.env.CHROMIUM_EXE } : {}) });
  const errors = [], requests = [];
  let activePage;
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await context.addInitScript(() => {
      window.__searchQueries = [];
      const post = Worker.prototype.postMessage;
      Worker.prototype.postMessage = function (message, ...args) {
        if (message?.type === 2) window.__searchQueries.push(message.data);
        return post.call(this, message, ...args);
      };
    });
    // Search has no external service dependency. Keep unrelated CDN work out of this test.
    await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
    const page = await context.newPage();
    activePage = page;
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push(request.url()));
    await page.goto(base, { waitUntil: 'networkidle' });
    assert.equal(requests.filter(url => url.includes('/search/search_index.')).length, 0, 'index stays lazy');
    assert.equal(requests.filter(url => url.includes('/workers/search')).length, 0, 'search worker stays lazy');
    const input = page.locator('[data-md-component="search-query"]');
    await input.focus(); await input.fill(phrase); await waitForPhrase(page);
    assert.equal(requests.filter(url => url.includes('/search/search_index.')).length, 1);
    assert.equal(requests.filter(url => url.includes('/workers/search-peicd.js')).length, 1);
    assert.equal(requests.filter(url => /\/search\.[\w.-]+\.js/.test(new URL(url).pathname)).length, 0, 'plain Chinese needs no Lunr worker');
    await page.screenshot({ path: path.join(artifacts, 'search-desktop.png') });
    await input.press('Enter');
    await page.waitForURL(url => isTarget(url.href));
    await page.waitForFunction(() => document.querySelector('.md-content__inner')?.textContent.includes('會第一直覺用一'));
    assert.equal(await page.locator('#__search').isChecked(), false);
    result.keyboardSectionJump = 'PASS';

    // Navigate away through Material's actual instant-navigation link, then search again.
    await page.evaluate(() => { window.__searchNavigationMarker = true; });
    const away = page.locator('.md-tabs__link').first();
    const awayURL = new URL(await away.getAttribute('href'), page.url()).href;
    assert.equal(new URL(awayURL).origin, new URL(base).origin);
    await away.click();
    await page.waitForURL(awayURL);
    await input.focus(); await input.fill(phrase); await waitForPhrase(page);
    assert.equal(await page.evaluate(() => !!window.__searchNavigationMarker), true, 'actual instant navigation retains the window');
    assert.equal(requests.filter(url => url.includes('/search/search_index.')).length, 1, 'instant navigation reuses index');
    assert.equal(requests.filter(url => url.includes('/workers/search-peicd.js')).length, 1, 'instant navigation reuses worker');
    result.instantNavigation = 'PASS';

    await input.fill('雙邊緣 posedge');
    await page.waitForFunction(() => [...document.querySelectorAll('.md-search-result__list mark')].some(mark => mark.textContent.toLowerCase() === 'posedge'));
    const andHrefs = await page.locator('.md-search-result__item').first().locator('a.md-search-result__link').evaluateAll(anchors => anchors.map(anchor => anchor.href));
    assert.ok(andHrefs.some(isTarget));
    await input.fill('ＡＬＷＡＹＳ 第一直覺');
    await page.waitForFunction(() => [...document.querySelectorAll('.md-search-result__list mark')].some(mark => mark.textContent === '第一直覺'));
    await input.fill('第一直覺 絕不應存在的檢驗詞');
    await page.waitForFunction(() => document.querySelector('.md-search-result__list')?.children.length === 0);
    result.andMixedWidthAndNoPartialMatches = 'PASS';

    const queriesBeforeIME = await page.evaluate(() => window.__searchQueries.length);
    const urlBeforeIME = page.url();
    await input.evaluate((element, value) => {
      element.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
      element.value = value;
      element.dispatchEvent(new InputEvent('input', { bubbles: true, isComposing: true }));
      for (const type of ['keydown', 'keyup']) element.dispatchEvent(new KeyboardEvent(type, { key: 'Enter', code: 'Enter', bubbles: true, isComposing: true }));
    }, phrase);
    assert.equal(await page.evaluate(() => window.__searchQueries.length), queriesBeforeIME, 'IME intermediate input is not queried');
    assert.equal(page.url(), urlBeforeIME, 'IME Enter does not select a search result');
    await input.evaluate(element => {
      element.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true }));
      element.dispatchEvent(new InputEvent('input', { bubbles: true, isComposing: false }));
      element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    });
    await waitForPhrase(page);
    assert.equal(await page.evaluate(() => window.__searchQueries.length), queriesBeforeIME + 1, 'final IME value is queried exactly once');
    result.inputPasteAndIMECommit = 'PASS';

    await input.fill('posedge*');
    await page.waitForFunction(() => [...document.querySelectorAll('.md-search-result__list mark')].some(mark => /^posedge$/i.test(mark.textContent)));
    assert.ok(requests.some(url => /\/search\.[\w.-]+\.js/.test(new URL(url).pathname)), 'original worker is loaded only for explicit Lunr syntax');
    await input.fill(phrase); await waitForPhrase(page);
    result.advancedLunrAndReturnToChinese = 'PASS';
    await input.press('Escape');
    assert.equal(await page.locator('#__search').isChecked(), false);
    await page.keyboard.press('/');
    assert.equal(await input.evaluate(element => document.activeElement === element), true);
    result.keyboardOpenClose = 'PASS';

    const shared = await context.newPage();
    activePage = shared;
    shared.on('request', request => requests.push(request.url()));
    shared.on('pageerror', error => errors.push(error.message));
    // The existing root index.md redirects to blog/index.html and drops query
    // parameters. Real search.share links point at the current article instead.
    await shared.goto(base + articlePath + '?q=' + encodeURIComponent(phrase), { waitUntil: 'networkidle' });
    await waitForPhrase(shared);
    assert.equal(await shared.locator('[data-md-component="search-query"]').inputValue(), phrase);
    result.sharedQuery = 'PASS';
    await shared.close();

    const mobile = await context.newPage();
    activePage = mobile;
    await mobile.setViewportSize({ width: 390, height: 844 });
    mobile.on('pageerror', error => errors.push(error.message));
    await mobile.goto(base + articlePath, { waitUntil: 'networkidle' });
    await mobile.locator('label.md-header__button[for="__search"]').click();
    await mobile.locator('[data-md-component="search-query"]').fill(phrase);
    await waitForPhrase(mobile);
    // The search panel animates open; a fast worker can finish before its CSS
    // transform settles. Check final layout, not an intermediate animation frame.
    await mobile.waitForFunction(() => {
      const bounds = document.querySelector('.md-search__inner').getBoundingClientRect();
      const content = document.querySelector('.md-search__scrollwrap');
      return bounds.left >= -1 && bounds.right <= window.innerWidth + 1 && content.scrollWidth <= content.clientWidth + 1;
    }, null, { timeout: 5000 });
    await mobile.screenshot({ path: path.join(artifacts, 'search-mobile.png') });
    result.mobile390 = 'PASS';
    result.lazyRequests = { index: 1, literalWorker: 1, stockWorkerOnDemand: true };
    assert.deepEqual(errors, []);
    result.pageErrors = errors;
    fs.writeFileSync(path.join(artifacts, 'browser-result.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    const diagnostic = { ...result, error: error.message, requests, pageErrors: errors };
    if (activePage && !activePage.isClosed()) {
      diagnostic.url = activePage.url();
      try {
        diagnostic.ui = await activePage.evaluate(() => ({
          query: document.querySelector('[data-md-component="search-query"]')?.value,
          meta: document.querySelector('.md-search-result__meta')?.textContent,
          marks: [...document.querySelectorAll('.md-search-result__list mark')].map(mark => mark.textContent),
          queries: window.__searchQueries,
          searchOpen: document.getElementById('__search')?.checked,
          panel: document.querySelector('.md-search__inner')?.getBoundingClientRect().toJSON(),
          viewport: window.innerWidth,
          resultWidths: [...document.querySelectorAll('.md-search__scrollwrap')].map(element => [element.clientWidth, element.scrollWidth])
        }));
        await activePage.screenshot({ path: path.join(artifacts, 'failure.png') });
      } catch (diagnosticError) { diagnostic.uiUnavailable = diagnosticError.message; }
    }
    fs.writeFileSync(path.join(artifacts, 'failure.json'), JSON.stringify(diagnostic, null, 2) + '\n');
    console.error('Failure UI:', JSON.stringify(diagnostic.ui));
    throw error;
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
