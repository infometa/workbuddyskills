---
name: wangxiaobao-audio-wiki
version: 0.1.0
description: "旺小宝录音入库：把指定时间窗的录音同步到本地，按 项目/顾问/日期/录音 四层目录归档到 llm-wiki 知识库（wiki/projects/{projectId}-{projectName}/raw/audio/...），再 ingest 提炼为 顾问画像 / 客户 / 话题 / 话术 四类 Layer 2 知识页。每个旺小宝项目对应一个独立 wiki 目录不串味；一站式 sync→ingest 工作流。底层依赖: xiaobao-cli audio list 拉元数据 + xiaobao-cli audio text 拉文本，配合 Read/Write 工具落盘 + 维护 .cursor 增量游标。何时用：用户说拉录音/同步录音/旺小宝录音/音频归档/录音入库/建录音知识库；要为某位置业顾问建立画像、统计客户跟进、整理话术；要把旺小宝录音长期沉淀成可检索的销售知识 wiki。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli audio --help"
---

# 旺小宝录音入库

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

完整工作流：**登录 → 选项目 → 翻页拉元数据 → 逐条取文本 → 按
**项目 / 顾问 / 日期 / 录音** 分层写 wiki → 推进游标 → ingest 提炼为
Layer 2 知识页**。

## 上游接口

| 接口 | 命令 | 用途 |
| --- | --- | --- |
| `POST /ai-open/audio/page` | `xiaobao-cli audio list` | 分页列录音元数据 |
| `GET /ai-open/audio/text/{audioId}` | `xiaobao-cli audio text` | 单条录音转录文本 + 说话人占比 |

## 执行前必读

1. **登录**：先调 `xiaobao-cli auth whoami`；未登录 / 过期就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）。
2. **激活项目**：命令内部从 `~/.xiaobao/active-project.json`
   读 tenant/project。如果任何 命令 返回 `error: 'NO_ACTIVE_PROJECT'`，
   先走 `wangxiaobao-switch-project` skill 让用户选。
3. **拿到 projectId / projectName**（写 wiki 路径用）：调一次
   `xiaobao-cli project list` 后定位当前 active-project 对应行，或者直接复用
   `xiaobao-cli project use` 上一次的返回值里的 `activeProject` 字段。
4. **wiki 输出目录**：默认 `./wiki/`（cwd 下）。如果用户在 cwd `./.env`
   配了 `WIKI_DIR`，用 `${WIKI_DIR}/`。raw/ 子目录是 llm-wiki Layer 1，
   **不可变**。
5. **游标变量名**：`WB_SYNC_CURSOR`，**仍写到 cwd `./.env`**（游标是 per-workspace
   的同步进度，不是 CLI 全局状态，跟 active-project 不一样），格式
   `yyyy-MM-dd HH:mm:ss`。
6. **wiki schema 必读**：业务知识页结构详见
   [`references/audio-wiki-schema.md`](references/audio-wiki-schema.md)
   ——目录布局 / frontmatter / wikilinks 规则全在那里。

## 时间格式

上游用 pierre 框架 Jackson 配置，LocalDateTime 反序列化只接受
`yyyy-MM-dd HH:mm:ss`（中间空格分隔，**不是** ISO 的 `T`）。

- ✅ `"2026-05-12 12:00:00"`
- ⚠️ `"2026-05-12T12:00:00"`（命令 内部会自动转空格，但 SKILL 里直接传空格更稳）
- ❌ `"2026-05-12T12:00:00+08:00"`（带时区会被剥掉，避免传）

## 工作流

### 第 1 步：确定时间范围

按优先级：

1. 用户显式给了 `--from` / `--to` → 直接用
2. `.env` 里有 `WB_SYNC_CURSOR` → `from = WB_SYNC_CURSOR`, `to = now()`
3. 都没有 → `from = now() - 7 days`, `to = now()`

### 第 2 步：按 3 小时窗口翻页拉元数据

把 `[from, to]` 切成连续的 3 小时窗口。每个窗口循环：

```
for each window [winStart, winEnd):
  page = 1                              # ⚠️ PageParam 默认从 1 开始
  loop:
    resp = xiaobao-cli audio list {
      fromDate: winStart,
      toDate:   winEnd,
      page,
      size: 50
      # ⚠️ 没有 tenantId / projectId —— CLI 自己从 active-project 读
    }
    pageResult = resp.data.data           # Result<PageResult<...>> 拨开两层 envelope
    records = pageResult.content
    把每条 record 进入第 3 步取文本

    若 records 长度 < size 或 page * size >= pageResult.total → break 翻页
    否则 page += 1
```

若 命令 返回 401 → 走 `auth login --no-wait --force` split-flow 重登后重试当前窗口
（最多重试一次）。

### 第 3 步：逐条取文本

每条 record（有 audioId）单独调一次：

```
text = xiaobao-cli audio text {
  audioId: record.audioId
  # ⚠️ 没有 tenantId / projectId
}
# text.data.data 是 AudioTextResp: { audioId, talkRatios[], texts[] }
```

如果 `texts` 为空（转录还没好 / 录音异常）：**跳过**这条，不写文件、不阻塞
游标推进。在最终汇总里报告"X 条无文本"。

### 第 4 步：按 项目/顾问/日期/录音 四层写入 raw/

**路径**：

```
wiki/projects/{projectId}-{projectName}/raw/audio/{userId}-{saleName}/{yyyy-MM-dd}/{audioId}.md
```

- 第 0 层 `projects/{projectId}-{projectName}/` — 旺小宝项目隔离（projectId
  锚稳定 + projectName 给人看，name 含特殊字符要 sanitize）
- 第 1 层 `{userId}-{saleName}/` — 置业顾问目录（userId 在前保证稳定，
  saleName 给人看；saleName 里的非法路径字符要 sanitize，详见 schema 文档）
- 第 2 层 `{yyyy-MM-dd}/` — 录音发生时的日期（从 `record.startTime` 拿）
- 第 3 层 `{audioId}.md` — 单条录音

**frontmatter 必填**：

```yaml
---
source: wangxiaobao-audio
audio_id: 12345
file_id: "..."
file_url: "..."

tenant_id:  "395809723556831232"
project_id: "434616948240678912"

recorded_start: "2026-05-12 10:23:11"
recorded_end:   "2026-05-12 10:35:42"
duration_sec:   751

consultant_user_id: 100
consultant_name:    张三

talk_ratios:
  - role: 销售
    ratio: 0.62
  - role: 客户
    ratio: 0.38

layer: raw
parent_consultant: "[[consultants/100-张三]]"
---
```

正文：把 `text.texts[]` 按 "speaker: content" 逐行排好，行首带时间戳。

**写入策略**：
- 用 Write tool 创建文件（Claude Code 内置写文件工具），**同名文件已存在就跳过**（raw 幂等不可变）
- 写完一个窗口报"本窗口写入 N 条 / 跳过 M 条同名 / 跳过 K 条无文本"

> 完整 frontmatter 字段含义 + saleName sanitize 规则见
> [`references/audio-wiki-schema.md`](references/audio-wiki-schema.md) 第 1-2 节。

### 第 5 步：推进游标

每个窗口跑完且全部记录写盘后，立刻把 cwd `./.env` 的 `WB_SYNC_CURSOR`
更新为 `winEnd`：

- Read `./.env`
- Edit 替换 `WB_SYNC_CURSOR=...` 行；没有就追加
- **保留** `.env` 其他 key

### 第 6 步：sync 阶段汇总

```
📦 同步完成
- 时间范围：2026-05-01 00:00:00 ~ 2026-05-12 12:00:00
- 窗口数：64
- 元数据条数：215
- 写入 wiki/projects/9001-成都项目甲/raw/audio/：208 条
- 跳过（同名）：3 条
- 跳过（无文本）：4 条
- 游标推进到：2026-05-12 12:00:00

下一步可执行 ingest，把本项目 raw/audio/ 提炼为 Layer 2 知识页。
```

---

## 第 7 步：ingest 提炼 Layer 2 知识页

raw/ 数据落盘后，把内容按"**顾问 → 客户/话题 → 话术**"层级提炼成 Layer 2
知识页。**ingest 跑在当前项目目录内**，不跨项目读写。Layer 2 目录结构：

```
wiki/projects/{projectId}-{projectName}/
├── consultants/{userId}-{saleName}.md   # 置业顾问画像（沟通风格、客户类型、月度统计）
├── customers/{customerName}.md          # 客户画像（兴趣点、跟进时间线、状态）
├── topics/{topic}.md                    # 话题/场景（"户型疑虑"、"价格异议"）
└── scripts/{scriptName}.md              # 可复用话术（"破冰寒暄"、"户型介绍"）
```

每层页 frontmatter 字段、wikilinks 最少数量、tag 词表来源——都按
[`references/audio-wiki-schema.md`](references/audio-wiki-schema.md) 走。

通用 ingest 流程（dedupe / wikilinks 检查 / log/index 维护 / Layer 不可变约束）
继承 Karpathy LLM Wiki 规范，详见
[`references/llm-wiki-ingest.md`](references/llm-wiki-ingest.md)。

### 三条必守 prime（给 LLM 一个最小约束集）

1. **`raw/` 只读**——ingest 不要回写 raw/，新增内容只能写 Layer 2 + Layer 3 (index/log)
2. **wikilinks ≥ 2**——每个 Layer 2 页至少 2 个 wikilinks（具体最小连接图见 schema 第 5 节）
3. **tag 必须从 SCHEMA.md 词表选**——遇到词表外新词时**先 prompt 用户加进词表**，不要私自创建

### ingest 阶段汇总

```
🧠 Ingest 完成
- 项目：9001-成都项目甲
- 扫描 raw/audio/：208 条新文件
- 新建 consultants 页：3 个
- 更新 consultants 页：5 个
- 新建 customers 页：12 个
- 新建 topics 页：4 个（其中 1 个等用户确认 SCHEMA 词表后再补）
- 新建 scripts 页：2 个
- 更新 index.md / log.md
```

---

## 用户参数解析

| 用户说法                   | 行为                                                          |
| -------------------------- | ------------------------------------------------------------- |
| "拉一下今天的录音"         | from = 今天 00:00:00, to = now                                |
| "把上周的录音入库"         | from = 上周一 00:00:00, to = 上周日 23:59:59                  |
| "从游标继续" / "继续同步"  | from = WB_SYNC_CURSOR, to = now                               |
| "重跑某天"                 | 临时用指定窗口，**不**回退游标                                |
| "干跑 / dry-run"           | 走前 3 步但跳过第 4-5 步的写盘和游标更新                      |
| "只看某个销售的"           | 先调 `xiaobao-cli consultant list` 反查 user-id，再 list_audio 带 `--user-id <sale-user-id>` |
| "把张三本周的录音存下来"   | 同上 + 时间窗口限定本周                                       |
| "ingest 录音建知识库"      | 跳到第 7 步（前提：raw/ 已经有数据）                          |
| "拉完顺便 ingest"          | 走完整 7 步（sync + ingest 一站式）                           |

---

## 完整链路

```
1. xiaobao-cli auth login --no-wait → --resume   — 拿到 token
2. wangxiaobao-switch-project    — 选好租户/项目，写 ~/.xiaobao/active-project.json
3. 本 skill - sync 阶段          — 翻页拉 → 逐条取文本 → 按 顾问/日期 写 raw → 推进游标
4. 本 skill - ingest 阶段         — 读 raw/ → 提炼 4 层 Layer 2 知识页 → 更新 index/log
```

> sync 跟 ingest 是同一个 skill 的两个阶段，用户可以分两次调用（先拉数据
> 后入库提炼），也可以一次性走完。

---

## 注意事项

- Token 有效期由 phoenix 端 client 配置决定（默认 1h access + 30d refresh）。
- 游标为空时默认从 7 天前开始。
- 首次跑或拉历史范围大时建议先 dry-run。
- API 路径已封装在 命令 里，**不要**用 `xiaobao-cli api` 自己拼
  `/audio/page` / `/audio/text/{id}`。
- 激活项目状态在 `~/.xiaobao/active-project.json`（CLI
  全局单份，跟 cwd 无关）；游标 `WB_SYNC_CURSOR` 在 cwd `.env`（per-workspace）。
- `wiki/projects/.../raw/audio/` 是 Layer 1 不可变，**不要**回写、改名、删除。
- **批量取文本要节制并发**：一个窗口可能几十条录音，串行调（不要 parallel
  fan-out 太多），让 token refresh-on-401 不打架。
- ingest 阶段如果某个 Layer 2 页 wikilinks 凑不够 2 个，**先不创建那页**，
  留到累积够引用再建（避免孤儿页污染知识图）。

## 常见错误与排查

- **`xiaobao-cli audio list` 返回 401** — token 过期 → 走 `auth login --no-wait --force` split-flow 重登
- **`xiaobao-cli audio text` 返回 `data: null` / `texts: []`** — 转录未就绪 / 录音异常 → 跳过该条
- **page 翻不动 / 重复返回同一页** — 检查 page 是否从 1 开始；`total = 0` 直接结束窗口
- **fromDate/toDate 报参数错** — 用空格分隔的 `yyyy-MM-dd HH:mm:ss`，不带时区
- **游标没推进** — 窗口中途报错被跳过 → 查哪个窗口失败、修复后从上次成功窗口的末尾重跑
- **`error: 'NO_ACTIVE_PROJECT'`** — 还没设过激活项目 → 跑
  `wangxiaobao-switch-project` skill。注意：CLI active-project 是全局单份，
  跟 cwd 无关；游标 `WB_SYNC_CURSOR` 在 cwd `.env` 里，用户切了 cwd 会丢失游标
  上下文，需要从指定时间继续或重新拉
- **raw/ 写文件冲突** — 同名 audioId 已存在 → 跳过（raw 幂等）
- **顾问名含特殊字符导致路径错** — 按 schema 文档 sanitize 规则处理（删 `/ \ : * ? " < > |` 和空格）
- **顾问改名导致 consultants/ 出现两个文件** — `git mv` 老路径到新路径，批量 replace 所有指向它的 wikilinks，**不要**两个文件并存
- **ingest 时 tag 词表外的新词** — 先 prompt 用户加进 SCHEMA.md，不要私自新建
