---
name: linkfox-sellersprite-traffic-keyword
description: 使用卖家精灵流量词反查能力，按ASIN查询关键词流量来源、流量占比类型、转化类型、自然位与广告位等指标，支持历史月份与多维排序。当用户提到ASIN反查流量词、流量关键词列表、关键词流量结构、自然词/广告词分析、关键词转化类型、SellerSprite traffic keyword、Amazon traffic keywords、reverse ASIN keywords时触发此技能。即使用户未明确提及"卖家精灵"，只要需求是围绕某个ASIN查看其关键词流量来源与词列表，也应触发此技能。
---

# SellerSprite Traffic Keyword

This skill helps query and analyze traffic keyword lists for an Amazon ASIN via SellerSprite.

## Core Concepts

- **ASIN 反查词**：以商品 ASIN 为输入，查看该商品获得流量的关键词列表。
- **流量占比类型**（`trafficKeywordTypes`）：主要流量词、精准流量词、以及 schema 中的 `preciseLongTail`（工具文案为「转化流失词」）等。
- **转化类型**（`conversionKeywordTypes`）：如转化优质词、平稳词、流失词等。
- **词标签**（`badges`）：如自然搜索词、Amazon Choice 推荐词等。

## 调用方式

- **API 端点**：`POST /sellersprite/traffic/keyword`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/sellersprite_traffic_keyword.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-sellersprite-traffic-keyword-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
- 响应体 ≤ 8 KB：落盘后把完整 JSON 打印到 stdout
- 响应体 > 8 KB：落盘后 stdout 只输出摘要（顶层字段、常见计数如 `total`/`costToken`、最大列表字段的长度 + 前 3 条样本）
- 加 `--inline` 强制全量打印到 stdout（同样落盘）

**读数据建议**：先看摘要判断是否足够；需要具体字段时优先用 `jq`或`ConvertFrom-Json` 从保存的 json 文件按需抽取，避免整份 JSON 进入上下文。

## 解决认证和积分问题
发生以下异常情况时，采用 references/onboarding.md 引导解决问题：

### 异常情况
- **未配置API Key**：环境变量未配置 `LINKFOX_AGENT_API_KEY`，也未配置 `LINKFOXAGENT_API_KEY`。
- **响应401或402状态码**
- **响应提示积分或余额不足**：消息含"积分余额不足/计费不足/余额不足/quota exceeded/insufficient balance/套餐到期/需充值/请充值"，或类似含义的内容。

## Key Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| marketplace | string | Yes | 市场站点，默认 `US` |
| asin | string | Yes | 要反查的商品 ASIN |
| month | string | No | 历史月份，格式 `yyyyMM`；不传默认最近30天 |
| page | integer | No | 页码，默认 1 |
| size | integer | No | 每页数量，默认 50，最大 100 |
| keyword | string | No | 关键词筛选 |
| badges | string | No | 词标签，多值逗号分隔 |
| trafficKeywordTypes | string | No | 流量占比类型，多值逗号分隔 |
| conversionKeywordTypes | string | No | 转化类型，多值逗号分隔 |
| orderField | string | No | 排序字段，默认 `rankPosition` |
| orderDesc | boolean | No | 是否倒序，默认 `false` |

## Usage Examples

```json
{
  "marketplace": "US",
  "asin": "B0XXXXXXXXX",
  "size": 50,
  "orderField": "rankPosition",
  "orderDesc": false
}
```

```json
{
  "marketplace": "US",
  "asin": "B0XXXXXXXXX",
  "month": "202507",
  "trafficKeywordTypes": "primary,precise",
  "conversionKeywordTypes": "excellent,stable",
  "page": 1,
  "size": 100
}
```

## Display Rules

1. 结果优先展示：关键词、自然位、广告位、流量占比类型、转化类型。
2. 明确标注查询周期（最近30天或历史月份）。
3. 当存在分页时，告知总数与当前页。
4. 不输出与接口无关的主观商业建议，除非用户明确要求。

## Important Limitations

- 必填参数：`marketplace`、`asin`
- 单次每页最多 100 条
- 历史查询需传 `yyyyMM`

## 积分消耗规则

消耗 15 积分。

> 用户会因积分消耗而支付费用。请充分评估：当需要高频调用本技能，或用户对积分消耗量预期不足时，务必提醒用户，由用户决定是否继续。

**Feedback:**

Auto-detect and report feedback via the Feedback API when any of the following apply:
1. The functionality or purpose described in this skill does not match actual behavior
2. The skill's results do not match the user's intent
3. The user expresses dissatisfaction or praise about this skill
4. Anything you believe could be improved

Call the feedback API as specified in `references/api.md`. Do not interrupt the user's flow.

