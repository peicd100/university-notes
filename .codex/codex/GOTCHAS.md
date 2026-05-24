# GOTCHAS

## Source Jump 不可只靠頁面文字首次命中

- 狀態：active
- 證據：observed
- 日期：2026-05-18
- 影響範圍：`tools/source_jump_hook.py`、`docs/theme/assets/pymdownx-extras/source-jump.js`
- 正確做法：文字比對要搭配標題路徑、前後 block、tag、block index、section index、page progress。
- 不要做：不要只用 `record.markdown.find(selection)` 或第一個 container 命中位置當結果。
- 驗證方式：用重複短句、`==...==` 標記與同頁不同章節測試右鍵定位。

## Source Jump 開檔不可只看子程序送出

- 狀態：active
- 證據：verified
- 日期：2026-05-23
- 影響範圍：`tools/source_jump_hook.py`、`docs/theme/assets/pymdownx-extras/source-jump.js`
- 正確做法：開 VS Code 時要等待 CLI 回傳並檢查 exit code；前端成功或失敗都要顯示狀態，避免使用者以為按鈕沒反應。
- 不要做：不要只用 `subprocess.Popen(...)` 成功建立子程序就回報 `opened: true`，也不要成功後立刻無聲關閉選單。
- 驗證方式：用 preview server 右鍵段落並點「開啟原文檔案」，確認按鈕先顯示「開啟中...」，HTTP 回傳含 `opened: true` 與成功訊息；VS Code CLI 失敗時應顯示錯誤。

## Source Jump 右鍵選單只保留開檔

- 狀態：active
- 證據：user-requested
- 日期：2026-05-23
- 影響範圍：`docs/theme/assets/pymdownx-extras/source-jump.js`。
- 正確做法：右鍵選單只顯示「開啟原文檔案」，讓操作目的單一明確。
- 不要做：不要再加回「複製」按鈕或 clipboard fallback；一般複製可用瀏覽器/系統既有操作。
- 驗證方式：`mkdocs serve` 預覽頁右鍵段落後，`#peicd-source-jump-menu` 應只有一顆 `data-role="jump"` 按鈕，且文字為「開啟原文檔案」。

## MkDocs Preview 需支援 serve --dirty

- 狀態：active
- 證據：verified
- 日期：2026-05-18
- 影響範圍：`tools/source_jump_hook.py`
- 正確做法：保留 `on_files` 預索引，再由 `on_page_markdown` 覆寫精修。
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

## Mermaid htmlLabels 字母下緣裁切

- 狀態：active
- 證據：verified
- 日期：2026-05-22
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、Mermaid flowchart htmlLabels。
- 正確做法：Mermaid htmlLabels 的 `foreignObject > div` 行高必須貼近 Mermaid 量測高度；同時 `mermaid-render-fix.js` 必須在渲染後把 `g.label > foreignObject` 高度額外加 5px，並把 `foreignObject` overflow 設成 visible。只檢查 `divHeight <= foreignObject height` 不夠，因為字型實際墨跡可能仍貼到底部。
- 不要做：不要只靠降低 line-height，也不要把 Mermaid htmlLabels 行高調到 `1.4` 或套用全站較大的 line-height；Mermaid 產生的單行 `foreignObject` 原始高度約 19px，`y` 的 descender 容易在最下方被切成像 `v`。
- 驗證方式：開啟 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係 Mermaid 圖，確認 `Higher priority`、`Lower priority` 最後的 `y` 下緣完整；瀏覽器量測單行 label `foreignObject` 應從 19px 增為 24px，且 console error/warn 為空。

## Mermaid 深色主題文字對比

- 狀態：active
- 證據：verified
- 日期：2026-05-23
- 影響範圍：`docs/theme/assets/pymdownx-extras/mermaid-config-override.js`、`docs/theme/assets/pymdownx-extras/自定義.css`、Mermaid flowchart 暗色主題。
- 正確做法：暗色主題的 Mermaid flowchart 要同時改 themeVariables/themeCSS 與外層 CSS 保底；節點文字使用接近白色，節點底色加深，邊框使用 `#72e3fd`，edge label 使用深底白字。
- 不要做：不要維持紫底配紫字，也不要只改 `.nodeLabel`；edge label、SVG text、flowchart link 與放大檢視也要同步處理。
- 驗證方式：開啟 `docs/md/114-2/電機_作業系統/ch 7.md` 的 deadlock Mermaid 圖；`dracula` 主題下 node label 應為 `rgb(248, 251, 255)`、node fill 應為 `rgb(49, 40, 77)`、edge label 背景應為 `rgb(20, 27, 42)`，且 console error/warn 為空。

## 標題錨點不可用可換行 flex

- 狀態：active
- 證據：verified
- 日期：2026-05-24
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、MkDocs Material heading permalink。
- 正確做法：h2~h6 保持一般 block 排版並預留左側錨點空間，`.headerlink` 用 absolute 定位在標題第一行開頭，讓長標題文字自己換行。
- 不要做：不要把 h2~h6 設為 `display:flex` 且 `flex-wrap:wrap`；長標題會把 `.headerlink` 當成獨立 flex item 擠到上一行。
- 驗證方式：開啟 `docs/md/114-2/電機_作業系統/ch 7.md` 的 `⭐Resource-Allocation Graph Algorithm` h2，量測 `.headerlink` 與標題文字第一行應為同一行，console error/warn 為空。

## 中版面左側目前頁不可同時顯示 TOC label 與頁面連結

- 狀態：active
- 證據：verified
- 日期：2026-05-24
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、MkDocs Material primary sidebar。
- 正確做法：中版面已把 primary sidebar 內嵌的 `.md-nav--secondary` TOC 隱藏，因此也要隱藏 `.md-sidebar--primary label.md-nav__link[for="__toc"]`，只保留同一頁真正的 `<a>` 頁面連結。
- 不要做：不要只隱藏 `.md-nav--secondary`；Material 仍會輸出目前頁的 TOC toggle label，視覺上會變成兩個相同文章標題。
- 驗證方式：以約 1212px 寬度開啟 `docs/md/114-2/電機_作業系統/ch 1.md`，左側抽屜中目前頁應只剩一個可見 `Ch 1`；`label.md-nav__link[for="__toc"]` 應為 `display:none`，console error/warn 為空。

## 文章圖片寬度限制不可影響放大檢視

- 狀態：active
- 證據：verified
- 日期：2026-05-24
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`docs/theme/assets/pymdownx-extras/image-zoom.js`。
- 正確做法：一般文章圖片用 `--peicd-article-img-max-width` 控制，桌機預設 70%，窄螢幕改回 100%；全螢幕 `.peicd-image-viewer__img` 維持不受限制。
- 不要做：不要把 `max-width:70%` 套到 `.peicd-image-viewer__img`、logo、twemoji 或 Mermaid viewer 圖片，否則放大檢視和小螢幕可讀性會變差。
- 驗證方式：開啟 `ch 7.html`，桌機量測文章圖片最大比例應為 0.7；手機窄螢幕量測應可到 1.0；點圖放大時 viewer 圖片仍可縮放。

## 深色主題不要回到藍灰底

- 狀態：active
- 證據：user-requested
- 日期：2026-05-23
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、全站深色主題。
- 正確做法：深色主背景要像 ChatGPT 一樣接近黑色；body/container/main/content 應為 `#000000`，header/tabs 應為近黑，Mermaid 與右側 TOC 可用黑底漸層保留層級。
- 不要做：不要只改 `--md-default-bg-color` 後留下 header、tabs、Mermaid 圖卡或右側 TOC 仍是 `#1e2029` 這類藍灰底。
- 驗證方式：瀏覽器量測 `ch 7.html` 深色主題，body/container/main/content 為 `rgb(0, 0, 0)`，header/tabs 為 `rgba(0, 0, 0, 0.98)`，console error/warn 為空。

## 中/窄版 primary drawer 不可漏掉多層背景

- 狀態：active
- 證據：verified
- 日期：2026-05-24
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、MkDocs Material primary sidebar drawer。
- 正確做法：深色模式下要同時覆寫 `.md-sidebar--primary`、`.md-sidebar__inner`、`.md-sidebar__scrollwrap`、`.md-nav`、`.md-nav__list`、`.md-nav__item` 與 `.md-overlay`；drawer 本體維持 `#000000`，只用少量 cyan 邊界與目前項目提示。
- 不要做：不要只把 `.md-nav__title[for]` 或連結背景改黑；Material 的 drawer 由多層容器組成，漏一層就會在開啟側欄時露出藍灰底。
- 驗證方式：以約 1212px 寬度開啟 `ch 8.html` 並打開左側 drawer，量測 primary sidebar/scrollwrap/nav/list 應為 `rgb(0, 0, 0)`，overlay 應為黑色半透明，console error/warn 為空。

## 右側 TOC 深色模式不可留下藍灰 surface

- 狀態：active
- 證據：verified
- 日期：2026-05-24
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`peicd-toc-sidebar`。
- 正確做法：深色 TOC 的 `--peicd-toc-card-bg`、`--peicd-toc-head-bg`、`--peicd-toc-surface-bg` 應為 `#000000`，目前項目只用 `#050505` 加細 cyan 內框；inner/scrollwrap/nav/list/item 也要保底為黑色。
- 不要做：不要只改外層 `.md-sidebar__inner`；章節 link、控制按鈕、toggle、mobile close 仍可能用藍灰 surface 或外光，會讓右側欄看起來不是黑色。
- 驗證方式：以約 1212px 寬度開啟 `ch 8.html`，量測右側 TOC inner/scrollwrap/head/control/一般章節 link 應為 `rgb(0, 0, 0)`，目前項目可為 `rgb(5, 5, 5)`，console error/warn 為空。

## Blog excerpt 深色模式不可回到藍灰玻璃卡
- 狀態：active
- 證據：verified
- 日期：2026-05-24
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、MkDocs Material blog index。
- 正確做法：深色 `article.md-post--excerpt` 應使用 `#000000`、薄 cyan 邊界與低調角標；一般卡片不可有 background image，標題維持高對比淺青白。
- 不要做：不要保留原本的 radial/linear 玻璃漸層、掃描線、網格或大面積外光；首頁會和目前黑底筆記/TOC 風格不一致。
- 驗證方式：開啟 `blog/index.html`，桌機量測 blog card 為 `rgb(0, 0, 0)` 且 `background-image:none`；390px 窄版無水平 overflow，標題寬度應小於卡片寬度，console error/warn 為空。

## .codex/ Git 忽略策略

- 狀態：active
- 證據：observed
- 日期：2026-05-22
- 影響範圍：`.codex/`、`.gitignore`
- 正確做法：保留舊 `/codex/` 忽略規則作相容；`.codex/` 只忽略 `tmp/`、`private/`、`artifacts/`、`codex_tmp/` 與 `codex_compressed/`，不可忽略 `.codex/AGENTS.md` 與 `.codex/codex/` 核心文件。
- 不要做：不要把整個 `.codex/` 加進 `.gitignore`。
- 驗證方式：`git check-ignore -v .codex/codex/00_START_HERE.md` 不應命中；`.codex/codex/tmp/` 應被忽略。
