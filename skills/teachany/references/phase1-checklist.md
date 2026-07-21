# Phase 1 标准问卷与输出合同

> 目的：把教学设计从“模型自由判断”改成“结构化填空”。进入 Phase 2 前，必须完成本文件的问卷和输出合同。

## 1. 五问强制问卷

### Q1. 学习者画像

- 学段/年级：`{{STAGE_GRADE}}`
- 已学前置：`{{PREREQUISITE_NAMES}}`
- 常见卡点：来自 `_errors.json` / 教材补充 / 搜索记录
- 本课默认难度：基础 / 标准 / 挑战

判定要求：前置知识必须能落成至少 2 道前测题。

### Q2. 课型

从下列 5 类中选择一个，并写入 `manifest.json.lesson_type`：

| lesson_type | 适用场景 | 标准结构 |
| :--- | :--- | :--- |
| `new-concept` | 新概念、新公式、新方法 | ABT → 前测 → 概念建模 → 练习 → 后测 |
| `review` | 错题复盘、薄弱点修复 | 诊断 → 修复 → 迁移 → 再测 |
| `experiment` | 理科实验、现象验证 | 预测 → 观察 → 解释 → 证据 |
| `special-topic` | 跨节点专题 | 对比 → 连接 → 综合 |
| `inquiry-project` | 探究课/PBL | 问题 → 尝试 → 暴露缺口 → 学习 → 重试 → 反思 |

判定要求：课型必须和 `{{CONTENT_SECTIONS}}` 的 section 顺序一致。

### Q3. ABT 三句话

- And：学生已经知道 `{{KNOWN_CONTEXT}}`
- But：但现在遇到 `{{CONFLICT_OR_GAP}}`
- Therefore：所以本课要学 `{{TARGET_CONCEPT_OR_METHOD}}`

判定要求：ABT 必须面向学生，不直接展示课标文本。

### Q4. 问题锚点

填写 2-3 个真实问题，替换 `{{PROBLEM_ANCHOR_CHOICES}}`：

```html
<button class="choice" data-anchor-choice="{{ANCHOR_1}}">{{ANCHOR_1}}</button>
<button class="choice" data-anchor-choice="{{ANCHOR_2}}">{{ANCHOR_2}}</button>
<button class="choice" data-anchor-choice="{{ANCHOR_3}}">{{ANCHOR_3}}</button>
```

判定要求：问题锚点必须能牵引后续例子、section hint、AI 学伴建议问题。

### Q5. 核心交互

选择 1 个主交互，并写清楚“学生操作什么、系统反馈什么、学到什么”：

| 交互类型 | 适用场景 | 必填字段 |
| :--- | :--- | :--- |
| Canvas 参数滑块 | 函数、物理、数据变化 | 参数、实时图像、结论反馈 |
| SVG 拖拽/匹配 | 结构、流程、分类 | 拖拽目标、判定规则、错因反馈 |
| ConcepTest | 概念误区 | 题干、正确项、3 个干扰项、诊断 |
| Leaflet 标准地图 | 历史/地理 | `data-teachany-map` 配置、本地 GeoJSON、hillshade |
| 记录单/反思单 | 探究课/PBL | 假设、证据、结论、反思 |

判定要求：交互不能只是装饰，必须改变学生判断或产生诊断反馈。

## 2. Phase 1 输出合同

进入 Phase 2 前，必须产出以下结构：

```markdown
## Phase 1 输出合同

- course_id：
- node_id：
- lesson_type：
- 学习者画像：
- ABT：
  - And：
  - But：
  - Therefore：
- 问题锚点：
  1.
  2.
  3.
- 主交互：
  - 类型：
  - 学生操作：
  - 系统反馈：
  - 学到什么：
- section 顺序：
  1. hero
  2. hero-infographic
  3. audio-player
  4. problem-anchor
  5. objectives
  6. pretest
  7. module-1
  8. module-2
  9. interaction
  10. posttest
  11. summary
  12. knowledge-graph
  13. teachany-ai-tutor-card
- Bloom 覆盖：至少 3 级
- ConcepTest 位置：
- 自适应四路分支：review-prereq / scaffold / normal / challenge
```

## 3. 阻断规则

以下任一项缺失，禁止进入 Phase 2：

- 未选择 `lesson_type`
- ABT 只有口号，没有具体冲突
- 问题锚点不能对应后续内容
- 没有前测设计
- 没有主交互设计
- Bloom 覆盖少于 3 级
- ConcepTest 没有干扰项诊断
- 未规划自适应四路分支
