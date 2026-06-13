(function () {
  "use strict";

  const currentScript = document.currentScript;
  const assetBase = new URL(".", currentScript?.src || document.baseURI);
  const loaded = new Map();
  const ASSETS = {
    folderPath: "folder-path-bar.js?v=20260614-2",
    imageZoom: "image-zoom.js?v=20260614-2",
    legacyImageWidth: "legacy-image-width.js?v=20260614-2",
    markdownEmbed: "markdown-embed.js?v=20260516-1",
    mathjaxRefresh: "mathjax-refresh.js?v=20260614-2",
    mermaidConfig: "mermaid-config-override.js?v=20260523-1",
    mermaidLegacy: "mermaid-legacy-flowchart-compat.js?v=20260614-1",
    mermaidRender: "mermaid-render-fix.js?v=20260614-1",
    mermaidZoom: "mermaid-zoom.js?v=20260404-1",
    scrollBottom: "scroll-bottom.js?v=20260424-3",
    sourceJump: "source-jump.js?v=20260523-2",
    tocFold: "toc-fold.js?v=20260611-2"
  };

  const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
  let scanQueued = false;
  let mermaidToolsPromise = null;

  function scriptUrl(name) {
    return new URL(name, assetBase).href;
  }

  function loadScriptOnce(name) {
    const src = scriptUrl(name);
    if (loaded.has(src)) return loaded.get(src);

    const existing = Array.from(document.scripts).find((script) => script.src === src);
    if (existing) {
      const promise = existing.dataset.peicdLoaded === "true"
        ? Promise.resolve(existing)
        : new Promise((resolve, reject) => {
          existing.addEventListener("load", () => resolve(existing), { once: true });
          existing.addEventListener("error", reject, { once: true });
        });
      loaded.set(src, promise);
      return promise;
    }

    const promise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.dataset.peicdConditionalLoader = "true";
      script.addEventListener("load", () => {
        script.dataset.peicdLoaded = "true";
        resolve(script);
      }, { once: true });
      script.addEventListener("error", reject, { once: true });
      document.head.appendChild(script);
    }).catch((error) => {
      loaded.delete(src);
      console.warn("[peicd-loader] failed to load", name, error);
    });

    loaded.set(src, promise);
    return promise;
  }

  function hasArticleRoot() {
    return Boolean(document.querySelector("article.md-content__inner, .md-content__inner.md-typeset"));
  }

  function hasArticleImages() {
    return Boolean(document.querySelector([
      "article.md-content__inner.md-typeset img:not(.twemoji)",
      ".md-content__inner.md-typeset img:not(.twemoji)"
    ].join(", ")));
  }

  function hasLegacyImageWidth() {
    return Array.from(document.querySelectorAll("img[src]")).some((img) => /=\d+%x$/.test(img.getAttribute("src") || ""));
  }

  function hasMermaid() {
    return Boolean(document.querySelector("pre.diagram, .peicd-mermaid-host"));
  }

  function hasMath() {
    return Boolean(document.querySelector(".arithmatex"));
  }

  function hasMarkdownEmbed() {
    return Boolean(document.querySelector("[data-peicd-markdown-embed]"));
  }

  function hasTocOrDangerUi() {
    return Boolean(document.querySelector([
      "[data-md-component='toc']",
      ".md-sidebar--secondary",
      ".admonition.danger",
      "details.danger",
      "label[for='__search']"
    ].join(", ")));
  }

  function shouldLoadSourceJump() {
    return LOCAL_HOSTS.has(window.location.hostname) && typeof window.livereload === "function";
  }

  function loadMermaidTools() {
    if (mermaidToolsPromise) return mermaidToolsPromise;

    mermaidToolsPromise = loadScriptOnce(ASSETS.mermaidConfig)
      .then(() => loadScriptOnce(ASSETS.mermaidLegacy))
      .then(() => loadScriptOnce(ASSETS.mermaidRender))
      .then(() => loadScriptOnce(ASSETS.mermaidZoom));

    return mermaidToolsPromise;
  }

  function scanPage() {
    scanQueued = false;

    if (hasTocOrDangerUi()) loadScriptOnce(ASSETS.tocFold);
    if (hasArticleRoot()) loadScriptOnce(ASSETS.folderPath);
    if (document.querySelector("[data-peicd-scroll-bottom]")) loadScriptOnce(ASSETS.scrollBottom);
    if (hasMath()) loadScriptOnce(ASSETS.mathjaxRefresh);
    if (hasMermaid()) loadMermaidTools();
    if (hasArticleImages()) loadScriptOnce(ASSETS.imageZoom);
    if (hasLegacyImageWidth()) loadScriptOnce(ASSETS.legacyImageWidth);
    if (hasMarkdownEmbed()) loadScriptOnce(ASSETS.markdownEmbed);
    if (shouldLoadSourceJump()) loadScriptOnce(ASSETS.sourceJump);
  }

  function scheduleScan() {
    if (scanQueued) return;
    scanQueued = true;
    window.requestAnimationFrame(scanPage);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleScan, { once: true });
  } else {
    scheduleScan();
  }

  window.addEventListener("load", scheduleScan, { once: true });
  if (window.document$?.subscribe) {
    window.document$.subscribe(scheduleScan);
  }
})();
