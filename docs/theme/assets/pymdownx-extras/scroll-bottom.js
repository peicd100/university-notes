(function () {
  "use strict";

  const BUTTON_SELECTOR = "[data-peicd-scroll-bottom]";
  const HIDDEN_CLASS = "is-hidden";
  const HIDE_THRESHOLD_PX = 24;
  let listenersBound = false;
  let frameRequested = false;
  let documentSubscribed = false;

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

  function handleClick() {
    const maxScroll = getMaxScroll();
    if (maxScroll <= 0) return;

    window.scrollTo({
      top: maxScroll,
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
    const button = getButton();
    if (!button) return;

    bindButton(button);
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
