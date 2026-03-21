# 模擬控制與 System Tasks

## 一句話先懂

`timescale`、`#delay` 與大多數 system tasks 都偏向模擬用途。  
它們很重要，但和可綜合 RTL 主邏輯不是同一層事情。

## 核心規則

- ``timescale` 是 compiler directive，不是 `always` 裡的敘述。
- ``timescale 1ns/1ps` 代表時間單位是 `1ns`，模擬精度是 `1ps`。
- `#delay` 是模擬延遲，常見於 testbench。
- `$display`：立刻印一次。
- `$monitor`：參數任一值改變時，自動印出最新值。
- `$time`：取得目前模擬時間。
- `$finish`：結束模擬。
- `$stop`：暫停模擬，常用於除錯。

## 常用模板或例子

### ``timescale`

```verilog
`timescale 1ns/1ps
```

- `#1` 代表 `1ns`
- 模擬器能分辨到 `1ps`

### `#delay`

```verilog
initial begin
    a = 1'b0;
    #10 a = 1'b1;
end
```

- 常用來安排 testbench 刺激時序。

### `$display`

```verilog
initial begin
    a = 1'b0;
    b = 1'b1;
    $display("a=%b b=%b", a, b);
end
```

### `$monitor`

```verilog
initial begin
    $monitor("time=%0t a=%b b=%b", $time, a, b);
end
```

### `$finish` / `$stop`

```verilog
initial begin
    #100 $finish;
end
```

```verilog
initial begin
    if (error)
        $stop;
end
```

## 常見地雷

- 把 `#delay` 當成一般可綜合 RTL 主力。
- 忘記 ``timescale` 會影響你看到的 `#1` 到底代表多長。
- 以為 `$display` 會一直更新，它其實只在執行到那一行時印一次。
- 忘記在 testbench 結束時加 `$finish`，讓模擬一直跑下去。

## 相關主題

- [always、initial 與事件控制](always、initial 與事件控制.md)
- [迴圈與程序控制](迴圈與程序控制.md)
