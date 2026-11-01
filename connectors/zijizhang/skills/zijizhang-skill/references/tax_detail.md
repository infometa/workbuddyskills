## 获取当前需要申报的税种列表和申报情况

```shell
zijizhang-cli tax tax_detail --uid='<uid>'
```

### 参数说明

| 参数  | 类型     | 必填 | 说明                    |
|:----|:-------|:---|:----------------------|
| uid | string | ❌  | 公司唯一标识uid；不传则使用当前激活公司 |

### 使用示例

```shell
zijizhang-cli tax tax_detail

zijizhang-cli tax tax_detail --uid='<uid>'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 需要申报的信息 |

**data 字段说明**

| 参数       | 类型   | 说明 |
|:---------|:------|:---|
| uid      | string | 当前查询所属 uid |
| dt       | string | 服务器当前时间，格式 `YYYY-MM-DD hh:mm:ss` |
| sssj     | string | 所属税局 |
| need_tax | array  | 需申报税种信息列表 |

**need_tax 元素字段说明**

| 参数    | 类型   | 说明 |
|:------|:------|:---|
| sz    | string | 税种 |
| sm    | string | 税目 |
| sbzq  | string | 申报周期 |
| yxqq  | string | 有效期起 |
| yxqz  | string | 有效期止 |
| sbjzrq| string | 申报截止日期 |
| sbzt  | int    | 申报状态，`1` 代表申报成功 |
| sbrq  | string | 申报日期，格式 `YYYY-MM-DD`；未申报时可能返回 `null` |
| sbjt  | string | 申报截图 url；未申报时可能返回 `null` |

### 返回例子

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "dt": "2026-01-01 10:53:10",
    "sssj": "广东省电子税局",
    "uid": "xxxx",
    "need_tax": [
      {
        "sz": "个人所得税",
        "sm": "工资薪金所得",
        "sbzq": "月",
        "yxqq": "2023-07-01",
        "yxqz": "9999-12-31",
        "sbjzrq": "2026-04-20",
        "sbzt": 0,
        "sbrq": null,
        "sbjt": null
      }
    ]
  }
}
```

### 补充说明

- 该命令用于查看当前公司需要申报的税种，以及各税种当前申报状态
- `need_tax` 为空时，通常表示当前没有需要申报的税种，具体以服务端返回为准
- `sbzt=1` 表示对应税种已申报成功；其他状态值请结合服务端实际返回和 `sbrq`、`sbjt` 一起判断
