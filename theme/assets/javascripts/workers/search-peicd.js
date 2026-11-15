/* Material 9.7.x SETUP=0 / READY=1 / QUERY=2 / RESULT=3, FIFO replies retained.
 * Only the filtered public index is used. No original Markdown or external service.
 */
(function () {
  "use strict";
  const url = new URL(self.location.href);
  const version = url.searchParams.get("v") || "20261115-ux-1";
  importScripts("../../pymdownx-extras/search-core.js?v=" + encodeURIComponent(version));
  let engine, setup, materialWorker, materialReady;
  let serial = Promise.resolve();

  function requestMaterial(message) {
    const worker = materialWorker;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => finish(new Error("Material search worker timed out")), 6000);
      function finish(error, reply) {
        clearTimeout(timer);
        worker.removeEventListener("message", onMessage);
        worker.removeEventListener("error", onError);
        worker.removeEventListener("messageerror", onError);
        if (error) reject(error); else resolve(reply);
      }
      function onMessage(event) { finish(null, event.data); }
      function onError() { finish(new Error("Material search worker failed")); }
      worker.addEventListener("message", onMessage);
      worker.addEventListener("error", onError);
      worker.addEventListener("messageerror", onError);
      try { worker.postMessage(message); } catch (error) { finish(error); }
    });
  }

  async function queryMaterial(query) {
    try {
      if (!materialWorker) {
        const upstream = new URL(url.searchParams.get("material"), url);
        if (upstream.origin !== url.origin || new URL(".", upstream).href !== new URL(".", url).href ||
            !/\/search\.[\w.-]+\.js$/.test(upstream.pathname)) throw new Error("Invalid Material search worker URL");
        materialWorker = new Worker(upstream.href);
        materialReady = requestMaterial({ type: 0, data: setup }).then(reply => {
          if (reply.type !== 1) throw new Error("Invalid Material search setup response");
        });
      }
      await materialReady;
      const reply = await requestMaterial({ type: 2, data: query });
      if (reply.type !== 3) throw new Error("Invalid Material search query response");
      return reply.data;
    } catch (error) {
      materialWorker?.terminate();
      materialWorker = materialReady = null; // A manual retry can create a fresh fallback.
      throw error;
    }
  }

  function completeEnglishMatches(result) {
    return { ...result, items: (result.items || []).map(group => {
      const matches = group.filter(item => item.score > 0 && Object.keys(item.terms).length && Object.values(item.terms).every(Boolean));
      if (!matches.length) return [];
      const parent = group.find(item => !item.location.includes("#"));
      if (parent && !matches.some(item => item.location === parent.location)) matches.push({ ...parent, score: 0, terms: {} });
      return matches;
    }).filter(group => group.length) };
  }

  function wildcardHighlight(item, query) {
    const prefixes = [...query.matchAll(/(?:^|\s)(?:\w+:)?([\p{L}\p{N}_]+)\*(?=\s|$)/gu)].map(match => match[1]);
    if (!prefixes.length) return item;
    const format = html => String(html || "").replace(/(<mark\b[^>]*>)([^<]*)(<\/mark>)/gi, (all, open, body, close) => {
      const prefix = prefixes.find(value => body.toLowerCase().startsWith(value.toLowerCase()));
      return prefix ? open + body.slice(0, prefix.length) + close + body.slice(prefix.length) : all;
    });
    return { ...item, title: format(item.title), text: format(item.text) };
  }

  function capFallback(result, query, options) {
    const size = 10, offset = Math.max(0, Math.floor(Number(options.offset) || 0));
    const groups = (result.items || []).filter(group => {
      const page = group.find(item => !item.location.includes("#"))?.location || group[0]?.location.split("#")[0];
      const scope = engine.pages.get(page)?.scope || "";
      return (!options.page || options.page === page) && (!options.scope || scope.startsWith(options.scope));
    });
    const selected = options.page ? groups : groups.slice(offset, offset + size);
    const details = [];
    const items = selected.map(group => {
      const parent = group.find(item => !item.location.includes("#"));
      const children = group.filter(item => item.location.includes("#"));
      const page = parent?.location || group[0].location.split("#")[0];
      const shown = options.page ? children.slice(offset, offset + size) : children.slice(0, 3);
      details.push({ page, sections: children.length, shown: shown.length });
      return (parent ? [...shown, parent] : shown).map(item => wildcardHighlight(item, query));
    });
    const total = options.page ? (details[0]?.sections || 0) : groups.length;
    return { ...result, items, peicd: { query, scope: options.scope || "", page: options.page || "",
      totalPages: groups.length, totalSections: groups.reduce((n, g) => n + g.length, 0), total,
      offset, pageSize: size, more: offset + size < total, groups: details, facets: engine.facets } };
  }

  async function handle(message) {
    if (message.type === 0) {
      materialWorker?.terminate(); materialWorker = materialReady = null;
      setup = message.data;
      engine = new self.PeicdSearch.LiteralSearch(setup.docs);
      self.postMessage({ type: 1, data: { facets: engine.facets } });
    } else if (message.type === 2) {
      const options = typeof message.data === "object" && message.data ? message.data : {};
      const query = String(options.query ?? message.data ?? ""), parsed = self.PeicdSearch.parseQuery(query);
      let data = { items: [], peicd: { query, facets: engine?.facets || [] } };
      if (parsed.terms.length && engine) {
        if (parsed.advanced) data = capFallback(await queryMaterial(query), query, options);
        else {
          data = engine.search(query, options);
          if (!data.peicd.totalPages && !parsed.chinese && !parsed.quoted) {
            data = capFallback(completeEnglishMatches(await queryMaterial(query)), query, options);
          }
          if (setup.options?.suggest) data.suggest = (await queryMaterial(query)).suggest || [];
        }
      }
      data.peicd = { ...data.peicd, requestId: options.requestId };
      self.postMessage({ type: 3, data });
    }
  }
  self.addEventListener("message", event => {
    serial = serial.then(() => handle(event.data)).catch(error => {
      console.error("PEICD search:", error);
      const request = event.data.data;
      const peicd = { error: "搜尋暫時無法使用，請重試。", query: String(request?.query ?? request ?? ""), requestId: request?.requestId };
      self.postMessage(event.data.type === 0 ? { type: 1, data: peicd } : { type: 3, data: { items: [], peicd } });
    });
  });
})();
