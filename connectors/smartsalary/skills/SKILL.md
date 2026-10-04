---
name: smartsalary
display_name: "eRoad·市场人才薪酬数据"
display_name_en: "eRoad Market Talent & Compensation Data"
description: "使用 SmartSalary Connector 查询和分析 HR、人力资源、招聘、人才市场、薪酬与人效数据。当用户需要数据回答招聘量、职位或人才结构、薪资工资、月薪年薪、薪酬区间或分位值、涨薪率、离职率、人员配置、薪酬投入和组织人效，或询问有多少、平均多少、趋势、对比、排名、分布时自动触发。非数据型制度撰写、劳动法咨询、简历编辑和候选人寻访不触发。"
description_zh: "连接薪智（SmartSalary），把外部人才与薪酬市场数据带入现有工作流。随手查询竞品招聘变化、岗位人才供给、市场薪酬和人效指标，为招聘策略、岗位定薪及人才规划获得更清晰的外部参照，让招聘、定薪和人才规划不再只凭经验。"
description_en: "Connect eRoad to bring external talent and compensation market data into your workflows. Explore competitor hiring changes, talent supply by role, market compensation, and workforce productivity metrics to benchmark recruiting strategy, role pricing, and workforce planning with data instead of experience alone."
category: "人力资源/数据查询"
version: "1.0.0"
disable-model-invocation: false
user-invocable: true
author: "薪智大数据"
---

# 薪智 HR 与人才市场数据

通过 SmartSalary Connector 获取企业招聘、人才需求、薪酬及人效数据。Connector 提供查询结果，Agent 负责完成分析和回答。

## 适用范围

- 公司或竞品的招聘规模、变化趋势、热招岗位、岗位结构、招聘城市、学历和经验要求。
- 多家公司的人才需求、岗位数量、城市布局、薪资区间和用人重点对比。
- 特定岗位、行业、城市或职级的薪酬区间、分位值、固定薪酬、总现金收入和薪酬竞争力。
- 涨薪率、离职率、应届生起薪、薪酬投入、人员配置、支持效能和上市公司人效。
- 基于招聘结构与变化解读人才投入重点。涉及战略、业务方向或经营判断时，必须明确标注为基于招聘信号的推断。

通用编程、当前工作区代码分析或与 HR 无关的问题不使用本 Skill。

## Connector 工具与参数

### `list_smartsalary_agents`

列出当前用户实时可用的薪智智能体。根据智能体名称和能力说明选择本次任务的匹配项。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| 无 | - | - | - | 此工具不接收参数 |

返回 `agents[]`。每项包含 `id`、`name`、`description` 和 `is_default`。

### `ask_smartsalary`

使用指定智能体执行一次独立的数据查询。结果可能是原始明细，不保证已经聚合。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `question` | string | 是 | 无 | 完整且自包含的问题，并写明业务条件和分析所需字段 |
| `agent_id` | integer | 是 | 无 | 本任务调用 `list_smartsalary_agents` 后返回的智能体 ID |
| `context` | string \| null | 否 | `null` | 补充背景；不能代替 `question` 中的核心问题和限制条件 |

返回对象包含以下字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `answer` | string | Markdown 数据源，可能包含职位明细、薪酬样本或其他原始记录 |
| `agent` | object | 实际使用的智能体 `id` 和 `name` |
| `sources` | array | 可披露来源的引用序号、标题、URL、文档 ID 和来源类型 |

## Connector 工具编排

1. 每个新的 HR、招聘、人才或薪酬任务先调用一次 `list_smartsalary_agents`。
2. 根据实时返回的 `name` 和 `description` 选择最匹配的智能体。`is_default` 不能代替能力匹配。
3. 将本次返回的 `id` 作为 `agent_id` 调用 `ask_smartsalary`。不要记忆或固化历史 ID。
4. 同一主题的后续查询复用已选智能体。任务所需能力改变时，重新列出并选择智能体。
5. 每次 `ask_smartsalary` 都是独立查询。`question` 必须包含完成本次查询所需的全部条件。
6. 明细结果是成功结果。不得仅为聚合、改写格式、制作表格或图表而重复调用工具。

## 构造查询

- 在 `question` 中写明公司、竞品、岗位、城市、行业、时间范围、经验、职级、学历及薪酬口径等必要条件。
- 用户需要统计结果时，同时请求计算所需字段。不要依赖 SmartSalary 预先完成聚合。
- `context` 只放补充背景。核心问题和限制条件仍写入 `question`。
- 只有缺失信息会显著改变数据口径时才先澄清。
- 同一智能体可以处理的相关问题尽量合并查询，避免重复消耗调用额度。

## 典型调用

先调用 `list_smartsalary_agents`，无需参数：

```json
{}
```

选择匹配智能体后调用 `ask_smartsalary`：

```json
{
  "question": "统计新能源汽车行业在上海、深圳、合肥和广州的职位发布量与平均招聘月薪。返回计算所需的城市、职位标识、发布日期、薪酬上下限和薪酬周期字段。",
  "agent_id": 10,
  "context": "需要按城市对比，并说明时间范围、样本量和薪酬计算方法。"
}
```

典型返回结构：

```json
{
  "answer": "<Markdown 格式的查询结果或明细数据>",
  "agent": {
    "id": 10,
    "name": "<实际使用的智能体名称>"
  },
  "sources": [
    {
      "citation_numbers": [1],
      "document_id": "<来源文档 ID>",
      "title": "<可披露来源标题>",
      "url": "<可披露来源 URL>",
      "source_type": "<来源类型>"
    }
  ]
}
```

## 分析Connector 返回结果

- `answer` 是 Markdown 格式的数据源，包含招聘职位明细、薪酬样本或其他原始记录，不保证包含聚合统计。
- 先识别每行数据的粒度，再筛选、去重并统一城市、日期、货币和薪酬周期。
- 计算平均薪酬时只使用口径一致的有效样本。若用薪酬区间中点计算，必须说明该方法。
- 按用户要求分组、计数、求平均值、计算分位值或趋势。说明时间范围、样本量、计算方法和排除规则。

## 补充查询与网络数据

- 仅当结果截断或缺少必要字段时，按城市、公司、岗位或时间范围拆分补充查询。
- 需要不同智能体时可以拆分调用。每次查询都要带上完整背景。
- 可以并行搜索公开网络数据作为补充。SmartSalary 与网络数据必须分别标注来源、时间和统计口径。

## 输出规范

- 不要原样转发 `answer`。先给结论，再给支持结论的精确数据和方法说明。
- 多个公司、岗位、城市或时间点可比较时，使用 Markdown 表格或对比矩阵。
- 引用网络补充数据时，提供对应公开来源，并与 SmartSalary 结果分开展示。
- 返回数据适合展示趋势、排名、分布或结构时，可以生成图表。图表不能替代表格中的精确值。

## 示例场景

- 字节跳动、腾讯和阿里云在大模型、AI 基础设施与推理优化岗位上的招聘投入有何差异？请对比职位数量、主要城市、薪酬区间和经验门槛，并注明哪些业务投入判断属于招聘信号推断。
- 新能源汽车行业在上海、深圳、合肥和广州的招聘量与平均招聘薪酬分别如何？哪个城市的人才需求最旺、薪酬竞争最强？
- 宁德时代、比亚迪和阳光电源在动力电池与储能岗位上的招聘结构有何差异？请对比热招岗位、城市布局、薪酬区间和学历要求。
- 汽车、半导体和智能制造行业的年度离职率有何差异？哪些细分行业的人才保留压力更大？
- 汽车整车制造、半导体设备和工业自动化行业的技术人员占比、研发类薪酬占比和薪酬成本占营收比例有何差异？哪个行业的人才投入更偏研发？
