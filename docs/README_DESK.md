# PEICD100

## 每次寫完
```
activate mkdocs_desk
mkdocs gh-deploy
git add .
git commit -m "PEICD100"
git branch -M main
git push -u origin main

```
























































## 預覽
```



activate mkdocs_desk
p              docs\md\114-2\電機_作業系統\ch 4.md





```
```
activate mkdocs_desk
mkdocs serve

```
```
activate mkdocs_desk
mkdocs serve -f mkdocs.preview.yml --dirty

```

## 單頁預覽快捷指令
```bat
activate mkdocs_desk
.\preview     docs\md\114-2\電機_作業系統\ch 4.md
```
- 可接受 `docs\...` 或 `md\...` 路徑。
- 如果目前終端是 PowerShell，請用 `.\preview ...`；若是 `cmd`，可直接用 `preview ...`。
- 指令會自動更新 `mkdocs.preview.yml` 內的 preview 目標，然後啟用 `mkdocs_desk`，最後以 `python -m mkdocs serve -f mkdocs.preview.yml --dirty` 啟動預覽。


# 環境安裝指令

## 只安裝環境

```
conda create -n mkdocs_desk python=3.11 -y
activate mkdocs_desk
conda install pip -y 
conda install -n mkdocs -y -c conda-forge ffmpeg pyside6
pip install -r requirements.txt
conda install git -y

```

## 安裝 cuda

```
conda install cuda -c nvidia -y
```

## 使用 git
```
git clone https://github.com/peicd100/peicd100.github.io.git
git init
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/peicd100/peicd100.github.io.git
git push -u origin main
mkdocs gh-deploy

```


# git 指令

## 初始化
```
git init
git remote add origin https://github.com/peicd100/peicd100.github.io.git

```
## 推送到main
```
git add .
git commit -m "PEICD100"
git branch -M main
git push -u origin main

```
## 推送到網頁
```
mkdocs gh-deploy

```
## 還原成 GitHub 最新資料
```
git fetch origin && git switch main && git reset --hard origin/main && git clean -fd && git status

```
## 查看儲存庫
```
git remote -v

```
## 克隆儲存庫
```
git clone https://github.com/peicd100/peicd100.github.io.git

```

## 刪除環境

```
conda env remove -n mkdocs_desk -y
```
