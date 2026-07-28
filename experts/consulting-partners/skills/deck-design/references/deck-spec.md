# Unified DeckSpec

`deck_spec.json` 是 S3、构建和审计的唯一机器输入。禁止并存 `outline.json`、`content.json` 或手写 Fusion 调用脚本。

## 完整示例

```json
{
  "meta": {
    "title": "区域增长战略",
    "audience": "管理委员会",
    "governing_thought": "未来两年应聚焦三个高潜城市群，并用渠道共建替代重资产直营",
    "total_slides": 2,
    "language": "zh-CN",
    "confidentiality": "CONFIDENTIAL"
  },
  "slides": [
    {
      "idx": 1,
      "layout": "cover",
      "engine": "main",
      "title": "区域增长战略",
      "role": "Transition",
      "rhythm": "Transition",
      "visual_role": "Cover",
      "anti_pattern": "不使用受保护品牌标识",
      "density": "low",
      "objective": "建立汇报主题与决策范围",
      "one_message": "聚焦高潜城市群并采用轻资产进入",
      "evidence": [],
      "source": [],
      "data": {
        "subtitle": "管理委员会讨论稿",
        "date": "2026-07"
      }
    },
    {
      "idx": 2,
      "layout": "big_number",
      "engine": "main",
      "title": "三个城市群贡献约七成增量，因此资源应从全国铺开转向重点突破",
      "role": "Hero",
      "rhythm": "Peak",
      "visual_role": "Stat hero",
      "anti_pattern": "不展示与资源选择无关的城市明细",
      "density": "medium",
      "objective": "证明增长高度集中",
      "one_message": "集中投入三个城市群",
      "evidence": [
        {"claim_id": "C-01", "grade": "[E]"}
      ],
      "source": [
        {"label": "内部销售数据与咨询团队估算", "url": ""}
      ],
      "data": {
        "number": "70",
        "unit": "% [E]",
        "description": "三个城市群贡献未来两年的主要可获取增量",
        "detail_items": ["统一口径：可获取收入增量", "待用城市级订单数据验证"]
      }
    }
  ]
}
```

## 字段说明

### meta

- `title`：演示名称。
- `audience`：决策受众。
- `governing_thought`：唯一顶层结论。
- `total_slides`：必须等于 `slides.length`。
- `language`、`confidentiality`：可选交付元数据。

### slides[]

| 字段 | 规则 |
|---|---|
| idx | 从 1 开始连续递增 |
| layout | 已注册版式；未知值直接失败 |
| engine | `main` / `mck_ppt` 或 `supplemental` / `mckinsey_pptx` |
| title | 内容页必须是完整行动标题；封面/章节/结束页可放宽 |
| role | Hero / Supporting / Transition |
| rhythm | Peak / Valley / Transition |
| visual_role | 页面用什么视觉关系证明主张 |
| anti_pattern | 本页必须主动避免的视觉或论证反模式 |
| density | low / medium / high |
| objective | 本页证明任务 |
| one_message | 本页唯一应被记住的信息 |
| evidence | 结构化数组，每项至少含 `claim_id` 和 `[F]/[I]/[A]/[E]` 等级 |
| source | 结构化数组，每项至少含非空 `label`，可选 `url`、`accessed_at` |
| data | 直接传给选定版式的参数；标题、来源和页码由管线注入 |

内容页的 `evidence` 与 `source` 不得为空。`cover`、`section_divider`、`closing`、`appendix_title` 可为空。

## Engine 规则

- `main` 调用 `mck_ppt.MckEngine` 注册方法。
- `supplemental` 调用 `mckinsey_pptx.builder._REGISTRY` 注册方法。
- 不允许自动猜测未知版式，不允许失败后换版式静默重试。
- `data` 中禁止设置 `page_number`、`theme` 或内部 presentation 对象；页码和主题由 Fusion 管线统一注入。

## Source 渲染

构建器把结构化来源渲染为 `label (url)`，多个来源以 `; ` 分隔。URL 为空时只显示 label。脚注解释定义和口径，不得用 `source=xx`、`TBD` 等占位文本。

## 失败语义

以下任一情况导致整个构建失败：JSON 非法、slides 为空、idx 不连续、meta 页数不一致、缺少必填语义字段、占位符、错误 evidence/source、未知引擎或版式、版式参数不匹配、单页未生成、最终实际页数不一致。