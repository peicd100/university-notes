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

  let navigation = null, alignmentFrame = 0, lastRoot = null, lastPath = null, restoredURL = null;
  const pathKey = () => location.pathname + location.search;
  function cancelNavigation() {
    navigation?.observer?.disconnect();
    navigation = null; restoredURL = null;
    if (alignmentFrame) cancelAnimationFrame(alignmentFrame);
    alignmentFrame = 0;
  }
  function alignNavigation() {
    if (alignmentFrame) cancelAnimationFrame(alignmentFrame);
    alignmentFrame = 0;
    const current = navigation;
    if (!current?.root?.isConnected || !current.target?.isConnected) return;
    const offset = (document.querySelector(".md-header")?.offsetHeight || 56) + 12;
    const delta = current.target.getBoundingClientRect().top - offset;
    // No polling, animation or scroll lock: only react to real layout changes.
    if (Math.abs(delta) > 1.5) window.scrollTo({ top: Math.max(0, scrollY + delta), behavior: "instant" });
  }
  function requestAlignment() {
    if (navigation?.root?.isConnected && !alignmentFrame) alignmentFrame = requestAnimationFrame(alignNavigation);
  }
  function bindNavigation(root) {
    if (!navigation || navigation.path !== pathKey()) return false;
    if (navigation.replaceRoot && root === navigation.sourceRoot) return false;
    const target = revealHash(navigation.hash);
    if (!target || !root?.contains(target)) { cancelNavigation(); return false; }
    navigation.observer?.disconnect();
    navigation.root = root; navigation.target = target;
    navigation.sourceRoot = null; navigation.replaceRoot = false; // Release the detached previous article.
    if ("ResizeObserver" in window) {
      // ResizeObserver is already batched before paint. Correct here rather than
      // one frame later; scrolling does not resize the observed article.
      navigation.observer = new ResizeObserver(alignNavigation);
      navigation.observer.observe(root);
    }
    requestAlignment();
    return true;
  }
  function beginNavigation(url) {
    cancelNavigation();
    if (!url.hash) return false;
    const root = document.querySelector(".md-content__inner");
    navigation = { path: url.pathname + url.search, hash: url.hash, sourceRoot: root,
      replaceRoot: url.pathname !== location.pathname, root: null, target: null };
    if (!navigation.replaceRoot) return bindNavigation(root);
    return true;
  }
  window.__PEICD_PAGE_UX__ = {
    navigateToHash(hash) {
      if (restoredURL === location.href) return false;
      const url = new URL(location.href); url.hash = hash;
      const bound = navigation?.path === pathKey() && navigation.hash === url.hash
        ? bindNavigation(document.querySelector(".md-content__inner")) : beginNavigation(url);
      if (bound) highlightLanding();
      return bound;
    },
    isAnchoring: () => Boolean(navigation || restoredURL === location.href),
    isRestoring: () => restoredURL === location.href
  };
  function userScrollIntent(event) {
    if (event.target?.closest?.(".md-sidebar,.md-search,[role='dialog']")) return;
    cancelNavigation();
  }
  window.addEventListener("wheel", userScrollIntent, { capture: true, passive: true });
  window.addEventListener("touchmove", userScrollIntent, { capture: true, passive: true });
  window.addEventListener("pointerdown", userScrollIntent, { capture: true, passive: true });
  window.addEventListener("keydown", event => {
    if (!["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(event.key)) return;
    if (event.target?.closest?.("input,textarea,select,[contenteditable='true']")) return;
    userScrollIntent(event);
  }, true);
  window.addEventListener("popstate", () => {
    cancelNavigation();
    if (typeof history.state?.y === "number") {
      restoredURL = location.href;
      // Math-local history can be ahead of Material's deduplicated location$.
      if (lastRoot?.isConnected && lastPath === pathKey()) window.scrollTo({ top: history.state.y, behavior: "instant" });
    }
  }, true);
  for (const name of ["resize", "peicd:math-rendered", "peicd:mermaid-updated"]) window.addEventListener(name, requestAlignment);
  document.addEventListener("load", event => { if (event.target?.tagName === "IMG") requestAlignment(); }, true);
  document.fonts?.addEventListener("loadingdone", requestAlignment);

  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button > 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest?.("a[href]");
    if (!link || link.target || link.hasAttribute("download")) return;
    let url;
    try { url = new URL(link.href, location.href); } catch (_) { return; }
    if (url.origin !== location.origin) return;
    if (link.classList.contains("peicd-danger-link")) { cancelNavigation(); return; }
    if (link.closest('[data-md-component="search-result"]')) {
      // Run before document-capture Math anchors can stop Material's close listener.
      window.__PEICD_SEARCH_TARGET__ = { path: url.pathname, hash: url.hash,
        query: document.querySelector('[data-md-component="search-query"]')?.value || "" };
      const toggle = document.getElementById("__search");
      if (toggle?.checked) { toggle.checked = false; toggle.dispatchEvent(new Event("change", { bubbles: true })); }
      if (document.activeElement?.closest?.('[data-md-component="search"]')) document.activeElement.blur();
    }
    beginNavigation(url);
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

  function revealHash(hash = location.hash) {
    let target;
    try { target = document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch (_) { return; }
    if (!target) return;
    for (let parent = target.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS" && !parent.open) parent.open = true;
      if (parent.classList.contains("tabbed-block")) {
        const set = parent.closest(".tabbed-set"), blocks = set?.querySelector(".tabbed-content");
        const index = blocks ? Array.from(blocks.children).indexOf(parent) : -1;
        const input = index >= 0 ? set.querySelectorAll(":scope > input")[index] : null;
        if (input && !input.checked) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); }
      }
    }
    return target;
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
  function onPage() {
    const root = document.querySelector(".md-content__inner");
    if (navigation) bindNavigation(root);
    else if (root !== lastRoot && location.hash && restoredURL !== location.href) beginNavigation(new URL(location.href));
    lastRoot = root; lastPath = pathKey();
    highlightLanding();
  }
  document.addEventListener("DOMContentLoaded", () => {
    onPage();
    window.document$?.subscribe(onPage);
  }, { once: true });
  window.addEventListener("hashchange", () => {
    if (lazyActive && !eagerBoot && /^#(?:__code|__codelineno|annotation)/.test(location.hash)) {
      location.reload(); return;
    }
    if (restoredURL === location.href) return;
    window.__PEICD_PAGE_UX__.navigateToHash(location.hash);
    highlightLanding();
  });
})();
