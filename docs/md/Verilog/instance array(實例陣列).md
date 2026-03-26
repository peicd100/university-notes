題目：https://hdlbits.01xz.net/wiki/Bcdadd4
![alt text](<images/instance array(實例陣列).png>)

有三種寫法

1. 直接寫
2. generate
3. instance array(實例陣列)

/// collapse-code  
```v title="第一種"
module top_module (
    input [15:0] a, b,
    input cin,
    output cout,
    output [15:0] sum
);

    wire c1, c2, c3;

    bcd_fadd u0 (
        .a   (a[3:0]),
        .b   (b[3:0]),
        .cin (cin),
        .cout(c1),
        .sum (sum[3:0])
    );

    bcd_fadd u1 (
        .a   (a[7:4]),
        .b   (b[7:4]),
        .cin (c1),
        .cout(c2),
        .sum (sum[7:4])
    );

    bcd_fadd u2 (
        .a   (a[11:8]),
        .b   (b[11:8]),
        .cin (c2),
        .cout(c3),
        .sum (sum[11:8])
    );

    bcd_fadd u3 (
        .a   (a[15:12]),
        .b   (b[15:12]),
        .cin (c3),
        .cout(cout),
        .sum (sum[15:12])
    );

endmodule
```
///

/// collapse-code  
```v title="第二種"
module top_module (
    input [15:0] a, b,
    input cin,
    output cout,
    output [15:0] sum
);

    wire [4:0] c;
    genvar i;

    assign c[0] = cin;
    assign cout = c[4];

    generate
        for (i=0; i<4; i=i+1) begin : gen_bcd
            bcd_fadd u (
                .a   (a[i*4+3 : i*4]),
                .b   (b[i*4+3 : i*4]),
                .cin (c[i]),
                .cout(c[i+1]),
                .sum (sum[i*4+3 : i*4])
            );
        end
    endgenerate

endmodule
```
///

/// collapse-code  
```v title="第三種"
module top_module (
    input [15:0] a, b,
    input cin,
    output cout,
    output [15:0] sum
);

    wire [3:0] c;

    assign c[0] = cin;

    bcd_fadd u[3:0] (
        a,
        b,
        c,
        {cout, c[3:1]},
        sum
    );
endmodule
```
///

第三種最方便
為何可以這樣寫呢？

## 語法講解

最基本語法

語法長這樣：
```v
my_module u[3:0] (...);
```
意思是建立 4 個 instance：
```v
u[3], u[2], u[1], u[0]
```

---

所以這種寫法：
```v
wire [3:0] c;
assign c[0] = cin;

bcd_fadd u[3:0] (
    a,
    b,
    c,
    {cout, c[3:1]},
    sum
);
```
本質上就是把下面 4 行壓縮成 1 行：
```v
        // [15:0]a    [15:0]b    [3:0]c {cout, c[3:1]} [15:0]sum
bcd_fadd u0(a[3:0],    b[3:0],    c[0],          c[1], sum[3:0]);
bcd_fadd u1(a[7:4],    b[7:4],    c[1],          c[2], sum[7:4]);
bcd_fadd u2(a[11:8],   b[11:8],   c[2],          c[3], sum[11:8]);
bcd_fadd u3(a[15:12],  b[15:12],  c[3],          cout, sum[15:12]);
```

他會從 LSB 開始切。

### 如果總寬度和切片寬度不一樣呢？

也就是說，實務上你可以直接記成：
```v
1) E = W      -> 廣播給每個 instance
2) E = N * W  -> 自動切成 N 片
3) 其他       -> 錯
```

