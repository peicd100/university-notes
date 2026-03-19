# vector

## 宣告

需要注意的是陣列大小在變數前面，不像 C++ 是在後面。

type \[MSB:LSB\] vector\_name;  
wire \[2:0\] v; // 名稱為 v 大小為 3bit 的 wire  
MSB和LSB可以隨便定義數字，反正他就是一個範圍，然後由大到小或由小到大也完全隨意。  
但一般來說是由大到小，因為要保留”第k位元”的性質(bit4 bit3 bit2 bit1 bit0)

i.......j  
^       ^  
MSB     LSB    
i和j可以隨意填，順序和反序都可以，但是之後就要用相同「方向」操作

一次宣告多變數：  
wire \[3:0\] a,b,c; //三個都是 \[3:0\];

### 進階

1\.  
wire \[7:0\] w;  
宣告了一個名為 w 的 8-bit 向量，它等價於 8 條彼此獨立的 wire。

2\.  
wire \[7:0\] w;  
宣告一個 8-bit 的 wire w 。

3\.  
reg \[4:1\] x;  
宣告一個 4-bit 的 reg x。

4\.  
output reg \[8:0\] y;  
宣告一個 9-bit 的 reg，同時它也是一個輸出埠。

5\.  
input wire \[3:-2\] z;  
宣告一個 6-bit 的 wire 輸入 z，而且範圍可以包含負數索引。

6\.  
output \[3:0\] a;  
宣告一個 4-bit 的輸出 wire a。如果沒有另外寫，output 預設型別是 wire。

7\.  
wire \[0:7\] b;  
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
wire \[2:0\] a, c;  
宣告兩個 3-bit vector：a 和 c。

11\.  
assign a \= 3'b101;   
把 a 設成二進位 101。  
3'b101：\<size\>'\<base\>\<digits\>  
size：這個常數要用幾個 bit 表示  
'：分隔符號  
base：進位制  
	b=2進位  
	d=10進位  
	h=16進位  
digits：實際的數字內容。

12\.  
assign c \= b; // c \= 001 \<-- bug  
因為 b 只有 1-bit，所以 assign 到 c 時就變成只有那 1 bit 被用到，結果 c 會變成像 001 這種錯誤結果。這就是 bug。

13\.  
如果兩邊位寬不同，Verilog 會依情況做：  
假設：  
assign A \= B;  
如果 A 比 B 長：A 的高位(最左邊位元)補 0。  
如果 A 比 B 短：B 的高位(最左邊位元)截掉。  
ex.  
assign \_\_\_\_ \= 01011; //A \= 1011  
assign \_\_\_\_\_ \= 0110; //A \= 00110

## Unpacked vs. Packed Arrays

寫在前面和後面的意義不同。  
一般風格上常見：前面的是\[大:小\]，後面的用\[小:大\]。  
也就是：  
packed 常見 \[大:小\]  
unpacked 常見 \[小:大\]

### Packed(翻譯：打包的)

wire \[9:0\] v;  // v=0000000000  
v \= \[  
 v\[9\] v\[8\] v\[7\] v\[6\] v\[5\] v\[4\] v\[3\] v\[2\] v\[1\] v\[0\]  
\](示意)

### Unpacked

wire v \[0:9\];  // v=\[0,0,0,0,0,0,0,0,0,0\]  
v \= \[  
 v\[0\],  
 v\[1\],  
 v\[2\],  
 v\[3\],  
 v\[4\],  
 v\[5\],  
 v\[6\],  
 v\[7\],  
 v\[8\],  
 v\[9\]  
\](示意)

### Packed+Unpacked(依照常見度排序)

1\.  
wire \[1:0\] v \[0:3\];		// v=\[00,00,00,00\]  
					v=\[  
  \[v\[0\]\[1\], v\[0\]\[0\]\],  
  \[v\[1\]\[1\], v\[1\]\[0\]\],  
  \[v\[2\]\[1\], v\[2\]\[0\]\],  
  \[v\[3\]\[1\], v\[3\]\[0\]\]  
\](示意)

2\.  
wire \[1:0\] \[3:0\] v;		  
// v \= \[v\[1\]\[3\] v\[1\]\[2\] v\[1\]\[1\] v\[1\]\[0\] v\[0\]\[3\] v\[0\]\[2\] v\[0\]\[1\] v\[0\]\[0\]\]    
它和 wire \[7:0\] v; 總位元數相同都是 8 bits，但 wire \[1:0\]\[3:0\] v; 額外保留了 2 × 4-bit 的 packed 分組語意，因此可用 v\[i\]\[j\] 兩層索引。

	※ 這種多維 packed 寫法是 SystemVerilog 觀念。

3-1.  
這種二維 unpacked array 常用來表示二維資料，例如影像、座標格點、表格資料。

wire v \[0:1\] \[0:3\];		// v=\[\[0,0,0,0\], \[0,0,0,0\]\]  
v=\[   
\[v\[0\]\[0\], v\[0\]\[1\], v\[0\]\[2\], v\[0\]\[3\]\],  
\[v\[1\]\[0\], v\[1\]\[1\], v\[1\]\[2\], v\[1\]\[3\]\]    
\](示意)

wire \[1:0\] v \[0:1\] \[0:3\];	// v=\[\[00,00,00,00\], \[00,00,00,00\]\]  
   v=\[  
 \[  
  {v\[0\]\[0\]\[1\], v\[0\]\[0\]\[0\]},  
  {v\[0\]\[1\]\[1\], v\[0\]\[1\]\[0\]},  
  {v\[0\]\[2\]\[1\], v\[0\]\[2\]\[0\]},  
  {v\[0\]\[3\]\[1\], v\[0\]\[3\]\[0\]}  
 \],  
 \[  
  {v\[1\]\[0\]\[1\], v\[1\]\[0\]\[0\]},  
  {v\[1\]\[1\]\[1\], v\[1\]\[1\]\[0\]},  
  {v\[1\]\[2\]\[1\], v\[1\]\[2\]\[0\]},  
  {v\[1\]\[3\]\[1\], v\[1\]\[3\]\[0\]}  
 \]  
\](示意)

## 呼叫

當宣告 wire \[3\] \[4\] v \[1\] \[2\] ;  
呼叫時 v\[1\]\[2\]\[3\]\[4\]  
呼叫有兩種型態  
\[i\]：第i個  
\[i:j\]：從第i到j  
也就是先後面由左到右，再從前面由左到右。

在乎叫時，如果原本是\[0:3\]，不可呼叫\[2:0\]，方向必須相同。

# 賦值 & 大括號使用

1.大括號傳遞

input \[2:0\] a,  
input \[2:0\] b,  
output \[5:0\] out\_not  
assign out\_not \= {\~b, \~a}; //a+b=out\_not，可以直接接上去。

wire \[7:0\] D;  
wire \[3:0\] A;  
wire \[1:0\] B, C;  
assign D \= {A, {B, C}}; //這樣也可以接，要”接”就是用大括號，切片才用中括號“\[\]”。

不管怎麼括號，只要寬度(位寬)對、每個傳入都有接收的就是合理的。

A \--- B  
C \--- D  
.     .  
.     .  
.     .  
像上面有一一對到就好，如下：

wire \[3:0\] a,b,c,d,e,f,g,h;  
wire \[7:0\] A,B,C,D;  
assign {A,B,C,D} \= {a,b,c,d,e,f,g,h};

其實也可以像下面這樣寫  
assign {A,{B},C,D} \= {a,b,{c},d,e,f,g,h};  
assign {A,B,C,D} \= {a,b,{c,d,e},f,g,h};  
assign {A,{B,{C}},D} \= {a,b,c,d,e,f,g,h};  
assign {A,B,{C,D}} \= {a,b,c,d,e,f,g,h};

可以想像成四則運算的括號，你愛括幾個都可以，只要可以正常運算就好，就像是：  
3\*2+10 \= ((3\*(2))+((10))) //亂括號，但是沒有邏輯錯誤

2.用大括號替代 “assign \=”：

wire a,b,c,d,e,f,g;  
wire A,B,C,D,E,F,G;  
wire ab,cd;  
assign {A,B,C,D,E,F,G}={a,b,c,d,e,f,g};  
assign {ab,cd}={a\&b,c\&d};

3.合併兩個1  
module top\_module (  
    input \[4:0\] a, b, c, d, e, f,  
    output \[7:0\] w, x, y, z );//  
    // assign { ... } \= { ... };  
    assign {w,x,y,z}={a,b,c,d,e,f,1'b1,1'b1};  
endmodule

其實可以替換成

module top\_module (  
    input  \[4:0\] a, b, c, d, e, f,  
    output \[7:0\] w, x, y, z  
);  
    assign {w, x, y, z} \= {a, b, c, d, e, f, 2'b11};  
endmodule

因為位寬相同

## 重複次數

{num{vector}}  
最外面的大括號不能省略，如： z \= { {3{x}}  , y };

num 重複次數，必須是常數，不可是變數，也就是說可以寫：{3{1’b1}}，不能寫{n{1’b1}}。  
vector 內容，可以是 “3’b100” 也可以是 {a,b,c};

範例：

{5{1'b1}}   
\= {1'b1,1'b1,1'b1,1'b1,1'b1}

{2{a,b,c}}  
\= {a,b,c,a,b,c}

{3{2'b01}}  
\= 12'b010101010101 //先開內層再開外層

## 重複次數範例： sign-extension(符號延伸)

把一個有號數從較小位寬擴成較大位寬時，左邊補上的新 bit 不是一律補 0，而是複製原本的最高位 MSB，也就是符號位，這樣數值正負才會保持不變。在二補數表示法裡，正數的最高位是 0，負數的最高位是 1，所以 sign-extension 本質上就是「把 sign bit 一直往左複製」。  
	  
4'b0101 是 \+5，sign-extension 後變成 8'b00000101

4'b1101 是 \-3，sign-extension 後變成 8'b11111101

把 in 延伸到和 output 一樣：

module top\_module (  
    input \[7:0\] in,  
    output \[31:0\] out );  
    assign out \= {{24{in\[7\]}}, in};  
    // 重複 24 次 MSB  
endmodule

## 圖案

在電路圖裡，一條線旁邊如果有斜線記號和數字，表示那是一條多位元的向量（也就是 bus / 匯流排），也就是 Packed 。  
![][image1]

# 練習題

## 重複 \+ logical operators

![][image2]

module top\_module (  
    input a, b, c, d, e,  
    output \[24:0\] out );//

    // The output is XNOR of two vectors created by   
    // concatenating and replicating the five inputs.  
    // assign out \= \~{ ... } ^ { ... };  
      
    assign out \= \~{{{5{a}},{5{b}},{5{c}},{5{d}},{5{e}}}}^{5{a,b,c,d,e}};

endmodule  


[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAAA/CAIAAAC3jNulAAAGcElEQVR4Xu2abUxTVxjHS1tEEMVYoh8k+yCuFo1ilAxRTJBE1KBCfFtMI2B0TBNFRwwvipqgU2KiU/GLxhDr1m2kKlnmujrJAkNWEmpUTKagEnWCiCIqChOQ7k+vuzmc3t5e3VHv2PnFmHvP87Tc+8tzznmOonEPUjQEe/fupcPvDA09MFjgQhnDhTKGC2UMF8oYLpQxXChjuFDGcKGM4UIZw4UyhgtlDBfKmEEr9PDhw/TQe2FwCr127Vp4eDg9+l5QtdCuri6r1ZqXl1dUVFRTU0OGLBbLhQsXyJFTp06dO3cOF42NjcuWLRs2bNhXHqqrq4uLi10uF5nc1NSE0IMHD8hBJqhX6M2bN6OiosaNG5eRkbFw4cIhQ4bk5+eLUZPJlJubS6S7ExIS0tPTcXHgwIHY2NigoKB0D2fOnElOTp4/fz6ZXFhYOHr06J6eHnKQCeoVCguzZ8/u7OwUbisqKgICAsrLy4VbGaEAJUlOeZvNptPp7t+/L45MmDAhOztbvGWISoViMuKBzp49Sw4mJiZiLgvXbyT05cuXBoNh//79wm1tbS2+/OrVq2ICQ1QqtKqqCg/U0NBADmZlZU2bNk24fiOhYOPGjdHR0cL1pk2bYmJiyChDVCoUWxAe6MaNG+Tg5s2bRSneQuPi4mSEXrx4EV9YV1fX29s7ZsyYI0eOkFGGqFQo9ne9Xm+328nBefPmpaamCtdTpkxZt24dGY2IiJAR6vZ8ZPv27egEsF89fvyYivrlyZMnSroClQoFSUlJmMVY/oRblJhWq8WWLdwuWrRo/PjxYjLU4wVEoZWVlbi9d++emADQJ02ePHnNmjUrVqwgxxWybdu2kJCQXbt20YGBqFdoW1sb2qapU6eiD127di36SvwtRrHdw++kSZNycnLgEZmzZs0Shb569QrzGuvDzp07T58+LQy2trYGBgZCClX4SsDDDB8+HI52795NxwYiIxTrWElJSXNzMznICv9CwdOnT9Gub9iwYevWrefPn6eiqFnYRMUdPHgQspBQVlYmRjGChRI9rMPhEAePHz+ODhTLqDiiEJQnBI0aNerZs2d0bCAyQgGKA82f0WjEG+Fg8hZP4gtFQlWC8vJ0+xMKtmzZghB2iKFDh2LapaSk4NSnZHWW578kFNWkUVaebgVC3R6nsCnkoGChFcsXVq2CggKn04n1iv6AAqSF4hj+s8ooLS0NDg7WeHY8OiYFKXT16tV0+B+WLl2KwzSZDAI94MfFx8fjAP3w4UNakG/6hfb29TQ//9PVUv3tH8cKndnmn5ISTpg+/sKgD9VSP+l/CNYEFK+wr1L9uCSaL2ty4r+LTCyNmmH96JNvIvAHFwtOxIw0jAxTDSNGjMBb4fUwQ+mYD0gpMp/CN+t0OjKZJMADjoV79uy5dOlSX18f7c+L/gqtuOtY8kN87Nf9QhNLTcfqXp+11UN+fj5ez2AwKFk9BUgvvtZQnBFwysD5gkzGTMd8x0q9atUqm82GHPpjsmjS7AvmlJpyKz9L+N6YUjbj96Zf6ZQPzaNHj0JDQ/GqKBM65hvSkaRQwaawgGIvwo6EUp0+fTqSL1++TGcrRmOrt3T2PM/8ZcmnP85p6rhLx1UAekaNpzw7OjromG/khQo2EYJEFGNaWhoabbTbVNpb0D/l2/9qy/vt866e1//iqSqwwwrl6S1FHhmh7e3tM2fOjIuLKyoqunLlChn69/QL7ehWujC9f4TyDA8Pf6PydMsKbWhoYFKMkkj3oerh+vXrZrN53759dMAfMkLfKWoX+tZwoYzhQhnDhUrz4sULnKaXL1+O40pycvLRo0e7u7vpJCm4UAngzmg0omGEkZMnT2ZmZqKFysjIoPOk4EKlaWxsJE/QBQUFOFyjkSRSpOFCFVFSUqLX63EYpQNecKH+wQowceLEuXPn0gEpuFCfuFyuHTt2LF68GMf5rKys1tZWOkMKLtQnDocDNk0mU1BQ0MqVK51OJ50hBRfqHxzA169fr9PpWlpa6JgXXKgisB2FhIQUFxfTAS+4UEXcunVLq9UeOnSIDnjBhUpw+/bt8vJy8b9z79y5Yzabg4OD6+vrByZKwIVKUFtbi40oLCwsOjo6MjISasaOHSv+WpU8XKg02IjsdrvFYrFarVVVVeLvrPmFC2UMF8oYLpQxXChjuFDGcKGM4UIZw4UyhgtlDBfKmA8l9G9V4i5slxruGgAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,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>