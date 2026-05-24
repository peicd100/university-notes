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
    
    
