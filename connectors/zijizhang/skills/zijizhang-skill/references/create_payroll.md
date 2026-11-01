## 创建工资单

```shell
zijizhang-cli payroll create_payroll '<month>' '<data>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型     | 必填 | 说明                                                                                          |
|:------|:-------|:---|:--------------------------------------------------------------------------------------------|
| month | string | ✅  | 工资单月份，如 2026-04                                                                             |
| data  | string | ✅  | 工资单列表的json字符串                                                                               |
| uid   | string | ❌  | 公司唯一标识，可以不指定，如果不指定会用默认使用终端激活在用的`uid`，参见 `zijizhang-cli account get_cpy_list` 状态为 `true` 的公司 |

data（工资单列表）结构说明

传入的 json 字符串应当是一个数组，主要支持以下字段：

| 参数        | 类型     | 必填 | 描述            |
|:----------|:-------|:---|:--------------|
| xm        | string | 是  | 员工姓名          |
| zjhm      | string | 是  | 证件号码          |
| bqsr      | float  | 是  | 本期收入(元)       |
| gr_zfgjj  | float  | 否  | 个人 住房公积金(元)   |
| gr_jbpbxf | float  | 否  | 个人 基本养老保险费(元) |
| gr_jbmbxf | float  | 否  | 个人 基本医疗保险费(元) |
| gr_sybxf  | float  | 否  | 个人 失业保险费(元)   |
| qy_zfgjj  | float  | 否  | 企业 住房公积金(元)   |
| qy_jbpbxf | float  | 否  | 企业 基本养老保险费(元) |
| qy_jbmbxf | float  | 否  | 企业 基本医疗保险费(元) |
| qy_sybxf  | float  | 否  | 企业 失业保险费(元)   |
| qy_gsbxf  | float  | 否  | 企业 工伤保险费(元)   |
| lzbcj     | float  | 否  | 离职补偿金(元)      |
| qnycxjj   | float  | 否  | 全年一次性奖金(元)    |

### 使用示例

#### 创建 2026年4月 的工资单

```shell
zijizhang-cli payroll create_payroll 2026-04 '[{"xm":"夏","zjhm":"310...","bqsr":5000.00,"gr_zfgjj":500.00,"gr_jbpbxf":554.68,"gr_jbmbxf":129.68,"gr_sybxf":25.00,"gr_tq":0.00,"gr_bz":"","qy_zfgjj":500.00,"qy_jbpbxf":800.00,"qy_jbmbxf":421.46,"qy_sybxf":25.00,"qy_qt":0.00,"qy_gsbxf":8.00,"lzbcj":0.00,"qnycxjj":0.00}]'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 消息，code!=200时为失败原因      |
| data | dict   | 数据对象，包含最终状态等            |

### 补充说明

- 创建工资单前，请先调用 `zijizhang-cli payroll get_payroll_creation_status '<month>'`，确保返回状态允许创建
- 可先调用 `zijizhang-cli payroll get_preview_payroll '<month>'` 获取预览工资单，作为用户确认与调整的基础
- 请确保工资单数据准确可靠，不要在缺乏足够信息和用户确认的情况下擅自补写或捏造
- 要求：`bqsr` > `gr_zfgjj + gr_jbpbxf + gr_jbmbxf + gr_sybxf`

### 返回例子

#### 创建成功
```json
{
    "msg": "创建成功",
    "code": 200,
    "data": {
        "uid": "123451c07f47435e12a34111",
        "year": 2026,
        "month": 4
    }
}
```
