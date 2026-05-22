# 舊版紀錄摘要

## 封存位置

舊版 PEICD 協作檔完整封存在：

`codex/archive/legacy-2026-05-18/`

## 高訊號脈絡

- 專案是 MkDocs Material 筆記網站，使用 conda `mkdocs`。
- Source Jump 功能由 `source-jump.js` 與 `source_jump_hook.py` 共同提供。
- 先前已修過 `serve --dirty` 下索引不穩，因此 `on_files` 預索引不能移除。
- 單頁 preview 由 `preview.bat`、`p.bat` 與 `tools/update_preview_config.py` 管理。
- `Back to bottom` 按鈕需支援 Material `navigation.instant`。
- 多益600 小專案已併入主專案，生成物不得進 Git 或站點輸出。

## 舊檔映射

- `README_PEICD100.md` -> `PROJECT.md`
- `專案規格書.md` -> `ARCHITECTURE.md`
- `使用者要求.md` -> `USER_REQUIREMENTS.md`
- `協作重要事項.md` -> `GOTCHAS.md`
- 舊 `log.md`：本次未偵測到根目錄舊檔
