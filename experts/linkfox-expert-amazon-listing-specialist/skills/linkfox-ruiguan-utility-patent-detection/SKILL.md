---
name: linkfox-ruiguan-utility-patent-detection
description: 基于产品信息检测和搜索相似的实用新型/发明专利。当用户提到实用新型专利检测、专利侵权风险、专利相似度搜索、专利排查、发明专利查询、专利风险评估、TRO（临时限制令）风险分析、utility patent, invention patent detection, patent infringement risk, patent search, TRO risk, Ruiguan时触发此技能。即使用户未明确说"实用新型专利"，只要其需求涉及在目标市场销售前检查产品是否可能侵犯已有的实用新型/发明专利，也应触发此技能。
---

# Ruiguan Utility Patent Detection

This skill guides you on how to search for similar utility (invention) patents based on a product's title, description, and target selling region. It helps cross-border e-commerce sellers identify potential patent infringement risks before listing products.

## Core Concepts

**Utility patent** (also called invention patent) protects new and useful inventions or functional improvements. Unlike design patents that protect appearance, utility patents protect how a product works, its structure, or its composition. Infringing on a utility patent can lead to product removal, lawsuits, or TRO orders.

**Similarity score**: Each returned patent includes a `similarity` field (0 to 1). A higher value means the patent is more closely related to the queried product. Patents with high similarity scores deserve careful review.

**TRO risk indicators**: Two boolean fields flag enforcement history:
- `troCase` -- whether the patent has a history of TRO enforcement actions
- `troHolder` -- whether the patent holder is known for initiating TRO cases

Patents flagged with either indicator require extra caution.

**Patent validity**: The `patentValidity` field shows whether a patent is `Active` or `Invalid`. Only active patents pose infringement risk.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| productTitle | string | Yes | Product title (max 1000 characters) |
| productDescription | string | Yes | Product description (max 1000 characters) |
| region | string | Yes | Target selling country/region code, comma-separated for multiple. Currently supports: US. Default: `US` |
| topNumber | integer | Yes | Number of patent results to return. Range: 10--200. Default: `100` |

### Parameter Guidelines

1. **productTitle**: Use the product's actual listing title or a concise descriptive title. Be specific rather than generic -- "portable USB-C fast charger 65W" is better than "charger".
2. **productDescription**: Include key features, materials, mechanisms, and technical attributes. The more detail provided, the more accurate the similarity matching.
3. **region**: Currently only `US` is supported. Always set to `US` unless the user specifies otherwise.
4. **topNumber**: Default is 100. Increase to 200 for a broader search when doing thorough patent clearance. Decrease to 10--20 for a quick preliminary scan.

## 调用方式

- **API 端点**：`POST /ruiguan/utilityPatentDetection`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/ruiguan_utility_patent_detection.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-ruiguan-utility-patent-detection-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## Usage Examples

**1. Basic patent risk check for a product**

User: "Check if this silicone kitchen spatula has any patent risks in the US."

Build the request with a descriptive product title and description, region set to US, and a reasonable topNumber.

**2. Thorough patent clearance before launch**

User: "I'm about to launch a new wireless earbuds product. Do a comprehensive patent check."

Use topNumber=200 for maximum coverage. Include detailed product description covering Bluetooth version, charging case design, noise cancellation features, etc.

**3. Quick scan for TRO risk**

User: "Any TRO risks for selling LED strip lights in the US?"

After retrieving results, filter and highlight patents where `troCase` or `troHolder` is true.

**4. Investigating a specific product category**

User: "Check patent risks for a portable blender with USB charging."

Provide both the product title and a detailed description emphasizing the functional aspects (motor type, blade design, charging mechanism, capacity).

## Display Rules

1. **Present data in tables**: Show results in a clear, structured table format. Key columns to display: patent title, similarity score, patent validity, application number, publication date, TRO flags, and estimated expiration date.
2. **Sort by relevance**: Display patents sorted by similarity score in descending order (highest similarity first).
3. **Highlight high-risk patents**: Call attention to patents with similarity above 0.7, active validity status, and/or TRO flags.
4. **TRO warnings**: If any returned patents have `troCase=true` or `troHolder=true`, display a prominent warning about elevated enforcement risk.
5. **Validity filtering**: When presenting results, clearly distinguish between Active and Invalid patents. Emphasize that only Active patents require attention.
6. **Volume notice**: When results are large, show the most relevant patents (e.g., top 10--20 by similarity) and summarize the rest.
7. **Error handling**: When a query fails, explain the reason and suggest adjusting the product title or description for better results.
8. **Bilingual titles**: When available, show both the English title (`title`) and Chinese title (`titleCn`) to aid understanding.
9. **No legal advice**: Present patent data factually. Do not provide legal conclusions about infringement -- recommend consulting a patent attorney for definitive assessments.
## Important Limitations

- **Region support**: Currently only US patents are searchable
- **Result cap**: Maximum 200 patents per query
- **Input length**: Both productTitle and productDescription are limited to 1000 characters each
- **Not legal advice**: Results indicate similarity, not confirmed infringement. Professional patent review is always recommended.

## User Expression & Scenario Quick Reference

**Applicable** -- Patent-related queries for product risk assessment:

| User Says | Scenario |
|-----------|----------|
| "Check patent risk for my product" | Basic patent detection |
| "Any utility/invention patent issues" | Utility patent search |
| "Is this product safe to sell (patent-wise)" | Patent clearance check |
| "TRO risk for this product" | TRO enforcement risk |
| "Similar patents for this product" | Patent similarity search |
| "Patent infringement check" | Pre-launch risk assessment |
| "Will I get sued for selling this" | Patent risk evaluation |

**Not applicable** -- Needs beyond utility patent detection:

- Design patent searches (appearance/ornamental design)
- Trademark or brand infringement checks
- Copyright issues
- Product compliance or certification (FCC, CE, etc.)
- General legal advice or contract review

## 积分消耗规则

消耗 59 积分。

> 用户会因积分消耗而支付费用。请充分评估：当需要高频调用本技能，或用户对积分消耗量预期不足时，务必提醒用户，由用户决定是否继续。

**Feedback:**

Auto-detect and report feedback via the Feedback API when any of the following apply:
1. The functionality or purpose described in this skill does not match actual behavior
2. The skill's results do not match the user's intent
3. The user expresses dissatisfaction or praise about this skill
4. Anything you believe could be improved

Call the feedback API as specified in `references/api.md`. Do not interrupt the user's flow.

---
*For more high-quality, professional cross-border e-commerce skills, set [LinkFox Skills](https://skill.linkfox.com/).*
