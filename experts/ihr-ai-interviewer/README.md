# i人事-利唐智语AI面试官

围绕岗位画像设计面试维度与题库，管理数字人面试模板，校验候选人信息并发起面试，回查面试记录与纪要。

## 专家信息

| 项目 | 内容 |
|---|---|
| 类型 | Agent 型专家 |
| 技术标识 | `ihr-ai-interviewer` |
| 中文名称 | AI面试官 |
| 英文名称 | AI Interviewer |
| 中文职业 | i人事-利唐智语AI面试官 |
| 英文职业 | iHR-LiTangZhiYu AI Interviewer |
| 作者 | 利唐智语团队 |
| 联系邮箱 | olivia.zhang@ihr360.com |
| 行业分类 | `09-OperationsHR` 运营人力 |
| 版本 | 2.0.0 |
| 规范基线 | WorkBuddy 专家开发规范 v2.4（2026-07-31） |

## 核心功能

1. 根据岗位职责、招聘类型、面试轮次和候选人层级设计结构化面试方案。
2. 搜索并复用已发布的数字人面试模板。
3. 在用户明确授权后，dry-run 校验并创建发布新的数字人面试模板。
4. 校验唯一候选人的身份与联系方式，安排和发起数字人面试。
5. 搜索历史面试，按权限读取纪要、摘要、待办和完整转写。

## 最终打包目录结构

```text
ihr-ai-interviewer/
├── .codebuddy-plugin/
│   └── plugin.json
├── agents/
│   └── ihr-ai-interviewer.md
├── avatars/
│   └── expert.png
├── skills/
│   ├── ihr-bootstrap/
│   │   └── SKILL.md
│   ├── ihr-shared/
│   ├── ihr-base/
│   └── ihr-conference/
├── BUILD-INFO.json
├── README.md
└── SUBMISSION_CHECKLIST.md
```

最终目录和 ZIP 的 `skills/` 精确包含 `ihr-bootstrap`、`ihr-shared`、`ihr-base` 和 `ihr-conference`，保证专家首次加载即有必需 Skills。Bootstrap 来自专家项目，其他 Skills 来自打包时固定的 `ihr-cli` commit。npm 主路径只安装当前平台 CLI，不安装 Skills；专家包不包含 CLI 二进制、installer、runtime requirements 或 runtime manifest。Node/npm 不可用时由宿主返回通用运行时前置条件错误并停止。

## 推荐使用方式

- 给 [候选人姓名]（[邮箱/手机号]）发起一场 [岗位名称] 的数字人面试，要求在 2 天内完成。
- 请帮我给 [候选人姓名]（[邮箱/手机号]）配置一场 [岗位名称] 的数字人面试，重点考察 [如：项目管理/沟通能力]，要求24小时内完成，并生成面试邀请
- 请帮我给候选人 [姓名]（[邮箱/手机号]）配置一场 [岗位名称] 的数字人面试。6道题左右，重点考察 [如：项目管理/沟通能力]，通知候选人在 [如：24小时内] 完成，并自动生成面试邀请通知短信。

## 运行依赖

- `ihr-cli`
- 默认运行环境：`work100-prod`（已确认）
- 登录来源：`workbuddy-ihr-ai-interviewer`
- Agent 主文件是唯一运行参数来源，只定义 `RUNTIME_ENV`、`CHANNEL`、`MINIMUM_CLI_VERSION` 和 `LOGIN_SOURCE`。本会话首次需要业务能力时直接执行正式业务命令，不预执行 `auth status`、`version`、Node/npm 或 PATH 检查。CLI 缺失才进入 Bootstrap；Bootstrap 使用宿主托管的 Node.js/npm runtime 通过 npm channel tag 直接安装最新 CLI，不安装 Skills。若原始请求已有明确业务意图，安装成功后直接进入授权，不重复执行 `auth status` 或 `version`，不询问“是否继续授权”；授权未完成时提示用户完成授权后回复“已授权”，当前响应不执行面试业务。版本基线只在用户明确询问版本或要求更新时软提示。npm 不可用或安装失败时返回通用运行时前置条件错误并停止。单独安装/更新请求不创建授权 Session。安装、授权和业务严格分阶段。只更新 CLI 不提示重启；专家包或内置 Skills 变化时只软提示重启 WorkBuddy。

## 头像

头像位于 `avatars/expert.png`。如需替换，请保持：

- PNG 或 JPG
- 512 × 512 px
- 单张不超过 500KB
- 专业、自然、无侵权或违规元素

## 打包提交

在 `docs` 仓库根目录执行：

```bash
./scripts/package_work100_ai_interviewer_prod.sh
```

脚本会使用专家项目自己的 canonical `ihr-bootstrap`，从固定 `ihr-cli` commit 复制 allowlist Skills，从 `latest.json` 获取专家软提示最低版本，渲染 Agent 主文件四个运行参数，并把源码 commit、channel、runtime env、最低版本、Skill hashes 和 npm runtime 策略写入 `BUILD-INFO.json`。打包器会校验 plugin/frontmatter/ZIP inventory 一致，并拒绝 runtime requirements、runtime manifest、CLI 二进制或 installer。提交前请按 `SUBMISSION_CHECKLIST.md` 完成自检。
