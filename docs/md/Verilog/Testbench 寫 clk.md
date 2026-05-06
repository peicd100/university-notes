# Testbench 寫 clk



## repeat

```v
initial begin
    clock = 1'b0;
    repeat (30)
        #10 clock = ~clock;
end
```

## always

always 不用放在 initial 裡面。

```v
initial begin
    clock = 1'b0;
end

initial #300 $finish;

always #10 clock = ~clock;
```

## forever

```v
initial begin
    clock = 0;
    forever #10 clock = ~clock;
end
```



## 實際推薦寫法

```v
`timescale 1ns/1ps

module tb;

    reg clock;
    reg reset;

    initial begin
        clock = 1'b0;
        forever #10 clock = ~clock;
    end

    initial begin
        reset = 1'b1;
        #25 reset = 1'b0;

        #300 $finish;
    end

endmodule
```


## 題外話


這三種都可以用 begin 和 end 包起來。

---

然後
```v
#10 clock = ~clock;
```
和
```v
#10;
clock = ~clock;
```
是一樣的但是兩行就要用 begin 、 end。
```v
initial begin
    clock = 1'b0;

    forever begin
        #10;
        clock = ~clock;
    end
end
```