# skill install / create / validate / list / push

安装当前应用业务 Skill，创建本地运行态 Skill 草稿，检查必要元数据，查看云端或本地 CLI 管理的 Skill 列表，并将本地个人 Skill 改动推回平台。

## 创建本地草稿

```bash
lovrabet skill create --name invoice-review --type write
lovrabet skill create --name customer-summary --type read --target ./skills
lovrabet skill create --name invoice-review --type write --dry-run
```

`create` 只写本地文件，不需要 AK、不需要 appcode、不上传、不发布、不写业务数据。默认生成：

```text
.agents/skills/<skill-name>/
  SKILL.md
  references/runtime-contract.md
  references/output-contract.md
```

生成的草稿带有 `【...】` 占位符。Agent 必须根据业务目标显式传入 `--type read|write`；无法判断是否存在业务副作用时停止并请求澄清。frontmatter `name` 是稳定 `skillCode`，`displayName` 根据用户实际展示诉求填写人类可读名称，`description` 应写模型触发语义，说明何时使用、不要使用的边界和关键词。CLI 会检查 `SKILL.md` 与 frontmatter 必要字段；缺少顶层 `displayName` 会 warning，但正文、章节、references、占位符和输出协议不参与 CLI validate 或 push 阻断。

## 必要元数据检查

```bash
lovrabet skill validate --dir .agents/skills/invoice-review
lovrabet skill validate --dir .agents/skills/invoice-review --strict
```

`validate` 只检查本地目录是否具备上传和识别所需的最小信息。`--strict` 为兼容保留，不启用额外检查。

检查项：

- 根目录存在普通文件 `SKILL.md`。
- `SKILL.md` 以 frontmatter 开头。
- frontmatter 中 `name`、`description` 非空。
- `metadata.type` 可选；若填写，必须是 `write` 或 `read`。

正文内容、章节名称、`references/*`、占位符、输出协议、明文凭证和外部链接不参与 CLI validate。

## 查看列表

```bash
lovrabet skill list
lovrabet skill list --scope personal
lovrabet skill list --scope company
lovrabet skill list --scope all
lovrabet skill list --code sales_playbook
lovrabet skill list --local
lovrabet skill list --local --scope all
lovrabet skill list --local --project
```

默认等价于 `--scope all`，查询 SkillHub-backed 云端 personal 和 company 业务 Skill，不安装、不下载内容。Builtin Skill 由 sandbox 镜像内置提供，不通过远端 `skill list` 查询。

`--local` 只读取当前 env、AK、App 下 CLI 管理的本地 cache 与用户级链接，依赖 `lovrabet.skill.json` 识别元数据；它不请求云端、不下载 package、不物化文件，也不清理旧目录。查看当前项目链接时使用 `skill list --local --project`。需要查看本地是否已经安装时用 `lovrabet skill list --local`，需要看云端是否存在时用不带 `--local` 的 `lovrabet skill list`。

## 安装业务 Skill

```bash
lovrabet skill install
lovrabet skill install --scope all
lovrabet skill install --scope personal
lovrabet skill install --scope company
lovrabet skill install --code sales_playbook
lovrabet skill install --project
```

默认等价于 `--scope all`，安装当前 App 下当前 AK 可见的 `personal` 和 `company` 业务 Skill，不安装 `builtin`。有效链接默认写入用户级 Agent Skill 目录；只有用户明确要求绑定当前项目时才添加 `--project`。

安装过程会使用当前环境和 AK 指纹隔离的 CLI 管理缓存：

```text
~/.lovrabet/cache/<env>/<ak_fingerprint>/skills/<appCode>/<scope>/<skillCode>/
  SKILL.md
  lovrabet.skill.json
```

- `SKILL.md` 是本地 Agent 可直接发现的入口文件；后端 Skill `content` 缺少 YAML frontmatter 时，CLI 会根据 Skill 元数据补齐 `name`、`displayName` 和 `description`；已有 frontmatter 时会同步顶层 `displayName`，但不改写 `name`；即使展示名等于 `skillCode`，也会显式写入 `displayName`
- `lovrabet.skill.json` 保存 `appCode`、`skillCode`、`scope`、版本、标签、content hash 等 Lovrabet 元数据；展示名以 `SKILL.md` 顶层 `displayName` 为可编辑入口
- 同名 `skillCode` 的 personal 和 company 副本都会保留，effective 链接优先 personal
- 完整 `skill install` 会移除当前 App 下远端已删除 Skill 对应的 CLI 管理链接和当前 AK 缓存目录；`--code <skillCode>` 只同步和清理指定 code

## 本地链接

默认用户级有效 Skill 会链接到：

```text
~/.agents/skills/<appCode>--<skillCode>
~/.claude/skills/<appCode>--<skillCode>
```

显式执行 `lovrabet skill install --project` 时，项目级链接不重复携带 appCode：

```text
<cwd>/.agents/skills/<skillCode>
```

personal 与 company 同名时 personal 优先；只有 company 时链接 company。用户级与项目级安装可以共存，CLI 只在本次选择的链接目标中替换或移除指向 `~/.lovrabet` cache 且 metadata 归属当前 App/code 的已管理 symlink，不覆盖或删除普通文件、目录、外部 symlink 或其他 App 的链接。显式项目安装清理缓存时，会保留已有用户级链接仍在引用的目录；项目安装也会拒绝覆盖 `lovrabet`、`runtime-observe`、`secret-retriever` 等平台保留 Skill 名称。

## 推送

```bash
lovrabet skill push --dir ~/.lovrabet/cache/production/<ak_fingerprint>/skills/app-1/personal/sales_playbook --diagram-file ./sales-playbook.mmd
lovrabet skill push --dir ./app-1--sales_playbook --diagram-file ./sales-playbook.mmd
```

`push` 读取目录下的 `SKILL.md`。frontmatter `name` 继续用于推导稳定 `skillCode`；顶层 `displayName` 会作为远端展示名提交到 SkillHub。没有 `displayName` 时，CLI 才回退使用 `lovrabet.skill.json` 中的名称。没有元数据时从目录名推导 `skillCode`，并去掉当前 App 的 `<appCode>--` 前缀。上传前会用该 `skillCode` 在当前 App namespace 下精确查询远端 Skill，命中时先把远端 scope、版本、状态、名称和描述写回 `lovrabet.skill.json`，再重新读取本地目录进入上传逻辑。

`push` 默认创建或更新 personal Skill。发布新 SkillVersion 时 `--diagram-file` 必填；文件内容是 Agent 根据本次 Skill 源码直接编写、且语法正确的原始 Mermaid flowchart，也可传 `--diagram-file -` 从标准输入读取。文件可位于 Skill 目录内或外；CLI 不把流程图加入 Skill 包、本地元数据或安装目录，而是与 Skill 包在同一个发布请求中提交。位于 Skill 目录内时，只有 `--diagram-file` 选中的规范化真实路径会从包扫描中排除，其他 `.mmd` 文件仍按普通包文件处理。SkillHub 必须明确确认图已校验、已绑定；缺少回执的旧服务会被视为不支持联合发布。流程图缺失、Mermaid 语法错误或服务端拒绝时，整个 push 失败，不先发布无图版本。若远端刷新后的元数据 scope 是 `company`，默认 personal push 会在上传前失败，并提示使用公司级 push 工作流。Builtin Skill 不能 push，也不能通过 company scope 提交审核。

## 公司级发布

```bash
lovrabet skill push --scope company --dir .agents/skills/sales-playbook --diagram-file ./sales-playbook.mmd --dry-run
lovrabet skill push --scope company --dir .agents/skills/sales-playbook --diagram-file ./sales-playbook.mmd --confirm-warnings
```

`push --scope company` 读取本地 Skill 目录与流程图并向 SkillHub 提交公司级新版本审核。`--dry-run` 会同时校验 Skill 包和 Mermaid，不创建版本或审核任务；正式提交使用 `visibility=NAMESPACE_ONLY`，两者必须一起成功，成功后版本进入审核，不代表已经成为 effective Skill。审核通过并需要本机 Agent 使用时，再运行 `lovrabet skill install` 安装已生效版本。

## 精确版本流程图维护

正常创建或更新源码版本时始终使用带 `--diagram-file` 的 `skill push`。只有为历史版本补图或修正已发布版本的图时，才使用独立命令：

```bash
lovrabet skill diagram-show --skill-code <skillCode> --version <version> --scope personal|company --format compress
lovrabet skill diagram-validate --skill-code <skillCode> --version <version> --scope personal|company --source-fingerprint <sha256> --expected-diagram-revision <revision> --diagram-file <mermaid-file> --format compress
lovrabet skill diagram-push --skill-code <skillCode> --version <version> --scope personal|company --source-fingerprint <sha256> --expected-diagram-revision <revision> --diagram-file <mermaid-file> --format compress
```

每次独立维护都先运行 `diagram-show`，只复制该次输出中的服务端 canonical `sourceFingerprint` 和 `expectedDiagramRevision`，不要自行计算 fingerprint、猜 revision 或复用旧读结果。已有图时 `expectedDiagramRevision` 等于当前 `diagramRevision`；`found=false` 表示该精确版本当前无图，但响应仍必须带该版本的 `sourceFingerprint`，并给出 `diagramRevision=null`、`expectedDiagramRevision=0` 供首次写入。若响应缺少 fingerprint，CLI 会按服务能力不完整失败，不能把它解释为无图。先 validate，再用完全相同的目标、fingerprint、revision 和 Mermaid 执行 push。revision 或 source fingerprint 冲突时重新读取并核对，不使用强制覆盖；认证、权限、网络或服务端错误同样不能解释为无图。

## 与 RuntimeAgent 原生 Skill 工具的关系

CLI 的 Skill 能力是目录同步：

- `skill install`：把当前应用下当前 AK 可见的 personal/company Skill 默认安装到用户级目录；`--project` 才安装到当前项目 `.agents/skills`。
- `skill create --name <name> --type read|write`：生成本地自包含 Skill 草稿，不上传。
- `skill validate --dir <dir>`：检查 Skill 必要元数据。
- `skill list`：查看云端 Skill 列表；`--local` 查看 CLI 管理的本地 cache 和链接。
- `skill push --dir <dir> --diagram-file <mermaid-file>`：检查必要上传信息和流程图后创建或更新 personal SkillVersion。
- `skill push --scope company --dir <dir> --diagram-file <mermaid-file>`：检查本地目录和流程图后提交 company Skill 新版本审核。
- `skill diagram-validate/diagram-push/diagram-show`：维护一个精确历史 SkillVersion 的流程图，不替代正常联合发布。

RuntimeAgent 原生的 `skill_load`、`skill_update` 等工具是 Agent 服务内部的资源读写能力，不是 `lovrabet` CLI 命令。写命令步骤时不要把这些原生工具当作 CLI 子命令，也不要要求 coworker 直接调用它们。
