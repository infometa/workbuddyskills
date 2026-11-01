# 单份自包含 HTML 报告结构模板

交付物为**单份自包含 HTML**（SVG/纯 CSS 内联，不外链本地资源，双击可开）。不产 Markdown、Word、PDF 或多册分册。

## 一、页面骨架

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{资产/标的}_{资产评估方法论参考}.html</title>
<style>
  body{font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;
       line-height:1.7;color:#1a1a1a;max-width:1040px;margin:0 auto;padding:32px;background:#fff;}
  h1{font-size:24px;border-bottom:3px solid #c0392b;padding-bottom:10px;margin-bottom:8px;}
  h2{font-size:19px;margin-top:32px;border-left:5px solid #c0392b;padding-left:10px;}
  h3{font-size:16px;margin-top:22px;color:#333;}
  table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13.5px;}
  th,td{border:1px solid #d0d0d0;padding:8px 10px;vertical-align:top;}
  th{background:#f4f4f4;font-weight:700;text-align:left;}
  .meta{color:#888;font-size:13px;margin-bottom:24px;}
  .verdict{background:#fafafa;border:1px solid #ddd;padding:16px 18px;border-radius:6px;margin:18px 0;}
  code{background:#f2f2f2;padding:1px 5px;border-radius:3px;font-size:12.5px;}
</style>
</head>
<body>
<!-- 正文 -->
</body>
</html>
```

图表用 `<svg>` 或纯 CSS 内联；字体用 `"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif`；不外链本地资源。

## 二、正文章节顺序（不可改）

1. **头部一句结论**：中性基准 + 窄幅区间 + 价值类型 + 基准日，一句话说完。
2. **概览表**：评估对象 / 评估目的 / 价值类型 / 评估基准日 / 所处环节 / 方法组合 / 中性基准 / 区间 / 关键参数。
3. **评估对象所处环节定位**：四层定位结论 + 易混淆点（若有）。
4. **方法适用性分析**：选用与未选用各方法的理由，附 `method_applicability.md` 口径。
5. **参数与测算**：分方法列公式、参数取值、来源标签与基准日；估算与假设单列。
6. **交叉验证与结论**：多方法结果对照、差异说明、收敛为单一中性基准与窄幅区间、流动性折让（若适用）。
7. **特别事项与假设前提**：权属瑕疵、资料限制、期后事项、未决诉讼等，逐条独立成行。
8. **风险与使用限制**。
9. **文末固定声明（一字不改）**：
   `本报告由祜·Care 与 Gangtise 合作开发，属测试技能，仅供资产评估方法论复盘与参考。本报告不构成任何投资建议，据此决策风险自担。如有优化建议或业务咨询，请联系 13386019198。`

## 三、来源标注位置

- 每个数字**就近**标注来源标签（`[项目方材料]` / `[研报]` / `[纪要]` / `[观点]` / `[公告]` / `[行情/财务]` / `[用户提供]`），不集中在页脚。
- 分析者署名 `[及]` 仅作分析者/合作署名，不当"独立裁判"。
- 硬数字须给时间快照与可自复核通道。

## 四、版式纪律（照 output-and-pitfalls.md）

- 表格与要点为主，禁大段无分段文字；
- 列表项（①②③ / 1.2.3.）独立成行，不挤一行；
- 无未闭合标签、无占位符、无孤立标题；
- 通篇中文，无工具词与故障词；
- 关键口径（基准值、半宽、折让）全文一致。
