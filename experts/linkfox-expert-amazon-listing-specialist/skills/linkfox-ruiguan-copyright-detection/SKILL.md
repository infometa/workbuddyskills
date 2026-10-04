---
name: linkfox-ruiguan-copyright-detection
description: 图片版权侵权检测与风险分析。当用户提到版权检测、版权核查、图片侵权检查、图片版权风险、版权相似度搜索、TRO风险分析、权利人查询、版权合规验证、copyright detection, image infringement, copyright risk, TRO risk, copyright lookup, infringement analysis, Ruiguan时触发此技能。即使用户未明确提及"版权"，只要其需求涉及检查图片是否可能侵犯已登记的版权作品，也应触发此技能。
---

# Ruiguan Copyright Detection

This skill guides you on how to perform image copyright detection, helping e-commerce sellers and designers identify potential copyright infringement risks before using images.

## Core Concepts

Copyright detection works by comparing a given image against a database of registered copyrighted works. The system returns visually similar copyrighted images along with key risk indicators such as similarity score, rights owner information, TRO (Temporary Restraining Order) litigation history, and radar-based infringement assessment.

**Similarity**: A decimal string (e.g., `"0.85"`) representing how closely the input image matches a copyrighted work. Higher values indicate greater risk.

**Radar detection**: An additional layer of analysis that provides a binary infringement judgment (`1` = infringing, `0` = not infringing). When enabled, each result includes this secondary assessment.

**TRO history**: TRO (Temporary Restraining Order) is a legal mechanism commonly used in copyright enforcement. Results flagged with TRO history indicate the rights owner has previously pursued legal action, signaling elevated risk.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| imageUrl | string | Yes | - | URL of the image to check for copyright infringement (max 1000 characters) |
| topNumber | integer | No | 100 | Number of results to return (min: 10, max: 200) |
| enableRadar | boolean | No | true | Whether to enable radar-based infringement detection |

### Parameter Guidelines

1. **imageUrl**: Must be a publicly accessible image URL. Supports common image formats. The URL must not exceed 1000 characters.
2. **topNumber**: Controls how many matching copyrighted works are returned. Use a smaller number (e.g., 10-20) for quick checks; use the maximum (200) for thorough audits.
3. **enableRadar**: When set to `true`, each result includes a radar-based infringement judgment. Keep enabled for comprehensive analysis; disable only when a faster, similarity-only scan is sufficient.

## 调用方式

- **API 端点**：`POST /ruiguan/copyrightDetection`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/ruiguan_copyright_detection.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-ruiguan-copyright-detection-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

**1. Basic Copyright Check for a Single Image**
User: "Check if this image has any copyright issues: https://example.com/my-image.jpg"
Action: Call with `imageUrl` set to the provided URL, using defaults for other parameters.

**2. Quick Scan with Fewer Results**
User: "Do a quick copyright scan on this product image, I just need the top matches: https://example.com/product.png"
Action: Call with `topNumber` set to 10 for faster results.

**3. Thorough Audit with Maximum Results**
User: "I need a full copyright audit on this design: https://example.com/design.jpg"
Action: Call with `topNumber` set to 200 for the most comprehensive scan.

**4. Similarity-Only Check (No Radar)**
User: "Just check the similarity of this image against copyrighted works, no need for detailed infringement analysis: https://example.com/photo.jpg"
Action: Call with `enableRadar` set to `false`.

**5. Batch Checking (Multiple Images)**
User: "Check these three images for copyright: url1, url2, url3"
Action: Call the API once for each image URL and consolidate results.

## Display Rules

1. **Present data clearly**: Show detection results in a well-structured table. Key columns to display include: similarity score, rights owner, copyright code, radar result, TRO history, and copyright source link.
2. **Highlight high-risk results**: When similarity is high (e.g., >= 0.80) or radar detection flags infringement (`subRadarResult` = 1), clearly mark these as high-risk entries.
3. **TRO warnings**: When `troCase` or `troHolder` is `true`, prominently warn the user about existing TRO litigation history associated with the rights owner.
4. **Image previews**: When `path` or `pathThumb` URLs are available, mention that thumbnail previews of the copyrighted works can be viewed at those URLs.
5. **Result count notice**: Inform the user of the `total` number of matches found. If many results are returned, show the most relevant (highest similarity) entries first.
6. **Error handling**: When a request fails, explain the reason and suggest checking that the image URL is publicly accessible and correctly formatted.
7. **No legal advice**: Present detection results factually. Do not provide legal conclusions — recommend the user consult legal counsel for definitive copyright assessments.
## Important Limitations

- **Image URL required**: The tool accepts image URLs only, not local file uploads. The image must be publicly accessible.
- **URL length**: The image URL must not exceed 1000 characters.
- **Result cap**: A maximum of 200 results can be returned per query.
- **Detection scope**: Results are limited to the copyrighted works database maintained by the detection service.

## User Expression & Scenario Quick Reference

**Applicable** -- Image copyright risk assessment:

| User Says | Scenario |
|-----------|----------|
| "Check if this image has copyright issues" | Basic copyright detection |
| "Is this image safe to use" | Infringement risk check |
| "Find similar copyrighted images" | Copyright similarity search |
| "Does this image have TRO risk" | TRO litigation risk analysis |
| "Who owns the copyright for this image" | Rights owner lookup |
| "Copyright audit for product images" | Batch copyright compliance check |
| "Is this design original or copied" | Originality verification |

**Not applicable** -- Needs beyond image copyright detection:
- Trademark or patent searches
- Text or music copyright checks
- Image editing or modification
- Reverse image search for non-copyright purposes
- Legal advice or litigation strategy

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
