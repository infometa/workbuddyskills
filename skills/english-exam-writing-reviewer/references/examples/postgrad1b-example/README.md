# 端到端批改示例：考研英语一 B 节（v1.4 新增）

> 本示例展示 **从原始考生作文 → JSON 批改数据 → 最终 HTML 报告** 的完整链路，
> 供用户（老师/考生）直观理解 english-exam-writing-reviewer 的输出形态。

## 1. 场景

- **考试级别**：Postgrad1B（考研英语一 B 节，图画论述文）
- **题目**：`input.txt` ——站在黄昏十字路口的青年，面对"即时成功"与"长路修炼"两条路
- **考生字数**：195 词（在 160–200 区间内，合规）
- **最终评分**：第四档 14/20（报告分原分制）

## 2. 文件清单

| 文件 | 内容 | 用途 |
|------|------|-----|
| `input.txt` | Directions + 考生原文 + 元信息 | 人读输入 |
| `review.json` | 完整的批改 JSON（符合 `references/output-schema.md`）| 机读输出 + HTML 渲染源 |
| `report.html` | 由 `scripts/render_report.py` 生成的中文报告 | 最终交付给用户的批改卷 |

## 3. 完整工作流演示

### 第一步：字数校验
```bash
python scripts/word_count.py --essay-file references/examples/postgrad1b-example/input.txt \
                              --exam-level Postgrad1B
# 输出：{"effective": 195, "requirement_min": 160, "requirement_max": 200,
#        "within_range": true, "penalty_triggered": false}
```

### 第二步：按 6 步工作流定档评分
参考 `references/scoring-workflow.md`：
1. **判型**：`exam_level=Postgrad1B, task_subtype=cartoon` ← 依据 Directions
2. **基础画像**：5 维定性打分（见 `review.json.dimension_diagnosis`）
3. **档次定位**：三要点齐全 + 语法较丰富 + 语言错误 3 处 → **第四档 13–16**
4. **档内调节**：完整度 > 下限但语言精度/衔接多样性均未达高位 → **+1 = 14**
5. **可追溯证据链**：6 条 `rationale_trace`，每条 claim 绑定 rubric_ref + evidence
6. **词汇升档 + 生成报告**：5 条 vocabulary_upgrades 基于 `references/writing-vocabulary.md`

### 第三步：渲染 HTML 报告
```bash
python scripts/render_report.py references/examples/postgrad1b-example/review.json \
                                 --output assets/examples/postgrad1b-example/report.html
# 输出：✅ HTML 报告生成成功
#       考试级别: Postgrad1B
#       最终分:   14/20
#       档次:     第四档（良好）
```

## 4. 关键评分证据回表

### 为什么是第四档（13-16）？
| 判定要素 | 本文表现 | 档次标准 |
|---------|---------|---------|
| 任务完成 | 三要点齐全 | **较好完成** ✓ |
| 语法结构 | 倒装（Only by… can we）+ 现在分词 × 2 | **较丰富** ✓ |
| 词汇 | fragile / attractive / patient 等 mid tier | **较丰富** ✓ |
| 错误密度 | 3 处主谓一致 | **基本准确，只有个别错误** ✓ |
| 衔接 | However / But / So + In my opinion | **适当运用衔接** ✓ |

### 为什么是档内 14（中高位）而非 16（高位）？
- ¶3 评论段**单向论证**（缺辩证维度）——第五档要求"立论有深度、多角度"；
- 衔接手法**偏模板**（However/So 高频）——第五档要求多种衔接手法自然交织；
- 无一处 academic tier 词汇——第五档要求"地道且精准"的高阶表达。

### 为什么不是第五档（17–20）？
读 `review.json.boundary_decision.compared_with_higher` 字段：完整列举 3 条差距，
每条都可在作文中定位。

## 5. 升档路径（14 → 17，跨入第五档）

从 `review.json.upgrade_path.actions`（5 条具体行动）：

1. **修复 3 处主谓一致**（tells / requires / makes）—— 语言准确性从"小错若干" → "基本零错"
2. **¶3 加辩证** —— "当然，不是每条亮路都是陷阱——时机与机遇亦不可忽视——但即便如此，
   深度积累的效益在长期仍胜于速度追逐"
3. **跨段呼应** —— ¶3 开头加 `Returning to the dusk crossroads,...`
4. **高阶句式** —— 独立主格 `With shortcuts crowded by impatient feet, the long road
   awaits those willing to...`
5. **词汇升档 × 5** —— 见 `review.json.vocabulary_upgrades`

## 6. 查看 HTML 报告

打开 `report.html`（浏览器直接双击即可），将看到 9 大区块：

1. 顶部仪表盘（14/20 + 第四档标签 + 档内调节 +1）
2. **档次判定（官方描述符）** ——  引用 2025 考研英语一大纲 B 节第四档原文
3. **评分维度诊断（考研 5 维）** —— 任务完成/语法词汇/准确/衔接/格式语域
4. *（考研 A 节特有 · 本例不显示）*
5. **档次边界判定** —— 与高档差距 + 与低档优势
6. **扣分明细** —— 本例无扣分
7. **错误清单** —— 3 warning + 2 tip，带位置、原文、建议、原因
8. **升档路径** —— 5 条具体行动
9. **词汇升档建议** —— 5 条 Low/Mid → High/Academic 的替换表
10. **判定证据链** —— 6 条可追溯 rationale_trace
11. **附录** —— 原题 + 作文原文

## 7. 延伸实验

- **不同考试标尺**：把 `meta.exam_level` 改成 `CET6` 重新渲染，看同一文在 CET-6
  rubric 下落到什么档次（预期：由于缺失 CET 议论文套路、文体不完全契合，大约落
  第三档 10-11 分）
- **跨考试推演**：用 `scripts/diff_rubric.py Postgrad1B CET6` 查看两者差异
- **回归测试**：用 `scripts/calibrate.py` 扫描含本例在内的所有样例是否符合 band 区间

## 8. 如何生成你自己的端到端示例

1. 把考生作文粘贴到一个文本文件（仿 `input.txt` 三段式）；
2. 按 `references/scoring-workflow.md` 的 6 步产出 `review.json`（或让 Skill 自动生成）；
3. 运行 `python scripts/render_report.py review.json --output report.html`；
4. 打开 `report.html` 检查批改质量。

---

## 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-04-22 | v1.4.0 新增——第一份端到端示例，覆盖考研英一 B 图画论述文（第四档 14 分） |
