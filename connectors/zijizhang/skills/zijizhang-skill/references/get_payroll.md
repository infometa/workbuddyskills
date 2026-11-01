## 获取工资单

```shell
zijizhang-cli payroll get_payroll '<month>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型     | 必填 | 说明                                                                                          |
|:------|:-------|:---|:--------------------------------------------------------------------------------------------|
| month | string | ✅  | 工资单月份，如 2026-04                                                                             |
| uid   | string | ❌  | 公司唯一标识，可以不指定，如果不指定会用默认使用终端激活在用的`uid`，参见 `zijizhang-cli account get_cpy_list` 状态为 `true` 的公司 |

### 使用示例

#### 获取当前公司 2026年4月 的工资单

```shell
zijizhang-cli payroll get_payroll 2026-04
```

#### 获取账号下 uid=xxxx 公司 2026年4月 的工资单

```shell
zijizhang-cli payroll get_payroll 2026-04 --uid='xxxx'
```

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
| payroll | list   | 工资单列表，如果为空数组，代表没有这个月的工资单信息        |

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
| gr_qt     | float  | 个人 其他保险费(元)   |
| gr_bz     | string | 个人 备注         |
| qy_zfgjj  | float  | 企业 住房公积金(元)   |
| qy_jbpbxf | float  | 企业 基本养老保险费(元) |
| qy_jbmbxf | float  | 企业 基本医疗保险费(元) |
| qy_sybxf  | float  | 企业 失业保险费(元)   |
| qy_gsbxf  | float  | 企业 工伤保险费(元)   |
| qy_qt     | float  | 企业 其他保险费(元)   |
| qy_bz     | float  | 企业 备注         |
| lzbcj     | float  | 离职补偿金(元)      |
| qnycxjj   | float  | 全年一次性奖金(元)    |
| gs        | float  | 个税(元)         |

其他说明

```
实发工资 = bqsr - gr_zfgjj - gr_jbpbxf - gr_jbmbxf - gr_sybxf - gr_tq - gs + qnycxjj + lzbcj
```

### 推荐展示方式

- 如果结果中只有一条记录

```markdown
| 项目 | 内容 |
| :--- | :--- |
| **基本信息** | |
| 员工姓名 | {xm} |
| 证件号码 | {zjhm} |
| **收入与奖金** | |
| 本期收入 | {bqsr} 元 |
| 全年一次性奖金 | {qnycxjj} 元 |
| 离职补偿金 | {lzbcj} 元 |
| **个人扣款明细** | |
| 住房公积金 | {gr_zfgjj} 元 |
| 养老保险 | {gr_jbpbxf} 元 |
| 医疗保险 | {gr_jbmbxf} 元 |
| 失业保险 | {gr_sybxf} 元 |
| 其他保险费 | {gr_qt} 元 |
| 个人备注 | {gr_bz} |
| **企业缴纳明细** | |
| 住房公积金 | {qy_zfgjj} 元 |
| 养老保险 | {qy_jbpbxf} 元 |
| 医疗保险 | {qy_jbmbxf} 元 |
| 失业保险 | {qy_sybxf} 元 |
| 工伤保险 | {qy_gsbxf} 元 |
| 其他保险费 | {qy_qt} 元 |
| 企业备注 | {qy_bz} |
| **税务信息** | |
| **个税** | **{gs} 元** |
```

- 如果结果中有多条记录

```markdown
| 姓名 | 证件号码 | 本期收入 | 全年一次性奖金 | 离职补偿金 | 个人-养老保险 | 个人-医疗保险 | 个人-失业保险 | 个人-其他保险 | 个人-公积金 | 个人-备注 | 企业-养老保险 | 企业-医疗保险 | 企业-失业保险 | 企业-工伤保险 | 企业-其他保险 | 企业-公积金 | 企业-备注 | 个税 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| {xm} | {zjhm} | {bqsr} | {qnycxjj} | {lzbcj} | {gr_jbpbxf} | {gr_jbmbxf} | {gr_sybxf} | {gr_qt} | {gr_zfgjj} | {gr_bz} | {qy_jbpbxf} | {qy_jbmbxf} | {qy_sybxf} | {qy_gsbxf} | {qy_qt} | {qy_zfgjj} | {qy_bz} | {gs} |
```````

### 返回例子

#### 获取成功

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
                "bqsr": 0.00,
                "gr_zfgjj": 0.00,
                "gr_jbpbxf": 0.00,
                "gr_jbmbxf": 0.00,
                "gr_sybxf": 0.00,
                "gr_qt": 0.00,
                "gr_bz": "",
                "qy_zfgjj": 0.00,
                "qy_jbpbxf": 0.00,
                "qy_jbmbxf": 0.00,
                "qy_sybxf": 0.00,
                "qy_qt": 0.00,
                "qy_bz": "",
                "qy_gsbxf": 0.00,
                "lzbcj": 0.00,
                "qnycxjj": 0.00,
                "gs": 0.00
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