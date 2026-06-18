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
/// danger|重點
    如果中間沒有條件限制，最後 process 數量是：
    ```text
    2^3 = 8 processes
    ```
///
```
/// html | div.result
/// danger|重點
    如果中間沒有條件限制，最後 process 數量是：
    ```text
    2^3 = 8 processes
    ```
///
///


##   程式碼塊

> hl_lines 中與順序無關，像是 27 可以放最前面

````tex title="程式塊"

/// collapse-code  
``` cpp linenums="1" hl_lines="27 6-8 13-13 16"  title="code"
#include <bits/stdc++.h>
using namespace std;

#define int long long

signed main() {
    int n;
    cin >> n;

    vector<int> v(n + 1);

    for (int i = 1; i <= n; i++) {
        cin >> v[i];
    }

    vector<int> dp(n + 1);

    for (int i = 0; i <= n; i++) {
        if (i <= 2)
            dp[i] = v[i];
        else
            dp[i] = min(dp[i - 1], dp[i - 2]) + v[i];
    }

    cout << dp[n];

    return 0;
}
```
///

````
//// html | div.result

/// collapse-code  
``` cpp linenums="1" hl_lines="27 6-8 13-13 16"  title="code"
#include <bits/stdc++.h>
using namespace std;

#define int long long

signed main() {
    int n;
    cin >> n;

    vector<int> v(n + 1);

    for (int i = 1; i <= n; i++) {
        cin >> v[i];
    }

    vector<int> dp(n + 1);

    for (int i = 0; i <= n; i++) {
        if (i <= 2)
            dp[i] = v[i];
        else
            dp[i] = min(dp[i - 1], dp[i - 2]) + v[i];
    }

    cout << dp[n];

    return 0;
}
```
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

![alt text](<images/mkdocs 語法.png>){width="60%"}

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


## 嵌入網頁/PDF


```tex title="雲端 PDF"

<iframe src="https://drive.google.com/file/d/1oO0sJSXeb9vxLrz9AjAvrsnqDtLMqWKz/preview" width="100%" height="300px"></iframe>


```
/// html | div.result

<iframe src="https://drive.google.com/file/d/1oO0sJSXeb9vxLrz9AjAvrsnqDtLMqWKz/preview" width="100%" height="300px"></iframe>


///


```tex title="docs/ 中的 PDF"

<iframe src="\筆記素材\Dijkstra.pdf" width="100%" height="550px"></iframe>


```
/// html | div.result

<iframe src="\筆記素材\Dijkstra.pdf" width="100%" height="550px"></iframe>

///

