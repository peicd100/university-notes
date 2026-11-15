(function () {
  "use strict";
  if (window.__PEICD_SEARCH_LAZY_GUARD__) return;
  const NativeXHR = window.XMLHttpRequest, NativeWorker = window.Worker;
  const SEARCH_VERSION = "20261115-ux-1";
  const pendingSearchRequests = [], pendingWorkers = [], searchWorkers = new Set();
  let activated = false, query = "", sequence = 0;
  let view = { scope: "", page: "", offset: 0 };
  const state = { phase: "idle", ready: false, info: null, error: "", facets: [] };
  const later = fn => Promise.resolve().then(fn);
  function emit() {
    if (typeof CustomEvent === "function" && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent("peicd:search-state", { detail: { ...state } }));
    }
  }
  function fail() { state.phase = "error"; state.error = "搜尋載入失敗，請重試。"; emit(); }
  function isSearchIndexUrl(url) { return /(?:^|\/)search\/search_index\.(?:json|js)(?:[?#].*)?$/.test(String(url || "")); }
  function isSearchWorkerUrl(url) { return /(?:^|\/)assets\/javascripts\/workers\/search\.[^/]+\.js(?:[?#].*)?$/.test(String(url || "")); }
  function enhancedSearchWorkerUrl(url) {
    const material = new URL(url, document.baseURI);
    if (material.origin !== location.origin) return url;
    const enhanced = new URL("search-peicd.js", material);
    enhanced.searchParams.set("v", SEARCH_VERSION);
    enhanced.searchParams.set("material", material.href);
    return enhanced.href;
  }
  function activateSearch() {
    if (activated) return;
    activated = true; state.phase = "loading"; emit();
    while (pendingWorkers.length) pendingWorkers.shift().activate();
    while (pendingSearchRequests.length) {
      const request = pendingSearchRequests.shift();
      request.send.apply(request.xhr, request.args);
    }
  }
  function configure(patch = {}) {
    view = { ...view, ...patch };
    const worker = [...searchWorkers].find(w => !w.terminated);
    if (worker && state.ready) worker.postMessage({ type: 2, data: { ...view, query } });
  }
  function retry() {
    state.error = "";
    const worker = [...searchWorkers].find(w => !w.terminated);
    if (state.ready) configure();
    else if (worker?.lastSetup) worker.restart();
    else {
      // Index download failed before SETUP. Explicit user action reloads with q.
      const url = new URL(location.href);
      const input = document.querySelector?.('[data-md-component="search-query"]');
      if (input?.value) url.searchParams.set("q", input.value);
      location.assign(url.href);
    }
  }

  function bindActivationEvents() {
    const composing = new WeakSet();
    const isQuery = target => target instanceof Element && target.matches("[data-md-component='search-query']");
    const notifyInput = target => {
      activateSearch();
      // Feed Material's keyup pipeline; no second result renderer or IME owner.
      target.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
    };
    document.addEventListener("compositionstart", event => { if (isQuery(event.target)) composing.add(event.target); }, true);
    document.addEventListener("compositionend", event => {
      if (!isQuery(event.target)) return;
      composing.delete(event.target); notifyInput(event.target);
    }, true);
    document.addEventListener("input", event => {
      if (isQuery(event.target) && !event.isComposing && !composing.has(event.target)) notifyInput(event.target);
    }, true);
    for (const type of ["keydown", "keyup"]) {
      document.addEventListener(type, event => {
        if (!isQuery(event.target)) return;
        if (event.isComposing || composing.has(event.target)) event.stopImmediatePropagation();
        else if (type === "keydown" && event.key === "Enter" && ["loading", "querying"].includes(state.phase)) {
          event.preventDefault(); event.stopImmediatePropagation();
        }
      }, true);
    }
    document.addEventListener("click", event => {
      if (event.target instanceof Element && event.target.closest("label[for='__search'], .md-search")) activateSearch();
    }, true);
    document.addEventListener("focusin", event => {
      if (event.target instanceof Element && event.target.closest("[data-md-component='search-query'], .md-search")) activateSearch();
    }, true);
    window.addEventListener("keydown", event => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey ||
          event.target?.closest?.("input, textarea, select, [contenteditable]")) return;
      if (["/", "f", "s"].includes(event.key)) activateSearch();
    }, true);
    if (location.search.includes("q=") || location.search.includes("h=")) activateSearch();
  }

  if (NativeXHR) {
    const nativeOpen = NativeXHR.prototype.open, nativeSend = NativeXHR.prototype.send;
    NativeXHR.prototype.open = function (method, url) {
      this.__peicdSearchLazyUrl = isSearchIndexUrl(url) ? String(url) : "";
      return nativeOpen.apply(this, arguments);
    };
    NativeXHR.prototype.send = function () {
      if (this.__peicdSearchLazyUrl && !this.__peicdSearchObserved) {
        this.__peicdSearchObserved = true;
        this.addEventListener?.("error", fail);
        this.addEventListener?.("timeout", fail);
        this.addEventListener?.("load", () => { if (this.status >= 400) fail(); });
      }
      if (!activated && this.__peicdSearchLazyUrl) {
        pendingSearchRequests.push({ xhr: this, send: nativeSend, args: Array.from(arguments) });
        return;
      }
      return nativeSend.apply(this, arguments);
    };
  }
  if (NativeWorker) {
    window.Worker = function PeicdLazyWorker(url, options) {
      if (!isSearchWorkerUrl(url)) return new NativeWorker(url, options);
      const workerUrl = enhancedSearchWorkerUrl(url), listeners = new Map(), queue = [];
      let restarting = false;
      const proxy = {
        onmessage: null, onerror: null, realWorker: null, lastSetup: null, terminated: false,
        addEventListener(type, listener, optionsArg) {
          if (!listeners.has(type)) listeners.set(type, []);
          listeners.get(type).push({ listener, options: optionsArg });
        },
        removeEventListener(type, listener) {
          listeners.set(type, (listeners.get(type) || []).filter(entry => entry.listener !== listener));
        },
        dispatchEvent(event) {
          const handler = this["on" + event.type];
          if (typeof handler === "function") handler.call(this, event);
          for (const entry of [...(listeners.get(event.type) || [])]) {
            if (typeof entry.listener === "function") entry.listener.call(this, event);
            else entry.listener.handleEvent(event);
            if (entry.options?.once) this.removeEventListener(event.type, entry.listener);
          }
          return true;
        },
        postMessage(message, transfer) {
          if (this.terminated) return;
          if (message.type === 0) this.lastSetup = message;
          if (message.type === 2) {
            const data = typeof message.data === "object" && message.data ? message.data : null;
            const next = String(data ? data.query : message.data || "");
            if (next !== query) { view = { ...view, page: "", offset: 0 }; query = next; }
            const requestId = ++sequence;
            message = { ...message, data: { ...view, ...data, query: next, requestId } };
            state.phase = "querying"; state.error = ""; emit();
          }
          if (this.realWorker) this.realWorker.postMessage(message, transfer || []);
          else queue.push([message, transfer]);
        },
        terminate() {
          this.terminated = true; this.realWorker?.terminate(); queue.length = 0; searchWorkers.delete(this);
        },
        restart() {
          this.realWorker?.terminate(); this.realWorker = null; restarting = true;
          state.ready = false; state.phase = "loading"; emit();
          queue.length = 0; queue.push([this.lastSetup]); this.activate();
        },
        activate() {
          if (this.terminated || this.realWorker) return;
          const worker = new NativeWorker(workerUrl, options);
          this.realWorker = worker;
          worker.onmessage = event => {
            const message = event.data, info = message.data?.peicd;
            if (message.type === 1) {
              state.ready = !message.data?.error;
              state.facets = message.data?.facets || state.facets;
              state.phase = state.ready ? "ready" : "error";
              state.error = message.data?.error || "";
            }
            if (message.type === 3 && info && info.requestId === sequence && info.query === query) {
              state.info = info; state.facets = info.facets || state.facets;
              state.phase = info.error ? "error" : "results"; state.error = info.error || "";
            }
            // Every FIFO reply still reaches Material. Controls/status update after its render.
            this.dispatchEvent(event);
            later(emit);
            if (message.type === 1 && restarting) { restarting = false; configure(); }
          };
          worker.onerror = event => { state.ready = false; fail(); this.dispatchEvent(event); };
          worker.onmessageerror = event => { state.ready = false; fail(); this.dispatchEvent(event); };
          while (queue.length) { const [message, transfer] = queue.shift(); worker.postMessage(message, transfer || []); }
        }
      };
      searchWorkers.add(proxy); pendingWorkers.push(proxy);
      if (activated) proxy.activate();
      return proxy;
    };
    window.Worker.prototype = NativeWorker.prototype;
  }
  window.__PEICD_SEARCH_LAZY_GUARD__ = { activate: activateSearch, configure, retry,
    snapshot: () => ({ ...state, view: { ...view }, activated }) };
  bindActivationEvents();
})();
