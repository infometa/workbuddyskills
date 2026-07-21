# 端到端示例 · CET4 · news_report

## 用途

- 展示 **CET4 `task_subtype = "news_report"`** 的完整 review → report 流程
- 演示 `news_report_check` 字段（v1.7.0 新增）：五 W 覆盖 + 第一人称禁用 + 主观评价禁用 + 引述存在性
- 展示 `calibration_status = "normal"` 的 banner 默认隐藏逻辑

## 本例亮点

| 维度 | 表现 |
|-----|------|
| 五 W 齐全 | when / where / who / what / why_significance 全覆盖 |
| 第一人称 | ❌ 未使用（news_report 核心禁令）|
| 主观评价 | ❌ 未使用 |
| 引述 | ✅ `According to Zhang Wei, the chief coordinator` |
| 档位 | 第四档 11 分（= CET4 news_report 中位锚点，与 `cet4-08-band-news-report-01.md` 形成档位对比）|

## 文件清单

| 文件 | 说明 |
|-----|------|
| `input.txt` | 原始输入（exam_level + prompt + essay 三段）|
| `review.json` | 批改引擎输出（含 v1.7.0 全部新字段）|
| `report.html` | `render_report.py` 渲染出的中文报告 |

## 复现命令

```bash
cd <skill-root>   # 进入 english-exam-writing-reviewer Skill 根目录（本项目示例：.cursor/skills/english-exam-writing-reviewer）
python3 scripts/render_report.py \
  --json references/examples/cet4-news-report-example/review.json \
  --output assets/examples/cet4-news-report-example/report.html
```

## 与同类锚点样例的档位关系

| 样例 | 档位 | 与本例关系 |
|-----|------|-----------|
| `cet4-08-band-news-report-01.md` | 第三档 8 分 | 第一人称 + 主观评价双重 critical，扣至 3 档 |
| **本例（cet4-news-report-example）** | **第四档 11 分** | **news_report 合规典范** |
