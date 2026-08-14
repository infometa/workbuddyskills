# Plan 编写指南

## 原则

写 plan 时，假设执行者对项目零上下文。plan 中必须包含执行每个 task 所需的全部信息：哪些文件需要操作、具体代码内容、如何验证结果。

每个 task 是一个 2-5 分钟可完成的原子操作。"验证"是独立的 step，不是附属操作。

## Plan Header（必须）

每个 plan 必须以此 header 开头：

```markdown
# {项目名} 执行计划

**Goal:** 一句话描述本次要达成的目标
**模板:** static / dw-readonly / crud / dw-crud（新建时）
**needs_dw:** true/false
**needs_db:** true/false

---
```

## Task 结构

plan 中的每个 task 使用 markdown checkbox，执行完毕后由模型将 `[ ]` 改为 `[x]`：

```markdown
- [ ] **Task 1: {组件/动作名}**

  **Files:**
  - Create: `exact/path/to/file`
  - Modify: `exact/path/to/file`

  **Step 1: {具体动作}**

  {精确的代码 / 命令 / 操作描述}

  **Step 2: 验证**

  {验证方式 + 预期结果}

- [ ] **Task 2: {组件/动作名}**

  ...
```

## Bite-Sized 粒度

每个 step 只做一件事：

- "复制模板到项目目录" — 一个 step
- "替换 PAGE_TITLE 占位符" — 一个 step
- "执行 full-deploy 部署到 AnyDev" — 一个 step
- "验证 health-check 通过" — 一个 step
- "执行 publish 注册发布" — 一个 step

**不要**把多个操作塞进一个 step。

## Remember

- 精确文件路径（不是"改一下那个文件"）
- 完整代码片段（不是"加个验证逻辑"）
- 精确 CLI 命令 + 预期输出
- 验证是独立 step，不是可选附属
- 每个 task 完成后有明确的验证方式

## page-deliver CLI 入参规范（必须写进相关 Task）

写 plan 时，凡是调用 `node "$PD" <topic> <subcommand>`，必须在命令里写出 `--help` 契约要求的完整 JSON 入参，尤其是 `projectDir`。不确定字段时先执行：

```bash
node "$PD" <topic> <subcommand> --help
```

常用命令的正确入参如下（`<project_dir_abs>` 必须替换为项目目录绝对路径）：

| 命令 | 正确调用示例 | 注意 |
|------|--------------|------|
| `state init` | `echo '{"projectId":"<project_id>","projectDir":"<project_dir_abs>","projectName":"<project_name>"}' \| node "$PD" state init --input -` | **幂等**：每个 project_dir 开始时都先执行一次。不存在则创建；已存在（含旧/异形结构，如 `schemaVersion≠2`、残留 `steps`）则**归一化为标准 schemaVersion=2**。归一化已有文件时 `projectId` 可省略（从文件读取，兼容 `project_id` 别名）；新建时 `projectId`/`projectDir` 必填 |
| `state show` | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" state show --input -` | 只读 state |
| `state update` | `echo '{"projectDir":"<project_dir_abs>","fields":{"needsDw":false,"needsDb":false}}' \| node "$PD" state update --input -` | 必须同时传 `projectDir` 和 `fields` |
| `anydev full-deploy` | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" anydev full-deploy --input -` | **只接受 `projectDir`**；不要传 `skillDir/envInsId/ip/port` |
| `anydev publish` | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" anydev publish --input -` | **只接受 `projectDir`**；必须等用户点击确认后执行 |
| `anydev remote-exec` | `echo '{"projectDir":"<project_dir_abs>","cmd":"pm2 logs <project_id> --lines 80 --nostream"}' \| node "$PD" anydev remote-exec --input -` | 只接受 `projectDir` + `cmd` |
| `inspect token` | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" inspect token --input -` | 部署复盘时使用 |
| `baseline stats` | `echo '{}' \| node "$PD" baseline stats --input -` | 无参数也要传 `{}` |
| `validate plan` | `echo '{"planPath":"<project_dir_abs>/docs/plan.md","state":{...deployState...}}' \| node "$PD" validate plan --input -` | 只读校验，主要给 inspector 使用 |
| `validate execution` | `echo '{"planPath":"<project_dir_abs>/docs/plan.md","projectDir":"<project_dir_abs>"}' \| node "$PD" validate execution --input -` | 只读校验，主要给 inspector 使用 |

Plan 中禁止出现缺 `projectDir` 的部署/state 命令，禁止给 `anydev full-deploy/publish/remote-exec` 传 `skillDir`。

---

## 迭代循环（核心流程）

> **代码合规检查**：在进入下面的迭代预览之前，建议在 Plan 中安排一个「代码合规检查」task，按 `${SKILL_DIR}/references/project-constraints.md` 自查并修复硬约束违规（C1 文件上传路径、C2 MongoDB 数据库名）。该 task 不计入"最后三个固定 task"，位置灵活（代码生成完成后、迭代预览前即可）。详见 SKILL.md → 阶段4 步骤5。

Plan 的最后**三个** task 必须固定为「迭代预览」「Dockerfile 检查/生成」「注册发布」，覆盖从部署到上线的完整循环。

### 1. Task N: 迭代预览

```
- [ ] **Task N: 迭代预览**
```

这是整个部署阶段的核心 task。它本身是一个**循环**，直到用户明确点击"确认发布"才跳出。

**循环体**（每次迭代）：
1. `anydev full-deploy` — 部署/重新部署代码到 AnyDev：
   ```bash
   echo '{"projectDir":"<project_dir_abs>"}' | node "$PD" anydev full-deploy --input -
   ```
2. 按 `references/output-templates.md` → **预览确认模板** 输出 markdown 表格
3. 按 `references/output-templates.md` → **后续动作** 的 JSON 格式弹出 `ask_followup_question`

**用户两种反应**：
- 用户**点"确认发布"** → 跳出循环，进入 Task N+1（Dockerfile 检查/生成）
- 用户**输入文字**（如"改一下颜色""再加个图表"）→ 模型修改代码 → **在 Task N 之前追加新的 task**（Task N-1.5 等），执行完新增的 task 后重新回到 Task N 的循环体开头（重新 full-deploy + 预览确认）。**不要**改本 task 的内容，**不要**把 `[ ]` 改回 `[x]`。

> ⚠️ **迭代中引入/移除 DB 或数仓时必须先同步 state**：若某轮反馈让代码**新增或去掉**了数据库持久化（mongoose/`db.js`/`MONGO_URI` 等）或数仓访问（`queryDW`/`starrocks` 等），在重新 `full-deploy` 之前先 `state update` 把 `needsDb` / `needsDw` 改成与代码一致的值：
> ```bash
> echo '{"projectDir":"<project_dir_abs>","fields":{"needsDb":true,"needsDw":false}}' | node "$PD" state update --input -
> ```
> 否则 `full-deploy` / `publish` 会因检测到「代码用了但 state flag 仍为 false」而 `STATE_DATA_MISMATCH` 强阻塞（publish 靠 `needsDb` 决定是否挂 mongo sidecar，flag 陈旧会导致生产起不来）。

**Plan 结构示意**（迭代后）：
```
- [x] Task 1: 初始化项目
- [x] Task 2: 填充页面内容
- [x] Task 3: 添加年龄分布图表   ← 用户反馈后新增
- [x] Task 4: 调整主题色         ← 用户反馈后新增
- [ ] Task 5: 迭代预览            ← 当前卡在这里
- [ ] Task 6: Dockerfile 检查/生成
- [ ] Task 7: 注册发布
```

**关键规则**：
- 每次修改都必须**重新 full-deploy**（`anydev full-deploy` 是幂等的，14 步走完保证状态一致）
- 修改代码后必须**重新弹确认按钮**
- "迭代预览" task 本身永远不勾 `[x]`，直到用户点了"确认发布"才勾，然后进入下一步
- Task N 之前的 task 正常勾 `[x]`

### 2. Task N+1: Dockerfile 检查/生成

```
- [ ] **Task N+1: Dockerfile 检查/生成**
```

**仅在用户点击"确认发布"后执行**。COS 归档的代码会被流水线拉取并按 Dockerfile 构建生产镜像，因此 Dockerfile 的正确性直接决定生产环境能否正常运行。

**目标**：确保项目根目录存在一个合理的 Dockerfile（含 `{{PROJECT_ID}}` 占位符）和配套的 `.dockerignore`。
- [重要] 使用 bash 命令 `cp` 目标dockerfile 到项目根目录， 在已有模板的基础上新增内容，** 不要动已有内容 ** 
- 完成后将 projectType 持久化到 state

### 3. Task N+2: 注册发布

```
- [ ] **Task N+2: 注册发布**
```

**Dockerfile 就绪后执行**。`anydev publish` 内部自动完成 Gateway 注册 + COS 归档。成功后的输出格式见 `references/output-templates.md` → **部署输出模板**。

正确命令：

```bash
echo '{"projectDir":"<project_dir_abs>"}' | node "$PD" anydev publish --input -
```

完成后用 `state update` 标记完成（必须带 `projectDir` + `fields`）：

```bash
echo '{"projectDir":"<project_dir_abs>","fields":{"state":"completed"}}' | node "$PD" state update --input -
```

---

## Scene Reference（按需读取）

- **常见 Task 示例** → `${SKILL_DIR}/references/common-tasks.md`
- **dw-readonly 模板详细约束** → `${SKILL_DIR}/references/dw-readonly-guide.md`（仅 `needs_dw=true` 时读取）
- **输出模板** → `${SKILL_DIR}/references/output-templates.md`（部署阶段读取）

---

## 注意事项

- **不要把所有示例都写进 plan** — 只写本次需求真正需要的 task
- **task 之间可以合并** — 如果两个操作紧密关联且 2-5 分钟内能完成
- **数仓相关 task** 仅在 needs_dw=true 时出现，且必须使用模板内置工具（`batchQueryDW`、`useChart` 等）
- **数据库相关 task** 仅在 needs_db=true 时出现
- **文件上传相关 task** 仅在需求含文件上传时出现；存储路径硬约束见 `${SKILL_DIR}/references/project-constraints.md` → **C1**，由阶段4 步骤5 自查修复
