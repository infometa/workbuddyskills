## 获取银行文件列表

```shell
zijizhang-cli bank bank_file_list --uid='<uid>' --current='<current>'
```

### 参数说明

| 参数      | 类型  | 必填 | 说明 |
|:--------|:------|:---|:---|
| uid     | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |
| current | int   | ❌  | 页码，默认 1 |

### 使用示例

```shell
zijizhang-cli bank bank_file_list --current=1
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据，当 code=200 时返回 |

data 参数说明（以服务端返回为准）

| 参数     | 类型   | 说明 |
|:--------|:------|:---|
| uid     | string| 当前查询所属的 uid |
| current | int   | 当前页码 |
| total   | int   | 总数 |
| items   | list  | 文件列表 |

items 元素参数说明

| 参数           | 类型     | 说明 |
|:--------------|:--------|:---|
| bank_name     | string  | 银行名称 |
| file_type     | string  | 文件类型（如：回单文件｜回单明细） |
| file_name     | string  | 文件名 |
| upload_time   | string  | 上传时间 |
| status        | string  | 状态 |
| refuse_reason | string  | 拒绝原因 |
| book_time     | string  | 所属月份 |

