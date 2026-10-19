# 網站效能與驗證

## 環境

預覽入口 `s.bat` 使用既有 Conda `mkdocs_desk`。依賴已列在根目錄 `requirements.txt`：

```bat
conda activate mkdocs_desk
python -m pip install "Pillow>=10,<13" "tinycss2>=1.2,<2"
```

## 行為

- 原始 Markdown 與原圖不改動。建置時替換為較小的 lossless WebP；動畫 PNG、遠端圖片、不支援格式及不划算的轉換保留原檔。
- 頁面圖片與功能旗標以單次 HTML 標籤掃描處理，只為實際圖片建立小型 BeautifulSoup 物件，不再替整頁建立／序列化 HTML tree。未閉合、錯置標籤仍交回既有 BeautifulSoup 修補，維持搜尋與後續 hook 的行為；其他正文與屬性保留。
- Logo 使用 96px WebP、favicon 使用 32px PNG，均為衍生檔。
- 圖片快取在 `.cache/site-images/`，以輸入 bytes、Pillow/WebP encoder 版本與參數識別；重用前檢查 metadata 與 output SHA-256。不要在每次預覽前刪除 `.cache/`。
- 自訂 CSS 在建置時合併，保留規則順序、不同 media scope 與 fallback；僅移除註解、多餘空白與較早的完全相同規則。CSS URL 使用內容 Hash。相同完整來源內容重用最近一份記憶體快取，省略重新解析／壓縮；內容變更即失效，不只依檔名或時間判斷。
- MathJax 使用單一 controller：可見內容優先，小批次排版，閒置時補齊全文。一般公式獨立轉換；macro、label/ref 與自動編號等語意公式保留 shared-document 順序。
- 同頁 anchor 保留已排版的 DOM；真正換頁仍使用 Material instant navigation。
- 右側 TOC／Danger（含手機目錄）鏡像正文已排版的標題公式，不重新處理 TeX。標題公式會在原 controller queue 優先排版；forward refs 的後續更新會同步。鏡像移除重複 IDs、內層連結與額外 Tab stops，保留 Assistive MathML。
- Source Jump 只在 `serve` 登記頁面，第一次實際定位該頁時才解析原文，依內容 Hash 重用；每次定位回讀原文，變更或刪除來源會失效。登記表原子替換，多個請求共用鎖，避免重複解析。
- `s.bat` 透過 `tools/serve_site.py` 快取 `Page.render` 的內容、標題、TOC 與連結／anchor 資訊。JSON payload SHA-256、來源全文、設定與 INHERIT、檔案目錄、hook／本機 extension／主題內容、Python／套件版本共同驗證。同一套件的重複發現不影響辨識。metadata、其他 hook、導覽、加密與範本仍執行。每頁只留最新一份快取，原子寫入，損壞就重建。適配 MkDocs 1.6.1；其他版本保守停用。
- Material 9.7.1 的每頁搜尋擷取結果另存 `.cache/preview-search/`，額外檢查當下完整 HTML、metadata、title、TOC、URL 與搜尋設定，重用至新建立的 SearchIndex。搜尋外掛仍處理屬性、增量合併與整站索引輸出。自訂 Jieba 字典、無法穩定表示的 metadata、未知版本或特殊 index 類別沿用原流程；不儲存 plugin／page 物件。
- Markdown 快取位於 `.cache/preview-render/`。`s --fresh` 略過 Markdown 與搜尋重用；strict／verbose 診斷也略過兩者。外部 include 與特殊 Blog 頁面正常重新轉換 Markdown，搜尋若符合驗證仍可重用。這些情況的速度不代表一般快取命中速度。

2026-10-19 整站量測（既有圖片快取保留）：

| 項目 | 本次優化前 | 本次優化後 |
| --- | ---: | ---: |
| 獨立程序重開整站 | 27.14 秒 | 15.76 秒 |
| 一般暖重建 | 約 1 秒 | 0.99 秒 |
| 強制 L04 重建 | 先前約 1.64 秒 | 1.25 秒 |

重開縮短約 42%；110 頁 Markdown、118 頁搜尋擷取命中。圖片 hook 約 10.38 → 5.59 秒。程式變更後建立新的 Markdown／搜尋快取，本次花 39.26 秒；完全沒有圖片快取時還要轉換圖片，不能套用重開數字。每個數字只代表此環境樣本。

預設 `s` CLI（127.0.0.1:8000）另測重開 16.29 秒，兩種快取皆命中，已預先建立預設快取。變更 host／port 會重新驗證 URL 相依結果。

121 頁內容與功能旗標、全部圖片衍生檔 SHA-256、完整 6,035 筆搜尋 JSON 與原流程一致；123 個 HTML、實際 HTTP／4 張圖片、L04 正文／目錄與原文第 9 行定位通過。59 項回歸通過。未修改前端腳本，沿用既有 MathJax／Mermaid／Source Jump 瀏覽器驗證。

## 列印

建議使用 **Ctrl+P / Cmd+P**，controller 會等全文公式完成後才開列印。`window.print()` 同樣會等候。

瀏覽器選單的原生 `beforeprint` 無法等非同步工作；若背景公式尚未完成，請改用快捷鍵或先等全文排版完成。已完成排版的頁面不受影響。

## 最小驗證

```bat
python -m unittest tools.test_site_performance tools.test_latex_bracket_math_hook -v
node --test tools/test_mathjax_refresh.cjs
mkdocs build -f mkdocs.preview.yml
```

側欄 DOM 回歸另用 `node tools/test_toc_math.cjs`（需已安裝 Playwright 與 Chromium；可用 `PLAYWRIGHT_MODULE`／`CHROMIUM_EXE` 指定既有安裝）。涵蓋 script 載入順序、鏡像更新、折疊、anchor、Danger、手機及換頁。

完整發布驗證使用 `mkdocs build --clean`，不要把 `--dirty` 建置當成發布檢查。首次全站建置需建立圖片快取，會比後續增量預覽久；快取與 `site/` 都是可重建產物，不提交 Git。
