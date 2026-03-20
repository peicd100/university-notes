(function () {
  "use strict";

  const HOST_CLASS = "peicd-mermaid-host";
  const PRE_SELECTOR = "pre.diagram";
  let renderToken = 0;
  let observerBound = false;

  function getCurrentScheme() {
    return document.querySelector("[data-md-color-scheme]")?.getAttribute("data-md-color-scheme") || "default";
  }

  function getMermaidConfig() {
    const scheme = getCurrentScheme();
    const root = window.mermaidConfig || {};
    return root[scheme] || root.default || {
      startOnLoad: false,
      theme: "default",
      flowchart: { htmlLabels: true, useMaxWidth: false }
    };
  }

  function ensureHost(pre) {
    const existing = pre.previousElementSibling;
    if (existing?.classList.contains(HOST_CLASS)) return existing;

    const host = document.createElement("div");
    host.className = "diagram " + HOST_CLASS;
    pre.parentNode.insertBefore(host, pre);
    return host;
  }

  function extractDiagramText(pre) {
    const code = pre.querySelector("code");
    return (code?.textContent || pre.textContent || "").trim();
  }

  async function renderPre(pre, index, token) {
    const source = extractDiagramText(pre);
    if (!source) return;

    const host = ensureHost(pre);
    host.dataset.peicdMermaidSource = source;
    const id = "peicd_mermaid_" + index + "_" + Date.now();

    try {
      const result = await window.mermaid.render(id, source);
      if (token !== renderToken) return;

      host.innerHTML = result.svg;
      result.bindFunctions?.(host);
      if (pre.isConnected) pre.remove();
    } catch (error) {
      console.error("Mermaid render failed", error);
      host.remove();
    }
  }

  async function renderAll(force) {
    if (typeof window.mermaid === "undefined") return;

    renderToken += 1;
    const token = renderToken;
    const pres = Array.from(document.querySelectorAll(PRE_SELECTOR));
    const hosts = Array.from(document.querySelectorAll("." + HOST_CLASS));
    if (!pres.length && !hosts.length) return;

    window.mermaid.initialize(getMermaidConfig());

    if (force) {
      for (let index = 0; index < hosts.length; index += 1) {
        const host = hosts[index];
        const source = host.dataset.peicdMermaidSource;
        if (!source) continue;
        try {
          const result = await window.mermaid.render("peicd_mermaid_rerender_" + index + "_" + Date.now(), source);
          if (token !== renderToken) return;
          host.innerHTML = result.svg;
          result.bindFunctions?.(host);
        } catch (error) {
          console.error("Mermaid rerender failed", error);
        }
      }

      if (!pres.length) return;
    }

    for (let index = 0; index < pres.length; index += 1) {
      await renderPre(pres[index], index, token);
    }
  }

  function bindSchemeObserver() {
    if (observerBound) return;
    observerBound = true;

    const target = document.body;
    if (!target) return;

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "attributes" && mutation.attributeName === "data-md-color-scheme") {
          renderAll(true);
          break;
        }
      }
    });

    observer.observe(target, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
  }

  function initMermaidRenderFix() {
    bindSchemeObserver();
    renderAll(false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMermaidRenderFix, { once: true });
  } else {
    initMermaidRenderFix();
  }

  if (window.document$?.subscribe) {
    window.document$.subscribe(initMermaidRenderFix);
  }
})();
