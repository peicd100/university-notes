(function () {
  "use strict";

  if (window.__PEICD_SEARCH_LAZY_GUARD__) return;

  const NativeXHR = window.XMLHttpRequest;
  const NativeWorker = window.Worker;
  const SEARCH_VERSION = "20261009-search-1";
  const pendingSearchRequests = [];
  const pendingWorkers = [];
  let activated = false;

  function isSearchIndexUrl(url) {
    return /(?:^|\/)search\/search_index\.(?:json|js)(?:[?#].*)?$/.test(String(url || ""));
  }

  function isSearchWorkerUrl(url) {
    return /(?:^|\/)assets\/javascripts\/workers\/search\.[^/]+\.js(?:[?#].*)?$/.test(String(url || ""));
  }

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
    activated = true;

    while (pendingWorkers.length) {
      pendingWorkers.shift().activate();
    }

    while (pendingSearchRequests.length) {
      const request = pendingSearchRequests.shift();
      request.send.apply(request.xhr, request.args);
    }
  }

  function bindActivationEvents() {
    const composing = new WeakSet();
    const isQuery = target => target instanceof Element &&
      target.matches("[data-md-component='search-query']");
    const notifyInput = target => {
      activateSearch();
      // Material 9.7.x observes keyup rather than input. Bridge paste/mobile/IME
      // commits into that existing pipeline; its distinct-value filter dedupes
      // the following real keyup, without maintaining a second search UI owner.
      target.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
    };
    document.addEventListener("compositionstart", event => {
      if (isQuery(event.target)) composing.add(event.target);
    }, true);
    document.addEventListener("compositionend", event => {
      if (!isQuery(event.target)) return;
      composing.delete(event.target);
      notifyInput(event.target);
    }, true);
    document.addEventListener("input", event => {
      if (isQuery(event.target) && !event.isComposing && !composing.has(event.target)) {
        notifyInput(event.target);
      }
    }, true);
    for (const type of ["keydown", "keyup"]) {
      document.addEventListener(type, event => {
        if (isQuery(event.target) && (event.isComposing || composing.has(event.target))) {
          // Do not let Enter/arrow keys select search results while the IME is
          // selecting characters. Keep the browser's default IME action intact.
          event.stopImmediatePropagation();
        }
      }, true);
    }

    document.addEventListener("click", (event) => {
      const target = event.target;
      if (target instanceof Element && target.closest("label[for='__search'], .md-search")) {
        activateSearch();
      }
    }, true);

    document.addEventListener("focusin", (event) => {
      const target = event.target;
      if (target instanceof Element && target.closest("[data-md-component='search-query'], .md-search")) {
        activateSearch();
      }
    }, true);

    window.addEventListener("keydown", (event) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === "/" || event.key === "f" || event.key === "s") {
        activateSearch();
      }
    }, true);

    if (location.search.includes("q=") || location.search.includes("h=")) {
      activateSearch();
    }
  }

  if (NativeXHR) {
    const nativeOpen = NativeXHR.prototype.open;
    const nativeSend = NativeXHR.prototype.send;

    NativeXHR.prototype.open = function (method, url) {
      this.__peicdSearchLazyUrl = isSearchIndexUrl(url) ? String(url) : "";
      return nativeOpen.apply(this, arguments);
    };

    NativeXHR.prototype.send = function () {
      if (!activated && this.__peicdSearchLazyUrl) {
        pendingSearchRequests.push({
          xhr: this,
          send: nativeSend,
          args: Array.from(arguments)
        });
        return undefined;
      }

      return nativeSend.apply(this, arguments);
    };
  }

  if (NativeWorker) {
    window.Worker = function PeicdLazyWorker(url, options) {
      const isSearch = isSearchWorkerUrl(url);
      const workerUrl = isSearch ? enhancedSearchWorkerUrl(url) : url;
      if (activated || !isSearch) {
        return new NativeWorker(workerUrl, options);
      }

      const listeners = new Map();
      const queue = [];
      let terminated = false;
      const proxy = {
        onmessage: null,
        onerror: null,
        realWorker: null,
        addEventListener(type, listener, optionsArg) {
          if (!listeners.has(type)) listeners.set(type, []);
          listeners.get(type).push({ listener, options: optionsArg });
          if (this.realWorker) this.realWorker.addEventListener(type, listener, optionsArg);
        },
        removeEventListener(type, listener, optionsArg) {
          const entries = listeners.get(type) || [];
          listeners.set(type, entries.filter((entry) => entry.listener !== listener));
          if (this.realWorker) this.realWorker.removeEventListener(type, listener, optionsArg);
        },
        dispatchEvent(event) {
          const handler = this["on" + event.type];
          if (typeof handler === "function") handler.call(this, event);
          (listeners.get(event.type) || []).forEach((entry) => entry.listener.call(this, event));
          return true;
        },
        postMessage(message, transfer) {
          if (terminated) return;
          if (this.realWorker) {
            this.realWorker.postMessage(message, transfer || []);
          } else {
            queue.push([message, transfer]);
          }
        },
        terminate() {
          terminated = true;
          if (this.realWorker) this.realWorker.terminate();
          queue.length = 0;
        },
        activate() {
          if (terminated || this.realWorker) return;
          const worker = new NativeWorker(workerUrl, options);
          this.realWorker = worker;
          worker.onmessage = (event) => {
            if (typeof this.onmessage === "function") this.onmessage(event);
          };
          worker.onerror = (event) => {
            if (typeof this.onerror === "function") this.onerror(event);
          };
          listeners.forEach((entries, type) => {
            entries.forEach((entry) => worker.addEventListener(type, entry.listener, entry.options));
          });
          while (queue.length) {
            const [message, transfer] = queue.shift();
            worker.postMessage(message, transfer || []);
          }
        }
      };

      pendingWorkers.push(proxy);
      return proxy;
    };
    window.Worker.prototype = NativeWorker.prototype;
  }

  bindActivationEvents();
  window.__PEICD_SEARCH_LAZY_GUARD__ = { activate: activateSearch };
})();
