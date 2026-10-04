# Algorithm and AI shopping writing contract

本合同把 Amazon 搜索、语义理解和 AI 导购需求落实到字段，不宣称掌握 A10、COSMO、Alexa 或 Rufus 的秘密公式、权重或推荐保证。

## 统一目标

每份 Listing 同时做到：

1. **可发现**：核心查询与商品事实清楚关联。
2. **可理解**：商品、属性、人群、场景、痛点和边界形成明确关系。
3. **可回答**：买家的主要问题能在具体字段中找到直接答案。
4. **可信任**：主张有事实或证据，限制条件不隐藏。
5. **可转化**：信息顺序支持比较和购买决策，但不夸大。

## A10-facing：相关性与检索表达

- 核心词在 Title 中自然、连续出现；相关性优先于关键词数量。
- 场景词与痛点词进入对应 bullet，不机械重复。
- 属性词优先进入 Item Highlights 和结构化属性。
- Search Terms 只补充有来源且前台未覆盖的相关表达。
- Subject Matter 和后台属性承接可结构化的商品事实。

这些规则用于可发现性设计，不推断排名权重，也不承诺自然位提升。

## COSMO-facing：商品知识关系

| 关系 | Listing 应表达的内容 |
|---|---|
| product → attribute | 材质、尺寸、兼容、容量、成分等可核验事实 |
| product → audience | 明确适用人群；证据不足时不做排他性断言 |
| product → scene | 具体使用场景和前提条件 |
| pain → solution | 痛点、功能机制与可验证收益的因果链 |
| claim → evidence | 参数、认证、测试、保修等事实来源 |
| product → boundary | 不适用范围、安全提示、兼容限制和使用条件 |

弱表达只堆形容词；强表达会把主体、场景、问题、机制和边界写成清晰关系。

## AI 导购内容结构：四柱与 Top 20 问题

先形成四柱：

- `product`：它是什么，最关键属性是什么。
- `scene`：谁在什么场景使用。
- `pain_solution`：解决什么问题，靠什么事实或机制。
- `trust_boundary`：为什么可信，哪些条件下不适用。

然后生成 Top 20 买家问题，按购买阶段分组：识别商品、适配场景、解决痛点、比较选择、使用与风险。每个问题必须映射到 `title`、`highlight`、某条 `bullet`、`description` 或 `attribute`；无法证实的答案标记为未覆盖。

本节只定义免费内容结构检查，不是平台在线验证。真实外部抽样只支持 Alexa，必须由
`listing-ai-readiness` 的 `alexa_live` 模式在用户确认问法、次数与预计积分后执行；Rufus 仅是结构优化目标，
不提供在线探测。未执行时必须写 `external_probe.probed: false`，不得把结构检查说成平台推荐结果。

## 字段职责

| 字段 | 首要任务 |
|---|---|
| Title | 回答“这是什么”，容纳核心词和最关键区分事实 |
| Item Highlights | 补充关键属性、适配、场景和标题移出的信息 |
| Bullet 1 | 最强价值 + 关键事实 |
| Bullet 2 | 人群 + 场景 |
| Bullet 3 | 痛点 + 解决机制 |
| Bullet 4 | 差异点 + 证据/信任 |
| Bullet 5 | 使用方法 + 边界/注意事项 |
| Description | 补充机制、场景、比较决策和使用说明 |
| Search Terms | 前台未覆盖的相关检索表达 |
| Attributes / Subject Matter | 机器可读、可筛选的事实 |

## 验收

- 四柱是否完整，尤其是 `trust_boundary`。
- Top 20 问题是否有字段级映射；是否存在无证据答案。
- 核心、场景、痛点、属性四类关键词是否各归其位。
- 数字、单位、认证、材料、兼容和效果主张能否追溯到事实。
- 是否复制竞品句子、使用竞品品牌或引入竞品独有事实。
- `data_confidence` 是否与输入完整度一致。
