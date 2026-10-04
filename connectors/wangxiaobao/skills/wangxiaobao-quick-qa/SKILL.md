---
name: wangxiaobao-quick-qa
version: 0.1.0
description: "旺小宝业务数据问数（自然语言）：用一句话问当前激活项目的客户 / 来访 / 挖需率 / 销冠 / 录音覆盖率 / 业务指标等开放式问题，AI 直接基于旺小宝数据回答。只读、无副作用、超时 30 分钟。多轮追问通过 --thread-id 续接。高频命令: xiaobao-cli qa '<prompt>' [--thread-id <id>]。何时用：用户问今天来了几个客户/本周新增多少客户/意向客户都有谁/老客户回访/今天到访多少组/首访 vs 复访比/挖需率/成交转化率/客户分级分布/本月销冠是谁/张三这周成交几单/销售排行榜/业绩 TOP3/录音覆盖率/哪些销售有几条录音/本周通话时长 TOP5/未跟进客户有多少；任何问一句旺小宝业务数据的开放式问题。注：要列录音元数据走 audio-query 更快；批量同步录音文本到 wiki 走 audio-wiki。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli qa --help"
---

# 旺小宝问数

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli qa` 用自然语言问当前激活项目的业务数据。
零副作用，不写文件、不动 wiki，所以用错也没成本，鼓励放心调用。

> **后端说明**：问数底层已由旧的 fast-responder 升级为 **sql-agent**（自然语言 → SQL，
> 由 ai-open 代理到 wang-ai-mcp）。行为对调用方**透明**——请求 `{ prompt, thread_id }`
> 与响应结构（含 `type: "quick-qa"`）都不变，多轮 `--thread-id` 续接照旧。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录 / 过期就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：命令内部自动从激活项目状态读 tenant/project，
  调用方**不要传** tenant/project 参数。如果 命令 返回
  `error: 'NO_ACTIVE_PROJECT'`，让用户跑 `wangxiaobao-switch-project` skill
  后再重试
- **绝不要**写文件。即使用户随口说"顺便存一下"也要拦——告诉用户"出长报告
  的功能暂未发布，如果想存可以把回答复制下来"

---

## 快速索引：意图 → 工具

| 用户意图                           | 命令        | 关键参数                              |
| ---------------------------------- | ------------------ | ------------------------------------- |
| 单轮问数                           | `xiaobao-cli qa` | `prompt`                              |
| 接着上一轮继续追问                 | `xiaobao-cli qa` | `prompt + threadId`                   |
| 给问题加上下文（如客户 ID 列表）    | `xiaobao-cli qa` | `prompt + context: {...}`             |

---

## 核心约束

### 1. 用业务语言问，不要追问 ID

用户问"张三本周成交几单"——直接把 prompt 原样传给 命令，**不要**先去查
张三的 user-id 再拼参数。后端 AI 知道"张三"在当前项目里就是谁。

如果用户问的是开放性问题（"客户主要疑虑是啥"），更不要画蛇添足拼任何
ID / 时间窗口——AI 会自己定义合理范围。

### 2. 多轮：threadId 由 agent 自己接续

第一轮**不传** `--thread-id`，走单轮模式。响应里有 `resp.data.data.thread_id`，
**记在 agent 当前对话上下文里**，后续追问把它原样传回 `--thread-id` 入参。
**不要**把 thread_id 写到任何文件 / .env / 状态——它只是会话短期记忆。

跨 session（用户关了 chat）就**不再延续**，新 session 重新发起新一轮即可。

### 3. 响应只取 answer 给用户

`xiaobao-cli qa` 返回结构：

```jsonc
{
  "code": "0",
  "msg":  "success",
  "data": {
    "type":      "quick-qa",
    "thread_id": "...",
    "answer":    "最终文本（这就是要展示给用户的）",
    "output":    { /* 原始结构化数据，agent 自己看就行，不展示 */ }
  }
}
```

CLI 又把上面塞进 `{ status, ok, data }` 外包：拿最终文本写
`resp.data.data.answer`，渲染给用户**只展示 answer**。

如果要支持后续追问，结尾加一句"💡 想接着问可以告诉我，会沿用本次对话上下文"
（threadId 由 agent 自己存，不要让用户记）。

### 4. 不要拉太多上下文进 context

`context` 字段可以塞额外背景，但**控制在 < 4KB**。需要塞大块录音 / 客户
档案的需求暂时没有 CLI 侧支持——用户可以分多轮 prompt 喂，每轮塞一段。

### 5. 不要替代 audio-query 做"列录音元数据"

用户问"列下今天哪些录音"、"audioId 是多少"——那是
`wangxiaobao-audio-query` skill 的事（直接走录音元数据 API，更快也更精确）。
本 skill 是问"开放式业务问题"用的，不是数据列表 API 代理。

---

## 使用场景示例

### 场景 1：问客户来访

```bash
xiaobao-cli qa "今天到访了多少组客户，里面有几组是首访？"
```

渲染：

```
今天到访 18 组，其中：
- 首访 11 组（61%）
- 复访 7 组

💡 想接着问可以告诉我，会沿用本次对话上下文。
```

### 场景 2：问销冠

```bash
xiaobao-cli qa "本月销冠是谁，业绩多少？"
```

渲染：

```
本月销冠：张三
- 成交 8 单 / 金额 1240 万
- 跟进客户 47 组，成交转化率 17%
```

### 场景 3：问录音覆盖率

```bash
xiaobao-cli qa "本周录音覆盖率怎么样？哪些销售覆盖低？"
```

渲染：

```
本周录音覆盖率 78%（45 个销售里 35 个开了工牌录音）。
覆盖偏低的销售（< 50%）：
1. 李四（22%）
2. 王五（38%）
3. 赵六（45%）
```

### 场景 4：接着追问（多轮）

用户："那张三跟客户讲到学区时通常怎么应对？"
（接着上一轮 ——agent 自己存了 threadId）

```bash
xiaobao-cli qa "那张三跟客户讲到学区时通常怎么应对？" --thread-id "<上一轮 resp.data.data.thread_id>"
```

### 场景 5：带额外 context（v0.1.x 暂不支持）

CLI 当前只暴露 `--thread-id`，不支持 `--context` JSON 入参。要给 AI 喂上下文，
**把上下文直接写进 prompt** 即可：

```bash
xiaobao-cli qa "评估一下客户 12345 的成交概率，相关录音 audioId: 9001, 9023, 9045"
```

后端 AI 会从 prompt 文本里识别 customer_id / audio 引用。

---

## 典型问数关键词参考

帮 agent 识别用户意图。看到这类词就走本 skill：

- **客户类**：客户、新客、老客、意向客、成交客、客户画像、客户分级、回访
- **来访类**：到访、来访、首访、复访、上门、到店、客流
- **挖需 / 转化**：挖需率、转化率、意向、成交率、跟进、转化漏斗
- **销售 / 销冠**：销冠、销售排行、业绩、佣金、TOP、成单
- **录音 / 接待**：录音、通话、对话、接待、覆盖率、时长
- **业务指标**：成单、签约、定金、退订、回款、佣金

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 还没设过激活项目 → 跑
  `wangxiaobao-switch-project` skill 后重试
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登，重试一次
- **响应耗时 > 30 分钟** — 后端慢到打满 CLI timeout → 告诉用户"上游慢，稍后重试"
- **answer 为空** — 上游这一轮没产出最终文本 → 让用户换个 prompt 重试
- **用户想"批量出报告"** — 拦住：本期 CLI 没有报告生成 skill，
  解释"出长报告的功能在做异步化改造，下期发布"
- **用户问"列录音元数据 / audioId 是多少"** — 切到
  `wangxiaobao-audio-query` skill，那个走元数据 API 更精确
