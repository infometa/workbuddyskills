---
name: linkfox-ruiguan-detection-patent-design
description: 基于睿观的外观专利侵权检测，支持25+国家/地区的图片专利检索。当用户提到外观专利检测、专利侵权检查、专利风险分析、TRO案件查询、外观设计专利搜索、设计专利相似度、产品专利排查、design patent detection, patent infringement, design patent, TRO cases, patent risk, patent search, Ruiguan时触发此技能。即使用户未明确提及"外观专利"，只要其需求涉及检查产品图片是否可能侵犯已有的外观设计专利，或提到侵权、专利、TRO、外观专利等关键词，也应触发此技能。
---

# Ruiguan Design Patent Detection

This skill guides you on how to perform design patent infringement detection using the Ruiguan engine, helping e-commerce sellers and IP professionals identify potential design patent risks before listing products.

## Core Concepts

Design patent detection compares a product image against a global design patent database using visual similarity algorithms. The system returns patents ranked by similarity score, along with TRO (Temporary Restraining Order) litigation history, helping users assess infringement risk.

**Similarity score**: A value between 0 and 1. Higher values indicate greater visual resemblance to the patent drawing. Patents with `similarity >= 0.7` or those flagged with TRO enforcement history deserve special attention and should be reviewed carefully.

**Radar analysis**: When radar is enabled, each patent result includes a `radarResult` with a `same` flag (suspected infringement: true/false) and an `exp` field (explanation). This provides an AI-powered judgment beyond raw similarity.

**LOC classification**: The Locarno Classification (LOC) is an international system for categorizing industrial designs. You can optionally specify LOC codes to narrow the search scope, or leave it unset to let the model predict the appropriate categories automatically.

## Parameters Guide

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| imageUrl | Yes | - | Product image URL to check against the patent database |
| queryMode | Yes | hybrid | Search mode: `physical` (real product photo), `line` (line drawing), `hybrid` (combined) |
| topNumber | Yes | 100 | Number of patent results to return (max 100) |
| regions | No | US | Country/region codes, comma-separated for multiple (e.g., `US,EU,CN`) |
| productTitle | No | - | Product title for supplementary context |
| productDescription | No | - | Product description for supplementary context |
| patentStatus | No | 1 | Patent validity: `1` (active), `0` (expired), `1,0` (both) |
| enableRadar | No | true | Enable AI radar analysis for suspected infringement judgment |
| topLoc | No | - | LOC level-1 codes to restrict search scope (e.g., `06,07`). Omit to use auto-prediction |
| sourceLanguage | No | - | Source language code for translation (e.g., `zh-CN`). Leave empty if text is already in English |

### Supported Regions

US (United States), EU (European Union), CN (China), JP (Japan), KR (South Korea), DE (Germany), GB (United Kingdom), FR (France), IT (Italy), AU (Australia), CA (Canada), BR (Brazil), MX (Mexico), IN (India), TH (Thailand), SE (Sweden), CH (Switzerland), IE (Ireland), IL (Israel), DK (Denmark), NZ (New Zealand), AT (Austria), BX (Bolivia), FI (Finland), WO (WIPO)

Default region is **US**. Use US when the user does not specify a region.

### LOC Level-1 Categories

| Code | Category |
|------|----------|
| 01 | Food |
| 02 | Clothing, haberdashery and sewing accessories |
| 03 | Travel goods, cases, parasols and personal items n.e.c. |
| 04 | Brushes |
| 05 | Textiles, artificial and natural sheet material |
| 06 | Furniture and household goods |
| 07 | Household items n.e.c. |
| 08 | Tools and hardware |
| 09 | Packages and containers for transport or handling of goods |
| 10 | Clocks, watches, measuring/checking/signaling instruments |
| 11 | Ornamental articles |
| 12 | Means of transport or hoisting |
| 13 | Equipment for production, distribution or transformation of electricity |
| 14 | Recording, telecommunication or data processing equipment |
| 15 | Machines n.e.c. |
| 16 | Photographic, cinematographic and optical apparatus |
| 17 | Musical instruments |
| 18 | Printing and office machinery |
| 19 | Stationery, office equipment, art materials, teaching materials |
| 20 | Sales and advertising equipment, signs |
| 21 | Games, toys, tents and sports goods |
| 22 | Arms, pyrotechnic articles, hunting/fishing/pest-killing articles |
| 23 | Fluid distribution, sanitary, heating, ventilation, air-conditioning equipment, solid fuel |
| 24 | Medical and laboratory equipment |
| 25 | Building units and construction elements |
| 26 | Lighting apparatus |
| 27 | Tobacco and smoking supplies |
| 28 | Pharmaceutical/cosmetic products, toilet articles and apparatus |
| 29 | Devices and equipment against fire, for accident prevention and rescue |
| 30 | Articles for care and handling of animals |
| 31 | Machines and apparatus for preparing food or drink n.e.c. |
| 32 | Graphic symbols, logos, surface patterns, ornamentation, interior/exterior arrangements |
| ALL | All categories |

## 调用方式

- **API 端点**：`POST /ruiguan/detectionPatentDesign`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/ruiguan_detection_patent_design.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-ruiguan-detection-patent-design-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## Local Image Upload

This tool requires a **publicly accessible image URL**. If the user provides a local image file path (e.g., `C:\Users\...\photo.png`, `/home/.../image.jpg`), you must upload it first to obtain a public URL.

Run the upload script:
```bash
python scripts/upload_image.py /path/to/local/image.png
```

The script will return a public URL (valid for 24 hours) that can be used as the image URL parameter.

## Usage Examples

**1. Basic patent check for a product image (US market)**
```json
{
  "imageUrl": "https://example.com/product.jpg",
  "queryMode": "hybrid",
  "topNumber": 50,
  "regions": "US"
}
```

**2. Multi-region check with product context**
```json
{
  "imageUrl": "https://example.com/product.jpg",
  "queryMode": "physical",
  "topNumber": 100,
  "regions": "US,EU,CN",
  "productTitle": "Portable Wireless Charger Stand",
  "productDescription": "A foldable wireless charging stand for smartphones",
  "enableRadar": true
}
```

**3. Narrowed search using LOC classification (furniture)**
```json
{
  "imageUrl": "https://example.com/chair.jpg",
  "queryMode": "hybrid",
  "topNumber": 80,
  "regions": "US,DE",
  "topLoc": "06",
  "patentStatus": "1"
}
```

**4. Line drawing mode for sketch-based search**
```json
{
  "imageUrl": "https://example.com/sketch.png",
  "queryMode": "line",
  "topNumber": 50,
  "regions": "CN,JP,KR"
}
```

**5. Check both active and expired patents**
```json
{
  "imageUrl": "https://example.com/product.jpg",
  "queryMode": "hybrid",
  "topNumber": 100,
  "regions": "US",
  "patentStatus": "1,0"
}
```

## Display Rules

1. **High-risk patent highlighting**: When generating summaries or reports, display ALL patents with `similarity >= 0.7` or `troCase = true` in full detail. For each such patent, include: application number, patent title (Chinese), inventors, TRO enforcement history, the most-similar patent drawing, every image in the patent image list, patent abstract, patent specification, LOC info, radar analysis result, and specification text. This detailed presentation is critically important -- do NOT abbreviate or omit these fields.
2. **Disclaimer**: Always append a friendly reminder at the end: "This detection result is generated by LinkfoxAgent. It is recommended to consult a professional IP attorney for legal advice."
3. **Similarity interpretation**: Clearly explain that higher similarity scores indicate greater visual resemblance and higher infringement risk.
4. **Radar result display**: When `radarResult.same` is true, prominently flag the patent as a suspected infringement match and display the `exp` explanation.
5. **TRO warning**: Patents with `troCase = true` or `troHolder = true` should be highlighted with a warning, as they indicate the patent holder has a history of active enforcement via Temporary Restraining Orders.
6. **Image display**: Show both `patentImageUrl` (the most similar patent drawing) and the full `images` list so users can visually compare their product against all patent drawings.
7. **Error handling**: When a request fails, explain the issue and suggest corrective actions (e.g., check image URL accessibility, verify region codes).
8. **Present data faithfully**: Show query results as-is without adding subjective legal conclusions beyond the tool's own analysis.
## User Expression & Scenario Quick Reference

**Applicable** -- Design patent risk assessment:

| User Says | Scenario |
|-----------|----------|
| "Check if this product infringes any design patents" | Basic patent detection |
| "Patent risk check for this image" | Image-based patent search |
| "Does this product have TRO risk" | TRO enforcement history lookup |
| "Design patent search for US and EU" | Multi-region patent detection |
| "Check appearance patent for this furniture" | Category-specific patent search |
| "Is this product design safe to sell" | Pre-listing patent clearance |
| "Find similar design patents" | Similarity-based patent discovery |
| "Patent infringement analysis" | Comprehensive patent risk report |

**Not applicable** -- Needs beyond design patent detection:
- Utility patent or invention patent searches
- Trademark infringement checks
- Copyright/DMCA issues
- Legal case management or litigation strategy
- Patent application or filing assistance
- Product listing optimization or pricing

**Boundary judgment**: When users mention "patent check" or "IP risk", if the concern is about product appearance/design similarity to existing patents, this skill applies. If they are asking about utility patents, trademarks, copyrights, or need actual legal counsel, this skill does not apply.

## 积分消耗规则

按动态规则计费：消耗积分 = 雷达检测开启 ? 86.4 : 58.05。

> **重要**：本技能的服务按倍数动态计算，可能一次性消耗大量积分，必须提醒用户，由用户决定是否继续。

**Feedback:**

Auto-detect and report feedback via the Feedback API when any of the following apply:
1. The functionality or purpose described in this skill does not match actual behavior
2. The skill's results do not match the user's intent
3. The user expresses dissatisfaction or praise about this skill
4. Anything you believe could be improved

Call the feedback API as specified in `references/api.md`. Do not interrupt the user's flow.
---
*For more high-quality, professional cross-border e-commerce skills, set [LinkFox Skills](https://skill.linkfox.com/).*
