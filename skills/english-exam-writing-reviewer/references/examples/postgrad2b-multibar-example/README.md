# 端到端示例 · Postgrad2B · multi_bar

## 用途

- 展示 **Postgrad2B `chart_subtype = "multi_bar"`** 的完整 review → report 流程
- **重点演示 v1.6.1 新增 `chart_subtype_specific` 字段在 HTML 报告中的渲染**：
  - `data_coverage_ratio` / `data_coverage_note` / `data_accuracy_errors[]`
  - `trend_description_ok` / `multi_group_parallel_ok` / `interpretation_present`
- 与校准样例 `postgrad2b-04-band-multibar-01.md` 构成"样例-端到端"配对

## 本例亮点

| 维度 | 表现 |
|-----|------|
| `data_coverage_ratio` | **1.0**（6/6 数据点全精确）|
| `data_accuracy_errors` | 空数组（无错位）|
| `multi_group_parallel_ok` | ✅ 两组（2019/2024）均描述 |
| `trend_description_ok` | ✅ 三类均上升方向正确 |
| `interpretation_present` | ✅ 双因素归因 + 宏观评论 |
| 档位 | 第四档 11 分 |

## chart_subtype_specific 示例

```json
{
  "data_coverage_ratio": 1.0,
  "data_coverage_note": "6 个数据点（3 项 × 2 年）全覆盖且精确",
  "data_accuracy_errors": [],
  "trend_description_ok": true,
  "multi_group_parallel_ok": true,
  "interpretation_present": true
}
```

在 HTML 报告中：
- `data_coverage_ratio ≥ 0.95` → **绿色进度条 100%**
- `data_accuracy_errors` 为空 → "无数据错位"
- `multi_group_parallel_ok = true` → multi_bar 硬门槛绿勾

## 文件清单

| 文件 | 说明 |
|-----|------|
| `input.txt` | 原始输入 |
| `review.json` | 批改引擎输出（含 `chart_subtype_specific` 完整字段）|
| `report.html` | renderer 生成的中文报告 |

## 复现命令

```bash
cd <skill-root>   # 进入 english-exam-writing-reviewer Skill 根目录（本项目示例：.cursor/skills/english-exam-writing-reviewer）
python3 scripts/render_report.py \
  --json references/examples/postgrad2b-multibar-example/review.json \
  --output assets/examples/postgrad2b-multibar-example/report.html
```

## 与校准样例的对比

| 样例 | 数据覆盖 | 多组并列 | 档位 |
|-----|---------|---------|------|
| `postgrad2b-04-band-multibar-01.md` | 89%（others 未量化）| ✅ | 4 档 10 分 |
| **本例** | **100%** | **✅** | **4 档 11 分**（同档更高位）|
