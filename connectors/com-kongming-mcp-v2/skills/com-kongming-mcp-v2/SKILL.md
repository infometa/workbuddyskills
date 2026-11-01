---
name: com-kongming-mcp-v2
display_name: 孔明增长数据工具
display_name_en: KongMing Growth Data Tools
description: 教 AI 正确使用孔明增长 MCP 连接器的 20 个数据与媒体工具——先查数据再回答，任何数字都要有来源。
description_zh: 教 AI 正确使用孔明增长 MCP 连接器的 20 个数据与媒体工具——先查数据再回答，任何数字都要有来源。
description_en: Teaches the AI how to correctly use the 20 KongMing growth data and media tools — always query before answering, every number must have a source.
category: 数据分析
version: 1.0.4
author: KongMing-AI
---

# 孔明增长数据工具使用技能

## 何时使用本技能

用户问任何涉及其跨境电商业务**真实数据**的问题时：客户评论、痛点、竞品、
AI 可见度（GEO）、战略优先级、媒体生成价格。这些场景下**先查数据、后回答**。媒体生成类任务**先询价再生成**（`media_estimate_price` 免费），提交后用 `media_task_status` 查进度。

## 核心纪律（三条铁律）

1. **先查后答**：任何涉及客户业务数据的数字、原声、排名，必须来自工具返回。
   没查过就回答 = 编造。数据不足时诚实说「当前数据不足」，并说明缺什么。
2. **证据链**：引用时带上来源（渠道/时间窗/样本量 N）。推断要标
   「推断（非已证实）」并给出逻辑。
3. **积分语言**：涉及费用时只用「积分」表述，具体价格用 `media_estimate_price`
   查询，模型能力用 `model_catalog_get` 查询。

## 工具速查（以 tools/list 实际返回为准）

| 工具 | 用途 | 何时用 |
|---|---|---|
| `query_mentions` | 多渠道客户提及查询（评论/帖子/上传记录） | 问「客户在说什么」 |
| `get_pain_points` | 痛点聚类（严重度/分布/新兴趋势） | 问「客户在抱怨什么」 |
| `get_sentiment_trend` | 情感趋势（分桶时序+样本量） | 问「口碑在变好还是变坏」 |
| `query_competitor_mentions` | 竞品客户提及查询 | 问「竞品的客户怎么说」 |
| `compare_competitors` | 竞品对比（含样本量） | 问「我和竞品比怎么样」 |
| `query_geo_visibility` | GEO 可见度查询（query×引擎） | 问「AI 搜不搜得到我」 |
| `get_geo_audit_snapshot` | GEO 审计快照（自包含） | 问「AI 可见度体检」 |
| `generate_strategic_synthesis` | 战略综合（7 层框架+唯一要务） | 问「优先做什么」 |
| `search_knowledge` | 知识库检索 | 问「我们之前的分析结论」 |
| `model_catalog_get` | 模型目录（积分语言） | 问「有哪些模型能力」 |
| `media_estimate_price` | 媒体生成询价（免费） | 任何媒体生成前先报价 |
| `media_generate` | 图片/视频生成（多档位） | 主图/短视频/广告成片生成 |
| `media_image_set_plan` | 商品套图规划（免费） | 套图方案与分镜 |
| `media_image_set_generate` | 商品套图生成 | 多角度商品图/场景图 |
| `media_light_tool` | 视频去字幕/去水印/画质提升/图片高清放大 | 视频图片轻处理 |
| `image_analyze` | 产品图诊断（VLM 读图） | 主图合规/竞品图拆解 |
| `media_reverse_prompt` | 从参考视频反推提示词 | 复刻灵感提取 |
| `media_analyze_video` | 视频内容结构化解析 | 拆解竞品视频 |
| `media_task_status` | 任务进度查询（免费） | 生成提交后查状态 |
| `media_list_tasks` | 历史任务列表（免费） | 找回已有产物 |

## 使用示例

**例 1：痛点分析**
```
用户：最近客户抱怨最多的是什么？
→ get_pain_points（时间窗默认近 30 天）
→ 引用具体痛点类别+样本量+代表原声
→ 按严重度排序呈现，结尾给「下一步动作」建议
```

**例 2：AI 可见度**
```
用户：我的品牌在 AI 搜索里能被推荐吗？
→ get_geo_audit_snapshot
→ 呈现 query×引擎矩阵、被引情况、与竞品差距
→ 给出「本周可执行」的内容动作
```

## 边界

- 工具不可用或返回错误时：告知用户连接器状态，不臆测数据。
- 超出工具面的请求（如投放代操作）：诚实说明不在当前能力范围。
