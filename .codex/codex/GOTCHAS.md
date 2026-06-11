# GOTCHAS

## Source Jump 不可只靠頁面文字首次命中

- 狀態：active
- 證據：observed
- 日期：2026-05-18
- 影響範圍：`tools/source_jump_hook.py`、`theme/assets/pymdownx-extras/source-jump.js`
- 正確做法：文字比對要搭配標題路徑、前後 block、tag、block index、section index、page progress。
- 不要做：不要只用 `record.markdown.find(selection)`、第一個 container 命中位置，或過短 substring 當結果。
- 驗證方式：用重複短句、`==...==` 標記、同頁不同章節與長標題旁的短表格 cell 測試右鍵定位。

## Source Jump 的 serve 階段索引必須回讀原始 Markdown

- 狀態：active
- 證據：verified
- 日期：2026-06-10
- 影響範圍：`tools/source_jump_hook.py`
- 正確做法：`on_page_markdown` 可保留為 serve/dirty preview 的重建索引時機，但索引內容要優先讀回 `page.file.abs_src_path` 的原始 Markdown，讓 offset 與 VS Code 開檔行號一致。
- 不要做：不要直接用已經被頁面流程或其他 hook 改寫中的 `markdown` 參數覆寫 `_PAGE_INDEX`；它可能讓 `!!! danger` 內部標題回到 admonition 起始行。
- 驗證方式：`mkdocs serve` 後對 `/university-notes/md/114-2/科技_計算機結構/期末考複習-ch3.html` 的 h3 `3. mflo 和 mfhi：怎麼把答案拿回一般 register？` 做空 selection 與 `mflo` selection lookup，兩者都應回第 1631 行。

## Source Jump 需額外索引 Python-Markdown admonition

- 狀態：active
- 證據：verified
- 日期：2026-06-10
- 影響範圍：`tools/source_jump_hook.py`
- 正確做法：對 `!!!` / `???` admonition 建立 synthetic blocks，將縮排內文去縮排後用 MarkdownIt 解析，再把 synthetic offset 映射回原始 Markdown offset；標題列 `Danger` / `Danger 記下來` 映射到 admonition 起始行。
- 不要做：不要只靠 CommonMark token；它會把 admonition 內文當 indented code block，導致渲染後標題、表格與段落無法準確定位。
- 驗證方式：用 `!!! danger` 內的 h3、段落、表格 cell 與 code block 做 source jump；內文應回各自原始行，只有 admonition 標題列回 `!!! danger` 行。

## Source Jump 開檔與右鍵選單行為

- 狀態：active
- 證據：verified
- 日期：2026-05-23
- 影響範圍：`tools/source_jump_hook.py`、`theme/assets/pymdownx-extras/source-jump.js`
- 正確做法：開 VS Code 時要等待 CLI 回傳並檢查 exit code；前端成功或失敗都要顯示狀態。右鍵選單只顯示「開啟原文檔案」。
- 不要做：不要只用 `subprocess.Popen(...)` 成功建立子程序就回報 `opened: true`；不要加回「複製」按鈕或 clipboard fallback。
- 驗證方式：preview server 右鍵段落並點「開啟原文檔案」，確認按鈕先顯示「開啟中...」，HTTP 回傳含 `opened: true`；`#peicd-source-jump-menu` 應只有 `data-role="jump"` 一顆按鈕。

## MkDocs Preview 需支援 serve --dirty

- 狀態：active
- 證據：verified
- 日期：2026-05-18
- 影響範圍：`tools/source_jump_hook.py`
- 正確做法：保留 `on_files` 預索引，再由 `on_page_markdown` 以原始 Markdown 內容重建索引。
- 不要做：不要移除 `on_files` 後只依賴 `on_page_markdown`。
- 驗證方式：`mkdocs serve -f mkdocs.preview.yml --dirty` 下右鍵 lookup 能找到目前 preview 頁。

## Instant Navigation 前端綁定

- 狀態：active
- 證據：verified
- 日期：2026-05-18
- 影響範圍：所有依賴頁面 DOM 的自訂 JS。
- 正確做法：支援 `DOMContentLoaded` 與 `window.document$.subscribe(...)`。
- 不要做：不要只在 JS 初次載入時綁定一次頁面 DOM。
- 驗證方式：從首頁 instant navigation 到目標頁後，功能仍可操作。

## Danger TOC 需避開 Material 同頁 hash 重初始化

- 狀態：active
- 證據：verified
- 日期：2026-06-11
- 影響範圍：`theme/assets/pymdownx-extras/toc-fold.js`、右側 TOC / Danger 目錄。
- 正確做法：Danger 目錄連結需 `preventDefault()` 後自行 `history.pushState` 與 `scrollTo`，並在 Danger 視圖內同步目前項目；正文容器要分段優先找 `.md-content__inner.md-typeset`，不可用單一 selector list 的第一個 `.md-typeset`。
- 不要做：不要讓 Danger 連結走預設同頁 hash link；Material instant navigation 可能觸發 `document$` 重新初始化，把 Danger 視圖重設為一般 TOC。也不要假設 `[data-md-component="toc"]` 一定是 nav，它在目前頁面可直接是 `ul.md-nav__list`。
- 驗證方式：在 `期末考複習-ch4.2.html` 按 Danger 後點 `#peicd-danger-block-7`，URL hash 應停在該 block、Danger 視圖不消失、目前項目顯示「現在在這裡」；一般 TOC link 應不可見。

## UI 深色主題與版面壓縮索引

- 狀態：active
- 證據：verified
- 日期：2026-06-10
- 影響範圍：`theme/assets/pymdownx-extras/自定義.css`、Material sidebar / TOC / blog / article image / heading permalink。
- 正確做法：深色主背景維持純黑或近黑；drawer、右側 TOC、blog excerpt、路徑列與小工具都要同步覆寫多層容器。中版面 drawer 收起時不可投影壓暗正文；標題錨點要跟第一行同列；文章圖片寬度限制不可套到放大檢視。
- 不要做：不要回到藍灰玻璃底、radial/linear 大面積 glow、可換行 flex 標題錨點、或把全站正文改成 CJK fallback。
- 驗證方式：依 `VERIFY.md` 的前端互動清單驗證 drawer、TOC、blog、標題錨點、圖片、`==mark==`、`collapse-code` 與 dark theme。壓縮前全文封存在 `.codex/codex/archive/gotchas-2026-06-10-before-source-jump-admonition-compress.md`。

## Details summary pseudo-element 需重置 Material 定位

- 狀態：active
- 證據：verified
- 日期：2026-06-10
- 影響範圍：`theme/assets/pymdownx-extras/自定義.css` 的 `.md-typeset details:not([class]) > summary::before`。
- 正確做法：自訂 details 箭頭若使用 `summary::before`，必須重置 Material 既有 pseudo-element 定位與遮罩，例如 `position: static`、`inset: auto`、`mask: none`，並作為 flex item 佔位。
- 不要做：不要只改 `display`、`width`、`gap`；若保留既有 `position:absolute`，箭頭會蓋到標題文字。
- 驗證方式：Playwright 量測 `summary::before` computed `position` 為 `static`、`mask` 為 `none`，且文字 `Range.getClientRects()[0].left` 不小於預期箭頭右側。

## Mermaid Rendering 高風險索引

- 狀態：active
- 證據：verified
- 日期：2026-06-10
- 影響範圍：`theme/assets/pymdownx-extras/mermaid-config-override.js`、`theme/assets/pymdownx-extras/mermaid-render-fix.js`、`theme/assets/pymdownx-extras/自定義.css`
- 正確做法：Mermaid htmlLabels 的 `foreignObject` 渲染後需額外增高並允許 visible overflow；暗色主題同時改 themeVariables/themeCSS 與外層 CSS 保底。
- 不要做：不要只靠降低 line-height；不要只改 `.nodeLabel` 而漏 edge label、SVG text、flowchart link 或放大檢視。
- 驗證方式：`ch 6.md` 的 RM 關係圖檢查 `Higher priority` / `Lower priority` 的 `y` 下緣；`ch 7.md` deadlock flowchart 檢查 dark node label、fill、stroke、edge label 與 console。

## .codex/ Git 忽略策略

- 狀態：active
- 證據：observed
- 日期：2026-05-22
- 影響範圍：`.codex/`、`.gitignore`
- 正確做法：保留舊 `/codex/` 忽略規則作相容；`.codex/` 只忽略 `tmp/`、`private/`、`artifacts/`、`codex_tmp/` 與 `codex_compressed/`，不可忽略 `.codex/AGENTS.md` 與 `.codex/codex/` 核心文件。
- 不要做：不要把整個 `.codex/` 加進 `.gitignore`。
- 驗證方式：`git check-ignore -v .codex/codex/00_START_HERE.md` 不應命中；`.codex/codex/tmp/` 應被忽略。
