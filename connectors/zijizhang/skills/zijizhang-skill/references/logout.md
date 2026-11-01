## 退出登录

```shell
zijizhang-cli account logout
```

### 使用示例

```shell
zijizhang-cli account logout
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |

### 返回例子

#### 成功

```json
{
    "code": 200,
    "msg": "成功退出"
}
```

#### 失败

```json
{
    "code": 400,
    "msg": "尚未登录或者未读取到登录信息"
}
```
