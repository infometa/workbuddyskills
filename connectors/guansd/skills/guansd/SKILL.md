---
name: guansd
display_name: 观思动-AI开发部署企业应用
display_name_en: Guansd — AI-built enterprise apps
description: >-
  观思动（guansd）平台连接器：用 guansd 命令行把需求做成公司同事能登录使用的企业应用——建应用、克隆代码、
  写代码、部署开发版、请平台真机验收、发布正式版、看日志、回滚。当用户要「做成一个系统 / 应用 / 后台
  给同事用」——台账、请假/报销/采购审批、巡检/点检、报修/客诉工单、客户/设备/合同管理、库存与到期提醒、
  经营看板——或说 Excel / 在线表格 / 多维表格 / 智能表格 做不下去了、要权限、要审批流转、要自动提醒、
  要推到企业微信，或提到 观思动、guansd、企业应用、内部系统、开发版、正式版、企微登录、功能权限、
  定时任务、部署、发布 时使用。
description_zh: 用 guansd 命令行在观思动平台上建应用、写代码、部署开发版、平台验收、发布正式版
description_en: Build, deploy, verify and publish internal business apps on the Guansd platform with the guansd CLI
version: 1.0.2
author: 观思动
---

# 观思动 · 用 guansd 命令行开发并部署企业应用

> 🔌 **通过 WorkBuddy 连接器使用时，`guansd` 已经装好、版本已检查、用户已登录。** 不要再安装、
> 检查版本或执行 `guansd login`——直接开始干活。命令报「未登录」时，让用户到 WorkBuddy 的连接器中心
> 重新连接「观思动」，不要自己反复登录。

## 平台是什么（30 秒）

- 观思动托管企业内部应用。每个应用 = TypeScript **Fastify** 服务端 + **React** 客户端 + 自己的
  Postgres 数据库；平台负责企业微信登录、组织通讯录、功能权限、文件存储、定时任务、公开回调、
  部署与回滚。你只写业务。
- 两个环境：**开发版**（你部署、你验证）和 **正式版**（同事真正用的）。发布正式版 = 把验收通过的那次
  开发版镜像原样发布。
- 每个应用一个 git 仓库，在 **`work` 分支**上开发。平台文件（`src/_auth/**`、`Dockerfile`、
  `KNOWLEDGE.md`、`_reference/**`、`tools/**`、`AGENTS.md`）由平台维护，本地改动不会生效。
- 应用级命令（deploy / logs / verify / promote …）**必须在 `guansd clone` 出来的目录里运行**
  （或加 `--app org/slug`）；账户级命令（apps / create / clone / whoami）在哪都行。

## 标准流程

1. **看清情况**：`guansd whoami`（我是谁、管几个应用）→ `guansd apps`（名下应用：正式版在跑哪一版、
   开发版最近一次部署怎么样、哪些功能还待授权）。
2. **拿到代码**
   - 新应用：`guansd create <应用名称>`（中文名即可，用户成为负责人）。它会打印下一步
     `guansd clone <org/slug>`；仓库和数据库在后台准备约半分钟，`clone` 会自己等。
   - 已有应用：`guansd clone <org/slug> [目录名]`。凭证自动签发，不再开浏览器。
3. **进目录后先读 `AGENTS.md`**——这个仓库的开发合同：目录结构、可用的平台模块（登录、通讯录、
   功能权限、文件、定时任务、连接器）、部署门禁。再看
   `git log --format='%h %ad %s' --date=short -20`：每条提交主题都是业主提过的需求原话，
   它是这个应用的需求史，不是技术变更日志。
4. **改代码**。想在本机看效果：`node tools/local-up.mjs run`（需要 Docker；打印带登录态的本地链接，
   用的是合成账号，碰不到真实数据）。没有 Docker 就直接走开发版。
   - 在 WorkBuddy 里 `npm install` / `npm test` 若报 `CODEBUDDY_BROKER_DENY`，那是 WorkBuddy 的沙箱拒绝
     npm 在工作区外建目录（通常是 `~/.npm` 缓存），**不是平台问题**——按 WorkBuddy 的方式在沙箱外重跑这一条
     命令即可，别反复重试（一次失败要等 3 分钟）。
   - 本机已有别的观思动应用在跑本地库时，`docker-compose.dev.yml` 映射的 54329 端口会冲突：只在本机临时改
     端口（连同 `TEST_DATABASE_URL`），**不要提交**——它是平台文件，提交了也不会生效。
5. **提交并推送**：`git add -A && git commit -m "<用用户的原话描述这次改动>" && git push origin work`。
6. **预检 → 部署开发版**：`npm run preflight`（本地 ~1 秒，部署的同一套门禁）→ `guansd check`
   （服务端在已推送的代码上再跑一遍，这个结论才算数）→ `guansd deploy`（跟踪到 healthy / failed）。
   failed 先读 **failureReason**，再 `guansd logs` 看构建日志。
7. **交付开发版**：`guansd deploy` 成功时最后一行就是开发版网址；要程序化拿网址用 `guansd whoami --json`
   里的 `urls.dev` / `urls.prod`；`guansd open` 在本机浏览器打开。
   `guansd runtime` 还会报 **密钥没配 / 功能权限没授权**——这两件事只能业主在控制台做，原话转告用户。
8. **验收**：`guansd verify "<主流程，用用户的话说>"`，平台的验收 AI 会在真浏览器里实际操作开发版的
   **一次性隔离副本**——开发版的真实数据不会被它改动，验收完副本即销毁。所以验收通过后打开开发版仍是空的，
   这是正常的，交付时要向用户说清楚。命令会阻塞到结束（一般 1–4 分钟）；它开头打印的验证 id 要记下来，
   shell 有超时或被中断时用 `guansd verify --status <id> --wait` 接着等——验证本身不会因为终端断开而停。
   只有 **ok** 才能发布；「只看了一眼没操作」（observed-only）不算。
9. **发布正式版**：`guansd promote`（发布的是验收通过的那次开发版；202 后自动跟踪到 healthy）。
   发布后把输出里「仍待授权的功能」列表原样告诉用户——那些功能在业主授权前对所有人都是 403。
10. **出了问题**：`guansd history` 看版本，`guansd rollback <deployId>` 回滚正式版（不需要验收）；
    `guansd logs --env prod --since 3600` 看正式版最近一小时日志。

## 铁律

- **应用级命令只在应用目录里跑**。不在目录里会报「当前目录不是应用的本地副本」——`cd` 进去或加 `--app`。
- **部署构建的永远是已推送的 `work` 分支**。本地有未推送的提交时 `guansd deploy` 会拒绝——先 push。
- **一个应用同一时间只有一个写者**。控制台里正在跑的对话任务会占住应用（`occupiedBy`），此时 push 和
  deploy 都返回 409。**等它结束，或让用户去控制台处理**，不要循环重试。
- **发布正式版必须先 verify ok**，而且是针对当前这次开发版部署的——重新 `deploy` 之后要重新 `verify`。
  业主在控制台关掉了「允许本地开发操作正式版」时，promote / rollback / 正式版日志一律 403：问业主，不要重试。
- **别碰平台文件**（上面那一列）。`npm run preflight` 里 `auth-integrity` 红了，就是改到了平台文件。
- **数据是客户的**。`guansd` 不提供查库命令；要看开发版数据，按 `AGENTS.md` 里的 `db/query` 接口
  只读 SELECT（`guansd token` 打印当前凭证给 curl 用），结果不进代码、不进提交、不进日志。
  正式版数据永远只能在控制台看。
- **密钥只声明名字**。第三方 API key 之类在 `guansd.yaml` 里声明名称，值由业主在控制台填；
  永远不要把密钥写进代码、提交或对话。
- **需要外部系统（ERP / 企微 / 飞书 / 大模型 / 地图 …）时**，用 `AGENTS.md` 说明的连接器目录里的
  参考接口，不要凭记忆或网上搜索去猜字段。

## 常见报错 → 该做什么

| 现象 | 含义 | 动作 |
|---|---|---|
| `未登录 — 运行 guansd login` | 连接器的登录态丢了 | 让用户在 WorkBuddy 连接器中心重新连接观思动 |
| `需要该应用的负责人（或团队管理员）身份` | 用户不是这个应用的负责人 | 让用户找该应用负责人在控制台把他加为负责人；自己 `create` 的应用不会遇到 |
| `⛔ …占用着这个应用` / HTTP 409 | 控制台里有对话任务在跑 | 等它结束；或让用户到控制台的应用对话里回答 / 取消它 |
| `本地比远端多 N 个未推送的提交` | deploy 只构建已推送的代码 | `git push origin work` 后再 deploy |
| deploy `failed` + failureReason | 门禁 / 构建 / 迁移 / 健康检查失败 | 按 failureReason 修；`guansd logs` 看构建日志；`guansd check` 复查 |
| `secret_unset` | 声明的密钥业主还没填 | 转告业主：控制台 → 应用设置 → 密钥 |
| verify `blocked` / `observed-only` | 验收 AI 进不去，或只看没操作 | 读报告，通常是登录、权限或空数据问题；修完重新 verify |
| promote 409 `verify_required` | 没有针对当前开发版的 ok 验收 | 先 `guansd verify` |
| 正式版操作 403 | 业主关了「允许本地开发操作正式版」 | 告诉用户，由负责人在控制台开启或代为发布 |
| `本机 CLI 版本过旧` | guansd 需要升级 | 让用户在连接器中心重新连接（会自动升级），或 `npm i -g guansd@latest` |
| `npm install` 报 `CODEBUDDY_BROKER_DENY` | WorkBuddy 沙箱拒绝了工作区外的写入（npm 缓存） | 在沙箱外重跑这一条 npm 命令（WorkBuddy 会征求用户许可）；不是平台问题 |
| `docker compose up` 报 54329 端口被占 | 本机另一个观思动应用的本地库在跑 | 本机临时改端口和 `TEST_DATABASE_URL`，不提交 |
| 验收 ok 但开发版页面是空的 | 验收跑在一次性隔离副本上 | 正常；告诉用户开发版数据要自己录入或导入 |

## 命令速查

全部命令、参数与含义见 `references/cli-verbs.md`。任何命令后加 `--help` 看参数；查看类命令支持
`--json`（原样输出接口返回，给脚本用）。

## 更多能力

定时任务试跑、公开回调试投、第三方接口（连接器）参考、只读查库：在应用目录里按 `AGENTS.md` 的说明走
MCP 工具或 curl（`guansd token` 打印当前应用的凭证）。平台使用说明：https://guansd.cn/docs/ ，
命令行一页：https://guansd.cn/docs/local-dev/cli 。
