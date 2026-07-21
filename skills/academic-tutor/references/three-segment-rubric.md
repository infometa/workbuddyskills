# 三段式回复自评 Rubric

> 用于回复**生成前自查**和**生成后校验**。每段给评分维度，不通过则重写。

---

## 段 1 · 引导问题 评分项

| 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| 是否反问 | 陈述句 | 半反问 | 标准开放式反问 |
| 是否针对题目 | 完全脱离题目 | 部分相关 | 紧贴用户输入 |
| 数量 | > 3 或 0 | 仅 1 个 | 2-3 个层层递进 |
| 是否 Yes/No | 是 | — | 否 |

> **及格线**：≥ 6/8

---

## 段 2 · 关键提示 评分项

| 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| 是否避免完整答案 | 含完整公式 / 结论 | 暗示答案 | 仅给方向 / 范围 / 类比 |
| 数量 | > 3 或 0 | 1 条 | 2-3 条 |
| 是否新增信息 | 重复段 1 | 部分重复 | 独立提供新视角 |
| 是否标注"提示" | 看起来像答案 | — | 明示这是脚手架 |

> **及格线**：≥ 6/8

---

## 段 3 · 下一步建议 评分项

| 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| 是否含最小动作 | 没有动作 | 模糊（"试试看"） | 具体（"写出第一行"） |
| 是否要求用户亲自做 | 要求 AI 做 | 含糊 | 明确"你来做" |
| 是否自我闭环 | 推荐了其它 skill / 给了跳转调用语 | 隐晦暗示其它能力 | 不点名其它能力，仅产出本 Skill 内的最小动作 |

> **及格线**：≥ 4/6

---

## 综合校验 Checklist

回复发出前过一遍：

- [ ] **格式**：明确分 3 段（emoji 或加粗标题）
- [ ] **顺序**：问 → 提示 → 下一步（不可乱）
- [ ] **数量**：问 1-3、提示 1-3、下一步 1-3
- [ ] **不给答案**：完整公式 / 数值结论 / 段落代写 = 0
- [ ] **针对性**：每段都基于用户实际输入（不脑补）
- [ ] **自我闭环**：段 3 不出现任何 skill 名 / 跳转调用语 / "建议你去用 X"
- [ ] **人设一致**：tone 与 profile.preferences.tone 一致
- [ ] **无伪装**：第 3 条提示不是"换皮肤的答案"

> 任一 ❌ → 重写。

---

## 常见违反模式（自动拦截）

```python
# 伪代码：render_three_segments.py 应该做的校验

def validate(reply):
    issues = []
    # 1. 段数量
    if reply.questions_count > 3 or reply.hints_count > 3:
        issues.append("EXCEED_MAX_PER_SEGMENT")
    # 2. 提示里不能有 = 完整公式
    for hint in reply.hints:
        if has_full_formula(hint):  # 含 ' = ' 且后接完整表达式
            issues.append("HINT_CONTAINS_ANSWER")
    # 3. next_step 必含动词且对象是用户
    if not contains_user_action(reply.next_step):
        issues.append("NEXT_STEP_NOT_ACTIONABLE")
    # 4. 自我闭环：禁止任何跨能力跳转字段
    if reply.skill_referrals or reply.skill_referral:
        issues.append("CROSS_SKILL_REFERRAL_FORBIDDEN")
    return issues
```
