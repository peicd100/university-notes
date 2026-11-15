/* Must run before Material reads __config. Content stays in the initial HTML. */
(function () {
  "use strict";
  const config = document.getElementById("__config");
  let eagerBoot = false, lazyActive = false;
  const eagerRoutes = new Set();
  try {
    JSON.parse(document.getElementById("__peicd_eager_routes")?.textContent || "[]")
      .forEach(url => eagerRoutes.add(new URL(url, document.baseURI).pathname));
  } catch (_) { /* A missing optional manifest must not block the page. */ }
  // Material 9.7.1 warns that lazy annotations cannot resolve initial anchors.
  // Keep those pages, and direct code/annotation deep links, on its eager path.
  const anchoredCode = /^#(?:__code|__codelineno|annotation)/.test(location.hash);
  if (config) {
    try {
      const data = JSON.parse(config.textContent), features = data.features || [];
      lazyActive = features.includes("content.lazy");
      const nativeSelection = features.includes("content.code.select") || features.includes("content.code.annotate");
      if (anchoredCode || nativeSelection || document.querySelector(".highlight.annotate, .codehilite.annotate, .highlight.select, .codehilite.select, .md-annotation")) {
        eagerBoot = features.includes("content.lazy");
        data.features = features.filter(name => name !== "content.lazy");
        config.textContent = JSON.stringify(data);
      }
    } catch (_) { /* Material retains responsibility for configuration errors. */ }
  }

  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button > 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest?.("a[href]");
    if (!link || link.target || link.hasAttribute("download")) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin) return;
    const codeHash = /^#(?:__code|__codelineno|annotation)/.test(url.hash);
    if (codeHash && url.pathname === location.pathname && lazyActive && !eagerBoot) {
      // Numeric code ids are assigned at mount time. Reload conservatively for
      // a legacy deep link instead of sending it to a different lazy block.
      event.preventDefault(); event.stopPropagation();
      history.replaceState(history.state, "", url.href); location.reload(); return;
    }
    if (codeHash || eagerRoutes.has(url.pathname) || (eagerBoot && url.pathname !== location.pathname)) {
      link.target = "_self"; // Material 9.7.1 respects explicit targets; normal pages stay instant.
    }
  }, true);

  function revealHash() {
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
    catch (_) { return; }
    if (!target) return;
    let changed = false;
    for (let parent = target.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS" && !parent.open) { parent.open = true; changed = true; }
      if (parent.classList.contains("tabbed-block")) {
        const set = parent.closest(".tabbed-set"), blocks = set?.querySelector(".tabbed-content");
        const index = blocks ? Array.from(blocks.children).indexOf(parent) : -1;
        const input = index >= 0 ? set.querySelectorAll(":scope > input")[index] : null;
        if (input && !input.checked) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); changed = true; }
      }
    }
    if (changed) requestAnimationFrame(() => target.isConnected && target.scrollIntoView({ block: "start" }));
  }
  function highlightLanding() {
    const landing = window.__PEICD_SEARCH_TARGET__;
    if (!landing || landing.path !== location.pathname) return;
    window.__PEICD_SEARCH_TARGET__ = null;
    let target;
    try { target = document.getElementById(decodeURIComponent(landing.hash.slice(1))); } catch (_) { return; }
    const root = document.querySelector(".md-content__inner");
    if (!target || !root?.contains(target)) return;
    const terms = [...String(landing.query).normalize("NFKC").toLowerCase().matchAll(/"([^"]+)"|(\S+)/g)]
      .map(match => match[1] || match[2]).filter(term => term.length > 1 && !/[~*:^]/.test(term));
    if (!terms.length) return;
    root.querySelectorAll("mark.peicd-search-hit").forEach(mark => mark.replaceWith(document.createTextNode(mark.textContent)));
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    walker.currentNode = target;
    const nodes = [], level = /^H[1-6]$/.test(target.tagName) ? Number(target.tagName[1]) : 0;
    let node;
    while ((node = walker.nextNode()) && nodes.length < 500) {
      const heading = node.parentElement.closest("h1,h2,h3,h4,h5,h6");
      if (level && heading && heading !== target && Number(heading.tagName[1]) <= level) break;
      if (!node.parentElement.closest("script,style,.arithmatex,mjx-container,button,.md-code__nav")) nodes.push(node);
    }
    let index = 0, marked = 0;
    function chunk() {
      const end = Math.min(index + 40, nodes.length);
      for (; index < end && marked < 30; index++) {
        const text = nodes[index].nodeValue, folded = text.normalize("NFKC").toLowerCase();
        if (!nodes[index].isConnected || folded.length !== text.length) continue;
        const ranges = [];
        for (const term of terms) {
          let at = folded.indexOf(term);
          while (at >= 0 && ranges.length < 30) { ranges.push([at, at + term.length]); at = folded.indexOf(term, at + term.length); }
        }
        ranges.sort((a, b) => a[0] - b[0]);
        const merged = [];
        for (const range of ranges) {
          const last = merged.at(-1);
          if (last && range[0] <= last[1]) last[1] = Math.max(last[1], range[1]); else merged.push(range);
        }
        if (!merged.length) continue;
        const fragment = document.createDocumentFragment();
        let position = 0;
        for (const [from, to] of merged) {
          fragment.append(document.createTextNode(text.slice(position, from)));
          const mark = document.createElement("mark"); mark.className = "peicd-search-hit"; mark.textContent = text.slice(from, to);
          fragment.append(mark); position = to; marked++;
        }
        fragment.append(document.createTextNode(text.slice(position)));
        nodes[index].replaceWith(fragment);
      }
      if (index < nodes.length && marked < 30 && root.isConnected) requestAnimationFrame(chunk);
    }
    requestAnimationFrame(chunk);
  }
  function onPage() { revealHash(); highlightLanding(); }
  document.addEventListener("DOMContentLoaded", () => {
    onPage();
    window.document$?.subscribe(onPage);
  }, { once: true });
  window.addEventListener("hashchange", () => {
    if (lazyActive && !eagerBoot && /^#(?:__code|__codelineno|annotation)/.test(location.hash)) {
      location.reload(); return;
    }
    revealHash();
  });
})();
