# GOTCHAS

## Source Jump 不可只靠頁面文字首次命中

- 狀態：active
- 證據：observed
- 日期：2026-05-18
- 影響範圍：`tools/source_jump_hook.py`、`docs/theme/assets/pymdownx-extras/source-jump.js`
- 正確做法：文字比對要搭配標題路徑、前後 block、tag、block index、section index、page progress。
- 不要做：不要只用 `record.markdown.find(selection)` 或第一個 container 命中位置當結果。
- 驗證方式：用重複短句、`==...==` 標記與同頁不同章節測試右鍵定位。

## MkDocs Preview 需支援 serve --dirty

- 狀態：active
- 證據：verified
- 日期：2026-05-18
- 影響範圍：`tools/source_jump_hook.py`
- 正確做法：保留 `on_files` 預索引，再由 `on_page_markdown` 覆寫精修。
- 不要做：不要移除 `on_files` 後只依賴 `on_page_markdown`。
- 驗證方式：`mkdocs serve -f mkdocs.preview.yml --dirty` 下右鍵 lookup 能找到目前 preview 頁。

## Instant Navigation 前端綁定

- 狀態：active
- 證據：verified
- 日期：2026-05-18
- 影響範圍：所有依賴頁面 DOM 的自訂 JS。
- 正確做法：支援 `DOMContentLoaded` 與 `window.document$.subscribe(...)`。
- 不要做：不要只在 JS 初次載入時綁定一次頁面 DOM。
- 驗證方式：從首頁 instant navigation 到目標頁後，功能仍可操作。

## Mermaid htmlLabels 字母下緣裁切

- 狀態：active
- 證據：verified
- 日期：2026-05-22
- 影響範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、Mermaid flowchart htmlLabels。
- 正確做法：Mermaid htmlLabels 的 `foreignObject > div` 行高必須貼近 Mermaid 量測高度；同時 `mermaid-render-fix.js` 必須在渲染後把 `g.label > foreignObject` 高度額外加 5px，並把 `foreignObject` overflow 設成 visible。只檢查 `divHeight <= foreignObject height` 不夠，因為字型實際墨跡可能仍貼到底部。
- 不要做：不要只靠降低 line-height，也不要把 Mermaid htmlLabels 行高調到 `1.4` 或套用全站較大的 line-height；Mermaid 產生的單行 `foreignObject` 原始高度約 19px，`y` 的 descender 容易在最下方被切成像 `v`。
- 驗證方式：開啟 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係 Mermaid 圖，確認 `Higher priority`、`Lower priority` 最後的 `y` 下緣完整；瀏覽器量測單行 label `foreignObject` 應從 19px 增為 24px，且 console error/warn 為空。

## .codex/ Git 忽略策略

- 狀態：active
- 證據：observed
- 日期：2026-05-22
- 影響範圍：`.codex/`、`.gitignore`
- 正確做法：保留舊 `/codex/` 忽略規則作相容；`.codex/` 只忽略 `tmp/`、`private/`、`artifacts/`、`codex_tmp/` 與 `codex_compressed/`，不可忽略 `.codex/AGENTS.md` 與 `.codex/codex/` 核心文件。
- 不要做：不要把整個 `.codex/` 加進 `.gitignore`。
- 驗證方式：`git check-ignore -v .codex/codex/00_START_HERE.md` 不應命中；`.codex/codex/tmp/` 應被忽略。
