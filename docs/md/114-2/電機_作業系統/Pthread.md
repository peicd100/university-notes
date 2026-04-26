# Pthread

![alt text](images/Pthread.png)


## pthread_create() 格式




```C
int pthread_create(
    pthread_t *thread,
    pthread_attr_t *attr,
    void *(*start_routine)(void *),
    void *arg
);
```

| 參數                                 | 意思                       |
| ---------------------------------- | ------------------------ |
| `pthread_t *thread`                | 存放建立出來的 thread ID        |
| `pthread_attr_t *attr`             | thread 屬性；可用 `NULL` 表示預設 |
| `void *(*thread_function)(void *)` | thread 要執行的 function     |
| `void *arg`                        | 傳給 thread function 的參數   |



以圖片為例


## 範例：計算結果放在 sum 中。
```c
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>

int sum;

void *runner(void *param);

int main(int argc, char *argv[]) {
    pthread_attr_t attr;
    pthread_t tid;

    if (argc != 2) {
        printf("using command %s <integer>\n", argv[1]);
        exit(1);
    }

    pthread_attr_init(&attr);
    pthread_create(&tid, &attr, runner, argv[1]); 
    pthread_join(tid, NULL);

    printf("sum: %d\n", sum);

    return 0;
}

void *runner(void *param) {   // param = argv[1]
    int i, upper = atoi((char *)param);    
    sum = 0;

    for (i = 1; i <= upper; i++) {
        sum = sum + i;
    }

    pthread_exit(0);
}
```


在 terminal 輸入：

```txt
./test 10
```


會計算：
```
sum = 1 + 2 + 3 + ... + 10 = 55
```

會輸出：

```txt
sum: 55
```

那麼：

| 變數 | 值 |
| --- | --- |
| `argc` | 2 |
| `argv[0]` | `"./test"` |
| `argv[1]` | `"5"` |

pthread_create 把數字 `argv[1]` 傳給了 void *runner(void *param) ，最後計算結果累加在全域的 sum


## 範例：計算結果用 return 的

```c
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>

void *runner(void *param);

int main(int argc, char *argv[]) {
    pthread_t tid;
    pthread_attr_t attr;
    void *result;
    int *ans;

    if (argc != 2) {
        printf("usage: %s <integer>\n", argv[0]);
        return 1;
    }

    pthread_attr_init(&attr);
    pthread_create(&tid, &attr, runner, argv[1]);

    pthread_join(tid, &result);   // 把 thread 的回傳值接回來

    ans = (int *)result;
    printf("平方總和 = %d\n", *ans);

    free(ans);
    return 0;
}

void *runner(void *param) {
    int upper = atoi((char *)param);
    int *sum = malloc(sizeof(int));
    *sum = 0;

    for (int i = 1; i <= upper; i++) {
        *sum += i * i;
    }

    pthread_exit(sum);
}
```

pthread_create 把數字 `argv[1]` 傳給了 void *runner(void *param) ，最後計算結果return，被`pthread_join(tid, &result); `接收，`&result`是創建數值別名，所以最後 result 是結果。


如果輸入：

```txt
./test 3
```

會計算：

```txt
1² + 2² + 3² = 1 + 4 + 9 = 14
```

最後輸出：
```
平方總和 = 14
```