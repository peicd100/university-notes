/* Material 9.7.x worker protocol: SETUP=0, READY=1, QUERY=2, RESULT=3.
 * Plain queries use literal full-text/AND search. Explicit Lunr syntax, and
 * English linguistic fallback, use the unmodified Material worker on demand.
 */
(function () {
  "use strict";
  const url = new URL(self.location.href);
  const version = url.searchParams.get("v") || "20261009-search-1";
  importScripts("../../pymdownx-extras/search-core.js?v=" + encodeURIComponent(version));

  let engine, setup, materialWorker, materialReady;
  let serial = Promise.resolve();

  function requestMaterial(message) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => finish(new Error("Material search worker timed out")), 20000);
      function finish(error, reply) {
        clearTimeout(timer);
        materialWorker.removeEventListener("message", onMessage);
        materialWorker.removeEventListener("error", onError);
        materialWorker.removeEventListener("messageerror", onError);
        if (error) reject(error);
        else resolve(reply);
      }
      function onMessage(event) { finish(null, event.data); }
      function onError() { finish(new Error("Material search worker failed")); }
      materialWorker.addEventListener("message", onMessage);
      materialWorker.addEventListener("error", onError);
      materialWorker.addEventListener("messageerror", onError);
      try { materialWorker.postMessage(message); }
      catch (error) { finish(error); }
    });
  }

  async function queryMaterial(query) {
    if (!materialWorker) {
      const upstream = new URL(url.searchParams.get("material"), url);
      // Only the same site's original search worker is a valid fallback.
      if (upstream.origin !== url.origin ||
          new URL(".", upstream).href !== new URL(".", url).href ||
          !/\/search\.[\w.-]+\.js$/.test(upstream.pathname)) {
        throw new Error("Invalid Material search worker URL");
      }
      materialWorker = new Worker(upstream.href);
      materialReady = requestMaterial({ type: 0, data: setup }).then(reply => {
        if (reply.type !== 1) throw new Error("Invalid Material search setup response");
      });
    }
    await materialReady;
    const reply = await requestMaterial({ type: 2, data: query });
    if (reply.type !== 3) throw new Error("Invalid Material search query response");
    return reply.data;
  }

  function completeEnglishMatches(result) {
    // A plain multi-keyword query should not silently degrade to an OR query.
    // Keep only original results that matched every term, plus their parent.
    return {
      ...result,
      items: (result.items || []).map(group => {
        const matches = group.filter(item => item.score > 0 &&
          Object.keys(item.terms).length && Object.values(item.terms).every(Boolean));
        if (!matches.length) return [];
        const parent = group.find(item => !item.location.includes("#"));
        if (parent && !matches.some(item => item.location === parent.location)) {
          matches.push({ ...parent, score: 0, terms: {} });
        }
        return matches;
      }).filter(group => group.length)
    };
  }

  async function handle(message) {
    if (message.type === 0) {
      if (materialWorker) materialWorker.terminate();
      materialWorker = materialReady = null;
      setup = message.data;
      engine = new self.PeicdSearch.LiteralSearch(setup.docs);
      self.postMessage({ type: 1 });
    } else if (message.type === 2) {
      const query = String(message.data || ""), parsed = self.PeicdSearch.parseQuery(query);
      let data = { items: [] };
      if (parsed.terms.length && engine) {
        if (parsed.advanced) {
          data = await queryMaterial(query);
        } else {
          data = engine.search(query);
          if (!data.items.length && !parsed.chinese && !parsed.quoted) {
            data = completeEnglishMatches(await queryMaterial(query));
          }
          if (setup.options && setup.options.suggest) {
            data.suggest = (await queryMaterial(query)).suggest || [];
          }
        }
      }
      self.postMessage({ type: 3, data });
    }
  }

  // Material associates replies with queries in order. Do not drop or reorder
  // replies when an on-demand Lunr initialization overlaps rapid input.
  self.addEventListener("message", event => {
    serial = serial.then(() => handle(event.data)).catch(error => {
      console.error("PEICD search:", error);
      self.postMessage(event.data.type === 0 ? { type: 1 } : { type: 3, data: { items: [] } });
    });
  });
})();
