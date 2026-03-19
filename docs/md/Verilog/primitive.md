primitive
直接寫 true table 的電路模組，可以有多個 input ，但是 output 只能有一個，而且定義時要放最前面。

```v
primitive p(
    output z,  		//第一個只能放 output ，而且 output 只能有一個。
    input x,y
    );
    table
        0 0  : 0;  // x y : z;
        0 1  : 1;
        1 0  : 0;
        1 1  : 0;
    endtable
endprimitive
```

