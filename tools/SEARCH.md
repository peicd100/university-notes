# 中文全文搜尋

保留 MkDocs Material 9.7.1 的搜尋介面、章節索引、分享、鍵盤與 instant navigation，不再讓一般查詢依賴 jieba 斷詞。無外部搜尋服務或 API key，也不讀原始 Markdown 或額外建立一份公開全文索引。

## 用法

| 輸入 | 行為 |
| --- | --- |
| `會第一直覺用一` | 任意中文連續片段；命中「雙邊緣觸發 → 解題」的內文 |
| `雙邊緣 posedge` | 所有關鍵字都必須存在；可結合文章名稱與章節內文 |
| `ＡＬＷＡＹＳ 第一直覺` | 全形／半形、英文大小寫不影響匹配 |
| `"always @(posedge clk)"` | 引號內視為一個必須連續出現的片段 |
| `posedge*`、`title:always`、`verlog~1` | 明確的 Lunr wildcard／欄位／英文編輯距離語法，交給原本 Material worker |

- 一般查詢的空格分詞採 **AND**，不是只找到其中一個詞就算匹配。範圍是同一章節的內文／標題／tags，加上該文章的名稱，不把不同章節的零散命中拼成假結果。
- 標題、tags 與連續片段優先於零散內文命中；結果依文章分組，摘要靠近命中處並高亮，按 Enter 可直接跳到最高分章節。
- 支援貼上、手機 `input` 與中文 IME 組字完成。組字中的 Enter／方向鍵不會誤選搜尋結果；不阻止瀏覽器的原生輸入法動作。
- 摘要是安全跳脫後的純文字；程式碼會以緊湊文字呈現，原頁的程式碼與 Markdown 不變。

## 實作與維護

- `theme/assets/pymdownx-extras/search-core.js`：從既有索引去除 jieba 零寬分隔，HTML → 純文字、NFKC／空白／大小寫正規化；substring／AND、加權排序、安全摘要與 Material 結果分組。
- `theme/assets/javascripts/workers/search-peicd.js`：相容 Material 的 `SETUP=0 / READY=1 / QUERY=2 / RESULT=3`。一般查詢在 worker 內執行；明確進階語法及沒有 literal 命中的英文查詢才啟動原版 Lunr worker。英文 fallback 只保留完整詞命中；中文片段沒有結果時不退回不完整斷詞結果。
- `theme/assets/pymdownx-extras/search-lazy-guard.js`：既有 lazy 行為、same-origin／GitHub Pages 子路徑 worker 選擇及 input／IME bridge。介面仍只有 Material 一個 owner。
- `theme/main.html`：guard 必須在 Material bundle **之前**載入。
- `search/search_index.json` 仍由既有 `search`／`encryptcontent` plugins 產生與過濾。`search.exclude` 與預設 encrypted 頁面不進公開索引；本次沒有改動解密或存取政策。
- 搜尋首次互動或 `?q=` 分享查詢才下載索引／worker；instant navigation 重用同一份搜尋。原版 worker URL 從 Material 的當前 URL 傳入，不硬編碼官方 hash。
- 修改 runtime 時同步更新 `theme/main.html`、guard 的 `SEARCH_VERSION` 及新 worker 的版本 fallback。升級 Material 後重跑 protocol／browser regressions。

## 驗證

沿用 Conda `mkdocs`；Node 用於引擎與瀏覽器測試。Playwright／Chromium 可透過 `PLAYWRIGHT_MODULE`／`CHROMIUM_EXE` 指向既有安裝，不需重新下載。

```bat
node --test tools/test_search.cjs
conda run -n mkdocs python -m unittest tools.test_search_index -v
conda run -n mkdocs python -m mkdocs build -f mkdocs.yml --clean
node tools/test_search_browser.cjs
```

Browser test 以 `site/` 為預設，可用 `SEARCH_SITE_DIR` 指定 staging build、`SEARCH_ARTIFACTS_DIR` 指定報告／截圖目錄。內建測試 server 模擬 Pages 子路徑並將 sitemap origin／port 改成測試 server（等同 serve），不改建置產物。包括實際章節／鍵盤、paste／IME 去重、手機搜尋 panel、分享、真正的 instant navigation、lazy requests 與原版 Lunr fallback。

`mkdocs.preview.yml` 原本使用 `plugins: []` 且只選一篇筆記，**不能**用它驗證全站搜尋；請用正式 `mkdocs.yml` 的 build／serve。網站發布仍走既有流程，本次不自動 commit／push／部署。

## 邊界

- 這是文字檢索，不是 AI 問答／同義詞搜尋；沒有自動繁簡轉換或中文錯字容錯。若有需求，可獨立增加明確可驗收的繁簡／容錯層。
- 現在採 worker 內正規化全文掃描，不增加大型 n-gram 網路索引。5819 個章節的本機 Node 樣本中，指定片段約 6 ms、常見單字查詢約 38 ms；這不含下載／UI 時間，也不代表所有手機。
- 索引量顯著增加時可換成 n-gram 候選查找，Material protocol 與 UI 不需重寫。
- 已驗證 Chromium 桌機／390px 手機 viewport；其他瀏覽器與實體中文輸入法仍可補驗（目前 IME 使用原生 DOM composition events 模擬）。
- 根目錄 `docs/index.md` 既有轉址會丟掉 query parameters；分享測試使用實際文章頁，未修改筆記或根目錄轉址。
