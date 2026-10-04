# 霍兰德职业兴趣评测算法说明（60题版）

## 维度定义

霍兰德职业兴趣类型共有六大维度：

- R：现实型
- I：研究型
- A：艺术型
- S：社会型
- E：企业型
- C：常规型

## 题目设计原则

- 每题都归属于一个维度；
- 用户作答为 `Y` / `N`；
- 若该题属于某维度且答案为 `Y`，则该维度得分 +1；
- 维度总分可以理解为用户对该方向的倾向强度。
- 60 题版本中每个维度均匀分配 10 题，保证各维度可比较性。

## 作答输入格式

`calculate_scores(answers, questions)` 的 `answers` 支持两种合规格式，均按题号 1→60 顺序解析：

1. **紧凑序列（推荐）**：长度为 60 的 `Y`/`N` 字符串，第 `i` 位对应题号 `i`（1-based）。
   - 示例：`"YYNNYYNN...YYNN"`（共 60 字符）。
   - 优点：约 60 字符，远低于系统约 530 字符的传输截断阈值，提交不丢数据。
2. **JSON 对象（兼容，不推荐）**：键为题号字符串、值为 `Y`/`N`。
   - 示例：`{"1":"Y","2":"N",...}`。
   - 缺点：约 530 字符，在约 530 字符处会被系统截断，导致答案丢失。

两种格式产生的评分结果完全一致。序列解析时忽略空格等分隔字符，仅取 `Y`/`N`；序列长度不足 60 时，视为未答完，返回 `incomplete`。

## 评分公式

```text
score[dimension] = sum(1 for question in answered_questions if question.dimension == dimension and answer == "Y")
```

## 结果输出

- 维度分数 `details`：按固定顺序输出六个维度 `{"R": 7, "I": 3, "A": 2, "S": 6, "E": 5, "C": 4}`。
- `top_dimensions`：按分数降序取前 3 个维度；分数相同按固定优先级 `R, I, A, S, E, C` 取靠前者。
- `dominant_type`：`top_dimensions` 前 3 项拼接，例如 `RSE`。
- `reportTextList`：数组，只含 `top_dimensions` 对应 3 个维度的详情，每项字段为 `type / name / commonFeatures / typicalOccupations`（驼峰，不带 score）。
- `qrCodePath`：固定值 `"pages/hollander/index"`。

例如：

```text
R=7, S=6, E=5 -> top_dimensions = ["R","S","E"], dominant_type = "RSE"
```

## 评分标准说明

- 每个维度得分范围为 0~10；
- 得分越高，说明用户更偏向该维度；
- 取前三高分维度组成职业兴趣组合；
- 若用户未回答完所有题目，可返回 `incomplete` 状态并给出未完成题号。

## 扩展说明

本版本作为 60 题简版满足快速演示和平台上传要求。若后续需要接近 181 题真实量表，可按同一维度规则继续扩充题库，不影响评分逻辑。