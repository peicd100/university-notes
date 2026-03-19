# module

## 兩種寫 input 和 output 的方式

```verilog
module f1(  
    input a,b,  
    output c,d  
);  
    assign c = a & b;  
    assign d = a | b;  
endmodule
```

```verilog
module f2(a,b,c,d);  
    input a,b;  
    output c,d;  
     
    assign c = a & b;  
    assign d = a | b;  
endmodule
```


較推薦第一種