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
- Preview 流程：`COMMANDS.md`、`VERIFY.md`、`mkdocs.preview.yml`、`p.exe`、`tools/p.py`。

## 最後驗證

- 2026-06-14 Mermaid lazy render：`node --check` 通過；`image_lazy_loading_hook.py` py_compile 通過；`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name mermaid-lazy-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean` returncode 0；Playwright local server 量測 `ch 3.html#311-行程process` 初始 DCL 約 2.7s、初始 Mermaid rendered 0，完整捲頁後 18/18 Mermaid render；ch6/ch7 Mermaid 回歸通過。
- `Y:\conda\envs\mkdocs_desk\python.exe -m py_compile tools\p.py`：通過。
- `cmd /d /c "pushd ""\\vmware-host\Shared Folders\github_note\university notes"" && p /? && set PREVIEW_SKIP_SERVE=1&& p docs\md\114-2\科技_計算機結構\期末考複習-ch5.md && popd"`：通過；`p /?` 顯示 `Usage: p ...`，確認目前 `p` 走 `p.exe`。
- `cmd /d /c "set PREVIEW_SKIP_SERVE=1&& ""\\vmware-host\Shared Folders\github_note\university notes\p.bat"""`：通過。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name preview-absolute-config-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f "\\vmware-host\Shared Folders\github_note\university notes\mkdocs.preview.yml" --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260611-224242-preview-absolute-config-build.*`。
- 從 `C:\Windows` 執行 `Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f "\\vmware-host\Shared Folders\github_note\university notes\mkdocs.preview.yml" -d ".codex/codex/tmp/preview-absolute-cwd-site" --clean`：returncode 0；暫存 site 已刪除。
- `node --check theme\assets\pymdownx-extras\toc-fold.js`：通過。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name danger-toc-button-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260611-222259-danger-toc-button-build.*`。
- Playwright CLI 驗證 `site/md/114-2/科技_計算機結構/期末考複習-ch4.2.html`：`Danger` 文字完整可見；重複按 `Danger`、點 Danger 項目、帶 `#peicd-danger-block-1` 重載後皆維持 Danger 視圖；截圖在 `.codex/codex/artifacts/danger-toc-toolbar-after.png`。
- `cmd /d /c "set PREVIEW_SKIP_SERVE=1&& p.bat"`：通過。
- `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\admonition_title_hook.py tools\source_jump_hook.py`：通過。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name ctrlc-details-final-preview-build-retry -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260610-233544-ctrlc-details-final-preview-build-retry.*`。
- Playwright 量測 `docs/md/114-2/電機_作業系統/ch 5.md` 的 plain details：`summary::before position=static`、`mask=none`、`noOverlap=true`，截圖在 `.codex/codex/artifacts/details-summary-after.png`。
- `node --check theme\assets\pymdownx-extras\source-jump.js`：通過。
- `node --check theme\assets\pymdownx-extras\folder-path-bar.js`：通過。
- `node --check theme\assets\pymdownx-extras\mermaid-config-override.js`：通過。
- `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`：通過。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name site-config-split-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260531-204305-site-config-split-build.*`。
- `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name site-config-split-preview-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`：returncode 0；輸出在 `.codex/codex/tmp/20260531-204414-site-config-split-preview-build.*`。
- 檢查：`site/assets/pymdownx-extras/source-jump.js` 與 `site/assets/pymdownx-extras/自定義.css` 存在；`site/.mkdocs/site.yml` 不存在；`docs/theme` 不存在；`theme/main.html` 存在。
