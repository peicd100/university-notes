# university notes

## 專案用途
使用 MkDocs Material 維護大學課程筆記與 blog 靜態網站，包含自訂主題、RSS、加密內容、Markdown 延伸功能，以及本機預覽與靜態輸出流程。

## university notes、mkdocs
- 專案資料夾：`y:\github_note\university notes`
- conda 環境名稱：`mkdocs`

## conda環境完整安裝指令
```bat
conda create -n mkdocs python=3.11 pip git ffmpeg -y
conda activate mkdocs
python -m pip install -r requirements.txt pyinstaller
```

## 程式執行指令
```bat
Y:\conda\envs\mkdocs\python.exe -m mkdocs serve --dirty --livereload
Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
vbs_bat\university notes.vbs
```

## 打包指令
先依序測試 debug 版，再打包 noconsole 版：
```bat
Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
Y:\conda\envs\mkdocs\python.exe -m PyInstaller --noconfirm --clean --onedir --console --name "university notes" --add-data "site;site" tools\project_launcher.py
Y:\conda\envs\mkdocs\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name "university notes" --add-data "site;site" tools\project_launcher.py
```

## github 參考指令
說明：這裡我改用實際儲存庫 `university-notes`，而不是 conda 環境名 `mkdocs`，避免把 remote 指到錯的 GitHub 倉庫。

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

## 使用者要求
- 此資料夾已明確視為專案，後續持續維護 `README_PEICD100.md`、`.gitignore`、`專案規格書.md`。
- 此專案使用 `mkdocs` conda 環境。
- Python 專案需要維護 `vbs_bat\university notes.vbs` 與 `vbs_bat\run.bat`，按 `.vbs` 可直接啟動專案。
- 本機隱藏啟動流程：先 `mkdocs build --clean`，再用 `tools\project_launcher.py` 開啟本機靜態站。
- 2026-03-19：已修正手機窄版側欄圖片/文字遮擋與首頁卡片干擾問題。
- 2026-03-19：已修正手機抽屜標題列 `logo icon` 絕對定位導致的站名字樣遮擋問題。
- 2026-03-19：已將 `docs/md/114-2/電機_作業系統/ch2.md` 的所有 Markdown 標題整體下移一級。
- 2026-03-19：已修正 GitHub Pages 首頁跳錯站的問題，並同步修正 `site_url`、`robots.txt` 與 TTS localStorage 命名空間。
