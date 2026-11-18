(function () {
  "use strict";

  const BUTTON_SELECTOR = "[data-peicd-scroll-bottom]";
  const HIDDEN_CLASS = "is-hidden";
  const HIDE_THRESHOLD_PX = 24;
  let listenersBound = false;
  let frameRequested = false;
  let documentSubscribed = false;
  let lastSectionTarget = null;

  function sectionTargets() {
    const article = document.querySelector("article.md-content__inner, .md-content__inner.md-typeset");
    const headings = Array.from(article?.querySelectorAll("h2") || []).filter(heading => heading.getClientRects().length);
    const currentY = getScrollTop();
    if (lastSectionTarget && Math.abs(lastSectionTarget.y - currentY) <= 2) {
      const index = headings.indexOf(lastSectionTarget.heading);
      if (index >= 0) return { headings, up: headings[index - 1], down: headings[index + 1] };
    }
    lastSectionTarget = null;
    const offset = sectionOffset(headings[0]);
    return {
      headings,
      up: headings.filter(heading => heading.getBoundingClientRect().top < offset - 2).at(-1),
      down: headings.find(heading => heading.getBoundingClientRect().top > offset + 2)
    };
  }

  function sectionOffset(heading) {
    const header = document.querySelector("[data-md-component='header']");
    const headerBottom = Math.max(0, header?.getBoundingClientRect().bottom || 0);
    const margin = heading ? Number.parseFloat(getComputedStyle(heading).scrollMarginTop) || 0 : 0;
    return Math.max(headerBottom + 12, margin);
  }

  function syncSectionNavigation() {
    const navigation = document.querySelector("[data-peicd-section-jump]");
    if (!navigation) return;
    const targets = sectionTargets();
    navigation.hidden = targets.headings.length === 0;
    for (const button of navigation.querySelectorAll("[data-peicd-section-direction]")) {
      button.disabled = !targets[button.dataset.peicdSectionDirection];
    }
  }

  function jumpSection(event) {
    const heading = sectionTargets()[event.currentTarget.dataset.peicdSectionDirection];
    if (!heading) return;
    window.scrollTo({ top: Math.max(0, getScrollTop() + heading.getBoundingClientRect().top - sectionOffset(heading)), behavior: "instant" });
    lastSectionTarget = { heading, y: getScrollTop() };
    syncSectionNavigation();
  }

  function getButton() {
    return document.querySelector(BUTTON_SELECTOR);
  }

  function getScrollRoot() {
    return document.scrollingElement || document.documentElement;
  }

  function getScrollTop() {
    const root = getScrollRoot();
    return Math.max(
      window.scrollY || 0,
      root.scrollTop || 0,
      document.documentElement.scrollTop || 0,
      document.body?.scrollTop || 0
    );
  }

  function getMaxScroll() {
    const root = getScrollRoot();
    return Math.max(0, root.scrollHeight - window.innerHeight);
  }

  function prefersReducedMotion() {
    return Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
  }

  function syncButtonState() {
    syncSectionNavigation();
    const topButton = document.querySelector('[data-peicd-scroll-top]');
    if (topButton) {
      const header = document.querySelector('[data-md-component="header"]');
      topButton.style.setProperty('--peicd-header-bottom', `${Math.max(0, header?.getBoundingClientRect().bottom || 0)}px`);
    }
    const button = getButton();
    if (!button) return;

    const maxScroll = getMaxScroll();
    const scrollTop = getScrollTop();
    const shouldShow = maxScroll > 0 && scrollTop < maxScroll - HIDE_THRESHOLD_PX;

    button.hidden = false;
    button.classList.toggle(HIDDEN_CLASS, !shouldShow);
    button.setAttribute("aria-hidden", String(!shouldShow));
    button.tabIndex = shouldShow ? 0 : -1;
  }

  function requestSync() {
    if (frameRequested) return;
    frameRequested = true;

    window.requestAnimationFrame(() => {
      frameRequested = false;
      syncButtonState();
    });
  }

  function handleClick(event) {
    const target = event.currentTarget.hasAttribute('data-peicd-scroll-top') ? 0 : getMaxScroll();
    window.scrollTo({
      top: target,
      behavior: prefersReducedMotion() ? "auto" : "smooth"
    });
  }

  function bindButton(button) {
    if (button.dataset.peicdScrollBottomBound === "true") return;
    button.dataset.peicdScrollBottomBound = "true";
    button.addEventListener("click", handleClick);
  }

  function bindGlobalListeners() {
    if (listenersBound) return;
    listenersBound = true;

    window.addEventListener("scroll", requestSync, { passive: true });
    window.addEventListener("resize", requestSync, { passive: true });
  }

  function initScrollBottomButton() {
    lastSectionTarget = null;
    for (const control of document.querySelectorAll("[data-peicd-section-direction]")) {
      if (control.dataset.peicdSectionBound === "true") continue;
      control.dataset.peicdSectionBound = "true";
      control.addEventListener("click", jumpSection);
    }
    for (const button of document.querySelectorAll('[data-peicd-scroll-top], [data-peicd-scroll-bottom]')) bindButton(button);
    bindGlobalListeners();
    requestSync();
  }

  function subscribeToMaterialNavigation() {
    if (documentSubscribed) return;
    if (!window.document$?.subscribe) return;

    documentSubscribed = true;
    window.document$.subscribe(initScrollBottomButton);
  }

  function init() {
    initScrollBottomButton();
    subscribeToMaterialNavigation();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }

  window.addEventListener("load", subscribeToMaterialNavigation, { once: true });
})();
