# PEICD100

## 安裝環境

```
conda create -n mkdocs python=3.11 -y
activate mkdocs
conda install pip -y 
conda install -n mkdocs -y -c conda-forge ffmpeg pyside6
pip install -r requirements.txt
conda install git -y

```

## 每次寫完推送

```
activate mkdocs
mkdocs gh-deploy
git add .
git commit -m "PEICD100"
git branch -M main
git push -u origin main

```
