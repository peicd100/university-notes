安裝
⭐ 步驟 1：更新套件清單

sudo apt update

⭐ 步驟 2：安裝 Vim

sudo apt install vim

⭐ 步驟 3：確認有沒有安裝成功

vim --version

如果有成功，你會看到一大串版本資訊。Ubuntu 社群文件也提到，安裝完成後可以直接在終端機輸入 vim 啟動；也可以用 vimtutor 練習基本操作。

安裝完怎麼開檔案

例如你要編輯作業檔：

vim endian.c

使用



1. 開檔 vim endian.c
2. 按下 “i“ ，進入編輯模式 (左下角會寫 -- Insert -- )
3. 編輯完成之後按下 esc 回到一般模式
4. 輸入 “:w” 按下 enter ，代表 write（寫入檔案）
5. 輸入 “:q” 按下 enter 代表輸入退出

也可已輸入 “:wq” 儲存又退出
執行 cpp
編譯
gcc endian.c -o endian


1. gcc
這是 GNU C Compiler（GNU C 編譯器） 的指令名稱。
它負責把你的 .c 原始碼處理成最後可以執行的程式。GCC 官方文件說明，gcc 會接受選項與檔名作為操作對象。
2. endian.c
這是你的 source file（原始碼檔案）。
副檔名 .c 告訴 GCC：這是一個 C 程式來源檔，所以要用 C 的規則去編譯。GCC 官方文件明確說它接受檔名作為 operand（操作數）。
3. -o endian
這裡的 -o 是 output file（輸出檔名） 選項。
意思是：把編譯後的結果命名成 endian。如果你不寫 -o，GCC 通常會用預設名稱 a.out。這是 GCC 的標準行為。

執行
./endian

1. . 是什麼
. 代表 current directory（目前目錄）。
在 Unix/POSIX 語意裡，. 就是你現在所在的資料夾。很多系統工具與手冊都用 . 表示目前路徑。
2. /
這只是路徑分隔符號。
所以 ./endian 合起來就是：
目前資料夾裡的 endian
3. endian
這就是你剛剛用 gcc ... -o endian 產生出來的可執行檔名稱。


為什麼不能直接打 endian，要打 ./endian

這是很多新手最容易卡住的點。

在 Bash shell 裡，當你輸入一個指令名稱時，shell 通常會到 PATH 環境變數列出的目錄裡找，例如 /usr/bin、/bin 等，而通常不會自動搜尋目前目錄。因此你要明確寫出路徑 ./endian，告訴 shell：

我要執行的是「目前資料夾裡的檔案」，不是系統指令。

生活化一點講：

你打 ls：系統去固定的工具櫃找 ls

你打 ./endian：你是在說「請拿我桌上這個檔案來執行」
