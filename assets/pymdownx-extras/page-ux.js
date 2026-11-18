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
  const hitKey = "peicd-pending-hit";
  try {
    const pending = JSON.parse(sessionStorage.getItem(hitKey));
    if (pending?.href === location.href) window.__PEICD_SEARCH_TARGET__ = pending;
    sessionStorage.removeItem(hitKey);
  } catch (_) { /* Storage may be disabled. */ }
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
    const delta = (current.target.getClientRects()[0]?.top ?? current.target.getBoundingClientRect().top) - offset;
    // No polling, animation or scroll lock: only react to real layout changes.
    if (Math.abs(delta) > 1.5) window.scrollTo({ top: Math.max(0, scrollY + delta), behavior: "instant" });
  }
  function requestAlignment() {
    if (navigation?.root?.isConnected && !alignmentFrame) alignmentFrame = requestAnimationFrame(alignNavigation);
  }
  function bindNavigation(root) {
    if (!navigation || navigation.path !== pathKey()) return false;
    if (navigation.replaceRoot && root === navigation.sourceRoot) return false;
    const target = navigation.hash ? revealHash(navigation.hash) : root;
    if (!target || !root?.contains(target)) { cancelNavigation(); return false; }
    navigation.observer?.disconnect();
    const landing = window.__PEICD_SEARCH_TARGET__;
    if (landing?.path === location.pathname && landing.hash === navigation.hash) {
      navigation.hit = highlightLanding(root, target, landing);
      window.__PEICD_SEARCH_TARGET__ = null;
      try { sessionStorage.removeItem(hitKey); } catch (_) {}
    }
    navigation.root = root; navigation.target = navigation.hit?.isConnected ? navigation.hit : target;
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
    if (!url.hash && window.__PEICD_SEARCH_TARGET__?.href !== url.href) return false;
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
      return bound;
    },
    isAnchoring: () => Boolean(navigation || restoredURL === location.href),
    isRestoring: () => restoredURL === location.href
  };
  function userScrollIntent(event) {
    if (event.target?.closest?.(".md-sidebar,.md-search,[role='dialog']")) return;
    cancelNavigation();
  }
  function openSearch() {
    const toggle = document.getElementById("__search");
    const input = document.querySelector('[data-md-component="search-query"]');
    if (!toggle || !input) return;
    if (!toggle.checked) toggle.click();
    input.focus({ preventScroll: true });
  }
  document.addEventListener("click", event => {
    if (event.target.closest?.("[data-library-search]")) openSearch();
    const focus = event.target.closest?.(".reading-focus");
    if (focus) {
      const active = document.documentElement.classList.toggle("reading-focused");
      focus.setAttribute("aria-pressed", String(active));
    }
  });
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
      window.dispatchEvent(new CustomEvent("peicd:search-select", { detail: url.href }));
      // Run before document-capture Math anchors can stop Material's close listener.
      const hit = link.querySelector("mark");
      window.__PEICD_SEARCH_TARGET__ = { href: url.href, path: url.pathname, hash: url.hash,
        needle: hit?.textContent || "", bodyHit: Boolean(hit?.closest(".md-search-result__teaser")) };
      try { sessionStorage.setItem(hitKey, JSON.stringify(window.__PEICD_SEARCH_TARGET__)); } catch (_) {}
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
    if (target) revealElement(target);
    return target;
  }
  function revealElement(target) {
    for (let parent = target.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS" && !parent.open) parent.open = true;
      if (parent.classList.contains("tabbed-block")) {
        const set = parent.closest(".tabbed-set"), blocks = set?.querySelector(".tabbed-content");
        const index = blocks ? Array.from(blocks.children).indexOf(parent) : -1;
        const input = index >= 0 ? set.querySelectorAll(":scope > input")[index] : null;
        if (input && !input.checked) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); }
      }
    }
  }
  function highlightLanding(root, heading, landing) {
    // Take the term from the clicked result. OR alternatives and excluded words
    // that did not produce this snippet must not determine the landing.
    const normalize = value => value.normalize("NFKC").toLowerCase().replace(/[\u200b\ufeff]/g, "").replace(/\s+/gu, " ");
    const needle = normalize(landing.needle ?? landing.query ?? "").trim();
    root.querySelectorAll("mark.peicd-search-hit").forEach(mark => mark.replaceWith(...mark.childNodes));
    if (!needle) return null;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    walker.currentNode = heading;
    const level = /^H[1-6]$/.test(heading.tagName) ? Number(heading.tagName[1]) : 0;
    let block = null, nodes = [];
    function markBlock() {
      if (!nodes.length || !normalize(nodes.map(node => node.data).join("")).includes(needle)) return null;
      // Map normalized characters back to the original UTF-16 offsets. This
      // preserves emphasis, links, full-width glyphs and split inline phrases.
      let text = "";
      const positions = [];
      for (const node of nodes) {
        let start = 0;
        for (const char of node.data) {
          const value = normalize(char);
          const end = start + char.length;
          if (value && !(value === " " && text.endsWith(" "))) {
            text += value;
            for (let i = 0; i < value.length; i++) positions.push({ node, start, end });
          }
          start = end;
        }
      }
      const at = text.indexOf(needle);
      if (at < 0) return null;
      const spans = new Map();
      for (const pos of positions.slice(at, at + needle.length)) {
        const span = spans.get(pos.node);
        if (span) span.end = pos.end; else spans.set(pos.node, { start: pos.start, end: pos.end });
      }
      let first;
      for (const [node, span] of spans) {
        const math = node.parentElement.closest(".arithmatex, mjx-container");
        if (math) { first ||= math.closest(".arithmatex") || math; continue; }
        const range = document.createRange();
        range.setStart(node, span.start); range.setEnd(node, span.end);
        const mark = document.createElement("mark"); mark.className = "peicd-search-hit";
        range.surroundContents(mark); first ||= mark;
      }
      if (first) revealElement(first);
      return first;
    }
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      const title = parent.closest("h1,h2,h3,h4,h5,h6");
      if (level && title && title !== heading && Number(title.tagName[1]) <= level) break;
      if ((landing.bodyHit && title === heading) || parent.closest("script,style,button,.headerlink,.peicd-folder-pathbar,.md-code__nav")) continue;
      const nextBlock = parent.closest("p,li,td,th,dt,dd,pre,h1,h2,h3,h4,h5,h6,summary") || parent;
      if (nextBlock !== block) {
        const hit = markBlock();
        if (hit) return hit;
        nodes = []; block = nextBlock;
      }
      nodes.push(node);
    }
    return markBlock();
  }
  function onPage() {
    const root = document.querySelector(".md-content__inner");
    document.querySelector(".reading-focus")?.setAttribute("aria-pressed",
      String(document.documentElement.classList.contains("reading-focused")));
    if (navigation) bindNavigation(root);
    else if (root !== lastRoot && (location.hash || window.__PEICD_SEARCH_TARGET__) && restoredURL !== location.href) beginNavigation(new URL(location.href));
    lastRoot = root; lastPath = pathKey();
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
  });
})();
