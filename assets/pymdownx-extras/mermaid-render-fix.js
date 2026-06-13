(function () {
  "use strict";

  const HOST_CLASS = "peicd-mermaid-host";
  const PRE_SELECTOR = "pre.diagram";
  const UPDATE_EVENT = "peicd:mermaid-updated";
  const MERMAID_SCRIPT_ID = "peicd-mermaid-runtime";
  const MERMAID_SRC = "https://unpkg.com/mermaid@10.6.1/dist/mermaid.min.js";
  const INTERSECTION_MARGIN = "900px 0px";
  const HTML_LABEL_DESCENDER_PAD = 5;

  let renderToken = 0;
  let renderSequence = 0;
  let observerBound = false;
  let mermaidPromise = null;
  let intersectionObserver = null;
  let renderQueue = [];
  let queueRunning = false;

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

  function extractDiagramText(pre) {
    const code = pre.querySelector("code");
    return (code?.textContent || pre.textContent || "").trim();
  }

  function makeStatus(text) {
    const status = document.createElement("div");
    status.className = "peicd-mermaid-status";
    status.textContent = text;
    return status;
  }

  function ensureHost(pre) {
    const existing = pre.previousElementSibling;
    const source = extractDiagramText(pre);
    if (!source) return null;

    if (existing?.classList.contains(HOST_CLASS)) {
      existing.dataset.peicdMermaidSource = source;
      existing.dataset.peicdMermaidPreId = pre.dataset.peicdMermaidPreId || "";
      if (existing.dataset.peicdMermaidState !== "rendered") {
        delete existing.dataset.peicdMermaidQueued;
      }
      return existing;
    }

    const host = document.createElement("div");
    host.className = "diagram " + HOST_CLASS + " is-pending";
    host.dataset.peicdMermaidState = "pending";
    host.dataset.peicdMermaidSource = source;
    host.setAttribute("role", "status");
    host.setAttribute("aria-label", "Mermaid 圖表待載入");
    host.appendChild(makeStatus("圖表載入中..."));

    pre.hidden = true;
    pre.dataset.peicdMermaidPreId = "peicd-mermaid-pre-" + Date.now() + "-" + renderSequence++;
    host.dataset.peicdMermaidPreId = pre.dataset.peicdMermaidPreId;
    pre.parentNode.insertBefore(host, pre);
    return host;
  }

  function getSourcePre(host) {
    const preId = host.dataset.peicdMermaidPreId;
    if (!preId) return null;
    const escaped = window.CSS?.escape ? CSS.escape(preId) : preId.replace(/"/g, "\\\"");
    return document.querySelector(PRE_SELECTOR + "[data-peicd-mermaid-pre-id=\"" + escaped + "\"]");
  }

  function expandHtmlLabelClipBoxes(svg) {
    svg.querySelectorAll("g.label > foreignObject").forEach((labelBox) => {
      labelBox.style.overflow = "visible";
      if (labelBox.getAttribute("data-peicd-descender-pad") === "true") return;

      const height = Number.parseFloat(labelBox.getAttribute("height"));
      if (!Number.isFinite(height) || height <= 0) return;

      labelBox.setAttribute("height", String(height + HTML_LABEL_DESCENDER_PAD));
      labelBox.setAttribute("data-peicd-descender-pad", "true");
    });
  }

  function decorateHost(host) {
    host.classList.remove("is-pending", "is-rendering", "is-error");
    host.classList.add("peicd-zoomable-mermaid", "is-rendered");
    host.dataset.peicdMermaidState = "rendered";
    host.setAttribute("role", "button");
    host.setAttribute("tabindex", "0");
    host.setAttribute("aria-label", "點擊放大 Mermaid 圖表");

    const svg = host.querySelector("svg");
    if (!svg) return;

    svg.classList.add("peicd-mermaid-svg");
    svg.setAttribute("focusable", "false");
    svg.setAttribute("aria-hidden", "true");
    expandHtmlLabelClipBoxes(svg);
    if (!svg.getAttribute("preserveAspectRatio")) {
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    }
  }

  function notifyMermaidUpdated() {
    window.dispatchEvent(new CustomEvent(UPDATE_EVENT));
  }

  function applyMermaidPatch() {
    if (typeof window.peicdPatchMermaidRender === "function") {
      window.peicdPatchMermaidRender();
    }
  }

  function loadMermaid() {
    if (window.mermaid) {
      applyMermaidPatch();
      return Promise.resolve(window.mermaid);
    }

    if (mermaidPromise) return mermaidPromise;

    mermaidPromise = new Promise((resolve, reject) => {
      const existing = document.getElementById(MERMAID_SCRIPT_ID);
      if (existing) {
        existing.addEventListener("load", () => {
          applyMermaidPatch();
          resolve(window.mermaid);
        }, { once: true });
        existing.addEventListener("error", reject, { once: true });
        return;
      }

      const script = document.createElement("script");
      script.id = MERMAID_SCRIPT_ID;
      script.src = MERMAID_SRC;
      script.async = true;
      script.crossOrigin = "anonymous";
      script.addEventListener("load", () => {
        applyMermaidPatch();
        resolve(window.mermaid);
      }, { once: true });
      script.addEventListener("error", reject, { once: true });
      document.head.appendChild(script);
    });

    return mermaidPromise;
  }

  function markRenderError(host, error) {
    console.error("Mermaid render failed", error);
    host.classList.remove("is-pending", "is-rendering");
    host.classList.add("is-error");
    host.dataset.peicdMermaidState = "error";
    host.removeAttribute("tabindex");
    host.setAttribute("role", "status");
    host.setAttribute("aria-label", "Mermaid 圖表載入失敗");
    host.replaceChildren(makeStatus("圖表載入失敗"));

    const pre = getSourcePre(host);
    if (pre) pre.hidden = false;
  }

  async function renderHost(host, token, rerender) {
    if (!host.isConnected || token !== renderToken) return;
    if (!rerender && host.dataset.peicdMermaidState === "rendered") return;
    delete host.dataset.peicdMermaidQueued;

    const source = host.dataset.peicdMermaidSource;
    if (!source) return;

    host.classList.remove("is-error");
    host.classList.add("is-rendering");
    host.dataset.peicdMermaidState = "rendering";

    try {
      const mermaid = await loadMermaid();
      if (!mermaid || !host.isConnected || token !== renderToken) return;

      mermaid.initialize(getMermaidConfig());
      const result = await mermaid.render("peicd_mermaid_" + token + "_" + renderSequence++, source);
      if (!host.isConnected || token !== renderToken) return;

      host.innerHTML = result.svg;
      decorateHost(host);
      result.bindFunctions?.(host);

      const pre = getSourcePre(host);
      if (pre?.isConnected) pre.remove();
      notifyMermaidUpdated();
    } catch (error) {
      if (host.isConnected && token === renderToken) markRenderError(host, error);
    }
  }

  function runQueue(token) {
    if (queueRunning) return;
    queueRunning = true;

    (async () => {
      while (renderQueue.length && token === renderToken) {
        const item = renderQueue.shift();
        await renderHost(item.host, token, item.rerender);
      }
    })().finally(() => {
      queueRunning = false;
      if (renderQueue.length && token === renderToken) runQueue(token);
    });
  }

  function enqueueHost(host, token, rerender) {
    if (!host?.isConnected || token !== renderToken) return;
    if (!rerender && (host.dataset.peicdMermaidQueued === "true" || host.dataset.peicdMermaidState === "rendered")) return;

    host.dataset.peicdMermaidQueued = "true";
    renderQueue.push({ host, rerender: Boolean(rerender) });
    runQueue(token);
  }

  function observeHost(host, token) {
    if (!host || host.dataset.peicdMermaidState === "rendered") return;

    if (!("IntersectionObserver" in window)) {
      enqueueHost(host, token, false);
      return;
    }

    intersectionObserver.observe(host);
  }

  function resetIntersectionObserver(token) {
    if (intersectionObserver) intersectionObserver.disconnect();

    if (!("IntersectionObserver" in window)) {
      intersectionObserver = null;
      return;
    }

    intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const host = entry.target;
        intersectionObserver.unobserve(host);
        enqueueHost(host, token, false);
      });
    }, { rootMargin: INTERSECTION_MARGIN });
  }

  function scanPage() {
    renderToken += 1;
    const token = renderToken;
    renderQueue = [];
    queueRunning = false;
    resetIntersectionObserver(token);

    const pres = Array.from(document.querySelectorAll(PRE_SELECTOR));
    pres.forEach((pre) => {
      const host = ensureHost(pre);
      observeHost(host, token);
    });
  }

  function rerenderRenderedHosts() {
    const token = renderToken;
    const hosts = Array.from(document.querySelectorAll("." + HOST_CLASS + ".is-rendered"));
    if (!hosts.length) return;

    hosts.forEach((host) => {
      host.dataset.peicdMermaidQueued = "";
      enqueueHost(host, token, true);
    });
  }

  function bindSchemeObserver() {
    if (observerBound) return;
    observerBound = true;

    const target = document.body;
    if (!target) return;

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "attributes" && mutation.attributeName === "data-md-color-scheme") {
          rerenderRenderedHosts();
          break;
        }
      }
    });

    observer.observe(target, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
  }

  function initMermaidRenderFix() {
    bindSchemeObserver();
    scanPage();
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
