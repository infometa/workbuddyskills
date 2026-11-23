---
name: cue-research-cli
description: Cue 深度研究 CLI（@cueai/cue-cli，命令 cue）使用说明。用于行业/公司/人物/政策/合规类深度调研：一句话发起多智能体研究，输出带来源的 Markdown 报告，可落盘、可续接会话追问、可指定搭子模板。涉及「深度调研」「尽调」「行研」「公司研究」「竞品对比」「政策跟踪」「人物核查」等需要多源检索与交叉验证的场景时使用。
version: "1.1.0"
---

# Cue 调研搭子（cue CLI）

`cue`（npm 包 `@cueai/cue-cli`）是 Cue（cuecue.cn）多智能体深度研究的本地命令行桥梁。WorkBuddy 负责安装与登录态调度，本 Skill 只负责「拿到命令后怎么调」。

**核心命令：`cue research`** —— 把一句自然语言问题交给 Cue，自动拆解子任务、多源检索交叉验证，返回带来源引用的 Markdown 研究报告。

> ⚠️ 本 skill 与仓库里那个**同名的 Python 形态** `cue-research/` 是两件事：那个是
> 让 agent 直接跑 Python 脚本的形态，本目录是 **CLI 形态**（命令 `cue`，由 WorkBuddy 安装）。
> 两者名字相近但入口不同，别混用。

## 一、何时使用 / 何时不用

**应使用**：需要多源检索 + 交叉验证 + 出报告的开放性问题，例如行业研究、公司/竞品调研、政策与监管跟踪、人物背景核查、合规风险体检、投前/贷前尽调。

**不应使用**：
- 单条事实查询（某股票现价、今天天气）—— 直接用行情/搜索工具，不要为它跑一次深度研究；
- 纯本地文件处理（解析 PDF、改写文档）—— Cue 不做这个（`cue` 没有文档解析命令）；
- 需要秒级返回的交互 —— 一次研究通常数分钟。

## 二、前置条件

1. CLI 由 WorkBuddy 通过 `npm install -g @cueai/cue-cli` 安装（Node ≥ 20.12，由 WorkBuddy 托管运行时）；
2. 登录态：`cue auth status`（Windows 为 `cue.cmd auth status`）输出「已登录」才算可用，退出码 0=已登录 / 2=未登录；
3. 未登录时引导用户在连接器面板点「连接」：`cue auth login` 会打印 https:// 授权 URL，由 WorkBuddy 打开浏览器完成设备码授权；
4. **浏览器授权暂不可用时的退路**：若 `cue auth login` 明确提示「服务端尚未开放设备码授权」，改用用户自填 Key —— 到 https://cuecue.cn/api-key 创建 key，然后 `cue auth login --api-key <key>`，或设 `export CUE_API_KEY=sk-...` 后重跑。**看到该提示时直接走这条退路，不要反复重试 `auth login`**；
5. 排障先看 `cue doctor`（输出 JSON：node 版本、配置文件、脱敏 key、API 连通性）。

> **登录态是怎么维持的**：设备码换来的访问令牌 1 小时过期，但 CLI 会在任何 API 调用
> 遇到 401 时**自动静默刷新一次并重试**。所以**不要因为一次 401 就急着让用户重新登录** ——
> 只有刷新也失败时，CLI 才会以退出码 2 结束，那时再引导重连。

## 三、命令速查

| 命令 | 用途 |
|---|---|
| `cue research "<问题>"` | 发起一次研究，报告打到 stdout（前台阻塞到完成） |
| `cue research "<问题>" -o <文件>` | 报告落盘为 Markdown，并附来源清单 |
| `cue research "<问题>" --json` | 输出 `{conversationId, elapsedMs, report, sources, timeline}` |
| `cue research "<问题>" --conversation-id <id>` | 续接同一会话追问 |
| `cue research "<问题>" --template-id <id>` | 用指定搭子模板跑 |
| `cue playbook list` / `cue playbook get <id>` | 查看搭子模板（列表 / 详情） |
| `cue doctor` | 环境与连通性自检（JSON，无副作用） |
| `cue auth login` / `status` / `logout` | 授权 / 查登录态 / 登出清凭证 |

Windows 下命令名用 `cue.cmd`，参数完全一致。

## 四、`cue research` 参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `<query>` | string | 是 | — | 研究问题，自然语言，用引号包裹 |
| `--template-id <id>` | string | 否 | — | 搭子模板；裸 id 自动补 `template_` 前缀，纯数字后缀直接报错 |
| `--conversation-id <id>` | string | 否 | 随机 | 续接会话；ID 来自上次输出的 `conversation_id` |
| `-o, --output <file>` | string | 否 | — | 落盘 Markdown，支持 `~/`，目录自动创建 |
| `--timeout <seconds>` | number | 否 | 1200 | 整轮超时 |
| `--json` | flag | 否 | false | 结构化输出，适合再做二次处理 |
| `-q, --quiet` | flag | 否 | false | 不打印进度（进度默认写 stderr） |

## 五、推荐调用姿势

**落盘（默认用法）**：

```bash
cue research "比亚迪 DM-i 与长城 Hi4 混动技术路线差异" -o reports/byd-hi4.md
```

**要结构化结果**（需同时拿到来源与时间线）：加 `--json`。

**续接追问**：用上次输出的 `conversation_id` 加 `--conversation-id`，在原研究上下文里追问（如「再补一节供应商集中度」）。

**用搭子模板**：先 `cue playbook list` 找到 `template_id`，再 `--template-id` 传入。

## 六、耗时与额度

- 单次研究通常数分钟，默认超时 1200 秒；
- 一次只跑一个研究，不要并发；
- 深度研究消耗 Cue 额度，问题越聚焦越省；不要为验证连通性反复提交真实研究（用 `cue doctor` 验证连通即可）。

## 七、错误处理

| 退出码 | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | — |
| 2 | 缺少/失效凭证（含 401、403） | 重新连接；`cue auth login` |
| 3 | 入参错误（如纯数字 template_id） | 改参数后重试 |
| 4 | 网络不可达 | 检查网络/代理/`--base-url` |
| 5 | 超时 | 加大 `--timeout`，或用 `--conversation-id` 续跑 |
| 1 | 其他错误 | 读 stderr 原文 |

「未捕获到报告正文」时 stderr 会给出 `kind=...`（`no_agent_events` / `stream_cut_before_reporter` / `reporter_started_no_text`）与 `conversation_id`，据此续跑或调超时，不要凭空补写内容。

## 八、纪律

- 不在命令行、日志或回复里输出 API Key；非必要不用 `--api-key`（会进进程列表）；
- 报告结论以 Cue 返回的正文与来源为准，缺失部分标注「未检索到」，**不要补写未经验证的数据**；
- 需要用户决策的高风险动作（对外发送、下单、删除）先确认；研究本身只读取公开信息与用户自有数据。
