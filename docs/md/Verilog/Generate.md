## 一句話先懂

`parameter` 讓模組可調大小；`generate` 讓 Verilog 在模組層級自動展開重複或條件式硬體。
最容易搞混的是：`generate for` 不是程序式 `for`，它比較像「建立很多份硬體結構」。

## 核心規則

- `parameter`：模組的可調常數，常用來控制 `WIDTH`、`DEPTH`、`SIZE`、`STAGES`
- `localparam`：模組內部固定常數，外部不能改
- `generate`：寫在 module 裡，不寫在 `always` / `initial` 裡
- 常見形式：
  - `generate for`
  - `generate if ... else`
  - `generate case`
- `generate for` 的索引要用 `genvar`
- `generate` 的重點是「展開硬體結構」；`always` 裡的 `for` 是「描述程序式邏輯」

## 先建立正確觀念

### `generate` 在做什麼？

它不是在模擬時「跑很多次」，而是在設計展開時，根據規則產生多份硬體。

你可以把它想成：

- `always` 裡的 `for`：像在寫「怎麼算」
- `generate for`：像在寫「要蓋幾份一樣的電路」

### `genvar` 是什麼？

`genvar` 是給 `generate for` 用的索引。

它不是：

- `wire`
- `reg`
- `integer` 的替代品
- 真正存在的硬體暫存器

它只是工具在展開硬體時，用來數 `0,1,2,...` 的索引。

---

## 常用模板或例子

### 1. `parameter`，定義可調模組

```verilog
module adder #(parameter WIDTH = 8) (
    input  [WIDTH-1:0] a, b,
    output [WIDTH-1:0] y
);
    assign y = a + b;
endmodule
```

### 2. 例化時改參數

```verilog
adder #(.WIDTH(16)) u0 (
    .a(a),
    .b(b),
    .y(y)
);
```

### 3. `generate for`

```verilog
genvar i;
generate
    for (i = 0; i < 8; i = i + 1) begin : bit_and
        assign y[i] = a[i] & b[i];
    end
endgenerate
```

### 4. `generate if ... else`

```verilog
generate
    if (WIDTH == 1) begin : use_simple
        assign y = a ^ b;
    end
    else begin : use_vector
        assign y = a + b;
    end
endgenerate
```

### 5. `generate case`

```verilog
generate
    case (MODE)
        0: begin : mode0
            assign y = a & b;
        end
        1: begin : mode1
            assign y = a | b;
        end
        default: begin : mode_default
            assign y = a ^ b;
        end
    endcase
endgenerate
```

### 6. HDLBits 常見型：重複例化 full adder

```verilog
genvar i;
generate
    for (i = 0; i < 100; i = i + 1) begin : fa_block
        if (i == 0) begin
            full_adder fa (
                .a(a[i]),
                .b(b[i]),
                .cin(cin),
                .sum(sum[i]),
                .cout(cout[i])
            );
        end
        else begin
            full_adder fa (
                .a(a[i]),
                .b(b[i]),
                .cin(cout[i-1]),
                .sum(sum[i]),
                .cout(cout[i])
            );
        end
    end
endgenerate
```

---

## `generate for` 跟程序式 `for` 的差別

### 程序式 `for`

通常寫在 `always` / `initial` 裡，拿來描述邏輯怎麼算。

```verilog
integer i;
always @(*) begin
    for (i = 0; i < 8; i = i + 1)
        y[i] = a[i] & b[i];
end
```

### `generate for`

寫在 module scope，拿來建立很多份硬體。

```verilog
genvar i;
generate
    for (i = 0; i < 8; i = i + 1) begin : g
        assign y[i] = a[i] & b[i];
    end
endgenerate
```

### 一句話記憶

- 要**複製硬體**：想 `generate`
- 要**描述邏輯**：想程序式 `for`

---

## 快速判斷

- 要做很多份相似硬體：用 `generate`
- 要在 `always` 裡逐位處理：用程序式 `for`
- 要讓模組能切換位寬或規模：用 `parameter`
- 要在例化時改模組大小：用 `#(.WIDTH(...))`

---

## 常見地雷

- 把 `generate for` 當成程序式 `for`
- 把 `genvar` 和 `integer` 混用
- 用 input 控制 `generate if`
- 忘了 named block，例如 `begin : blk`
- 把 `parameter` 完全等同於 C/C++ 的 `#define`

---

## 和 C++ 怎麼對照

### `parameter`

可以先粗略想成比 `#define` 更聰明的常數。

但更精確地說，它比較像：

- `constexpr`
- template parameter

因為同一個 module 的不同 instance，可以各自有不同參數值。

### `generate`

可以把它想成接近「編譯期展開」：

```cpp
for (int i = 0; i < 100; i++) {
    建一顆 full_adder;
}
```

但它不是執行期 loop，而是最後展開成很多份硬體。

---

## 建議在原頁補一行導覽

你可以在「迴圈與程序控制」頁的 `for` 段落補一句：

```md
注意：`generate for` 不屬於程序式迴圈，另見〈參數化模組與 generate〉。
```

---

## 相關主題

- [模組與建模方式](./模組與建模方式.md)
- [常見資料型別](./常見資料型別.md)
- [迴圈與程序控制](./迴圈與程序控制.md)

---
