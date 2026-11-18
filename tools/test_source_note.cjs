/* Run with PLAYWRIGHT_MODULE pointing at an existing Playwright installation. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const renderer = fs.readFileSync(path.resolve(__dirname, '../theme/assets/pymdownx-extras/source-note.js'), 'utf8');
const loader = fs.readFileSync(path.resolve(__dirname, '../theme/assets/pymdownx-extras/conditional-loader.js'), 'utf8');
function child(id, height) {
  return `<main style="height:${height}px"></main><script>
    window.requests=0;
    addEventListener('message',event=>{
      if(event.source!==parent||event.data?.type!=='peicd-note-measure'||event.data.id!==${JSON.stringify(id)})return;
      requests++;parent.postMessage({type:'peicd-note-size',id:${JSON.stringify(id)},height:document.querySelector('main').offsetHeight},'*');
    });
    <\/script>`;
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    const page = await browser.newPage({ viewport: {width:390,height:844} });
    await page.setContent('<article class="md-typeset"></article>');
    await page.evaluate(() => { window.nav=[]; window.document$={subscribe:fn=>nav.push(fn)}; });
    async function addFrame(id, height) {
      await page.evaluate(({id,html}) => {
        const wrapper=document.createElement('div');wrapper.className='peicd-source-note';
        const frame=document.createElement('iframe');frame.dataset.peicdNoteFrame=id;frame.sandbox='allow-scripts';frame.srcdoc=html;frame.height='1';
        wrapper.appendChild(frame);document.querySelector('article').appendChild(wrapper);
      }, {id,html:child(id,height)});
    }
    await addFrame('same-id',180);
    await page.addScriptTag({content:renderer});
    await page.waitForFunction(()=>document.querySelector('iframe').height==='180');
    results.push('initial/load handshake measures a sandboxed opaque-origin frame');
    const frame=page.frames().find(f=>f.parentFrame());
    for (const height of [0,-1,Infinity,NaN,2000001,'123',null]) await frame.evaluate(height=>parent.postMessage({type:'peicd-note-size',id:'same-id',height},'*'),height);
    await frame.evaluate(()=>parent.postMessage({type:'peicd-note-size',id:'wrong-id',height:2},'*'));
    await page.evaluate(()=>postMessage({type:'peicd-note-size',id:'same-id',height:2},'*'));
    await page.waitForTimeout(80);
    assert.equal(await page.locator('iframe').getAttribute('height'),'180');
    results.push('wrong sender/id, non-numeric, non-finite and out-of-range heights rejected');
    await frame.evaluate(()=>parent.postMessage({type:'peicd-note-size',id:'same-id',height:243.2},'*'));
    await page.waitForFunction(()=>document.querySelector('iframe').height==='244');
    results.push('valid heights are rounded up without repeated subpixel resize writes');
    const styleCount=await page.locator('head style').count();
    await page.addScriptTag({content:renderer});
    await page.waitForFunction(()=>document.querySelector('iframe').height==='180');
    assert.equal(await page.locator('head style').count(),styleCount);
    assert.equal(await page.evaluate(()=>nav.length),1);
    results.push('reloading renderer does not duplicate style, message listener, or navigation subscription');
    await page.evaluate(()=>{window.oldWindow=document.querySelector('iframe').contentWindow;document.querySelector('.peicd-source-note').remove();});
    await addFrame('same-id',400);
    await page.evaluate(()=>nav.forEach(fn=>fn()));
    await page.waitForFunction(()=>document.querySelector('iframe').height==='400');
    await page.evaluate(()=>dispatchEvent(new MessageEvent('message',{source:oldWindow,data:{type:'peicd-note-size',id:'same-id',height:1}})));
    await page.waitForTimeout(80);
    assert.equal(await page.locator('iframe').getAttribute('height'),'400');
    results.push('instant navigation releases detached frames; reused IDs cannot accept stale-window messages');
    const next=page.frames().find(f=>f.parentFrame());
    const requests=await next.evaluate(()=>window.requests);
    await page.evaluate(()=>dispatchEvent(new Event('beforeprint')));
    await page.waitForFunction(()=>document.querySelector('iframe').height==='400');
    await page.waitForTimeout(80);
    assert.ok(await next.evaluate(()=>window.requests)>requests);
    assert.equal(await next.evaluate(()=>{try{return !!parent.document;}catch{return false;}}),false);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    results.push('print remeasurement, sandbox isolation and narrow-page containment');
    const lazy = await browser.newPage();
    await lazy.route('http://notes.test/**',route=>{
      const url=route.request().url();
      if(url.endsWith('/conditional-loader.js')) return route.fulfill({contentType:'text/javascript',body:loader});
      if(url.includes('mathjax-refresh.js')) return route.fulfill({contentType:'text/javascript',body:'window.mathLoads=(window.mathLoads||0)+1;'});
      return route.fulfill({contentType:'text/html',body:'<details class="peicd-note-markdown"><summary>Editable</summary><span class="arithmatex">x^2</span></details>'});
    });
    await lazy.goto('http://notes.test/');
    await lazy.addScriptTag({url:'http://notes.test/conditional-loader.js'});
    await lazy.waitForTimeout(80);
    assert.equal(await lazy.locator('script[src*="mathjax-refresh.js"]').count(),0);
    await lazy.locator('details').evaluate(n=>n.open=true);
    await lazy.waitForFunction(()=>window.mathLoads===1);
    await lazy.locator('details').evaluate(n=>{n.open=false;n.open=true;});
    await lazy.waitForTimeout(80);
    assert.equal(await lazy.evaluate(()=>window.mathLoads),1);
    results.push('closed Markdown fallback does not request MathJax; opening it loads tools once (independent visible math/TOC still loads normally)');
    console.log(JSON.stringify({passed:results.length,results},null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
