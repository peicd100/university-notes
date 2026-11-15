/* Navigation disclosure, not an ARIA application menu. Shell is built in Python. */
(function () {
  "use strict";
  const BASE = "peicd-folder-pathbar";
  let openItem = null;

  function close(restore = false) {
    if (!openItem) return;
    const item = openItem;
    item.classList.remove("is-open");
    item.querySelector("button").setAttribute("aria-expanded", "false");
    item.querySelector("." + BASE + "__menu").hidden = true;
    openItem = null;
    if (restore) item.querySelector("button").focus();
  }

  function position(item) {
    const menu = item.querySelector("." + BASE + "__menu");
    menu.style.left = "0px";
    const rect = menu.getBoundingClientRect();
    if (rect.right > innerWidth - 12) menu.style.left = (innerWidth - 12 - rect.right) + "px";
  }

  function visibleLinks(menu) {
    return [...menu.querySelectorAll("li:not([hidden]) a")];
  }

  function build(item) {
    const menu = item.querySelector("." + BASE + "__menu");
    if (menu.dataset.built) return;
    let options;
    try { options = JSON.parse(item.dataset.peicdOptions); } catch (_) { return; }
    menu.dataset.built = "true";
    const title = document.createElement("strong");
    title.className = BASE + "__caption";
    title.textContent = menu.dataset.caption;
    menu.appendChild(title);
    const filter = document.createElement("input");
    filter.type = "search";
    filter.className = BASE + "__filter";
    filter.placeholder = "篩選這份清單…";
    filter.setAttribute("aria-label", "篩選" + menu.dataset.caption);
    filter.hidden = options.length < 9;
    menu.appendChild(filter);
    const list = document.createElement("ul");
    list.className = BASE + "__options";
    for (const entry of options) {
      let url;
      try { url = new URL(entry.href, document.baseURI); } catch (_) { continue; }
      if (!/^https?:$/.test(url.protocol)) continue;
      const row = document.createElement("li");
      row.dataset.label = String(entry.label).normalize("NFKC").toLowerCase();
      const link = document.createElement("a");
      link.className = BASE + "__option";
      link.href = entry.href; // Real anchors retain Material instant navigation and modified clicks.
      link.textContent = entry.label;
      if (entry.current) {
        link.classList.add(BASE + "__option--current");
        link.setAttribute("aria-current", menu.dataset.caption === "切換頁面" ? "page" : "true");
        const badge = document.createElement("small");
        badge.textContent = "目前";
        badge.className = BASE + "__current";
        link.appendChild(badge);
      }
      row.appendChild(link);
      list.appendChild(row);
    }
    menu.appendChild(list);
    const count = document.createElement("span");
    count.className = BASE + "__count";
    count.setAttribute("role", "status");
    const update = () => {
      const query = filter.value.normalize("NFKC").trim().toLowerCase();
      let shown = 0;
      for (const row of list.children) {
        row.hidden = !row.dataset.label.includes(query);
        if (!row.hidden) shown++;
      }
      count.textContent = shown ? `${shown} 個項目` : "沒有符合的項目";
    };
    filter.addEventListener("input", update);
    menu.appendChild(count);
    update();
    menu.addEventListener("keydown", event => {
      if (event.isComposing) return;
      if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(true); return; }
      if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
      if (event.target === filter && ["Home", "End"].includes(event.key)) return;
      const links = visibleLinks(menu);
      if (!links.length) return;
      event.preventDefault();
      const at = links.indexOf(document.activeElement);
      const index = event.key === "Home" ? 0 : event.key === "End" ? links.length - 1 :
        event.key === "ArrowDown" ? (at + 1) % links.length : (at <= 0 ? links.length : at) - 1;
      links[index].focus();
    });
    menu.addEventListener("click", event => { if (event.target.closest("a")) close(); });
  }

  function show(item, focus = false) {
    if (openItem !== item) close();
    build(item);
    const menu = item.querySelector("." + BASE + "__menu");
    menu.hidden = false;
    item.classList.add("is-open");
    item.querySelector("button").setAttribute("aria-expanded", "true");
    openItem = item;
    position(item);
    const current = menu.querySelector('[aria-current]');
    if (current) menu.scrollTop = Math.max(0, current.offsetTop - menu.clientHeight / 2);
    if (focus) (current || visibleLinks(menu)[0])?.focus();
  }

  function visibility() {
    const bar = document.querySelector("." + BASE);
    if (!bar) return;
    const hidden = document.getElementById("__drawer")?.checked || document.getElementById("__search")?.checked;
    bar.classList.toggle(BASE + "--hidden", Boolean(hidden));
    if (hidden) close();
  }

  function init() {
    if (openItem && !openItem.isConnected) openItem = null;
    document.querySelectorAll("." + BASE + "__item").forEach(item => {
      if (item.dataset.bound) return;
      item.dataset.bound = "true";
      const button = item.querySelector("button");
      button.addEventListener("click", () => openItem === item ? close() : show(item));
      button.addEventListener("keydown", event => {
        if (["ArrowDown", "ArrowUp"].includes(event.key)) { event.preventDefault(); show(item, true); }
      });
      item.addEventListener("focusout", event => {
        if (event.relatedTarget && item.contains(event.relatedTarget)) return;
        // A microtask runs before mousedown's focus default: it can hide the
        // destination link and swallow the click. Wait until focus has settled.
        setTimeout(() => {
          if (openItem === item && !item.contains(document.activeElement)) close();
        }, 0);
      });
    });
    visibility();
  }
  document.addEventListener("pointerdown", event => {
    if (openItem && !openItem.contains(event.target)) close();
  }, true);
  document.addEventListener("keydown", event => {
    if (openItem && event.key === "Escape") { event.preventDefault(); close(true); }
  });
  document.addEventListener("change", event => {
    if (["__drawer", "__search"].includes(event.target.id)) visibility();
  });
  window.addEventListener("resize", () => { if (openItem) position(openItem); }, { passive: true });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
  window.document$?.subscribe(init);
})();
