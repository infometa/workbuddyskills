# WorkBuddy 上架自检清单

规范基线：WorkBuddy 专家开发规范 v2.4（2026-07-31）。

## 文件结构

- [x] `.codebuddy-plugin/plugin.json` 已存在且为合法 JSON
- [x] `agents/ihr-ai-interviewer.md` 已存在
- [x] `avatars/expert.png` 路径已在配置中声明
- [x] `skills/` 精确包含 `ihr-bootstrap`、`ihr-shared`、`ihr-base` 和 `ihr-conference`
- [x] 每个 Skill 根目录均包含 `SKILL.md`
- [x] 包内不含 runtime requirements、runtime manifest 或 CLI 二进制
- [x] 专家包不包含 `install.sh`、`install.ps1` 或其他 installer
- [x] 未使用 `hooks/`、`commands/`、`.lsp.json`
- [x] 已提供 `README.md`

## plugin.json

- [x] `name` 使用小写字母和连字符
- [x] `version` 使用语义化版本号
- [x] `description` 为英文技术描述
- [x] `author` 包含名称和邮箱
- [x] `agents` 为路径数组且文件存在
- [x] `skills` 与 Agent frontmatter、最终目录和 ZIP inventory 完全一致
- [x] `expertType` 为 `agent`
- [x] `agentName`、Agent 文件名和 frontmatter `name` 一致
- [x] 中英文 `displayName`、`profession`、`displayDescription` 完整
- [x] `categoryId` 为 `09-OperationsHR`
- [x] `plugin` 与 `name` 一致
- [x] 标签数量为 3，且均有中英文
- [x] 推荐提示词数量为 3，且均有中英文

## Agent 定义

- [x] frontmatter 不含 `tools` 字段
- [x] 已定义角色、核心能力、SOP、输出规范和边界限制
- [x] `## iHR CLI 运行参数` 只定义 `RUNTIME_ENV`、`CHANNEL`、`MINIMUM_CLI_VERSION`、`LOGIN_SOURCE`
- [x] `MINIMUM_CLI_VERSION` 只作为专家文档软版本基线，不作为启动、安装、授权或业务硬门禁
- [x] CLI 缺失、用户主动安装/更新/登录和一次鉴权恢复委托 `ihr-bootstrap`
- [x] 已有 CLI 不因版本或 channel 不匹配自动更新、切换或降级
- [x] Bootstrap 使用宿主托管 Node.js/npm runtime 的 channel tag 只安装 CLI，不传固定版本
- [x] 安装、授权、业务严格分阶段；明确业务请求在安装成功后自动进入授权，不询问“是否继续授权”，授权未完成时不执行业务
- [x] 每会话首次业务直接执行正式命令；不预执行 `auth status`、`version`、Node/npm 或 PATH 检查
- [x] 业务命令不统一追加 `--expected-env`
- [x] `CREDENTIAL_MISSING`、`AUTH_EXPIRED`、`ENVIRONMENT_MISMATCH` 走普通登录
- [x] 真实结构化 `AUTH_REQUIRED`/401 或用户主动重新登录最多触发一次强制重授权
- [x] HTTP 403、网络错误、429、5xx 不触发登录
- [x] 只更新 CLI 不提示重启；专家包内置 Skills 变化时只软提示重启 WorkBuddy，不探测热加载
- [x] Windows 安装只使用当前原生 PowerShell 5.1+，禁止命令字符串、`Invoke-Expression`、`powershell.exe -File`、`Start-Process` 或第二个 Shell
- [x] 已区分模板创建、面试发起等真实副作用
- [x] 已明确内部人员 ID 不可猜测
- [x] 已明确数字人模板 `templateId` 只作为 `interviewCode`
- [x] 已明确不使用 raw API 或后端内部角色码
- [x] 引流文案已移除（v2 不再配置）

## 构建溯源

- [x] `BUILD-INFO.json` 使用 schema v2
- [x] 记录 docs commit、`ihr-cli` commit、runtime env、channel 和 `MINIMUM_CLI_VERSION`
- [x] 记录四个 Skill 的 inventory 与 SHA-256
- [x] 记录 npm 包、stable/beta tag 和 Node.js 18+ runtime 策略
- [x] 最低版本来源固定为 `latest.json` 或 `latest-beta.json`
- [x] 最终 ZIP 已复核 plugin、Agent 参数、Skills inventory 和禁止制品

## 头像

- [ ] 最终人工确认画面符合品牌与市场展示要求
- [x] 文件格式为 PNG
- [x] 尺寸为 512 × 512 px
- [x] 文件大小不超过 500KB

## 提交前人工确认

- [x] 作者名称已确认为“利唐智语团队”
- [x] 联系邮箱已确认为 `olivia.zhang@ihr360.com`
- [x] 默认环境已确认为 `work100-prod`
- [ ] 在目标 WorkBuddy 环境试运行三个推荐提示词
- [ ] 人工确认打包固定的 `ihr-cli` commit 中 Domain Skills 与 latest pointer 的 CLI 版本兼容
- [ ] 在 Windows PowerShell 5.1 与 7 上验证宿主托管 Node/npm 的 CLI 首次安装与更新
- [ ] 验证 CLI 缺失时由宿主 npm runtime 直接安装，并在安装成功后直接进入 `auth ensure`
- [ ] 验证授权链接逐事件展示、同一 Session 恢复和授权完成后独立开始业务阶段
- [ ] 安装新专家包后确认已向用户软提示建议重启 WorkBuddy
