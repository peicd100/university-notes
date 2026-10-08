(function () {
  "use strict";

  const SCRIPT_ID = "peicd-mathjax-runtime";
  const SRC = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js";
  const SEMANTIC_TEX = /\\(?:def|gdef|edef|xdef|let|newcommand|renewcommand|providecommand|DeclareMathOperator|label|ref|eqref|tag|require)\b|\\begin\{(?:equation|align|alignat|gather|multline)\}/;
  const states = new WeakMap();
  let current = null;
  let previous = null;
  let runtime = null;
  let running = false;
  let batchSize = 2;
  let idleHandle = null;
  let printing = false;
  const metrics = { batches: 0, processed: 0, maxBatchMs: 0, maxBatchIndex: -1, pageResets: 0 };

  function loadMathJax() {
    if (window.MathJax?.typesetPromise) return Promise.resolve(window.MathJax);
    if (runtime) return runtime;
    // Disable MathJax's automatic whole-document pass. This queue is its sole
    // owner; clearing the registry and re-scanning rendered MathML duplicates it.
    window.MathJax = window.MathJax || {};
    window.MathJax.startup = { ...window.MathJax.startup, typeset: false };
    // GPT's proof sheets use mathtools arrows such as \\xRightarrow. Without
    // this package, noundefined can silently print the command in red rather
    // than create an mjx-merror node. Load the official extension once.
    const packages = window.MathJax.tex?.packages;
    window.MathJax.loader = { ...window.MathJax.loader,
      load: [...new Set([...(window.MathJax.loader?.load || []), "[tex]/mathtools"])] };
    window.MathJax.tex = { ...window.MathJax.tex,
      packages: Array.isArray(packages) ? [...new Set([...packages, "mathtools"])] :
        { ...packages, "[+]": [...new Set([...(packages?.["[+]"] || []), "mathtools"])] } };
    // Generate font CSS once, rather than repeatedly growing/replacing a
    // stylesheet (and recalculating the entire long article) for each batch.
    window.MathJax.chtml = { ...window.MathJax.chtml, adaptiveCSS: false };
    runtime = new Promise((resolve, reject) => {
      let script = document.getElementById(SCRIPT_ID);
      if (!script) {
        script = document.createElement("script");
        script.id = SCRIPT_ID;
        script.src = SRC;
        script.async = true;
        document.head.appendChild(script);
      }
      script.addEventListener("load", async () => {
        try {
          await window.MathJax.startup.promise;
          resolve(window.MathJax);
        } catch (error) { reject(error); }
      }, { once: true });
      script.addEventListener("error", reject, { once: true });
    });
    return runtime;
  }

  function visible(node, margin = 600) {
    if (!node.isConnected || !node.getClientRects().length) return false;
    const box = node.getBoundingClientRect();
    return box.bottom >= -margin && box.top <= innerHeight + margin;
  }

  function outstanding(state) {
    return state.nodes.some((node) => node.isConnected && !state.done.has(node));
  }

  function settle(state) {
    if (outstanding(state)) return;
    state.waiters.splice(0).forEach((resolve) => resolve(true));
    state.observer?.disconnect();
  }

  function enqueue(state, nodes, priority = true) {
    if (state.failed) return;
    const wanted = nodes.filter((node) => node.isConnected && !state.done.has(node));
    if (state.semantic && wanted.length) {
      const end = Math.max(...wanted.map((node) => state.nodes.indexOf(node)));
      nodes = state.nodes.slice(0, end + 1); // Preserve macros, references and AMS numbering order.
    }
    nodes.forEach((node) => {
      if (!node.isConnected || state.done.has(node)) return;
      state.queue.add(node);
      if (priority) state.priority.add(node);
    });
    pump();
  }

  function yieldToBrowser() {
    // Unlike an await of an already-resolved Promise, this yields to input and
    // paint. No requestAnimationFrame dependency (background tabs/print still work).
    return new Promise((resolve) => setTimeout(resolve, 0));
  }

  function scheduleBackground() {
    if (idleHandle !== null || !current || current.failed || !outstanding(current)) return;
    const work = () => {
      idleHandle = null;
      const state = current;
      if (!state || running) { scheduleBackground(); return; }
      const node = state.nodes.find((item) => item.isConnected && !state.done.has(item));
      if (node) enqueue(state, [node], false);
    };
    idleHandle = window.requestIdleCallback
      ? window.requestIdleCallback(work, { timeout: 1000 })
      : setTimeout(work, 80);
  }

  async function pump() {
    if (running || !current?.queue.size) return;
    running = true;
    try {
      const math = await loadMathJax();
      while (current?.queue.size) {
        const state = current;
        if (!state.initialized) {
          if (previous && previous !== state) math.typesetClear?.([previous.target]);
          math.texReset?.();
          state.initialized = true;
          previous = state;
          metrics.pageResets += 1;
        }
        const candidates = state.nodes.filter((node) => state.queue.has(node) && node.isConnected);
        if (!state.semantic) candidates.sort((a, b) => Number(state.priority.has(b)) - Number(state.priority.has(a)));
        const batch = candidates.slice(0, batchSize);
        if (!batch.length) { state.queue.clear(); break; }
        batch.forEach((node) => { state.queue.delete(node); state.priority.delete(node); });
        const start = performance.now();
        if (!state.semantic && math.tex2chtmlPromise) {
          // Stateless formulas can be converted independently. typesetPromise
          // resets the document's processing pipeline on each call; doing that
          // hundreds of times revisits old math and causes quadratic work.
          const outputs = [];
          for (const node of batch) {
            const raw = node.textContent.trim();
            const display = raw.startsWith("\\[");
            const bracketed = (display && raw.endsWith("\\]")) ||
              (raw.startsWith("\\(") && raw.endsWith("\\)"));
            if (!bracketed) { await math.typesetPromise([node]); continue; }
            const em = parseFloat(getComputedStyle(node).fontSize) || 16;
            const containerWidth = node.parentElement?.clientWidth || state.target.clientWidth || 800;
            const output = await math.tex2chtmlPromise(raw.slice(2, -2), {
              display, em, ex: em * 0.5, containerWidth
            });
            outputs.push([node, output]);
          }
          if (!document.getElementById("MJX-CHTML-styles")) {
            document.head.appendChild(math.chtmlStylesheet());
          }
          // Commit only after conversion succeeds, and only to its owned page.
          if (current === state) outputs.forEach(([node, output]) => {
            if (node.isConnected) node.replaceChildren(output);
          });
        } else {
          await math.typesetPromise(batch); // Semantic TeX keeps MathJax's shared document/state.
        }
        const elapsed = performance.now() - start;
        metrics.batches += 1;
        if (elapsed > metrics.maxBatchMs) {
          metrics.maxBatchMs = elapsed;
          metrics.maxBatchIndex = state.nodes.indexOf(batch[0]);
        }
        // Bound subsequent synchronous work instead of processing 1000+ formulas
        // in one long task. A single complicated formula is the minimum unit.
        if (elapsed > 40) batchSize = 1;
        else if (elapsed < 12) batchSize = Math.min(4, batchSize + 1);
        batch.forEach((node) => {
          state.done.add(node);
          state.observer?.unobserve(node);
          metrics.processed += 1;
        });
        settle(state);
        if (current === state) window.dispatchEvent(new CustomEvent("peicd:math-rendered", { detail: { nodes: batch } }));
        await yieldToBrowser();
      }
    } catch (error) {
      console.warn("MathJax incremental render failed", error);
      // Keep original TeX visible on failure. Never silently hide a formula.
      if (current) {
        current.failed = true;
        current.observer?.disconnect();
        current.waiters.splice(0).forEach((resolve) => resolve(false));
        current.queue.clear();
      }
    } finally {
      running = false;
      if (!current && previous && window.MathJax?.typesetClear) {
        window.MathJax.typesetClear([previous.target]);
        previous = null;
      }
      scheduleBackground();
    }
  }

  function scan() {
    const target = document.querySelector(".md-content__inner") || document.body;
    if (!target?.querySelector(".arithmatex")) {
      current?.observer?.disconnect();
      current?.waiters.splice(0).forEach((resolve) => resolve(false));
      current = null;
      if (!running && previous && window.MathJax?.typesetClear) {
        window.MathJax.typesetClear([previous.target]);
        previous = null;
      }
      return;
    }
    if (current?.target === target) return; // Same-page hash/document$ is NOT a new page.
    current?.observer?.disconnect();
    current?.waiters.splice(0).forEach((resolve) => resolve(false));
    let state = states.get(target);
    if (!state) {
      const nodes = Array.from(target.querySelectorAll(".arithmatex"));
      state = { target, nodes, urlKey: location.pathname + location.search,
        semantic: nodes.some((node) => SEMANTIC_TEX.test(node.textContent)),
        done: new WeakSet(), queue: new Set(), priority: new Set(), waiters: [], initialized: false, observer: null };
      nodes.filter((node) => node.querySelector("mjx-container")).forEach((node) => state.done.add(node));
      states.set(target, state);
    }
    current = state;
    if (window.IntersectionObserver) {
      state.observer = new IntersectionObserver((entries) => {
        if (current !== state) return;
        enqueue(state, entries.filter((entry) => entry.isIntersecting).map((entry) => entry.target));
      }, { rootMargin: "600px 0px" });
      state.nodes.filter((node) => !state.done.has(node)).forEach((node) => state.observer.observe(node));
    }
    enqueue(state, state.nodes.filter((node) => visible(node)));
    scheduleBackground();
    prepareHash();
  }

  function prioritize(nodes) {
    scan();
    const state = current;
    if (state && !state.failed) enqueue(state, Array.from(nodes).filter((node) => state.nodes.includes(node)));
  }

  function renderAll() {
    scan();
    const state = current;
    if (state?.failed) return Promise.resolve(false);
    if (!state || !outstanding(state)) return Promise.resolve(true);
    const result = new Promise((resolve) => state.waiters.push(resolve));
    enqueue(state, state.nodes);
    return result;
  }

  async function prepareHash() {
    const state = current;
    if (!state || !location.hash) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target || !state.target.contains(target)) return;
    // Let Material/TOC choose the scroll position; prioritize formulas around
    // that position. IntersectionObserver follows subsequent layout changes.
    await yieldToBrowser();
    if (current === state) enqueue(state, state.nodes.filter((node) => visible(node, 900)));
  }

  function scrollToHash() {
    if (!current || current.urlKey !== location.pathname + location.search) return false;
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (_) { return false; }
    if (location.hash && !target) return false;
    const header = document.querySelector(".md-header");
    const top = target ? target.getBoundingClientRect().top + window.scrollY - (header?.offsetHeight || 56) - 12 : 0;
    window.scrollTo({ top: Math.max(0, top), behavior: "auto" });
    prepareHash();
    window.dispatchEvent(new CustomEvent("peicd:math-anchor"));
    return true;
  }

  // Material instant navigation can replace even a same-page hash document.
  // Keep its current DOM (and math registry) for local anchors; real page changes
  // still use Material. Respect modified clicks, downloads and Danger's own handler.
  document.addEventListener("click", (event) => {
    if (!current || event.defaultPrevented || event.button > 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest?.("a[href]");
    if (!link || link.target === "_blank" || link.hasAttribute("download") || link.classList.contains("peicd-danger-link")) return;
    const url = new URL(link.href, location.href);
    if (!url.hash || url.origin !== location.origin || url.pathname + url.search !== current.urlKey) return;
    let target;
    try { target = document.getElementById(decodeURIComponent(url.hash.slice(1))); } catch (_) { return; }
    if (!target) return;
    event.preventDefault();
    event.stopPropagation();
    if (url.hash !== location.hash) history.pushState(history.state, "", url.hash);
    scrollToHash();
  }, true);
  for (const name of ["popstate", "hashchange"]) {
    window.addEventListener(name, (event) => {
      if (current?.target.isConnected && scrollToHash()) event.stopImmediatePropagation();
    }, true);
  }

  const nativePrint = window.print.bind(window);
  window.print = async function () {
    if (printing) return;
    printing = true;
    try {
      const ok = await renderAll();
      if (ok) nativePrint();
      else window.alert("公式尚未完成排版，請確認網路後再列印。");
    } finally { printing = false; }
  };
  window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "p") {
      event.preventDefault();
      window.print();
    }
  }, true);
  window.addEventListener("beforeprint", () => {
    // Browser-menu print cannot await an event handler. If the runtime is ready,
    // synchronously finish remaining formulas; Ctrl+P/window.print use the
    // responsive asynchronous path above instead.
    const state = current;
    const math = window.MathJax;
    if (!state || !math?.typeset || !outstanding(state)) return;
    if (running || !state.initialized) {
      renderAll();
      console.warn("Formulas are still rendering; use Ctrl+P to wait before printing");
      return; // Never run synchronous typeset concurrently with typesetPromise.
    }
    const nodes = state.nodes.filter((node) => node.isConnected && !state.done.has(node));
    try {
      math.typeset(nodes);
      nodes.forEach((node) => { state.done.add(node); state.queue.delete(node); state.priority.delete(node); });
      settle(state);
      window.dispatchEvent(new CustomEvent("peicd:math-rendered", { detail: { nodes } }));
    } catch (error) { console.warn("Prepare formulas with Ctrl+P before printing", error); }
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", scan, { once: true });
  else scan();
  window.document$?.subscribe(scan);
  window.__PEICD_MATH__ = { renderAll, prioritize, metrics };
  window.dispatchEvent(new CustomEvent("peicd:math-ready"));
})();
