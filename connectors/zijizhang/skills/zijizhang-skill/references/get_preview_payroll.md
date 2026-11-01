## 获取预览工资单

```shell
zijizhang-cli payroll get_preview_payroll '<month>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型     | 必填 | 说明                                                                                          |
|:------|:-------|:---|:--------------------------------------------------------------------------------------------|
| month | string | ✅  | 工资单月份，如 2026-04                                                                             |
| uid   | string | ❌  | 公司唯一标识，可以不指定，如果不指定会用默认使用终端激活在用的`uid`，参见 `zijizhang-cli account get_cpy_list` 状态为 `true` 的公司 |

### 使用示例

#### 获取当前公司 2026年4月 的预览工资单

```shell
zijizhang-cli payroll get_preview_payroll 2026-04
```

### 补充说明

- 此操作仅结合历史工资单和相关社保数据生成概览
- 该结果不代表最终创建结果
- 最终工资单请通过 `get_payroll` 获取

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据，当code=200时返回         |

data 参数说明

| 参数      | 类型     | 说明                                |
|:--------|:-------|:----------------------------------|
| uid     | string | 当前查询所属的`uid`                      |
| year    | int    | 查询的年份                             |
| month   | int    | 查询的月份                             |
| payroll | list   | 预览的工资单数据                          |

payroll 参数说明

| 参数        | 类型     | 说明            |
|:----------|:-------|:--------------|
| xm        | string | 员工姓名          |
| zjhm      | string | 证件号码          |
| bqsr      | float  | 本期收入(元)       |
| gr_zfgjj  | float  | 个人 住房公积金(元)   |
| gr_jbpbxf | float  | 个人 基本养老保险费(元) |
| gr_jbmbxf | float  | 个人 基本医疗保险费(元) |
| gr_sybxf  | float  | 个人 失业保险费(元)   |
| qy_zfgjj  | float  | 企业 住房公积金(元)   |
| qy_jbpbxf | float  | 企业 基本养老保险费(元) |
| qy_jbmbxf | float  | 企业 基本医疗保险费(元) |
| qy_sybxf  | float  | 企业 失业保险费(元)   |
| qy_gsbxf  | float  | 企业 工伤保险费(元)   |

### 推荐展示方式

- 如果结果中只有一条记录

```markdown
| 项目 | 内容 |
| :--- | :--- |
| **员工姓名** | {xm} |
| **证件号码** | {zjhm} |
| **本期收入** | {bqsr} 元 |
| **个人社保公积金** | |
| 住房公积金 | {gr_zfgjj} 元 |
| 养老保险 | {gr_jbpbxf} 元 |
| 医疗保险 | {gr_jbmbxf} 元 |
| 失业保险 | {gr_sybxf} 元 |
| **企业社保公积金** | |
| 住房公积金 | {qy_zfgjj} 元 |
| 养老保险 | {qy_jbpbxf} 元 |
| 医疗保险 | {qy_jbmbxf} 元 |
| 失业保险 | {qy_sybxf} 元 |
| 工伤保险 | {qy_gsbxf} 元 |
```

- 如果结果中有多条记录

```markdown
| 姓名 | 证件号码 | 本期收入 | 个人公积金 | 个人-养老保险 | 个人-医疗保险 | 个人-失业保险 | 企业-公积金 | 企业-养老保险 | 企业-医疗保险 | 企业-失业保险 | 企业-工伤保险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| {xm} | {zjhm} | {bqsr} | {gr_zfgjj} | {gr_jbpbxf} | {gr_jbmbxf} | {gr_sybxf} | {qy_zfgjj} | {qy_jbpbxf} | {qy_jbmbxf} | {qy_sybxf} | {qy_gsbxf} |
```

### 返回例子

```json
{
    "code": 200,
    "msg": "",
    "data": {
        "uid": "123451c07f47435e12a34111",
        "year": 2026,
        "month": 4,
        "payroll": [
            {
                "xm": "夏天",
                "zjhm": "440000200202111111",
                "bqsr": 5000.00,
                "gr_zfgjj": 500.00,
                "gr_jbpbxf": 554.68,
                "gr_jbmbxf": 129.68,
                "gr_sybxf": 25.00,
                "qy_zfgjj": 500.00,
                "qy_jbpbxf": 800.00,
                "qy_jbmbxf": 421.46,
                "qy_sybxf": 25.00,
                "qy_gsbxf": 8.00
            }
        ]
    }
}
```

### 表格生成规则
- 必须用标准 Markdown 表格格式
- 表头、分隔线、内容行**列数必须完全一致**
- 空缺的内容可用空字符串填充
- 每一列必须对齐，不能缺失