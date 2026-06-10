# VERIFY

## Source Jump

最小驗證：

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\admonition_title_hook.py
node --check theme\assets\pymdownx-extras\source-jump.js
Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

手動驗證：

- 啟動 `p.bat` 或 `preview.bat docs\md\114-2\電機_作業系統\ch 6.md`。
- 在 preview 頁右鍵一般段落、`==...==` 高亮段落、code block、重複短句。
- 在 `docs/md/114-2/科技_計算機結構/期末考複習-ch3.md` 的 `!!! danger` 區塊內右鍵 `3. mflo 和 mfhi：怎麼把答案拿回一般 register？`，應定位到原文第 1631 行；選字 `mflo` 也應回第 1631 行，不可跳到第 1629 行的 `!!! danger`。
- 確認 VS Code 開到同一 Markdown 的正確行附近。
- 右鍵選單應只顯示「開啟原文檔案」，不應再出現「複製」。

## 前端互動

- 使用瀏覽器確認選字右鍵與未選字右鍵都可顯示選單。
- 若涉及 Material instant navigation，從其他頁切到目標頁後再測一次。
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
- 若修改 TTS 面板，開啟 header 喇叭按鈕，確認深色面板使用黑底薄線、slider 與選取狀態使用 cyan、控制文字不擠壓，且 console error/warn 為空。
- 若修改文章圖片尺寸，桌機量測 `.md-content__inner.md-typeset img:not(.twemoji)` 最大寬度比例應不超過 0.7；手機或窄螢幕應可回到 1.0；全螢幕 image viewer 不應被 70% 規則限制。
- 若修改 `collapse-code` 樣式，開啟有 `/// collapse-code` 的頁面，收合狀態展開按鈕應約 1.45rem、不是大色塊；展開後 `.code-footer` 不應覆蓋最後幾行程式碼，且 footer 背景應與 code block 背景一致、不可留下突兀黑色底條，console error/warn 應為空。
- 若修改 admonition 標題處理，驗證 `!!! danger "記下來"` 會輸出 `Danger 記下來`，且 `!!! danger` 仍只輸出 `Danger`，不可重複成 `Danger Danger`。

## 輸出管理

若需要保留驗證輸出，使用：

```bat
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name <name> -- <command...>
```

輸出應落在 `.codex/codex/tmp/`。
