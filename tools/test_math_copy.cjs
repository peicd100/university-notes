// Browser regression: use an existing Playwright/Chromium via environment variables.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const script=path.resolve('theme/assets/pymdownx-extras/mathjax-refresh.js');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXE?{executablePath:process.env.CHROMIUM_EXE}:{})});
 try{
 const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setContent(String.raw`<aside id="outside">Outside</aside><article class="md-content__inner">
 <p id="mixed">Before <span id="inline" class="arithmatex">\(x&lt;y\)</span> after.</p>
 <section id="sheet"><p>Relation on A</p><pre class="arithmatex">\[\boxed{R\subseteq A\times A}\]</pre>
 <p>Number of Relations（有限集合）</p><pre class="arithmatex">\[|A|=m,|B|=n\Rightarrow2^{mn}\]</pre><p>Notation</p></section>
 <p id="plain">Plain <b>text</b>.</p><pre id="code">const x = 1;</pre>
 <div id="editable" contenteditable="true">Editable <span class="arithmatex">\(z\)</span></div><input id="input" value="Input">
 </article>`);
 await page.evaluate(()=>{
  const subscribers=[];window.document$={subscribe(fn){subscribers.push(fn);},emit(){subscribers.forEach(fn=>fn());}};
  window.requestIdleCallback=()=>1;
  let release;window.renderGate=new Promise(r=>release=r);window.releaseRender=release;
  window.MathJax={startup:{promise:Promise.resolve()},typesetPromise:async()=>{},texReset(){},typesetClear(){},
   async tex2chtmlPromise(){await renderGate;const node=document.createElement('mjx-container');node.innerHTML='<span class="glyph">VISUAL</span><mjx-assistive-mml>DUPLICATE</mjx-assistive-mml>';return node;},
   chtmlStylesheet(){const s=document.createElement('style');s.id='MJX-CHTML-styles';return s;}};
  window.copySelection=(selector,partial=false,fail=false)=>{
   const el=document.querySelector(selector),range=document.createRange();
   if(partial){range.setStart(el.firstChild,1);range.setEnd(el.firstChild,2);}else range.selectNodeContents(el);
   const selection=getSelection();selection.removeAllRanges();selection.addRange(range);
   const data=new DataTransfer();data.setData('text/plain','NATIVE');
   const event=new ClipboardEvent('copy',{clipboardData:data,bubbles:true,cancelable:true});
   if(fail)Object.defineProperty(event,'clipboardData',{value:{setData(){throw Error('denied');}}});
   el.dispatchEvent(event);return {handled:event.defaultPrevented,text:data.getData('text/plain'),html:data.getData('text/html')};
  };
 });
 await page.addScriptTag({path:script});
 let result=await page.evaluate(()=>copySelection('#mixed'));
 assert.deepEqual(result,{handled:true,text:String.raw`Before \(x<y\) after.`,html:''},'copy pending TeX');
 await page.evaluate(()=>{releaseRender();return __PEICD_MATH__.renderAll();});
 result=await page.evaluate(()=>copySelection('#mixed'));
 assert.equal(result.text,String.raw`Before \(x<y\) after.`);assert(result.handled);
 result=await page.evaluate(()=>copySelection('#sheet'));
 assert.equal(result.text,String.raw`Relation on A

\[\boxed{R\subseteq A\times A}\]

Number of Relations（有限集合）

\[|A|=m,|B|=n\Rightarrow2^{mn}\]

Notation`);
 assert(!result.text.includes('VISUAL'));assert(!result.text.includes('DUPLICATE'));
 result=await page.evaluate(()=>copySelection('#inline .glyph',true));assert.equal(result.text,String.raw`\(x<y\)`);
 result=await page.evaluate(()=>copySelection('#inline'));assert.equal(result.text,String.raw`\(x<y\)`);
 for(const selector of ['#plain','#code','#outside','#editable']){
  result=await page.evaluate(s=>copySelection(s),selector);assert.equal(result.handled,false,selector);assert.equal(result.text,'NATIVE');
 }
 await page.locator('#input').focus();result=await page.evaluate(()=>copySelection('#mixed'));assert.equal(result.handled,false);
 await page.evaluate(()=>document.activeElement.blur());
 result=await page.evaluate(()=>copySelection('#mixed',false,true));assert.equal(result.handled,false,'clipboard failure falls back');
 result=await page.evaluate(()=>{const el=document.querySelector('#inline .glyph'),r=document.createRange();r.setStart(el.firstChild,0);r.collapse(true);getSelection().removeAllRanges();getSelection().addRange(r);const e=new ClipboardEvent('copy',{clipboardData:new DataTransfer(),bubbles:true,cancelable:true});el.dispatchEvent(e);return e.defaultPrevented;});assert.equal(result,false);
 // Instant navigation captures the new source and never reuses old formula text.
 await page.evaluate(()=>{document.querySelector('article').outerHTML=String.raw`<article class="md-content__inner"><p id="fresh">Fresh <span class="arithmatex">\(q=2\)</span></p></article>`;document$.emit();return __PEICD_MATH__.renderAll();});
 result=await page.evaluate(()=>copySelection('#fresh'));assert.equal(result.text,String.raw`Fresh \(q=2\)`);
 assert.deepEqual(errors,[]);console.log('PASS: pending/rendered mixed copy, block separators, partial/whole formula, native prose/code/editable/outside, failure, collapsed selection, instant navigation; pageerrors0');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
