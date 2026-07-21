# 端到端示例 · Postgrad1A · letter · complaint

## 用途

- 展示 **Postgrad1A `letter_category = "complaint"`** 的完整 review → report 流程
- **重点演示 v1.6.1 新增 `category_specific_check` 字段在 HTML 报告中的渲染**：
  - `opening_phrase_ok` / `tone_ok` / `required_elements[]` / `category_pitfalls[]`
- 与校准样例 `postgrad1a-04-band-complaint-letter-01.md` 构成"样例-端到端"配对

## 本例亮点

| 维度 | 表现 |
|-----|------|
| letter_category 专属 5 要素 | 4/4 必备要素全 ✅ + 0 个 pitfall |
| 语气 | formal / 坚定但克制（无 angry 用语）|
| 数量化证据 | 30 pages / 198 RMB / 2 September / 15 August / Order No. | 
| 诉求 | 双方案（refund OR replacement）|
| 档位 | 第四档 7 分 |

## category_specific_check 示例

```json
{
  "opening_phrase_ok": true,
  "tone_ok": true,
  "required_elements": [
    { "name": "投诉事实（事件+时间+损失）", "present": true, "evidence": "..." },
    { "name": "订单号等定位信息", "present": true, "evidence": "..." },
    { "name": "具体诉求（含补救方案）", "present": true, "evidence": "..." },
    { "name": "期待回复", "present": true, "evidence": "..." }
  ],
  "category_pitfalls": []
}
```

**所有 4 个 required_elements 在报告中以绿色 `✓` 标注**，`category_pitfalls` 为空数组不显示。

## 文件清单

| 文件 | 说明 |
|-----|------|
| `input.txt` | 原始输入 |
| `review.json` | 批改引擎输出（含 `category_specific_check` 完整字段）|
| `report.html` | renderer 生成的中文报告 |

## 复现命令

```bash
cd <skill-root>   # 进入 english-exam-writing-reviewer Skill 根目录（本项目示例：.cursor/skills/english-exam-writing-reviewer）
python3 scripts/render_report.py \
  --json references/examples/postgrad1a-complaint-letter-example/review.json \
  --output assets/examples/postgrad1a-complaint-letter-example/report.html
```
