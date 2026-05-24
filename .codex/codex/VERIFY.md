# VERIFY

## Source Jump

最小驗證：

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py
node --check docs\theme\assets\pymdownx-extras\source-jump.js
Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

手動驗證：

- 啟動 `p.bat` 或 `preview.bat docs\md\114-2\電機_作業系統\ch 6.md`。
- 在 preview 頁右鍵一般段落、`==...==` 高亮段落、code block、重複短句。
- 確認 VS Code 開到同一 Markdown 的正確行附近。
- 右鍵選單應只顯示「開啟原文檔案」，不應再出現「複製」。

## 前端互動

- 使用瀏覽器確認選字右鍵與未選字右鍵都可顯示選單。
- 若涉及 Material instant navigation，從其他頁切到目標頁後再測一次。
- 若修改 Mermaid 樣式，至少開啟 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係圖，確認 `Priority-based Preemptive Scheduling`、`Shorter period`、`Higher priority` 等英文字下緣沒有被裁切。
- Mermaid htmlLabels 可用瀏覽器量測：目標圖表每個 `g.node foreignObject` 都應帶 `data-peicd-descender-pad="true"`；單行 label 高度應從原始 19px 增到約 24px，且 `Higher priority`、`Lower priority` 最後的 `y` 必須可見。
- 若修改 Mermaid 暗色對比，開啟 `docs/md/114-2/電機_作業系統/ch 7.md` 的 deadlock flowchart；`dracula` 主題下 node label 應接近白色、node fill 應為深紫、node stroke 應為 `#72e3fd`，edge label 應為深底白字，console error/warn 應為空。
- 若修改深色背景，量測 `ch 7.html`：body/container/main/content 應為 `rgb(0, 0, 0)`，header/tabs 應為 `rgba(0, 0, 0, 0.98)`；Mermaid 圖卡與右側 TOC 可為黑底漸層，console error/warn 應為空。
- 若修改標題錨點樣式，開啟 `ch 7.html` 的 `⭐Resource-Allocation Graph Algorithm` h2，量測 `.headerlink` 與標題文字第一行應維持同一行，且長標題不應讓 `#` 獨立換到上一行。
- 若修改中版面左側導覽或路徑列，開啟 `ch 1.html` 並用約 1212px 寬度測試：目前頁的 `label.md-nav__link[for="__toc"]` 應為 `display:none`、左側目前頁只剩一個可見連結；深色路徑列的目前資料夾與頁面文字需有清楚對比。再用約 766px 寬度確認窄版 select 文字同樣清楚。
- 若修改文章圖片尺寸，桌機量測 `.md-content__inner.md-typeset img:not(.twemoji)` 最大寬度比例應不超過 0.7；手機或窄螢幕應可回到 1.0；全螢幕 image viewer 不應被 70% 規則限制。

## 輸出管理

若需要保留驗證輸出，使用：

```bat
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name <name> -- <command...>
```

輸出應落在 `.codex/codex/tmp/`。
