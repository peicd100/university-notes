// Same-machine cold-context A/B, CPU x4. Not field CWV, INP or a real phone test.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { serve } = require('./browser_site_fixture.cjs');
if (!process.env.UX_BASELINE_DIR || !process.env.UX_SITE_DIR || !process.env.PERF_OUT) throw new Error('Set UX_BASELINE_DIR, UX_SITE_DIR, PERF_OUT');
assert.notEqual(process.env.UX_SOURCE_OVERLAY, '1', 'No source overlay in final performance results');
assert(!process.env.UX_HTML_OVERLAY_DIR, 'No HTML overlay in final performance results');
const out = path.resolve(process.env.PERF_OUT); fs.mkdirSync(out, { recursive: true });
const pages = ['blog/index.html', 'md/114-2/科技_計算機結構/ch 2.html', 'md/115-1/離散/L03.html'];
const report = { conditions: { cpu: 4, viewport: '1440x900 DPR1', cache: 'fresh browser context; cache disabled',
  network: 'localhost, uncompressed; external resources blocked equally in both arms',
  samples: 3, note: 'No claims about production network, real-device GPU memory, field INP or p75 CWV' }, samples: [], medians: {} };
if (process.env.PERF_RESUME_FROM) {
  const previous = JSON.parse(fs.readFileSync(path.join(process.env.PERF_RESUME_FROM, 'partial.json'), 'utf8'));
  const checkpoint = JSON.parse(fs.readFileSync(path.join(process.env.PERF_RESUME_FROM, 'checkpoint.json'), 'utf8'));
  assert.deepEqual(previous.conditions, report.conditions);
  assert.equal(checkpoint.baseline, process.env.UX_BASELINE_DIR);
  assert.equal(checkpoint.candidate, process.env.UX_SITE_DIR);
  report.samples = previous.samples;
  report.resumeFrom = process.env.PERF_RESUME_FROM;
}
if (process.env.PERF_BASELINE_FROM) {
  assert(!process.env.PERF_RESUME_FROM);
  const previous = JSON.parse(fs.readFileSync(path.join(process.env.PERF_BASELINE_FROM, 'result.json'), 'utf8'));
  const checkpoint = JSON.parse(fs.readFileSync(path.join(process.env.PERF_BASELINE_FROM, 'checkpoint.json'), 'utf8'));
  assert.deepEqual(previous.conditions, report.conditions);
  assert.equal(checkpoint.baseline, process.env.UX_BASELINE_DIR);
  report.samples = previous.samples.filter(sample => sample.arm === 'baseline');
  assert.equal(report.samples.length, 9);
  report.baselineReuseFrom = process.env.PERF_BASELINE_FROM;
}
const median = values => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
(async () => {
  const before = await serve(process.env.UX_BASELINE_DIR), after = await serve(process.env.UX_SITE_DIR);
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXE ? { executablePath: process.env.CHROMIUM_EXE } : {}) });
  fs.writeFileSync(path.join(out, 'checkpoint.json'), JSON.stringify({ status: 'running', pid: process.pid, started: new Date().toISOString(), script: __filename, scriptSha256: require('node:crypto').createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'), resumeFrom: report.resumeFrom || null, baselineReuseFrom: report.baselineReuseFrom || null, baseline: process.env.UX_BASELINE_DIR, candidate: process.env.UX_SITE_DIR, pages, ...report.conditions }, null, 2));
  try {
    for (const route of pages) for (let trial = 0; trial < 3; trial++) {
      for (const arm of trial % 2 ? ['candidate', 'baseline'] : ['baseline', 'candidate']) {
        if (report.samples.some(sample => sample.page === route && sample.trial === trial && sample.arm === arm)) continue;
        const base = arm === 'candidate' ? after.base : before.base;
        const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
        try {
          await context.route('**/*', request => new URL(request.request().url()).origin === new URL(base).origin ? request.continue() : request.abort());
          await context.addInitScript(() => {
            window.__timing = { longTasks: [], shifts: [], lcp: null };
            new PerformanceObserver(list => list.getEntries().forEach(e => __timing.longTasks.push(e.duration))).observe({ type: 'longtask', buffered: true });
            new PerformanceObserver(list => list.getEntries().forEach(e => { if (!e.hadRecentInput) __timing.shifts.push({ time: e.startTime, value: e.value }); })).observe({ type: 'layout-shift', buffered: true });
            new PerformanceObserver(list => list.getEntries().forEach(e => { __timing.lcp = e.startTime; })).observe({ type: 'largest-contentful-paint', buffered: true });
          });
          const page = await context.newPage(), errors = [];
          page.on('pageerror', error => errors.push(error.message));
          const cdp = await context.newCDPSession(page);
          await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
          await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
          await page.goto(base + route.split('/').map(encodeURIComponent).join('/'), { waitUntil: 'domcontentloaded', timeout: 90000 });
          await page.waitForTimeout(700);
          const sample = await page.evaluate(() => {
            const nav = performance.getEntriesByType('navigation')[0], timing = window.__timing;
            let cls = 0, sum = 0, start = 0, last = 0;
            for (const shift of timing.shifts) {
              if (shift.time - last > 1000 || shift.time - start > 5000) { sum = 0; start = shift.time; }
              sum += shift.value; cls = Math.max(cls, sum); last = shift.time;
            }
            return { domContentLoaded: nav.domContentLoadedEventEnd, fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || null,
              lcp: timing.lcp, cls, maxLongTask: Math.max(0, ...timing.longTasks), longTaskCount: timing.longTasks.length,
              longTaskTimeOver50ms: timing.longTasks.reduce((n, duration) => n + Math.max(0, duration - 50), 0),
              observedBytes: nav.encodedBodySize + performance.getEntriesByType('resource').reduce((n, e) => n + e.encodedBodySize, 0),
              domElements: document.querySelectorAll('*').length, totalCodeBlocks: document.querySelectorAll('pre > code').length,
              mountedCodeBlocks: document.querySelectorAll('pre[id^="__code_"]').length, horizontalPageOverflow: document.documentElement.scrollWidth > innerWidth + 1 };
          });
          await cdp.send('HeapProfiler.collectGarbage');
          sample.retainedJsHeapAfterDebugGC = (await cdp.send('Runtime.getHeapUsage')).usedSize;
          report.samples.push({ page: route, trial, arm, ...sample, pageErrors: errors });
          fs.writeFileSync(path.join(out, 'partial.json'), JSON.stringify(report, null, 2));
        } finally { await context.close(); }
      }
    }
    for (const route of pages) {
      report.medians[route] = {};
      for (const arm of ['baseline', 'candidate']) {
        const entries = report.samples.filter(s => s.page === route && s.arm === arm), stats = {};
        for (const metric of ['domContentLoaded', 'fcp', 'lcp', 'cls', 'maxLongTask', 'longTaskTimeOver50ms', 'observedBytes', 'domElements', 'mountedCodeBlocks', 'retainedJsHeapAfterDebugGC']) {
          stats[metric] = median(entries.map(s => s[metric]));
        }
        report.medians[route][arm] = stats;
      }
    }
    const heavy = report.medians[pages[1]];
    assert(heavy.candidate.domContentLoaded < heavy.baseline.domContentLoaded * .8, 'Heavy-page DCL improvement must reproduce');
    assert(heavy.candidate.maxLongTask < heavy.baseline.maxLongTask * .75, 'Heavy-page blocking improvement must reproduce');
    assert(report.samples.filter(s => s.arm === 'candidate').every(s => !s.horizontalPageOverflow && s.pageErrors.length === 0));
    report.acceptance = 'PASS';
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ acceptance: report.acceptance, medians: report.medians }, null, 2));
  } catch (error) {
    report.failure = error.message; fs.writeFileSync(path.join(out, 'failure.json'), JSON.stringify(report, null, 2)); throw error;
  } finally { await browser.close(); await before.close(); await after.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
