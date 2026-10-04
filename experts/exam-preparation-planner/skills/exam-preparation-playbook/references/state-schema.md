# 备考状态与迁移规则

## 一、计划状态

```yaml
exams:
  - id: ""
    name: ""
    date: ""
    goal: ""
    current_level: ""
    scope_source: ""
    minimum_daily_minutes: 0
    priority: high | medium | low | pending
constraints:
  daily_minutes: 0
  capacity_type: gross | net | unknown
  buffer_rate: 0.15
  unavailable_times: []
  preferred_session_minutes: 30
mode: term | sprint | rescue
plan_version: 1
assumptions: []
last_review_date: ""
next_review_date: ""
change_log: []
```

字段原则：

- `scope_source` 记录“已核验 / 用户提供 / 待确认”及具体来源。
- `priority` 依据不足时使用 `pending`，不伪造排序。
- `plan_version` 使用递增整数；第一次成形计划为 1，每次实质重排加 1。
- 仅调整措辞或解释、不改变任务和状态时，不递增版本。

## 二、知识点状态

```yaml
- id: ""
  subject: ""
  chapter: ""
  topic: ""
  scope_source: ""
  exam_weight: high | medium | low | unknown
  mastery: proficient | uncertain | not_learned | unverified
  estimated_minutes: 0
  status: not_started | learning | due_for_review | verified
  evidence_type: answer | practice | recall | mock | correction | self_report | none
  evidence: ""
  next_action: ""
  next_review_date: ""
```

### 掌握状态迁移

- 新知识点默认 `unverified`，明确完全未学可记为 `not_learned`。
- 只看过、抄完、听懂或主观感觉良好，不得直接进入 `proficient`。
- 独立答题、实操、闭卷复述、真题、自测或错题复做表现不稳定，更新为 `uncertain`。
- 至少一次与目标匹配的独立验证达到完成标准，才可更新为 `proficient`；高风险或高权重内容仍应安排后续复验。
- 新证据显示错误或遗忘时，可从 `proficient` 回退到 `uncertain`，并记录原因。

## 三、每日任务

```yaml
- id: ""
  date: ""
  priority: A | B | C
  action: ""
  topic: ""
  estimated_minutes: 0
  completion_criteria: ""
  status: completed | partial | not_started | cancelled | replaced
  actual_minutes: 0
  mastery: proficient | uncertain | not_learned | unverified
  blocker: ""
  previous_task_id: ""
  change_reason: ""
```

### 任务状态迁移

- `completed`：达到完成标准；是否掌握仍由证据单独判断。
- `partial`：只完成部分标准；下一轮不得默认整项重做，先保留已完成部分。
- `not_started`：先判断原因，不自动判定为懒惰或执行力差。
- `cancelled`：任务已无价值、容量不足或条件不成立。
- `replaced`：用更小前置任务、替代练习或更合适任务替换，并填写 `previous_task_id` 和原因。

## 四、每次打卡后的状态迁移

按固定顺序执行：

1. **匹配原任务**：优先用任务 ID；没有 ID 时用日期、动作和知识点匹配。
2. **更新执行结果**：记录完成状态、实际耗时和卡点。
3. **更新掌握证据**：只根据答题、实操、复述、真题、自测或错题复做改变掌握状态。
4. **校正估时**：同类任务实际耗时明显偏离时，后续估时参考最近证据，不沿用旧值。
5. **检查重排触发器**：连续未完成、耗时偏差、新高权重弱项、范围或日程变化、容量溢出、疲劳或受挫。
6. **生成差异**：列出保留、后移、删除、新增和替换项及原因。
7. **递增版本**：任务顺序、容量、范围或优先级发生实质变化时，`plan_version + 1`。
8. **给出下一入口**：明确用户完成什么后再反馈哪些字段。

## 五、变更日志

每次实质重排追加一条：

```yaml
- version: 2
  reason: "A1 实际耗时 80 分钟，超过原估时且卡在前置知识"
  kept: ["task-a2"]
  moved: ["task-b1"]
  removed: ["task-c1"]
  added: ["task-a1-foundation"]
  replaced:
    - from: "task-a1"
      to: "task-a1-foundation"
  unresolved: ["考试范围仍待确认"]
```

理由必须对应用户反馈、练习证据或现实约束，不能只写“优化计划”。

## 六、多考试分配

多门考试并行时：

1. 先更新每门考试日期、目标、范围依据、当前基础和最低保障。
2. 使用 `decision-guide.md` 的稳定排序规则确定主攻科目。
3. 先分配最低保障，再分配剩余净容量。
4. 某门考试结束、目标完成或日程变化后，释放容量并生成新版本。
5. 范围和基础不足时将优先级标为 `pending`，同时给出最低风险诊断任务。

## 七、无持久化时的对话摘要

用户未要求写文件时，只在当前对话维护简化状态。每次形成或重排计划后，附一段可复制摘要：

```markdown
【下轮状态摘要｜计划 v2】
- 考试与日期：
- 每日净容量：
- 当前主攻：
- 今日任务 ID：
- 已验证掌握：
- 待确认：
- 下次反馈：任务 ID｜完成度｜掌握度｜实际耗时｜卡点
```

跨会话没有这段摘要或用户提供的历史记录时，不假装记得原计划。

## 八、记录与授权

- 写入工作区、日历或外部系统前，展示目标、内容摘要、是否覆盖及恢复方式，并取得用户确认。
- 不覆盖用户已有记录；优先新增版本或明确合并。
- 日期和时间使用用户所在时区；无法确定时先确认。
- 只记录规划需要的信息，不保存无关敏感字段。
