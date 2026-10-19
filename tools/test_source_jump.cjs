// Browser point-hit-testing regression. Reuses existing Playwright/Chromium;
// requests are intercepted and no VS Code process can be launched.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict'),path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXE?{executablePath:process.env.CHROMIUM_EXE}:{})});
 try{
 const page=await browser.newPage({viewport:{width:1000,height:800}}),requests=[],errors=[];
 let delayNext=0,failNext=false;
 page.on('pageerror',e=>errors.push(e.message));
 const html=String.raw`<!doctype html><meta charset="utf-8"><style>body{font:22px Arial;margin:24px}p{line-height:2;width:90%}</style>
 <main class="md-content"><article class="md-content__inner">
 <h1>Test</h1><p id="main">前綴😀 <b id="bold">粗體文字</b> 和 <a id="link" href="#test">連結文字</a> 和 <code id="code">inline_code</code>。</p>
 <p id="repeat">重複 重複 重複</p>
 <p id="math">前 <span class="arithmatex">\(x=1\)</span> 中 <span class="arithmatex">\(x=1\)</span> 後</p>
 </article></main>`;
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname.endsWith('/__peicd/source-jump')){
   if(url.searchParams.get('selection')!=='__probe__'){
    requests.push(Object.fromEntries(url.searchParams));
    if(delayNext){const delay=delayNext;delayNext=0;await new Promise(r=>setTimeout(r,delay));}
    if(failNext){failNext=false;return route.fulfill({status:500,json:{ok:false,message:'Test editor unavailable'}});}
   }
   return route.fulfill({json:{ok:true,opened:true,probe:url.searchParams.get('selection')==='__probe__'}});
  }
  return route.fulfill({contentType:'text/html',body:html});
 });
 const script=path.resolve('theme/assets/pymdownx-extras/source-jump.js');
 await page.goto('http://localhost/caret-test');await page.evaluate(()=>window.livereload=function(){});await page.addScriptTag({path:script});
 async function coords(selector,offset){const el=page.locator(selector);await el.scrollIntoViewIfNeeded();return el.evaluate((el,offset)=>{const text=el.firstChild,r=document.createRange();r.setStart(text,Math.min(offset,text.length-1));r.setEnd(text,Math.min(offset+1,text.length));let b=r.getBoundingClientRect();if(b.top<0||b.bottom>innerHeight){window.scrollBy(0,b.top-innerHeight/2);b=r.getBoundingClientRect();}return {x:offset===text.length?b.right-.1:b.left+.2,y:(b.top+b.bottom)/2};},offset);}
 async function open(xy){await page.waitForTimeout(100);const before=requests.length,pending=page.waitForResponse(r=>r.url().includes('/__peicd/source-jump?')&&r.url().includes('action=open'));pending.catch(()=>{});await page.mouse.click(xy.x,xy.y,{button:'right'});await pending;await page.waitForTimeout(30);assert.equal(requests.length,before+1);assert.equal(await page.locator('#peicd-source-jump-menu').count(),0,'no intermediate menu');return requests.at(-1);}
 async function point(selector,offset){await page.evaluate(()=>getSelection().removeAllRanges());return open(await coords(selector,offset));}
 for(const [selector,offset] of [['#main',4],['#bold',2],['#link',2],['#code',7],['#repeat',7]]){
  const request=await point(selector,offset),text=await page.locator(selector).evaluate(el=>el.firstChild.nodeValue);
  assert.equal(request.selection,text);assert.equal(Number(request.caret_offset),Array.from(text.slice(0,offset)).length,selector);
 }
 const endXY=await coords('#bold',4),endHit=await page.evaluate(({x,y})=>{const p=document.caretPositionFromPoint(x,y);return {text:p.offsetNode.nodeValue,at:Array.from(p.offsetNode.nodeValue.slice(0,p.offset)).length};},endXY),end=await open(endXY);assert.equal(end.selection,endHit.text);assert.equal(Number(end.caret_offset),endHit.at);
 // The exact offset must survive a truncated long-text anchor.
 await page.locator('#repeat').evaluate(el=>el.textContent='重複 '.repeat(1500));const long=await point('#repeat',2200);
 assert.equal(Number(long.caret_offset),40);assert.equal(Array.from(long.selection).length,80);assert.equal(long.prefix.length,500);assert.equal(long.point_prefix_length,'2159');
 // Math must use original TeX, not visual/assistive MathJax duplicate text.
 await page.locator('.arithmatex').evaluateAll(nodes=>nodes.forEach(el=>{el.dataset.peicdTex=el.textContent;el.innerHTML='<mjx-container><span>VISUAL</span><mjx-assistive-mml>DUPLICATE</mjx-assistive-mml></mjx-container>';}));
 const math=page.locator('.arithmatex').last();await math.scrollIntoViewIfNeeded();const box=await math.boundingBox(),formula=await open({x:box.x+box.width/2,y:box.y+box.height/2});
 assert.equal(formula.math_source,String.raw`\(x=1\)`);assert.equal(formula.math_index,'1');assert.equal(formula.selection,'');
 // Selection is deliberately higher priority than the point under the mouse.
 await page.locator('#bold').evaluate(el=>{const r=document.createRange();r.selectNodeContents(el);getSelection().removeAllRanges();getSelection().addRange(r);});
 const selected=await open(await coords('#bold',2));assert.equal(selected.selection,'粗體文字');assert.equal(selected.caret_offset,undefined);await page.evaluate(()=>getSelection().removeAllRanges());
 // Unsupported APIs and blank margins must not fabricate a caret.
 await page.evaluate(()=>{document.caretPositionFromPoint=undefined;document.caretRangeFromPoint=undefined;});const unsupported=await point('#bold',2);assert.equal(unsupported.caret_offset,undefined);assert.equal(unsupported.selection,'');await page.evaluate(()=>{delete document.caretPositionFromPoint;delete document.caretRangeFromPoint;});
 const p=await page.locator('#main').boundingBox(),blank=await open({x:p.x+p.width-2,y:p.y+p.height/2});assert.equal(blank.caret_offset,undefined);
 // Global handler must work after instant-navigation article replacement.
 await page.locator('article').evaluate(el=>el.replaceWith(el.cloneNode(true)));assert.equal((await point('#bold',1)).caret_offset,'1');
 await page.setViewportSize({width:390,height:844});assert.equal((await point('#bold',2)).caret_offset,'2');
 // A held open request must suppress rapid extra clicks, then release its lock.
 const xy=await coords('#bold',1),before=requests.length;delayNext=200;
 const pending=page.waitForResponse(r=>r.url().includes('action=open'));pending.catch(()=>{});
 await page.locator('#bold').evaluate((el,{x,y})=>{for(let i=0;i<2;i++)el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:x,clientY:y}));},xy);
 await pending;await page.waitForTimeout(30);assert.equal(requests.length,before+1);await point('#bold',1);
 // Failures are visible, do not require a menu, and must not block the next jump.
 failNext=true;await point('#bold',2);assert.equal(await page.locator('#peicd-source-jump-status').textContent(),'Test editor unavailable');await page.keyboard.press('Escape');assert.equal(await page.locator('#peicd-source-jump-status').count(),0);await point('#bold',1);assert.equal(await page.locator('#peicd-source-jump-status').count(),0);
 // Non-loopback pages must retain their native context menu.
 await page.goto('http://example.test/caret-test');await page.addScriptTag({path:script});assert.equal(await page.locator('#bold').evaluate(el=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true});el.dispatchEvent(e);return e.defaultPrevented;}),false);
 assert.deepEqual(errors,[]);console.log('PASS: direct-right-click/no-menu/dedupe/failure-retry/text/UTF16/formatting/long anchor/math/selection/fallback/navigation/mobile/local-only');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
