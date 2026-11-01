## 切换公司

```shell
zijizhang-cli account switch_to '<uid>'
```

### 参数说明

| 参数  | 类型     | 必填 | 说明                                                            |
|:----|:-------|:---|:--------------------------------------------------------------|
| uid | string | ✅  | 公司唯一标识，可通过 `zijizhang-cli account get_cpy_list` 查看对应的 `uid` |

### 使用示例

```shell
zijizhang-cli account switch_to 123451c07f47435e12a34111
```

### 返回参数

| 参数   | 类型     | 说明                    |
|:-----|:-------|:----------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string | 提示信息，失败时为异常信息         |

### 返回例子

#### 切换成功

```json
{
    "code": 200,
    "msg": "切换成功 xxx科技有限公司"
}
```

#### 切换失败

```json
{
    "code": 404,
    "msg": "没有找到符合uid=xxxx条件的公司信息"
}
```
