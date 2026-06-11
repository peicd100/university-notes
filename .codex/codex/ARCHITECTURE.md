# ARCHITECTURE

## Slash admonition 與 plain details block

- `tools/admonition_title_hook.py` 在 MkDocs `on_page_markdown` 階段處理 admonition 標題：
  - 一般 `!!! type "title"` 會正規化成 `Type | title`。
  - slash shorthand 支援 `/// type "title"` 與 `/// type|title` / `/// type | title`。
  - slash shorthand 只處理 `_TYPE_LABELS` 內的 admonition 類型，因此 `/// details|title` 仍交給 `pymdownx.blocks.details`。
- `tools/source_jump_hook.py` 需要和上述語法同步解析 `quoted_title` 與 `pipe_title`，才能讓渲染後的 `Danger | title` 仍定位回原 Markdown 的 `/// danger|title` 起始行。
- `theme/assets/pymdownx-extras/自定義.css` 只針對暗色模式的 `.md-typeset details:not([class])` 補 plain details 樣式：
  - 背景使用 `#050505` / `#0b0d10` 近黑純色。
  - 左側與外框使用 cyan 細線。
  - `summary` 使用精簡標題列、箭頭 pseudo-element、右側細分隔線。
  - 內文維持正文尺寸，只調整摺疊框內距與段落間距。

## 專案定位

- 型態：MkDocs Material 筆記網站。
- 主要內容：課程筆記、Verilog 筆記、自訂互動功能、多益600 小工具。
- 執行環境：conda `mkdocs`。

## MkDocs 設定分層

- `mkdocs.yml`：根目錄主要設定檔，保留 theme、plugins、hooks、Markdown extensions、extra CSS/JS 等技術設定。
- `docs/.mkdocs/site.yml`：由 `mkdocs.yml` 的 `INHERIT` 繼承，存放 `site_name`、`site_url`、`use_directory_urls`、`exclude_docs`、`not_in_nav` 與 `nav`。
- `theme/`：自訂 Material theme 覆蓋與前端資產，透過 `theme.custom_dir: theme` 載入；不放在 `docs/` 內，避免與筆記內容混在一起。

## Source Jump

- 前端：`theme/assets/pymdownx-extras/source-jump.js`
  - 只在 localhost / 127.0.0.1 / ::1 且 `mkdocs serve` livereload 存在時啟用。
  - 右鍵選單只提供「開啟原文檔案」。
  - 查詢時送出選取文字、block 文字、prefix、標題路徑、前後 block、tag、整頁 block index、區段內 block index、整頁進度比例。
- 後端：`tools/source_jump_hook.py`
  - `on_serve` 提供 `__peicd/source-jump` lookup endpoint。
  - `on_files` 先掃描 Markdown 建立 `_PAGE_INDEX`，支援 `serve --dirty` 與單頁 preview。
  - `on_page_markdown` 仍會在頁面流程中重建索引，但優先讀回原始 Markdown 檔，避免已轉換的頁面 Markdown 污染原始檔行號。
  - Python-Markdown admonition `!!!` / `???` 不是 CommonMark 原生區塊；後端會額外建立 synthetic blocks，把 admonition 標題與縮排內文解析成渲染後文字，再映射回原始 Markdown 行。
  - 比對時綜合文字、標題路徑、前後 block、tag、block order、section order、page progress。
  - container-only lookup 對「短文字被長 container 包含」會依覆蓋比例降權，避免表格 cell `3` 之類短內容誤搶長標題定位。
  - 常見渲染標記 `==...==`、`^^...^^` 會在索引階段視為渲染後文字。

## Single Page Preview

- `p.exe`：cmd preview 主入口。由 `tools/p.py` 產生，輸入 `p <Markdown path>` 時會因 PATHEXT 的 `.EXE` 優先於 `.BAT` 而避開 batch context，避免 Ctrl+C 出現「要終止批次工作嗎 (Y/N)」。
- `tools/p.py`：自包含 launcher；先用目前 Python 呼叫 `tools/update_preview_config.py` 更新 `mkdocs.preview.yml` managed block，再啟動 `python -m mkdocs serve -f <root>/mkdocs.preview.yml --dirty`，並捕捉 Ctrl+C 等 MkDocs 正常關閉。
- `p.bat` / `preview.bat`：舊 fallback。不要再把它們當作 Ctrl+C 無詢問的主要解法，因為 cmd 只要仍在 batch context 中被 Ctrl+C 打斷，就可能詢問是否終止批次工作。
- `tools/update_preview_config.py`：正規化路徑，驗證目標位於 `docs/`，管理 `# preview-target:start` 到 `# preview-target:end`。

## Back To Bottom

- 模板：`theme/partials/scroll-bottom.html`
- 邏輯：`theme/assets/pymdownx-extras/scroll-bottom.js`
- 樣式：`theme/assets/pymdownx-extras/自定義.css`
- 載入位置：`theme/main.html` 的 `scripts` block，位於 `{{ super() }}` 後。
- Material `navigation.instant` 啟用時，要使用 `DOMContentLoaded`、`load` 與 `window.document$.subscribe(...)` 補初始化。

## Right TOC 與 Danger TOC

- 一般右側 TOC 邏輯在 `theme/assets/pymdownx-extras/toc-fold.js`，樣式在 `theme/assets/pymdownx-extras/自定義.css`。
- TOC 工具列提供「展開 / 收合 / 自動 / 手動 / Danger」；前四者控制一般 TOC 模式，`Danger` 進入並保持 Danger Block 目錄，重複按不回一般 TOC。
- Danger 目錄在前端從 `.md-content__inner.md-typeset` 內掃描 `.admonition.danger` 與 `details.danger` 產生，不依賴 Source Jump endpoint，因此 build 後靜態頁也可使用。
- Danger 項目標題優先取 `.admonition-title` / `summary` 去掉 `Danger |` 前綴後的自訂標題；若沒有自訂標題，先取 block 內標題，再依渲染後畫面位置比較前後 `h1-h6`，距離相同取前方標題。
- Danger 項目點擊會攔截同頁 hash link，自行 `history.pushState` 與 `scrollTo`，避免 Material instant navigation 重新初始化後把視圖重設為一般 TOC。
- 若頁面載入或重新初始化時網址 hash 指向 `#peicd-danger-block-*`，TOC 初始化應直接維持 Danger 視圖。
- `mkdocs.yml` 的 `toc-fold.js` 與 `自定義.css` 使用版本參數；修改 TOC 行為或樣式後需同步 bump，避免手機或瀏覽器快取吃舊檔。

## Admonition 標題

- `tools/admonition_title_hook.py` 在 `on_page_markdown` 階段補強 `!!! type "自訂標題"` 的標題文字，並跳過 fenced code block 內的教學範例。
- 若自訂標題尚未包含類型名稱，輸出會保留預設類型前綴與分隔線，例如 `!!! danger "記下來"` 渲染為 `Danger | 記下來`；未自訂標題的 `!!! danger` 維持 `Danger`，避免重複成 `Danger Danger`。
- 此 hook 只改渲染流程中的 Markdown 字串，不改 Markdown 原文；優先順序排在 Source Jump 索引之後，避免干擾原文定位。

## Folder Path Bar

- 邏輯：`theme/assets/pymdownx-extras/folder-path-bar.js`
- 樣式：`theme/assets/pymdownx-extras/自定義.css`
- 功能：在文章 H1 上方插入檔案總管式路徑列，提供章節與頁面下拉切換。
- 互動：桌機/中版面使用自製 dropdown；開啟頁面 dropdown 時會把目前頁 `.peicd-folder-pathbar__option--current` 捲入可視範圍。窄版使用 native select。

## Dark Theme

- `theme/assets/pymdownx-extras/自定義.css` 在 `slate` 與 `dracula` 主題下覆寫 Material 背景變數。
- 深色主背景為 `#000000`；header/tabs 使用 `rgba(0, 0, 0, 0.98)`；Mermaid 圖卡與右側 TOC 使用黑底漸層保留層次。
- `mkdocs.yml` 的 `自定義.css` 帶版本參數，修改深色背景後要更新版本避免舊快取。

## Mermaid Rendering

- Mermaid 由 `mkdocs.yml` 載入 `mermaid@10.6.1`、`mermaid-config-override.js`、`mermaid-render-fix.js` 與 `mermaid-zoom.js`。
- `mermaid-config-override.js` 強制 flowchart 使用 `htmlLabels`，讓節點內 `<br>` 正常換行；暗色主題會合併高對比 flowchart themeVariables/themeCSS。
- `mermaid-render-fix.js` 負責把 `pre.diagram` 渲染成 `.peicd-mermaid-host`，支援主題切換與 Material instant navigation，並在渲染後把 htmlLabels 的 `foreignObject` 高度加大 5px，避免 descender 被裁切。
- `theme/assets/pymdownx-extras/自定義.css` 控制 `.peicd-mermaid-host` 圖卡外觀、htmlLabels 行高與暗色主題 SVG 保底樣式；行高不可大於 Mermaid 的 `foreignObject` 量測高度，且 `foreignObject` 需要允許 visible overflow，否則英文字母 descender 會被裁切。

## 多益600 小專案

- 位於 `docs/md/多益600/`。
- Git 保留站點內容、圖片、includes、`紀錄.py`、工具 README 與轉換規則。
- 生成影音、TTS cache、暫存與本機測試輸出由 `.gitignore` 與 `mkdocs.yml exclude_docs` 排除。

## Slash admonition shorthand

- `tools/admonition_title_hook.py` 會在 `on_page_markdown` 階段把已知 admonition 類型的 `/// type "title"` block 轉成 Python-Markdown admonition：`!!! type "Type | title"`，並把未縮排內文加上 4 空格縮排。
- 此語法只支援 `_TYPE_LABELS` 中的 admonition 類型，避免誤吃 `/// collapse-code` 等既有 pymdownx block。
- `tools/source_jump_hook.py` 會直接從原始 `/// ... ///` span 建立 synthetic admonition title/content blocks，並過濾完整落在該 span 內的原始 CommonMark block，讓「開啟原文檔案」定位到原始 `/// danger` 標題行或未縮排內容行。
- 未閉合的 `/// danger` 不會被轉換，讓錯誤語法保留在輸出中，方便作者發現。
