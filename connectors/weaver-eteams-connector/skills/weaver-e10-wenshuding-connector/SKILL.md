---
name: weaver-e10-wenshuding-connector
display_name: 泛微E10文书定档案管理
display_name_en: Weaver E10 Wenshuding
description: "泛微 E10 文书定档案管理：全宗与预归档库、全文检索、档案基本信息、借阅车、借阅单、原文下载、发起借阅/续借流程页与预归档上传确认链。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微 E10 文书定档案管理。支持查询全宗与预归档电子文件库、全文检索可借档案、查看档案基本信息、查看借阅车并直接加入档案（免确认写操作）、查看借阅单与详情、下载借阅单原文 zip，并通过 prepare/apply 确认链处理发起借阅、续借和预归档上传。全宗信息仅在预归档上传时需要查询；借阅相关流程页面默认用系统默认浏览器打开。全文检索结果的默认返回显示样式为三段式卡片视图（标题可点击、命中词高亮、全宗/分类/日期摘要行）。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Weaver E10 Wenshuding archive skill for fonds and pre-archive libraries, full-text search, archive info, borrow car, borrow orders, original file packaging and download, borrow/renew workflow URL generation, and confirmed pre-archive upload. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.4
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
  - weaver-e10-shared-connector
cliHelp: "weaver-work-cli archive --help"
---

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

认证和登录态只能按共享规则通过 `weaver-work-cli auth ...` 命令判断；禁止直接读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。

### 登录与请求头凭证契约

本 Skill 是 CLI 型技能，不自行发起 HTTP 请求：认证与会话**统一由连接器托管**（即 `weaver-work-cli auth ...`），禁止自建或绕过登录流程。CLI 调用 E10 接口时按契约注入以下三项用户信息，**缺一不可**：

接口请求头（由 CLI 注入，Agent 不手写）：

```text
Cookie: <登录返回的完整原始 Cookie 串>   # 禁止裁剪、去重或改写
eteamsid: <登录返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

| 凭证 | 取值与要求 |
| --- | --- |
| `Cookie` | 登录返回的**完整原始 Cookie 串**，禁止裁剪、去重或改写 |
| `eteamsid` | 登录返回的 `ETEAMSID` |
| `User-Agent` | `AgentType=<agentType>,IsAgent=true` |

Agent 不得自行拼接、改写或向用户索取上述凭证（禁止要求用户贴 Cookie / ETEAMSID / token），也不得直接 `curl` / `fetch` E10 接口。
所有命令通过 `weaver-work-cli --profile eteams --json archive run <operation>` 执行：简单 JSON 优先传 `--input-json '<json>'`，复杂或多行 JSON 先写入 UTF-8 文件再传 `--input <path>`，只有确认当前 shell 能稳定传管道时才使用 `--input -`。调用前先按需读取 references 下对应的文件，查参数结构，不要猜字段；**references 是第一信息源**，`weaver-work-cli archive schema` 是 operation、字段和风险等级的合约来源。
命令示例、提示词和临时说明必须同时兼容 Windows 和 macOS/Linux；涉及 JSON 输入、用户目录、路径分隔符、Python 启动器、文件删除、目录查看或文件比对时，同时给 Windows PowerShell 与 macOS/Linux（bash/zsh）两套示例。Agent 先根据当前系统和 shell 选择对应示例，不确定时用 `node -p "process.platform"` 判断。Windows/PowerShell 下不要使用 `printf`、`$HOME/...`、`~/...`、bash 反斜杠续行、`rm/ls/diff/python3` 等 Unix-only 写法。
涉及档案附件、图片、本地文件、借阅原文 zip 或文件上传的操作，执行前必须提醒用户：文件内容可能被上传到 E10 文书定档案系统、文件服务器或下载到本地磁盘，并可能进入当前大模型上下文用于理解和处理；必须等待用户明确确认后才继续。

# 泛微E10文书定档案管理

## 认证与请求头契约

登录与会话由 E10 登录能力统一提供：文档型约定为 `weaver-e10-login` 技能；连接器场景下由连接器完成授权（`weaver-work-cli auth login`），业务命令统一通过 `--profile eteams` 读取该登录态。业务 Skill 不自建登录流程，不索取、打印或转存任何凭证。

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，**缺一不可**（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 路由优先级（先判断是不是文书定档案，再选 operation）

文书定档案不是通用 E10 对象。**只要用户的核心对象是档案、全宗、借阅车、借阅单、档案借阅/续借或预归档上传，就优先使用 `weaver-e10-wenshuding-connector`。**

### 明确归 `weaver-e10-wenshuding-connector` 的高优先级语义

出现以下任一语义时，优先走本 Skill：

- 文书定 / 档案 / 全宗 / 收集库 / 管理库 / 预归档库 / 电子文件库
- 档案检索 / 全文检索 / 可借档案 / 档号 / 案卷 / 保管期限 / 密级 / 库位
- 借阅车 / 加入借阅车 / 我的借阅车
- 借阅单 / 我的借阅 / 借阅记录 / 续借 / 归还期限
- 档案下载 / 原文下载 / 借阅单打包 / 水印件
- 发起借阅 / 借阅申请 / 借阅流程
- 预归档上传 / 电子文件上传 / 归档入库

**判定规则：** 只要最终动作是对文书定档案做查询、检索、加入借阅车、查看借阅单、下载原文、发起借阅/续借或预归档上传，就归 `weaver-e10-wenshuding-connector`。只有当用户处理的是非档案类 E10 业务、通用工作流或尚未封装的档案能力时，才不使用本 Skill。

## 选哪个命令

| 想做什么 | 命令 | 按需读取 reference |
|---|---|---|
| 查看可用 operation、字段和风险等级 | `archive schema` | [`archive-agent-entry.md`](references/archive-agent-entry.md) |
| 查询全宗 / 预归档电子文件库节点 | `archive run archive.fonds.list` / `archive.prelib.tree` | [`archive-fonds.md`](references/archive-fonds.md) |
| 全文检索可借档案（默认卡片视图展示） | `archive run archive.search.run` | [`archive-search.md`](references/archive-search.md) |
| 查看档案基本信息 | `archive run archive.info.get` | [`archive-info.md`](references/archive-info.md) |
| 查看借阅车 | `archive run archive.borrow-car.list` | [`archive-borrow-car.md`](references/archive-borrow-car.md) |
| 加入借阅车（免确认） | `archive run archive.borrow-car.add` | [`archive-borrow-car.md`](references/archive-borrow-car.md) |
| 查看借阅单 / 详情 | `archive run archive.borrow-list.list` / `.detail` | [`archive-borrow-list.md`](references/archive-borrow-list.md) |
| 下载借阅单原文 | `archive run archive.borrow-list.download.prepare/apply` | [`archive-download.md`](references/archive-download.md) |
| 从借阅车发起借阅 | `archive run archive.flow.borrow-car.prepare/apply` | [`archive-flow.md`](references/archive-flow.md) |
| 从检索结果发起借阅 | `archive run archive.flow.search.prepare/apply` | [`archive-flow.md`](references/archive-flow.md) |
| 借阅单续借 | `archive run archive.flow.renew.prepare/apply` | [`archive-flow.md`](references/archive-flow.md) |
| 上传到预归档电子文件库 | `archive run archive.upload.prelib.prepare/apply` | [`archive-upload.md`](references/archive-upload.md) |
| 借阅提交、借阅车移除、归还/催还等未暴露能力 | 无可用命令 | [`archive-disabled-capabilities.md`](references/archive-disabled-capabilities.md) |

处理链：

- 检索并借阅：`archive.search.run` -> 用户选择条目 -> `archive.borrow-car.add`（免确认直接加入）-> 需要时 `archive.borrow-car.list` 复核
- 从借阅车发起借阅：`archive.borrow-car.list` 取 `arcDangan` 与 `dataId` -> `archive.flow.borrow-car.prepare` -> 用户确认 -> `.apply` -> 用系统默认浏览器打开返回的流程创建页 URL（仅用户强调内置打开时用 IDE 内置视图）
- 从检索结果直接发起借阅：`archive.search.run` 取 `id`+`formId` -> `archive.flow.search.prepare` -> 用户确认 -> `.apply` -> 同上默认系统浏览器打开 URL
- 续借：`archive.borrow-list.list` 取 `dataId` -> `archive.flow.renew.prepare` -> 用户确认 -> `.apply` -> 同上默认系统浏览器打开 URL
- 下载原文：`archive.borrow-list.list` 取 `dataId` -> `archive.borrow-list.download.prepare`（校验未超期且有可下载原文）-> 用户确认 -> `.apply`（轮询打包并落盘）
- 预归档上传：`archive.fonds.list` 取全宗 `id` -> 需要时 `archive.prelib.tree` 取 `treeId` -> `archive.upload.prelib.prepare` -> 用户确认 -> `.apply`

## 执行原则（减少误路由、误重试和无效消耗）

### 1) 先拿最小必要信息，再执行

- 只是查列表时，优先直接用 `archive.borrow-car.list` / `archive.borrow-list.list`，默认小页（`pageSize=10`）
- 用户没有要求全量时不要自动翻完整列表
- 用户已给出 `dataId` 时，不要先查列表再过滤，直接用 `archive.borrow-list.detail` 或对应 prepare
- 全宗 `id` 与电子文件库 `treeId` 只在预归档上传前查一次，同轮内复用；检索、借阅车、借阅单、下载等流程不需要查询全宗，已有展示位置里的全宗信息照常显示

### 1.5) 大结果只摘要给用户

- 当前 CLI 会把完整 JSON envelope 写 stdout；Agent 回复时不要原样贴完整 JSON
- **全文检索结果的默认返回展示样式 = 「卡片视图」**，与 `weaver-work-cli --profile eteams archive search --format card`（或 `archive search --key <词> --format card`）输出保持一致；**除用户明确要求其他样式（text / html / 表格）外，一律按卡片视图返回，禁止退化成普通表格或贴 JSON**：
  - 每条固定三段：`序号. 【类型】 可点击题名链接` + 空行 + 命中高亮摘要 + 空行 + `全宗 / 分类 / 日期`；标题必须是可点击的档案视图链接（域名取当前 baseUrl）
  - 最多先给前 10 条；不要把 `dataId`、`formId`、`arcDangan` 等内部 ID 作为展示内容，它们只用于后续 operation 入参
  - Agent 需要卡片时优先直接调用 `archive search ... --format card` 拿渲染结果，避免手工拼字段
- **借阅车 / 借阅单列表的默认返回展示样式 = 「Markdown 表格」**（与检索的卡片视图区分开），除用户明确要求其他样式外一律用表格渲染：
  - 借阅车表格列：`序号 / 题名 / 类型(className) / 分类(categoryNames) / 形成日期(fileDate)`；借阅单表格列：`序号 / 题名 / 借阅时间 / 归还时间 / 归还状态 / 是否超期`
  - 各列取对应 operation 返回的可读字段；不要把 `dataId`、`workflowId`、`arcDangan` 等内部 ID 放进展示，它们只用于后续操作入参
  - 表格样式：分隔行统一 `| :---: |`（表头与各列内容都居中显示）；序号列只放 `1`/`2`… 纯序号，不放其他说明
  - 最多先给前 10 条；列数多时可只保留用户关心的关键列，题名超长时省略号截断
- 超长响应优先落本地文件并向用户提供摘要和文件路径

### 2) 已知对象时直达动作

- 已拿到 `dataId`、档案标识或本地文件路径时，优先调用对应 operation
- 同一轮里已有足够的新鲜查询结果时，不要重复查询同一列表或同一详情
- 不要默认走 `list -> detail -> prepare -> apply` 全链路；对象已明确时应压缩步骤

### 3) 错误语义驱动，而不是盲目重试

- 失败后先看进程退出码、`error.type`、`error.subtype` 和 `error.message`
- **除非错误明确提示可恢复或需要补充参数，否则不要重复刷同一个 operation**
- 写请求已经发出后，遇到结果不确定必须停止；不要把 `.apply` 当成可重试读操作
- 下载是异步任务，`.apply` 会持续轮询进度；不要因为等待时间长就中断重放
- **错误为 `authentication` 或 `session_expired` 时：立即停止当前操作，不要用示例占位域名或自行猜域名登录，也不要盲目重试**。先读取共享规则 `../weaver-e10-shared-connector/references/e10-auth-and-session.md`，按其中流程引导用户**断开并重新连接本连接器**完成重新登录，然后再继续原操作。

### 4) 附件、图片和文件解析确认

- 执行 `archive.upload.prelib.prepare/apply`、`archive.borrow-list.download.prepare/apply`，或任何会读取本地文件、上传文件内容、下载借阅原文 zip、解析图片/PDF/OFD 的步骤前，必须先提醒用户文件内容可能进入大模型上下文，也可能发送到 E10 文书定档案系统或文件服务器，或落到本地磁盘。
- 用户未明确确认前，不要运行上传、下载或解析命令。

## 写操作失败处理：`partial/write_uncertain` 决策树

当加入借阅车、发起借阅/续借、下载或上传返回 `partial/write_uncertain`，或提示网络中断、部分成功、回查失败、回查字段不一致时，按下面规则处理：

1. **先停止盲目重试**，不要连续重复提交相同 `.apply`
2. 优先从以下角度解释：
   - 写请求可能已经到达服务端，但连接在结果确认前中断
   - 服务端可能只处理了部分档案或只完成了部分上传步骤
   - 异步打包任务可能仍在后台进行，重新提交会再起一个任务
   - continuation、目标文件、目标借阅单或登录上下文可能已经变化
3. 如需确认，只补 **一次** 只读查询（例如 `archive.borrow-car.list` 或 `archive.borrow-list.detail`），不要陷入 query/write 循环
4. 最终给用户明确结论、已知状态、成功/失败项和下一步人工确认建议，而不是继续无意义重试

**特别注意：** 上传和下载最容易因重复提交造成重复入库或重复打包，更要严格执行上述规则。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams archive schema
weaver-work-cli --profile eteams --json archive run archive.fonds.list --input-json '{"menuSign":"collectLib"}'
weaver-work-cli --profile eteams --json archive run archive.search.run --input-json '{"key":"会计凭证","pageNo":0,"pageSize":10}'
weaver-work-cli --profile eteams --json archive run archive.borrow-car.list --input-json '{"pageNo":1,"pageSize":10}'
weaver-work-cli --profile eteams --json archive run archive.borrow-car.add --input-json '{"formAndIds":[{"formId":"1190991330335571989","ids":["1252600626189156465"]}]}'
weaver-work-cli --profile eteams --json archive run archive.borrow-list.download.prepare --input-json '{"dataId":"1302806508947652629"}'
weaver-work-cli --profile eteams --json archive run archive.flow.borrow-car.prepare --input-json '{"arcIds":["1252600626189156465_1190991330335571989"],"carIds":["1302754028599656449"]}'
weaver-work-cli --profile eteams --json archive run archive.upload.prelib.prepare --input-json '{"file":"./档案.pdf","fondsId":"1042286256822697531"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams archive schema
weaver-work-cli --profile eteams --json archive run archive.fonds.list --input-json '{"menuSign":"collectLib"}'
weaver-work-cli --profile eteams --json archive run archive.search.run --input-json '{"key":"会计凭证","pageNo":0,"pageSize":10}'
weaver-work-cli --profile eteams --json archive run archive.borrow-car.list --input-json '{"pageNo":1,"pageSize":10}'
weaver-work-cli --profile eteams --json archive run archive.borrow-car.add --input-json '{"formAndIds":[{"formId":"1190991330335571989","ids":["1252600626189156465"]}]}'
weaver-work-cli --profile eteams --json archive run archive.borrow-list.download.prepare --input-json '{"dataId":"1302806508947652629"}'
weaver-work-cli --profile eteams --json archive run archive.flow.borrow-car.prepare --input-json '{"arcIds":["1252600626189156465_1190991330335571989"],"carIds":["1302754028599656449"]}'
weaver-work-cli --profile eteams --json archive run archive.upload.prelib.prepare --input-json '{"file":"./档案.pdf","fondsId":"1042286256822697531"}'
```

## 不在本 skill 范围

- 禁止加载原始接口文档版 Skill 代替 CLI；本 Skill 通过 `weaver-work-cli` 执行业务操作。
- 禁止 curl、fetch、浏览器自动化或直接访问 E10 `/api/archive/**`、`/api/ebuilder/**`、`/api/file/**`。
- 禁止读取或复制 CLI runtime 内部 Token、Cookie、ETEAMSID。
- 禁止读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
- 借阅申请表单提交、借阅车移除、归还/催还等能力当前未纳入 CLI manifest；需要先在页面操作或使用流程创建页 URL。
- 非档案类 E10 能力、通用流程编排、非文书定的表单/审批/组织等业务不由本 Skill 承载。
