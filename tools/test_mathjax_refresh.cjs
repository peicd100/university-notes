const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('theme/assets/pymdownx-extras/mathjax-refresh.js','utf8');

function fixture(tex = ['x=1','y=2','z=3','w=4'], semantic = false, convert = false, initialMathJax = {}) {
  const calls = [], events = {}, subscriptions = [], notifications = [];
  const nodes = tex.map((textContent,index) => ({
    textContent, isConnected:true, rendered:false,
    getClientRects:()=>[{}], getBoundingClientRect:()=>({top:index*1600,bottom:index*1600+20}),
    replaceChildren(output){this.rendered=true;this.output=output;},
    querySelector(){return this.rendered ? {} : null;}
  }));
  if(semantic) nodes[0].textContent = String.raw`\newcommand{\foo}{x}`;
  const target={isConnected:true,querySelector:()=>nodes[0],querySelectorAll:()=>nodes,contains:n=>nodes.includes(n)};
  const location={href:'http://localhost/a.html',origin:'http://localhost',pathname:'/a.html',search:'',hash:''};
  const api={startup:{promise:Promise.resolve()},typesetClear:()=>calls.push('clear'),texReset:()=>calls.push('reset'),
    typesetPromise:async batch=>{calls.push(batch.map(n=>nodes.indexOf(n)));await new Promise(r=>setTimeout(r,2));batch.forEach(n=>n.rendered=true);},
    typeset:batch=>batch.forEach(n=>n.rendered=true)};
  if(convert){api.tex2chtmlPromise=async tex=>{calls.push('convert:'+tex);return {tex};};api.chtmlStylesheet=()=>({id:'MJX-CHTML-styles'});}
  let currentTarget=target;
  let stylesheet=null;
  let autoTypeset, startupConfig;
  const document={readyState:'complete',body:target,querySelector:()=>currentTarget,
    getElementById:id=>id==='node2'?nodes[2]:(id==='MJX-CHTML-styles'?stylesheet:null),addEventListener:(name,fn)=>events['document-'+name]=fn,createElement:()=>({addEventListener(type,fn){this[type]=fn;}}),
    head:{appendChild(script){if(script.id==='MJX-CHTML-styles'){stylesheet=script;return;}queueMicrotask(()=>{autoTypeset=window.MathJax.startup.typeset;startupConfig=JSON.parse(JSON.stringify(window.MathJax));window.MathJax=api;script.load();});}}};
  const window={MathJax:initialMathJax,print:()=>calls.push('print'),alert:()=>calls.push('alert'),
    scrollY:0,scrollTo:()=>{},dispatchEvent:event=>notifications.push(event),
    addEventListener:(name,fn)=>events[name]=fn,document$:{subscribe:fn=>subscriptions.push(fn)},requestIdleCallback:()=>1};
  const history={state:null,pushState(state,title,hash){location.hash=hash;}};
  const context=vm.createContext({window,document,innerHeight:900,location,history,performance,URL,
    getComputedStyle:()=>({fontSize:'16px'}),
    CustomEvent:class {constructor(type,options={}){this.type=type;this.detail=options.detail;}}, setTimeout,console,Promise,Set,WeakSet,WeakMap});
  vm.runInContext(source,context);
  return {window,nodes,calls,events,subscriptions,notifications,get autoTypeset(){return autoTypeset;},get startupConfig(){return startupConfig;},setTarget:t=>currentTarget=t};
}

test('startup disabled, viewport first, then renderAll exactly once per formula', async()=>{
  const f=fixture();
  await new Promise(r=>setTimeout(r,30));
  assert.equal(f.autoTypeset,false);
  assert.equal(f.nodes[0].rendered,true);
  assert.equal(f.nodes[3].rendered,false);
  assert.equal(await f.window.__PEICD_MATH__.renderAll(),true);
  assert(f.nodes.every(n=>n.rendered));
  const all=f.calls.filter(Array.isArray).flat();
  assert.deepEqual(all,[0,1,2,3]);
  assert.equal(f.calls.filter(x=>x==='reset').length,1);
  assert(!f.calls.includes('clear'));
  assert(f.calls.filter(Array.isArray).every(x=>x.length<=4));
});

test('sidebar prioritizes article sources without registering clones or rendering twice',async()=>{
  const f=fixture();f.window.__PEICD_MATH__.prioritize([f.nodes[3],{textContent:'sidebar clone'}]);
  await new Promise(r=>setTimeout(r,35));
  assert(f.nodes[3].rendered);assert(!f.nodes[1].rendered);
  const before=f.calls.length;f.window.__PEICD_MATH__.prioritize([f.nodes[3]]);
  await new Promise(r=>setTimeout(r,10));assert.equal(f.calls.length,before);
  await f.window.__PEICD_MATH__.renderAll();
  assert.deepEqual(f.calls.filter(Array.isArray).flat().sort(),[0,1,2,3]);
});

test('render notifications are emitted after owned article outputs commit',async()=>{
  const f=fixture();await f.window.__PEICD_MATH__.renderAll();
  assert.equal(f.notifications.filter(e=>e.type==='peicd:math-ready').length,1);
  const nodes=f.notifications.filter(e=>e.type==='peicd:math-rendered').flatMap(e=>e.detail.nodes);
  assert.deepEqual(nodes,f.nodes);assert(nodes.every(n=>n.rendered));
});

test('official mathtools extension is configured without losing author packages',async()=>{
  for(const packages of [undefined,{'[+]':['color']},['base','ams']]){
    const f=fixture(['x'],false,false,{loader:{load:['[tex]/color']},tex:{packages}});
    await f.window.__PEICD_MATH__.renderAll();
    assert.deepEqual(f.startupConfig.loader.load,['[tex]/color','[tex]/mathtools']);
    const result=f.startupConfig.tex.packages;
    assert((Array.isArray(result)?result:result['[+]']).includes('mathtools'));
    if(Array.isArray(packages))assert(result.includes('ams'));
    else if(packages)assert(result['[+]'].includes('color'));
  }
});

test('stateless math uses independent conversion rather than global rescans',async()=>{
  const f=fixture([String.raw`\(x=1\)`,String.raw`\[y=2\]`],false,true);
  await f.window.__PEICD_MATH__.renderAll();
  assert(f.nodes.every(n=>n.rendered));
  assert.deepEqual(f.calls.filter(x=>typeof x==='string'&&x.startsWith('convert:')),['convert:x=1','convert:y=2']);
  assert.equal(f.calls.filter(Array.isArray).length,0);
});

test('same-page document/hash events do not re-typeset or reset',async()=>{
  const f=fixture();await f.window.__PEICD_MATH__.renderAll();
  const before=f.calls.length;
  f.subscriptions.forEach(fn=>fn());f.events.hashchange({stopImmediatePropagation(){}});
  await new Promise(r=>setTimeout(r,15));
  assert.equal(f.calls.length,before);
});

test('local anchor clicks bypass DOM-replacing instant navigation',async()=>{
  const f=fixture();await f.window.__PEICD_MATH__.renderAll();
  const before=f.calls.length;let prevented=false,stopped=false;
  const link={href:'http://localhost/a.html#node2',target:'',hasAttribute:()=>false,classList:{contains:()=>false}};
  f.events['document-click']({button:0,target:{closest:()=>link},preventDefault(){prevented=true;},stopPropagation(){stopped=true;}});
  await new Promise(r=>setTimeout(r,15));
  assert(prevented&&stopped);assert.equal(f.calls.length,before);
});

test('semantic TeX batches maintain document order',async()=>{
  const f=fixture(['x','y','z','w'],true);await f.window.__PEICD_MATH__.renderAll();
  assert.deepEqual(f.calls.filter(Array.isArray).flat(),[0,1,2,3]);
});

test('print waits until every formula has rendered',async()=>{
  const f=fixture();await f.window.print();
  assert(f.nodes.every(n=>n.rendered));assert.equal(f.calls.at(-1),'print');
});

test('leaving a math page cleans the registry without restarting it',async()=>{
  const f=fixture();await f.window.__PEICD_MATH__.renderAll();
  f.setTarget({querySelector:()=>null});f.subscriptions.forEach(fn=>fn());
  await new Promise(r=>setTimeout(r,15));
  assert.equal(f.calls.at(-1),'clear');
});
