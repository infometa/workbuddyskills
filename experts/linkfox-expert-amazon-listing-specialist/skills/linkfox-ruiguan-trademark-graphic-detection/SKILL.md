---
name: linkfox-ruiguan-trademark-graphic-detection
description: 产品图片的图形商标检测与相似度搜索。当用户提到商标检测、图形商标搜索、Logo侵权检查、商标相似度分析、图片商标风险评估、产品图片商标筛查、graphic trademark detection, logo infringement, trademark similarity, trademark risk, image trademark screening, Ruiguan时触发此技能。即使用户未明确说"商标检测"，只要其需求涉及将产品图片与已注册的图形商标进行比对或评估商标侵权风险，也应触发此技能。
---

# Ruiguan Graphic Trademark Detection

This skill guides you on how to detect graphic trademarks in product images, helping e-commerce sellers and brand owners identify potential trademark infringement risks before listing products.

## Core Concepts

Graphic trademark detection analyzes a product image to find visually similar registered trademarks across multiple countries and regions. The tool uses YOLO-based object detection to locate logo-like regions in the image, then compares them against trademark databases worldwide.

**Similarity score**: A higher `similarity` value means the detected graphic is more visually similar to the registered trademark. Values closer to 1.0 indicate near-identical matches and higher infringement risk.

**Trademark status meanings**:
| Status | Meaning |
|--------|---------|
| registered | Trademark is actively registered |
| act | Trademark is active |
| pend | Trademark application is pending |
| filed | Trademark application has been filed |
| ended | Trademark has expired |
| DEL | Trademark has been deleted/cancelled |

## Parameter Guide

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| imageUrl | Yes | Product image URL or base64-encoded image data | - |
| topNumber | Yes | Maximum number of detection results to return (1-100) | 5 |
| productTitle | No | Product title, helps improve detection accuracy | - |
| trademarkName | No | Suspected logo name, helps narrow down results | - |
| regions | No | Country/region codes to check, comma-separated. If omitted, all countries are searched | All |
| enableLocalizing | No | Whether to enable image cropping for detected regions | false |
| enableRadar | No | Whether to enable radar monitoring | true |

### Supported Regions

US (United States), WO (WIPO), ES (Spain), GB (United Kingdom), DE (Germany), IT (Italy), CA (Canada), MX (Mexico), EM (European Union), AU (Australia), FR (France), JP (Japan), TR (Turkey), BX (Benelux), CN (China)

When the user does not specify a region, omit the `regions` parameter so all countries are searched by default.

## Local Image Upload

This tool requires a **publicly accessible image URL**. If the user provides a local image file path (e.g., `C:\Users\...\photo.png`, `/home/.../image.jpg`), you must upload it first to obtain a public URL.

Run the upload script:
```bash
python scripts/upload_image.py /path/to/local/image.png
```

The script will return a public URL (valid for 24 hours) that can be used as the image URL parameter.

## Usage Examples

**1. Basic image trademark check**
Detect trademarks in a product image across all regions, returning up to 10 results:
```
imageUrl: "https://example.com/product-image.jpg"
topNumber: 10
```

**2. Region-specific trademark check**
Check a product image against US and EU trademark databases only:
```
imageUrl: "https://example.com/product-image.jpg"
topNumber: 5
regions: "US,EM"
```

**3. Detailed check with product context**
Provide product title and suspected logo name for more accurate detection:
```
imageUrl: "https://example.com/product-image.jpg"
topNumber: 10
productTitle: "Wireless Bluetooth Headphones with Noise Cancellation"
trademarkName: "SonicWave"
regions: "US,GB,DE"
```

**4. Full detection with image cropping**
Enable localizing to get cropped images of detected logo regions:
```
imageUrl: "https://example.com/product-image.jpg"
topNumber: 20
enableLocalizing: true
regions: "US"
```

## 调用方式

- **API 端点**：`POST /ruiguan/trademarkGraphicDetection`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/ruiguan_trademark_graphic_detection.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-ruiguan-trademark-graphic-detection-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## Display Rules

1. **Present results clearly**: Show detection results in a well-structured table including trademark image, similarity score, trademark name, status, registration office, Nice classification, applicant name, and key dates
2. **Highlight high-risk matches**: When similarity is above 0.8, explicitly warn the user about high infringement risk
3. **Explain trademark status**: When showing results, clarify what each trademark status means for the user's risk assessment
4. **Radar results**: If `radarResult` is present in the response, display it prominently as it contains aggregated risk assessment
5. **Sub-radar results**: If individual items contain `subRadarResult`, include this information alongside each match
6. **Region context**: Always indicate which regions were searched so the user understands the scope of the check
7. **Error handling**: When a detection fails, explain the reason based on the response and suggest adjustments (e.g., using a clearer image, specifying regions, adjusting topNumber)
## Important Limitations

- **Image requirement**: The `imageUrl` parameter is mandatory; the tool cannot perform detection without an image
- **Result cap**: The `topNumber` parameter caps at 100 results per request
- **Image quality**: Detection accuracy depends on image resolution and clarity; higher quality images yield better results
- **Region coverage**: Not all countries are covered; the supported list includes 15 major trademark offices

## User Expression & Scenario Quick Reference

**Applicable** -- Graphic trademark detection tasks:

| User Says | Scenario |
|-----------|----------|
| "Check if this image has trademark issues" | Basic trademark detection |
| "Is this logo registered anywhere" | Multi-region trademark search |
| "Trademark risk for my product image" | Product listing risk assessment |
| "Find similar trademarks to this graphic" | Similarity search |
| "Check this image against US trademarks" | Region-specific detection |
| "Does this design infringe any trademark" | Infringement risk check |
| "Scan my product photo for logos" | Logo detection in product images |

**Not applicable** -- Needs beyond graphic trademark detection:
- Text/word trademark search (no image involved)
- Trademark registration or filing
- Patent or copyright checks
- Legal advice on trademark disputes
- Product listing optimization

**Boundary judgment**: When users say "check my product" or "is this safe to sell", if the concern relates to graphic elements or logos in product images potentially infringing registered trademarks, this skill applies. If they are asking about text trademarks, patent issues, or general legal compliance, it does not apply.

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
