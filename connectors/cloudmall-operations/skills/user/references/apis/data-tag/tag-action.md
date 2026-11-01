# 数据标签域 — 标签写操作契约

> 规则结构见 `references/domains/data-tag.md`（规则表达式两种不可混用的运行时格式），操作顺序见 `references/flows/data-tag.md`；标签现值读取（分页/详情/操作者）先读 `tag-query.md`，运算符先查 `operator.md`。所有 ID 是十进制字符串；写操作须遵守入口 Skill 的风险档位、影响说明和回读纪律（确认由运行时权限模式兜底）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：data-tag.tag.create-rule 创建规则标签 · data-tag.tag.create-manual 创建手工标签 · data-tag.tag.update 更新标签 · data-tag.tag.disable 禁用标签 · data-tag.tag.enable 启用标签 · data-tag.tag.delete 删除标签 🔴

---

## ✅ 创建规则标签 — ops.data-tag.tag.create-rule

- 当前运营端创建规则标签传 `valType=6`；服务实现未校验该值且会按枚举默认运算符处理，和 `ValTypeEnum` 仅列 1/2 已漂移

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 标签名称（≤50） |
| categoryId | String | ✅ | 分类 ID（来自 `category.tree`） |
| remark | String | — | 备注（≤500） |
| scope | Integer | — | 0=全局 / 1=租户——**scope=0 会创建后续不可改/不可删的全局标签，只在确认过权限边界时传** |
| valType | Integer | — | 值类型（当前运营端传 6） |
| tagValues | Array | ✅ | 标签值列表，每个 `value` 不可为空 |

`tagValues[]` 子结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | — | 创建时不传（update 编辑已有值时传） |
| value | String | ✅ | 标签值名称（如「高活跃」） |
| valueDefine | String | ✅（规则标签） | 规则定义 **JSON 字符串**，必须序列化后传，结构见下表 |
| crowdId | String | — | 手工标签值绑定人群包用（规则标签不传） |

**`valueDefine`（JSON 字符串）内部结构**：

顶层字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| combinations | Array | ✅ | 规则组合列表 |
| combinationLogic | String | — | 组间逻辑，默认 `AND`（**仅 AND / OR 两态**，非 AND 一律按 OR 处理） |

`combinations[]` 子结构：`rules[]`（规则项）+ `ruleLogic`（组内逻辑，默认 AND，同样仅 AND/OR 两态）。⚠️ valueDefine 解析层**不读** `ruleLogics`/`combinationLogics` 数组变体（与人群包 queryCondition 不同）。

`rules[]` 子结构（规则项）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dimension | String | ✅ | 被引用标签 ID（⚠️ **字段名是 `dimension` 不是 `tagId`**——与人群包 queryCondition 的关键差异；服务端同时容忍已是标签英文名的字符串）。被引用标签必须存在且有英文名（tagNameEn），反查不到的规则被**静默跳过**（该值条件缺失、标签值可能永不命中） |
| operator | String | ✅ | ⚠️ valueDefine 规则项运算符仅支持小写短码：`eq` / `ne` / `gt` / `lt` / `ge` / `le` / `in` / `nin` / `between`——**不是** `operator.list` 返回的 neq/gte/lte/not_in 长码（valueDefine 运行时按原样下发，长码会校验失败/规则不命中）；别名双兼容仅在人群包 queryCondition 路径成立 |
| value | String | ✅ | 条件值——匹配的是被引用标签的**标签值名称**（`tag.search` 行内 `tagValList[].tagValue`）；in/not_in 逗号分隔多值；between 两值逗号分隔 |

**⚠️ valueDefine 与人群包 queryCondition 的格式差异（不可混用）**：

| 差异点 | 标签 `valueDefine` | 人群包 `queryCondition` |
|--------|-------------------|------------------------|
| 规则项引用字段 | `dimension` | `tagId` |
| 逻辑数组变体（ruleLogics/combinationLogics） | ❌ 不支持（忽略） | ✅ 支持（优先于标量逻辑） |
| 逻辑值域 | 仅 AND / OR（非 AND 即 OR） | AND / OR / ANDNOT/AND_NOT/EXCEPT 差集 |
| 组合语义 | 组内 rules 连接 → 组间连接（&/\|） | 位图嵌套二元运算（含差集） |
| 引用失败行为 | 规则**静默跳过**（标签值条件缺失） | 整次圈选**报错** |

### 调用示例

```json
{"capability":"ops.data-tag.tag.create-rule","input":{"name":"高活跃用户","categoryId":"6000000000000000001","valType":6,"tagValues":[{"value":"高活跃","valueDefine":"{\"combinations\":[{\"rules\":[{\"dimension\":\"6400000000000000001\",\"operator\":\"eq\",\"value\":\"高活跃\"},{\"dimension\":\"6400000000000000002\",\"operator\":\"ge\",\"value\":\"100\"}],\"ruleLogic\":\"AND\"}],\"combinationLogic\":\"AND\"}"}]},"summary":"创建规则标签：值为高活跃（标签1命中高活跃且标签2≥100）"}
```

---

## ✅ 创建手工标签 — ops.data-tag.tag.create-manual

- ⚠️ **`tagValues` 与顶层 `crowdId` 均不传时会静默创建一个没有任何标签值的手工标签**——两者必须至少提供其一

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 标签名称（≤50） |
| categoryId | String | ✅ | 分类 ID |
| scope | Integer | — | 同 create-rule——0=全局，慎传 |
| valType | Integer | — | 值类型 |
| tagValues | Array | — | 每个标签值必须有 `value` 和已存在人群包的 `crowdId`；只传顶层 `crowdId` 是兼容模式，业务新建应显式提供 `tagValues` |

服务端仅校验 `crowdId` 非空，不验证该人群是否存在、已上线或适合绑定；这是调用前必须查询人群详情并确认 ONLINE 的 Agent 责任，否则可能创建失效绑定。

### 调用示例

```json
{"capability":"ops.data-tag.tag.create-manual","input":{"name":"线下活动用户","categoryId":"6000000000000000001","valType":1,"tagValues":[{"value":"已到场","crowdId":"6300000000000000001"}]},"summary":"创建绑定已上线人群包的手工标签"}
```

---

## ✅ 更新标签 — ops.data-tag.tag.update

- 先读详情。**已有值必须回传其 `id`**（锚定差量更新——`tag.detail` 回显的 `tagValues[].id`），遗漏 id 的旧值会被软删除；⚠️ **误传 DB 中不存在的 id 不报错**——服务端按新增处理（生成新雪花 ID 插入，旧数据仍被软删除），回传 id 时须确保来自 detail 回显

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID |
| name | String | ✅ | 标签名称 |
| categoryId | String | — | 分类 ID |
| remark | String | — | 备注 |
| status | Integer | — | 状态（可经 update 修改，但**状态变更应走专用 disable/enable 端点**，语义更明确） |
| tagValues | Array | — | 不传只更新基本信息；传入时至少一条（空数组报错 1726）；`value`/`valueDefine`/`crowdId` 变更按 id UPDATE，id 为空的新行 INSERT；`valueDefine` 结构同 create-rule 的展开表（编辑回显原文可原样带回，需变更时按结构改写） |

全局标签不可更新。

### 调用示例

```json
{"capability":"ops.data-tag.tag.update","input":{"id":"6100000000000000001","name":"高活跃用户","tagValues":[{"id":"6110000000000000001","value":"高活跃","valueDefine":"{\"combinations\":[{\"rules\":[{\"dimension\":\"6400000000000000001\",\"operator\":\"eq\",\"value\":\"1\"}],\"ruleLogic\":\"AND\"}],\"combinationLogic\":\"AND\"}"}]},"summary":"保留既有标签值并更新规则标签"}
```

---

## ✅ 禁用标签 — ops.data-tag.tag.disable

- 先读详情，复述名称和影响

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID |

### 调用示例

```json
{"capability":"ops.data-tag.tag.disable","input":{"id":"6100000000000000001"},"summary":"禁用已确认的标签"}
```

---

## ✅ 启用标签 — ops.data-tag.tag.enable

- 先读详情，复述名称和影响

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID |

### 调用示例

```json
{"capability":"ops.data-tag.tag.enable","input":{"id":"6100000000000000001"},"summary":"启用已确认的标签"}
```

---

## ✅ 删除标签 — ops.data-tag.tag.delete

- 🔴 删除会逻辑删除标签并清理标签值，不可恢复；全局标签不可操作

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID |

### 调用示例

```json
{"capability":"ops.data-tag.tag.delete","input":{"id":"6100000000000000001"},"summary":"删除已确认且可承受影响的标签"}
```
