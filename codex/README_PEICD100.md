# university notes

## 專案用途
使用 MkDocs Material 維護大學課程筆記、Verilog 筆記與自訂前端互動。專案包含自訂 CSS / JS / hooks，並提供本機 `mkdocs serve` 預覽時的右鍵跳回 Markdown 原文檔功能。

## university notes、mkdocs
- 專案目錄：`y:\github_note\university notes`
- conda 環境名稱：`mkdocs`

## conda 環境完整安裝指令
```bat
conda create -n mkdocs python=3.11 pip git ffmpeg -y
conda activate mkdocs
python -m pip install -r requirements.txt pyinstaller
```

## 程式執行指令
```bat
Y:\conda\envs\mkdocs\python.exe -m mkdocs serve --dirty --livereload
Y:\conda\envs\mkdocs\python.exe -m mkdocs serve -f mkdocs.preview.yml --dirty
Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
vbs_bat\university notes.vbs
preview.bat docs\md\114-2\科技_計算機結構\ch 2.md
p.bat docs\md\114-2\電機_作業系統\ch 4.md
```

## 常用操作補充
- `mkdocs.preview.yml` 目前是單頁 preview 設定，實際預覽頁面以該檔 `nav` / `exclude_docs` 為準。
- `preview.bat` 會自動把輸入的 `docs\...` 或 `md\...` 路徑正規化為 `docs_dir` 相對路徑，更新 `mkdocs.preview.yml` 的 managed 區塊，然後啟用 `mkdocs_desk` 並用 `python -m mkdocs serve -f mkdocs.preview.yml --dirty` 執行 preview serve。
- `p.bat` 是 `preview.bat` 的短命令包裝；PowerShell 可直接用 `.\p docs\md\114-2\電機_作業系統\ch 4.md`。
- `mkdocs.preview.yml` 的 `# preview-target:start` 到 `# preview-target:end` 區塊現在交由工具維護；若要保留額外 preview 設定，請放在區塊外。
- 本機右鍵「開啟原文檔案 / 複製」由 `docs/theme/assets/pymdownx-extras/source-jump.js` 與 `tools/source_jump_hook.py` 配合提供。
- 站點目前保留 Material 內建的頁首 `Back to top`，並額外提供右下角 `Back to bottom` 浮動按鈕；後者由 `docs/theme/partials/scroll-bottom.html`、`docs/theme/assets/pymdownx-extras/scroll-bottom.js` 與 `docs/theme/assets/pymdownx-extras/自定義.css` 共同控制。
- 為了讓 `mkdocs serve --dirty` 也能正常跳檔，`source_jump_hook.py` 會在 `on_files` 先建立 Markdown 索引，再由 `on_page_markdown` 用實際頁面內容覆寫精修。
- 手動驗證若需要保留 `stdout/stderr`，統一用 `tools/run_logged.py`，輸出落在 `codex/tmp/`，不要再把 `.out.log` / `.err.log` 散在專案根目錄。
- 標題錨點與標題內 inline code 的排版目前集中由 `docs/theme/assets/pymdownx-extras/自定義.css` 控制；若標題內使用 backticks 出現版面錯位，先檢查 `h2~h6` 的 flex 規則與 heading code 規則。
- 手寫頁面內目錄若要顯示 `1.`、`2.` 這種序號，不要直接寫 `- 1. ...`；Python-Markdown 會把它解析成巢狀 `<ol>`。目前專案內較穩定的寫法是 `- 1&#46; ...`。
- 若標題內 inline code 需要和文字上下置中，優先用 heading code 的 `align-self: center`，避免再用 `top` 微移去硬修。

## 驗證輸出記錄
```bat
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name pycheck-source-jump -- Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name preview-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name build-scroll-bottom -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
```
- 每次執行都會在 `codex/tmp/` 產生 `*.out.log`、`*.err.log`、`*.meta.json`。
- `codex/tmp/` 只保留 `.gitkeep` 供 Git 追蹤目錄，其他暫存輸出一律忽略。

## 打包方式
```bat
Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
Y:\conda\envs\mkdocs\python.exe -m PyInstaller --noconfirm --clean --onedir --console --name "university notes" --add-data "site;site" tools\project_launcher.py
Y:\conda\envs\mkdocs\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name "university notes" --add-data "site;site" tools\project_launcher.py
```

## github 參考指令
#### 初始化

```bat
(
echo.
echo # PyInstaller
echo dist/
echo build/
echo user_data/
echo # Python-generated files
echo __pycache__/
echo *.py[oc]
echo build/
echo dist/
echo wheels/
echo *.egg-info
echo # Virtual environments
echo .venv
)>> .gitignore
git init
git branch -M main
git remote add origin https://github.com/peicd100/university-notes.git
git add .
git commit -m "PEICD100"
git push -u origin main
```

#### 例行上傳

```bat
git add .
git commit -m "PEICD100"
git push -u origin main
```

#### 還原成Git Hub最新資料

```bat
git rebase --abort || echo "No rebase in progress" && git fetch origin && git switch main && git reset --hard origin/main && git clean -fd && git status
```

#### 查看儲存庫

```bat
git remote -v
```

#### 克隆儲存庫

```bat
git clone https://github.com/peicd100/university-notes.git
```
