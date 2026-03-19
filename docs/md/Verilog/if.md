```.v
assign out = (sel == 2'b00) ? in0 :
(sel == 2'b01) ? in1 :
(sel == 2'b10) ? in2 :
in3;
```
