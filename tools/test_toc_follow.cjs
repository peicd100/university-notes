// Native sidebar intent regression. No CDN requests or Git mutations.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict'),path=require('node:path');
const script=path.resolve('theme/assets/pymdownx-extras/toc-fold.js');
const sections=Array.from({length:40},(_,i)=>`<h2 id="h${i}">Heading ${i}</h2><div style="height:650px"></div>`).join('');
const links=Array.from({length:40},(_,i)=>`<li class="md-nav__item"><a class="md-nav__link" href="#h${i}"><span class="md-ellipsis">Heading ${i}</span></a><nav class="md-nav"><ul><li>Child choice ${i}</li></ul></nav></li>`).join('');
const html=`<style>body{margin:0;font:18px sans-serif}main{width:650px}h2{margin:0}.md-sidebar--secondary{position:fixed;right:0;top:0;width:300px;height:700px}.md-sidebar__scrollwrap{height:700px;overflow:auto}.md-nav__link{display:block;height:40px}li{list-style:none}.peicd-toc-item--collapsed>nav{display:none}.md-header{height:40px}</style><header class="md-header"></header><main><article class="md-content__inner">${sections}</article></main><aside class="md-sidebar md-sidebar--secondary"><div class="md-sidebar__scrollwrap"><div class="md-sidebar__inner"><nav class="md-nav--secondary"><label class="md-nav__title">TOC</label><ul data-md-component="toc" class="md-nav__list">${links}</ul></nav></div></div></aside>`;
(async()=>{const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXE?{executablePath:process.env.CHROMIUM_EXE}:{})});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.setContent(html);
 await page.evaluate(()=>{window.document$={subscribe(fn){fn();window.reinit=fn;}};const w=document.querySelector('.md-sidebar__scrollwrap'),native=w.scrollTo.bind(w);window.followCalls=[];w.scrollTo=(...a)=>{followCalls.push(a);return native(...a);};});
 await page.addScriptTag({path:script});await page.waitForTimeout(500);
 const wrap=page.locator('.md-sidebar__scrollwrap');
 await page.mouse.move(1260,350);await page.mouse.wheel(0,500);await page.waitForTimeout(200);await page.evaluate(()=>followCalls=[]);const chosen=await wrap.evaluate(n=>n.scrollTop);assert(chosen>200);
 // Native anchoring and delayed image/math height changes also emit real window scroll.
 await page.evaluate(()=>scrollTo({top:17000,behavior:'instant'}));await page.waitForTimeout(500);
 const layoutCalls=await page.evaluate(()=>followCalls.length);assert.equal(layoutCalls,0,'Layout/programmatic body scroll must not steal sidebar browsing');assert(Math.abs(await wrap.evaluate(n=>n.scrollTop)-chosen)<=1,'Keep chosen sidebar position');
 // Main-wheel intent resumes auto follow even if the focused link was in TOC.
 await page.mouse.move(250,300);await page.mouse.wheel(0,-2200);await page.waitForTimeout(500);assert(await page.evaluate(()=>followCalls.length)>0,'Real main wheel resumes auto follow');
 // Hover alone (no sidebar wheel) is sufficient to protect selection.
 await page.mouse.move(1260,350);await page.evaluate(()=>followCalls=[]);await page.evaluate(()=>scrollTo({top:2600,behavior:'instant'}));await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>followCalls.length),0,'Hover alone protects browsing');
 // Explicit Auto is allowed to recenter intentionally (pick an offscreen heading).
 await page.evaluate(()=>scrollTo({top:21000,behavior:'instant'}));await page.waitForTimeout(150);
 await page.getByRole('button',{name:'自動',exact:true}).click();await page.waitForTimeout(400);assert(await page.evaluate(()=>followCalls.length)>0,'Auto button remains an explicit resume');
 // Keyboard focus survives document-only layout changes after pointer leaves.
 await page.locator('.md-sidebar--secondary a[href="#h3"]').evaluate(n=>n.focus());await page.mouse.move(200,250);await page.evaluate(()=>followCalls=[]);await page.evaluate(()=>scrollTo({top:10000,behavior:'instant'}));await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>followCalls.length),0,'Keyboard selection must not be interrupted');
 // Manual mode never auto-recenters merely because main content scrolls.
 await page.getByRole('button',{name:'手動',exact:true}).click();await page.mouse.move(200,300);await page.evaluate(()=>followCalls=[]);await page.mouse.wheel(0,1000);await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>followCalls.length),0);
 // Opening mobile TOC takes ownership before the first touch.
 await page.setViewportSize({width:390,height:844});await page.locator('#peicd-mobile-toc-toggle').click();await page.evaluate(()=>followCalls=[]);await page.evaluate(()=>scrollTo({top:500,behavior:'instant'}));await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>followCalls.length),0);await page.keyboard.press('Escape');
 assert.deepEqual(errors,[]);console.log(JSON.stringify({layoutSnapback:false,mainWheelResumes:true,hoverProtected:true,focusProtected:true,autoButtonResumes:true,manualModePreserved:true,mobileProtected:true,errors},null,2));await page.close();
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
