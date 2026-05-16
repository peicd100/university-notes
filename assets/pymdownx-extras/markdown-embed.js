(function () {
  "use strict";

  const CARD_SELECTOR = "[data-peicd-markdown-embed]";
  const PREVIEW_BUTTON_SELECTOR = "[data-peicd-markdown-embed-preview], [data-peicd-markdown-embed-fullscreen]";
  const CLOSE_BUTTON_SELECTOR = "[data-peicd-markdown-embed-close]";
  const FRAME_SELECTOR = ".peicd-markdown-embed__frame";
  const ACTIVE_CLASS = "peicd-markdown-embed--preview";
  const LOCK_CLASS = "peicd-markdown-embed-preview-open";
  const BACKDROP_SELECTOR = "[data-peicd-markdown-embed-backdrop]";
  const SCROLL_MESSAGE_TYPE = "peicd-markdown-embed-scroll";

  let activeCard = null;
  let previousFocus = null;
  let backdrop = null;
  let lastTouchY = null;

  function closestCard(target) {
    if (!target || typeof target.closest !== "function") return null;
    return target.closest(CARD_SELECTOR);
  }

  function ensureBackdrop() {
    if (backdrop && document.body.contains(backdrop)) return backdrop;

    backdrop = document.querySelector(BACKDROP_SELECTOR);
    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.setAttribute("data-peicd-markdown-embed-backdrop", "");
      backdrop.className = "peicd-markdown-embed__backdrop";
      backdrop.hidden = true;
      document.body.append(backdrop);
    }

    return backdrop;
  }

  function updateButton(button) {
    const card = closestCard(button);
    const active = Boolean(card && card === activeCard);
    button.textContent = active ? "關閉" : "放大預覽";
    button.setAttribute("aria-expanded", String(active));
    button.disabled = !card;
  }

  function updateButtons() {
    document.querySelectorAll(PREVIEW_BUTTON_SELECTOR).forEach(updateButton);
  }

  function setPageLocked(locked) {
    document.documentElement.classList.toggle(LOCK_CLASS, locked);
    document.body.classList.toggle(LOCK_CLASS, locked);
  }

  function scrollActiveFrame(deltaX, deltaY) {
    const frame = activeCard?.querySelector(FRAME_SELECTOR);
    if (!frame?.contentWindow) return;

    frame.contentWindow.postMessage(
      {
        type: SCROLL_MESSAGE_TYPE,
        deltaX,
        deltaY,
      },
      "*"
    );
  }

  function closePreview(options = {}) {
    if (!activeCard) return;

    const card = activeCard;
    activeCard = null;
    card.classList.remove(ACTIVE_CLASS);
    card.removeAttribute("role");
    card.removeAttribute("aria-modal");
    setPageLocked(false);
    lastTouchY = null;

    if (backdrop) {
      backdrop.hidden = true;
    }

    updateButtons();

    if (options.restoreFocus !== false && previousFocus && document.contains(previousFocus)) {
      previousFocus.focus({ preventScroll: true });
    }
    previousFocus = null;
  }

  function openPreview(card, trigger) {
    if (!card || card === activeCard) return;

    closePreview({ restoreFocus: false });
    previousFocus = trigger instanceof HTMLElement
      ? trigger
      : document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    activeCard = card;
    card.classList.add(ACTIVE_CLASS);
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-modal", "true");
    setPageLocked(true);

    ensureBackdrop().hidden = false;
    updateButtons();

    const closeButton = card.querySelector(CLOSE_BUTTON_SELECTOR);
    if (closeButton) {
      closeButton.focus({ preventScroll: true });
    }
  }

  function togglePreview(button) {
    const card = closestCard(button);
    if (!card) return;

    if (card === activeCard) {
      closePreview();
    } else {
      openPreview(card, button);
    }
  }

  document.addEventListener("click", (event) => {
    const previewButton = event.target.closest?.(PREVIEW_BUTTON_SELECTOR);
    if (previewButton) {
      event.preventDefault();
      togglePreview(previewButton);
      return;
    }

    const closeButton = event.target.closest?.(CLOSE_BUTTON_SELECTOR);
    if (closeButton) {
      event.preventDefault();
      closePreview();
      return;
    }

    if (event.target.matches?.(BACKDROP_SELECTOR)) {
      closePreview();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closePreview();
    }
  });

  document.addEventListener(
    "wheel",
    (event) => {
      if (!activeCard) return;
      if (event.target.closest?.(FRAME_SELECTOR)) return;

      event.preventDefault();
      scrollActiveFrame(event.deltaX, event.deltaY);
    },
    { capture: true, passive: false }
  );

  document.addEventListener(
    "touchstart",
    (event) => {
      if (!activeCard || event.touches.length !== 1) return;
      lastTouchY = event.touches[0].clientY;
    },
    { capture: true, passive: true }
  );

  document.addEventListener(
    "touchmove",
    (event) => {
      if (!activeCard || event.touches.length !== 1) return;
      if (event.target.closest?.(FRAME_SELECTOR)) return;

      const currentY = event.touches[0].clientY;
      const deltaY = lastTouchY === null ? 0 : lastTouchY - currentY;
      lastTouchY = currentY;
      event.preventDefault();
      scrollActiveFrame(0, deltaY);
    },
    { capture: true, passive: false }
  );

  function init() {
    if (activeCard && !document.contains(activeCard)) {
      closePreview({ restoreFocus: false });
    }
    updateButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }

  window.addEventListener("load", init, { once: true });
  if (window.document$?.subscribe) {
    window.document$.subscribe(init);
  }
})();
