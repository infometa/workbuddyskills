# 数据标签域 — 标签查询契约

> 规则结构见 `references/domains/data-tag.md`（规则表达式两种不可混用的运行时格式），操作顺序见 `references/flows/data-tag.md`；标签写操作（创建/更新/启停/删除）见 `tag-action.md`，分类见 `category-query.md` / `category-action.md`，运算符见 `operator.md`。所有 ID 是十进制字符串，时间筛选格式为 `yyyy-MM-dd HH:mm:ss`。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：data-tag.tag.search 标签分页 · data-tag.tag.detail 标签详情 · data-tag.tag.operators 标签操作者 · data-tag.tag.user-values 会员命中标签值 · data-tag.tag.batch-detail 批量标签详情

---

## ✅ 标签分页 — ops.data-tag.tag.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | pageNum 默认 1；pageSize 1..100、默认 20 |
| keyword | String | — | 关键词 |
| categoryId | String | — | 分类筛选 |
| tagType / tagTypes | Integer / Integer[] | — | 标签类型筛选 |
| status | Integer | — | 状态筛选 |
| createdBy | String | — | 操作者筛选 |
| updateTimeStart | String | — | 更新时间范围起始（yyyy-MM-dd HH:mm:ss） |
| updateTimeEnd | String | — | 更新时间范围结束（yyyy-MM-dd HH:mm:ss） |
| tagIds | String[] | — | 非空时只按其精确查询 |

### 出参（原始返回）

**行内关键字段**：`id`（→ 详情/写操作路径参数）、`tagType`（1=预置 / 2=规则 / 3=手工 / 4=属性 / 5=指标，附 tagTypeDesc——注意 1 是预置而非用户属性）、`valType` + `valueType`（别名，同值；1=枚举 / 2=数值区间，规则标签实际传 6）、`operators`（**逗号分隔的可用运算符字符串**，按 valType 推断：枚举/文本型为 `"eq,ne,in,nin"`、数值型为 `"eq,ne,gt,lt,ge,le,between"`、日期型为 `"eq,gt,lt,ge,le,between"`——⚠️ 字段值可能含 **ne/ge/le/nin 别名形态**，与 `operator.list` 返回的 neq/gte/lte/not_in 编码体系不同；**构造人群包 queryCondition 时以 operator.list 的编码为准**（该解析层对别名双兼容）；**⚠️ 标签 valueDefine 例外**——规则标签的 valueDefine 运行时仅支持 eq/ne/gt/lt/ge/le/in/nin/between 短码，neq/gte/lte/not_in 会校验失败/规则不命中，详见 `tag-action.md`）、`scope`（0=全局 1=租户）、`tagCount`（打标人数）；**恒 null 字段**：`categoryName`（全链路无赋值——分类名称需以 `categoryId` 对照 `category.tree`）。

**`tagValList[]` 子结构**（标签预定义值，规则条件的 value 取值来源）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | **标签值 ID**（t_tag_value.id）——促销定向/装修投放按此 ID 做命中判定（不是 tagId） |
| tagValue | String | 标签值名称——即规则条件 `value` 要匹配的值 |
| tagValueDesc | String | 展示文案 |

⚠️ **会员等级标签同款陷阱（与 detail 一致）**：tagNameEn=member_level 的预置标签，search 行内 `tagValList` 同样被动态替换——`id` 为运行时序号（1,2,3…非真实标签值 ID）、`tagValue` 为等级编码、`tagValueDesc` 为等级名称。**该标签不可用 tagValList[].id 做促销定向绑定锚点**，等级定向以 `member-level` 域等级配置为唯一真相。

**`crowdList[]` 子结构**（关联人群包反查，手工标签的值绑定人群）：`crowdId`、`crowdName`、`crowdCount`（人数）、`crowdStatus`。

### 调用示例

```json
{"capability":"ops.data-tag.tag.search","input":{"pageNum":1,"pageSize":20,"tagTypes":[2,3],"status":1},"summary":"查询启用中的规则和手工标签"}
```

---

## ✅ 标签详情 — ops.data-tag.tag.detail

- 编辑前必读

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签 ID |

### 出参（原始返回）

标签基本信息（字段同列表行——含 `categoryName` 恒 null 的同款说明）+ **`tagValues[]`**（编辑回显/回填来源）+ 关联人群（`crowdId`/`crowdName`/`crowdCount`/`crowdStatus`——取关联人群包）。

**`tagValues[]` 子结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String | 标签值 ID（update 回传锚点——**已有值必须带 id，否则被软删除**） |
| value | String | 标签值名称 |
| description | String | 描述 |
| valueDefine | String | 规则定义 JSON **原文字符串回显**（结构见 create-rule 的展开表；update 回填时原样带回可保留，需变更时按结构改写） |
| crowdId | String | 手工标签值绑定的人群包 ID |

⚠️ **动态数据源特例**：会员等级标签（tagNameEn=member_level 预置标签）的枚举值**不落库**，detail 时从 user-center 实时拉取等级列表动态替换（id 为运行时序号非真实标签值 ID）——该标签的值以 `member-level` 域等级配置为唯一真相，不要用 detail 回显 id 做绑定锚点。

### 调用示例

```json
{"capability":"ops.data-tag.tag.detail","input":{"id":"6100000000000000001"},"summary":"查看标签及标签值完整配置"}
```

---

## ✅ 标签操作者 — ops.data-tag.tag.operators

- 返回 uid/username，用于列表操作者筛选

### 调用示例

```json
{"capability":"ops.data-tag.tag.operators","input":{},"summary":"查看可筛选的标签操作者"}
```

---

## ✅ 会员命中标签值 — ops.data-tag.tag.user-values

- 输入 `memberId`（会员雪花 ID，不是业务编号），开放能力层将其作为业务目标映射给上游 BFF，不允许输入受保护的身份字段名。返回**标签 ID → 该会员命中的标签值名称**映射（键是 **tagId**，不是标签值 ID——促销定向所需的标签值 ID 请用 `tag.search` 行内的 `tagValList[].id`；键用于配合 `batch-detail` 补齐标签名称/类型）。⚠️ **范围限制（源码核验）**：本接口**只返回手工标签命中**（tagType=3 且启用、标签值绑定 crowdId 的）——规则/预置/属性/指标标签的命中不在此接口返回内（规则标签命中看标签计算引擎，无运营端查询面）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memberId | String | ✅ | 会员雪花 ID（不是业务编号） |

### 调用示例

```json
{"capability":"ops.data-tag.tag.user-values","input":{"memberId":"6200000000000000001"},"summary":"查看会员命中的标签值"}
```

---

## ✅ 批量标签详情 — ops.data-tag.tag.batch-detail

- `tagIds` 为 ID 数组，用于补齐标签名称和类型

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tagIds | String[] | ✅ | 标签 ID 数组 |

### 调用示例

```json
{"capability":"ops.data-tag.tag.batch-detail","input":{"tagIds":["6100000000000000001"]},"summary":"批量查看指定标签详情"}
```
