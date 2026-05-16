---
# draft: true 
date: 2024-02-06
categories:
  - 'mkdocs'
authors:
  - squidfunk
readtime: 100
---





# mkdocs 語法

<!-- more -->


## 螢光筆


```

哈哈哈 ==重點== 哈哈哈

```
/// html | div.result

哈哈哈 ==重點== 哈哈哈

///


## 重點區塊


```
!!! danger  "重點"
    如果中間沒有條件限制，最後 process 數量是：
    ```text
    2^3 = 8 processes
    ```
```
/// html | div.result
!!! danger  "重點"
    如果中間沒有條件限制，最後 process 數量是：
    ```text
    2^3 = 8 processes
    ```
///


##   支持折疊程式碼塊


````tex title="程式塊"

/// collapse-code  
```cpp
#include<bits/stdc++.h>
using namespace std;
```
///

````
//// html | div.result

/// collapse-code  
````cpp
#include<bits/stdc++.h>
using namespace std;
int main(){
    //...//
}

````
///

////


## 引用框


```

背景
/// html | div.i
背景
///

```
/// html | div.result

背景
/// html | div.i
背景
///

///

## 摺疊區塊

```
/// details | 摺疊名稱

摺疊內容

///
```
/// html | div.result
/// details | 摺疊名稱

摺疊內容

///
///

## 變更圖片大小

```
/// details | 摺疊名稱

![alt text](<images/mkdocs 語法.png>){width="60%"}

///
```
/// html | div.result

![alt text](<images/mkdocs 語法.png>){width="60%"}

///


## 嵌入 HTML

在一個 .md 中放 GPT 給的乾淨的 HTML，直接把該檔案依照以下格式：

```txt
## 範例

![[docs\md\範例.md]]

### 哈哈
```