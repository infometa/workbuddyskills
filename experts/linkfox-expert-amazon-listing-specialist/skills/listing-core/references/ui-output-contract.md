# Listing UI output contract

核心流程复用现有 `agent-listing` UI schema，不新增平行格式。

## 产物与组件映射

| 产物 | 识别方式 | UI 用途 |
|---|---|---|
| `run-manifest.json` | `kind=listingRunManifest` | 阶段进度、workbench、最终产物入口 |
| `keywords.json` | `kind=listingKeywordPlan` | Keyword Plan 面板 |
| `check-report.json` | `kind=listingCheckReport` | Check Report 面板 |
| `ai-readiness.json` | `kind=listingAiReadiness` | AI 导购承接检查 / Alexa 实测面板；由 `inspection_mode` 与 `external_probe.probed` 区分状态，Rufus 不表示在线实测 |
| `listing-final.json` | `kind=listingFinalBundle` | 右侧首选结构化 Amazon PDP 文案预览；`preview` 明确 copy/commerce 能力 |
| `listing-final.md` | 固定标题结构 | Markdown 兜底与文案下载 |
| `score-result.json` | canonical scorer 的 `scorePanel` | 数字评分事实源；仅按需生成 |
| `listing-report.html` | manifest `final.html` + `Rendered <abs>` | 右侧可交互 Listing/素材/评分报告 |
| `amazon-detail-preview.json` | 文件名匹配（前端 `AmazonDetailPreviewRenderer`，handoff §8 形态 A 信封）| 与 `listing-final.json` 共享 `preview`。`imagesSource` 三态：rewrite 注入本品图+价格（`own`）；benchmark/create 注入竞品图并逐张标「参考图（竞品）」（`reference`，前端横幅提示，不注入竞品价格）；作图套图经 `update_detail_preview.py` 回写后替换为生成图（`generated`）。缺图缺价降级渲染 |
| `linkfox-agent-listing-copy-xlsx-*.xlsx` | manifest `final.xlsx` | 复用 agent-listing 既有四 sheet 文案表下载 |

`preview` 固定形态：

```json
{
  "mode": "copy",
  "sourceRelation": "product_info",
  "capabilities": { "showCommerce": false }
}
```

`sourceRelation=own_listing` 只表示用户明确提供的自有在售 Listing（当前 core 对应 rewrite）；且真实商业字段存在时才可令 `showCommerce=true`。参考 ASIN、普通产品资料、跨站点文案迁移均不得显示占位价格、评分、库存、配送或店铺。

## Markdown 固定标题

顺序和拼写保持不变：

```markdown
# Listing 文案
## Title
## Item Highlights
## Bullet Points
## Product Description
## Search Terms
## Subject Matter
## 算法与 AI 导购验收摘要
```

Item Highlights 使用单行分隔文本，Bullet Points 使用 Markdown 列表。不要把诊断过程、竞品原文或内部推理写入 final Markdown。

## AI readiness

沿用 schema v1：

```json
{
  "kind": "listingAiReadiness",
  "schema_version": 1,
  "marketplace": "US",
  "four_pillars": {"what": "pass", "who_scene": "pass", "pain_solution": "weak", "trust_boundary": "weak"},
  "questions": [{
    "question": "can I put it in a backpack?",
    "source": "insight",
    "answered_by": ["bullet_2"],
    "strength": "explicit",
    "alexa_probe": {"probed": false}
  }],
  "fix_suggestions": []
}
```

结构验收与真实平台探测必须分开表述。

## 报告语言

Listing 文案字段使用 `output_language`（目标站点语言）。除此之外的一切用户可见文字——诊断结论、扣分理由、检查报告说明、AI readiness 说明、HTML 报告叙述、Excel 中的评分/风险说明列、对话交付摘要——默认中文；引用的原文关键词与字段片段保留原文。用户明确要求其他语言的报告时才切换。

## Agent-listing Excel

禁止在 Core 内维护 Flat Excel 列表或 OOXML writer。通过 `agent-listing-result-html-skill/scripts/export_listing_copy_xlsx.py` 生成既有工作簿：

1. `Listing文案表`
2. `文案详情`
3. `关键词映射`
4. `评分风险`

`Listing文案表` 必须严格使用业务模板 Sheet1 的 19 列顺序：

`商品名称 | Item Highlight | 流量词 | 【关键词台账汇总】 | 空列 | 长描述 | 五点描述1…5 | 空列 | 后台关键词1…5 | 空列 | 后台关键词字符统计`

首行就是表头，不增加标题、生成时间、序号、SKU、品牌、平台、评分等管理列；E、L、R 保留为空分隔列。其余三个 Sheet 同样不得输出 SKU 列或 SKU 值，只保留文案审核、关键词映射、评分风险本身需要的字段。商品库 `skuId` 继续保留在 `listing-final.json`，用于写回链路，不泄漏到文案工作簿。

`listing-final.json` 必须提供 exporter 使用的 `product`、`listing`、`researchReport`、`scorePanel`。该工作簿用于审阅、批量交付和 UI 下载，不声称是 Seller Central 官方上传模板。

Core 只执行基础字段门时，`scorePanel.overall=null`、`grade=—`、`basis=Core 基础字段质量门`。只有 `listing-quality-scorer` 运行后才能显示 canonical 数字分；UI 不得把字段通过状态转换成默认 80/90 分。

## Manifest final

```json
{
  "listing_json": "/abs/.../listing-final.json",
  "listing_md": "/abs/.../listing-final.md",
  "xlsx": "/abs/.../linkfox-agent-listing-copy-xlsx-<timestamp>.xlsx",
  "check_report": "/abs/.../check-report.json",
  "ai_readiness": "/abs/.../ai-readiness.json",
  "detail_preview": "/abs/.../amazon-detail-preview.json",
  "score_report": "/abs/.../score-result.json",
  "html": "/abs/.../listing-report.html"
}
```

`score_report` 与 `html` 为按需字段。HTML renderer 使用 `listing-final.json` 的 authoritative 数据，不再生成第二份结构化 JSON 或第二份 XLSX；因此 stdout 仍只有 Core 的一行 `Saved full response:`。
