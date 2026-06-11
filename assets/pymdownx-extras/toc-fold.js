(function () {
  "use strict";

  const CLASS = {
    sidebar: "peicd-toc-sidebar",
    head: "peicd-toc-head",
    headRow: "peicd-toc-head__row",
    headRowTitleless: "peicd-toc-head__row--titleless",
    title: "peicd-toc-title",
    toolbar: "peicd-toc-toolbar",
    toolbarGroup: "peicd-toc-toolbar__group",
    control: "peicd-toc-control",
    modeActive: "peicd-toc-control--active",
    dangerMode: "peicd-toc-danger-mode",
    dangerList: "peicd-danger-list",
    dangerItem: "peicd-danger-item",
    dangerLink: "peicd-danger-link",
    dangerLinkTop: "peicd-danger-link__top",
    dangerBadge: "peicd-danger-badge",
    dangerMeta: "peicd-danger-meta",
    dangerCurrentLabel: "peicd-danger-current-label",
    dangerEmpty: "peicd-danger-empty",
    toggle: "peicd-toc-toggle",
    nested: "peicd-toc-item--nested",
    collapsed: "peicd-toc-item--collapsed",
    currentLink: "peicd-toc-link--current",
    currentItem: "peicd-toc-item--current",
    currentPath: "peicd-toc-item--current-path",
    proxyLink: "peicd-toc-link--proxy-current",
    syncing: "peicd-toc-syncing",
    close: "peicd-toc-close",
    mobileToggle: "peicd-mobile-toc-toggle",
    mobileScrim: "peicd-toc-scrim",
    mobileVisible: "peicd-mobile-toc-visible",
    mobileOpen: "peicd-mobile-toc-open"
  };

  const MOBILE_MQ = "(max-width: 59.999em)";
  const AUTO_SCROLL_GUARD_MS = 360;
  const ACTIVATION_OFFSET = 28;
  const FOLLOW_TARGET_RATIO = 0.42;
  const FOLLOW_PADDING_RATIO = 0.18;
  const MOBILE_PANEL_ID = "peicd-mobile-toc-panel";
  const MOBILE_TOGGLE_ID = "peicd-mobile-toc-toggle";

  let state = null;

  function now() {
    return Date.now();
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function listen(target, eventName, handler, options) {
    target.addEventListener(eventName, handler, options);
    state.cleanups.push(() => target.removeEventListener(eventName, handler, options));
  }

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function isMobile() {
    return window.matchMedia(MOBILE_MQ).matches;
  }

  function getHeaderOffset() {
    const header = document.querySelector(".md-header");
    if (header) return Math.round(header.getBoundingClientRect().height);

    const raw = getComputedStyle(document.documentElement).getPropertyValue("--md-header-height").trim();
    const value = parseFloat(raw);
    return Number.isFinite(value) ? value : 56;
  }

  function scheduleSync(force) {
    if (!state) return;
    state.forceSync = state.forceSync || Boolean(force);
    if (state.syncRaf) return;

    state.syncRaf = requestAnimationFrame(() => {
      if (!state) return;
      state.syncRaf = 0;
      const shouldForce = state.forceSync;
      state.forceSync = false;
      sync(shouldForce);
    });
  }

  function setMode(nextMode) {
    if (!state) return;
    state.mode = nextMode;
    state.sidebar.dataset.peicdTocMode = nextMode;

    updateToolbarState();
  }

  function setView(nextView) {
    if (!state) return;

    const view = nextView === "danger" ? "danger" : "toc";
    state.view = view;
    state.sidebar.dataset.peicdTocView = view;
    state.sidebar.classList.toggle(CLASS.dangerMode, view === "danger");
    updateToolbarState();
  }

  function updateToolbarState() {
    if (!state) return;

    const inDangerView = state.view === "danger";
    state.buttons.auto?.setAttribute("aria-pressed", String(!inDangerView && state.mode === "auto"));
    state.buttons.auto?.classList.toggle(CLASS.modeActive, !inDangerView && state.mode === "auto");
    state.buttons.manual?.setAttribute("aria-pressed", String(!inDangerView && state.mode === "manual"));
    state.buttons.manual?.classList.toggle(CLASS.modeActive, !inDangerView && state.mode === "manual");
    state.buttons.danger?.setAttribute("aria-pressed", String(inDangerView));
    state.buttons.danger?.classList.toggle(CLASS.modeActive, inDangerView);
  }

  function setExpanded(item, expanded) {
    item.classList.toggle(CLASS.collapsed, !expanded);

    const toggle = item.querySelector(":scope > ." + CLASS.toggle);
    if (toggle) {
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.setAttribute("title", expanded ? "收合子章節" : "展開子章節");
    }
  }

  function clearCurrentClasses() {
    if (!state?.toc) return;

    state.toc.querySelectorAll(
      "." + CLASS.currentLink + ", ." + CLASS.proxyLink
    ).forEach((element) => {
      element.classList.remove(CLASS.currentLink, CLASS.proxyLink);
      element.removeAttribute("aria-current");
    });

    state.toc.querySelectorAll(
      "." + CLASS.currentItem + ", ." + CLASS.currentPath
    ).forEach((element) => {
      element.classList.remove(CLASS.currentItem, CLASS.currentPath);
    });

    state.toc.querySelectorAll("." + CLASS.dangerCurrentLabel).forEach((element) => {
      element.hidden = true;
    });
  }

  function isVisible(element) {
    if (!element || !element.isConnected) return false;
    if (element.getClientRects().length === 0) return false;

    const style = getComputedStyle(element);
    return style.visibility !== "hidden" && style.display !== "none";
  }

  function getVisibleLink(link) {
    if (!link) return null;
    if (isVisible(link)) return link;

    let item = link.closest("li.md-nav__item");
    while (item && state?.toc?.contains(item)) {
      const candidate = item.querySelector(":scope > a.md-nav__link");
      if (candidate && isVisible(candidate)) return candidate;
      item = item.parentElement?.closest("li.md-nav__item") ?? null;
    }

    return null;
  }

  function applyCurrent(entry) {
    clearCurrentClasses();
    if (!entry) return;

    entry.link.classList.add(CLASS.currentLink);
    entry.link.setAttribute("aria-current", "true");
    const dangerLabel = entry.link.querySelector("." + CLASS.dangerCurrentLabel);
    if (dangerLabel) dangerLabel.hidden = false;

    let item = entry.link.closest("li.md-nav__item");
    if (item) item.classList.add(CLASS.currentItem);

    while (item && state.toc.contains(item)) {
      item.classList.add(CLASS.currentPath);
      item = item.parentElement?.closest("li.md-nav__item") ?? null;
    }

    const visible = getVisibleLink(entry.link);
    if (visible && visible !== entry.link) visible.classList.add(CLASS.proxyLink);
  }

  function expandPath(entry) {
    let item = entry?.link?.closest("li.md-nav__item") ?? null;
    while (item && state.toc.contains(item)) {
      if (item.querySelector(":scope > nav.md-nav")) setExpanded(item, true);
      item = item.parentElement?.closest("li.md-nav__item") ?? null;
    }
  }

  function collapseToCurrent(entry) {
    state.nestedItems.forEach((item) => setExpanded(item, false));
    if (entry) expandPath(entry);
  }

  function getEntryHash(entry) {
    if (!entry?.link) return "";
    return new URL(entry.link.href, window.location.href).hash || "";
  }

  function getCurrentHashId() {
    const hash = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : "";
    if (!hash) return "";

    try {
      return decodeURIComponent(hash);
    } catch (_) {
      return hash;
    }
  }

  function hasDangerHash() {
    const hashId = getCurrentHashId();
    return Boolean(hashId && state?.dangerEntries?.some((entry) => entry.id === hashId));
  }

  function syncHash(entry) {
    const nextHash = getEntryHash(entry);
    if (!nextHash) return;
    if (window.location.hash === nextHash) return;

    history.replaceState(history.state, "", nextHash);
  }

  function findCurrentEntry() {
    if (state?.view === "danger") return findCurrentDangerEntry();
    if (!state?.entries?.length) return null;

    const activationLine = getHeaderOffset() + ACTIVATION_OFFSET;
    let current = state.entries[0];

    for (const entry of state.entries) {
      if (entry.target.getBoundingClientRect().top <= activationLine) current = entry;
      else break;
    }

    return current;
  }

  function findCurrentDangerEntry() {
    if (!state?.dangerEntries?.length) return null;

    const activationLine = getHeaderOffset() + ACTIVATION_OFFSET;
    let current = state.dangerEntries[0];
    let bestDistance = Number.POSITIVE_INFINITY;

    for (const entry of state.dangerEntries) {
      const top = entry.target.getBoundingClientRect().top;
      const distance = Math.abs(top - activationLine);
      const isBeforeOrHere = top <= activationLine;
      const bestTop = current.target.getBoundingClientRect().top;
      const bestIsBeforeOrHere = bestTop <= activationLine;

      if (
        distance < bestDistance ||
        (distance === bestDistance && isBeforeOrHere && !bestIsBeforeOrHere)
      ) {
        current = entry;
        bestDistance = distance;
      }
    }

    return current;
  }

  function followCurrent(entry) {
    if (!state?.scrollWrap || !entry) return;
    if (state.sidebarManualLocked) return;

    const target = getVisibleLink(entry.link);
    if (!target) return;

    const wrap = state.scrollWrap;
    const wrapRect = wrap.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const headHeight = state.head?.getBoundingClientRect().height ?? 0;
    const topPadding = Math.max(headHeight + 14, 20);
    const bottomPadding = 20;
    const freeHeight = Math.max(80, wrap.clientHeight - topPadding - bottomPadding);
    const midpoint = targetRect.top + targetRect.height / 2;
    const comfortTop = wrapRect.top + topPadding + freeHeight * FOLLOW_PADDING_RATIO;
    const comfortBottom = wrapRect.top + topPadding + freeHeight * (1 - FOLLOW_PADDING_RATIO);

    if (midpoint >= comfortTop && midpoint <= comfortBottom) return;

    const desiredMidpoint = wrapRect.top + topPadding + freeHeight * FOLLOW_TARGET_RATIO;
    const delta = midpoint - desiredMidpoint;
    const maxScroll = Math.max(0, wrap.scrollHeight - wrap.clientHeight);
    const nextTop = clamp(wrap.scrollTop + delta, 0, maxScroll);

    if (Math.abs(nextTop - wrap.scrollTop) < 4) return;

    state.autoScrollUntil = now() + AUTO_SCROLL_GUARD_MS;
    wrap.scrollTo({
      top: nextTop,
      behavior: prefersReducedMotion() ? "auto" : "smooth"
    });
  }

  function holdManual() {
    if (!state) return;
    state.sidebarManualLocked = true;
  }

  function releaseManualHold() {
    if (!state) return;
    state.sidebarManualLocked = false;
  }

  function sync(force) {
    if (!state?.toc) return;

    const entry = findCurrentEntry();
    const key = entry?.link?.getAttribute("href") ?? "";
    const changed = key !== state.activeKey;

    applyCurrent(entry);

    if (state.mode === "auto" && (changed || force)) {
      state.sidebar.classList.add(CLASS.syncing);
      collapseToCurrent(entry);
      applyCurrent(entry);
      requestAnimationFrame(() => state?.sidebar?.classList.remove(CLASS.syncing));
    }

    state.activeKey = key;
    if (entry && (changed || force)) syncHash(entry);
    if (state.mode === "auto") followCurrent(entry);
  }

  function createToolbarGroup(label) {
    const group = document.createElement("div");
    group.className = CLASS.toolbarGroup;
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", label);
    return group;
  }

  function createButton(label, options) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = CLASS.control + (options.mode ? " " + options.mode : "");
    button.textContent = label;
    if (options.pressed !== undefined) button.setAttribute("aria-pressed", String(options.pressed));
    if (options.title) button.setAttribute("title", options.title);
    button.addEventListener("click", options.onClick);
    return button;
  }

  function buildToolbar() {
    const toolbar = document.createElement("div");
    toolbar.className = CLASS.toolbar;

    const actions = createToolbarGroup("目錄操作");
    const modes = createToolbarGroup("目錄模式");

    const expandButton = createButton("展開", {
      onClick() {
        setView("toc");
        setMode("manual");
        holdManual();
        state.nestedItems.forEach((item) => setExpanded(item, true));
        scheduleSync(false);
      },
      title: "展開所有章節"
    });

    const collapseButton = createButton("收合", {
      onClick() {
        setView("toc");
        setMode("manual");
        holdManual();
        state.nestedItems.forEach((item) => setExpanded(item, false));
        scheduleSync(false);
      },
      title: "收合所有章節"
    });

    const autoButton = createButton("自動", {
      mode: "peicd-toc-control--mode",
      pressed: true,
      onClick() {
        setView("toc");
        if (state.mode === "auto") {
          releaseManualHold();
          scheduleSync(true);
          return;
        }
        setMode("auto");
        releaseManualHold();
        scheduleSync(true);
      },
      title: "只展開目前閱讀路徑"
    });

    const manualButton = createButton("手動", {
      mode: "peicd-toc-control--mode",
      pressed: false,
      onClick() {
        setView("toc");
        if (state.mode === "manual") {
          holdManual();
          scheduleSync(false);
          return;
        }
        setMode("manual");
        holdManual();
        scheduleSync(false);
      },
      title: "保留你手動展開的狀態"
    });

    const dangerButton = createButton("Danger", {
      mode: "peicd-toc-control--danger",
      pressed: false,
      onClick() {
        setView("danger");
        releaseManualHold();
        scheduleSync(true);
      },
      title: "顯示 Danger Block 目錄"
    });

    actions.append(expandButton, collapseButton);
    modes.append(autoButton, manualButton);
    toolbar.append(actions, modes, dangerButton);

    state.buttons = {
      auto: autoButton,
      manual: manualButton,
      danger: dangerButton
    };

    return toolbar;
  }

  function buildHead() {
    const nav = state.toc.closest(".md-nav--secondary") || state.toc;
    let title = nav.querySelector(".md-nav__title");

    if (!title) {
      title = document.createElement("div");
      nav.insertBefore(title, nav.firstChild);
    }

    title.classList.add(CLASS.title);
    title.removeAttribute("for");
    title.textContent = "";
    title.hidden = true;
    title.setAttribute("aria-hidden", "true");

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = CLASS.close;
    closeButton.setAttribute("aria-label", "關閉目錄");
    closeButton.innerHTML = '<span aria-hidden="true">×</span>';
    closeButton.addEventListener("click", () => setMobileOpen(false));

    const head = document.createElement("div");
    head.className = CLASS.head;

    const row = document.createElement("div");
    row.className = CLASS.headRow + " " + CLASS.headRowTitleless;
    row.append(title, closeButton);

    head.append(row, buildToolbar());
    nav.insertBefore(head, nav.firstChild);

    state.head = head;
    state.closeButton = closeButton;
  }

  function decorateNestedItems() {
    state.nestedItems = [];

    Array.from(state.toc.querySelectorAll("li.md-nav__item")).forEach((item, index) => {
      const childNav = item.querySelector(":scope > nav.md-nav");
      const link = item.querySelector(":scope > a.md-nav__link");
      if (!childNav || !link) return;

      item.classList.add(CLASS.nested);
      childNav.id = childNav.id || "peicd-toc-branch-" + (index + 1);

      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = CLASS.toggle;
      toggle.setAttribute("aria-controls", childNav.id);
      toggle.setAttribute("aria-label", "切換「" + link.textContent.trim() + "」子章節");
      toggle.innerHTML = '<span class="peicd-toc-toggle__icon" aria-hidden="true"></span>';
      toggle.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setMode("manual");
        setExpanded(item, item.classList.contains(CLASS.collapsed));
        holdManual();
        scheduleSync(false);
      });

      link.insertAdjacentElement("afterend", toggle);
      state.nestedItems.push(item);
      setExpanded(item, false);
    });
  }

  function buildEntries() {
    state.entries = Array.from(
      state.toc.querySelectorAll(".md-nav__list a.md-nav__link[href*='#']")
    ).map((link) => {
      const href = link.getAttribute("href");
      if (!href || !href.includes("#")) return null;

      let id = href.split("#").pop();
      try {
        id = decodeURIComponent(id);
      } catch (_) {
        return null;
      }

      const target = document.getElementById(id);
      return target ? { link, target } : null;
    }).filter(Boolean);
  }

  function normalizeText(text) {
    return (text || "").replace(/\s+/g, " ").trim();
  }

  function getHeadingText(heading) {
    if (!heading) return "";

    const clone = heading.cloneNode(true);
    clone.querySelectorAll(".headerlink, .anchor, a[href^='#']").forEach((element) => element.remove());
    return normalizeText(clone.textContent);
  }

  function getDangerTitle(block) {
    const title = block.querySelector(":scope > .admonition-title, :scope > summary");
    const raw = normalizeText(title?.textContent);
    if (!raw) return "";

    const custom = raw.replace(/^Danger(?:\s*\|\s*|\s*[:：-]\s*|\s+)?/i, "").trim();
    return custom && custom.toLowerCase() !== "danger" ? custom : "";
  }

  function getElementTop(element) {
    return element.getBoundingClientRect().top + window.scrollY;
  }

  function findNearestHeading(block, headings) {
    const innerHeading = Array.from(block.querySelectorAll("h1, h2, h3, h4, h5, h6"))
      .find((heading) => getHeadingText(heading));
    if (innerHeading) return { heading: innerHeading, relation: "內部標題" };

    const blockTop = getElementTop(block);
    let previous = null;
    let next = null;

    for (const heading of headings) {
      if (block.contains(heading) || !getHeadingText(heading)) continue;

      const headingTop = getElementTop(heading);
      const candidate = {
        heading,
        distance: Math.abs(blockTop - headingTop),
        relation: headingTop <= blockTop ? "前方標題" : "後方標題"
      };

      if (headingTop <= blockTop) {
        if (!previous || headingTop >= getElementTop(previous.heading)) previous = candidate;
      } else if (!next || headingTop < getElementTop(next.heading)) {
        next = candidate;
      }
    }

    if (previous && next) return previous.distance <= next.distance ? previous : next;
    return previous || next;
  }

  function ensureDangerTargetId(block, index) {
    if (!block.id) block.id = "peicd-danger-block-" + (index + 1);
    return block.id;
  }

  function getArticleRoot() {
    return (
      document.querySelector(".md-content__inner.md-typeset") ||
      document.querySelector(".md-content .md-typeset") ||
      document.querySelector("article.md-content__inner") ||
      document.querySelector("main .md-typeset")
    );
  }

  function createDangerLink(entry) {
    const link = document.createElement("a");
    link.className = "md-nav__link " + CLASS.dangerLink;
    link.href = "#" + encodeURIComponent(entry.id);
    link.setAttribute("title", entry.title);

    const top = document.createElement("span");
    top.className = CLASS.dangerLinkTop;

    const badge = document.createElement("span");
    badge.className = CLASS.dangerBadge;
    badge.textContent = "Danger";

    const label = document.createElement("span");
    label.className = "md-ellipsis";
    label.textContent = entry.title;

    const meta = document.createElement("span");
    meta.className = CLASS.dangerMeta;
    meta.textContent = entry.meta;

    const current = document.createElement("span");
    current.className = CLASS.dangerCurrentLabel;
    current.textContent = "現在在這裡";
    current.hidden = true;

    top.append(badge, label);
    link.append(top, meta, current);
    link.addEventListener("click", (event) => {
      event.preventDefault();
      setView("danger");
      releaseManualHold();
      if (isMobile()) setMobileOpen(false);

      const nextHash = "#" + encodeURIComponent(entry.id);
      if (window.location.hash !== nextHash) {
        history.pushState(history.state, "", nextHash);
      }

      const targetTop = entry.target.getBoundingClientRect().top + window.scrollY - getHeaderOffset() - 12;
      window.scrollTo({
        top: Math.max(0, targetTop),
        behavior: prefersReducedMotion() ? "auto" : "smooth"
      });

      applyCurrent(entry);
      followCurrent(entry);
      window.setTimeout(() => scheduleSync(true), prefersReducedMotion() ? 0 : 260);
    });

    return link;
  }

  function buildDangerEntries() {
    const article = getArticleRoot();
    const blocks = article ? Array.from(article.querySelectorAll(".admonition.danger, details.danger")) : [];
    const headings = article ? Array.from(article.querySelectorAll("h1, h2, h3, h4, h5, h6")) : [];

    state.dangerEntries = blocks.map((block, index) => {
      const customTitle = getDangerTitle(block);
      const nearest = customTitle ? null : findNearestHeading(block, headings);
      const headingTitle = nearest ? getHeadingText(nearest.heading) : "";
      const title = customTitle || headingTitle || "Danger #" + (index + 1);
      const id = ensureDangerTargetId(block, index);
      const meta = customTitle ? "Block 標題" : (nearest ? nearest.relation : "未找到附近標題");

      return {
        id,
        target: block,
        title,
        meta,
        link: null
      };
    });
  }

  function renderDangerList() {
    if (state.dangerList) state.dangerList.remove();

    const list = document.createElement("ul");
    list.className = "md-nav__list " + CLASS.dangerList;

    if (!state.dangerEntries.length) {
      const item = document.createElement("li");
      item.className = "md-nav__item " + CLASS.dangerEmpty;
      item.textContent = "此筆記沒有任何 Danger Block";
      list.append(item);
    } else {
      state.dangerEntries.forEach((entry) => {
        const item = document.createElement("li");
        item.className = "md-nav__item " + CLASS.dangerItem;
        entry.link = createDangerLink(entry);
        item.append(entry.link);
        list.append(item);
      });
    }

    state.toc.append(list);
    state.dangerList = list;
  }

  function createObserver() {
    if (state.observer) state.observer.disconnect();
    const observedEntries = [...state.entries, ...state.dangerEntries];
    if (!observedEntries.length || !("IntersectionObserver" in window)) return;

    state.observer = new IntersectionObserver(() => scheduleSync(), {
      root: null,
      rootMargin: "-" + (getHeaderOffset() + 12) + "px 0px -62% 0px",
      threshold: [0, 1]
    });

    observedEntries.forEach((entry) => state.observer.observe(entry.target));
  }

  function setMobileOpen(open) {
    if (!state?.sidebar) return;

    state.sidebar.classList.toggle(CLASS.mobileVisible, open);
    document.documentElement.classList.toggle(CLASS.mobileOpen, open);

    if (state.mobileButton) {
      state.mobileButton.setAttribute("aria-expanded", String(open));
      state.mobileButton.setAttribute("title", open ? "關閉目錄" : "打開目錄");
      state.mobileButton.setAttribute("aria-label", open ? "關閉目錄" : "打開目錄");
    }

    if (state.mobileScrim) state.mobileScrim.hidden = !open;
  }

  function updateMobileUI() {
    if (!state?.mobileButton || !state.sidebar) return;

    const visible = Boolean(state.entries.length || state.dangerEntries.length) && isMobile();
    state.mobileButton.hidden = !visible;
    state.mobileScrim.hidden = !(visible && state.sidebar.classList.contains(CLASS.mobileVisible));
    state.mobileButton.setAttribute("aria-controls", MOBILE_PANEL_ID);

    if (!visible) setMobileOpen(false);
  }

  function buildMobileChrome() {
    const searchToggle = document.querySelector("label[for='__search'].md-header__button.md-icon");
    const headerOptions = document.querySelector(".md-header__options");
    const headerInner = document.querySelector(".md-header__inner");

    const mobileButton = document.createElement("button");
    mobileButton.type = "button";
    mobileButton.id = MOBILE_TOGGLE_ID;
    mobileButton.className = "md-header__button md-icon " + CLASS.mobileToggle;
    mobileButton.setAttribute("aria-label", "打開目錄");
    mobileButton.setAttribute("title", "打開目錄");
    mobileButton.innerHTML = [
      '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
      '  <path d="M7 5h14v2H7V5M3 4.5A1.5 1.5 0 0 1 4.5 6A1.5 1.5 0 0 1 3 7.5A1.5 1.5 0 0 1 1.5 6A1.5 1.5 0 0 1 3 4.5M7 11h14v2H7v-2M3 10.5A1.5 1.5 0 0 1 4.5 12A1.5 1.5 0 0 1 3 13.5A1.5 1.5 0 0 1 1.5 12A1.5 1.5 0 0 1 3 10.5M7 17h14v2H7v-2M3 16.5A1.5 1.5 0 0 1 4.5 18A1.5 1.5 0 0 1 3 19.5A1.5 1.5 0 0 1 1.5 18A1.5 1.5 0 0 1 3 16.5Z"></path>',
      "</svg>"
    ].join("");
    mobileButton.hidden = true;
    mobileButton.addEventListener("click", () => setMobileOpen(!state.sidebar.classList.contains(CLASS.mobileVisible)));

    const mobileScrim = document.createElement("button");
    mobileScrim.type = "button";
    mobileScrim.className = CLASS.mobileScrim;
    mobileScrim.hidden = true;
    mobileScrim.setAttribute("aria-label", "關閉目錄");
    mobileScrim.addEventListener("click", () => setMobileOpen(false));

    document.body.append(mobileScrim);
    if (searchToggle) searchToggle.insertAdjacentElement("afterend", mobileButton);
    else if (headerOptions) headerOptions.append(mobileButton);
    else if (headerInner) headerInner.append(mobileButton);
    else document.body.append(mobileButton);

    state.mobileButton = mobileButton;
    state.mobileScrim = mobileScrim;
    state.sidebar.id = MOBILE_PANEL_ID;
  }

  function bindSidebarEvents() {
    const wrap = state.scrollWrap;
    if (!wrap) return;

    const markManualKeys = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "]);

    listen(wrap, "wheel", holdManual, { passive: true });
    listen(wrap, "touchstart", holdManual, { passive: true });
    listen(wrap, "touchmove", holdManual, { passive: true });
    listen(wrap, "pointerdown", holdManual, { passive: true });
    listen(wrap, "keydown", (event) => {
      if (markManualKeys.has(event.key)) holdManual();
    });
    listen(wrap, "scroll", () => {
      if (now() > state.autoScrollUntil) holdManual();
    }, { passive: true });
  }

  function bindGlobalEvents() {
    const onResize = () => {
      clearTimeout(state.resizeTimer);
      state.resizeTimer = window.setTimeout(() => {
        createObserver();
        updateMobileUI();
        scheduleSync(true);
      }, 120);
    };
    const onHashChange = () => {
      releaseManualHold();
      scheduleSync(true);
    };
    const onWindowScroll = () => {
      releaseManualHold();
      scheduleSync();
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape" && state?.sidebar?.classList.contains(CLASS.mobileVisible)) setMobileOpen(false);
    };

    listen(window, "resize", onResize, { passive: true });
    listen(window, "scroll", onWindowScroll, { passive: true });
    listen(window, "hashchange", onHashChange);
    listen(document, "keydown", onKeyDown);
    state.cleanups.push(() => clearTimeout(state.resizeTimer));

    const mql = window.matchMedia(MOBILE_MQ);
    const onMediaChange = () => updateMobileUI();
    if (typeof mql.addEventListener === "function") mql.addEventListener("change", onMediaChange);
    else if (typeof mql.addListener === "function") mql.addListener(onMediaChange);

    state.cleanups.push(() => {
      if (typeof mql.removeEventListener === "function") mql.removeEventListener("change", onMediaChange);
      else if (typeof mql.removeListener === "function") mql.removeListener(onMediaChange);
    });
  }

  function resetSidebar(sidebar) {
    sidebar.classList.remove(CLASS.sidebar, CLASS.mobileVisible, CLASS.syncing, CLASS.dangerMode);
    sidebar.removeAttribute("data-peicd-toc-mode");
    sidebar.removeAttribute("data-peicd-toc-view");
    sidebar.querySelectorAll("." + CLASS.toggle).forEach((element) => element.remove());
    sidebar.querySelectorAll("." + CLASS.dangerList).forEach((element) => element.remove());
    sidebar.querySelectorAll("." + CLASS.head).forEach((head) => {
      const nav = sidebar.querySelector(".md-nav--secondary");
      const title = head.querySelector(".md-nav__title");
      if (nav && title && title.parentElement !== nav) nav.insertBefore(title, nav.firstChild);
      head.remove();
    });

    sidebar.querySelectorAll("li.md-nav__item").forEach((item) => {
      item.classList.remove(CLASS.nested, CLASS.collapsed, CLASS.currentItem, CLASS.currentPath);
    });

    sidebar.querySelectorAll("a.md-nav__link").forEach((link) => {
      link.classList.remove(CLASS.currentLink, CLASS.proxyLink);
      link.removeAttribute("aria-current");
    });
  }

  function teardown() {
    if (!state) return;

    if (state.observer) state.observer.disconnect();
    state.cleanups.forEach((cleanup) => {
      try {
        cleanup();
      } catch (_) {
        /* noop */
      }
    });
    clearTimeout(state.resizeTimer);
    if (state.mobileButton) state.mobileButton.remove();
    if (state.mobileScrim) state.mobileScrim.remove();
    document.documentElement.classList.remove(CLASS.mobileOpen);
    state = null;
  }

  function init() {
    teardown();

    const sidebar = document.querySelector(".md-sidebar--secondary");
    const toc = sidebar?.querySelector("[data-md-component='toc']");
    if (!sidebar || !toc) return;

    resetSidebar(sidebar);

    state = {
      sidebar,
      toc,
      scrollWrap: sidebar.querySelector(".md-sidebar__scrollwrap"),
      head: null,
      closeButton: null,
      mobileButton: null,
      mobileScrim: null,
      entries: [],
      dangerEntries: [],
      dangerList: null,
      nestedItems: [],
      buttons: {},
      observer: null,
      mode: "auto",
      view: "toc",
      activeKey: "",
      sidebarManualLocked: false,
      autoScrollUntil: 0,
      resizeTimer: 0,
      syncRaf: 0,
      forceSync: false,
      cleanups: []
    };

    sidebar.classList.add(CLASS.sidebar);
    buildHead();
    decorateNestedItems();
    buildEntries();
    buildDangerEntries();
    renderDangerList();
    buildMobileChrome();
    createObserver();
    bindSidebarEvents();
    bindGlobalEvents();
    setMode("auto");
    setView(hasDangerHash() ? "danger" : "toc");
    updateMobileUI();
    scheduleSync(true);
  }

  if (window.document$?.subscribe) {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
