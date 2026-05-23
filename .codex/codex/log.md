# log

## 2026-05-23 12:39：Source Jump 開檔回饋修正

- 任務類型：bugfix
- 修改範圍：`docs/theme/assets/pymdownx-extras/source-jump.js`、`tools/source_jump_hook.py`、`mkdocs.yml`、`.codex/codex/` 交接文件。
- 主要決策：VS Code 開檔改為等待 CLI 回傳並檢查 exit code；前端成功時短暫顯示狀態再收起選單，右鍵事件先阻止原生選單競態。
- 驗證結果：`py_compile`、`node --check`、`mkdocs build -f mkdocs.preview.yml --clean` 均通過；本機 preview 右鍵 `ready queue 像 FCFS 一樣排隊` 可送出開檔，endpoint 回傳 `opened: true`、line 1564 column 4，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`GOTCHAS.md` 的 Source Jump 條目、`VERIFY.md` 的 Source Jump 驗證。
- 相關檔案：`tools/source_jump_hook.py`、`docs/theme/assets/pymdownx-extras/source-jump.js`、`mkdocs.yml`。

## 2026-05-22：`.codex/` 集中式協作目錄遷移

- 狀態：completed
- 本次遷移範圍：
  - `codex/` -> `.codex/codex/`
  - `codex_tmp/` -> `.codex/codex_tmp/legacy-codex_tmp/`
  - `.codex_tmp/` -> `.codex/codex_tmp/legacy-dot-codex_tmp/`
  - `vbs_bat/` -> `.codex/vbs_bat/`
- 已封存舊資料：既有 `archive/legacy-2026-05-18/` 隨 `codex/` 完整移到 `.codex/codex/archive/legacy-2026-05-18/`。
- 已建立或更新的新入口：`.codex/AGENTS.md`、`.codex/codex/00_START_HERE.md`。
- `.gitignore` 調整：新增 `.codex/` 暫存、私密、artifacts、壓縮備份忽略規則；保留舊 `/codex/` 忽略規則作相容。
- 驗證結果：根目錄不再有 `codex/`、`codex_tmp/`、`.codex_tmp/`、`vbs_bat/`；`.codex/codex/` 核心文件存在。
- 尚未處理：無。
- 下一位代理接手時必讀：`.codex/codex/00_START_HERE.md`、`.codex/codex/CURRENT_STATE.md`、`.codex/codex/GOTCHAS.md`。

## 2026-05-22

- 修正 Mermaid flowchart htmlLabels 英文字母 descender 被裁切：
  - `docs/theme/assets/pymdownx-extras/自定義.css` 將 `foreignObject > div` 行高從 `1.4` 改為 `1.18`，並明確保留 `overflow: visible`。
  - 使用者回報底部 `Higher priority` / `Lower priority` 的 `y` 仍像被切成 `v` 後，新增 `mermaid-render-fix.js` 渲染後補強：每個 `g.label > foreignObject` 高度額外加 5px，並把 `foreignObject` overflow 設成 visible。
  - `mkdocs.yml` 將 `自定義.css` cache 版本更新為 `20260522-2`，`mermaid-render-fix.js` 更新為 `20260522-1`。
- 驗證：
  - `Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`
  - `node --check docs\theme\assets\pymdownx-extras\mermaid-render-fix.js`
  - 以本機靜態預覽檢查 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係圖；目標節點 `divHeight <= foreignObject height`，瀏覽器 console error/warn 為空。
  - 再次截圖確認 `Higher priority`、`Lower priority` 的 `y` 下緣完整；單行 label `foreignObject` 由 19px 增為 24px。
  - `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\run_logged.py`
  - `tools\run_logged.py --name run-logged-smoke`，確認輸出落在 `.codex/codex/tmp/`。

## 2026-05-18

- 將舊版協作檔完整封存到 `.codex/codex/archive/legacy-2026-05-18/`，並建立新版分層結構。
- 改善 Preview 右鍵「開啟原文檔案」定位準確度：
  - 前端新增 `section_index` 與 `block_progress` 位置指紋。
  - 後端新增 section order、page progress 加權。
  - 後端索引會把 `==...==` 與 `^^...^^` 視為渲染後文字。
- 驗證：
  - `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
  - `node --check docs\theme\assets\pymdownx-extras\source-jump.js`
  - 以 `docs/md/114-2/電機_作業系統/ch 6.md` line 746 做定位 smoke test，回傳 line 746 column 3。
  - `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name source-jump-preview-build-2 -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0，歷史輸出已隨遷移移到 `.codex/codex/tmp/`。
  - 啟動本機 preview server 後以 HTTP 查詢 `__peicd/source-jump`，`ch 6.md` 高亮段落回傳 line 746 column 3；測完已停止 server。
