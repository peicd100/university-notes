(function () {
  if (window.__PEICD_SOURCE_JUMP__) {
    if (typeof window.__PEICD_SOURCE_JUMP__.init === "function") {
      window.__PEICD_SOURCE_JUMP__.init();
    }
    return;
  }

  var LOCAL_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
  var CONTENT_SELECTOR = ".md-content .md-content__inner, .md-content, main";
  var BLOCK_SELECTOR = "p, li, pre, blockquote, h1, h2, h3, h4, h5, h6, td, th, summary";
  var STATUS_ID = "peicd-source-jump-status";
  var STYLE_ID = "peicd-source-jump-style";
  var MAX_SELECTION_CHARS = 600;
  var MAX_CONTAINER_CHARS = 2000;
  var MAX_PREFIX_CHARS = 500;
  var MAX_NEIGHBOR_CHARS = 500;
  var MAX_HEADING_PATH_CHARS = 500;
  var bound = false;
  var opening = false;
  var endpointProbe = null;
  var endpointAvailable = false;
  var endpointChecked = false;
  var statusTimer = null;

  function isLocalPreview() {
    return LOCAL_HOSTS.has(window.location.hostname);
  }

  function isMkDocsServePreview() {
    return typeof window.livereload === "function";
  }

  function getContentRoot() {
    return document.querySelector(".md-content .md-content__inner")
      || document.querySelector(".md-content")
      || document.querySelector("main")
      || document.body;
  }

  function getSiteBaseUrl() {
    if (window.__md_scope && typeof window.__md_scope.href === "string") {
      return window.__md_scope;
    }

    var configNode = document.getElementById("__config");
    if (configNode) {
      try {
        var config = JSON.parse(configNode.textContent || "{}");
        if (config && config.base) {
          return new URL(config.base, window.location.href);
        }
      } catch (_) {
      }
    }

    return new URL(".", window.location.href);
  }

  function clearStatus() {
    window.clearTimeout(statusTimer);
    var status = document.getElementById(STATUS_ID);
    if (status) status.remove();
  }

  function showFailure(message) {
    clearStatus();
    if (!document.getElementById(STYLE_ID)) {
      var style = document.createElement("style");
      style.id = STYLE_ID;
      style.textContent = "#" + STATUS_ID + "{position:fixed;right:16px;bottom:20px;z-index:10001;max-width:min(440px,calc(100vw - 32px));padding:12px 16px;border:1px solid var(--md-default-fg-color--light,#888);border-radius:10px;background:var(--md-default-bg-color,#fff);color:var(--md-default-fg-color,#222);font-size:14px;overflow-wrap:anywhere;pointer-events:none;}";
      document.head.appendChild(style);
    }
    var status = document.createElement("div");
    status.id = STATUS_ID;
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.textContent = message;
    document.body.appendChild(status);
    statusTimer = window.setTimeout(clearStatus, 6000);
  }

  function sanitizeText(text, maxLength) {
    var cleaned = String(text || "")
      .replace(/\u00a0/g, " ")
      .replace(/[\u200b\u200c\u200d\ufeff]/g, "")
      .replace(/\s+/g, " ")
      .trim();

    if (maxLength && cleaned.length > maxLength) {
      return cleaned.slice(0, maxLength);
    }
    return cleaned;
  }

  function getSelectionText() {
    var selection = window.getSelection ? window.getSelection() : null;
    if (!selection || selection.rangeCount === 0) return "";
    var text = sanitizeText(selection.toString(), MAX_SELECTION_CHARS);
    if (!text || text.length > MAX_SELECTION_CHARS) return "";
    return text;
  }

  function getSelectionObject() {
    return window.getSelection ? window.getSelection() : null;
  }

  function closestElement(node) {
    if (!node) return null;
    return node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  }

  function getClosestBlock(node) {
    var root = getContentRoot();
    var element = closestElement(node);
    if (!element || !root.contains(element)) return null;
    return element.closest(BLOCK_SELECTOR) || root;
  }

  function isWithinContent(node) {
    var root = getContentRoot();
    var element = closestElement(node);
    return !!(root && element && root.contains(element));
  }

  function getBlockText(block) {
    return sanitizeText(block && (block.innerText || block.textContent || ""), MAX_CONTAINER_CHARS);
  }

  function getContentBlocks() {
    var root = getContentRoot();
    if (!root) return [];

    return Array.prototype.filter.call(
      root.querySelectorAll(BLOCK_SELECTOR),
      function (node) {
        return !!sanitizeText(node && (node.innerText || node.textContent || ""), 1);
      }
    );
  }

  function getHeadingPath(block) {
    var root = getContentRoot();
    if (!root || !block) return "";

    var headings = root.querySelectorAll("h1, h2, h3, h4, h5, h6");
    var stack = [];

    for (var i = 0; i < headings.length; i += 1) {
      var heading = headings[i];
      var relation = heading.compareDocumentPosition(block);
      var isBeforeBlock = heading === block || !!(relation & Node.DOCUMENT_POSITION_FOLLOWING);
      if (!isBeforeBlock) break;

      var level = parseInt(heading.tagName.slice(1), 10);
      if (!level) continue;

      var text = sanitizeText(heading.innerText || heading.textContent || "", 120);
      if (!text) continue;

      stack = stack.slice(0, Math.max(level - 1, 0));
      stack.push(text);
    }

    return sanitizeText(stack.join(" / "), MAX_HEADING_PATH_CHARS);
  }

  function getBlockContextMeta(block) {
    if (!block) {
      return {
        blockTag: "",
        blockIndex: -1,
        sectionBlockIndex: -1,
        blockProgress: -1,
        headingPath: "",
        prevBlock: "",
        nextBlock: ""
      };
    }

    var blocks = getContentBlocks();
    var blockIndex = blocks.indexOf(block);
    var sectionBlockIndex = -1;
    var blockProgress = -1;
    var prevBlock = "";
    var nextBlock = "";

    if (blockIndex >= 0) {
      var nearestHeadingIndex = -1;
      for (var headingIndex = blockIndex; headingIndex >= 0; headingIndex -= 1) {
        if (/^H[1-6]$/.test(blocks[headingIndex].tagName || "")) {
          nearestHeadingIndex = headingIndex;
          break;
        }
      }
      sectionBlockIndex = nearestHeadingIndex >= 0 ? blockIndex - nearestHeadingIndex : blockIndex;
      blockProgress = blocks.length > 1 ? blockIndex / (blocks.length - 1) : 0;
    }

    if (blockIndex >= 0) {
      for (var prevIndex = blockIndex - 1; prevIndex >= 0; prevIndex -= 1) {
        prevBlock = sanitizeText(blocks[prevIndex].innerText || blocks[prevIndex].textContent || "", MAX_NEIGHBOR_CHARS);
        if (prevBlock) break;
      }

      for (var nextIndex = blockIndex + 1; nextIndex < blocks.length; nextIndex += 1) {
        nextBlock = sanitizeText(blocks[nextIndex].innerText || blocks[nextIndex].textContent || "", MAX_NEIGHBOR_CHARS);
        if (nextBlock) break;
      }
    }

    return {
      blockTag: (block.tagName || "").toLowerCase(),
      blockIndex: blockIndex,
      sectionBlockIndex: sectionBlockIndex,
      blockProgress: blockProgress,
      headingPath: getHeadingPath(block),
      prevBlock: prevBlock,
      nextBlock: nextBlock
    };
  }

  function buildSelectionContext(targetNode) {
    var selection = getSelectionObject();
    if (!selection || selection.rangeCount === 0) return null;

    var range = selection.getRangeAt(0);
    if (range.collapsed) return null;

    var text = getSelectionText();
    if (!text) return null;

    var clickedBlock = getClosestBlock(targetNode);
    var block = getClosestBlock(range.startContainer || selection.anchorNode);
    if (!block || !clickedBlock || block !== clickedBlock) return null;
    var blockMeta = getBlockContextMeta(block);

    var containerText = getBlockText(block);
    var prefixText = "";

    try {
      var prefixRange = document.createRange();
      prefixRange.selectNodeContents(block);
      prefixRange.setEnd(range.startContainer, range.startOffset);
      prefixText = sanitizeText(prefixRange.toString(), MAX_PREFIX_CHARS);
    } catch (_) {
      prefixText = "";
    }

    return {
      page: window.location.pathname,
      selection: text,
      container: containerText,
      prefix: prefixText,
      hasSelection: true,
      headingPath: blockMeta.headingPath,
      prevBlock: blockMeta.prevBlock,
      nextBlock: blockMeta.nextBlock,
      blockTag: blockMeta.blockTag,
      blockIndex: blockMeta.blockIndex,
      sectionBlockIndex: blockMeta.sectionBlockIndex,
      blockProgress: blockMeta.blockProgress
    };
  }

  function buildBlockContext(targetNode) {
    var block = getClosestBlock(targetNode);
    if (!block) return null;
    var blockMeta = getBlockContextMeta(block);

    var containerText = getBlockText(block);
    if (!containerText) return null;

    return {
      page: window.location.pathname,
      selection: "",
      container: containerText,
      prefix: "",
      hasSelection: false,
      headingPath: blockMeta.headingPath,
      prevBlock: blockMeta.prevBlock,
      nextBlock: blockMeta.nextBlock,
      blockTag: blockMeta.blockTag,
      blockIndex: blockMeta.blockIndex,
      sectionBlockIndex: blockMeta.sectionBlockIndex,
      blockProgress: blockMeta.blockProgress
    };
  }

  function buildPointContext(event) {
    var context = buildBlockContext(event.target);
    if (!context) return null;
    var element = event.target.nodeType === 1 ? event.target : event.target.parentElement;
    var block = getClosestBlock(element);
    var formula = element.closest(".arithmatex");
    if (formula && block.contains(formula)) {
      context.mathSource = formula.dataset.peicdTex || (!formula.querySelector("mjx-container") ? formula.textContent : "");
      var formulas = block.matches(".arithmatex") ? [block] : Array.from(block.querySelectorAll(".arithmatex"));
      context.mathIndex = formulas.indexOf(formula);
      return context;
    }
    if (element.closest("img, svg, .mermaid, .peicd-mermaid-host, input, textarea, [contenteditable='true']")) return context;
    try {
      var caret = document.caretPositionFromPoint
        ? document.caretPositionFromPoint(event.clientX, event.clientY) : null;
      var hit = !caret && document.caretRangeFromPoint
        ? document.caretRangeFromPoint(event.clientX, event.clientY) : null;
      var node = caret ? caret.offsetNode : hit && hit.startContainer;
      var offset = caret ? caret.offset : hit && hit.startOffset;
      if (!node || node.nodeType !== 3 || getClosestBlock(node) !== block || !node.length) return context;
      if (node.parentElement.closest(".arithmatex, svg, .mermaid")) return context;
      // Hit-testing can return the nearest text for clicks in empty margins.
      // Accept only a caret adjacent to a glyph actually under the pointer.
      var glyph = document.createRange();
      glyph.setStart(node, Math.min(offset, node.length - 1));
      glyph.setEnd(node, Math.min(offset + 1, node.length));
      var previous = document.createRange();
      previous.setStart(node, Math.max(0, offset - 1));
      previous.setEnd(node, offset);
      var rects = Array.from(glyph.getClientRects()).concat(Array.from(previous.getClientRects()));
      if (!rects.some(function (r) { return event.clientX >= r.left - 2 && event.clientX <= r.right + 2 && event.clientY >= r.top - 2 && event.clientY <= r.bottom + 2; })) return context;
      var chars = Array.from(node.nodeValue);
      var at = Array.from(node.nodeValue.slice(0, offset)).length;
      var start = Math.max(0, at - 40), end = Math.min(chars.length, at + 40);
      var anchor = chars.slice(start, end).join("");
      if (!anchor.trim()) return context;
      var prefix = document.createRange();
      prefix.selectNodeContents(block);
      prefix.setEnd(node, chars.slice(0, start).join("").length);
      // Preserve the raw snippet: backend offsets are Unicode code points;
      // display/Markdown normalization must not move the requested caret.
      context.selection = anchor;
      context.caretOffset = at - start;
      var prefixText = sanitizeText(prefix.toString());
      context.pointPrefixLength = Array.from(prefixText).length;
      context.prefix = prefixText.slice(0, MAX_PREFIX_CHARS);
    } catch (_) { /* Unsupported hit-testing: keep the block fallback. */ }
    return context;
  }

  function makeLookupUrl(context) {
    var url = new URL("__peicd/source-jump", getSiteBaseUrl());
    url.searchParams.set("page", context.page);
    url.searchParams.set("selection", context.selection);
    if (context.container) url.searchParams.set("container", context.container);
    if (context.prefix) url.searchParams.set("prefix", context.prefix);
    if (typeof context.caretOffset === "number") url.searchParams.set("caret_offset", String(context.caretOffset));
    if (typeof context.pointPrefixLength === "number") url.searchParams.set("point_prefix_length", String(context.pointPrefixLength));
    if (context.mathSource) url.searchParams.set("math_source", context.mathSource);
    if (typeof context.mathIndex === "number") url.searchParams.set("math_index", String(context.mathIndex));
    if (context.headingPath) url.searchParams.set("heading_path", context.headingPath);
    if (context.prevBlock) url.searchParams.set("prev_block", context.prevBlock);
    if (context.nextBlock) url.searchParams.set("next_block", context.nextBlock);
    if (context.blockTag) url.searchParams.set("block_tag", context.blockTag);
    if (typeof context.blockIndex === "number" && context.blockIndex >= 0) {
      url.searchParams.set("block_index", String(context.blockIndex));
    }
    if (typeof context.sectionBlockIndex === "number" && context.sectionBlockIndex >= 0) {
      url.searchParams.set("section_index", String(context.sectionBlockIndex));
    }
    if (typeof context.blockProgress === "number" && context.blockProgress >= 0) {
      url.searchParams.set("block_progress", context.blockProgress.toFixed(6));
    }
    return url.toString();
  }

  function makeProbeUrl() {
    return makeLookupUrl({
      page: window.location.pathname,
      selection: "__probe__",
      container: "",
      prefix: "",
      headingPath: "",
      prevBlock: "",
      nextBlock: "",
      blockTag: "",
      blockIndex: -1,
      sectionBlockIndex: -1,
      blockProgress: -1
    });
  }

  async function probeEndpoint() {
    if (endpointChecked) return endpointAvailable;
    if (endpointProbe) return endpointProbe;

    endpointProbe = fetch(makeProbeUrl(), {
      method: "GET",
      headers: { "Accept": "application/json" },
      cache: "no-store"
    }).then(function (response) {
      var contentType = String(response.headers.get("content-type") || "");
      endpointAvailable = contentType.indexOf("application/json") >= 0;
      endpointChecked = true;
      return endpointAvailable;
    }).catch(function () {
      endpointAvailable = false;
      endpointChecked = true;
      return false;
    }).finally(function () {
      endpointProbe = null;
    });

    return endpointProbe;
  }

  async function openSourceLocation(context) {
    try {
      var url = new URL(makeLookupUrl(context));
      url.searchParams.set("action", "open");
      var response = await fetch(url.toString(), {
        method: "GET",
        headers: { "Accept": "application/json" },
        cache: "no-store"
      });

      var payload = await response.json().catch(function () { return null; });
      if (!response.ok || !payload || !payload.ok || payload.opened !== true) {
        var message = payload && payload.message ? payload.message : "目前無法自動開啟對應檔案。";
        showFailure(message);
        return;
      }

      // Successful jumps are intentionally silent: no menu or extra click.
    } catch (error) {
      showFailure("開檔失敗，請確認目前是用 mkdocs serve 預覽。");
      console.error("[source-jump] lookup failed:", error);
    }
  }

  async function handleContextMenu(event) {
    if (!isLocalPreview()) return;
    if (!isWithinContent(event.target)) return;

    var context = buildSelectionContext(event.target) || buildPointContext(event);
    if (!context) return;

    event.preventDefault();
    event.stopPropagation();

    if (opening) return;
    // Lock before the endpoint probe too; rapid clicks must not queue opens.
    opening = true;
    clearStatus();
    var ttsPop = document.getElementById("tts-selection-pop");
    if (ttsPop) ttsPop.style.display = "none";
    try {
      if (!(await probeEndpoint())) {
        showFailure("無法連線到原文定位服務，請確認已啟動 mkdocs serve 預覽。");
        return;
      }
      await openSourceLocation(context);
    } finally {
      opening = false;
    }
  }

  function bindGlobalEventsOnce() {
    if (bound) return;
    bound = true;

    document.addEventListener("contextmenu", handleContextMenu, true);

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") clearStatus();
    });
    document.addEventListener("navigation:complete", clearStatus);
  }

  function init() {
    if (!isLocalPreview() || !isMkDocsServePreview()) return;
    bindGlobalEventsOnce();
  }

  window.__PEICD_SOURCE_JUMP__ = { init: init };

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
