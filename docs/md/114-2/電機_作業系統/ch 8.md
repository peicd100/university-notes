## ⭐Memory Management Background + Base and Limit Registers — 作業系統為什麼要管記憶體？

講義位置：PDF viewer page 3 ~ PDF viewer page 4

### 1. 這個知識點在解決什麼問題？

一個程式要執行，不能只待在 disk(磁碟) 裡；它必須被 brought into memory(載入記憶體)，放進某個 process(行程) 的記憶體空間中，CPU 才能執行它。講義也明確說，CPU 能直接存取的主要是 registers(暫存器) 和 main memory(主記憶體)，disk 不是 CPU 可直接拿來執行指令的地方。

生活化例子：
你可以把 disk 想成倉庫，main memory 想成工作桌，registers 想成你手上正在拿的工具。CPU 工作時不能每一步都跑去倉庫翻東西，所以程式和資料要先搬到工作桌附近。

---

### 2. Memory Management(記憶體管理)第一個核心矛盾：快、不夠快、又不能亂碰

講義 page 3 其實在建立三個限制：

1. Program must be brought into memory
   程式要執行，必須先從 disk 進入 memory。

2. Main memory can take many cycles
   CPU register 很快，可能一個 clock cycle 就能存取；main memory 慢很多，會造成 stall(停等)。

3. Protection of memory required
   OS 必須保護記憶體，避免一個 user process(使用者行程) 亂改別人的記憶體或 OS kernel(核心) 的資料。

所以 Chapter 8 不是只在問「資料放哪裡」，而是在問：

**如何讓每個 process 以為自己有一塊安全可用的記憶體，同時讓 CPU 能有效率地把 logical address(邏輯位址) 轉成真正的 physical address(實體位址)，又不能讓 process 越界亂碰？**

---

### 3. Base and Limit Registers(基底與界限暫存器)：最直覺的記憶體保護法

Base Register(基底暫存器) 可以想成「這個 process 的合法記憶體起點」。
Limit Register(界限暫存器) 可以想成「這個 process 合法使用的範圍大小」。

講義 page 4 寫到：一對 base and limit registers define the logical address space，而且 CPU 必須檢查 user mode 產生的每一次 memory access 是否介於 base 與 limit 所允許的範圍內。

用生活例子說：
假設學校借你一間實驗室，你可以用「第 30000 號櫃子開始，最多用 12000 格」。那麼：

* base = 30000
* limit = 12000
* 你能碰的範圍大約就是 30000 到 41999
* 你想碰 42000 以外，就違規，OS 要擋下來

---

### 4. 核心流程：CPU 每次記憶體存取都要過守門員

Base/Limit 的精神不是「相信程式自己守規矩」，而是硬體協助 OS 做檢查。

```mermaid
flowchart LR
    A["Process in user mode<br>CPU generates logical address LA"] --> B{"Is LA within<br>0 <= LA < limit?"}
    B -- "No" --> E["Trap / addressing error<br>交給 OS 處理"]
    B -- "Yes" --> C["Translate address<br>PA = base + LA"]
    C --> D["Allow memory access<br>Memory uses physical address PA"]
```

重點是：
**user mode 的 process 每次要碰 memory，都要先確認沒有越過自己的合法 logical address space(邏輯位址空間)。**

也就是：

**先檢查 logical address，再加 base 變 physical address。**

1. `LA < limit ?`
2. 若合法：`PA = base + LA`
3. 若不合法：trap to OS
    

---

### 5. 最容易混淆的地方

第一個常見錯法是把 base 當成 limit。
Base 是起點，limit 是範圍或長度；不是終點。

第二個常見錯法是以為 CPU 直接相信 process 給的位址。
不對。講義強調 CPU 必須檢查 user mode 的每次 memory access。

第三個常見錯法是忘記這是「保護機制」，不是「效能最佳化機制」。
Base/Limit 的主要目的，是防止越界與互相破壞；但之後的 paging、TLB、cache 才會更明顯牽涉位址轉換與效能。

---

### 6. 中文理解版

Memory Management(記憶體管理)的起點是：程式必須載入主記憶體才能執行，但記憶體速度、空間與保護都有問題。Base and Limit Registers(基底與界限暫存器)是一種基本保護方法，用 base 記錄合法記憶體起點，用 limit 限制可用範圍；CPU 在 user mode 每次記憶體存取時都要檢查是否越界。

### 7. English Exam Version

Memory management is needed because a program must be loaded from disk into main memory before it can run, while the operating system must also ensure efficient access and memory protection. Base and limit registers provide a simple protection mechanism: the base register stores the starting physical address of a process, and the limit register defines the valid range of logical addresses. Every memory access generated in user mode must be checked to ensure that it falls within this allowed range.

### 8. 最短記法

**Program must be in memory to run. Base = start, Limit = legal range, CPU checks every user-mode memory access.**



### 為何叫做 logical ， logical 本身意義是什麼，和這裡有啥關聯

1.`logical` 本身的意思
    

`logical` 原本是 `logic(邏輯)` 的形容詞，基本意思是「跟推理規則、形式規則、抽象結構有關」。Merriam-Webster 對 `logical` 的定義包含「relating to logic」以及「formally true or valid」這類意思，也就是它不只是在說「合理」，而是在說「依某套規則成立」。[梅里亞姆-韋伯斯特詞典](https://www.merriam-webster.com/dictionary/logical?utm_source=chatgpt.com)

所以 `logical` 在電腦科學裡常常帶有這種語感：

**不是物理世界中的真實位置，而是某個抽象模型、規則系統、程式視角裡成立的位置或關係。**

---

2.跟 `logical address(邏輯位址)` 的關聯
    

講義說，CPU 產生的位址叫 `logical address(邏輯位址)`；memory unit(記憶體單元) 看到、真正送進 memory-address register 的位址叫 `physical address(實體位址)`。

講義\_chapter 8\_20240520

所以這裡的 `logical` 不是在說「這個 address 很合理」，而是在說：

**這個 address 是 process / program 的抽象位址規則裡的編號。**

也就是：

- `logical address`：程式世界裡的位址。
    
- `physical address`：RAM 硬體世界裡的位址。
    

社群問答裡也常用同一種說法：CPU 產生的 address 稱為 logical address，memory unit 看到的 address 稱為 physical address；若是 execution-time binding，兩者會不同，並透過 MMU 做轉換。[Stack Overflow](https://stackoverflow.com/questions/3697729/difference-between-logical-addresses-and-physical-addresses?utm_source=chatgpt.com)



### 錯題

!!! danger "PEICD100"

    #### 1

    ##### Q:
    Explain why a program must be brought from disk into main memory before it can be executed by the CPU. Your answer must mention what the CPU can directly access.

    ##### 我寫的:
    必需要在 main memory 是因為如果在 disk 太慢了。

    ##### ANS:
    你說「disk 太慢」方向對，但考試版要更精準：CPU 不能直接從 disk 執行程式，CPU 可直接存取的是 registers(暫存器) 與 main memory(主記憶體)；disk 慢是原因之一，但不是唯一關鍵。講義 page 3 明確寫到程式必須從 disk 載入 memory 才能執行，而且 CPU 可直接存取的 storage 是 main memory 和 registers。

    #### 2

    ##### Q:
    Suppose a process has base = 30000 and limit = 12000. For each logical address, determine whether the access is legal or illegal, and briefly explain why:
    a. 0
    b. 11999
    c. 12000
    d. 15000


    ##### 我寫的：
    允許的範圍： 30000~41999，共 12000，都不合法，因為不在範圍30000~41999中


    ##### ANS：
    第 2 題錯在哪裡？
        

    你寫：

    「允許的範圍：30000～41999，共 12000，都不合法，因為不在範圍 30000～41999 中」

    這句其實抓到 **physical memory range(實體記憶體範圍)**，但題目問的是 **logical address(邏輯位址)**。

    在 base/limit 模型中：

    - `base = 30000`：這個 process 在 physical memory 的起點。
        
    - `limit = 12000`：這個 process 的 logical address 合法範圍大小。
        
    - 合法的 `logical address` 是 `0 ~ 11999`。
        
    - 轉成 physical address 時才加 base。
        

    所以正確判斷是：

    | logical address | 是否合法 | physical address | 原因 |
    | --- | --- | --- | --- |
    | 0 | ✅ legal | 30000 | 0 < 12000 |
    | 11999 | ✅ legal | 41999 | 11999 < 12000，是最後一格合法位址 |
    | 12000 | ❌ illegal | 不轉換 | 12000 不小於 limit，剛好越界 |
    | 15000 | ❌ illegal | 不轉換 | 15000 超過 limit |

    更精準地說：  
    **logical address 先檢查是否 `< limit`；合法後才做 `physical address = base + logical address`。**

    這也和講義 page 6 的說法一致：`local address` 必須與 `base register` 相加才會得到 `physical address`；page 7 則定義 CPU 產生的是 logical address，memory unit 看到的是 physical address。

    講義\_chapter 8\_20240520

    
    外部課程講義也用同樣定義：logical address 是 CPU 產生，也叫 virtual address；physical address 是 memory module 看到的位址。[ocw.nthu.edu.tw](https://ocw.nthu.edu.tw/ocw/upload/141/news/%E5%91%A8%E5%BF%97%E9%81%A0%E6%95%99%E6%8E%88%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1_chap%EF%BC%908%EF%BC%BFOperating%20System%20Chap8%20Memory%20Management%EF%BC%BF.pdf?utm_source=chatgpt.com) 社群討論裡常見的混淆也正是「程式看到的位址」和「RAM 實際位置」混在一起。
    
    


## ⭐Address Binding — 程式的位址到底什麼時候變成真正的記憶體位置？

講義位置：PDF viewer page 5 ~ PDF viewer page 7

### 1. 這個概念在解決什麼問題？

程式寫出來時，裡面會有很多 address(位址)：例如某個變數在哪裡、某段 code 從哪裡開始執行。

但問題是：

**程式還沒真的執行前，我們不一定知道它會被放到 main memory(主記憶體) 的哪個位置。**

所以 `Address Binding(位址連結)` 在問：

**程式中的位址，要在什麼時候綁定成真正可執行／可存取的記憶體位置？**

講義 page 5 直接定義：Address Binding 是決定程式起始位置，也就是程式要在記憶體哪個地方開始執行。

---

### 2. 三種 Binding Time(連結時機)

### 2.1 Compile Time Binding(編譯時間連結)

在 compile time(編譯時間)，compiler(編譯器) 就決定程式將來執行的起始位址。

直覺例子：
像你在搬家前就指定「我一定要住 5000 號房」。如果到時候 5000 號房已經有人住，你就麻煩了。

缺點是：
如果那個位址被其他程式佔用，或之後想換位置，就要 recompile(重新編譯)。講義 page 5 也明確列這個缺點。

---

### 2.2 Load Time Binding(載入時間連結)

在 load time(載入時間)，由 linking loader / linkage editor 決定程式載入 memory 的起始位置。

直覺例子：
你不是一開始就指定房號，而是到飯店 check-in 時，櫃台看哪間空房再安排你。

優點是比 compile time 彈性高。
但缺點是：程式一旦載入並開始執行，起始位址仍不能在執行期間改變。講義 page 5 也說，load time binding 支援 relocation(重定位)，但程式執行期間仍不可以改變起始位址。

---

### 2.3 Execution Time Binding(執行時間連結)

在 execution time(執行時間)，OS 可以在程式執行期間動態決定或調整程式起始位置，所以又稱 `dynamic binding(動態連結／動態位址綁定)`。

這需要額外硬體支援：`MMU(Memory-Management Unit，記憶體管理單元)`。

講義 page 6 說，execution time binding 由 OS 動態決定，需要 MMU；`Base Register(基底暫存器)` 記錄目前程式起始位址，`Local Address(區域位址)` 要和 base register 相加才會得到 physical address。

---

### 3. 為什麼 page 7 要接在 Address Binding 後面？

因為如果位址可以被轉換，我們就要分清楚兩種位址：

1. `Logical Address(邏輯位址)`：CPU / process 產生的位址。
2. `Physical Address(實體位址)`：memory unit 真正看到、真正拿去存取 RAM 的位址。

講義 page 7 明確定義：CPU 產生的位址通常稱為 logical address；記憶體單元看到的位址，也就是載入到 memory-address register 的數值，稱為 physical address。

所以 page 5～7 其實在講同一條故事：

**程式的位址何時決定？如果執行時才決定，就會出現 logical address 到 physical address 的轉換問題。**

---

### 4. 核心流程圖

```mermaid
flowchart LR
    A["Program uses address<br>程式中的位址"] --> B{"When is the address<br>bound to memory?"}
    B --> C["Compile time<br>編譯時就固定"]
    B --> D["Load time<br>載入時決定"]
    B --> E["Execution time<br>執行時動態決定"]
    E --> F["MMU translates<br>logical address to physical address"]
    F --> G["Memory unit accesses<br>physical address"]
```

---

### 5. 最短記法

`Address Binding` = **程式位址什麼時候變成記憶體位置**。

三種時機：

1. `Compile time`：編譯時固定，最不彈性。
2. `Load time`：載入時決定，執行期間不能改。
3. `Execution time`：執行時動態決定，最彈性，需要 MMU，效能較差。



### "Load time：載入時決定，執行期間不能改。"載入是指什麼時候

程式已經編譯好之後，準備被放進 main memory(主記憶體)、建立成 process(行程)、即將開始執行的那段時間。


## ⭐Dynamic Loading / Dynamic Linking — 程式一定要一開始全部載入嗎？

講義位置：PDF viewer page 8 ~ PDF viewer page 11

### 1. 這個概念在解決什麼問題？

前面 `Load-time binding(載入時間連結)` 比較像是在問：

**整個程式這次從記憶體哪裡開始執行？**

現在 `Dynamic Loading(動態載入)` 和 `Dynamic Linking(動態鏈結)` 問的是另一件事：

**程式裡不是每段 code、每個 library 都一定會用到，那可不可以等真的用到再載入或連結？**

生活化例子：
你去考試不會把整個書櫃搬進考場，你只會帶這次可能會用的筆記。Dynamic Loading / Linking 的精神也是：**不要一開始把所有東西都放進 main memory，等真的需要時再處理。**

---

### 2. Dynamic Loading(動態載入)

`Dynamic Loading(動態載入)` 是：

**主程式先在 main memory 執行；某個 subroutine(副程式) 真的被呼叫時，才把那個副程式從 disk / auxiliary storage 載入 main memory。**

講義 page 8 說，Dynamic Loading 是主程式呼叫副程式時，才將副程式由輔助記憶體載入主記憶體。

直覺例子：

你寫一個程式有：

1. 正常流程。
2. 錯誤處理流程。
3. 罕見功能流程。

如果錯誤處理流程 99% 時候不會用到，那一開始就把它載入 memory 可能浪費空間。Dynamic Loading 就是等真的發生錯誤、真的呼叫那段 code 時，再把它載入。

---

### 3. Dynamic Loading 的優缺點

優點：節省 `main memory(主記憶體)` 空間。講義 page 9 明確列出優點是節省 main memory 空間。

缺點：`programmer(程式設計者)` 負擔較大，因為要自己規劃什麼時候載入，而且可能拖長執行時間。講義 page 9 也說缺點是 programmer 的負擔、拖長執行時間。

最短理解：

**Dynamic Loading 省 memory，但比較麻煩，且用到時會有額外載入成本。**

---

### 4. Linking(鏈結)是什麼？

`Linking(鏈結)` 是把 library(函式庫) 或 object file(目的檔) 接到程式裡，讓程式可以呼叫那些 library code。

講義 page 10 說，函式庫是向其他程式提供服務的 code；library linking 是把一個或多個函式庫包括到程式中，分成 `Static Linking(靜態鏈結)` 與 `Dynamic Linking(動態鏈結)`。

---

### 5. Static Linking(靜態鏈結)

`Static Linking(靜態鏈結)` 是：

**在產生 executable file(可執行檔) 時，就把 library 的內容複製／整合進可執行檔。**

優點是執行時比較直接。
缺點是 executable file 會變大，需要更多系統資源，載入記憶體時也比較花時間。講義 page 10 明確列出靜態連結最大缺點是可執行檔太大，需要更多系統資源，裝入記憶體也消耗更多時間。

生活化例子：
你把整本工具書影印進自己的筆記本，筆記本就會很厚。


#### executable file 是啥

executable file 裡面大概有什麼？
    

你可以把 executable file 想成「已經打包好的程式搬家箱」。

裡面通常包含：

1. `text section / code section(程式碼區段)`  
    已經變成 CPU 能執行的 machine instructions(機器指令)。講義 Chapter 3 也說 text section contains the executable code，並且是從 program's executable file mapped into memory。
    
    講義\_chapter 3\_20240318
    
2. `data section(資料區段)`  
    已初始化的 global/static variables。
    
3. `metadata(中繼資訊)`  
    告訴 OS loader 怎麼把這個檔案放進 memory，例如入口點在哪、哪些段要載入、需要哪些 shared libraries。
    
4. `relocation / linking information(重定位／鏈結資訊)`  
    有些 executable file 需要 loader 在載入時修正位址或接上 library。

---

### 6. Dynamic Linking(動態鏈結) / Shared Library(共用函式庫)

`Dynamic Linking(動態鏈結)` 是：

**程式執行期間，某個 library module 真的被呼叫時，才由 OS 的 loader 把它載入 main memory。**

講義 page 11 說，Dynamic Linking 又稱 Shared Library，在程式執行期間，當某個模組真正被呼叫到時，才由 OS 裝載程式將其載入 main memory。

`Shared Library(共用函式庫)` 的重點是：

**多個 process 可以共用同一份 library copy，不需要每個 process 都載入一份。**

講義 page 11 也說，大多數情況下，同一時間多個應用可以使用一個函式庫的同一份拷貝，OS 不需要載入多個實例。


#### library copy 是啥


---

### 7. Dynamic Loading vs Dynamic Linking 差在哪？

| 比較     | Dynamic Loading           | Dynamic Linking              |
| ------ | ------------------------- | ---------------------------- |
| 主要對象   | 程式自己的 subroutine / module | library / shared library     |
| 誰負擔較明顯 | programmer 自己規劃           | OS / loader 支援較多             |
| 核心精神   | 用到副程式才載入                  | 用到函式庫才鏈結／載入                  |
| 目的     | 節省 memory                 | 節省 memory、支援 library sharing |

最容易混淆的地方是：
兩者都很像「用到才載入」，但 **Dynamic Loading 偏向程式模組載入策略；Dynamic Linking 偏向函式庫連結策略**。

---

### 8. 流程圖

```mermaid
flowchart TD
    A["Program starts<br>主程式開始執行"] --> B{"Does it need<br>a subroutine/module?"}
    B -- "Yes, dynamic loading" --> C["Load subroutine<br>from disk to memory"]
    B -- "No" --> D["Do not load it yet<br>節省 memory"]

    A --> E{"Does it call<br>a library function?"}
    E -- "Yes, dynamic linking" --> F["OS/loader loads or links<br>shared library"]
    E -- "No" --> G["Library not loaded yet<br>or not linked yet"]
```

---

### 9. 最短記法

`Dynamic Loading`：**副程式用到才載入。**

`Static Linking`：**函式庫先塞進 executable，檔案大。**

`Dynamic Linking / Shared Library`：**函式庫用到才載入，而且多個 process 可共用同一份。**




## 我覺得好混亂，從 p.3 開始，到底有哪些是被存到 main memory 中，到底有哪些只是映射而已？映射是指複製到 main memory 中嗎？還是只是知道實體位置之後直接讀取實體位置

1. 先把最關鍵的結論講清楚

你現在混亂是正常的，因為這幾頁把三件不同層次的事混在一起講：

1. `Loading(載入)`：把程式碼／資料從 disk 帶進 `main memory(主記憶體)`，或建立之後可被帶進 memory 的關係。
2. `Linking(鏈結)`：把程式裡「我要呼叫某函式」這種 reference(引用)，接到真正的 code / library。
3. `Mapping(映射)`：建立「process 看到的 logical / virtual address」到「實體記憶體位置或 backing file」的對應關係。

最短答案：

**Mapping(映射)本身不是複製。**
它是「建立地址對照關係」。

但：

**如果 CPU 真的要執行或讀取某段 code/data，==那段內容最後一定要在 main memory 裡；如果還不在，就會由 OS 載入進 RAM 後再讀。==**

所以不是：

「知道 disk 實體位置後，CPU 直接讀 disk」。

而是：

「CPU 只能直接讀 main memory/registers；如果資料目前只在 disk，OS 必須先把它帶進 main memory。」講義 page 3 明確說 program must be brought from disk into memory 才能 run，且 CPU 能直接存取的 storage 只有 main memory 和 registers。

---

2. 三個詞分開定義

### 2.1 Loading(載入)

`Loading` 解決的是：

**東西有沒有進入 main memory，或有沒有準備好被放進 process 可用的記憶體空間。**

例如：

* executable file 從 disk 載入 memory。
* dynamic loading 時，副程式被呼叫才從 auxiliary storage 載入 main memory。
* dynamic linking 時，shared library 被需要時才由 OS loader 載入 main memory。

講義 page 8 說 `Dynamic Loading(動態載入)` 是主程式呼叫副程式時，才將副程式由輔助記憶體載入主記憶體；同頁也說所有副程式以 relocatable load format 存在磁碟中，需要時載入主記憶體並更新行程位址表。

---

### 2.2 Linking(鏈結)

`Linking` 解決的是：

**程式裡的函式名稱／外部符號／library reference 要接到哪一段真正的 code。**

例如你的程式呼叫：

`printf()`

Linking 要處理的是：

「`printf` 這個名字到底接到哪個 library 裡的哪段機器碼？」

講義 page 10 說，library linking 是把一個或多個函式庫包括到程式中，分為 static linking 與 dynamic linking。

所以：

**Linking 不是等於載入 main memory。**
它的核心是「接引用」。

---

### 2.3 Mapping(映射)

`Mapping` 解決的是：

**process 看到的 address，要對應到哪個 physical memory 或哪個 file-backed object。**

它不是直接複製。

比較精準地說，mapping 是 OS / MMU 建立一份對照：

| process 看到                 | OS / MMU 對應到                            |
| -------------------------- | --------------------------------------- |
| virtual address 0x400000   | physical frame A，或某 executable file 的某段 |
| virtual address 0x7f...    | shared library 的某段 code                 |
| virtual address stack area | process 自己的 stack pages                 |

Linux `mmap()` 的官方手冊也把 mapping 描述成「在 process 的 address space 建立 mapping」，而且 `munmap()` 是刪除指定 address range 的 mapping；這表示 mapping 是 address-space 關係，不是單純複製檔案。([man7.org][1])

---

3. 你問的核心：映射是複製到 main memory 嗎？

答案要分兩層：

### 3.1 Mapping 本身不是複製

當 OS 說：

「把 shared library map 到 process address space」

意思不是立刻把整個 library 複製一份給這個 process。

它的意思是：

**這個 process 的某段 virtual address，之後如果被存取，應該對應到這個 library 的某些 code/data。**

也就是先建立關係。

---

### 3.2 但真的執行時，內容必須在 main memory

CPU 不能直接從 disk 執行 library code。
所以如果那一頁 library code 還不在 RAM，通常會發生 page fault，OS 再把那一頁從 disk 載入 RAM，更新 page table / mapping，然後 CPU 繼續執行。

因此比較正確的流程是：

```mermaid
flowchart TD
    A["Process accesses virtual address<br>例如呼叫 library function"] --> B{"Is the mapped page<br>already in main memory?"}
    B -- "Yes" --> C["MMU translates virtual/logical address<br>to physical address"]
    C --> D["CPU reads instruction/data<br>from main memory/cache"]
    B -- "No" --> E["Page fault<br>OS loads needed page from disk to RAM"]
    E --> F["Update mapping / page table"]
    F --> C
```

所以不是：

**mapping = 複製。**

也不是：

**mapping = 知道 disk 位置後 CPU 直接讀 disk。**

而是：

**mapping = 建立地址對應；真正被 CPU 使用的 bytes 最後必須在 RAM。**

---

4. 從 p.3 開始逐頁整理：哪些真的在 main memory？哪些只是關係？

### 4.1 PDF viewer page 3：Program must be brought into memory

這頁的意思最硬：

**程式要 run，就必須從 disk 被 brought into memory，而且 placed within a process。**

也就是：

| 東西                        | 是否在 main memory？                 | 說明                                 |
| ------------------------- | -------------------------------- | ---------------------------------- |
| 即將執行的 program code / data | 至少需要的部分要在 main memory            | CPU 只能直接存取 main memory 和 registers |
| disk 上的 executable file   | 不算正在被 CPU 直接執行                   | 它只是來源                              |
| process                   | 需要有 memory image / address space | 才能被 CPU 執行                         |

講義 page 3 的核心就是：CPU 不能直接跑 disk 上的程式檔。

---

### 4.2 PDF viewer page 5～6：Address Binding

這裡不是在講「又載入了什麼新東西」，而是在講：

**程式位址什麼時候決定。**

| Binding 類型               | main memory 發生什麼？         | 重點                                                  |
| ------------------------ | ------------------------- | --------------------------------------------------- |
| `Compile-time binding`   | 執行前已假設固定 physical address | 位址太早固定                                              |
| `Load-time binding`      | 載入 main memory 時決定起始位置    | 載入時 relocation                                      |
| `Execution-time binding` | 執行中靠 MMU 動態轉換             | logical address 加 base / 或透過 MMU 轉 physical address |

page 6 說 `Base Register` 記錄目前程式起始位址，`local address` 要和 base register 相加才會得到 physical address。

所以 page 5～6 重點不是「copy 哪個檔案」，而是：

**process 內部位址要如何變成 main memory 的真正位置。**

---

### 4.3 PDF viewer page 7：Logical Address / Physical Address

這頁純粹是在定義兩種位址：

| 位址                 | 是誰看到？            | 是否代表東西被複製？              |
| ------------------ | ---------------- | ----------------------- |
| `logical address`  | CPU / process 產生 | ❌ 不是複製，只是 process 視角的位址 |
| `physical address` | memory unit 看到   | ❌ 不是複製，是 RAM 真正被存取的位置   |

講義 page 7 說 CPU 產生的是 logical address，memory unit 看到的是 physical address。

所以這頁的「映射／轉換」是地址關係，不是搬資料。

---

### 4.4 PDF viewer page 8～9：Dynamic Loading

這裡就真的有「載入到 main memory」。

| 東西                                   | 一開始在 main memory 嗎？           | 什麼時候進 main memory？         |
| ------------------------------------ | ----------------------------- | -------------------------- |
| 主程式                                  | 是，主程式在 main memory 執行         | program start 時            |
| 很少用到的 subroutine                     | 不一定                           | 被呼叫時才載入                    |
| relocatable load format 的 subroutine | 一開始在 disk / auxiliary storage | 需要時由 loader 載入 main memory |

講義 page 8 說，Dynamic Loading 是主程式執行中，需要呼叫其他程式時，先看它是否已在 memory；如果不是，就呼叫 relocatable linking loader，把所需程式載入 main memory，並更新行程位址表。

這句很重要：

**Dynamic Loading 不是只有 mapping，它真的會在需要時把副程式載入 main memory。**

---

### 4.5 PDF viewer page 10：Static Linking

`Static Linking(靜態鏈結)` 是：

**library code 在產生 executable file 時，就被放進 executable file。**

所以流程是：

```mermaid
flowchart LR
    A["main program object file"] --> C["static linking"]
    B["static library code"] --> C
    C --> D["larger executable file<br>library code already included"]
    D --> E["loaded into process memory<br>when program starts"]
```

所以 static linking 下：

| 東西           | 何時進 executable file？          | 何時進 main memory？          |
| ------------ | ----------------------------- | ------------------------- |
| library code | link time 就放進 executable file | executable 被載入時一起進 memory |

講義 page 10 說 static linking 會讓可執行檔太大，需要更多系統資源，裝入記憶體也消耗更多時間。

---

### 4.6 PDF viewer page 11：Dynamic Linking / Shared Library

`Dynamic Linking(動態鏈結)` 比較微妙，因為它同時有 mapping 和 loading。

講義 page 11 說：當某個模組被真正呼叫到時，才由 OS loader 將其載入 main memory；而多個應用可以使用一個函式庫的同一份拷貝，OS 不需要載入多個實例。

所以：

| 層次                 | 發生什麼                                           |
| ------------------ | ---------------------------------------------- |
| process 視角         | shared library 被 map 到 process 的 address space |
| physical memory 視角 | library code pages 可以只有一份，被多個 process 共用       |
| disk 視角            | library file 原本在 disk 上，例如 `.so` 或 `.dll`      |
| 執行時                | 真的需要的 pages 會在 RAM 中被 CPU 執行                   |

官方 Linux `ld.so` 文件也說 dynamic linker 會找出並載入程式需要的 shared objects，準備程式執行後再執行它。([man7.org][2])

---

5. 用一張總表把「在 memory」和「映射」分清楚

| 章節頁面 | 名詞                               |       是複製／載入到 main memory 嗎？ |              是 mapping 嗎？ | 精準理解                                |
| ---- | -------------------------------- | ---------------------------: | ------------------------: | ----------------------------------- |
| p.3  | program brought into memory      |             ✅ 是，至少必要部分要進 RAM | 也會有 process address space | 不進 memory 不能跑                       |
| p.5  | compile-time binding             |                     ❌ 不是載入重點 |            ❌ 主要不是 mapping | 編譯時就固定位址                            |
| p.5  | load-time binding                |                    ✅ 載入時決定位址 |                  可能建立位址配置 | 載入時 relocation                      |
| p.6  | execution-time binding           |                      不一定搬新資料 |                   ✅ 是地址轉換 | 執行中 logical → physical              |
| p.7  | logical / physical address       |                      ❌ 不是搬資料 |                ✅ 是位址視角／轉換 | CPU 產生 logical，memory 看 physical    |
| p.8  | dynamic loading                  |                 ✅ 需要時真的載入副程式 |               ✅ 也會更新行程位址表 | 用到才載入 subroutine                    |
| p.10 | static linking                   |        executable 載入時一起進 RAM |              較少強調 sharing | library code 已塞進 executable         |
| p.11 | dynamic linking / shared library |   ✅ 需要時 library pages 會進 RAM |         ✅ map 到多個 process | 多 process 共用同一份 physical code pages |
| p.12 | swapping                         | ✅/❌ process 可被搬出 RAM、再搬回 RAM |      可涉及 address space 狀態 | 不在 RAM 就不能直接執行                      |

---

6. 你可以用「三層世界」理解

### 6.1 Disk 世界

這裡放：

* executable file
* shared library file
* relocatable load format 的 subroutine
* backing store / swap area

這些東西躺在 disk 上時，CPU 不能直接執行。

---

### 6.2 Process address space 世界

這是 process 自己看到的世界。

裡面可能有：

* code segment
* data segment
* heap
* stack
* mapped shared library region

注意：
**process address space 裡「看得到」某段 library，不代表每個 process 都真的有一份獨立 physical copy。**

---

### 6.3 Physical memory 世界

這是 RAM 真正存放 bytes 的地方。

裡面可能有：

* process 的 code/data/heap/stack pages
* shared library 的 code pages
* kernel 管理的 page cache
* page frames

真正 CPU 執行時，最後要靠 MMU 把 process 的 logical / virtual address 轉成 physical address，memory unit 才能存取。講義 page 7 的 logical / physical address 定義就是在講這個視角差異。

---

7. 回答你最後那句：「知道實體位置之後直接讀取實體位置」嗎？

要分成 CPU 視角和 OS/MMU 視角。

### 7.1 CPU 執行程式時

程式通常產生 logical / virtual address。
CPU 搭配 MMU 轉成 physical address。
memory unit 用 physical address 存取 RAM。

這部分可以說：

**最後是讀 RAM 的 physical address。**

---

### 7.2 如果內容還在 disk

不能直接讀 disk 的 physical location 來執行。

正確流程是：

1. process 存取某個 virtual address。
2. MMU 查 mapping。
3. 如果 page 不在 RAM，觸發 page fault。
4. OS 從 disk 把對應 page 載入 RAM。
5. 更新 mapping。
6. CPU 重新執行該指令，這次從 RAM 讀 physical address。

所以：

**mapping 可以先存在，但真正使用時資料必須在 RAM。**

---

8. 最短總結

你先記這三句就好：

1. `Loading`：把 code/data 從 disk 帶進 main memory，或讓它可被 process 使用。
2. `Linking`：把函式／library 的名字或引用，接到真正 code 的位置。
3. `Mapping`：建立 process address 到 physical memory / file-backed object 的對應；mapping 本身不是複製，但被 CPU 真正用到的內容最後必須在 RAM。

最重要的修正：

**shared library 不是「放在 process 外面，process 知道實體位置後直接去讀」。**
它是：

**被 map 到每個 process 的 address space；底層 physical memory 裡的 code pages 可以只有一份，由 OS/MMU 讓多個 process 共用。**

第 11 次對話

[1]: https://man7.org/linux/man-pages/man2/mmap.2.html?utm_source=chatgpt.com "mmap(2) - Linux manual page"
[2]: https://man7.org/linux/man-pages/man8/ld.so.8.html?utm_source=chatgpt.com "ld.so(8) - Linux manual page"
