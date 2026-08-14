# 阶段2 · 建议（Suggest）

> **目标**：基于能力矩阵推荐 Agent，让用户确认或调整配置。
> **约束**：逐项弹窗确认，不可跳过、不可合并。

---

## 2.1 匹配模板

加载 `references/agent-templates.md` 中的**通用模板库**，按 `appType` 推荐。

---

## 2.2 默认推荐组合

默认推荐 **1 Agent + 2~4 Skill** 的组合，每个 Skill 都有清晰的"何时触发"。

---

## 2.3 展示推荐 + 逐项确认

> 🔴 步骤 1→2→3→4→5 必须依次用 `ask_followup_question` 弹窗确认（步骤4为内部 hook 执行），不可跳过、不可合并。

### 步骤 1：展示推荐概览 + 询问 Agent 名称

先展示推荐概览（只读信息），然后弹窗询问 Agent 名称：

```
🔎 推荐配置

应用类型：dashboard
推荐 Agent 名称：employee-dashboard-helper
推荐 Skills（3 个）：
  1) app-guide       — 应用导览
  2) overview-report — 生成数据周报/月报
  3) page-monitor    — 监控页面健康
```

然后用 `ask_followup_question` 弹窗：

> **Agent 名称确认**
>
> 选项：
> 1) 使用推荐名称：`employee-dashboard-helper`
> 2) 自定义名称（输入 kebab-case 名称）

### 步骤 2：询问启用的 Skill

确认名称后，弹窗询问 Skill 选择：

> **Skill 启用确认**
>
> 选项（multiSelect）：
> 1) app-guide — 应用导览
> 2) overview-report — 生成数据周报/月报
> 3) page-monitor — 监控页面健康
> 4) 添加自定义 Skill（描述你需要的功能）

### 步骤 3：能力启用确认

确认 Skill 后，进入 §2.4 能力启用确认。汇总 §1 `【CAPABILITY HOOK · detect】` 产出的能力建议，弹窗让用户选启用哪些可选能力。

### 步骤 4：【CAPABILITY HOOK · confirm】

对每个已启用的能力，依次执行其 `#confirm` 锚点（加载 `modules/{name}.md#confirm`），收集配置。详见 §2.5。

### 步骤 5：最终确认

能力确认后，进入 §2.6 最终确认。

---

## 2.3.1 自定义 Skill（可选）

如果用户在步骤 2 选了"添加自定义 Skill"，引导用户描述需求：

> 请描述你需要的功能，我会生成对应的 SKILL.md。
> 例如：
> - "一个能接收用户投诉并自动分类汇总的 Skill"
> - "一个能根据销售数据预测下月趋势的 Skill"
> - "一个能对比两个时间段数据变化的 Skill"

生成自定义 Skill 时，遵循 `references/agent-templates.md` §四"自定义 Skill 模板"中的格式：
- YAML frontmatter 必须包含 `name`（kebab-case）+ `description`（一句话，英文）
- body 必须包含：触发条件、执行流程、约束
- 每个自定义 Skill 以标准目录形式写入 `.agent/skills/{name}/`（含 `SKILL.md` + 按需支撑文件）
- 确保 skill name 不与其他 skill 重名

---

## 2.4 能力启用确认

> 确认 Skill 后执行。汇总 §1 `【CAPABILITY HOOK · detect】` 产出的能力建议，按注册表中的 `userLabel`（功能化名称）展示，弹窗让用户选启用哪些可选能力。

```
🔎 根据项目分析，推荐启用以下能力：

  ✅ 🔐 API 鉴权 — 检测到 N 个写接口 / M 个敏感路径，建议启用
  ⬜ （其他 detect 命中的能力按 userLabel 展示）

是否调整？（多选 / 全部采用推荐）
```

> **展示规则**：
> - 一律用各能力在 `modules/registry.md` 注册表中的 `userLabel`（如"🔐 API 鉴权"），**不暴露内部标识**（authz 等）
> - 每个能力后附一句话 detect 摘要（来自 §1 `#detect` 产出，各能力模块自定义）
> - detect 未命中（`recommend=false`）的能力不出现在列表
> - 用户确认后，对每个「已启用」的能力，依次进入 §2.5 调用其 `#confirm` 锚点

---

## 2.5 【CAPABILITY HOOK · confirm】

> 对每个已启用的能力，加载 `modules/{name}.md`，执行其 `#confirm` 锚点，收集配置并持久化。
> **执行方式**：按 `modules/registry.md` §3.1 能力清单表顺序，对 `enabled=true` 的能力逐一 confirm。
> 各能力的 confirm 步骤与产出见对应 `modules/{name}.md#confirm`（如 authz 的步骤 A/B + 名单来源选择产出 `.agent/authz/api-authz.json`）。
> 主线不硬编码任何能力名，按注册表遍历执行。

---

## 2.6 最终确认

所有询问完成后，展示最终配置摘要，让用户做最后确认：

```
🤖 最终 Agent 配置

名称：employee-dashboard-helper
Skills（3 个）：
  1) app-guide       — 应用导览
  2) overview-report — 生成数据周报/月报
  3) page-monitor    — 监控页面健康
能力：${已启用能力列表，如「API 鉴权(middleware·N个受限接口)」}
MCP Bridge：将生成于 mcp_server/，端口自动分配（起始 :8932）

继续创建？(y/n)
```

> 此步骤是最终总确认，用户选 `y` 后进入阶段三（创建）。选 `n` 则回到 §2.3 对应步骤调整。

---

## 2.7 路线 B · 修改模式（改已有 Skill）

> 路线 B 选项 1 触发。只改 Skill 的 prompt/规则，不改代码、不重新部署。

### 步骤 1：展示已有 Skill 列表

从 `boost-state.json` 读取 `skills` 列表（每项含 `name` + `hasFiles`），`ask_followup_question` 让用户选要修改哪个 Skill。

### 步骤 2：读取并展示当前内容

读取选中的 `.agent/skills/{name}/SKILL.md` 全文展示给用户（多文件 skill 可一并展示支撑文件列表）。

### 步骤 3：收集修改意图

`ask_followup_question` 询问修改方向（如"调整触发条件"/"修改执行流程"/"增加约束"等），或让用户直接描述修改需求。

### 步骤 4：更新 SKILL.md

按用户意图更新对应 `SKILL.md`，保留 frontmatter 不变，修改 body。更新后展示 diff 摘要让用户确认。

### 步骤 5：→ §4.3 快速注册

无需重新部署，直接快速注册使改动秒级生效。

---

## 2.8 路线 B · 轻量版（新增 Skill）

> 路线 B 选项 2 触发。在现有 Agent 上添加新 Skill，不重建已有文件、不重新部署。

### 步骤 1：展示已有 Skill + 可选模板

从 `boost-state.json` 读取已有 `skills`（避免重名），加载 `references/agent-templates.md` 展示可选模板列表。

### 步骤 2：选择 Skill

`ask_followup_question` 让用户选模板或自定义。校验 skill name 不与已有 skill 重名。

### 步骤 3：生成 SKILL.md

- 选模板 → 从 `agent-templates.md` 取对应模板，按项目实际情况微调
- 自定义 → 引导描述需求，按 §2.3.1"自定义 Skill 模板"格式生成

写入 `.agent/skills/{name}/`（标准目录形式，不覆盖已有文件）。

### 步骤 4：更新 boost-state.json

将新 skill 元数据 `{"name": "<name>", "hasFiles": <true/false>}` 追加到 `skills` 数组。

### 步骤 5：→ §4.3 快速注册

无需重新部署，直接快速注册使新 Skill 生效。
