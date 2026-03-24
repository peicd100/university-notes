## 組合邏輯電路變成 latch 的問題

如果 laways 裡面寫 if 、 else 時，沒有寫清楚所有條件，就會根據上一次的值。

例如：

always @(\*) begin  
	if(a==1) b=1;  
end

上面程式碼沒有說 a==0 是多少，所以 a=0 時， b 就會根據上一次的數值。這個 always 方塊就會變成 latch。

如果本來是要寫 latch 那就沒問題。

但是如果目的是要寫 combinational 那就錯了。

## combinational 和 sequential 差在哪？

Combinational logic（組合邏輯）：輸出只看「現在的輸入」

Sequential logic（序向邏輯）：輸出除了看現在輸入，還會看「之前的狀態」

組合邏輯像計算機：你現在按什麼，它現在就算什麼

序向邏輯像計分板：它要記得前一秒的分數，所以一定有「記憶」

## 為何在寫 FF 時，@() 裡面要寫 posedge clk 而不直接寫 clk ，反正 always 不是只有在改變時才會啟動 是因為要阻止 1-\>0 的時候嗎？ posedge 指的是 0-\>1 對不對

### **先直接回答三個問題**

1. posedge 指的是 0→1 嗎？  
   對，posedge 是 positive edge（上升沿），也就是訊號從低到高的跳變。更精確地說，Verilog 的 edge control 會把 0/X/Z \-\> 1 視為 posedge，把 1/X/Z \-\> 0 視為 negedge。  
2. 為何寫 FF 時要用 @(posedge clk)，不直接寫 @(clk)？  
   因為 FF（flip-flop）是邊緣觸發 edge-triggered 元件，只應該在某一個時脈邊緣更新。@(clk) 則代表 clock 只要有任何變化都會觸發，也就是 0→1 和 1→0 都會進 block，這不符合一般 D flip-flop 的語意。  
3. 是不是因為要阻止 1→0 的時候也觸發？  
   是，但不只這樣。更本質地說，是要明確告訴工具：  
   我要的是「在上升沿取樣」的 FF，而不是「clock 一變就反應」的其他東西。  
   這樣綜合器才會推成標準的 edge-triggered flip-flop。

## @(\*) 到是啥意思，他會偵測誰的變化

這段裡，被讀到的訊號有兩個：

1. cpu\_overheated  
2. shut\_off\_computer（右邊那個 shut\_off\_computer）

所以從語意上理解，@(\*) 會把它當成大致類似：
```v
always @(cpu_overheated or shut_off_computer) begin

   ...

end
```
因為 @\* 會包含 block 中被讀取的訊號。Stack Overflow 上對 @\* 的常見解釋也是：任何在 block 內被 read（讀取）的 signal，都應該被包含進 sensitivity list。

