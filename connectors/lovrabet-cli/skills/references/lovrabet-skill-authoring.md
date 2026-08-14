# Skill 创建、更新与发布工作流

`lovrabet skill create/validate/install/list/push` 用于当前应用下 personal/company 业务 Skill 的本地开发和同步。Builtin Skill 由 sandbox 镜像或 CLI Built-in Skill 安装源提供，不通过 `lovrabet skill install` 拉取。

## 目录约定

所有新建或更新的 Skill 都在当前 workspace 的 `.agents/skills/<skillCode>/` 下完成。

- `skillCode` 使用简短英文 kebab-case，不超过 64 字符。
- `SKILL.md` 必须位于 Skill 目录根部。
- `lovrabet.skill.json` 必须位于 Skill 目录根部。
- 需要较长规则、schema、示例或脚本时，放入 `references/`、`scripts/` 或 `assets/`，并在 `SKILL.md` 中说明读取时机。
- `SKILL.md` frontmatter 中 `name` 固定写稳定 `skillCode`，不要写展示文案；面向用户的业务展示名写顶层 `displayName`，即使展示名暂时等于 `skillCode` 也应显式保留。
- 顶层 `example` 是一条用户可以直接发送、用于触发该 Skill 的推荐话术，例如 `example: 上传这份产品资料`。
- `example` 可选；缺失、空白或不是单个标量时，`lovrabet skill validate` 会给出 warning，但不阻断 push。
- 不要把正文说明、内部 CLI 命令、执行步骤或多个示例写入 `example`，也不要自动生成该字段。

### Thin Prompt，Thick Skill

用户 Prompt 只表达本次任务相对于稳定契约发生变化的目标、对象、范围等变量；稳定规则、执行步骤、能力标识、输出契约、安全边界和降级策略由业务 Skill 承载，不要求用户重复输入。

- `example`：一句用户可直接发送的最简典型诉求。
- `description`：说明触发语义以及何时使用或不使用。
- `SKILL.md` 与其明确引用的 `references/`：承载完整稳定契约。

如果用户必须在每次 Prompt 中重复 Skill 名称、内部命令或完整规则才能正确触发和执行，应优先补齐 `description` 或 Skill 契约，而不是继续加长 Prompt。

## 新建

```bash
lovrabet skill create --name "<skillCode>" --type read --target .agents/skills
lovrabet skill validate --dir .agents/skills/<skillCode> --strict
lovrabet skill push --dir .agents/skills/<skillCode> --diagram-file ./<skillCode>.mmd --format compress
```

业务 Skill 模板类型仅支持 `read | write`。Agent 必须根据业务目标显式传入 `--type`；无法判断是否存在业务副作用时，停止并请求澄清。仅查询、汇总或核对且不改变业务状态时选择 `read`；涉及创建、更新、删除、状态流转、发送、发布或上传等业务副作用时选择 `write`，并在 Skill 契约中定义预览、用户确认、正式执行、读回核对和失败恢复。

`displayName` 是给人看的展示名，`description` 是触发依据，要说明 Skill 做什么、什么时候使用、什么时候不要使用；`example` 则是一句推荐给用户直接发送的最简触发话术。

## 更新

本地已有目录时，直接编辑 `.agents/skills/<skillCode>/SKILL.md` 和必要资源。当前 workspace 没有目标 Skill 时，先安装当前应用可见的业务 Skill：

```bash
lovrabet skill install --project --code <skillCode> --format compress
lovrabet skill validate --dir .agents/skills/<skillCode> --strict
lovrabet skill push --dir .agents/skills/<skillCode> --diagram-file ./<skillCode>.mmd --format compress
```

`skill install` 默认安装到用户级 Agent Skill 目录。这里需要直接编辑当前项目中的 Skill，所以显式添加 `--project`，把有效链接写到当前工作目录的 `.agents/skills/<skillCode>`。

如果安装得到的是 company Skill，默认不要覆盖 company 源；新建或更新 personal 副本，通过带 `--diagram-file` 的 `lovrabet skill push` 保存为个人 Skill。

### 配置 YAML frontmatter

当用户要求修改展示名、推荐话术、读写类型或其他明确字段时，直接编辑目标 `SKILL.md` 顶部的 YAML frontmatter：

- 只修改用户明确指定的字段，保留其他字段和 Markdown 正文。
- `name` 是稳定 `skillCode`，普通配置任务不得修改。
- `displayName` 根据用户实际展示诉求填写人类可读名称。
- `example` 写一句用户可直接发送的最简触发话术。
- `metadata.type` 只能是 `read` 或 `write`。
- 不创建或开启 `metadata.internal`；未知字段默认保留，语义不明确时不修改。

修改后执行 `lovrabet skill validate --dir <dir> --strict`。只有用户明确要求更新 company 源并提交审核时，才按既有流程先 dry-run，再执行带 `--diagram-file` 的 `push --scope company`；否则遵循上文规则创建或更新 personal 副本。company 新版本审核通过前不得声称已生效。

推荐用户话术：

> 请把企业 Skill `<skillCode>` 的 YAML frontmatter 中 `displayName` 改为「<展示名>」，保持 `name` 不变；校验通过后提交企业版新版本审核。

## 生成作用流程图

每次创建 Skill 或修改源码并准备发布新版本时，Agent 必须在 push 前读取本次上传的 `SKILL.md` 及其明确引用的必要文件，直接编写一张 Mermaid flowchart。不要要求用户提供流程图。流程图是该 SkillVersion 的作用说明，不是实际执行记录。

图中应覆盖：

- 触发条件和主要输入。
- 关键执行步骤，以及影响结果的重要条件分支。
- 权限不足、契约缺失、校验失败或结果不确定时的停止、澄清或安全降级。
- 最终输出或业务副作用；写入类 Skill 还要体现确认与读回核对。

只写文档能够支持的步骤，标签保持简短，不逐段复述正文，也不编造能力。源码不足以形成可信流程图时，先完善 Skill 契约或向用户澄清，再发布；不得提交空图或占位图。

建议从 `flowchart TD` 开始，使用清晰的节点、边和条件标签表达作用流程。提交的文件必须是语法正确的 Mermaid；先让 dry-run 通过，再使用同一份文件正式发布。

将原始 Mermaid 保存为 `.mmd` 文本并通过 `--diagram-file` 传给 dry-run 和正式 push；两次必须使用同一份 Skill 源码和 Mermaid。文件可以放在 Skill 目录内或外；CLI 会把所选文件作为独立 diagram 提交，并在它位于 Skill 目录内时按规范化真实路径从包扫描中精确排除，不会忽略其他 `.mmd` 文件。也可以用 `--diagram-file -` 从标准输入读取。任一部分失败时修正后整体重试，不改成分步发布。

## 发布扫描告警

personal `skill push --dry-run` 会用 `visibility=PRIVATE` 调用 SkillHub publish validate，提前返回正式发布会遇到的 errors 和 warnings。errors 始终阻断；正式 push 遇到 warnings 时会展示告警并停止。人工复核后，personal 或 company push 都需显式添加 `--confirm-warnings`，提交未经改写的同一份包。CLI 不根据 warning 文案自行分类。

发布扫描告警是打包反馈，不是修改业务 Skill 的授权。不要为了通过扫描删除、替换或改写业务 Skill 中的标识、映射、路径、规则、scripts 或 references。先确认告警内容：

- 真实问题（例如明文凭证、违规扩展名或内容格式不匹配）：personal push 不会因 warning 自动停止，仍需根据返回结果尽快修复；涉及凭证时还必须轮换。
- 已确认的误报：保留源码，不要创建内容不同的临时发布副本。

CLI 不自动创建脱敏包，也不自动改写源 Skill。

## 发布公司级版本

本地目录确认可交付后，可提交公司级 Skill 新版本审核：

```bash
lovrabet skill validate --dir .agents/skills/<skillCode> --strict
lovrabet skill push --scope company --dir .agents/skills/<skillCode> --diagram-file ./<skillCode>.mmd --dry-run
lovrabet skill push --scope company --dir .agents/skills/<skillCode> --diagram-file ./<skillCode>.mmd --confirm-warnings --format compress
```

`push --scope company` 使用 SkillHub `NAMESPACE_ONLY` 可见性把 Skill 包与 Mermaid 一起提交审核。命令成功只表示带图的新版本已提交 review；审核通过前不要声称该版本已对所有成员生效。需要本机 Agent 使用生效版本时，审核后再执行 `lovrabet skill install --code <skillCode>`。

## 内容要求

- `SKILL.md` 面向未来 Agent，使用精简 Markdown。
- 正文写可执行流程、命令、边界和输出要求。
- 不引用 RuntimeAgent 原生 `skill_load`、`skill_update`，也不要把不存在的 pull 类 Skill 操作写成 `lovrabet` 命令。
- 不把明文凭证、cookie、AK、用户私有路径写入 Skill。
- 不把临时调试记录、变更日志或面向人的安装说明放入 `SKILL.md`。

## 发布后检查

`lovrabet skill push` 成功后，使用下面命令确认本地和云端可见性：

```bash
lovrabet skill list --scope all --format compress
lovrabet skill list --local --scope all --format compress
```

命令失败时报告 CLI 错误和当前 appCode，不声称已保存。
