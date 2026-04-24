# 多益600

## 專案用途
批次產生複習檔案：把所有 `<數字>.md` 的 `<span class="tts">` 文字轉成 MP4 影片，支援「一次」與「兩次（每句重複兩次）」模式，輸出到 `產生複習檔案`。目前已優化為共用句子快取、`ffmpeg encoder` 單次掃描、兩次模式重用單句音檔，且在 `--mode both` 時共用同一輪 TTS（不再重複合成第二輪），並加入無效 proxy（`127.0.0.1:9`）自動停用、自動略過僅標點句子（避免 `No audio was received`），以及流程結束後 `產生複習檔案/` 只保留 `一次/` 與 `兩次/`。

## 多益600、mkdocs(conda 環境名稱)
- workspace_root_basename: `多益600`
- ENV_NAME: `mkdocs`

## conda環境完整安裝指令(使用'-y'一次複製安裝)
```bat
call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
conda activate base
conda create -n mkdocs -y python=3.13
conda install -n mkdocs -y -c conda-forge ffmpeg
conda run -n mkdocs python -m pip install edge-tts
```

## 程式執行指令
### CLI 互動式設定精靈（預設，推薦）
```bat
call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
conda activate base
conda activate mkdocs
python 紀錄.py
```
- 啟動第一題可選 `全部預設`，選後會直接用預設值執行（不再逐題詢問）。
- 互動式與非互動式 CLI 轉換時都會顯示：`進度百分比 + 目前/預估大小 + CPU/GPU 使用率`。
- 底部固定狀態列每 0.1 秒刷新一次（進度條、CPU、GPU）。
- CPU/GPU 使用率會以橫槓長度條呈現（bar + 百分比）。
- GPU 使用率讀值改為 `max(utilization.gpu, utilization.encoder)`；多 GPU 時取最高值，避免 NVENC 轉檔時數值偏低。
- 每次執行結束（成功或失敗）會自動清理 `產生複習檔案/` 中除了 `一次/`、`兩次/` 之外的所有暫存項目。
- 轉換期間的監控資訊固定在終端最下方 4 行：
  - 第 1 行：進度條（格式如 `⣿⣿⣿⣿⣿⣿⣷⣦⣀⣀⣀⣀⣀⣀⣀ 37%`）
  - 第 2 行：CPU 使用率（橫槓條）
  - 第 3 行：GPU 使用率（橫槓條）
  - 第 4 行：旋轉特效（僅顯示 `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` + `4` 個空格，不含其他文字）

### CLI（不進入精靈，單次執行）
```bat
call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
conda activate base
conda activate mkdocs
python 紀錄.py --workspace . --run-once --rate 1.0 --gap 0.4 --mode both
```

## 打包指令(要打包成完全不依賴環境的.exe，.exe名稱請使用<workspace_root_basename>)
### debug 版（先驗證）
```bat
call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
conda activate base
conda activate mkdocs
pyinstaller --name 多益600 --clean --noconfirm 紀錄.py
```

### noconsole 版
```bat
call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
conda activate base
conda activate mkdocs
pyinstaller --name 多益600 --clean --noconfirm --noconsole 紀錄.py
```

## github 參考指令
### 初始化

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
git remote add origin https://github.com/peicd100/mkdocs.git
git add .
git commit -m "PEICD100"
git push -u origin main
```

### 例行上傳

```bat
git add .
git commit -m "PEICD100"
git push -u origin main
```

### 還原成Git Hub最新資料

```bat
git rebase --abort || echo "No rebase in progress" && git fetch origin && git switch main && git reset --hard origin/main && git clean -fd && git status
```

### 查看儲存庫

```bat
git remote -v
```

### 克隆儲存庫

```bat
git clone https://github.com/peicd100/mkdocs.git
```




## Filename Rules (2026-02-21)
- Per-item files in the `一次` output folder use `_一次` suffix (example: `4_一次.mp4`).
- Per-item files in the `兩次` output folder use `_兩次` suffix (example: `4_兩次.mp4`).
- Merged file names use range format: `<min>~<max>_一次.mp4` and `<min>~<max>_兩次.mp4`.

## Performance Notes (2026-02-21)
- Conversion concurrency is capped (`MAX_FILE_CONCURRENCY=6`) to avoid too many simultaneous jobs causing contention.
- GPU video encoding now uses a dedicated cap (`MAX_GPU_VIDEO_ENCODE_CONCURRENCY=2`) to reduce mid-run NVENC/session failures.
- With sentence cache + audio cache + throttled progress scan, runtime behavior is closer to linear in effective workload.
- During conversion, manifest (`_convert_manifest.json`) stores `<數字>.md` 的 `size + mtime_ns + hash` 與設定簽章，先用 `size + mtime_ns` 快速命中，再決定是否重算 hash。
- During conversion, sentence cache (`_sentence_cache.json`) stores extracted TTS sentences per file fingerprint to avoid repeated markdown parsing.
- When file fingerprints and options are unchanged and outputs exist, conversion is skipped and existing outputs are reused.

## 使用者要求
- 回報「程式執行到一半會自動停止」；要求實測 GPU `once` / `twice` 並修正。
- 2026-02-21 修正：加入 GPU 視訊編碼併發上限，避免多路 NVENC 造成中途中斷。
- 需求改為「不要 GUI，改成 CLI 啟動後先互動設定參數再執行」。
- 互動式 CLI 第一題新增「全部預設」選項，且 CLI 需顯示 CPU/GPU 使用率與進度。
- CLI 狀態列改為固定在最下方，並分成 3 行顯示進度/CPU/GPU。
- CLI 狀態列更新頻率調整為每 0.1 秒刷新一次。
- CLI 狀態列新增第 4 行旋轉特效，並將 CPU/GPU 改為橫槓條顯示使用率。
- 進度條樣式調整為 `⣿⣿⣿⣿⣿⣿⣷⣦⣀⣀⣀⣀⣀⣀⣀ 37%`；旋轉特效行只保留字元本身加 4 個空格。
- GPU 監控改為同時讀取 `utilization.gpu` 與 `utilization.encoder`，並加上短期快取避免高頻刷新造成抖動與誤差。
- 每次執行前後都會掃描並清理 `產生複習檔案/`，最後只保留 `一次/`、`兩次/`。
- 新需求：`產生複習檔案/` 執行後不可殘留其他暫存檔案，只保留 `一次/` 與 `兩次/`。

