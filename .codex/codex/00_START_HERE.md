# 00 START HERE

## 讀取順序

1. `AGENTS.md`：每次新任務都先重新定位並完整讀取。
2. `.codex/codex/00_START_HERE.md`
3. `.codex/codex/CURRENT_STATE.md`
4. `.codex/codex/USER_REQUIREMENTS.md`
5. `.codex/codex/GOTCHAS.md`
6. 依任務讀取 `ARCHITECTURE.md`、`VERIFY.md`、`COMMANDS.md`、`playbooks/` 或 `knowledge/`。

## 專案地圖

- `PROJECT.md`：專案用途、環境與常用入口。
- `ARCHITECTURE.md`：MkDocs、preview、source-jump、Back to bottom、多益600 小專案架構。
- `COMMANDS.md`：常用 build、preview、驗證命令。
- `VERIFY.md`：修改後的最小可靠驗證。
- `DECISIONS.md`：重要決策與取捨。
- `GOTCHAS.md`：不要重犯的坑。
- `log.md`：近期工作摘要。

## 任務路由

- 右鍵開啟原文檔案：先讀 `ARCHITECTURE.md` 的 Source Jump，再看 `docs/theme/assets/pymdownx-extras/source-jump.js` 與 `tools/source_jump_hook.py`。
- 單頁 preview：先讀 `PROJECT.md`、`COMMANDS.md`，再看 `preview.bat`、`p.bat`、`tools/update_preview_config.py`、`mkdocs.preview.yml`。
- MkDocs 外觀或前端互動：看 `docs/theme/`、`mkdocs.yml`、`ARCHITECTURE.md`。
- Mermaid 圖表文字裁切：先看 `GOTCHAS.md` 的 Mermaid htmlLabels 條目，再改 `docs/theme/assets/pymdownx-extras/自定義.css`。
- 多益600：看 `docs/md/多益600/`、`PROJECT.md` 的小專案說明。

## 舊檔封存與映射

舊版 PEICD 檔案已於 2026-05-18 完整移到 `.codex/codex/archive/legacy-2026-05-18/`。
根目錄 `codex/` 已於 2026-05-22 移到 `.codex/codex/`。

- `README_PEICD100.md` -> `PROJECT.md`
- `專案規格書.md` -> `ARCHITECTURE.md`
- `使用者要求.md` -> `USER_REQUIREMENTS.md`
- `協作重要事項.md` -> `GOTCHAS.md`
- 舊 `log.md`：本次未偵測到根目錄舊檔；歷史摘要放在 `archive/log-history-summary.md`

## 高風險注意

- 工作樹可能已有使用者未提交的 Markdown 內容變更；除非任務直接相關，不要碰現有筆記內容。
- `.gitignore` 保留舊 `/codex/` 忽略規則，並只忽略 `.codex/` 下的 tmp/private/artifacts/壓縮備份；不要把 `.codex/AGENTS.md` 與 `.codex/codex/` 核心文件整包忽略。
- `source-jump` 不要只依賴 `on_page_markdown`；目前必須保留 `on_files` 預索引與 `on_page_markdown` 精修。
- 專案啟用 Material `navigation.instant`，前端 DOM 綁定需支援 `window.document$.subscribe(...)`。
- 驗證輸出要放 `.codex/codex/tmp/`，不要把 `.out.log` / `.err.log` 留在根目錄。
