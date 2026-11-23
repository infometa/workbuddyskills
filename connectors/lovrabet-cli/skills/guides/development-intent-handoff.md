# 开发能力交接

先判断用户是在咨询开发方式、讨论方案，还是请求执行。咨询或方案讨论时，直接回答所问，不因提及开发就启动安装或认证；仅询问影响回答的缺失信息。

用户请求执行 Lovrabet 开发任务时，保留已有需求和上下文，按下文流程交接 rabetbase CLI 内置 Skill（名称为 `rabetbase`，以下简称“rabetbase Skill”），并依据实际能力推进。尊重用户明确的操作方式；需要用户完成某一步时，说明该步骤及后续衔接。不要索要密码或含密码的连接串。

## 1. 按对象和操作判断

| 用户要做什么 | 使用哪项能力 |
| --- | --- |
| 创建 Lovrabet 应用、创建或修改页面、发布应用或页面 | rabetbase CLI 内置 Skill |
| 新增数据集、修改字段与关联结构 | rabetbase CLI 内置 Skill |
| 创建或修改应用级 Backend Function、Custom SQL 定义、菜单结构 | rabetbase CLI 内置 Skill |
| 创建、修改或发布审批流、工作流的流程定义 | rabetbase CLI 内置 Skill |
| 查询、新增或修改业务记录，导入 Excel | lovrabet 的 dataset/data 能力 |
| 执行已有且可信契约绑定的 BFF/SQL | lovrabet 的 bff/sql 能力 |
| 创建、修改或执行 Personal Backend Function | lovrabet 的 personal-bff 能力 |
| 修改角色成员、页面权限或角色菜单权限 | lovrabet 的 role/permit 能力 |
| 查询、批准、拒绝或转交已有审批任务 | lovrabet 的 approval 能力 |
| 管理个人 Skill、个人知识库、定时任务 | lovrabet 的对应运行态能力 |

- 不以“BFF”“SQL”“菜单”“数据集”单个关键词决定切换。“修改菜单”不明确时，先问是菜单结构还是角色可见权限；“修改数据集”不明确时，先问是字段结构还是业务记录。
- 普通网站或本地代码开发不自动视为 Lovrabet 应用开发；上下文不能确定平台或操作对象时，只询问缺失信息。
- 混合任务按实际依赖拆分：例如先执行已绑定 BFF 查询、再增加字段，可先在既有授权内完成查询，再交接结构变更。查询契约不足、认证失败或权限拒绝不构成切换开发身份的理由；不能借交接扩大权限或枚举未绑定实现资产。

## 2. 检查 CLI，缺失时引导安装

先只读探测命令是否存在，再读取 `rabetbase --version`。POSIX shell 可用 `command -v rabetbase`；PowerShell 可用 `Get-Command rabetbase -ErrorAction SilentlyContinue`。

- 命令不存在：说明本任务需要 rabetbase CLI。当前会话没有覆盖安装的明确授权时，询问是否安装；用户拒绝则停止需要该 CLI 的部分，保留原任务上下文。
- 用户同意安装后，使用官方 npm 包：

  ```bash
  npm view @lovrabet/rabetbase-cli@latest version engines --json
  npm install -g @lovrabet/rabetbase-cli@latest
  rabetbase --version
  ```

  先核对本机 `node --version` 是否满足目标包的 `engines`。用户指定精确版本时，将查询与安装的版本同时替换为该版本；不要擅自选择 beta。
- 命令存在但启动失败：先按真实错误处理 Node 版本、执行权限或 PATH，不当作“未安装”直接覆盖。已安装且满足任务能力时直接复用，不强制升级；是否需要升级以目标 Skill、CLI help/schema 的真实能力为准。
- 安装失败：说明实际原因与下一步，例如 Node 不满足要求、npm 写入权限不足、网络或 registry 错误。不要自动使用 sudo、修改 registry 或反复重装。
- npm 安装会提供 Built-in Skill。接着读取当前可用的 rabetbase `SKILL.md` 及本任务需要的 reference；若 Skill 缺失或不一致，使用 `rabetbase cli-skill install` 修复后重新读取。修复失败时报告阻碍，不凭记忆编写研发命令。

## 3. 各自认证，不传递凭证

lovrabet 使用 User Access Key；rabetbase 的开发能力通过浏览器 OAuth 登录。已有 lovrabet AK 不代表已登录 rabetbase，纯开发任务也不要求先取得 lovrabet AK。不要把 AK 传给 rabetbase 登录，不复制 Cookie、Token、环境变量或两者的配置文件。

交接后以 rabetbase Skill 的前置条件与 `references/rabetbase-auth-login.md` 为准：

- 先核对目标国家/地区、独立部署与应用上下文。连接配置由 rabetbase 自己管理；不自动把 `.lovrabet.json` 转成 `.rabetbase.json`，不为了探测就初始化或覆盖项目配置。需要新增或更改配置时按其 Skill 确认作用域。
- 已确认有效的 rabetbase 会话直接复用；未知或过期时，Agent 使用 `rabetbase auth login --yes`。该命令会先检查已有会话，有效时跳过登录。`--yes` 仅跳过 CLI 的本地询问，不代替用户的浏览器授权。
- 命令输出授权链接时，将链接交给用户在自己的浏览器完成授权；Agent 不自行访问，也不索要密码或 Cookie。保持登录命令运行并等待真实结果，不在授权过程中反复启动登录。
- 登录失败、取消或超时后停止依赖认证的操作，给出实际原因及重新登录步骤；不能仅凭退出码为 0 判定成功。只有有效会话或登录成功的明确结果才继续。
- 按目标 Skill 核对目标应用可见性与开发权限；已登录不等于有应用开发权限。权限不足时说明缺少的权限，不更换身份绕过限制。

## 4. 带着原任务继续

向 rabetbase Skill 传递：用户原始目标、已确认的应用标识、目标国家/地区或独立部署信息、已有工作目录、已完成的步骤、剩余操作与授权范围。只传必要信息，不传凭证、整份配置或无关业务数据。

随后按其 Skill 读取能力、执行并验证结果；安装成功或登录成功不等于原任务完成。若后续只需验证真实业务记录，回到 lovrabet 对应能力并单独核对运行态认证与授权，避免两个 CLI 之间反复交接同一步骤。
