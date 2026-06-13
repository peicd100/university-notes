# VERIFY

## Asset conditional loading

Recommended checks after editing loading hooks/scripts:

```bat
node --check theme\assets\pymdownx-extras\conditional-loader.js
node --check theme\assets\pymdownx-extras\search-lazy-guard.js
node --check theme\assets\pymdownx-extras\mathjax-refresh.js
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\image_lazy_loading_hook.py
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name asset-conditional-search-lazy-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
```

Browser checks:
- Initial `ch 3.html#311-行程process`: no `search_index`, no `workers/search`, no `tex-mml-chtml`, no `mermaid.min.js`; Mermaid hosts exist but rendered count starts at 0.
- Open/fill search: `search_index` and `workers/search` load, and results are shown.
- Scroll all Mermaid blocks: 18/18 render with no errors.
- Math page with `.arithmatex`: MathJax CDN loads and `mjx-container` appears.
- OS `ch 1.html`: no `data:image`, 48 externalized images, image viewer still opens.

## Slash admonition 與 details block

最小驗證命令：

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\admonition_title_hook.py tools\source_jump_hook.py
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name details-pipe-admonition-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
```

行為檢查：
- `/// danger|重點`、`/// danger | 重點`、`/// danger "重點"` 都應重寫成 `!!! danger "Danger | 重點"`。
- `/// danger|Danger | 重點` 不應變成 `Danger | Danger | 重點`。
- `/// details|摺疊` 不應被 `admonition_title_hook.py` 改寫，應由 `pymdownx.blocks.details` 輸出 `<details><summary>摺疊</summary>...`。
- Source Jump synthetic block 應把 `Danger | 重點` 對回 `/// danger|重點` 起始行，內容對回 body 行。
- `site/assets/pymdownx-extras/自定義.css` 應包含 `.md-typeset details:not([class])` 暗色樣式，`mkdocs.yml` 的 CSS query version 應同步 bump 避免快取。
- details summary 箭頭應是 `position: static` 的 flex item，且文字起點不可與箭頭重疊。

視覺檢查：
- 使用 Playwright CLI 開啟已建置站點，截 `details` 元素關閉與展開狀態。
- 參考產物：`.codex/codex/artifacts/details-style-playwright.png`、`.codex/codex/artifacts/details-style-playwright-open.png`、`.codex/codex/artifacts/details-summary-after.png`。

## Preview Ctrl+C

最小驗證：

```bat
Y:\conda\envs\mkdocs_desk\python.exe -m py_compile tools\p.py
cmd /d /c "pushd <repo> && p /? && set PREVIEW_SKIP_SERVE=1&& p docs\md\114-2\科技_計算機結構\期末考複習-ch5.md && popd"
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name preview-absolute-config-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

手動驗證：
- 在 cmd 啟動 `p docs\md\114-2\科技_計算機結構\期末考複習-ch4.2.md`；`p /?` 應顯示 `Usage: p ...`，表示跑到 `p.exe` 而不是 batch fallback。
- 等 `mkdocs serve` 開始後按 Ctrl+C，應直接返回命令提示字元，不應顯示「要終止批次工作嗎 (Y/N)」。
- 不要用 `p.bat` 或 `preview.bat` 驗證 Ctrl+C；長時間 `.bat` 在 cmd 中被 Ctrl+C 打斷時仍可能觸發 Y/N 詢問。

## Source Jump

最小驗證：

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\admonition_title_hook.py
node --check theme\assets\pymdownx-extras\source-jump.js
Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

手動驗證：

- 啟動 `p docs\md\114-2\電機_作業系統\ch 6.md`。
- 在 preview 頁右鍵一般段落、`==...==` 高亮段落、code block、重複短句。
- 在 `docs/md/114-2/科技_計算機結構/期末考複習-ch3.md` 的 `!!! danger` 區塊內右鍵 `3. mflo 和 mfhi：怎麼把答案拿回一般 register？`，應定位到原文第 1631 行；選字 `mflo` 也應回第 1631 行，不可跳到第 1629 行的 `!!! danger`。
- 確認 VS Code 開到同一 Markdown 的正確行附近。
- 右鍵選單應只顯示「開啟原文檔案」，不應再出現「複製」。

## 前端互動

- 使用瀏覽器確認選字右鍵與未選字右鍵都可顯示選單。
- 若修改 Mermaid 動態載入，開啟 `site/md/114-2/電機_作業系統/ch 3.html#311-行程process`：初始 `DOMContentLoaded` 目標約 3s 級距，`performance.getEntriesByType("resource")` 不應含 `mermaid.min.js`，`.peicd-mermaid-host` 應有 18 個且初始 rendered 為 0。捲到第一個 `.peicd-mermaid-host` 後才應載入 Mermaid runtime 並渲染附近圖表；逐段捲完整頁後 18 張都應 `.is-rendered`，`pre.diagram` 不應可見。
- 若修改文章圖片 lazy loading，build 後檢查 `ch 3.html`：文章第一張圖應有 `decoding="async"` 且不含 `loading="lazy"`，其餘文章圖應同時有 `loading="lazy"` 與 `decoding="async"`；logo/twemoji 不應被改動。
- 若涉及 Material instant navigation，從其他頁切到目標頁後再測一次。
- 若修改右側 TOC / Danger 目錄，開啟含多個 Danger block 的頁面如 `site/md/114-2/科技_計算機結構/期末考複習-ch4.2.html`：按 `Danger` 後應只顯示 Danger 項目，一般 TOC 連結不可同時可見；目前項目應顯示「現在在這裡」；點擊項目應跳到 `#peicd-danger-block-*` 且停留在 Danger 視圖；重複按 `Danger` 與帶 Danger hash 重新載入都應維持 Danger 視圖；按「自動」應回到一般 TOC。工具列中 `Danger` 文字不可被裁切，其他按鈕可比 Danger 更窄。再開啟無 Danger block 但有標題的頁面如 `site/md/Verilog/首頁.html`，應顯示「此筆記沒有任何 Danger Block」。
- 若修改 Mermaid 樣式，至少開啟 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係圖，確認 `Priority-based Preemptive Scheduling`、`Shorter period`、`Higher priority` 等英文字下緣沒有被裁切。
- Mermaid htmlLabels 可用瀏覽器量測：目標圖表每個 `g.node foreignObject` 都應帶 `data-peicd-descender-pad="true"`；單行 label 高度應從原始 19px 增到約 24px，且 `Higher priority`、`Lower priority` 最後的 `y` 必須可見。
- 若修改 Mermaid 暗色對比，開啟 `docs/md/114-2/電機_作業系統/ch 7.md` 的 deadlock flowchart；`dracula` 主題下 node label 應接近白色、node fill 應為深紫、node stroke 應為 `#72e3fd`，edge label 應為深底白字，console error/warn 應為空。
- 若修改深色背景，量測 `ch 7.html`：body/container/main/content 應為 `rgb(0, 0, 0)`，header/tabs 應為 `rgba(0, 0, 0, 0.98)`；Mermaid 圖卡可用黑底層級，右側 TOC 依下列 TOC 黑底條目驗證，console error/warn 應為空。
- 若修改中/窄版側邊欄 drawer 背景，開啟 `ch 8.html` 並用約 1212px 寬度打開左側 drawer；`.md-sidebar--primary`、`.md-sidebar__scrollwrap`、`.md-nav`、`.md-nav__list` 應為 `rgb(0, 0, 0)`，`.md-overlay` 應為黑色半透明，console error/warn 應為空。
- 若修改右側 TOC 深色背景，開啟 `ch 8.html` 並用約 1212px 寬度測試；右側 TOC inner/scrollwrap/head/control/一般章節 link 應為 `rgb(0, 0, 0)`，目前項目可為 `rgb(5, 5, 5)` 與細 cyan 內框，console error/warn 應為空。
- 若修改首頁 blog 方塊，開啟 `blog/index.html`；桌機寬度量測 `article.md-post--excerpt` 應為 `rgb(0, 0, 0)` 且 `background-image:none`，標題清楚；390px 窄版不應水平 overflow，標題寬度需小於卡片寬度，console error/warn 應為空。
- 若修改 Markdown `---` 分隔線，量測 `.md-typeset hr`：亮色與暗色都應是較長 1px 細線 + 置中約 2px 粗線、可見高度約 5px；目前目標 `background-size` 為 `88% 1px, 70% 2px`。不可回到整條同樣粗度或過亮雷射感，暗色主線維持柔和 cyan，亮色主線需比一般灰線更明顯。
- 若修改 `==mark==` 高亮，開啟 `docs/md/114-2/科技_計算機結構/期末考複習-ch3.md` 的 `clock edge 到來時` 表格列；暗色模式下高亮應是連續淡金螢光筆層、文字清楚，`mark` 內 inline code 不應變成分段厚膠囊，console error/warn 應為空。
- 若修改標題錨點樣式，開啟 `ch 7.html` 的 `⭐Resource-Allocation Graph Algorithm` h2，量測 `.headerlink` 與標題文字第一行應維持同一行，且長標題不應讓 `#` 獨立換到上一行。
- 若修改中版面左側導覽或路徑列，開啟 `ch 1.html` 並用約 1212px 寬度測試：目前頁的 `label.md-nav__link[for="__toc"]` 應為 `display:none`、左側目前頁只剩一個可見連結；深色路徑列的目前資料夾與頁面文字需有清楚對比。再用約 766px 寬度確認窄版 select 文字同樣清楚。若修改頁面 dropdown，打開 `ch 8.html` 的頁面選單時目前 `Ch 8` 應在選單可視範圍內。
- 若修改路徑列頁面清單，開啟手機寬度的 `site/md/114-2/電機_作業系統/期末考重點-ch9.html`：第二個 native select 應選中 `期末考整理 / 期末考重點 ch9`，選項中應包含 `期末考整理 / 期末考重點 ch6` 到 `ch9` 與 `期末考整理 / 期末考所有重點`。打開搜尋後 `.peicd-folder-pathbar` 應為 `display:none`，搜尋結果列表不可被路徑列擋住。
- 若修改 TTS 面板，開啟 header 喇叭按鈕，確認深色面板使用黑底薄線、slider 與選取狀態使用 cyan、控制文字不擠壓，且 console error/warn 為空。
- 若修改文章圖片尺寸，桌機量測 `.md-content__inner.md-typeset img:not(.twemoji)` 最大寬度比例應不超過 0.7；手機或窄螢幕應可回到 1.0；全螢幕 image viewer 不應被 70% 規則限制。
- 若修改 `collapse-code` 樣式，開啟有 `/// collapse-code` 的頁面，收合狀態展開按鈕應約 1.45rem、不是大色塊；展開後 `.code-footer` 不應覆蓋最後幾行程式碼，且 footer 背景應與 code block 背景一致、不可留下突兀黑色底條，console error/warn 應為空。
- 若修改 admonition 標題處理，驗證 `!!! danger "記下來"` 會輸出 `Danger | 記下來`，且 `!!! danger` 仍只輸出 `Danger`，不可重複成 `Danger Danger` 或 `Danger | Danger`。
- 若修改 admonition / `!!! danger` 樣式，開啟 `docs/md/114-2/科技_計算機結構/期末考複習-ch4-1.md`，量測 `PC+4` 所在 danger 內文與一般正文應同為約 16px；`.admonition-title` 可較小，約 14.08px。

## 輸出管理

若需要保留驗證輸出，使用：

```bat
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name <name> -- <command...>
```

輸出應落在 `.codex/codex/tmp/`。

## Slash admonition

最小驗證：

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\admonition_title_hook.py tools\source_jump_hook.py
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name slash-admonition-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
```

行為檢查：
- `/// danger "重點"`、未縮排內文、結尾 `///` 會在渲染前轉為 `!!! danger "Danger | 重點"` 與 4 空格縮排內文。
- `/// danger` 沒有自訂標題時渲染為預設 `Danger`。
- `/// collapse-code` 不能被轉成 admonition。
- fenced code block 裡的 `/// danger "重點"` 不能被改寫。
- Source Jump synthetic block 要能把 `Danger | 重點` 定位到 `/// danger "重點"` 原始行，把內文與 heading 定位到未縮排的原始內容行。
