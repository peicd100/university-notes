# log

## 2026-06-11 22:02：右側 Danger Block 目錄

- 任務類型：feature
- 修改範圍：`theme/assets/pymdownx-extras/toc-fold.js`、`theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：右側 TOC 新增 `Danger` 模式；Danger 項目由正文 DOM 掃描產生，優先使用自訂 Danger 標題，無標題時用最近 heading；Danger link 自行處理 hash 與捲動以避開 Material instant navigation 重初始化。
- 驗證結果：`node --check toc-fold.js` 通過；三次 full build returncode 0；內建瀏覽器驗證 12 筆 Danger、無 Danger 空狀態、點擊 `#peicd-danger-block-7`、按「自動」回一般 TOC，console error/warn 為空。
- 尚未完成：沒有。
- 下次建議先讀：`ARCHITECTURE.md` 的 Right TOC 與 Danger TOC、`GOTCHAS.md` 的 Danger TOC 條目、`VERIFY.md` 的前端互動 TOC 檢查。
- 相關檔案：`.codex/codex/tmp/20260611-215954-danger-toc-build-after-click-fix.meta.json`。

## 2026-06-10 23:36：Preview Ctrl+C 與 details 箭頭重疊修正

- 任務類型：bugfix
- 修改範圍：`p.bat`、`preview.bat`、`theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：`p.bat` 與 `preview.bat` 改用條件式 `exit /b` 收尾，避免 Ctrl+C 出現批次終止確認；details 箭頭重置為 `position: static` 的 flex item，避免蓋到標題。
- 驗證結果：`PREVIEW_SKIP_SERVE=1` 的 `p.bat` 通過；`py_compile` 通過；preview build retry returncode 0；Playwright 量測 `beforePosition=static`、`beforeMaskImage=none`、`noOverlap=true`。
- 尚未完成：無法在非互動工具中實際按 Ctrl+C，只能以 batch 條件式 exit 與手動驗證清單覆蓋；互動 cmd 可再人工確認。
- 下次建議先讀：`ARCHITECTURE.md` 的 Single Page Preview、`GOTCHAS.md` 的 details pseudo-element 條目、`VERIFY.md` 的 Preview Ctrl+C。
- 相關檔案：`.codex/codex/tmp/20260610-233544-ctrlc-details-final-preview-build-retry.meta.json`、`.codex/codex/artifacts/details-summary-after.png`。

## 2026-06-10 23:09：Slash pipe 標題與 details 樣式優化

- 任務類型：feature
- 修改範圍：`tools/admonition_title_hook.py`、`tools/source_jump_hook.py`、`theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/ARCHITECTURE.md`、`.codex/codex/VERIFY.md`、`.codex/codex/log.md`。
- 主要決策：支援 `/// danger|重點` / `/// danger | 重點` 轉成 `Danger | 重點`；`/// details|摺疊` 保留給 pymdownx details，並以暗色近黑、cyan 細線、精簡 summary 標題列改善外觀。
- 驗證結果：`py_compile` 通過；hook smoke test 通過；`details-pipe-admonition-build` full build returncode 0；Playwright 截圖確認 details 關閉與展開狀態。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的「Slash admonition 與 details 摺疊語法」、`VERIFY.md` 的「Slash admonition 與 details block」。
- 相關檔案：`.codex/codex/tmp/20260610-225556-details-pipe-admonition-build.meta.json`、`.codex/codex/artifacts/details-style-playwright.png`、`.codex/codex/artifacts/details-style-playwright-open.png`。

## 2026-06-10 22:43：Slash admonition 簡寫語法支援

- 任務類型：feature
- 修改範圍：`tools/admonition_title_hook.py`、`tools/source_jump_hook.py`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/ARCHITECTURE.md`、`.codex/codex/VERIFY.md`。
- 主要決策：新增 `/// danger "重點"` 到結尾 `///` 的未縮排簡寫語法，渲染前轉成既有 `!!! danger "Danger | 重點"`；只處理已知 admonition 類型，保留 `/// collapse-code`。
- 驗證結果：`py_compile` 通過；inline 轉換、Source Jump 行號、Python-Markdown admonition smoke test 通過；`slash-admonition-build` full build returncode 0。
- 尚未完成：未新增實際筆記範例檔，避免污染內容。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Slash admonition 簡寫語法、`ARCHITECTURE.md` 的 Slash admonition shorthand、`VERIFY.md` 的 Slash admonition。
- 相關檔案：`.codex/codex/tmp/20260610-224150-slash-admonition-build.meta.json`。

## 2026-06-10 18:53：Admonition 自訂標題加入分隔線

- 任務類型：feature
- 修改範圍：`tools/admonition_title_hook.py`、`tools/source_jump_hook.py`、`.codex/codex/ARCHITECTURE.md`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/VERIFY.md`。
- 主要決策：自訂 admonition 標題統一渲染為 `<Type> | <Title>`，例如 `!!! danger "記下來"` 變成 `Danger | 記下來`；已帶 `Danger |`、舊式 `Danger 記下來` 或 `Danger: 記下來` 也會正規化，未自訂標題仍只顯示 `Danger`。
- 驗證結果：`admonition_title_hook.py` 與 `source_jump_hook.py` 編譯通過；樣本測試確認 plain/already-pipe/old-space/old-colon/default 行為；完整 build returncode 0；輸出 HTML 已出現 `Danger | 重點`、`Danger | bit 數`。
- 尚未完成：沒有。
- 下次建議先讀：`ARCHITECTURE.md` 的 Admonition 標題與 `VERIFY.md` 的 admonition 標題驗證。
- 相關檔案：`.codex/codex/tmp/20260610-185219-admonition-title-pipe-build.meta.json`、`site/blog/2024/02/06/mkdocs-語法.html`、`site/md/114-2/科技_計算機結構/期末考複習-ch3.html`。

## 2026-06-10 16:47：Danger block 內文字級改回正文大小

- 任務類型：docs
- 修改範圍：`theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/VERIFY.md`。
- 主要決策：admonition / details 容器改為繼承正文 font-size / line-height；`.admonition-title` 與 `summary` 單獨維持 0.88em，讓標題列精簡但內文不再像註腳。
- 驗證結果：完整 build returncode 0；Chrome/Playwright 量測 `期末考複習-ch4-1.html` 中 danger 內文 `PC+4` 為 16px、一般正文為 16px、Danger 標題列為 14.08px。
- 尚未完成：沒有。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`VERIFY.md` 的 admonition 樣式驗證條目。
- 相關檔案：`.codex/codex/tmp/20260610-163202-admonition-body-font-build.meta.json`、`.codex/codex/tmp/admonition-font-serve-6.out.log`。

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
