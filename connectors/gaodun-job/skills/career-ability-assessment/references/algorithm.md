# 职业能力倾向测评算法说明（85题版）

## 维度定义

职业能力倾向测评共 17 个能力维度，分属 2 部分：

**第一部分 · 天赋能力（6 维）**

| 维度 ID | 名称 | sort |
|---|---|---|
| 10000 | 语言能力 | 16 |
| 10001 | 写作能力 | 13 |
| 10002 | 数学能力 | 10 |
| 10003 | 空间能力 | 4 |
| 10004 | 动觉能力 | 2 |
| 10005 | 审美能力 | 9 |

**第二部分 · 通用能力（11 维）**

| 维度 ID | 名称 | sort |
|---|---|---|
| 20000 | 逻辑思维 | 6 |
| 20001 | 研究分析 | 15 |
| 20002 | 创新能力 | 1 |
| 20003 | 灵活应变 | 5 |
| 20004 | 人际交往 | 8 |
| 20005 | 组织协调 | 17 |
| 20006 | 风险防范 | 3 |
| 20007 | 商业思维 | 11 |
| 20008 | 用户洞察 | 14 |
| 20009 | 细节洞察 | 12 |
| 20010 | 情绪控制 | 7 |

每个维度 5 道题，共 17 × 5 = 85 题。

## 计分设计原则

- **五级作答**：每题 5 个选项 A–E，对应 完全符合 / 比较符合 / 一般符合 / 比较不符合 / 完全不符合。
- **正向计分**（越符合得分越高），40 分制原始分换算为 100 分制显示（偶数×2.5 恒为整数，无需四舍五入）：

| 选项 | 标签 | 分数 |
|---|---|---|
| A | 完全符合 | 8 |
| B | 比较符合 | 6 |
| C | 一般符合 | 4 |
| D | 比较不符合 | 2 |
| E | 完全不符合 | 0 |

- 每题归属于且仅归属于一个能力维度（题库 `dimensionList` 标注）。
- 维度得分 = 该维度 5 题得分之和，范围 **0–40**；报告页按 100 分制展示（`score = rawScore × 2.5`）。
- 17 个维度各自独立计分，维度间不共享题目。

## 作答输入格式

评分脚本 `calculate_scores(answers, questions)` 的 `answers` 支持两种合规格式，均按全局 `seq` 1→85 顺序解析：

1. **紧凑序列（推荐）**：长度为 85 的 `A`/`B`/`C`/`D`/`E` 字符串，第 `i` 位对应 `seq=i` 的题（1-based）。
   - 示例：`"ABCABCABCABC..."`（共 85 字符）。
   - 优点：约 85 字符，远低于系统约 530 字符的传输截断阈值，提交不丢数据。
2. **JSON 对象（兼容，不推荐）**：键为 `seq` 字符串、值为 `A`–`E`。
   - 示例：`{"1":"A","2":"B",...}`。
   - 缺点：约 530 字符量级，在约 530 字符处会被系统截断，导致答案丢失。

两种格式产生的评分结果完全一致。序列解析时忽略空格等分隔字符，仅取 `A`/`B`/`C`/`D`/`E`；序列长度不足 85 时，视为未答完，返回 `incomplete`。

## 评分公式

```text
score_map = { "A": 8, "B": 6, "C": 4, "D": 2, "E": 0 }

for each question q (按 seq 1..85):
    dim = q.dimension
    a   = normalize(answers[seq_of(q)])        # "A".."E"
    if a in score_map:
        score[dim] += score_map[a]

# 每维度原始分 0..40
```

其中 `q.dimension` 即题库中该题所属 `dimensionList` 元素的 `id`（如 `10000`）或其 `name`（如 `语言能力`）；脚本需建立 `seq → dimension` 的映射（题目按 `dimensionList.questionList.seq` 遍历即可）。

## 评分脚本

评分入口：`career-ability-assessment/scripts/calculate_scores.py`，函数 `calculate_scores`。

```bash
# 推荐：紧凑序列（85 位 A-E 字符串，约 85 字符，不触发传输截断）
python career-ability-assessment/scripts/calculate_scores.py \
  --answers 'ABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCA'

# 指定 Top N 优势维度数量（默认 5，报告页能力卡片数）
python career-ability-assessment/scripts/calculate_scores.py --answers 'ABCAB...' --top-n 5

# 兼容：旧 JSON 对象格式（约 530 字符，不推荐，存在被截断风险）
python career-ability-assessment/scripts/calculate_scores.py \
  --answers '{"1":"A","2":"B","3":"C","4":"D","5":"E"}'
```

## 结果输出

评分脚本 `calculate_scores(answers, questions, dimensions, score_map, meta, top_n)` 输出 JSON，对齐前端报告页（上半 Top5 能力卡片 + 下半 17 维得分条）：

```json
{
  "assessment_id": "CAREER-ABILITY-85-001",
  "status": "completed",
  "answered_count": 85,
  "total_questions": 85,
  "dimension_count": 17,
  "totalScore": 49,
  "maxTotalScore": 100,
  "top_n": 5,
  "details": [
    { "id": 10000, "name": "语言能力", "sort": 16, "score": 65, "rawScore": 26, "maxScore": 100 }
  ],
  "ranked_dimensions": [
    { "id": 10004, "name": "动觉能力", "sort": 2, "score": 70 }
  ],
  "top_dimensions": [
    { "id": 10004, "name": "动觉能力", "sort": 2, "score": 70 }
  ],
  "reportTextList": [
    {
      "id": 10004,
      "name": "动觉能力",
      "score": 70,
      "highScoreDesc": "你的肢体协调能力较强，动作敏捷、反应迅速……"
    }
  ],
  "runnerUp": [
    { "id": 20007, "name": "商业思维", "score": 60 },
    { "id": 20010, "name": "情绪控制", "score": 60 }
  ],
  "qrCodePath": "pages/career-ability/index"
}
```

- `status`：`completed` / `incomplete`
- `answered_count` / `total_questions`：已答数 / 总数（85）
- `totalScore`：100 分制总分（满分 100），`maxTotalScore=100`
- `details`：17 个维度得分条数据源，按固定优先级顺序输出；`score` 为 100 分制（`maxScore=100`），`rawScore` 为 40 分制原始分（校验用）
- `ranked_dimensions`：17 维按分数降序；分数相同按固定优先级取靠前者
- `top_dimensions`：Top 5 优势维度（报告页上半部分能力卡片）
- `reportTextList`：Top 5 能力卡片数据源，每项含 `name`/`score`/`highScoreDesc`（**不含 icon/bgImg**，卡片不渲染图片避免图床花屏），文案取自题库预定义，不允许自由发挥
- `runnerUp`：与第 5 名同分但未入选卡片的维度数组（并列第 5）；非空时报告卡在 Top 5 下方补"同时，你在 xxx、xxx 能力方面得分也比较高"，`xxx` 取 `runnerUp[].name`；为空则不显示
- `qrCodePath`：固定跳转路径
- 若 `status == incomplete`，列出缺失题号 `missing_questions`

## 分数换算

40 分制原始分 → 100 分制显示分。计分映射 8/6/4/2/0 均为偶数，每维 5 题原始分必为偶数，换算恒为整数，**无需四舍五入**：

```text
score100   = rawScore * 100 // 40    # = rawScore * 2.5（偶数×2.5 必为整数）
totalScore = totalRaw * 100 // 680   # 总分：满分 680 → 100
```

## 评分标准说明

- 每个维度得分范围 0–40；
- 得分越高，说明用户在该能力维度上越具优势；
- 取若干高分维度作为职业能力优势画像；
- 若用户未答完 85 题，返回 `incomplete` 状态并给出未完成题号，不得强行生成完整结论。

## 确定性要求

1. 结果必须以脚本计算为唯一准绳，不允许模型自由推断分数。
2. `details` 中 17 个维度必须按固定顺序输出。
3. `top_dimensions` 必须按分数降序排列；分数相同按固定维度优先级取靠前者，确保同输入→同输出。
4. 分数必须为整数，由公式计算产生。
5. 任何场景都不允许输出随机、模糊、口语化的结论。
6. 生成结果时必须以 JSON 对象返回，不能返回 Markdown、自然语言说明或额外字段。

## 维度顺序约定（建议）

为保证确定性输出，`details` 建议按以下固定顺序（题库 `partList → dimensionList` 的自然顺序）：

```
10000 语言能力, 10001 写作能力, 10002 数学能力, 10003 空间能力, 10004 动觉能力, 10005 审美能力,
20000 逻辑思维, 20001 研究分析, 20002 创新能力, 20003 灵活应变, 20004 人际交往, 20005 组织协调,
20006 风险防范, 20007 商业思维, 20008 用户洞察, 20009 细节洞察, 20010 情绪控制
```

固定维度优先级（用于分数相同时的并列处理，取靠前者）即以上列表顺序。

## 扩展说明

本版本 85 题（17 维 × 5 题）满足当前测评需求。若后续需扩充每维度题量或新增能力维度，可按同一计分规则继续扩充题库，不影响评分逻辑（维度得分改为该维度所有题目得分之和，范围相应放大）。
