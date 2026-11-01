## 获取利润表

```shell
zijizhang-cli report lrb <begin> <end> --uid='<uid>'
```

### 参数说明

| 参数   | 类型   | 必填 | 说明 |
|:------|:------|:---|:---|
| begin | string | ✅  | 查询开始月份，格式 `YYYY-MM`，如 `2026-01` |
| end   | string | ✅  | 查询结束月份，格式 `YYYY-MM`，如 `2026-03` |
| uid   | string | ❌  | 公司唯一标识 uid；不传则使用当前激活公司 |

### 使用示例

```shell
# 获取 2026 年 1 月的利润表
zijizhang-cli report lrb 2026-01 2026-01
# 获取 2026 年第一季度的利润表
zijizhang-cli report lrb 2026-01 2026-03
# 获取 2025 年整年的利润表
zijizhang-cli report lrb 2025-01 2025-12
# 获取指定公司的 2026 年 1 月利润表
zijizhang-cli report lrb 2026-01 2026-01 --uid='<uid>'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 利润表数据 |

**data 字段说明**

| 参数    | 类型   | 说明 |
|:------|:------|:---|
| uid   | string | 公司唯一标识 uid |
| begin | string | 查询开始月份，格式 `YYYY-MM` |
| end   | string | 查询结束月份，格式 `YYYY-MM` |
| report| list   | 利润表项目列表 |

**report 元素字段说明**

| 参数    | 类型    | 说明 |
|:------|:-------|:---|
| title | string | 项目名称 |
| bnljje| float  | 本年累计金额（元） |
| bqje  | float  | 本期金额（元） |

### 返回例子

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "uid": "98b151c07f47435e12a34f41",
    "begin": "2026-01",
    "end": "2026-01",
    "report": [
      {
        "title": "一、营业收入",
        "bnljje": 0,
        "bqje": 0
      },
      {
        "title": "减：营业成本",
        "bnljje": 0,
        "bqje": 0
      },
      {
        "title": "二、营业利润（亏损以“-”号填列）",
        "bnljje": 0,
        "bqje": 0
      },
      {
        "title": "三、利润总额（亏损以“-”号填列）",
        "bnljje": 0,
        "bqje": 0
      },
      {
        "title": "四、净利润（净亏损以“-”号填列）",
        "bnljje": 0,
        "bqje": 0
      }
    ]
  }
}
```

### 补充说明

- 该命令为只读查询，不会修改账务数据
- 通常可按月、季度、全年传入时间范围；`begin` 与 `end` 都使用 `YYYY-MM`
- `report` 按利润表展示顺序返回，适合直接顺序渲染
- `bnljje` 表示本年累计金额，`bqje` 表示本期金额；数值可能为负数，以服务端返回为准
