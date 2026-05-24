# ARCHITECTURE

## 專案定位

- 型態：MkDocs Material 筆記網站。
- 主要內容：課程筆記、Verilog 筆記、自訂互動功能、多益600 小工具。
- 執行環境：conda `mkdocs`。

## Source Jump

- 前端：`docs/theme/assets/pymdownx-extras/source-jump.js`
  - 只在 localhost / 127.0.0.1 / ::1 且 `mkdocs serve` livereload 存在時啟用。
  - 右鍵選單只提供「開啟原文檔案」。
  - 查詢時送出選取文字、block 文字、prefix、標題路徑、前後 block、tag、整頁 block index、區段內 block index、整頁進度比例。
- 後端：`tools/source_jump_hook.py`
  - `on_serve` 提供 `__peicd/source-jump` lookup endpoint。
  - `on_files` 先掃描 Markdown 建立 `_PAGE_INDEX`，支援 `serve --dirty` 與單頁 preview。
  - `on_page_markdown` 用實際頁面 Markdown 覆寫索引，提升渲染頁準確度。
  - 比對時綜合文字、標題路徑、前後 block、tag、block order、section order、page progress。
  - 常見渲染標記 `==...==`、`^^...^^` 會在索引階段視為渲染後文字。

## Single Page Preview

- `preview.bat`：正式入口，負責更新 `mkdocs.preview.yml` managed block 並啟動 `python -m mkdocs serve -f mkdocs.preview.yml --dirty`。
- `p.bat`：短命令薄包裝，只轉送參數給 `preview.bat`。
- `tools/update_preview_config.py`：正規化路徑，驗證目標位於 `docs/`，管理 `# preview-target:start` 到 `# preview-target:end`。

## Back To Bottom

- 模板：`docs/theme/partials/scroll-bottom.html`
- 邏輯：`docs/theme/assets/pymdownx-extras/scroll-bottom.js`
- 樣式：`docs/theme/assets/pymdownx-extras/自定義.css`
- 載入位置：`docs/theme/main.html` 的 `scripts` block，位於 `{{ super() }}` 後。
- Material `navigation.instant` 啟用時，要使用 `DOMContentLoaded`、`load` 與 `window.document$.subscribe(...)` 補初始化。

## Folder Path Bar

- 邏輯：`docs/theme/assets/pymdownx-extras/folder-path-bar.js`
- 樣式：`docs/theme/assets/pymdownx-extras/自定義.css`
- 功能：在文章 H1 上方插入檔案總管式路徑列，提供章節與頁面下拉切換。
- 互動：桌機/中版面使用自製 dropdown；開啟頁面 dropdown 時會把目前頁 `.peicd-folder-pathbar__option--current` 捲入可視範圍。窄版使用 native select。

## Dark Theme

- `docs/theme/assets/pymdownx-extras/自定義.css` 在 `slate` 與 `dracula` 主題下覆寫 Material 背景變數。
- 深色主背景為 `#000000`；header/tabs 使用 `rgba(0, 0, 0, 0.98)`；Mermaid 圖卡與右側 TOC 使用黑底漸層保留層次。
- `mkdocs.yml` 的 `自定義.css` 帶版本參數，修改深色背景後要更新版本避免舊快取。

## Mermaid Rendering

- Mermaid 由 `mkdocs.yml` 載入 `mermaid@10.6.1`、`mermaid-config-override.js`、`mermaid-render-fix.js` 與 `mermaid-zoom.js`。
- `mermaid-config-override.js` 強制 flowchart 使用 `htmlLabels`，讓節點內 `<br>` 正常換行；暗色主題會合併高對比 flowchart themeVariables/themeCSS。
- `mermaid-render-fix.js` 負責把 `pre.diagram` 渲染成 `.peicd-mermaid-host`，支援主題切換與 Material instant navigation，並在渲染後把 htmlLabels 的 `foreignObject` 高度加大 5px，避免 descender 被裁切。
- `docs/theme/assets/pymdownx-extras/自定義.css` 控制 `.peicd-mermaid-host` 圖卡外觀、htmlLabels 行高與暗色主題 SVG 保底樣式；行高不可大於 Mermaid 的 `foreignObject` 量測高度，且 `foreignObject` 需要允許 visible overflow，否則英文字母 descender 會被裁切。

## 多益600 小專案

- 位於 `docs/md/多益600/`。
- Git 保留站點內容、圖片、includes、`紀錄.py`、工具 README 與轉換規則。
- 生成影音、TTS cache、暫存與本機測試輸出由 `.gitignore` 與 `mkdocs.yml exclude_docs` 排除。
