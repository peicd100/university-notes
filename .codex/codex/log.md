# log

## 2026-06-10 12:11：Danger block Source Jump 定位修正

- 任務類型：bugfix
- 修改範圍：`tools/source_jump_hook.py`、`.codex/codex/ARCHITECTURE.md`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/VERIFY.md`、`.codex/codex/GOTCHAS.md`、`.codex/codex/00_START_HERE.md`。
- 主要決策：Source Jump 在 `on_page_markdown` 重建索引時改回讀原始 Markdown，並為 `!!!` / `???` admonition 建立 synthetic blocks；container-only lookup 對短 substring 降權。因 `GOTCHAS.md` 超過 active 條目門檻，已封存全文並壓縮成主題索引。
- 驗證結果：`source_jump_hook.py` 編譯通過；合成與真實檔案測試確認 danger 標題/內文定位；preview endpoint 對 `期末考複習-ch3.md` 空 selection 與 `mflo` selection 都回第 1631 行；完整 build returncode 0。
- 尚未完成：沒有。
- 下次建議先讀：`GOTCHAS.md` 的 Source Jump serve 階段索引與 admonition synthetic blocks 條目。
- 相關檔案：`.codex/codex/tmp/20260610-120857-source-jump-admonition-final-build.meta.json`、`.codex/codex/tmp/source-jump-admonition-serve-fixed.out.log`、`.codex/codex/archive/gotchas-2026-06-10-before-source-jump-admonition-compress.md`。

## 2026-06-10 09:23：Admonition 自訂標題保留類型前綴

- 任務類型：feature
- 修改範圍：`tools/admonition_title_hook.py`、`mkdocs.yml`、`.codex/codex/ARCHITECTURE.md`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/VERIFY.md`。
- 主要決策：新增 MkDocs `on_page_markdown` hook，把 `!!! danger "記下來"` 這類自訂標題渲染成 `Danger 記下來`；未自訂標題維持預設 `Danger`，並跳過 fenced code block 範例。
- 驗證結果：`admonition_title_hook.py` 編譯通過；樣本測試確認自訂/預設/code fence 行為；完整 build returncode 0；產出 HTML 有 `Danger 重點`、一般 `Danger`，未出現 `Danger Danger`。
- 尚未完成：沒有。
- 下次建議先讀：`ARCHITECTURE.md` 的 Admonition 標題、`VERIFY.md` 的 admonition 標題處理驗證條目。
- 相關檔案：`.codex/codex/tmp/20260610-092133-admonition-title-prefix-build.meta.json`、`site/blog/2024/02/06/mkdocs-語法.html`、`site/md/114-2/科技_計算機結構/ch 3.html`。

## 2026-06-10 08:57：暗色高亮樣式優化

- 任務類型：docs
- 修改範圍：`theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/VERIFY.md`。
- 主要決策：暗色 `==mark==` 改為淡金純色連續高亮層，移除黃橙漸層與外光；`mark` 內 inline code 改透明，避免分段膠囊感。
- 驗證結果：preview build 與 full build 均 returncode 0；Playwright/Chrome 截圖確認目標表格列高亮變為連續細緻線條；console warning/error 為空，computed `backgroundImage:none`。
- 尚未完成：沒有。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`VERIFY.md` 的 `==mark==` 高亮驗證條目。
- 相關檔案：`output/playwright/mark-highlight-section-20260610.png`、`.codex/codex/tmp/20260610-085049-mark-highlight-preview-build.meta.json`、`.codex/codex/tmp/20260610-085630-mark-highlight-full-build.meta.json`。

## 2026-05-31 20:45：MkDocs 設定拆分與 theme 移動

- 任務類型：refactor
- 修改範圍：`mkdocs.yml`、`docs/.mkdocs/site.yml`、`theme/`、`.gitignore`、`2.py`、`.codex/codex/`。
- 主要決策：`mkdocs.yml` 保留技術設定並繼承 `docs/.mkdocs/site.yml`；自訂 theme 從 `docs/theme/` 移到根目錄 `theme/`；根目錄 `指令.txt` 改為本機忽略檔。
- 驗證結果：JS 語法檢查、`source_jump_hook.py` 編譯、完整 build 與 preview build 都通過；`docs/.mkdocs/site.yml` 未輸出到 `site/`。
- 尚未完成：沒有。
- 下次建議先讀：`docs/.mkdocs/site.yml`、`mkdocs.yml`、`theme/`、`CURRENT_STATE.md`。
- 相關檔案：`mkdocs.yml`、`docs/.mkdocs/site.yml`、`theme/main.html`、`.gitignore`、`.codex/codex/archive/current-state-2026-05-31-site-config-reorg.md`、`.codex/codex/archive/log-2026-05-31-site-config-reorg.md`。
