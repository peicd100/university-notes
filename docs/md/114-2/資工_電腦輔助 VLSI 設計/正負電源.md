## 電源英文

VDD：MOS / CMOS 很常見，通常表示正電源。

VCC：BJT / TTL 歷史命名很常見，也常拿來表示正電源。

VIN：Voltage In，輸入電源。

VBAT / VBATT：電池電源。

VBUS：常見於 USB 或匯流排供電命名。

AVDD：Analog VDD，類比電源。

DVDD：Digital VDD，數位電源。

VDDIO / VCCIO / VIO：I/O 介面的供電。

VEE：雙電源類比電路常見的負電源名稱。

\+3.3V / \+5V / \+12V / 3V3：直接用電壓值命名，在實務原理圖與 EDA 工具中非常常見。KiCad/Altium/JITX 這類工具與文件都直接用 VCC、GND、+3V3、+5V、3V3 這種名字當 power net label。

## 接地英文

GND / Ground：最通用，表示電路的 0V 參考點或共同回流點。

VSS：在 MOS / CMOS 語境很常見，通常就是低電位電源軌，很多單電源數位電路裡會等同於地。

AGND：Analog Ground，類比地。

DGND：Digital Ground，數位地。

PGND：Power Ground，大電流/電源切換那一側的地。

SGND：Signal Ground，訊號地；有些資料把它視為較安靜、給小訊號當參考的地。

PE / Protective Earth：保護接地，偏電力/安規語境。

Chassis / Chassis Ground：機殼地。  
後面這兩個比較常見在系統、設備、EMI/安規文件，不是你目前 CMOS 邏輯圖最常看到的主角。