/* Controls and status around Material's sole result renderer. No saved query history. */
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
    else if (!input.value.trim()) status.textContent = "可輸入中文片段或程式碼；空格表示同時符合所有詞。";
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
  result.addEventListener("click", event => {
    const link = event.target.closest("a[href]");
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const url = new URL(link.href, location.href);
    window.__PEICD_SEARCH_TARGET__ = { path: url.pathname, hash: url.hash, query: input.value };
  }, true);
  window.addEventListener("peicd:search-state", update);
  document.addEventListener("change", event => { if (event.target.id === "__search") update(); });
  input.addEventListener("focus", () => queueMicrotask(update));
  update();
})();
