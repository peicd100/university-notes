# USER REQUIREMENTS

## Slash admonition 與 details 摺疊語法

- 狀態：active
- 證據：user-requested
- 日期：2026-06-10
- 影響範圍：Markdown 筆記中的 admonition / danger block / details block 渲染。
- 正確做法：
  - `!!! danger "重點"`、`/// danger "重點"`、`/// danger|重點`、`/// danger | 重點` 都應渲染為 `Danger | 重點`。
  - `Danger` 與自訂標題中間固定使用 ` | ` 分隔。
  - `/// details|摺疊`、`/// details | 摺疊` 保持 pymdownx details 語法，視覺要符合目前深黑、cyan、等寬技術筆記風格。
  - details 摺疊框內文不可比正文刻意縮小；標題列可以較精簡。
- 不要做：
  - 不要把 `details` 當成 admonition 轉成 `!!! details`。
  - 不要輸出 `Danger Danger` 或 `Danger | Danger`。
  - 不要使用漸層、光暈或大面積彩色背景改善 details。
- 驗證方式：執行 hook smoke test、`mkdocs build --clean`，並用 Playwright 截 `details` 關閉與展開狀態。
- 相關檔案：`tools/admonition_title_hook.py`、`tools/source_jump_hook.py`、`theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 長期要求

- 狀態：active
- 證據：user-requested
- 日期：2026-05-18
- 正確做法：
  - 全程使用繁體中文。
  - 中文文字檔使用 UTF-8 無 BOM。
  - 沒有被要求修改檔案時，不主動改檔。
  - 使用 conda 管理 Python；本專案使用 `mkdocs` 環境。
  - 完成任務後要說明做了什麼、怎麼做、用了什麼。
  - 專案修改時要同步維護 `.codex/codex/` 協作檔。
  - 人工驗證輸出統一放 `.codex/codex/tmp/`，不要散在根目錄。

## Preview 與 UI 偏好

- 狀態：active
- 證據：user-requested
- 日期：2026-05-23
- 正確做法：
  - 單頁 preview 可用 `.\p <Markdown 路徑>`，也可只輸入 `.\p` 沿用上次目標。
  - 在 cmd 內用 `p <Markdown 路徑>` 啟動 preview 後，按 Ctrl+C 應直接結束，不要再停在「要終止批次工作嗎 (Y/N)」；此要求需由 `p.exe` console launcher 滿足，不要依賴長時間執行的 `.bat`。
  - Preview 右鍵「開啟原文檔案」要優先追求定位準確度，避免跳到同頁錯誤段落。
  - Preview 在 `!!! danger` / admonition block 內右鍵時，要定位到實際渲染的內文 block 原文行；只有點 admonition 標題列時才回 `!!! danger` 起始行。
  - Preview 右鍵選單只保留「開啟原文檔案」，不要顯示「複製」。
  - 保留 Material 內建 `Back to top`，右下角 `Back to bottom` 是額外功能。
  - UI 預設重點色可用 `#72e3fd`，但不要大面積無腦鋪滿。
  - 深色主題背景要接近 ChatGPT 黑底：主背景使用黑色，卡片、Mermaid 與 TOC 用很深的近黑層級色，不要回到藍灰底。
  - 中/窄版側邊欄 drawer 開啟時，本體背景也必須是純黑或近黑，不要露出藍灰底；可用少量 cyan 作目前項目與邊界提示。
  - 右側 TOC 深色模式也要以純黑為主；章節項目不要使用藍灰大底或明顯外光，目前項目可用極深近黑底與細 cyan 內框。
  - 首頁 blog 方塊要跟目前黑底技術筆記風格一致：純黑底、薄 cyan 邊界、低調角標，不要藍灰玻璃底、網格掃描線或大面積 glow。
  - 深色主題的 `==mark==` 高亮要比黑底明顯，保留筆記標記感，但文字與底色對比要清楚；避免厚重黃橙漸層、大面積外光或 `mark` 內 inline code 被切成一顆顆膠囊。
  - 標題錨點 `#` 要和標題文字維持同一行；長標題可以換行，但不要讓錨點自己獨立成一行。
  - 桌機文章圖片最多佔內容寬度 70%，比 70% 小的圖片不要放大；手機或窄螢幕圖片可回到 100% 以保留可讀性。
  - 深色模式的下拉選單與小工具面板要避免厚重四角框、藍灰大底與過度發光；優先用純黑/近黑底、薄邊框、小圓角、少量 cyan 選取狀態。
  - Markdown `---` 分隔線在亮色模式與暗色模式都要明顯但不要太硬；不要做成整條同樣粗度，應保留中間略粗、左右細且有留白呼吸感的視覺，中央粗線範圍約佔頁面寬度 70%，優先用柔和 cyan 中央線搭配低調左右細線。
  - `collapse-code` 展開/收合按鈕不要太大；應是小型工具按鈕，且展開後底部不要留下黑色底條或與 code block 表面不一致的 footer。
  - `!!! danger "記下來"` 這類 admonition 自訂標題渲染後要保留類型前綴與分隔線，例如顯示 `Danger | 記下來`；未自訂標題的 `!!! danger` 則維持 `Danger`。
  - Admonition / `!!! danger` 內文不要比正文小；框內段落、清單、表格與標題應回到正文基準字級，只有 `Danger` 標題列可維持較精簡的小一階樣式。
  - details 摺疊框的箭頭與標題文字不可重疊；若使用 pseudo-element 畫箭頭，必須保留穩定佔位與足夠間距。
  - 右側 TOC 工具列需提供 `Danger` 按鈕；按下後進入 Danger Block 目錄，項目使用 Danger 自訂標題文字，無自訂標題時使用最近的 `h1-h6` 標題，沒有任何 Danger block 時顯示「此筆記沒有任何 Danger Block」。
  - Danger 目錄需可點擊跳轉到對應 Danger block，並用「現在在這裡」標示目前最近的 Danger 項目；在 Danger 目錄中按「展開 / 收合 / 自動 / 手動」任一按鈕，必須切回一般 TOC 對應模式。
  - `Danger` 按鈕本身是固定進入 Danger 目錄，不是切換鈕；不管連按幾次都應停在 Danger 目錄，只有「展開 / 收合 / 自動 / 手動」會切回一般 TOC。

## 多益600

- 狀態：active
- 證據：user-requested
- 日期：2026-05-18
- 正確做法：
  - `docs/md/多益600` 併入主專案。
  - 保留筆記、圖片、includes、`紀錄.py` 與工具文件。
  - 生成影片、TTS 暫存、測試媒體與本機紀錄不得上傳到 Git。

## Slash admonition 簡寫語法

- 狀態：active
- 證據：user-requested
- 日期：2026-06-10
- 影響範圍：Markdown 筆記中的 admonition / danger block 寫法、Preview 渲染、Source Jump 定位。
- 正確做法：支援 `/// danger "重點"`、未縮排內文、結尾 `///` 的簡寫語法，渲染時等同 `!!! danger "重點"` 加縮排內文；標題需顯示為 `Danger | 重點`。`/// danger` 沒有自訂標題時維持預設 `Danger`。
- 不要做：不要把所有 `/// xxx` 都轉成 admonition；`/// collapse-code` 等既有非 admonition block 必須保持原行為。
- 驗證方式：用 `tools/admonition_title_hook.py` 字串轉換測試、`tools/source_jump_hook.py` synthetic block 行號測試、Python-Markdown admonition smoke test 與 `mkdocs build --clean`。
- 相關檔案：`tools/admonition_title_hook.py`、`tools/source_jump_hook.py`、`.codex/codex/VERIFY.md`。
