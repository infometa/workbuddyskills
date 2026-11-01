# 数据标签域 — 人群包写操作契约

> 概念知识：`references/domains/data-tag.md`（人群包状态机与规则表达式），运营流程：`references/flows/data-tag.md`；人群包现值读取（分页/详情/任务记录/成员）先读 `crowd-query.md`，运算符先查 `operator.md`，动态人群包与批量加用户见 `manual-tag-action.md`。ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、影响说明和回读纪律（确认由运行时权限模式兜底）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：data-tag.crowd.create-rule-select 创建规则圈选 · data-tag.crowd.update 更新人群包 · data-tag.crowd.online 上线 · data-tag.crowd.offline 下线 · data-tag.crowd.delete 删除 🔴 · data-tag.crowd.upload 文件上传创建/追加 🔴

---

## ✅ 创建规则圈选 — ops.data-tag.crowd.create-rule-select

- 提交后立即 CALCULATING，必须轮询任务记录（`crowd.task-records`），不得称为已生效

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| crowdName | String | ✅ | 人群包名称（≤50） |
| queryCondition | String | ✅ | 规则条件 **JSON 字符串**，必须序列化后传（结构见下） |
| calcPeriodType | Integer | ✅ | 计算周期：0=不刷新、1=每天、2=每周、3=每月 |
| calcPeriodValue | String | — | 周期日期（周几/月日，字符串，周期性时传） |

**`queryCondition`（JSON 字符串）内部结构**：

顶层字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| combinations | Array | ✅ | 规则组合列表，**非空**（空/缺失整次圈选报错）；组内空 rules 的组合被**静默跳过** |
| combinationLogic | String | — | 组间逻辑，默认 `AND` |
| combinationLogics | String[] | — | 可选数组：`combinationLogics[i]` 表示**第 i 与第 i+1 个组合之间**的逻辑；提供时优先于 combinationLogic |

`combinations[]` 子结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rules | Array | ✅ | 组内规则列表 |
| ruleLogic | String | — | 组内逻辑，默认 `AND` |
| ruleLogics | String[] | — | 可选数组：`ruleLogics[i]` 表示**第 i 与第 i+1 条规则之间**的逻辑；提供时优先于 ruleLogic |

`rules[]` 子结构（规则项）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tagId | String | ✅ | 被引用标签 ID（十进制字符串）。⚠️ 该标签**必须存在且已配置英文名**（tagNameEn，计算引擎按英文名定位位图），否则整次圈选报错；不传当前未消费的 `field`（旧格式字段，忽略） |
| operator | String | ✅ | 运算符，见下表；**未知运算符直接报错** |
| value | String | ✅ | 条件值（字符串形态）。`in` / `not_in` 为**逗号分隔多值**（如 `"1,2,3"`）；`between` 为**恰好两值逗号分隔**（`"100,500"`，非两值报错）；`eq` 值为 `0`/`0.0` 时服务端自动补「或为空」匹配（数值型标签兼容） |

**运算符（与 `ops.data-tag.operator.list` 返回一致，括号为兼容别名）**：

| 编码 | 语义 | value 形态 |
|------|------|-----------|
| `eq` | 等于 | 单值 |
| `neq`（ne） | 不等于 | 单值 |
| `gt` / `lt` | 大于 / 小于 | 单值 |
| `gte`（ge）/ `lte`（le） | 大于等于 / 小于等于 | 单值 |
| `in` / `not_in`（nin） | 包含 / 不包含 | 逗号分隔多值 |
| `between` | 区间 | `"min,max"` 两值 |

**逻辑运算合法值**（ruleLogic/ruleLogics/combinationLogic/combinationLogics 通用）：`AND`、`OR`、`ANDNOT`/`AND_NOT`/`EXCEPT`（三者为**差集**，等价）；⚠️ 其他未知逻辑值**不报错、静默按 AND 处理**——大小写不敏感。

**组合语义**：每个 combination 内的 rules 以 ruleLogic 连接成组 → 各组合以 combinationLogic 连接（位图嵌套二元运算：组间 AND/OR/差集）。

### 调用示例

```json
{"capability":"ops.data-tag.crowd.create-rule-select","input":{"crowdName":"高活跃人群","calcPeriodType":1,"queryCondition":"{\"combinations\":[{\"rules\":[{\"tagId\":\"6400000000000000001\",\"operator\":\"eq\",\"value\":\"1\"},{\"tagId\":\"6400000000000000002\",\"operator\":\"gte\",\"value\":\"100\"}],\"ruleLogic\":\"AND\"},{\"rules\":[{\"tagId\":\"6400000000000000003\",\"operator\":\"in\",\"value\":\"1,2\"}],\"ruleLogic\":\"AND\"}],\"combinationLogic\":\"OR\"}"},"summary":"提交每日计算的高活跃人群圈选任务（组1:标签1=1且标签2≥100；组2:标签3∈{1,2}；两组并集）"}
```

---

## ✅ 更新人群包 — ops.data-tag.crowd.update

- 先读详情。⚠️ **传 `updateFrequency` 但不传 `scheduleDay` 时周期日会被清空**（置 null，按周期默认日执行）——需保留 scheduleDay 时须随频次一起回传；`queryCondition` **实质变更**（与现值不同）会清空旧统计、转为 CALCULATING 并异步重算；只改名称/频次不触发重算

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |
| crowdName | String | ✅ | 人群包名称（≤50） |
| updateFrequency | String | — | 合法值 `once`/`daily`/`weekly`/`monthly`——**传非法频次字符串服务端不报错、频次保持不变**，调用后应回读详情核验 |
| scheduleDay | Integer | — | 周期日，周 1..7 或月 1..31（**服务端不校验范围**，任意整数照存，须自行把关） |
| queryCondition | String | — | 规则条件 JSON 字符串（**结构同 create-rule-select 的展开表**，以 `crowd.detail` 回显原文为回填基础） |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.update","input":{"id":"6300000000000000001","crowdName":"高活跃人群","updateFrequency":"daily"},"summary":"将规则人群包调整为每日更新"}
```

---

## ✅ 上线 — ops.data-tag.crowd.online

- 上线仅 OFFLINE，且文件上传/单次规则圈选（计算周期 NONE=0）不可重上；先查询详情确认类型可重上，执行后回读状态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.online","input":{"id":"6300000000000000001"},"summary":"重新上线已确认的周期性规则人群包"}
```

---

## ✅ 下线 — ops.data-tag.crowd.offline

- 下线仅 ONLINE，影响人群触达面；先查询详情确认状态，执行后回读状态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.offline","input":{"id":"6300000000000000001"},"summary":"下线已确认不再用于投放的人群包"}
```

---

## ✅ 删除 — ops.data-tag.crowd.delete

- 🔴 不可恢复。先查询详情并在回复中说明影响（可能被促销定向引用的人群，告知可能影响已经引用它的标签和活动），执行后回读状态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.delete","input":{"id":"6300000000000000001"},"summary":"删除已确认不再使用的人群包"}
```

---

## ✅ 文件上传创建/追加人群包 — ops.data-tag.crowd.upload

- 🔴 批量写——执行前向用户复述文件名与预期数量；上传后人群包进入导入处理（以任务记录/成员数核验结果，未完成不得当作失败）
- **传输形态特例**：multipart 文件上传

### 入参（multipart 文件 + 表单字段）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | CSV/TXT（≤50MB，**行数上限 500 万**——超限任务置失败并报 1733）；单列 ID 清单，官方模板首行表头（uid/openid/phone）会被自动跳过 |
| mode | String | — | `CREATE`（默认，新建）/ `APPEND`（追加到现有人群包） |
| targetCrowdId | String | 条件 | APPEND 模式必填；**仅 DYNAMIC / FILE_UPLOAD 类型人群包允许追加**（规则圈选包禁止，避免规则重算冲掉） |
| crowdName | String | 条件 | CREATE 模式必填（≤50 字符；APPEND 模式忽略） |
| convertType | Integer | ✅ | 文件内 ID 类型（权威枚举）：`0`=UID / `1`=OpenID / `4`=手机号（官方模板默认）；⚠️ `2`=W_UID 与 `3`=UNION_ID 当前后端未实现，传入将全部行失败——**勿使用** |

### 出参（原始返回）

`data` 为新人群包 ID（CREATE）或目标人群包 ID（APPEND），Long→string。导入为异步执行：轮询 `crowd.task-records` 或以 `crowd.members` 计数核验。

### 调用示例

```json
{"capability":"ops.data-tag.crowd.upload","input":{"file":"uploads/手机号清单.csv", "fileType":"csv","mode":"CREATE","convertType":4,"crowdName":"线下活动用户"},"summary":"上传手机号清单创建人群包"}
```
