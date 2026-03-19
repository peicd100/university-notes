GPT link ： [https://chatgpt.com/g/g-p-69ad8f226adc8191af1b76cd653135d1-peicd-verilog-hdlbits/c/69b7a014-4f34-83a2-9b5e-07cb003882a3](https://chatgpt.com/g/g-p-69ad8f226adc8191af1b76cd653135d1-peicd-verilog-hdlbits/c/69b7a014-4f34-83a2-9b5e-07cb003882a3)

# Procedural style(程序式寫法) 筆記

這版把三個層級都用**同一個粒度**寫完：

1. **RTL 常用**  
2. **模擬常用**  
3. **知道就好**

每個語法都包含：

* 語法格式  
* 每個位置放什麼  
* 常見資料型態  
* 用途  
* 常用技巧  
* 好看好用的寫法  
* 常見地雷

先給你一句總定義：

**procedural style(程序式寫法)** 是把程式寫在 **procedural block(程序區塊)** 裡，例如 `always`、`initial`，並在裡面用 `if / else if / else`、`case`、`for`、`=`、`<=`、`wait` 等程序式敘述。`always` 是 procedural block；裡面的 statements 會依程序語意執行。IEEE 1364-2005 也把 `if`、`case`、`loop_statement`、`wait`、`fork...join`、`disable` 等都列為 procedural statement。([ChipVerify](https://www.chipverify.com/verilog/verilog-always-block?utm_source=chatgpt.com))

---

## 最重要的一件事

左值通常放 reg

## 先建立總觀念

#### procedural style 跟 `assign` 的差別

* `assign` 是 **continuous assignment(連續指定)**，比較像「直接寫一條公式」。  
* `always / initial` 是 **procedural block**，比較像「進到一個區塊裡，用規則一步一步描述邏輯」。

HDLBits 直接說過：`always @(*)` 的組合邏輯寫法，本質上可以和 `assign` 描述同一種電路，只是語法表達力不同。([ChipVerify](https://www.chipverify.com/verilog/verilog-always-block?utm_source=chatgpt.com))

#### procedural style 不代表硬體真的像 CPU 跑程式

語法看起來像 C/C++，但綜合後仍是固定硬體。像：

* `if` 常對應 mux(多工器)  
* `case` 常對應 selector / decoder  
* `for` 在可綜合 RTL 中常被展開成重複硬體

這是 Verilog 教學與綜合風格的核心觀念。([約克大學電子與計算機工程系](https://www.eecs.yorku.ca/course_archive/2011-12/W/4210/Verilog.pdf?utm_source=chatgpt.com))

---

## 一、RTL 常用

---

### 1\. `always`

#### 語法格式

always @(event\_control)

    statement;

或

always @(event\_control) begin

    statement\_1;

    statement\_2;

    ...

end

#### 每個位置放什麼

* `always`：宣告一個反覆可觸發的程序區塊  
* `@(...)`：事件控制 event control / sensitivity list，決定何時觸發  
* `statement`：可以是一句 procedural statement，也可以是 `begin...end` 包起來的多句

IEEE 1364-2005 的 event control 形式包含 `@(*)`、`@(posedge clk)`、`@(negedge rstn)`、`@(a or b)` 等。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 常見資料型態

* 在 `always` 裡被賦值的左值，傳統 Verilog 通常宣告成 **`reg`**  
* 右值可以是 `wire`、`reg`、常數、比較結果、算式、函式回傳值

關於 `wire/reg` 的基本區分，ChipVerify 的資料型態整理有明確說明。([ChipVerify](https://www.chipverify.com/verilog/verilog-data-types?utm_source=chatgpt.com))

#### 常見用途

##### 組合邏輯

always @(\*) begin

    ...

end

##### 時序邏輯

always @(posedge clk) begin

    ...

end

`always @(*)` 用於 combinational logic，`always @(posedge clk)` 用於 sequential logic / flip-flops。這是 HDLBits 與 ChipVerify 都明確強調的模板。([ChipVerify](https://www.chipverify.com/verilog/verilog-always-block?utm_source=chatgpt.com))

#### 常用技巧

* **組合邏輯**：先給 default assignment，再用 `if` / `case` 覆蓋  
* **時序邏輯**：先寫 reset，再寫 enable，再寫正常資料流  
* 一個 `always` block 只做一件事，例如只算 `next_state` 或只存 `state`

#### 好看好用的寫法

always @(\*) begin

    out \= 8'b0;

    if (en)

        out \= data;

end

always @(posedge clk) begin

    if (reset)

        q \<= 8'b0;

    else if (en)

        q \<= d;

end

#### 常見地雷

* `always` 沒有 event control，也沒有 delay，模擬會卡成 zero-delay infinite loop。ChipVerify 明確提醒這種寫法會讓 simulation hang。([ChipVerify](https://www.chipverify.com/verilog/verilog-always-block?utm_source=chatgpt.com))  
* 把組合邏輯和時序邏輯混在同一個 block，會讓可讀性很差  
* 在 clocked block 裡大量用 `=`，或在 combinational block 裡大量用 `<=`，容易製造模擬/綜合理解混亂。([ChipVerify](https://www.chipverify.com/verilog/verilog-quick-refresher?utm_source=chatgpt.com))

---

### 2\. `begin ... end`

#### 語法格式

begin

    statement\_1;

    statement\_2;

    ...

end

#### 每個位置放什麼

* `begin`：開始一個 sequential block  
* 中間放多個 procedural statements  
* `end`：結束區塊

IEEE 文法把它列為 `seq_block`。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 常見資料型態

區塊裡可放各種 procedural statements；資料型態依各 statement 規則決定，例如賦值左值通常是 `reg`。

#### 常見用途

* `if/else` 分支裡放多句  
* `case` 某個 item 裡放多句  
* `for` 迴圈 body 裡放多句

#### 常用技巧

只要你覺得「這個分支未來可能多長一行」，就先加 `begin...end`。

#### 好看好用的寫法

always @(\*) begin

    if (sel) begin

        out   \= a;

        valid \= 1'b1;

    end

    else begin

        out   \= b;

        valid \= 1'b0;

    end

end

#### 常見地雷

沒加 `begin...end` 時，只有第一句屬於該分支，後面那句其實不在裡面。這是 Verilog 初學者最常踩的坑之一。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

---

### 3\. `if / else if / else`

#### 語法格式

if (condition\_1)

    statement\_1;

else if (condition\_2)

    statement\_2;

else

    statement\_default;

多句版本：

if (condition\_1) begin

    ...

end

else if (condition\_2) begin

    ...

end

else begin

    ...

end

#### 每個位置放什麼

* `condition`：放 expression，最後會被判斷成 true/false  
* `statement`：一個 procedural statement，或 `begin...end`

#### 常見資料型態

* `condition` 常是 `wire/reg` 或比較運算結果  
* 被指定的左值通常是 `reg`  
* 右值可為 `wire/reg/constant/expression`

#### 常見用途

* 2-to-1 mux  
* priority logic(優先邏輯)  
* reset / enable 控制  
* 範圍判斷

#### 它對應什麼硬體

* 在 `always @(*)` 裡，常綜合成 mux 或 priority logic  
* 在 `always @(posedge clk)` 裡，常綜合成帶 reset / enable 的 flip-flop 結構

#### 常用技巧

##### 技巧 1：有優先權才用 `else if`

always @(\*) begin

    if (req2)

        grant \= 2'b10;

    else if (req1)

        grant \= 2'b01;

    else

        grant \= 2'b00;

end

##### 技巧 2：組合邏輯先給預設值

always @(\*) begin

    grant \= 2'b00;

    if (req2)

        grant \= 2'b10;

    else if (req1)

        grant \= 2'b01;

end

##### 技巧 3：固定值很多時改用 `case`

如果條件都長得像 `sel == 2'b00`、`sel == 2'b01`，通常 `case` 更好讀。([ChipVerify](https://www.chipverify.com/verilog/verilog-quick-refresher?utm_source=chatgpt.com))

#### 好看好用的寫法

* `if / else if / else` 垂直對齊  
* 條件由高優先到低優先排序  
* 分支多行就加 `begin...end`

#### 常見地雷

* Verilog **沒有 `elif`**，只有 `else if`  
* 在組合邏輯裡漏掉 `else` 或預設值，可能推導出 latch。Nandland 明確提醒不完整賦值會造成 latch。([Nandland](https://www.nandland.com/sitemap.xml?utm_source=chatgpt.com))

---

### 4\. `case`

Verilog 的 case 不像 C/C++ 那樣需要 break。

#### 語法格式

case (expr)

    item\_1: statement\_1;

    item\_2: statement\_2;

    ...

    default: statement\_default;

endcase

多句版本：

case (expr)

    item\_1: begin

        ...

    end

    default: begin

        ...

    end

endcase

多條件語法：

case (expr)

    item\_1,item\_2: statement\_1;  // if(expr \== item\_1 || expr \== item\_2)

    item\_3,item\_4,item\_5: statement\_2;    
// if(expr \== item\_3 || expr \== item\_4 || expr \== item\_5)

    ...

    default: statement\_default;

endcase

#### 每個位置放什麼

* `expr`：被比較的 expression，例如 `sel`、`state`  
* `item_n`：常數或常數樣式  
* `statement_n`：一個 statement 或 `begin...end`

#### 常見資料型態

* `expr` 常是 scalar 或 vector  
* `item_n` 常寫成對應寬度的常數，如 `2'b00`  
* 左值通常是 `reg`

#### 常見用途

* 多工器 mux  
* decoder  
* FSM 狀態分支

#### 常用技巧

##### 技巧 1：固定值多選一時，優先 `case`

always @(\*) begin

    case (sel)

        2'b00: out \= in0;

        2'b01: out \= in1;

        2'b10: out \= in2;

        2'b11: out \= in3;

        default: out \= 8'b0;

    endcase

end

##### 技巧 2：先給預設值，後 `case`

always @(\*) begin

    out \= 8'b0;

    case (sel)

        2'b00: out \= in0;

        2'b01: out \= in1;

        2'b10: out \= in2;

        2'b11: out \= in3;

    endcase

end

##### 技巧 3：常數格式統一

都寫 `2'b00`、`2'b01`，不要混著寫 `0`、`1`、`2'b10`。

#### 好看好用的寫法

* `case (expr)` 自己一行  
* 所有 item 冒號對齊  
* 分支很多時按數值順序或邏輯順序排列

#### 常見地雷

* 漏 `default` 或漏預設值，組合邏輯仍可能做出 latch。([Nandland](https://www.nandland.com/sitemap.xml?utm_source=chatgpt.com))  
* case item 內有多句卻忘了 `begin...end`

---

### 5\. `for`

#### 語法格式

for (init; condition; step)

    statement;

或

for (init; condition; step) begin

    statement\_1;

    statement\_2;

end

#### 每個位置放什麼

* `init`：初始化，例如 `i = 0`  
* `condition`：結束條件，例如 `i < 8`  
* `step`：每輪更新，例如 `i = i + 1`  
* `statement`：一個 procedural statement，或 `begin...end`

#### 常見資料型態

* loop variable 通常宣告成 `integer i;`  
* 向量索引常見 `y[i]`、`a[i]`  
* 左值通常是 `reg`

#### 常見用途

* bit-slice 重複邏輯  
* 批次指定向量  
* 規則性結構展開

#### 它在 RTL 的意思

在可綜合 RTL 裡，`for` 主要是**展開重複硬體**，不是像軟體那樣真的在晶片裡跑迴圈。這是 Nandland 對 synthesizable `for` 的核心說法。([Nandland](https://www.nandland.com/sitemap.xml?utm_source=chatgpt.com))

#### 常用技巧

##### 技巧 1：上界用常數或 parameter

parameter WIDTH \= 8;

integer i;

always @(\*) begin

    for (i=0; i\<WIDTH; i=i+1)

        y\[i\] \= a\[i\] & b\[i\];

end

##### 技巧 2：body 多句就加 `begin...end`

integer i;

always @(\*) begin

    for (i=0; i\<8; i=i+1) begin

        y\[i\]     \= a\[i\] ^ b\[i\];

        valid\[i\] \= en;

    end

end

##### 技巧 3：只想讓前幾項有效時，用固定最大展開次數再加 `if`

integer i;

always @(\*) begin

    for (i=0; i\<8; i=i+1) begin

        if (i \< n)

            y\[i\] \= a\[i\];

        else

            y\[i\] \= 1'b0;

    end

end

#### 好看好用的寫法

* loop variable 用 `i`, `j`  
* `integer i;` 放在模組前段固定位置  
* `i=0; i<WIDTH; i=i+1` 格式一致

#### 常見地雷

* 上界若依賴執行時才知道的值，綜合不一定穩  
* 忘了 `begin...end`，只有第一句在 loop 裡  
* 用 `for` 時忘了它描述的是空間上的重複硬體，不是時間上的重複執行。([Nandland](https://www.nandland.com/sitemap.xml?utm_source=chatgpt.com))

---

### 6\. `=` 與 `<=`

這一段是 procedural style 最重要的核心。

#### 語法格式

lhs \= rhs;    // blocking assignment

lhs \<= rhs;   // non-blocking assignment

#### 每個位置放什麼

* `lhs`：left-hand side，通常是 `reg`、bit-select、part-select 等可被程序式指定的目標  
* `rhs`：right-hand side，可以是常數、訊號、運算式、比較結果等

#### `=` 是什麼

`=` 是 **blocking assignment(阻塞賦值)**。 它的程序語意是：**這一行先完成，再往下執行下一行**。ChipVerify 將 blocking assignment 說明為 sequentially execute 的形式。([ChipVerify](https://www.chipverify.com/verilog/verilog-interview-questions-set-3?utm_source=chatgpt.com))

例子：

always @(\*) begin

    x \= a;

    y \= x;

end

直覺上，`y` 看到的是**更新後的 `x`**。

#### `<=` 是什麼

`<=` 是 **non-blocking assignment(非阻塞賦值)**。 它的程序語意是：**先記下 rhs 的結果，lhs 的更新排到目前時間步較後面一起生效**。ChipVerify 說它會 schedule assignment，而不是立刻阻止後續敘述。([ChipVerify](https://www.chipverify.com/verilog/verilog-interview-questions-set-3?utm_source=chatgpt.com))

例子：

always @(posedge clk) begin

    x \<= a;

    y \<= x;

end

直覺上，`y` 看到的是**舊的 `x`**，這符合兩顆串接 flip-flop 的硬體直覺。

#### 差異總結

##### 差異 1：後續敘述看到的是新值還是舊值

* `=`：後面通常看到新值  
* `<=`：後面通常仍看到舊值

##### 差異 2：最常對應的硬體風格

* `=`：常用於組合邏輯  
* `<=`：常用於時序邏輯

##### 差異 3：實務規則

HDLBits 與 ChipVerify 都強烈建議：

* `always @(*)` 用 `=`  
* `always @(posedge clk)` 用 `<=`  
* 不要在同一個 always block 混用 `=` 和 `<=`。([ChipVerify](https://www.chipverify.com/verilog/verilog-quick-refresher?utm_source=chatgpt.com))

#### 常見地雷

* clocked block 裡主要用 `=`  
* combinational block 裡主要用 `<=`  
* 同一個 block 混用兩者  
* 沒搞清楚 `<=` 是「先排程後更新」，導致腦中模擬錯誤。([ChipVerify](https://www.chipverify.com/verilog/verilog-quick-refresher?utm_source=chatgpt.com))

---

## 二、模擬常用

---

### 7\. `initial`

#### 語法格式

initial

    statement;

或

initial begin

    statement\_1;

    statement\_2;

    ...

end

#### 每個位置放什麼

* `initial`：表示這個 block 在模擬開始時執行一次  
* 內容可放賦值、delay、wait、system task 等

#### 常見資料型態

和 `always` 一樣，程序式賦值左值通常是 `reg`。

#### 常見用途

* testbench 初始化  
* 產生刺激 stimulus  
* 搭配 `$display`、`$finish`

ChipVerify 明確說 `initial` 在 time 0 執行一次，常用於 testbench，且通常不綜合成硬體。([ChipVerify](https://www.chipverify.com/verilog/verilog-initial-block?utm_source=chatgpt.com))

#### 常用技巧

* 把「初始化」和「刺激流程」分成不同 `initial` block  
* 用 `initial begin ... end` 搭配 `#delay`

#### 好看好用的寫法

initial begin

    clk \= 0;

    rst \= 1;

    a   \= 0;

    b   \= 0;

end

#### 常見地雷

* 把 `initial` 當成一般 RTL 主邏輯寫法  
* 忘記它通常是 simulation-only。([ChipVerify](https://www.chipverify.com/verilog/verilog-initial-block?utm_source=chatgpt.com))

---

### 8\. `#delay`

#### 語法格式

\#10 a \= 1'b1;

或

\#5 statement;

#### 每個位置放什麼

* `#10`：延遲 10 個 simulation time units  
* 後面接一個 procedural statement

#### 常見資料型態

delay 數值通常是整數常數；後面的賦值左值仍通常是 `reg`。

#### 常見用途

* testbench 產生時序刺激  
* 產生 clock  
* 控制觀察時間點

#### 常用技巧

initial begin

    a \= 0;

    \#10 a \= 1;

    \#10 a \= 0;

end

#### 好看好用的寫法

每個時刻動作分行寫，不要把太多 `#delay` 擠成一行。

#### 常見地雷

* 誤以為 `#delay` 會變成實體硬體延遲  
* 在 synthesizable RTL 中濫用 delay。ChipVerify 與 always block 教學都提醒延遲主要是模擬概念。([ChipVerify](https://www.chipverify.com/verilog/verilog-always-block?utm_source=chatgpt.com))

---

### 9\. `$display`

#### 語法格式

$display("format string", arg1, arg2, ...);

#### 每個位置放什麼

* 第一個參數是格式字串  
* 後面可放想印出的訊號或數值

#### 常見資料型態

可印 `reg`、`wire`、整數、表達式。

#### 常見用途

* 除錯  
* 看關鍵時間點的訊號值  
* testbench 紀錄

#### 常用技巧

initial begin

    $display("simulation start");

end

或

always @(posedge clk) begin

    $display("q=%b", q);

end

#### 常見地雷

* 印太多內容，log 爆炸  
* 忘記 `$display` 不會綜合成硬體

---

### 10\. `$finish` / `$stop`

#### 語法格式

$finish;

$stop;

#### 每個位置放什麼

都是 system task，通常直接單獨一行。

#### 常見用途

* `$finish`：結束模擬  
* `$stop`：暫停模擬，像 breakpoint

ChipVerify 對 `$stop/$finish` 有明確說明。([ChipVerify](https://www.chipverify.com/verilog/verilog-stop-finish?utm_source=chatgpt.com))

#### 常用技巧

initial begin

    \#100 $finish;

end

#### 常見地雷

* 忘了在 testbench 結尾停模擬，導致 simulation 一直跑  
* 把 `$stop` 當 RTL 功能的一部分思考

---

## 三、知道就好

這區不是說不重要，而是**你現在做 HDLBits / RTL 基礎題時，不需要先深挖**。但我照你要求，把粒度補到和前面一樣完整。

---

### 11\. `repeat`

#### 語法格式

repeat (count)

    statement;

或

repeat (count) begin

    statement\_1;

    statement\_2;

end

#### 每個位置放什麼

* `count`：重複次數  
* `statement`：要被重複的 procedural statement

IEEE 將 `repeat` 列在 loop statement 中。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 常見資料型態

* `count` 通常是整數或整數表達式  
* 內部賦值左值仍通常是 `reg`

#### 常見用途

* testbench 等固定次數事件  
* 重複若干輪刺激  
* 等幾個 clock

#### 常用技巧

initial begin

    repeat (4) @(posedge clk);

    done \= 1'b1;

end

這比手寫四次 `@(posedge clk)` 乾淨很多。

#### 好看好用的寫法

`repeat (N)` 的 `N` 最好寫成有意義的常數或 parameter，別亂塞魔法數字。

#### 常見地雷

* 把 `repeat` 想成可綜合 RTL 主力  
* 忘記 `count` 若很複雜，閱讀性會變差

---

### 12\. `while`

#### 語法格式

while (condition)

    statement;

或

while (condition) begin

    ...

end

#### 每個位置放什麼

* `condition`：迴圈持續條件  
* `statement`：被重複執行的 procedural statement

IEEE 將 `while` 也列在 loop statement 中。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 常見資料型態

* `condition` 為邏輯表達式  
* 內部賦值左值通常仍是 `reg`

#### 常見用途

* testbench 等待某條件變化  
* 行為模型  
* 少量流程控制

#### 常用技巧

initial begin

    while (\!done)

        @(posedge clk);

end

#### 好看好用的寫法

* 確保 condition 會改變，避免無窮迴圈  
* body 若多句就加 `begin...end`

#### 常見地雷

* 在可綜合 RTL 中濫用 `while`  
* 忘了讓 condition 最終變成 false，模擬會卡住  
* 跟 `for` 不同，`while` 的迭代次數通常不夠靜態明確，因此不如 `for` 適合 synthesis。這是 Nandland 等教學常提醒的點。([Nandland](https://www.nandland.com/sitemap.xml?utm_source=chatgpt.com))

---

### 13\. `forever`

#### 語法格式

forever

    statement;

或

forever begin

    ...

end

ChipVerify 對 forever 也提醒：若沒有 delay 或時間控制，會讓模擬卡住。([ChipVerify](https://www.chipverify.com/systemverilog/systemverilog-forever-loop?utm_source=chatgpt.com))

#### 每個位置放什麼

* `forever`：表示無窮迴圈  
* 後面接一個 statement 或 block

#### 常見資料型態

和一般 procedural statement 相同。

#### 常見用途

* testbench 產生 clock  
* 永久監控流程

#### 常用技巧

initial begin

    clk \= 0;

    forever \#5 clk \= \~clk;

end

#### 好看好用的寫法

把 clock generator 單獨放一個 `initial` block，不要混進其他刺激流程。

#### 常見地雷

* `forever` 沒有 delay / event control，simulation 直接掛住  
* 拿它當一般 RTL 主邏輯寫法。([ChipVerify](https://www.chipverify.com/systemverilog/systemverilog-forever-loop?utm_source=chatgpt.com))

---

### 14\. `wait`

#### 語法格式

wait (condition) statement;

或

wait (condition) begin

    ...

end

IEEE 文法直接列出 `wait ( expression ) statement`。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 每個位置放什麼

* `condition`：等待成立的條件  
* `statement`：條件成立後執行的動作

#### 常見資料型態

* `condition` 為邏輯表達式  
* 內部賦值左值通常仍是 `reg`

#### 常見用途

* testbench 等待 ready / valid / done  
* 行為模型同步

#### 常用技巧

initial begin

    wait (ready);

    $display("ready seen");

end

#### 好看好用的寫法

對握手訊號很有幫助，例如 `wait(valid && ready)`。

#### 常見地雷

* 若 condition 永遠不成立，模擬會一直卡在那裡  
* 在 RTL 設計初學階段過度依賴 `wait`，容易把 testbench 思維帶進設計本體

---

### 15\. `fork ... join`

#### 語法格式

fork

    statement\_1;

    statement\_2;

    ...

join

還有變體：

fork

    ...

join\_any

fork

    ...

join\_none

ChipVerify 的 block statements 頁面也有介紹 `fork...join` 與 `join_any/join_none`。([ChipVerify](https://www.chipverify.com/verilog/verilog-block-statements?utm_source=chatgpt.com))

#### 每個位置放什麼

* `fork`：開始平行 block  
* 中間是多條平行執行的程序  
* `join`：等全部完成才往下走  
* `join_any`：任一完成即可往下走  
* `join_none`：立刻往下走，不等子程序結束

#### 常見資料型態

區塊內可放一般 procedural statements。

#### 常見用途

* testbench 做平行刺激  
* 同時監看多個事件  
* 較進階模擬流程

#### 常用技巧

fork

    \#10 a \= 1;

    \#20 b \= 1;

join

#### 好看好用的寫法

* 每條平行流程各自獨立一行  
* 複雜時加註解，說明哪條在做什麼

#### 常見地雷

* 不清楚 `join / join_any / join_none` 差異  
* 在 RTL 初學時就硬用，讓邏輯理解複雜化  
* 把平行模擬語意誤當作一般同步硬體語意。ChipVerify 也建議只在真需要時用 `join` 類機制。([ChipVerify](https://www.chipverify.com/verilog/verilog-block-statements?utm_source=chatgpt.com))

---

### 16\. `disable`

#### 語法格式

disable block\_name;

或用於 named block / task。

IEEE 文法把 `disable hierarchical_task_identifier`、`disable hierarchical_block_identifier` 列為合法 statement。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 每個位置放什麼

* `disable`：關鍵字  
* 後面是要被跳出的 block 名稱或 task 名稱

#### 常見資料型態

不牽涉特別資料型態，重點在 block/task 命名。

#### 常見用途

* 提前跳出 named block  
* 中止某段程序流程

#### 常用技巧

begin : SEARCH

    if (found)

        disable SEARCH;

end

#### 好看好用的寫法

只有在你真的需要中止某個命名區塊時才用，並且 block 名稱要有意義。

#### 常見地雷

* 初學者很少需要它，硬用只會增加閱讀負擔  
* 若 block 命名混亂，`disable` 會非常難追

---

### 17\. `casex / casez`

#### 語法格式

casex (expr)

    item\_1: statement\_1;

    ...

endcase

casez (expr)

    item\_1: statement\_1;

    ...

endcase

IEEE 文法列出 `case_statement ::= case ... | casez ... | casex ...`。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

#### 每個位置放什麼

和普通 `case` 類似，只是比較規則不同。

#### 常見資料型態

* `expr` 常是向量  
* `item_n` 可能含 `x` 或 `z` 樣式

#### 常見用途

* pattern matching  
* 某些 don't-care 比對

#### 常用技巧

如果只是普通固定值分支，先用普通 `case`；只有你真的理解 `x/z` 的語意時，再考慮 `casez/casex`。

#### 好看好用的寫法

* 先把普通 `case` 學穩  
* 若使用 `casez/casex`，在註解中明確說明 don't-care 意圖

#### 常見地雷

* 初學者很容易把模擬中的 `x/z` 和設計意圖混在一起  
* `casex` 特別容易因為 `x` 匹配太寬鬆而造成除錯困難，所以很多實務風格會偏向避免濫用。這也是業界常見風格提醒。([巴克內爾大學工程學院](https://www.eg.bucknell.edu/~csci320/2016-fall/wp-content/uploads/2015/08/verilog-std-1364-2005.pdf?utm_source=chatgpt.com))

---

## 最後整理成速記版

### RTL 常用

* `always @(*)`  
* `always @(posedge clk)`  
* `begin...end`  
* `if / else if / else`  
* `case`  
* `for`  
* `=` / `<=`

### 模擬常用

* `initial`  
* `#delay`  
* `$display`  
* `$finish / $stop`

### 知道就好

* `repeat`  
* `while`  
* `forever`  
* `wait`  
* `fork...join`  
* `disable`  
* `casex / casez`

### 最重要的 3 句話

1. **組合邏輯**：`always @(*)` \+ `=`  
2. **時序邏輯**：`always @(posedge clk)` \+ `<=`  
3. **知道就好那區** 多半偏 testbench、模擬控制或進階語法，不是你現在 HDLBits 基礎 RTL 的主力工具。([ChipVerify](https://www.chipverify.com/verilog/verilog-quick-refresher?utm_source=chatgpt.com))

