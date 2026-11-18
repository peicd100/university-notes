/* Controls and return navigation around Material's sole result renderer. */
(function () {
  "use strict";
  const api = window.__PEICD_SEARCH_LAZY_GUARD__;
  const input = document.querySelector('[data-md-component="search-query"]');
  const result = document.querySelector('[data-md-component="search-result"]');
  if (!api || !input || !result || document.querySelector(".peicd-search-controls")) return;
  const controls = document.createElement("div");
  controls.className = "peicd-search-controls";
  controls.hidden = true;
  const label = document.createElement("label");
  label.textContent = "範圍 ";
  const scope = document.createElement("select");
  scope.setAttribute("aria-label", "搜尋學期與課程");
  label.appendChild(scope);
  controls.appendChild(label);
  function button(text, action) {
    const node = document.createElement("button");
    node.type = "button"; node.textContent = text;
    node.addEventListener("click", action); return node;
  }
  const current = button("目前課程", () => {
    let path;
    try { path = decodeURIComponent(location.pathname).split("/md/")[1]; } catch (_) { return; }
    if (!path) return;
    const parts = path.split("/");
    const value = parts.slice(0, /^\d{3}-[12]$/.test(parts[0]) ? 2 : 1).join("/") + "/";
    if ([...scope.options].some(option => option.value === value)) {
      scope.value = value; api.configure({ scope: value, page: "", offset: 0 });
    }
  });
  controls.appendChild(current);
  const back = button("返回全部文章", () => api.configure({ page: "", offset: 0 }));
  controls.appendChild(back);
  const guide = document.createElement("div");
  guide.id = "peicd-query-guide"; guide.className = "peicd-query-guide"; guide.hidden = true;
  const help = button("搜尋語法", () => {
    guide.hidden = !guide.hidden;
    help.setAttribute("aria-expanded", String(!guide.hidden));
  });
  help.setAttribute("aria-controls", guide.id);
  help.setAttribute("aria-expanded", "false");
  for (const [syntax, meaning] of [
    ["單射 滿射", "同時包含兩個詞，也可用 + 標記必含詞"],
    ["雙射 -證明", "排除含有「證明」的段落"],
    ["單射 OR 滿射", "任一組符合即可；排除詞適用於所有組別"],
    ['"Finite State Machine"', "完整詞組，雙引號內保留詞序"]
  ]) {
    const example = document.createElement("code"), hint = document.createElement("span");
    example.textContent = syntax; hint.textContent = meaning;
    guide.append(example, hint);
  }
  controls.append(help, guide);
  const status = document.createElement("p");
  status.className = "peicd-search-status";
  status.setAttribute("role", "status"); status.setAttribute("aria-atomic", "true");
  controls.appendChild(status);
  const pager = document.createElement("div");
  pager.className = "peicd-search-pager";
  const previous = button("上一批", () => {
    const info = api.snapshot().info;
    api.configure({ offset: Math.max(0, info.offset - info.pageSize) });
  });
  const next = button("下一批", () => {
    const info = api.snapshot().info;
    api.configure({ offset: info.offset + info.pageSize });
  });
  const retry = button("重試", () => api.retry());
  pager.append(previous, next, retry); controls.appendChild(pager);
  input.form.after(controls);
  input.closest(".md-search").dataset.peicdEnhanced = "true";
  controls.addEventListener("keydown", event => { if (event.key !== "Escape") event.stopPropagation(); });
  scope.addEventListener("change", () => api.configure({ scope: scope.value, page: "", offset: 0 }));
  let facetKey = "";
  // The active trip survives a full-page note navigation. Older search lists
  // belong to their own browser history entries, not a global query history.
  const storageKey = "peicd-result-trip:" + new URL(
    JSON.parse(document.getElementById("__config").textContent).base + "/", document.baseURI).pathname;
  let trip = null, restoring = null;
  const scrollwrap = result.closest(".md-search__scrollwrap");
  try { trip = JSON.parse(sessionStorage.getItem(storageKey)); } catch (_) { /* storage optional */ }

  function syncReturn() {
    const control = document.querySelector(".search-return");
    if (control) control.hidden = !trip || new URL(trip.destination).pathname !== location.pathname;
  }
  window.addEventListener("peicd:search-select", event => {
    if (!input.value.trim() || !scrollwrap) return;
    const snapshot = api.snapshot();
    trip = { query: input.value, view: snapshot.view, top: scrollwrap.scrollTop,
      origin: location.href, destination: event.detail };
    try { history.replaceState({ ...history.state, peicdResults: trip }, ""); } catch (_) { /* full navigation fallback */ }
    try { sessionStorage.setItem(storageKey, JSON.stringify(trip)); } catch (_) { /* in-memory trip still works */ }
    restoring = null;
    requestAnimationFrame(syncReturn);
  });

  function finishRestore() {
    if (!restoring || !scrollwrap) return;
    const { info, phase } = api.snapshot();
    if (phase !== "results" || !info || info.query !== restoring.query.trim()) return;
    if (["scope", "page", "offset"].some(key => info[key] !== restoring.view[key])) {
      api.configure(restoring.view);
      return;
    }
    const saved = restoring;
    requestAnimationFrame(() => {
      if (restoring !== saved) return;
      const link = [...result.querySelectorAll("a[href]")].find(node => node.href === saved.destination);
      if (!link) return; // Material appends results asynchronously.
      restoring = null;
      const disclosure = link.closest("details");
      if (disclosure) disclosure.open = true;
      link.focus({ preventScroll: true });
      scrollwrap.scrollTop = saved.top;
      if (Number.isFinite(saved.viewportY)) {
        // The mobile header changes flow when search opens. Preserve the
        // reading position behind it and Material's offset for closing it.
        if (document.body.hasAttribute("data-md-scrolllock")) document.body.style.top = -saved.viewportY + "px";
        if (Math.abs(scrollY - saved.viewportY) > 1) window.scrollTo({ top: saved.viewportY, behavior: "instant" });
      }
    });
  }
  function reopen(saved) {
    if (!saved) return;
    const toggle = document.getElementById("__search");
    restoring = saved;
    if (!toggle.checked) toggle.click();
    input.focus({ preventScroll: true });
    if (input.value !== saved.query || api.snapshot().info?.query !== saved.query.trim()) {
      input.value = saved.query;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
    finishRestore();
  }
  const observer = new MutationObserver(finishRestore);
  observer.observe(result.querySelector("ol") || result, { childList: true, subtree: true });
  document.addEventListener("click", event => {
    if (event.target.closest?.(".search-return")) reopen(trip);
  });
  input.addEventListener("input", () => {
    if (restoring && input.value !== restoring.query) restoring = null;
  });
  let mountedPath = location.pathname, pendingHistory = null, historyTimer = 0;
  function restoreMountedPage() {
    mountedPath = location.pathname;
    if (pendingHistory) {
      const saved = pendingHistory;
      pendingHistory = null;
      // Material 9.7 closes both toggles 125 ms after location/target changes.
      // Restore after that native close, only while still on the source entry.
      clearTimeout(historyTimer);
      historyTimer = setTimeout(() => { if (saved.origin === location.href) reopen(saved); }, 160);
    }
    syncReturn();
  }
  const restoreHistory = () => {
    const saved = history.state?.peicdResults || (trip?.origin === location.href ? trip : null);
    pendingHistory = saved?.origin === location.href ? { ...saved, viewportY: history.state?.y } : null;
    // Cross-page Back closes search during Material's content swap. Same-page
    // Back has no swap and can restore on the next frame.
    if (mountedPath === location.pathname) restoreMountedPage();
  };
  let traversalURL = "";
  window.navigation?.addEventListener("navigate", event => {
    traversalURL = event.navigationType === "traverse" ? event.destination.url : "";
  });
  window.addEventListener("popstate", event => {
    // Material emits popstate on normal links too. A new visit to a previous
    // result's source hash must remain a reading/navigation action.
    if (!event.isTrusted || (window.navigation && traversalURL !== location.href)) return;
    const toggle = document.getElementById("__search");
    if (toggle?.checked) {
      const destination = location.href, y = history.state?.y;
      toggle.click();
      if (mountedPath === location.pathname && Number.isFinite(y)) requestAnimationFrame(() => {
        if (!toggle.checked && location.href === destination) window.scrollTo({ top: y, behavior: "instant" });
      });
    }
    restoreHistory();
  });
  for (const type of ["pointerdown", "keydown"]) {
    window.addEventListener(type, () => clearTimeout(historyTimer), true);
  }
  window.addEventListener("pageshow", event => { if (event.persisted) restoreHistory(); });
  if (performance.getEntriesByType("navigation")[0]?.type === "back_forward") restoreHistory();
  window.document$?.subscribe(restoreMountedPage);
  syncReturn();
  function update() {
    controls.hidden = !document.getElementById("__search")?.checked;
    const state = api.snapshot(), info = state.info;
    const facets = state.facets || [];
    const key = JSON.stringify(facets);
    if (key !== facetKey) {
      facetKey = key;
      scope.replaceChildren(new Option("全部筆記", ""));
      for (const facet of facets) scope.add(new Option(facet.label, facet.value));
    }
    scope.value = state.view.scope || "";
    scope.disabled = !state.ready;
    current.disabled = !state.ready || !location.pathname.includes("/md/");
    back.hidden = !state.view.page;
    previous.hidden = next.hidden = retry.hidden = true;
    const pending = ["loading", "querying"].includes(state.phase);
    result.setAttribute("aria-busy", String(pending));
    result.style.visibility = pending || state.error ? "hidden" : "";
    if (state.error) { status.textContent = state.error; retry.hidden = false; }
    else if (state.phase === "loading") status.textContent = "首次載入搜尋資料…";
    else if (state.phase === "querying") status.textContent = "搜尋中…";
    else if (!input.value.trim()) status.textContent = "輸入關鍵字，或用 - 排除、OR 擇一。";
    else if (info && state.phase === "results") {
      if (!info.totalPages) status.textContent = "沒有符合的結果。可切換全部筆記，或減少一個關鍵字。";
      else {
        const end = Math.min(info.offset + info.pageSize, info.total || 0);
        status.textContent = info.page
          ? `本篇共有 ${info.total} 個命中章節；顯示第 ${info.total ? info.offset + 1 : 0}–${end} 個。`
          : `找到 ${info.totalPages} 篇筆記；顯示第 ${info.offset + 1}–${end} 篇，每篇先顯示最多 3 個章節。`;
        previous.hidden = info.offset <= 0; next.hidden = !info.more;
      }
      const rows = result.querySelectorAll(".md-search-result__item");
      rows.forEach((row, index) => {
        const group = info.groups?.[index];
        if (!group || info.page || group.sections <= group.shown || row.querySelector(".peicd-search-more")) return;
        const more = button(`查看本篇 ${group.sections} 個命中章節`, () => api.configure({ page: group.page, offset: 0 }));
        more.className = "peicd-search-more";
        more.addEventListener("keydown", event => { if (event.key !== "Escape") event.stopPropagation(); });
        row.appendChild(more);
      });
    } else status.textContent = "輸入文字搜尋全部筆記。";
  }
  window.addEventListener("peicd:search-state", update);
  window.addEventListener("peicd:search-state", finishRestore);
  document.addEventListener("change", event => {
    if (event.target.id !== "__search") return;
    if (!event.target.checked) restoring = null;
    update();
  });
  input.addEventListener("focus", () => queueMicrotask(update));
  update();
})();
