## 提交审账

```shell
zijizhang-cli todo set_month_audited '<year>' '<month>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型  | 必填 | 说明 |
|:------|:------|:---|:---|
| year  | int   | ✅  | 年份，如 2026 |
| month | int   | ✅  | 月份(1-12)，如 3 |
| uid   | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid` |

### 使用示例

```shell
zijizhang-cli todo set_month_audited 2026 3
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据（可能为空对象）              |

data 参数说明

| 参数   | 类型     | 说明           |
|:-----|:-------|:-------------|
| uid  | string | 当前设置所属的 `uid` |

补充说明：

- 命令帮助中说明 `data` 常见字段为 `uid`，其余字段以服务端返回为准
