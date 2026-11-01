## 上传发票文件（仅支持 pdf/ofd）

```shell
zijizhang-cli invoice upload_invoice_file --uid='<uid>' --file='<file>'
```

别名命令：

```shell
zijizhang-cli invoice upload_invoice --uid='<uid>' --file='<file>'
```

### 参数说明

| 参数   | 类型     | 必填 | 说明 |
|:-----|:--------|:---|:---|
| uid  | string  | ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |
| file | string  | ✅  | 发票文件路径，仅支持 `.pdf` 或 `.ofd` |

### 使用示例

```shell
zijizhang-cli invoice upload_invoice_file --file='/path/to/invoice.pdf'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据，以服务端返回为准 |

data 参数说明（以服务端返回为准）

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| uid | string| 当前查询所属的 uid |
| filename | string | 文件名称 |
| file_path | string | 文件路径 |
| file_state | string | 文件状态（如：成功|拒绝） |
| file_state_desc | string | 文件状态描述，拒绝的原因或成功后文件数据的描述等信息 |


