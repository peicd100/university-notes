// Browser regression: PLAYWRIGHT_MODULE / CHROMIUM_EXE can select an existing installation.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const scripts={toc:path.resolve('theme/assets/pymdownx-extras/toc-fold.js'),math:path.resolve('theme/assets/pymdownx-extras/mathjax-refresh.js')};
const nav=html=>`<nav class="md-nav md-nav--secondary" data-md-component="toc"><label class="md-nav__title">TOC</label><ul class="md-nav__list">${html}</ul></nav>`;
const link=(id,text)=>`<a class="md-nav__link" href="#${id}"><span class="md-ellipsis">${text}</span></a>`;
const body=`<style>.md-sidebar--secondary{position:fixed;right:0;top:0;width:320px}.peicd-mobile-toc-toggle{position:fixed;bottom:12px;left:12px}</style><header class="md-header" style="height:40px"></header><main><article class="md-content__inner md-typeset">
<h2 id="divisibility">Divisibility <span class="arithmatex">\\(b\\mid a\\)</span><a class="headerlink" href="#divisibility">#</a></h2>
<span class="arithmatex">\\(x=1\\)</span><div style="height:2400px"></div>
<h3 id="example">Example <span class="arithmatex">\\(3\\mid12\\)</span></h3>
<div class="admonition danger"><p class="admonition-title">Danger | Title <span class="arithmatex">\\(t\\)</span></p><p>danger content</p></div>
<div style="height:2400px"></div><span id="unrelated" class="arithmatex">\\(unrelated\\)</span></article></main>
<div class="md-sidebar md-sidebar--secondary"><div class="md-sidebar__scrollwrap"><div class="md-sidebar__inner">${nav(`<li class="md-nav__item">${link('divisibility','Divisibility raw latex')}<nav class="md-nav"><ul class="md-nav__list"><li class="md-nav__item">${link('example','Example raw latex')}</li></ul></nav></li>`)}</div></div></div>`;
async function scenario(browser,order){
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.setContent(body);
  await page.evaluate(()=>{
   const subscribers=[];window.document$={subscribe(fn){subscribers.push(fn);fn();},emit(){subscribers.forEach(fn=>fn());}};
   window.requestIdleCallback=()=>1;window.mathCalls={converted:0,resets:0};
   window.MathJax={startup:{promise:Promise.resolve()},texReset(){mathCalls.resets++;},typesetClear(){},typesetPromise:async()=>{},
    async tex2chtmlPromise(tex){mathCalls.converted++;const c=document.createElement('mjx-container');c.id='source-math-'+mathCalls.converted;c.setAttribute('data-tex',tex);c.setAttribute('tabindex','0');c.innerHTML='<a href="#source"><span>'+tex+'</span></a><mjx-assistive-mml id="assistive-'+mathCalls.converted+'"><math>'+tex+'</math></mjx-assistive-mml>';return c;},
    chtmlStylesheet(){const s=document.createElement('style');s.id='MJX-CHTML-styles';return s;}};
  });
  for(const key of order)await page.addScriptTag({path:scripts[key]});
  await page.waitForFunction(()=>document.querySelectorAll('.md-sidebar--secondary .arithmatex > mjx-container').length===3);
  assert.equal(await page.locator('.md-sidebar--secondary .arithmatex [id]').count(),0);
  assert.equal(await page.locator('.md-sidebar--secondary .arithmatex [tabindex]').count(),0);
  assert.equal(await page.locator('.md-sidebar--secondary a a').count(),0);
  assert.equal(await page.locator('.md-sidebar--secondary mjx-assistive-mml').count(),3);
  assert.equal(await page.locator('#unrelated mjx-container').count(),0,'sidebar must not force unrelated body math');
  const before=await page.evaluate(()=>({...mathCalls}));assert.equal(before.converted,4);
  // Later semantic/forward-reference updates must refresh mirrors, not freeze '?'.
  await page.evaluate(()=>{
   const source=document.querySelector('#divisibility mjx-container');
   source.querySelector('span').textContent='resolved';source.querySelector('math').textContent='resolved';
  });
  await page.waitForFunction(()=>document.querySelector('.md-sidebar--secondary a[href="#divisibility"] mjx-container').textContent.includes('resolved'));
  assert.deepEqual(await page.evaluate(()=>({...mathCalls})),before);
  await page.evaluate(()=>document.querySelector('#divisibility mjx-container').setAttribute('data-tex','updated-by-attribute'));
  await page.waitForFunction(()=>document.querySelector('.md-sidebar--secondary mjx-container[data-tex="updated-by-attribute"]'));
  await page.getByRole('button',{name:'展開',exact:true}).click();
  assert.equal(await page.locator('.peicd-toc-toggle').getAttribute('aria-expanded'),'true');
  await page.locator('.md-sidebar--secondary a[href="#example"]').click();
  assert.equal(await page.evaluate(()=>location.hash),'#example');
  await page.getByRole('button',{name:'Danger',exact:true}).click();
  const danger=page.locator('.peicd-danger-link');assert.equal(await danger.locator('mjx-container').count(),1);
  assert.equal(await danger.locator('.md-ellipsis').innerText().then(s=>s.startsWith('Danger')),false);
  // Reinitializing the same document must not re-typeset formulas or duplicate labels.
  await page.evaluate(()=>document$.emit());
  await page.waitForFunction(()=>document.querySelectorAll('.md-sidebar--secondary .arithmatex > mjx-container').length===3);
  assert.deepEqual(await page.evaluate(()=>({...mathCalls})),before);
  // Mobile panel retains the same math DOM while it opens/closes.
  await page.setViewportSize({width:390,height:844});
  await page.locator('#peicd-mobile-toc-toggle').click();
  await page.waitForFunction(()=>document.querySelector('.peicd-mobile-toc-visible'));
  assert.equal(await page.locator('.md-sidebar--secondary .arithmatex > mjx-container').count(),3);
  await page.keyboard.press('Escape');
  // Instant-navigation replacement: old sources/labels must not leak into a new page.
  await page.evaluate(html=>{
   document.querySelector('.md-content__inner').outerHTML='<article class="md-content__inner md-typeset"><h2 id="fresh">Fresh <span class="arithmatex">\\(q\\)</span></h2></article>';
   document.querySelector('.md-sidebar__inner').innerHTML=html;document$.emit();
  },nav(`<li class="md-nav__item">${link('fresh','Fresh raw latex')}</li>`));
  await page.waitForFunction(()=>document.querySelector('.md-sidebar--secondary mjx-container[data-tex="q"]'));
  assert.equal(await page.locator('.md-sidebar--secondary mjx-container').count(),1);
  assert.equal(await page.locator('.md-sidebar--secondary .arithmatex [id]').count(),0);
  assert.equal(await page.evaluate(()=>mathCalls.resets),2);assert.deepEqual(errors,[]);
  return {order,sidebarMath:3,duplicateIds:0,unrelatedBodyForced:false,foldAnchorDangerMobileAndReplacement:'PASS',pageErrors:errors};
 }finally{await page.close();}
}
(async()=>{const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXE?{executablePath:process.env.CHROMIUM_EXE}:{})});try{
 const results=[];for(const order of [['toc','math'],['math','toc']])results.push(await scenario(browser,order));console.log(JSON.stringify(results,null,2));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
