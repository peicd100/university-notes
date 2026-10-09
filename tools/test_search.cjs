const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { LiteralSearch, parseQuery } = require('../theme/assets/pymdownx-extras/search-core.js');

const location = 'md/Verilog/%E9%9B%99%E9%82%8A%E7%B7%A3%E8%A7%B8%E7%99%BC.html';
const fixture = [
  { location, title: '雙邊\u200b緣\u200b觸發', text: '<p>題目 Dualedge</p>' },
  { location: location + '#解題', title: '解題', text: '<p>看到這題，我們\u200b會\u200b第\u200b一直\u200b覺用\u200b一個\u200b <code>always</code> + posedge、negedge 來寫。</p><pre><code>q &lt;= d ^ n;</code></pre>' },
  { location: 'other.html', title: '另一篇', text: '<p>第一直覺，但是沒有另一個關鍵字。</p>' }
];
const best = result => result.items[0].find(item => item.score > 0);

test('arbitrary Chinese body substrings ignore jieba boundaries and link to the section', () => {
  const result = new LiteralSearch(fixture).search('會第一直覺用一');
  assert.equal(result.items.length, 1);
  assert.equal(best(result).location, location + '#解題');
  assert.match(best(result).text, /<mark>會第一直覺用一<\/mark>個/);
  assert.equal(result.items[0].at(-1).location, location);
  assert.equal(result.items[0].at(-1).score, 0);
});

test('all keywords are required, including inherited article titles and mixed-language code', () => {
  const engine = new LiteralSearch(fixture);
  assert.equal(best(engine.search('雙邊緣 posedge')).location, location + '#解題');
  assert.equal(best(engine.search('第一直覺 ALWAYS negedge')).location, location + '#解題');
  assert.equal(engine.search('第一直覺 不存在').items.length, 0);
  assert.equal(engine.search('posedge otherword').items.length, 0);
});

test('quoted phrases are exact; normal words use AND, not implicit phrase-only matching', () => {
  const engine = new LiteralSearch([{ location: 'a.html', title: 'Words', text: 'first scattered second' }]);
  assert.equal(engine.search('first second').items.length, 1);
  assert.equal(engine.search('"first second"').items.length, 0);
  assert.equal(new LiteralSearch(fixture).search('"會第一直覺用一"').items.length, 1);
});

test('case, fullwidth characters, whitespace, entities, and code fragments normalize consistently', () => {
  const engine = new LiteralSearch(fixture);
  assert.equal(best(engine.search('ＡＬＷＡＹＳ\nＰＯＳＥＤＧＥ')).location, location + '#解題');
  assert.match(best(engine.search('"q <= d"')).text, /<mark>q &lt;= d<\/mark>/);
  const inline = new LiteralSearch([{ location: 'inline.html', title: 'Inline', text: '<p>中文<em>連續</em><code>片段</code> &#x1f680; &amp; test</p>' }]);
  assert.match(best(inline.search('中文連續片段')).text, /<mark>中文連續片段<\/mark>/);
  assert.match(best(inline.search('🚀')).text, /<mark>🚀<\/mark>/);
  const unusualCase = new LiteralSearch([{ location: 'case.html', title: 'İstanbul', text: 'İstanbul Example' }]);
  assert.match(best(unusualCase.search('example')).text, /İstanbul <mark>Example<\/mark>/);
});

test('title matches outrank body matches, and contiguous phrases outrank scattered keywords', () => {
  const engine = new LiteralSearch([
    { location: 'body.html', title: 'General', text: '中文搜尋的內容' },
    { location: 'title.html', title: '中文搜尋', text: 'general' },
    { location: 'scattered.html', title: 'General', text: 'quick ' + 'filler '.repeat(80) + 'brown' },
    { location: 'phrase.html', title: 'General', text: 'quick brown' }
  ]);
  assert.equal(best(engine.search('中文搜尋')).location, 'title.html');
  assert.equal(best(engine.search('quick brown')).location, 'phrase.html');
});

test('snippets are centered on late matches, not just the first paragraph', () => {
  const engine = new LiteralSearch([{ location: 'long.html', title: 'Long', text: '<p>' + '開頭文字'.repeat(1500) + '最後的關鍵片段在這裡</p>' }]);
  const item = best(engine.search('關鍵片段'));
  assert.match(item.text, /<mark>關鍵片段<\/mark>/);
  assert.ok(item.text.length < 250, 'bounded snippet');
  const emoji = best(new LiteralSearch([{ location: 'emoji.html', title: 'Emoji', text: '😀'.repeat(100) + 'X目標' + '😀'.repeat(100) }]).search('目標'));
  assert.equal(emoji.text.isWellFormed(), true, 'snippet boundaries must not split UTF-16 surrogate pairs');
});

test('snippets, titles, tags, and term objects cannot inject HTML or prototypes', () => {
  const engine = new LiteralSearch([{
    location: 'safe.html', title: '&lt;img src=x onerror=alert(1)&gt; __proto__',
    text: '<p>&lt;script&gt;alert(1)&lt;/script&gt; &amp; __proto__</p><script>hiddenpayload</script>',
    tags: ['<img onerror=x>', '__proto__']
  }]);
  const item = best(engine.search('__proto__'));
  assert.ok(Object.hasOwn(item.terms, '__proto__'));
  assert.equal(item.terms.__proto__, true);
  assert.ok(!item.title.includes('<img'));
  assert.ok(!item.text.includes('<script'));
  assert.ok(item.tags.every(tag => !tag.includes('<img')));
  assert.equal(engine.search('hiddenpayload').items.length, 0);
});

test('unordered or section-only input still produces a valid Material parent group', () => {
  const engine = new LiteralSearch([
    { location: 'page.html#later', title: 'Later', text: 'match' },
    { location: 'page.html', title: 'Page', text: '' },
    { location: 'missing.html#section', title: 'Section', text: 'match' }
  ]);
  const result = engine.search('match');
  assert.equal(result.items.length, 2);
  for (const group of result.items) assert.equal(group.filter(item => !item.location.includes('#')).length, 1);
  assert.equal(engine.search('excluded private text').items.length, 0);
});

test('empty queries and overlapping highlights are safe; advanced Lunr syntax stays explicit', () => {
  const engine = new LiteralSearch(fixture);
  for (const query of ['', '  ', '\u200b', '""']) assert.equal(engine.search(query).items.length, 0);
  const item = best(engine.search('第一直覺 直覺'));
  assert.match(item.text, /<mark>第一直覺<\/mark>/);
  assert.ok(!item.text.includes('<mark><mark>'));
  for (const query of ['title:hello', '+foo -bar', 'always*', 'verlog~1', 'term^2']) assert.equal(parseQuery(query).advanced, true, query);
  assert.equal(parseQuery('"a * b"').advanced, false);
});

function guardContext(search = '') {
  const workers = [], events = {}, sends = [];
  class Worker {
    constructor(url, options) { this.url = String(url); this.options = options; this.messages = []; this.listeners = {}; workers.push(this); }
    postMessage(message) { this.messages.push(message); }
    terminate() { this.terminated = true; }
    addEventListener(type, listener) { (this.listeners[type] ||= []).push(listener); }
    removeEventListener(type, listener) { this.listeners[type] = (this.listeners[type] || []).filter(fn => fn !== listener); }
  }
  class XHR {
    open(method, url) { this.url = url; }
    send(...args) { sends.push({ url: this.url, args }); }
  }
  const document = { baseURI: 'https://example.test/university-notes/md/Verilog/test.html', addEventListener(type, fn) { (events[type] ||= []).push(fn); } };
  const window = { Worker, XMLHttpRequest: XHR, addEventListener: document.addEventListener };
  const scope = { window, document, location: { search, origin: 'https://example.test' }, URL, Element: class {},
    KeyboardEvent: class { constructor(type, options) { this.type = type; Object.assign(this, options); } } };
  vm.runInNewContext(fs.readFileSync('theme/assets/pymdownx-extras/search-lazy-guard.js', 'utf8'), scope);
  return { ...scope, workers, sends, events };
}
const materialURL = '../../assets/javascripts/workers/search.2c215733.min.js';

test('guard keeps the full index and custom worker lazy, releases once, preserves Pages subpaths', () => {
  const context = guardContext();
  const index = new context.window.XMLHttpRequest();
  index.open('GET', '../../search/search_index.json'); index.send();
  const worker = new context.window.Worker(materialURL);
  worker.postMessage({ type: 0 });
  assert.equal(context.workers.length, 0); assert.equal(context.sends.length, 0);
  context.window.__PEICD_SEARCH_LAZY_GUARD__.activate();
  context.window.__PEICD_SEARCH_LAZY_GUARD__.activate();
  assert.equal(context.workers.length, 1); assert.equal(context.sends.length, 1);
  const url = new URL(context.workers[0].url);
  assert.equal(url.pathname, '/university-notes/assets/javascripts/workers/search-peicd.js');
  assert.equal(url.searchParams.get('material'), new URL(materialURL, context.document.baseURI).href);
  assert.deepEqual(context.workers[0].messages, [{ type: 0 }]);
});

test('already-activated shared searches use the same enhanced worker; unrelated workers stay unchanged', () => {
  const context = guardContext('?q=中文');
  new context.window.Worker(materialURL);
  new context.window.Worker('/unrelated-worker.js');
  assert.match(context.workers[0].url, /search-peicd\.js/);
  assert.equal(context.workers[1].url, '/unrelated-worker.js');
});

test('terminating a deferred worker does not resurrect it on activation', () => {
  const context = guardContext();
  const worker = new context.window.Worker(materialURL);
  worker.terminate(); worker.postMessage({ type: 0 });
  context.window.__PEICD_SEARCH_LAZY_GUARD__.activate();
  assert.equal(context.workers.length, 0);
});

test('input/paste and IME commits update search once without intercepting normal inputs or IME defaults', () => {
  const context = guardContext(), signals = [];
  const target = new context.Element();
  target.matches = () => true;
  target.dispatchEvent = event => signals.push(event);
  const fire = (type, extra = {}) => context.events[type].forEach(fn => fn({ target, ...extra }));
  fire('input');
  assert.equal(signals.length, 1); assert.equal(signals[0].type, 'keyup');
  fire('compositionstart');
  fire('input', { isComposing: true });
  let stopped = 0;
  fire('keyup', { isComposing: true, stopImmediatePropagation() { stopped++; } });
  fire('keydown', { isComposing: true, stopImmediatePropagation() { stopped++; } });
  assert.equal(stopped, 2); assert.equal(signals.length, 1);
  fire('compositionend');
  assert.equal(signals.length, 2, 'only the final IME commit notifies the query pipeline');
  target.matches = () => false;
  fire('input');
  assert.equal(signals.length, 2, 'unrelated input is untouched');
});

function workerContext() {
  const messages = [], upstream = [], listeners = {};
  class MaterialWorker {
    constructor(url) { this.url = url; this.listeners = {}; this.messages = []; upstream.push(this); }
    addEventListener(type, fn) { (this.listeners[type] ||= new Set()).add(fn); }
    removeEventListener(type, fn) { this.listeners[type]?.delete(fn); }
    terminate() { this.terminated = true; }
    postMessage(message) {
      this.messages.push(message);
      setTimeout(() => {
        const data = message.type === 0 ? { type: 1 } : { type: 3, data: { items: [[
          { location: 'fallback.html#section', title: message.data, text: 'fallback', score: 3, terms: { first: true, second: true } },
          { location: 'fallback.html#partial', title: 'Partial', text: '', score: 2, terms: { first: true, second: false } },
          { location: 'fallback.html', title: 'Parent', text: '', score: 0, terms: {} }
        ]] } };
        for (const fn of [...(this.listeners.message || [])]) fn({ data });
      }, message.type === 0 ? 10 : 2);
    }
  }
  const self = {
    location: { href: 'https://example.test/university-notes/assets/javascripts/workers/search-peicd.js?material=' + encodeURIComponent('https://example.test/university-notes/assets/javascripts/workers/search.2c215733.min.js') },
    PeicdSearch: { LiteralSearch, parseQuery },
    postMessage(message) { messages.push(message); },
    addEventListener(type, fn) { listeners[type] = fn; }
  };
  vm.runInNewContext(fs.readFileSync('theme/assets/javascripts/workers/search-peicd.js', 'utf8'), { self, URL, Worker: MaterialWorker, importScripts() {}, setTimeout, clearTimeout, console });
  return { self, messages, upstream, send(message) { listeners.message({ data: message }); } };
}
const wait = () => new Promise(resolve => setTimeout(resolve, 60));

test('worker setup/plain Chinese never starts Lunr, and failed Chinese phrases do not return partial matches', async () => {
  const context = workerContext();
  context.send({ type: 0, data: { docs: fixture, options: {} } });
  context.send({ type: 2, data: '會第一直覺用一' });
  context.send({ type: 2, data: '不存在的中文' });
  await wait();
  assert.deepEqual(context.messages.map(message => message.type), [1, 3, 3]);
  assert.equal(best(context.messages[1].data).location, location + '#解題');
  assert.equal(context.messages[2].data.items.length, 0);
  assert.equal(context.upstream.length, 0);
});

test('on-demand Lunr fallback preserves advanced syntax and reply ordering under rapid input', async () => {
  const context = workerContext();
  context.send({ type: 0, data: { docs: fixture, options: {} } });
  context.send({ type: 2, data: 'title:example' });
  context.send({ type: 2, data: '會第一直覺用一' });
  context.send({ type: 2, data: 'unmatchedenglish otherword' });
  await wait();
  assert.deepEqual(context.messages.map(message => message.type), [1, 3, 3, 3]);
  assert.equal(context.messages[1].data.items[0][0].title, 'title:example');
  assert.equal(context.messages[1].data.items[0].length, 3, 'advanced syntax preserves original results');
  assert.equal(best(context.messages[2].data).location, location + '#解題');
  assert.equal(context.messages[3].data.items[0].length, 2, 'plain English fallback requires every term');
  assert.equal(context.upstream.length, 1);
  assert.deepEqual(context.upstream[0].messages.map(message => message.type), [0, 2, 2]);
});
