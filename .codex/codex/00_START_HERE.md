# 00 START HERE

> UI 字體相關任務：正文預設維持原本 `var(--md-text-font), "Cascadia Mono", monospace`；不要再把全站正文改成 CJK fallback，除非使用者重新明確指定。

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

- 網站資訊、導覽或 `exclude_docs`：直接看 `docs/.mkdocs/site.yml`；根目錄 `mkdocs.yml` 只保留技術設定並用 `INHERIT` 繼承它。
- 右鍵開啟原文檔案：先讀 `ARCHITECTURE.md` 的 Source Jump，再看 `theme/assets/pymdownx-extras/source-jump.js` 與 `tools/source_jump_hook.py`。
- 單頁 preview：先讀 `PROJECT.md`、`COMMANDS.md`，再看 `preview.bat`、`p.bat`、`tools/update_preview_config.py`、`mkdocs.preview.yml`。
- MkDocs 外觀或前端互動：看 `theme/`、`mkdocs.yml`、`ARCHITECTURE.md`。
- 首頁 blog 方塊：先看 `USER_REQUIREMENTS.md` 的 UI 偏好與 `GOTCHAS.md` 的 Blog excerpt 條目，再改 `theme/assets/pymdownx-extras/自定義.css`。
- `collapse-code` 折疊程式碼外觀：先看 `USER_REQUIREMENTS.md` 的 UI 偏好與 `VERIFY.md` 的前端互動清單，再改 `theme/assets/pymdownx-extras/自定義.css` 的 `.collapse-code` 區段。
- 標題錨點或標題換行：先看 `USER_REQUIREMENTS.md` 的 UI 偏好與 `GOTCHAS.md` 的標題錨點條目，再改 `theme/assets/pymdownx-extras/自定義.css`。
- Markdown `---` 分隔線可讀性：先看 `USER_REQUIREMENTS.md` 的 UI 偏好，再改 `theme/assets/pymdownx-extras/自定義.css` 的 `.md-typeset hr` 與相關 CSS 變數。
- 中版面左側導覽、drawer 背景或路徑列對比：先看 `GOTCHAS.md` 的中版面左側目前頁與 primary drawer 背景條目、`VERIFY.md` 的前端互動清單，再改 `theme/assets/pymdownx-extras/自定義.css`。
- 文章圖片大小或放大檢視：先看 `USER_REQUIREMENTS.md` 的圖片寬度偏好、`GOTCHAS.md` 的文章圖片寬度條目，再改 `theme/assets/pymdownx-extras/自定義.css` 與必要時 `image-zoom.js`。
- 深色主題背景或右側 TOC：先看 `USER_REQUIREMENTS.md` 的 UI 偏好與 `GOTCHAS.md` 的深色主題、右側 TOC 條目，再改 `theme/assets/pymdownx-extras/自定義.css`。
- Mermaid 圖表文字可讀性（裁切或深色對比）：先看 `GOTCHAS.md` 的 Mermaid 條目，再改 `theme/assets/pymdownx-extras/mermaid-config-override.js` 與 `theme/assets/pymdownx-extras/自定義.css`。
- 多益600：看 `docs/md/多益600/`、`PROJECT.md` 的小專案說明。

## 舊檔封存與映射

舊版 PEICD 檔案已於 2026-05-18 完整移到 `.codex/codex/archive/legacy-2026-05-18/`。
根目錄 `codex/` 已於 2026-05-22 移到 `.codex/codex/`。
2026-05-31 已將過長的 `CURRENT_STATE.md` 與 `log.md` 全文封存到 `archive/current-state-2026-05-31-site-config-reorg.md` 與 `archive/log-2026-05-31-site-config-reorg.md`，主檔只保留近期高訊號狀態。

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
