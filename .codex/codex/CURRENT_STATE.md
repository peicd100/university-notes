# CURRENT STATE

## 目前狀態

- 2026-05-22 已將根目錄 `codex/`、`codex_tmp/`、`.codex_tmp/`、`vbs_bat/` 遷移到 `.codex/` 集中式協作目錄。
- 2026-05-22 已修正 Mermaid htmlLabels 英文字母 descender 被切到的問題：`docs/theme/assets/pymdownx-extras/自定義.css` 將 Mermaid label 行高調整為 `1.18`，`docs/theme/assets/pymdownx-extras/mermaid-render-fix.js` 會在渲染後把每個 label `foreignObject` 高度加大 5px，並更新 `mkdocs.yml` CSS/JS cache 版本。
- `mkdocs.preview.yml` 目前 preview 目標是 `md/114-2/電機_作業系統/ch 6.md`。

## 近期功能方向

- 前端 `source-jump.js` 會送出 block index、區段內 index、整頁進度比例、標題路徑與鄰近段落。
- 後端 `source_jump_hook.py` 會把這些位置指紋納入候選分數，降低重複文字跳錯位置的機率。
- 後端索引會把常見渲染標記 `==...==`、`^^...^^` 視為渲染後文字，讓右鍵未選字時也能落在可見文字位置。

## 既有工作樹注意

- 本次 Mermaid 修正未改動 `docs/md/114-2/電機_作業系統/ch 6.md` 筆記內容，只改共用樣式與協作目錄。

## 最後驗證

- 已完成：`Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
- 已完成：`node --check docs\theme\assets\pymdownx-extras\source-jump.js`
- 已完成：以 `ch 6.md` line 746 的 `==...==` 段落做定位函式 smoke test，回傳 line 746 column 3。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name source-jump-preview-build-2 -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0。
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8026`，直接呼叫 `__peicd/source-jump` endpoint，`ch 6.md` 高亮段落回傳 line 746 column 3；測完已停止 server。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0。
- 已完成：以本機靜態預覽開啟 `ch 6.html`，確認 `Priority-based Preemptive Scheduling` Mermaid 圖表的 label `divHeight` 均小於或等於 `foreignObject` 高度，瀏覽器 console error/warn 為空。
- 已完成：再次依使用者截圖回測底部 `Higher priority` / `Lower priority`，確認 `foreignObject` 由 19px 增為 24px，底部字母 `y` 不再被裁切，瀏覽器 console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m py_compile tools\run_logged.py`。
- 已完成：`tools\run_logged.py --name run-logged-smoke`，確認輸出改到 `.codex/codex/tmp/`。
