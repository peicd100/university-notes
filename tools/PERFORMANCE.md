# 網站效能與驗證

## 環境

沿用 Conda `mkdocs`。新依賴已列在根目錄 `requirements.txt`：

```bat
conda activate mkdocs
python -m pip install "Pillow>=10,<13" "tinycss2>=1.2,<2"
```

## 行為

- 原始 Markdown 與原圖不改動。建置時替換為較小的 lossless WebP；動畫 PNG、遠端圖片、不支援格式及不划算的轉換保留原檔。
- Logo 使用 96px WebP、favicon 使用 32px PNG，均為衍生檔。
- 圖片快取在 `.cache/site-images/`，以輸入 bytes、Pillow/WebP encoder 版本與參數識別；重用前檢查 metadata 與 output SHA-256。不要在每次預覽前刪除 `.cache/`。
- 自訂 CSS 在建置時合併，保留規則順序、不同 media scope 與 fallback；僅移除註解、多餘空白與較早的完全相同規則。CSS URL 使用內容 Hash。
- MathJax 使用單一 controller：可見內容優先，小批次排版，閒置時補齊全文。一般公式獨立轉換；macro、label/ref 與自動編號等語意公式保留 shared-document 順序。
- 同頁 anchor 保留已排版的 DOM；真正換頁仍使用 Material instant navigation。
- 右側 TOC／Danger（含手機目錄）鏡像正文已排版的標題公式，不重新處理 TeX。標題公式會在原 controller queue 優先排版；forward refs 的後續更新會同步。鏡像移除重複 IDs、內層連結與額外 Tab stops，保留 Assistive MathML。
- Source Jump 只在 `serve` 索引原文，依內容 Hash 重用；變更或刪除來源會失效，重建時以完整新 map 原子替換。

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
