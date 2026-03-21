## vector

### 宣告

需要注意的是陣列大小在變數前面，不像 C++ 是在後面。

```verilog
type [MSB:LSB] vector_name;
wire [2:0] v; // 名稱為 v 大小為 3bit 的 wire
```
MSB和LSB可以隨便定義數字，反正他就是一個範圍，然後由大到小或由小到大也完全隨意。  
但一般來說是由大到小，因為要保留”第k位元”的性質(bit4 bit3 bit2 bit1 bit0)

```text
i.......j
^       ^
MSB     LSB
```
i和j可以隨意填，順序和反序都可以，但是之後就要用相同「方向」操作

一次宣告多變數：  
```verilog
wire [3:0] a,b,c; //三個都是 [3:0];
```

#### 進階

1\.  
```verilog
wire [7:0] w;
```
宣告了一個名為 w 的 8-bit 向量，它等價於 8 條彼此獨立的 wire。

2\.  
```verilog
wire [7:0] w;
```
宣告一個 8-bit 的 wire w 。

3\.  
```verilog
reg [4:1] x;
```
宣告一個 4-bit 的 reg x。

4\.  
```verilog
output reg [8:0] y;
```
宣告一個 9-bit 的 reg，同時它也是一個輸出埠。

5\.  
```verilog
input wire [3:-2] z;
```
宣告一個 6-bit 的 wire 輸入 z，而且範圍可以包含負數索引。

6\.  
```verilog
output [3:0] a;
```
宣告一個 4-bit 的輸出 wire a。如果沒有另外寫，output 預設型別是 wire。

7\.  
```verilog
wire [0:7] b;
```
宣告一個 8-bit 的 wire b，而且這裡 b\[0\] 是最高有效位元（MSB）。

8\.  
一個 vector 的 endianness（也可比較口語地理解成「方向」），是指最低有效位元（LSB）到底是放在較小的索引，還是放在較大的索引。  
如果 LSB 在較小索引，叫 little-endian，例如 \[3:0\]。  
如果 LSB 在較大索引，叫 big-endian，例如 \[0:3\]。

9\.  
在 Verilog 裡，一旦 vector 用某種方向宣告之後，之後就必須一直用同樣的方向來使用它。  
例如，如果 vec 是用 wire \[3:0\] vec; 宣告的，那你之後寫成 vec\[0:3\] 是不合法的。  
在 endianness 上保持一致是很重要的習慣，因為如果不同方向的 vector 混在一起 assign 或一起使用，很容易出現很奇怪的 bug。

10\.  
```verilog
wire [2:0] a, c;
```
宣告兩個 3-bit vector：a 和 c。

11\.  
```verilog
assign a = 3'b101;
```
把 a 設成二進位 101。  
```verilog
3'b101：<size>'<base><digits>
```
size：這個常數要用幾個 bit 表示  
'：分隔符號  
base：進位制  
	b=2進位
	d=10進位
	h=16進位

digits：實際的數字內容。

12\.  
```verilog
assign c = b; // c = 001 <-- bug
```
因為 b 只有 1-bit，所以 assign 到 c 時就變成只有那 1 bit 被用到，結果 c 會變成像 001 這種錯誤結果。這就是 bug。

13\.  
如果兩邊位寬不同，Verilog 會依情況做：  
假設：  
```verilog
assign A = B;
```
如果 A 比 B 長：A 的高位(最左邊位元)補 0。  
如果 A 比 B 短：B 的高位(最左邊位元)截掉。  
ex.  
```verilog
assign ____ = 01011; //A = 1011
assign _____ = 0110; //A = 00110
```

### Unpacked vs. Packed Arrays

寫在前面和後面的意義不同。  
一般風格上常見：前面的是\[大:小\]，後面的用\[小:大\]。  
也就是：  
packed 常見 \[大:小\]  
unpacked 常見 \[小:大\]

#### Packed(翻譯：打包的)

```verilog
wire [9:0] v;  // v=0000000000
v = [
 v[9] v[8] v[7] v[6] v[5] v[4] v[3] v[2] v[1] v[0]
]
```
(示意)

#### Unpacked

```verilog
wire v [0:9];  // v=[0,0,0,0,0,0,0,0,0,0]
v = [
 v[0],
 v[1],
 v[2],
 v[3],
 v[4],
 v[5],
 v[6],
 v[7],
 v[8],
 v[9]
]
```
(示意)

#### Packed+Unpacked(依照常見度排序)

1\.  
```verilog
wire [1:0] v [0:3];		// v=[00,00,00,00]
					v=[
  [v[0][1], v[0][0]],
  [v[1][1], v[1][0]],
  [v[2][1], v[2][0]],
  [v[3][1], v[3][0]]
]
```
(示意)

2\.  
```verilog
wire [1:0] [3:0] v;
// v = [v[1][3] v[1][2] v[1][1] v[1][0] v[0][3] v[0][2] v[0][1] v[0][0]]
```
它和 wire \[7:0\] v; 總位元數相同都是 8 bits，但 wire \[1:0\]\[3:0\] v; 額外保留了 2 × 4-bit 的 packed 分組語意，因此可用 v\[i\]\[j\] 兩層索引。

	※ 這種多維 packed 寫法是 SystemVerilog 觀念。

3-1.  
這種二維 unpacked array 常用來表示二維資料，例如影像、座標格點、表格資料。

```verilog
wire v [0:1] [0:3];		// v=[[0,0,0,0], [0,0,0,0]]
v=[
[v[0][0], v[0][1], v[0][2], v[0][3]],
[v[1][0], v[1][1], v[1][2], v[1][3]]
]
```(示意)

```verilog
wire [1:0] v [0:1] [0:3];	// v=[[00,00,00,00], [00,00,00,00]]
   v=[
 [
  {v\[0\]\[0\]\[1\], v\[0\]\[0\]\[0\]},  
  {v\[0\]\[1\]\[1\], v\[0\]\[1\]\[0\]},  
  {v\[0\]\[2\]\[1\], v\[0\]\[2\]\[0\]},  
  {v[0][3][1], v[0][3][0]}
 ],
 [
  {v\[1\]\[0\]\[1\], v\[1\]\[0\]\[0\]},  
  {v\[1\]\[1\]\[1\], v\[1\]\[1\]\[0\]},  
  {v\[1\]\[2\]\[1\], v\[1\]\[2\]\[0\]},  
  {v[1][3][1], v[1][3][0]}
 ]
]
```(示意)

### 呼叫

```verilog
當宣告 wire [3] [4] v [1] [2] ;
```
呼叫時 v\[1\]\[2\]\[3\]\[4\]  
呼叫有兩種型態  
\[i\]：第i個  
\[i:j\]：從第i到j  
也就是先後面由左到右，再從前面由左到右。

在乎叫時，如果原本是\[0:3\]，不可呼叫\[2:0\]，方向必須相同。

## 賦值 & 大括號使用

1.大括號傳遞

```verilog
input [2:0] a,
input [2:0] b,
output [5:0] out_not
assign out_not = {\~b, \~a}; //a+b=out_not，可以直接接上去。

wire [7:0] D;
wire [3:0] A;
wire [1:0] B, C;
assign D = {A, {B, C}}; //這樣也可以接，要”接”就是用大括號，切片才用中括號“[]”。
```

不管怎麼括號，只要寬度(位寬)對、每個傳入都有接收的就是合理的。

A --- B
C --- D
.     .  
.     .  
.     .  
像上面有一一對到就好，如下：

```verilog
wire [3:0] a,b,c,d,e,f,g,h;
wire [7:0] A,B,C,D;
assign {A,B,C,D} = {a,b,c,d,e,f,g,h};
```

其實也可以像下面這樣寫  
```verilog
assign {A,{B},C,D} = {a,b,{c},d,e,f,g,h};
assign {A,B,C,D} = {a,b,{c,d,e},f,g,h};
assign {A,{B,{C}},D} = {a,b,c,d,e,f,g,h};
assign {A,B,{C,D}} = {a,b,c,d,e,f,g,h};
```

可以想像成四則運算的括號，你愛括幾個都可以，只要可以正常運算就好，就像是：  
```
3*2+10 = ((3*(2))+((10))) //亂括號，但是沒有邏輯錯誤
```

2.用大括號替代 “assign \=”：

```verilog
wire a,b,c,d,e,f,g;
wire A,B,C,D,E,F,G;
wire ab,cd;
assign {A,B,C,D,E,F,G}={a,b,c,d,e,f,g};
assign {ab,cd}={a\&b,c\&d};
```

3.合併兩個1  
```verilog
module top_module (
    input [4:0] a, b, c, d, e, f,
    output [7:0] w, x, y, z );//
    // assign { ... } = { ... };
    assign {w,x,y,z}={a,b,c,d,e,f,1'b1,1'b1};
endmodule
```

其實可以替換成

```verilog
module top_module (
    input  [4:0] a, b, c, d, e, f,
    output [7:0] w, x, y, z
);
    assign {w, x, y, z} = {a, b, c, d, e, f, 2'b11};
endmodule
```

因為位寬相同

### 重複次數

{num{vector}}
最外面的大括號不能省略，如： z = { {3{x}}  , y };

num 重複次數，必須是常數，不可是變數，也就是說可以寫：{3{1’b1}}，不能寫{n{1’b1}}。  
vector 內容，可以是 “3’b100” 也可以是 {a,b,c};

範例：

```verilog
{5{1'b1}}
= {1'b1,1'b1,1'b1,1'b1,1'b1}

{2{a,b,c}}
= {a,b,c,a,b,c}

{3{2'b01}}
= 12'b010101010101 //先開內層再開外層
```

### 重複次數範例： sign-extension(符號延伸)

把一個有號數從較小位寬擴成較大位寬時，左邊補上的新 bit 不是一律補 0，而是複製原本的最高位 MSB，也就是符號位，這樣數值正負才會保持不變。在二補數表示法裡，正數的最高位是 0，負數的最高位是 1，所以 sign-extension 本質上就是「把 sign bit 一直往左複製」。  
	  
4'b0101 是 \+5，sign-extension 後變成 8'b00000101

4'b1101 是 \-3，sign-extension 後變成 8'b11111101

把 in 延伸到和 output 一樣：

```verilog
module top_module (
    input [7:0] in,
    output [31:0] out );
    assign out = {{24{in[7]}}, in};
    // 重複 24 次 MSB
endmodule
```

### 圖案

在電路圖裡，一條線旁邊如果有斜線記號和數字，表示那是一條多位元的向量（也就是 bus / 匯流排），也就是 Packed 。  
![alt text](images/vector.png)

## 練習題

### 重複 \+ logical operators




![alt text](images/vector-1.png)
```verilog
module top_module (
    input a, b, c, d, e,
    output [24:0] out );//

    // The output is XNOR of two vectors created by
    // concatenating and replicating the five inputs.
    // assign out = \~{ ... } ^ { ... };

    assign out = \~{{{5{a}},{5{b}},{5{c}},{5{d}},{5{e}}}}^{5{a,b,c,d,e}};

endmodule
```
