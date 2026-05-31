# CURRENT STATE

## 目前狀態

- 2026-05-31 已將網站資訊與導覽設定從 `mkdocs.yml` 拆到 `docs/.mkdocs/site.yml`，根目錄 `mkdocs.yml` 以 `INHERIT: docs/.mkdocs/site.yml` 繼承。
- 2026-05-31 已將 `docs/theme/` 移到根目錄 `theme/`，並將 `theme.custom_dir` 改為 `theme`；後續外觀、模板與自訂 JS/CSS 請先看 `theme/`。
- 2026-05-31 已把根目錄 `指令.txt` 加入 `.gitignore`，並用 `git rm --cached -- 指令.txt` 保留本機檔案但停止 Git 追蹤。
- 2026-05-31 已壓縮舊 `CURRENT_STATE.md` 與 `log.md`：全文封存在 `archive/current-state-2026-05-31-site-config-reorg.md` 與 `archive/log-2026-05-31-site-config-reorg.md`。

## 下次建議先讀

- 導覽、網站名稱、`site_url`、`exclude_docs`：`docs/.mkdocs/site.yml`。
- MkDocs 技術設定、plugins、hooks、Markdown extensions、extra CSS/JS：`mkdocs.yml`。
- 自訂 Material template、TTS 面板、前端互動、CSS/JS：`theme/`。
- Preview 流程：`COMMANDS.md`、`VERIFY.md`、`mkdocs.preview.yml`、`preview.bat`。

## 最後驗證

- `node --check theme\assets\pymdownx-extras\source-jump.js`：通過。
- `node --check theme\assets\pymdownx-extras\folder-path-bar.js`：通過。
- `node --check theme\assets\pymdownx-extras\mermaid-config-override.js`：通過。
- `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`：通過。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name site-config-split-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260531-204305-site-config-split-build.*`。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name site-config-split-preview-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260531-204414-site-config-split-preview-build.*`。
- 檢查：`site/assets/pymdownx-extras/source-jump.js` 與 `site/assets/pymdownx-extras/自定義.css` 存在；`site/.mkdocs/site.yml` 不存在；`docs/theme` 不存在；`theme/main.html` 存在。