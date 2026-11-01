## 获取资产负债表

```shell
zijizhang-cli report zcfzb <begin> <end> --uid='<uid>'
```

### 参数说明

| 参数   | 类型   | 必填 | 说明 |
|:------|:------|:---|:---|
| begin | string | ✅  | 查询开始月份，格式 `YYYY-MM`，如 `2026-01` |
| end   | string | ✅  | 查询结束月份，格式 `YYYY-MM`，如 `2026-03` |
| uid   | string | ❌  | 公司唯一标识 uid；不传则使用当前激活公司 |

### 使用示例

```shell
# 获取 2026 年 1 月的资产负债表
zijizhang-cli report zcfzb 2026-01 2026-01
# 获取 2026 年第一季度的资产负债表
zijizhang-cli report zcfzb 2026-01 2026-03
# 获取 2025 年整年的资产负债表
zijizhang-cli report zcfzb 2025-01 2025-12
# 获取指定公司的 2026 年 1 月资产负债表
zijizhang-cli report zcfzb 2026-01 2026-01 --uid='<uid>'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 资产负债表数据 |

**data 字段说明**

| 参数          | 类型   | 说明 |
|:------------|:------|:---|
| uid         | string | 公司唯一标识 uid |
| begin       | string | 查询开始月份，格式 `YYYY-MM` |
| end         | string | 查询结束月份，格式 `YYYY-MM` |
| zchj        | dict   | 资产合计，字段见下表 |
| fzhsyzqyhj  | dict   | 负债和所有者权益（或股东权益）合计，字段见下表 |
| report      | list   | 报表主体列表 |

**合计字段说明（`zchj` / `fzhsyzqyhj` / `hj`）**

| 参数    | 类型     | 说明      |
|:------|:-------|:--------|
| title | string | 标题      |
| ncye  | float  | 年初余额（元） |
| qmye  | float  | 期末余额（元） |

**report 元素字段说明**

| 参数          | 类型   | 说明 |
|:------------|:------|:---|
| title       | string | 报表大类，如“资产”“负债”“所有者权益（或股东权益）” |
| hj          | dict   | 当前大类合计，字段见“合计字段说明” |
| report_items| list   | 分组列表 |

**report_items 元素字段说明**

| 参数   | 类型   | 说明 |
|:-----|:------|:---|
| title| string | 分组名称，如“流动资产”“非流动资产”“流动负债” |
| items| list   | 分组下的明细项目列表 |

**items 元素字段说明**

| 参数    | 类型     | 说明      |
|:------|:-------|:--------|
| title | string | 项目名称    |
| ncye  | float  | 年初余额（元） |
| qmye  | float  | 期末余额（元） |

### 返回例子

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "zchj": {
      "title": "资产合计",
      "ncye": 0,
      "qmye": 0
    },
    "fzhsyzqyhj": {
      "title": "负债和所有者权益（或股东权益）合计",
      "ncye": 0,
      "qmye": 0
    },
    "report": [
      {
        "title": "资产",
        "hj": {
          "title": "资产合计",
          "ncye": 0,
          "qmye": 0
        },
        "report_items": [
          {
            "title": "流动资产",
            "items": [
              {
                "title": "货币资金",
                "ncye": 0,
                "qmye": 0
              },
              {
                "title": "流动资产合计",
                "ncye": 0,
                "qmye": 0
              }
            ]
          }
        ]
      },
      {
        "title": "负债",
        "hj": {
          "title": "负债合计",
          "ncye": 20000,
          "qmye": 20000
        },
        "report_items": [
          {
            "title": "流动负债",
            "items": [
              {
                "title": "其他应付款",
                "ncye": 20000,
                "qmye": 20000
              },
              {
                "title": "流动负债合计",
                "ncye": 20000,
                "qmye": 20000
              }
            ]
          }
        ]
      }
    ],
    "uid": "98b151c07f47435e12a34f41",
    "begin": "2026-01",
    "end": "2026-01"
  }
}
```

### 补充说明

- 该命令为只读查询，不会修改账务数据
- 通常可按月、季度、全年传入时间范围；`begin` 与 `end` 都使用 `YYYY-MM`
- 返回中的 `report` 为分层结构，适合按“大类 -> 分组 -> 明细项”逐层展示
- `ncye` 表示年初余额，`qmye` 表示期末余额；数值可能为负数，以服务端返回为准
