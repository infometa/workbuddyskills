---
name: image-to-ui
description: "图生 UI（截图/设计稿 → 画布设计稿）。将参考图片转化为可编辑的 ardot 设计稿。四阶段流水线：设计风格提取 → 结构化精细描述 → 反思校验 → Agent Teams 画布绘制。触发场景：上传截图/线框图/草图要求生成设计稿、还原界面、复刻页面、参照图片设计。"
allowed-tools:
disable: false
---

# Image to UI — 图生 UI

将参考图片（截图、线框图、设计稿截图、手绘草图等）转化为可编辑的 ardot 画布设计稿。

**核心流程**：图片 → 设计风格提取 → 结构化精细描述 → 反思校验 → 画布绘制

本 Skill 采用 4 阶段流水线，融合 Prompt Chaining + Reflection + Multi-Agent Collaboration 设计模式。

## 输出规则

**Phase 1~3 是 Agent 内部思考过程，所有中间数据（`design_spec`、`page_structure`、校验结果等）禁止输出给用户。** 用户只需要看到：
- 简短的进度提示（如"正在分析设计风格…""正在构建画布…"）
- Phase 4 完成后的最终画布截图和完成说明

## 触发场景

在以下情况下激活本技能：

- **截图还原**："把这张截图做成设计稿"、"还原这个界面"、"复刻这个页面"
- **图片参考设计**："参照这张图设计"、"按照这个风格做一个页面"、"照着这个截图画"
- **草图转设计**："把我的手绘草图转成设计稿"、"根据线框图生成界面"
- **中文关键词**："图生 UI"、"截图转设计稿"、"照着这张图做"、"参照设计"、"还原界面"

**与其他能力的区分**：

| 场景 | 使用的 Skill |
|------|-------------|
| 用户上传图片 → 生成 ardot 画布设计稿 | **本 Skill（image-to-ui）** |
| 用户纯文字描述 → 生成 ardot 画布设计稿 | `ardot-design-assistant` |
| 用户上传图片 → 只做结构化分析，不生成设计稿 | `image-understanding-native` |
| 用户上传图片 → 编辑/风格转换图片本身 | `text_to_image` / `edit_image` MCP 工具（图片创作） |

## 工作流程

### Phase 1：设计风格提取（内部，不输出）

**目标**：从参考图片中提取 `design_spec`，所有参数格式直接对齐 ardot design-mcp API。

1. **获取图片** — 从用户上传的图片或提供的 URL 获取图片内容
2. **加载 `image-understanding-native` Skill**，执行 **设计风格提取**（任务 B）
3. 看图提取 `design_spec`，覆盖 10 个维度：style_direction / colors / variables / typography / spacing / corner_radius / shadows / borders / icons / layout

### Phase 2：结构化精细描述（内部，不输出）

**目标**：基于 Phase 1 的 design_spec，执行全页面结构分析，得到 `page_structure`。

1. 继续使用 `image-understanding-native` Skill，执行 **全页面结构分析**（任务 A）
2. 分析时所有设计参数引用 Phase 1 的 `design_spec`：
   - section 的 background 颜色来自 `design_spec.colors`
   - element 的字号来自 `design_spec.typography.scale`
   - 间距值来自 `design_spec.spacing.patterns`

### Phase 3：反思校验（内部，不输出）

**目标**：独立评审 Phase 1 + Phase 2 的结果，确保足够完整和准确。

Agent 作为独立的 Critic 角色，**重新看原图**，检查 4 个维度：

| 维度 | PASS 条件 |
|------|----------|
| 风格完整性 | colors >= 5 角色、typography >= 3 级、spacing 有 base_unit + >= 3 pattern、variables >= 5 COLOR + >= 2 FLOAT |
| 结构覆盖率 | sections bbox 总面积 / 10000 >= 90% |
| 参数一致性 | page_structure 中颜色值与 design_spec.colors 匹配率 >= 80% |
| 可绘制性 | 100% elements 有 type + label + bbox，交互元素有 width/height |

**回退策略**：

| 问题类型 | 修复方式 |
|---------|---------|
| 风格参数缺失/不准 | 回到 Phase 1 补充提取 |
| 结构区域遗漏 | 回到 Phase 2 追加分析 |
| 参数不一致 | 用 design_spec 的值替换结构描述中的值 |
| 元素不可绘制 | 对缺参数的元素补充视觉属性 |

**最多 2 轮**（初始 + 1 次修正）。第 2 轮仍未全部 PASS 则降级继续进入 Phase 4。

### Phase 4：画布绘制 (Agent Teams)

**目标**：基于 `design_spec` + `page_structure`，在 ardot 画布上生成可编辑的设计稿。

**加载 `ardot-design-assistant` Skill**，按照其标准工作流执行。

#### Design Lead 执行步骤

0. 确保设计文件已打开 — `create_design` / `open_design`（如编辑器已有文件则跳过），等待就绪确认后再继续
1. `fetch_editor_state(includeSchema: false)` — 获取画布状态和可用组件（schema 和编辑指南已内置为 reference 文件）
2. 加载内置设计规范 — 根据 `design_spec.style_direction.platform` 读取对应的 `references/guidelines-*.md` 文件
3. `fetch_style_guide(tags: design_spec.style_direction.tags)` — 匹配内置风格
4. `apply_variables(variables: design_spec.variables)` — **直接传入**，设置设计 Token
5. `locate_available_space(width, height)` — 定位画布位置
6. `batch_edit` scaffold — 创建顶层 Frame + 每个 section 的 placeholder Frame

#### 复杂度评估

| sections 数量 | 执行模式 |
|--------------|---------|
| <= 3 | 单 Agent 逐 section 构建 |
| >= 4 | Team Mode：spawn sub-agents 并行构建 |

#### Team Mode 执行

1. `team_create("image-to-ui-team")`
2. 为每个 section spawn 一个 sub-agent，prompt 包含：
   - 目标 frame ID
   - 该 section 的 `page_structure` 片段
   - `design_spec` 精简版（只保留该 section 用到的部分）
   - ardot 规则约束（25 ops/call、text 需 fill、cornerRadius 等）
3. 等待所有 sub-agents 完成
4. `capture_screenshot` 各 section → 保存到 `/workspace/ardot-screenshots`，读取截图文件检查视觉正确性
5. `batch_edit` 修复整合问题
6. `capture_screenshot` 全页 → 读取截图文件做最终验证
7. `team_delete`

### 阶段间的信息传递

| 从 | 到 | 传递内容 | 消费方式 |
|----|-----|---------|---------|
| Phase 1 | Phase 2 | `design_spec` | 颜色/字号/间距引用 |
| Phase 1 | Phase 3 | `design_spec` | 校验风格完整性和参数一致性 |
| Phase 2 | Phase 3 | `page_structure` | 校验结构覆盖率和可绘制性 |
| Phase 1 | Phase 4 | `design_spec.variables` | 直接传给 `apply_variables` |
| Phase 1 | Phase 4 | `design_spec.style_direction.tags` | 传给 `fetch_style_guide` |
| Phase 1 | Phase 4 | `design_spec.typography/spacing/shadows` | sub-agent 的设计参数 |
| Phase 2 | Phase 4 | `page_structure.layout.sections` | scaffold 结构 + sub-agent 任务分解 |

### bbox → ardot 尺寸转换

Phase 2 的 bbox 是百分比坐标，Phase 4 需要转换为 ardot 的 px 值：
- `x_px = bbox.x / 100 * viewport.width`
- `y_px = bbox.y / 100 * viewport.height`
- `width_px = bbox.width / 100 * viewport.width`
- `height_px = bbox.height / 100 * viewport.height`

优先使用 `width`/`height` 字段中的精确 px 值（如 `"240px"`）；当该字段为 `"fill"` 或 `"auto"` 时，回退到 bbox 换算值。

### 用户文字优先

当用户同时提供了参考图片和文字描述，且两者存在差异时：
- **文字描述优先** — 用户的文字说明是最终意图
- **图片作为视觉参考** — 图片提供布局和风格的参考基线
- 例如：用户上传了一张蓝色主题的 dashboard 截图，但文字说"帮我做一个绿色主题的类似页面" → 布局参照截图，颜色用绿色

## 关键规则

1. **中间数据不输出** — Phase 1~3 的 `design_spec`、`page_structure`、校验结果等 JSON 是 Agent 内部数据，**禁止在对话中输出给用户**。只给简短进度提示。
2. **严格按 4 阶段顺序执行** — Phase 1 → 2 → 3 → 4，不跳过任何阶段
3. **Phase 1 和 Phase 2 不可合并** — 先完成完整的 design_spec，再做结构分析
4. **Phase 3 必须重新看原图** — 不能只看 Phase 1/2 的数据，必须回头看原图独立评审
5. **design_spec.variables 直接传给 apply_variables** — 不做任何格式转换
6. **typography.scale 直接用于 batch_edit** — fontWeight 用数字字符串，lineHeight 用 `{value, unit}` 格式
7. **最多 2 轮校验** — Phase 3 不通过则修正 1 次，第 2 轮仍未通过则降级继续
8. **用户文字说明优先于图片** — 文字描述与图片有冲突时以文字为准
9. **不重复加载 Skill** — 如果 image-understanding-native 或 ardot-design-assistant 已在上下文中，不需要重复加载
