# DECISIONS

## ADR-0001：採用新版協作記憶分層結構

- 狀態：superseded by ADR-0004
- 日期：2026-05-18
- 背景：專案仍使用舊版 PEICD 協作檔，且本次任務會修改專案。
- 決策：將舊檔完整封存到 `.codex/codex/archive/legacy-2026-05-18/`，改用新版 `00_START_HERE.md`、`PROJECT.md`、`CURRENT_STATE.md` 等分層文件。
- 原因：符合全域 `AGENTS.md`，讓後續代理可由入口索引按需讀取，不再把所有內容塞進單一長檔。
- 後果：舊檔只作歷史全文，不再同步更新；2026-05-22 起主位置改為 `.codex/codex/`。
- 相關檔案：`.codex/codex/00_START_HERE.md`

## ADR-0002：Windows 下使用小寫 log.md

- 狀態：accepted
- 日期：2026-05-18
- 背景：Windows / NTFS 對大小寫檔名相容性較敏感。
- 決策：近期紀錄只使用 `.codex/codex/log.md`，不建立 `LOG.md`。
- 原因：避免同名大小寫檔案在不同工具或平台產生混淆。
- 相關檔案：`.codex/codex/log.md`

## ADR-0003：Source Jump 以位置指紋輔助文字比對

- 狀態：accepted
- 日期：2026-05-18
- 背景：Preview 右鍵開啟原文檔案有時會在重複文字或短段落時跳到錯誤位置。
- 選項：只靠文字搜尋；注入 source line；保留文字搜尋並加入前端位置指紋。
- 決策：保留既有文字比對，新增區段內 block index 與整頁進度比例加權，並把 `==...==`、`^^...^^` 視為渲染後文字。
- 原因：改動小、不需要修改筆記內容，也能降低重複文字誤判；若前端指紋缺失，後端仍可 fallback。
- 後果：前端與後端 query contract 新增 `section_index`、`block_progress`。
- 相關檔案：`tools/source_jump_hook.py`、`docs/theme/assets/pymdownx-extras/source-jump.js`

## ADR-0004：採用 `.codex/` 集中式協作目錄

- 狀態：accepted
- 日期：2026-05-22
- 背景：全域 PEICD 規則改為 `.codex/` 集中式協作目錄；本專案根目錄仍有 `codex/`、`codex_tmp/`、`.codex_tmp/`、`vbs_bat/`。
- 決策：將根目錄 `codex/` 移到 `.codex/codex/`，`codex_tmp/` 與 `.codex_tmp/` 移到 `.codex/codex_tmp/`，`vbs_bat/` 移到 `.codex/vbs_bat/`，並建立 `.codex/AGENTS.md`。
- 原因：符合新版代理啟動規則，讓協作檔集中管理，根目錄保留專案本體檔案。
- 後果：後續協作記憶只更新 `.codex/codex/`；根目錄 `codex/` 不再作為主記憶位置。
- 相關檔案：`.codex/AGENTS.md`、`.codex/codex/00_START_HERE.md`、`.gitignore`

## ADR-0005：Mermaid htmlLabels 行高與裁切框補強

- 狀態：accepted
- 日期：2026-05-22
- 背景：Mermaid flowchart 使用 htmlLabels 時，SVG `foreignObject` 高度由 Mermaid 量測產生；外部 CSS 若把 label 行高放大，文字實際高度會超過裁切框，造成 `g`、`p`、`y` 下緣被切。
- 決策：將 Mermaid htmlLabels 的 `foreignObject > div` 行高固定為 `1.18`，並在 `mermaid-render-fix.js` 渲染後把每個 `g.label > foreignObject` 高度額外加 5px、設為 visible overflow。
- 原因：`1.18` 讓 16px 字體的一行高度約 18.88px，接近 Mermaid 產生的一行 19px `foreignObject`；但實測最底部 `priority` 的 `y` 仍可能貼到底線，因此必須補大實際 SVG 裁切框。
- 後果：Mermaid 節點內多行文字行距較緊，label 裁切框略高但仍在節點矩形內；不需要改每個 Markdown 圖表。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`docs/theme/assets/pymdownx-extras/mermaid-render-fix.js`、`mkdocs.yml`
