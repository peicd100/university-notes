# VHDL


我先幫你定義範圍：這裡只教你 **Ch2 全部**，以及 **Ch3 到 p.62 為止** 的語法；也就是 **Behavior Model and Simulation（p.63）之前** 的內容，不含 p.63 之後。教材重點確實就是：**基本型別/物件 → dataflow → process/sequential → if/loop/case/wait**。 

---

## 1. 先建立整體心智模型

先用你熟的 Verilog 去對照：

```mermaid
flowchart TB
    A[Verilog module] --> B[VHDL entity<br>外部介面]
    A --> C[VHDL architecture<br>內部實作]

    D[assign] --> E[concurrent signal assignment<br>架構中平行執行]
    F[always @(*)] --> G[process(sensitivity list)<br>內部循序執行]
    H[always @(posedge clk)] --> I[process + if clk'EVENT and clk='1']

    J[blocking =] --> K[variable :=<br>立即更新]
    L[nonblocking <=] --> M[signal <=<br>排程更新]
```

你只要先記住這 5 句：

1. **VHDL = entity + architecture**
2. **architecture 外面預設是平行/concurrent**
3. **process 裡面才是循序/sequential**
4. **signal `<=` 像 Verilog nonblocking**
5. **variable `:=` 像 Verilog blocking 的暫存變數**

這五句吃透，你後面大半都會順。

---

## 2. 最基本的外觀：VHDL 長什麼樣

### 2.1 entity + architecture

VHDL 最基本結構：

```vhdl
entity OR_gate is
    port(
        A, B : in bit;
        C    : out bit
    );
end OR_gate;

architecture OR2_arch of OR_gate is
begin
    C <= A or B;
end OR2_arch;
```

Verilog 類比：

```verilog
module OR_gate(
    input  A, B,
    output C
);
assign C = A | B;
endmodule
```

對照方式：

* `entity`：像 module 的介面宣告
* `architecture`：像 module 內部實作
* `port (...)`：像 input/output 宣告
* `<=` 在 architecture 外層這種寫法：像 `assign`

教材明確說明，一個基本 VHDL 程式由 **entity declaration** 與 **architecture body** 組成；entity 描述外部介面，architecture 描述內部實作。

---

### 2.2 註解、大小寫、命名

VHDL 註解是：

```vhdl
-- 這是註解
```

另外有兩個你要注意：

* **大小寫不敏感**
* 識別字第一個字元要是英文字母，最後不能是底線 `_`

所以 `Clock`、`CLOCK`、`clock` 在 VHDL 裡視為同一個名字。這和 Verilog 很不一樣，Verilog 是大小寫敏感。教材在 Ch2 一開始就特別講了這點。

---

## 3. 物件宣告：VHDL 不是 `type name`，而是 `name : type`

這是你第一個需要適應的地方。

### 3.1 常見宣告格式

```vhdl
constant BUS_WIDTH : INTEGER := 8;
variable FOUND, DONE : BOOLEAN;
signal CLOCK : BIT;
signal DATA_BUS : BIT_VECTOR(0 to 7);
signal INIT_P : STD_LOGIC_VECTOR(7 downto 0);
```

Verilog 類比：

```verilog
parameter BUS_WIDTH = 8;
reg FOUND, DONE;      // 只能說概念上接近，不是完全等價
wire CLOCK;
wire [7:0] INIT_P;
```

VHDL 四種物件類別，教材列的是：

1. `constant`
2. `variable`
3. `signal`
4. `file`

其中最重要的是前 3 個。教材也說 port 是 signal 物件，generic 是 constant 物件。

---

### 3.2 先用 Verilog 直覺理解 constant / variable / signal

#### constant

像 Verilog `parameter`。

```vhdl
constant N : integer := 4;
```

#### variable

像 process/always block 裡的區域暫存變數，**立即更新**。

```vhdl
variable temp : bit;
temp := A and B;
```

#### signal

像線路上的訊號，**不是立刻改值，而是先排程，再更新**。

```vhdl
signal Z : bit;
Z <= A and B;
```

這個差異在 Ch3 是超級重點，因為教材專門拿它做例子。

---

## 4. 型別系統：VHDL 比 Verilog 更「強型別」

VHDL 很重型別，你不能像 Verilog 那樣很隨便混著用。這也是初學最常卡住的地方。

---

### 4.1 枚舉型別 enumeration

```vhdl
type car_state is (STOP, SLOW, MEDIUM, FAST);
type logic_state is ('0', '1', 'Z');
```

這很像你自己定義一組合法狀態。Verilog 類比比較接近：

* 傳統 Verilog：`parameter`/`localparam` 編碼狀態
* SystemVerilog：`enum`

教材也強調，枚舉值的**順序有大小關係**，所以可以比較 `SLOW < FAST`。

---

### 4.2 `BIT`、`BOOLEAN`、`STD_LOGIC`

#### `BIT`

只有 `'0'`、`'1'`

```vhdl
signal a : bit;
```

#### `BOOLEAN`

只有 `FALSE`、`TRUE`

```vhdl
variable done : boolean;
```

#### `STD_LOGIC`

這是實務上常用的，來自 `ieee.std_logic_1164`：

```vhdl
library ieee;
use ieee.std_logic_1164.all;

signal x : std_logic;
signal y : std_logic_vector(7 downto 0);
```

教材列了 `STD_LOGIC` 的 9 種值：`U X 0 1 Z W L H -`。
你可以先把它想成：**比 Verilog 的 4-state 更細的邏輯系統**。至少你看到 `Z`、`X`、`U` 不要嚇到。

---

### 4.3 integer 與 range

```vhdl
type INDEX is range 0 to 15;
type WORD_LENGTH is range 31 downto 0;
```

還有：

```vhdl
a : in integer range 0 to 255;
```

Verilog 類比比較像：

```verilog
integer a; // 但 Verilog 不會用這種語法直接綁範圍限制
```

VHDL 的 range 比較像「這個型別只允許某一段值」。

教材後面 comparator 就用：

```vhdl
a,b : in integer range 0 to 255;
```

 

---

### 4.4 physical type / TIME

這一段你先以「看得懂」為目標，不用太執著實作。

教材介紹 physical type，最重要是 **`TIME`**：

```vhdl
20 ns
5 us
1 ms
```

這主要拿來模擬、延遲、testbench。

---

## 5. 陣列與向量：這是你看懂 VHDL 電路描述的核心

### 5.1 array type

```vhdl
type ADDRESS_WORD is array (0 to 63) of BIT;
type DATA_WORD    is array (7 downto 0) of STD_LOGIC;
type ROM          is array (0 to 125) of DATA_WORD;
```

你可以把它想成：

* `ADDRESS_WORD`：64 個 bit
* `DATA_WORD`：8 個 std_logic
* `ROM`：126 組 8-bit word

Verilog 類比：

```verilog
wire [63:0] address_word;
wire [7:0]  data_word;
reg  [7:0]  rom [0:125];
```

教材也有示範可以對整個 array、單一元素、甚至 slice 指派。

---

### 5.2 `BIT_VECTOR`、`STD_LOGIC_VECTOR`

這兩個你一定會一直看到：

```vhdl
signal RX_BUS : BIT_VECTOR(0 to 5);
signal INIT_P : STD_LOGIC_VECTOR(7 downto 0);
```

Verilog 類比：

```verilog
wire [5:0] RX_BUS;   // 概念上
wire [7:0] INIT_P;
```

差別在 VHDL 會把元素型別講得很清楚：

* `BIT_VECTOR` = array of `BIT`
* `STD_LOGIC_VECTOR` = array of `STD_LOGIC`

教材把這兩個都列成常用 unconstrained array。

---

### 5.3 `to` 與 `downto`

這個是很多 Verilog 使用者第一次看 VHDL 會卡住的點。

```vhdl
signal areg : bit_vector(0 to 6);
signal breg : bit_vector(6 downto 0);
```

如果都指定：

```vhdl
areg <= "0000001";
breg <= "0000001";
```

那：

* `areg(6) = '1'`
* `breg(0) = '1'`

也就是說，**字串左邊對應 range 的左邊，右邊對應 range 的右邊**。
所以你不能只看字面 `"0000001"`，一定要同時看索引方向。

這跟 Verilog 固定常看 `[MSB:LSB]` 的直覺不太一樣。教材在 p.35~36 特別示範了這件事。

---

### 5.4 unconstrained array

```vhdl
type STACK_TYPE is array (INTEGER range <>) of ADDRESS_WORD;
signal MY_STACK : STACK_TYPE(-127 to 127);
```

這個概念像是：**先定義元素型別與維度形式，真正長度等建立物件時再決定**。

很像你先定義一個「模板型 array 型別」。
傳統 Verilog 沒有完全等價、直接同級的語法直覺。



---

### 5.5 record type

```vhdl
type MODULE is
record
    SIZE         : INTEGER range 20 to 200;
    CRITICAL_DLY : TIME;
    NO_INPUTS    : PIN_TYPE;
    NO_OUTPUTS   : PIN_TYPE;
end record;
```

Verilog 類比：

* 純 Verilog：幾乎沒有漂亮對應
* SystemVerilog：比較像 `struct`

教材還示範了 aggregate 指派：

```vhdl
NAND_COMP := (50, 20 ns, 3, 2);
```

這就像一次把整個結構塞值進去。

---

## 6. 不常拿來綜合，但你要看得懂的型別

### 6.1 subtype

```vhdl
subtype my_integer is integer range 0 to 20;
subtype MIDDLE is DIGIT range '3' to '7';
```

概念就是：**從既有型別切一塊比較小的合法範圍**。
像你在 Verilog 裡沒有直接對等，但可類比成「加上更嚴格限制的型別別名」。

---

### 6.2 access type

```vhdl
type PTR is access MODULE;
variable MOD_PTR : PTR;
MOD_PTR := new MODULE;
```

這像 C pointer。教材也直接說，多數 synthesizer 不支援，偏模擬/高階語法。你在 p.63 前如果看到，知道它是「指標型」就夠了。

---

### 6.3 file type

```vhdl
file source_data : text is in "source_data.txt";
file output_data : text is out "output_data.txt";
```

這主要是 testbench / simulation 在用，不是拿來做硬體本體邏輯。教材也明說檔案主要用於 testbench。

---

## 7. 運算子：大致上跟 Verilog 很像，但名字有差

教材把運算子分成邏輯、比較、位移、加法、乘法、其他。

### 7.1 邏輯運算

```vhdl
and or nand nor xor xnor not
```

>注意都是英文，不是符號。


Verilog 對照：

```verilog
& | ~& ~| ^ ^~ ~
```

---

### 7.2 比較運算

```vhdl
= /= < <= > >=
```

注意 VHDL 的不等於是 `/=`，不是 Verilog 的 `!=`。

---

### 7.3 位移與旋轉

```vhdl
sll srl sla sra rol ror
```

對照：

* `sll` ≈ `<<`
* `srl` ≈ `>>`
* `rol` / `ror`：旋轉，Verilog 沒有直接內建同名運算子



---

### 7.4 串接 `&`

```vhdl
'0' & '1'   -- 結果 "01"
```

Verilog 對照：

```verilog
{1'b0, 1'b1}
```

這個你一定常用。

> 要寫串接用 `'1' & '0'`，要 and 運算用 `'1' and '0'`

---

### 7.5 其他

```vhdl
* / mod abs **
```

* `mod`：取餘數
* `abs`：絕對值
* `**`：次方



---

## 8. Attributes：VHDL 很有特色的一塊

這部分是讀教材時會頻繁看到的語法糖。

### 8.1 範圍相關

```vhdl
T'LEFT
T'RIGHT
T'HIGH
T'LOW
```

例如：

```vhdl
type allowed_value is range 15 downto 0;
```

那：

* `allowed_value'LEFT = 15`
* `allowed_value'RIGHT = 0`
* `allowed_value'HIGH = 15`
* `allowed_value'LOW = 0`

這組語法在 Verilog 沒有這麼原生、這麼一致的型別 attribute 體系。

---

### 8.2 `'EVENT`、`'ACTIVE`、`'LAST_EVENT`

教材特別強調：

```vhdl
clock'EVENT and clock = '1'
```

代表偵測上升沿。
Verilog 類比就是：

```verilog
always @(posedge clock)
```

另外教材也區分：

* S'EVENT：目前這個 delta 內，signal S 有沒有發生「值改變」
* S'LAST_EVENT：距離 上一次 event 已經過了多少時間，它回傳的是一個 time 型別 的值，例如：10 ns、5 us，不是 true/false。
* S'ACTIVE：目前這個 delta 內，signal S 有沒有被指定新值；即使新值和舊值一樣，也算 active

這點很 VHDL，也很重要。

---

### 8.3 `'RANGE`、`'REVERSE_RANGE`

```vhdl
WBUS'RANGE
WBUS'REVERSE_RANGE
```

如果：

```vhdl
variable WBUS : BIT_VECTOR(7 downto 0);
```

那：

* `WBUS'RANGE = 7 downto 0`
* `WBUS'REVERSE_RANGE = 0 to 7`

這在寫 loop 時很好用，因為你不用手刻 7 downto 0。教材後面 bit count 例子就直接用 `d'RANGE`。 

---

## 9. Dataflow model：平行描述硬體

教材把 dataflow model 定義成：用 **concurrent signal assignment** 來描述功能。主要有三種：

1. 基本 concurrent signal assignment
2. conditional signal assignment
3. selected signal assignment



---

### 9.1 基本 concurrent signal assignment

```vhdl
C <= A or B;
```

Verilog：

```verilog
assign C = A | B;
```

這是最直觀的一種。
放在 architecture 的 `begin ... end` 之間，但**不在 process 裡**，就是平行執行。教材也明說 concurrent statements 的位置不重要，信號變化時就會觸發。

---

### 9.2 conditional signal assignment

```vhdl
Y <= X1 when S = '1'
     else X2;
```

Verilog 類比：

```verilog
assign Y = (S == 1'b1) ? X1 : X2;
```

更長一點可以寫優先鏈：

```vhdl
A <= "00" when B(0) = '1' else
     "01" when B(1) = '1' else
     "10" when B(2) = '1' else
     "11";
```

這很像一串巢狀 ternary。教材用這個做 priority encoder。

---

### 9.3 selected signal assignment

```vhdl
with S select
Y <= X(0) when "00",
     X(1) when "01",
     X(2) when "10",
     X(3) when "11";
```

Verilog 類比比較像：

```verilog
always @(*) begin
    case (S)
        2'b00: Y = X[0];
        2'b01: Y = X[1];
        2'b10: Y = X[2];
        2'b11: Y = X[3];
    endcase
end
```

或某種 case-based continuous selection。
重點差異：

* `conditional signal assignment`：偏 **priority**
* `selected signal assignment`：偏 **case/mux**

教材在 Ch2 後段把這兩個並列成 dataflow 的核心語法。 

---

## 10. Behavioral syntax：`process` 是 Ch3 的主角

教材明確說：behavior modeling style 的主要機制是 `process statement`。

### 10.1 process = Verilog always block

```vhdl
process(A, B, C, D)
    variable TEMP1, TEMP2 : bit;
begin
    TEMP1 := A and B;
    TEMP2 := C and D;
    TEMP1 := TEMP1 or TEMP2;
    Z <= not TEMP1;
end process;
```

Verilog 類比：

```verilog
always @(*) begin
    temp1 = A & B;
    temp2 = C & D;
    temp1 = temp1 | temp2;
    Z <= ~temp1;   // 概念上類比，不是建議寫法
end
```

VHDL 規則是：

* sensitivity list 裡任一 signal 發生 event，process 被執行一次
* 內部語句**照順序執行**
* 跑到最後會 suspend，等下一次 event

這和 Verilog always block 非常接近。

---

## 11. `variable :=` 與 `signal <=`：這是最大魔王

這裡我用一句話講透：

* `variable :=`：**現在就改**
* `signal <=`：**先排程，之後才更新**

教材直接說 variable assignment 是 executed and updated at the same time；signal assignment 是先執行，再經過一個 delay Δ 才更新。

---

### 11.1 為什麼 variable 很像 Verilog 的 blocking `=`

```vhdl
process(A, B, C)
    variable M, N : integer;
begin
    M := A;
    N := B;
    X <= M + N;
    M := C;
    Y <= M + N;
end process;
```

這裡 `Y` 用的是更新後的 `M = C`。
所以你可以直觀想成 Verilog：

```verilog
always @(*) begin
    M = A;
    N = B;
    X <= M + N;
    M = C;
    Y <= M + N;
end
```

---

### 11.2 為什麼 signal 不適合拿來存 process 內中間值

教材有一個反例：如果你把中間值也寫成 signal，像這樣：

```vhdl
signal TEMP1, TEMP2 : bit;
...
process(A,B,C,D,TEMP1,TEMP2)
begin
    TEMP1 <= A and B;
    TEMP2 <= C and D;
    TEMP1 <= TEMP1 and TEMP2;
    Z <= TEMP1;
end process;
```

結果不是你直覺想的那樣。
因為同一次 process 裡對同一個 signal 多次指定，**最後一次會生效**；而且 signal 不會立即更新。教材甚至畫出等效電路，指出 `A`、`B` 被丟著沒用。

這點完全可以用一句 Verilog 忠告記住：

> **在 VHDL process 裡，要做中間組合運算，優先用 variable，不要用 signal。**

---

### 11.3 sequential signal assignment 與 concurrent signal assignment 的差別

教材用兩段程式比較：

#### process 內 sequential signal assignment

```vhdl
process(B)
begin
    A <= B;
    Z <= A;
end process;
```

當 `B` 改變時：

* `A` 會在 `T + Δ` 變成 `B`
* `Z` 會在 `T + Δ` 取到 **舊的 A**

#### architecture 外 concurrent signal assignment

```vhdl
A <= B;
Z <= A;
```

當 `B` 改變時：

* `A` 在 `T + Δ` 更新
* 接著 `A` 的 event 觸發下一條
* `Z` 在 `T + 2Δ` 變成新的 `A`

教材把這兩種情況拆開講得很清楚。這一段你最好反覆讀 2 次。

---

## 12. `if`：組合邏輯與時序邏輯都靠它

### 12.1 基本語法

```vhdl
if condition then
    ...
elsif condition then
    ...
else
    ...
end if;
```

Verilog：

```verilog
if (condition) begin
    ...
end else if (condition) begin
    ...
end else begin
    ...
end
```

---

### 12.2 沒有 `else` 會保留前值 → 可能推導出 latch / FF

教材明講：`if` 若缺少 `else`，某些 signal 在某些情況下沒被指定，就會保留前值，因此可能推導出儲存元件。

#### 例：latch

```vhdl
process(Qin, en)
begin
    if en = '1' then
        Qout <= Qin;
    end if;
end process;
```

Verilog 類比：

```verilog
always @(*) begin
    if (en)
        Qout = Qin;   // 沒有 else，可能是 latch
end
```

---

### 12.3 D flip-flop：用 `'EVENT`

```vhdl
process(Qin, clk)
begin
    if (clk'EVENT and clk = '1') then
        Qout <= Qin;
    end if;
end process;
```

Verilog：

```verilog
always @(posedge clk) begin
    Qout <= Qin;
end
```

教材就是這樣教 rising edge 偵測。

---

### 12.4 非同步 reset

```vhdl
process(Qin, clk, clr)
begin
    if clr = '1' then
        Qout <= '0';
    elsif (clk'EVENT and clk = '1') then
        Qout <= Qin;
    end if;
end process;
```

Verilog：

```verilog
always @(posedge clk or posedge clr) begin
    if (clr)
        Qout <= 1'b0;
    else
        Qout <= Qin;
end
```

教材明確說這是 asynchronous reset。

---

### 12.5 `if ... else` 做組合邏輯

教材舉 comparator 為例，意思是：

* **沒有 else**：常常變成有記憶
* **有 else/elsif 全補齊**：比較像 combinational logic

這和 Verilog 的 `always @(*)` 規則完全一致。

---

## 13. `for loop`：硬體描述裡常拿來展開重複邏輯

### 13.1 基本語法

```vhdl
for i in 2 downto 0 loop
    ...
end loop;
```

Verilog：

```verilog
for (i = 2; i >= 0; i = i - 1) begin
    ...
end
```

教材用 bit count 做例子：

```vhdl
process(d)
    variable num_bits : integer;
begin
    num_bits := 0;
    for i in 2 downto 0 loop
        if d(i) = '1' then
            num_bits := num_bits + 1;
        end if;
    end loop;
    q <= num_bits;
end process;
```



---

### 13.2 更漂亮的寫法：`d'RANGE`

```vhdl
for i in d'RANGE loop
    ...
end loop;
```

這樣你不用自己硬寫 `2 downto 0`。
如果向量寬度改了，loop 也能跟著走，這是很 VHDL 的寫法。教材特別把這當作進階版例子。 

---

## 14. `case`：多工器/解碼器很常見

### 14.1 基本語法

```vhdl
case expression is
    when choice1 =>
        ...
    when choice2 =>
        ...
    when others =>
        ...
end case;
```

Verilog：

```verilog
case (expression)
    choice1: ...;
    choice2: ...;
    default: ...;
endcase
```

### 14.2 範例：4-to-1 mux

```vhdl
process(X, S)
begin
    case S is
        when "00" => Y <= X(0);
        when "01" => Y <= X(1);
        when "10" => Y <= X(2);
        when others => Y <= X(3);
    end case;
end process;
```

Verilog：

```verilog
always @(*) begin
    case (S)
        2'b00: Y = X[0];
        2'b01: Y = X[1];
        2'b10: Y = X[2];
        default: Y = X[3];
    endcase
end
```

`when others` 就是 `default`。

---

## 15. `wait`：另一種控制 process 的方式

教材列了三種基本形式：

```vhdl
wait on sensitivity_list;
wait until boolean_expression;
wait for time_expression;
```

---

### 15.1 `wait until` 類比 `@(posedge clk)`

```vhdl
process
begin
    wait until (clk'EVENT and clk = '1');
    Qout <= Qin;
end process;
```

Verilog：

```verilog
always begin
    @(posedge clk);
    Qout <= Qin;
end
```

教材直接把這當作另一種 DFF 寫法。

---

### 15.2 不可以同時有 sensitivity list 和 wait

教材明講：
**process 內若用了 `wait`，就不能再有 sensitivity list。**

也就是這種是錯的：

```vhdl
process(Qin, clk)
begin
    wait until (clk'EVENT and clk = '1');
    Qout <= Qin;
end process;
```

這點很重要。

---

### 15.3 沒有 sensitivity list 的 process，至少要有一個 wait

否則 process 不會 suspend，初始化時會變成無限迴圈。教材也有直接提醒這件事。

---

## 16. 你在 p.63 前一定要會辨識的三種模板

### 16.1 Dataflow 組合邏輯

```vhdl
architecture rtl of foo is
begin
    y <= a and b;
end rtl;
```

看法：`assign y = a & b;`

---

### 16.2 process 組合邏輯

```vhdl
process(a, b, sel)
begin
    if sel = '1' then
        y <= a;
    else
        y <= b;
    end if;
end process;
```

看法：`always @(*)`

---

### 16.3 process 時序邏輯

```vhdl
process(clk, rst)
begin
    if rst = '1' then
        q <= '0';
    elsif clk'EVENT and clk = '1' then
        q <= d;
    end if;
end process;
```

看法：`always @(posedge clk or posedge rst)`

---

## 17. 這份教材脈絡下，你最容易踩的 8 個坑

### 17.1 `signal` 不是單純等於 Verilog `wire`

VHDL 的 `signal` 可以是 port、內部連線、process 內被指定的目標。它比較接近「硬體訊號」，不要硬套 `wire/reg` 二分法。

### 17.2 `variable :=` 才是 process 內中間值的好朋友

教材用多個例子強調：中間計算用 variable，比較符合你要的「一步一步算完」效果。

### 17.3 同一個 process 裡多次對同一個 signal `<=`

常常只有最後一次有效，結果會和你腦中線路不同。教材專門畫了錯誤等效電路。

### 17.4 `if` 少了 `else`，組合邏輯可能變 latch

這和 Verilog 一模一樣。

### 17.5 向量方向要看 `to` / `downto`

不要只看字串常值，要同時看索引方向。

### 17.6 `when others` 很重要

等同 `default`，常拿來補齊所有情況。

### 17.7 `out` 在這份教材的規則下是只寫不讀

教材在 entity port mode 說 `out` 只能更新不能讀。你如果之後查到別的資料說某些新版 VHDL 可以讀 `out`，那是語言版本差異；但**就這份教材，先照教材規則理解最穩**。

### 17.8 `library ieee; use ieee.std_logic_1164.all;`

看到這兩行，就把它當成「我要用 `std_logic` / `std_logic_vector` 這套型別與邏輯定義」。教材在使用 `std_logic` 的例子前都會加這個。

---

## 18. 給你一份超濃縮 Verilog → VHDL 速記

```text
module                    -> entity + architecture
parameter                 -> generic / constant
input/output              -> port ... : in/out ...
wire/reg（概念上）        -> signal
always @(*)               -> process(sensitivity list)
always @(posedge clk)     -> process ... if clk'EVENT and clk='1'
assign                    -> concurrent signal assignment
=（blocking, 概念上）     -> variable :=
<=（nonblocking, 概念上） -> signal <=
?:                        -> when ... else ...
case/default              -> case ... when others ...
{a,b}                     -> a & b
!=                        -> /=
default                   -> others
```

---

## 19. 你現在該怎麼讀 p.63 前的程式

你看到任何一段 VHDL，請依序做這 5 件事：

### 19.1 先看它在 architecture 外層，還是 process 裡

* 外層：concurrent
* process 裡：sequential

### 19.2 看 `<=` 還是 `:=`

* `<=`：signal
* `:=`：variable

### 19.3 看 sensitivity list 或 wait

* `process(a,b,c)`：像 `always @(a,b,c)`
* `wait until clk'EVENT and clk='1'`：像 `@(posedge clk)`

### 19.4 看 if/case 是否補齊

* 沒補齊：可能有記憶
* 補齊：通常是組合邏輯

### 19.5 看 vector 方向

* `downto`
* `to`

只要這五步做對，你就已經能讀懂 p.63 前大部分程式。

---

## 20. 最後幫你下結論

如果你的目標是：

> 「能看懂 p.63 前所有語法」

那你真正必須吃透的核心，其實只有這 6 個：

1. `entity / architecture`
2. `signal / variable / constant`
3. `std_logic(_vector)`、`bit(_vector)`、`integer range`
4. `concurrent assignment`
5. `process + if/case/loop`
6. `signal <=` 與 `variable :=` 的更新時機差異

其中第 6 點最重要。
**Verilog 轉 VHDL，最容易死的不是 if、case、loop，而是把 `signal` 當成 process 內立即生效的暫存變數。**

---

你如果要，我下一則可以直接接著幫你做一份：

**「Verilog 工程師專用的 VHDL 速查表＋10 個最常見範例（mux / decoder / comparator / DFF / counter / onehot count）」**

讓你用最少時間把這些語法真的讀熟。
