// Requires existing Playwright/Chromium; no CDN requests or Git changes.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
const css=fs.readFileSync('theme/assets/pymdownx-extras/自定義.css','utf8');
const rule=css.match(/\.md-content__inner :is\(\.arithmatex, pre\.diagram, \.mermaid, \.peicd-mermaid-host\)[\s\S]*?\{\s*overflow-anchor: none;\s*\}/)?.[0];
assert(rule,'Production CSS must exclude changing render subtrees, not the document.');
async function scenario(browser,kind,stable){
 const page=await browser.newPage({viewport:{width:1000,height:800}});
 try{
  const markup=kind==='inline-math'?'<p style="margin:0">Intro <span class="arithmatex" style="display:inline-block;height:300px">Raw inline math</span></p>':`<pre class="${kind}">${'raw source\n'.repeat(10)}</pre>`;
  await page.setContent(`<style>body{margin:0;font-size:20px;line-height:30px}pre{margin:0;white-space:pre-wrap}${stable?rule:''}</style><article class="md-content__inner"><div style="height:500px"></div>${markup}<p id="reader">Reading text must remain at the same screen position.</p><div style="height:5000px"></div></article>`);
  await page.evaluate(()=>scrollTo(0,600));await page.waitForTimeout(50);
  const before=await page.locator('#reader').evaluate(n=>n.getBoundingClientRect().top);
  await page.locator(kind==='inline-math'?'.arithmatex':'pre').evaluate(n=>{n.innerHTML='<div style="height:30px">Rendered content</div>';if(n.style.height)n.style.height='30px';});await page.waitForTimeout(50);
  const after=await page.locator('#reader').evaluate(n=>n.getBoundingClientRect().top),shift=Math.abs(after-before);
  if(stable){assert(shift<=1,`${kind} reading shift ${shift}`);await page.mouse.wheel(0,120);await page.waitForTimeout(80);const moved=await page.locator('#reader').evaluate(n=>n.getBoundingClientRect().top);assert(moved<after-50,'Do not lock out real user scrolling');}
  else assert(shift>200,'Control must reproduce the unstable native anchor.');
  return {kind,stable,readingShiftPx:shift};
 }finally{await page.close();}
}
(async()=>{const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXE?{executablePath:process.env.CHROMIUM_EXE}:{})});try{
 const result=[await scenario(browser,'arithmatex',false)];for(const kind of ['arithmatex','inline-math','diagram','mermaid','peicd-mermaid-host'])result.push(await scenario(browser,kind,true));console.log(JSON.stringify(result,null,2));
}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
