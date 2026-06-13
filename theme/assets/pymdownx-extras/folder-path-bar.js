(function () {
  "use strict";

  const BAR_CLASS = "peicd-folder-pathbar";
  const OPEN_CLASS = "is-open";
  const HIDDEN_CLASS = BAR_CLASS + "--hidden";
  let outsideBound = false;

  function isDrawerOpen() {
    const drawer = document.getElementById("__drawer");
    return Boolean(drawer && drawer.checked);
  }

  function isSearchOpen() {
    const search = document.getElementById("__search");
    return Boolean(search && search.checked);
  }

  function getArticleRoot() {
    return document.querySelector("article.md-content__inner.md-typeset")
      || document.querySelector("article.md-content__inner")
      || document.querySelector(".md-content__inner.md-typeset");
  }

  function getTitleElement(root) {
    if (!root) return null;
    return root.querySelector(":scope > h1") || root.querySelector("h1");
  }

  function getActiveSectionLink() {
    return document.querySelector(".md-tabs__item--active > .md-tabs__link")
      || document.querySelector(".md-sidebar--primary li.md-nav__item--section.md-nav__item--active > label.md-nav__link")
      || document.querySelector(".md-sidebar--primary li.md-nav__item--section.md-nav__item--active > a.md-nav__link");
  }

  function getSectionOptions() {
    return Array.from(document.querySelectorAll(".md-tabs__item > .md-tabs__link"))
      .map((link) => ({
        label: normalizeLabel(link.textContent),
        href: link.href,
        current: link.closest(".md-tabs__item")?.classList.contains("md-tabs__item--active") || false
      }))
      .filter((item) => item.label && item.href);
  }

  function getCurrentSectionContainer() {
    return document.querySelector(".md-sidebar--primary li.md-nav__item--section.md-nav__item--active > nav.md-nav[data-md-level=\"1\"]");
  }

  function getDirectChild(element, selector) {
    if (!element) return null;
    return Array.from(element.children).find((child) => child.matches(selector)) || null;
  }

  function getDirectNavList(nav) {
    return nav ? getDirectChild(nav, "ul.md-nav__list") : null;
  }

  function getDirectPageLink(item) {
    return getDirectChild(item, "a.md-nav__link[href]");
  }

  function getDirectGroupLabel(item) {
    return getDirectChild(item, "label.md-nav__link");
  }

  function getDirectChildPageNav(item) {
    return Array.from(item.children).find((child) => (
      child.matches("nav.md-nav")
      && !child.classList.contains("md-nav--secondary")
    )) || null;
  }

  function normalizeComparableUrl(value) {
    try {
      const url = new URL(value, window.location.href);
      url.hash = "";
      return url.href;
    } catch (_) {
      return String(value || "").split("#")[0];
    }
  }

  function isCurrentPageLink(link) {
    if (!link) return false;
    if (link.classList.contains("md-nav__link--active")) return true;
    return normalizeComparableUrl(link.href) === normalizeComparableUrl(window.location.href);
  }

  function joinPageLabel(parts, label) {
    return parts.concat(label).filter(Boolean).join(" / ");
  }

  function collectPageOptionsFromList(list, parents) {
    if (!list) return [];

    return Array.from(list.children).flatMap((item) => {
      if (!item.matches("li.md-nav__item")) return [];

      const options = [];
      const pageLink = getDirectPageLink(item);
      if (pageLink) {
        const label = normalizeLabel(pageLink.textContent);
        if (label && pageLink.href) {
          options.push({
            label: joinPageLabel(parents, label),
            href: pageLink.href,
            current: isCurrentPageLink(pageLink)
          });
        }
      }

      const childNav = getDirectChildPageNav(item);
      if (childNav) {
        const groupLabel = normalizeLabel(getDirectGroupLabel(item)?.textContent);
        const nextParents = groupLabel ? parents.concat(groupLabel) : parents;
        options.push(...collectPageOptionsFromList(getDirectNavList(childNav), nextParents));
      }

      return options;
    });
  }

  function getPageOptions() {
    const sectionNav = getCurrentSectionContainer();
    if (!sectionNav) return [];

    return collectPageOptionsFromList(getDirectNavList(sectionNav), [])
      .filter((item) => item.label && item.href);
  }

  function getActivePageLink() {
    return document.querySelector(".md-sidebar--primary a.md-nav__link.md-nav__link--active[href]")
      || document.querySelector(".md-sidebar--primary li.md-nav__item--active > a.md-nav__link[href]");
  }

  function normalizeLabel(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function closeMenus(except) {
    document.querySelectorAll("." + BAR_CLASS + "__item." + OPEN_CLASS).forEach((item) => {
      if (item === except) return;
      item.classList.remove(OPEN_CLASS);
      const button = item.querySelector("." + BAR_CLASS + "__toggle");
      if (button) button.setAttribute("aria-expanded", "false");
    });
  }

  function syncBarVisibility(bar) {
    const target = bar || document.querySelector("." + BAR_CLASS);
    if (!target) return;

    const hidden = isDrawerOpen() || isSearchOpen();
    target.classList.toggle(HIDDEN_CLASS, hidden);
    if (hidden) closeMenus(null);
  }

  function scrollCurrentOptionIntoView(menu) {
    const current = menu && menu.querySelector("." + BAR_CLASS + "__option--current");
    if (!current) return;
    requestAnimationFrame(() => {
      try {
        current.scrollIntoView({ block: "center", inline: "nearest" });
      } catch (_) {
        current.scrollIntoView(false);
      }
    });
  }

  function bindGlobalClose() {
    if (outsideBound) return;
    outsideBound = true;

    document.addEventListener("mousedown", (event) => {
      const target = event.target;
      if (!(target instanceof Element) || target.closest("." + BAR_CLASS)) return;
      closeMenus(null);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      closeMenus(null);
    });

    document.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) return;
      if (target.id !== "__drawer" && target.id !== "__search") return;
      syncBarVisibility();
    });
  }

  function createMenuItem(option) {
    const link = document.createElement("a");
    link.className = BAR_CLASS + "__option";
    link.href = option.href;
    link.textContent = option.label;
    if (option.current) {
      link.classList.add(BAR_CLASS + "__option--current");
      link.setAttribute("aria-current", "page");
    }
    return link;
  }

  function createMobileSelect(option, options, ariaLabel) {
    const wrapper = document.createElement("div");
    wrapper.className = BAR_CLASS + "__mobile-group";

    const select = document.createElement("select");
    select.className = BAR_CLASS + "__mobile-select";
    select.setAttribute("aria-label", ariaLabel);

    options.forEach((entry) => {
      const optionElement = document.createElement("option");
      optionElement.value = entry.href;
      optionElement.textContent = entry.label;
      optionElement.selected = Boolean(entry.current);
      select.appendChild(optionElement);
    });

    select.value = option.href;
    select.addEventListener("change", () => {
      if (!select.value) return;
      window.location.href = select.value;
    });

    wrapper.appendChild(select);
    return wrapper;
  }

  function createSegment(option, options, ariaLabel) {
    const item = document.createElement("div");
    item.className = BAR_CLASS + "__item";
    if (option.current) item.classList.add(BAR_CLASS + "__item--current");

    const button = document.createElement("button");
    button.type = "button";
    button.className = BAR_CLASS + "__toggle";
    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    button.innerHTML = [
      '<span class="' + BAR_CLASS + '__label"></span>',
      '<span class="' + BAR_CLASS + '__caret" aria-hidden="true">▾</span>'
    ].join("");
    button.querySelector("." + BAR_CLASS + "__label").textContent = option.label;

    const menu = document.createElement("div");
    menu.className = BAR_CLASS + "__menu";
    menu.setAttribute("role", "menu");
    options.forEach((entry) => menu.appendChild(createMenuItem(entry)));

    button.addEventListener("click", () => {
      const nextOpen = !item.classList.contains(OPEN_CLASS);
      closeMenus(item);
      item.classList.toggle(OPEN_CLASS, nextOpen);
      button.setAttribute("aria-expanded", String(nextOpen));
      if (nextOpen) scrollCurrentOptionIntoView(menu);
    });

    item.appendChild(button);
    item.appendChild(menu);
    item.appendChild(createMobileSelect(option, options, ariaLabel));
    return item;
  }

  function initFolderPathBar() {
    bindGlobalClose();

    document.querySelectorAll("." + BAR_CLASS).forEach((element) => element.remove());

    const article = getArticleRoot();
    const title = getTitleElement(article);
    if (!article || !title) return;

    const sectionLink = getActiveSectionLink();
    const pageLink = getActivePageLink();
    const sectionOptions = getSectionOptions();
    const pageOptions = getPageOptions();
    const activePageOption = pageOptions.find((item) => item.current)
      || (pageLink ? {
        label: normalizeLabel(pageLink.textContent),
        href: pageLink.href,
        current: true
      } : null);

    if (!sectionLink || !activePageOption || sectionOptions.length === 0 || pageOptions.length === 0) return;

    const bar = document.createElement("nav");
    bar.className = BAR_CLASS;
    bar.setAttribute("aria-label", "目前資料夾路徑");
    bar.classList.toggle(HIDDEN_CLASS, isDrawerOpen() || isSearchOpen());

    const prefix = document.createElement("span");
    prefix.className = BAR_CLASS + "__prefix";
    prefix.textContent = "./";
    bar.appendChild(prefix);

    bar.appendChild(createSegment({
      label: normalizeLabel(sectionLink.textContent),
      href: sectionLink.href,
      current: true
    }, sectionOptions, "切換章節路徑"));

    const slash = document.createElement("span");
    slash.className = BAR_CLASS + "__separator";
    slash.textContent = "/";
    bar.appendChild(slash);

    bar.appendChild(createSegment(activePageOption, pageOptions, "切換頁面路徑"));

    title.parentNode.insertBefore(bar, title);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFolderPathBar, { once: true });
  } else {
    initFolderPathBar();
  }

  if (window.document$?.subscribe) {
    window.document$.subscribe(initFolderPathBar);
  }
})();
