## 提交审账前确认

```shell
zijizhang-cli todo before_set_month_audited '<year>' '<month>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型  | 必填 | 说明 |
|:------|:------|:---|:---|
| year  | int   | ✅  | 年份，如 2026 |
| month | int   | ✅  | 月份(1-12)，如 3 |
| uid   | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid` |

### 使用示例

```shell
zijizhang-cli todo before_set_month_audited 2026 3
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据，当 code=200 时返回       |

data 参数说明

| 参数    | 类型    | 说明 |
|:------|:--------|:---|
| uid   | string  | 当前设置所属的 `uid` |
| year  | int     | 年 |
| month | int     | 月 |
| state | bool    | 是否允许提交审账 |
| reason| string  | 不允许时的原因；若服务端返回更细粒度提示，也应一并展示给用户 |

**state 取值说明**

| state 值 | 说明 |
|:--------|:---|
| `可以提交审账` | 可直接调用 `set_month_audited` 提交审账 |
| `需要确认` | 需向用户展示 `reason` 内容，用户确认同意后再调用 `set_month_audited` 提交审账 |
| `不能提交审账` | 不允许提交审账，向用户展示 `reason` 说明原因，不可调用 `set_month_audited` |
