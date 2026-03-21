## Vector

### 宣告

```verilog
type [MSB:LSB] vector_name;
wire [2:0] v;
```

```text
i.......j
^       ^
MSB     LSB
```

- `type [MSB:LSB] 名稱;`
- 位寬範圍寫在變數名稱前面。
- `MSB`、`LSB` 可自行定義。
- 可用 `[大:小]`，也可用 `[小:大]`。
- 宣告後，後續使用方向必須一致。

```verilog
wire [3:0] a, b, c;
```

- 同一行宣告多個變數時，位寬會套用到所有變數。

### 常見宣告形式

```verilog
wire [7:0] w;
reg [4:1] x;
output reg [8:0] y;
input wire [3:-2] z;
output [3:0] a;
wire [0:7] b;
wire [2:0] a, c;
```

- `wire [7:0] w;`：8-bit wire。
- `reg [4:1] x;`：4-bit reg。
- `output reg [8:0] y;`：9-bit 輸出 reg。
- `input wire [3:-2] z;`：可使用負數索引。
- `output [3:0] a;`：`output` 未另外指定時，預設為 `wire`。
- `wire [0:7] b;`：`b[0]` 是 MSB。

### 方向與索引

- `[3:0]`、`[0:3]` 都合法。
- 宣告使用哪個方向，後續切片與索引就用同方向。
- 若宣告為 `wire [3:0] vec;`，不可寫成 `vec[0:3]`。

### 數值指定

```verilog
assign a = 3'b101;
```

```verilog
<size>'<base><digits>
```

- `size`：位寬。
- `base`：進位制。
  - `b`：二進位
  - `d`：十進位
  - `h`：十六進位
- `digits`：數值內容。

### 位寬不一致時

```verilog
assign A = B;
```

- 若 `A` 比 `B` 寬：左側補 `0`。
- 若 `A` 比 `B` 窄：截掉 `B` 左側高位。

```verilog
assign c = b;
```

- 指派時需自行確認左右位寬。

### Packed 與 Unpacked

- 寫在名稱前面的維度是 packed。
- 寫在名稱後面的維度是 unpacked。
- 常見寫法：
  - packed：`[大:小]`
  - unpacked：`[小:大]`

#### Packed

```verilog
wire [9:0] v;
```

```text
v = [v[9] v[8] v[7] v[6] v[5] v[4] v[3] v[2] v[1] v[0]]
```

#### Unpacked

```verilog
wire v [0:9];
```

```text
v = [v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9]]
```

#### Packed + Unpacked

```verilog
wire [1:0] v [0:3];
```

```text
v = [
  [v[0][1], v[0][0]],
  [v[1][1], v[1][0]],
  [v[2][1], v[2][0]],
  [v[3][1], v[3][0]]
]
```

```verilog
wire [1:0] [3:0] v;
```

```verilog
wire v [0:1] [0:3];
```

```text
v = [
  [v[0][0], v[0][1], v[0][2], v[0][3]],
  [v[1][0], v[1][1], v[1][2], v[1][3]]
]
```

```verilog
wire [1:0] v [0:1] [0:3];
```

```text
v = [
  [
    {v[0][0][1], v[0][0][0]},
    {v[0][1][1], v[0][1][0]},
    {v[0][2][1], v[0][2][0]},
    {v[0][3][1], v[0][3][0]}
  ],
  [
    {v[1][0][1], v[1][0][0]},
    {v[1][1][1], v[1][1][0]},
    {v[1][2][1], v[1][2][0]},
    {v[1][3][1], v[1][3][0]}
  ]
]
```

### 呼叫與切片

```verilog
wire [3] [4] v [1] [2];
```

- 存取順序：

```verilog
v[1][2][3][4]
```

- 可用兩種形式：
  - `[i]`
  - `[i:j]`
- 使用順序：先後面宣告的維度，再前面宣告的維度；各自依左到右展開。
- 切片方向必須與原宣告方向一致。

## 賦值與大括號

### 串接

```verilog
assign out_not = {~b, ~a};
```

```verilog
wire [7:0] D;
wire [3:0] A;
wire [1:0] B, C;
assign D = {A, {B, C}};
```

- 串接使用 `{}`。
- 切片使用 `[]`。
- 巢狀大括號可自由組合。
- 左右總位寬需一致。

```verilog
wire [3:0] a, b, c, d, e, f, g, h;
wire [7:0] A, B, C, D;
assign {A, B, C, D} = {a, b, c, d, e, f, g, h};
```

```verilog
assign {A, {B}, C, D} = {a, b, {c}, d, e, f, g, h};
assign {A, B, C, D} = {a, b, {c, d, e}, f, g, h};
assign {A, {B, {C}}, D} = {a, b, c, d, e, f, g, h};
assign {A, B, {C, D}} = {a, b, c, d, e, f, g, h};
```

### 以大括號同時接多個訊號

```verilog
wire a, b, c, d, e, f, g;
wire A, B, C, D, E, F, G;
wire ab, cd;
assign {A, B, C, D, E, F, G} = {a, b, c, d, e, f, g};
assign {ab, cd} = {a & b, c & d};
```

### 合併常數

```verilog
module top_module (
    input  [4:0] a, b, c, d, e, f,
    output [7:0] w, x, y, z
);
    assign {w, x, y, z} = {a, b, c, d, e, f, 1'b1, 1'b1};
endmodule
```

```verilog
module top_module (
    input  [4:0] a, b, c, d, e, f,
    output [7:0] w, x, y, z
);
    assign {w, x, y, z} = {a, b, c, d, e, f, 2'b11};
endmodule
```

### 重複次數

```verilog
{num{vector}}
```

- 最外層大括號不可省略。
- `num` 必須是常數。
- `vector` 可為常數、變數、串接結果。

```verilog
{5{1'b1}}
= {1'b1,1'b1,1'b1,1'b1,1'b1}

{2{a,b,c}}
= {a,b,c,a,b,c}

{3{2'b01}}
= 12'b010101010101
```

### Sign extension

```verilog
module top_module (
    input [7:0] in,
    output [31:0] out
);
    assign out = {{24{in[7]}}, in};
endmodule
```

- 延伸有號數時，補上原本 MSB。

### 圖示

![alt text](images/vector.png)

- 線旁有斜線與數字時，表示該線為多位元 bus。

## 練習題

### 重複 + logical operators

![alt text](images/vector-1.png)

```verilog
module top_module (
    input a, b, c, d, e,
    output [24:0] out
);
    assign out = ~{{5{a}}, {5{b}}, {5{c}}, {5{d}}, {5{e}}} ^ {5{a,b,c,d,e}};
endmodule
