/* Literal full-text search over Material's already-public section index.
 * No tokenizer, stop words, network calls, or raw Markdown access.
 */
(function (root) {
  "use strict";

  const entities = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
  const invisible = /[\u200b\ufeff]/g;

  function plainText(html) {
    return String(html || "")
      .replace(/<(script|style|object)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, " ")
      .replace(/<\/?(?:p|pre|li|ol|ul|br|div|table|tr)\b[^>]*>/gi, " ")
      .replace(/<[^>]*>/g, "")
      .replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi, (entity, name) => {
        if (name[0] !== "#") return entities[name.toLowerCase()] || entity;
        const hex = name[1].toLowerCase() === "x";
        const code = parseInt(name.slice(hex ? 2 : 1), hex ? 16 : 10);
        return code > 0 && code <= 0x10ffff && !(code >= 0xd800 && code <= 0xdfff)
          ? String.fromCodePoint(code) : "\ufffd";
      });
  }

  function clean(value) {
    return String(value || "").replace(invisible, "").normalize("NFKC").replace(/\s+/gu, " ").trim();
  }

  function field(value, html = false) {
    const text = clean(html ? plainText(value) : value);
    return { text, folded: text.toLowerCase() };
  }

  function escapeHTML(text) {
    return text.replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  function parseQuery(query) {
    const value = clean(query);
    const outsideQuotes = value.replace(/"[^"]*"/g, "");
    // Explicit Lunr syntax is handled by the original worker, not approximated.
    const advanced = /(?:^|\s)[+-]\S|\b(?:title|text|tags):|\S\*|\*\S|\S~\d|\S\^\d/.test(outsideQuotes);
    const tokens = [...value.matchAll(/"([^"]+)"|(\S+)/g)].map(match => clean(match[1] || match[2]));
    return {
      terms: [...new Set(tokens.map(token => token.toLowerCase()))],
      phrase: tokens.join(" ").toLowerCase(),
      advanced,
      quoted: value.includes('"'),
      chinese: /\p{Script=Han}/u.test(value)
    };
  }

  // Lowercasing normally preserves UTF-16 offsets (including emoji). Map the
  // rare expansions, e.g. İ -> i + combining dot, before marking display text.
  function displayOffsets(source) {
    if (source.text.length === source.folded.length) return null;
    const offsets = [];
    let index = 0;
    for (const char of source.text) {
      const folded = char.toLowerCase();
      for (let i = 0; i < folded.length; i++) offsets.push([index, index + char.length]);
      index += char.length;
    }
    return offsets;
  }

  function highlight(source, terms, start = 0, end = source.folded.length) {
    const offsets = displayOffsets(source);
    const from = index => offsets && index < offsets.length ? offsets[index][0] : index;
    const to = index => offsets && index > 0 ? offsets[index - 1][1] : index;
    const ranges = [];
    for (const term of terms) {
      let at = source.folded.indexOf(term, start);
      while (at >= start && at < end) {
        ranges.push([from(at), to(Math.min(at + term.length, end))]);
        at = source.folded.indexOf(term, at + Math.max(1, term.length));
      }
    }
    ranges.sort((a, b) => a[0] - b[0]);
    const merged = [];
    for (const range of ranges) {
      const previous = merged[merged.length - 1];
      if (previous && range[0] <= previous[1]) previous[1] = Math.max(previous[1], range[1]);
      else merged.push(range);
    }
    let position = from(start), result = "";
    for (const [left, right] of merged) {
      result += escapeHTML(source.text.slice(position, left));
      result += "<mark>" + escapeHTML(source.text.slice(left, right)) + "</mark>";
      position = right;
    }
    return result + escapeHTML(source.text.slice(position, to(end)));
  }

  function codePointBoundary(text, index, direction) {
    if (index > 0 && index < text.length &&
        /[\ud800-\udbff]/.test(text[index - 1]) && /[\udc00-\udfff]/.test(text[index])) {
      return index + direction;
    }
    return index;
  }

  function snippet(source, terms) {
    if (!source.text) return "";
    const hits = terms.map(term => [source.folded.indexOf(term), term.length])
      .filter(([at]) => at >= 0).sort((a, b) => a[0] - b[0]);
    const windows = [];
    for (const [at, length] of hits) {
      const left = codePointBoundary(source.folded, Math.max(0, at - 48), -1);
      const right = codePointBoundary(source.folded, Math.min(source.folded.length, at + length + 96), 1);
      const previous = windows[windows.length - 1];
      if (previous && left <= previous[1]) previous[1] = Math.max(previous[1], right);
      else if (windows.length < 3) windows.push([left, right]);
    }
    if (!windows.length) windows.push([0, codePointBoundary(source.folded, Math.min(200, source.folded.length), 1)]);
    return "<p>" + windows.map(([left, right], index) =>
      (left > 0 ? "… " : "") + highlight(source, terms, left, right) +
      (right < source.folded.length && index === windows.length - 1 ? " …" : "")
    ).join(" … ") + "</p>";
  }

  class LiteralSearch {
    constructor(docs) {
      this.pages = new Map();
      this.records = (docs || []).filter(doc => doc && typeof doc.location === "string").map(doc => {
        const record = {
          location: doc.location,
          page: doc.location.split("#")[0],
          title: field(doc.title, true),
          text: field(doc.text, true),
          tags: Array.isArray(doc.tags) ? doc.tags.map(tag => field(tag)) : [],
          boost: Number.isFinite(doc.boost) && doc.boost > 0 ? doc.boost : 1
        };
        if (!doc.location.includes("#")) this.pages.set(record.page, record);
        return record;
      });
      // Always supply a parent article to Material's renderer, even if a page's
      // heading was excluded or the input entries are not ordered by article.
      for (const record of this.records) {
        if (!this.pages.has(record.page)) {
          let title = record.page.split("/").pop().replace(/\.html$/, "");
          try { title = decodeURIComponent(title); } catch (_) { /* retain encoded path */ }
          this.pages.set(record.page, { ...record, location: record.page, title: field(title), text: field("") });
        }
        record.articleTitle = this.pages.get(record.page).title;
      }
    }

    item(record, terms, score) {
      return {
        location: record.location,
        title: highlight(record.title, terms),
        text: score ? snippet(record.text, terms) : "",
        ...(record.tags.length && { tags: record.tags.map(tag => highlight(tag, terms)) }),
        score,
        terms: score ? Object.fromEntries(terms.map(term => [term, true])) : {}
      };
    }

    search(query) {
      const parsed = parseQuery(query), { terms, phrase } = parsed;
      if (!terms.length || parsed.advanced) return { items: [] };
      const matches = [];
      for (const record of this.records) {
        const fields = [[record.title, 8], [record.articleTitle, 4],
          ...record.tags.map(tag => [tag, 6]), [record.text, 1]];
        let score = 100, found = true;
        for (const term of terms) {
          let weight = 0;
          for (const [value, boost] of fields) {
            if (value.folded.includes(term)) weight = Math.max(weight, boost);
          }
          if (!weight) { found = false; break; }
          score += weight * 10;
        }
        if (!found) continue;
        // Contiguous phrases outrank scattered keywords; title > tag > body.
        for (const [value, weight] of fields) {
          if (value.folded.includes(phrase)) score += weight * 20;
          if (value.folded === phrase) score += weight * 20;
        }
        const positions = terms.map(term => record.text.folded.indexOf(term)).filter(at => at >= 0);
        if (positions.length === terms.length) {
          const span = Math.max(...positions) - Math.min(...positions);
          score += 20 / (1 + span / 100);
        }
        matches.push({ record, score: score * record.boost });
      }
      matches.sort((a, b) => b.score - a.score || (a.record.location < b.record.location ? -1 : 1));
      const groups = new Map();
      for (const { record, score } of matches) {
        if (!groups.has(record.page)) groups.set(record.page, []);
        groups.get(record.page).push(this.item(record, terms, score));
      }
      for (const [page, items] of groups) {
        if (!items.some(item => item.location === page)) items.push(this.item(this.pages.get(page), [], 0));
      }
      return { items: [...groups.values()] };
    }
  }

  const api = { LiteralSearch, parseQuery };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.PeicdSearch = api;
})(typeof self !== "undefined" ? self : globalThis);
