---
name: linkfox-ruiguan-gun-parts-search
description: 基于睿观的产品图片政策合规检测，通过视觉相似度匹配识别潜在违规商品。当用户提到政策合规检查、产品图片合规、违规检测、禁售商品筛查、基于图片的合规审查、上架前风险排查、policy compliance detection, product compliance review, violation detection, image compliance check, product image risk screening, Ruiguan时触发此技能。即使用户未明确说"合规"，只要其需求涉及将产品图片与违规数据库进行比对，也应触发此技能。
---

# Ruiguan Policy Compliance Image Detection

This skill guides you on how to use the Ruiguan policy compliance detection tool to identify potential policy violations in product images. It performs image-based similarity search against a known database of prohibited products.

## Core Concepts

Ruiguan Policy Compliance Image Detection is an image-based compliance screening service. Given a product image URL, it searches for visually similar products in a database of known policy-violating items. The tool returns matching violations ranked by visual similarity.

**Similarity score (cosine)**: A value between 0 and 1. Higher values indicate stronger visual resemblance to known violating products. A score close to 1.0 means the product image is nearly identical to a flagged violation.

## Parameter Guide

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| Image URL | imageUrl | Yes | The URL of the product image to check (max 1000 chars) | https://example.com/product.jpg |

**Key notes:**
- The image URL must be publicly accessible
- Supported formats include common image types (JPG, PNG, etc.)
- The URL must not exceed 1000 characters

## Response Fields

| Field | API Name | Description |
|-------|----------|-------------|
| Total Matches | total | Number of matching violation records found |
| Violation List | data | Array of matched violating products |
| Violation Image | pdImgOssUrl | Image URL of the matched violating product |
| Similarity Score | cosine | Similarity between the input image and the violation (0~1) |
| Product Title (EN) | pdTitle | English title of the matched violating product |
| Product Title (CN) | pdTitleCHNCensored | Chinese title of the matched violating product |
| Detection ID | detectId | Unique identifier for this detection session |
| Token Cost | costToken | Number of tokens consumed by this request |

## 调用方式

- **API 端点**：`POST /ruiguan/gunPartsSearch`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/ruiguan_image_compliance_search.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-ruiguan-gun-parts-search-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

**1. Basic compliance check for a single product image**
```
Check this product image for policy compliance: https://example.com/images/product-123.jpg
```

**2. Batch checking multiple product images**
```
Please scan these product images for potential policy violations:
- https://example.com/images/item-a.jpg
- https://example.com/images/item-b.jpg
```

**3. Pre-listing compliance screening**
```
Before I list this product, can you check if the image triggers any policy flags?
Image: https://example.com/new-product.png
```

## Display Rules

1. **Show results in a clear table**: Present each matched violation with its image, similarity score, and product titles
2. **Highlight high-similarity matches**: When the cosine score exceeds 0.8, clearly flag the result as a strong match that likely requires attention
3. **Include violation images**: When results contain `pdImgOssUrl`, display the matched violation image so the user can visually compare
4. **Score interpretation**: Always explain what the similarity score means -- higher values indicate closer resemblance to known violations
5. **Error handling**: When a query fails, explain the issue and suggest checking whether the image URL is valid and publicly accessible
6. **No legal advice**: Present detection results factually without providing legal conclusions; remind users to verify with platform policies

## Important Limitations

- **Image-only detection**: This tool works exclusively with image URLs; it does not analyze text descriptions or product metadata
- **URL accessibility**: The image URL must be publicly reachable by the detection service
- **URL length cap**: Image URLs must not exceed 1000 characters
- **Similarity-based**: Results are based on visual similarity and do not constitute a definitive policy ruling

## User Expression & Scenario Quick Reference

**Applicable** -- Image-based product policy compliance checks:

| User Says | Scenario |
|-----------|----------|
| "Check if this product image has compliance risks" | Single image compliance check |
| "Scan my product images for policy violations" | Batch compliance screening |
| "Is this image flagged as a prohibited product" | Specific violation inquiry |
| "Pre-screen my listing images for policy risks" | Pre-listing compliance audit |
| "Find similar violations for this product image" | Similarity-based violation search |
| "这个产品能安全上架吗" | 合规风险预检 |
| "帮我检测一下这个图片是否违规" | 单图合规检测 |

**Not applicable** -- Needs beyond image-based policy compliance detection:
- Text-based product compliance analysis
- General product category classification
- Intellectual property / trademark infringement
- Patent or copyright detection (use other Ruiguan skills)

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
