# 旺小宝录音 Wiki — 业务 Schema

本文档定义 `wangxiaobao-audio-wiki` skill 落地的 wiki 目录结构、
frontmatter 字段约束、wikilinks 规则、标签词表来源。

**继承关系**：在 [`llm-wiki-ingest.md`](llm-wiki-ingest.md)（Karpathy LLM
Wiki 通用规范，Layer 1/2/3 分层、index/log 机制、wikilinks 最少数量等
框架）之上**叠加**这套业务 schema。先读通用规范再读本文。

---

## 1. Layer 0 — `projects/` 项目维度（最外层）

所有 wiki 内容**先按项目分组**。用户在 `wangxiaobao-switch-project` skill
切项目后，wiki 写入路径都落到对应项目目录下，避免不同项目的录音 / 顾问
画像 / 客户档案串味。

```
wiki/
└── projects/
    └── {projectId}-{projectName}/        # 第 0 层：项目（projectId 锚稳定，name 给人看）
        ├── raw/audio/...                  # 第 1-3 层（顾问/日期/录音，见下文）
        ├── consultants/                   # Layer 2 子目录
        ├── customers/
        ├── topics/
        ├── scripts/
        ├── index.md                       # Layer 3：本项目索引
        ├── log.md                         # Layer 3：本项目 ingest 日志
        └── SCHEMA.md                      # Layer 3：本项目标签词表
```

### 为什么是 `{projectId}-{projectName}`

跟下文顾问目录同思路：`projectId`（前缀）稳定唯一，`projectName`（后缀）
给人看。项目改名是低频事件，靠 frontmatter `project_id` 字段做稳定关联。

### projectName 同样要 sanitize

删 `/ \ : * ? " < > |` 和空格；保留中文 / 字母 / 数字 / `-` / `.`。

示例：`"成都小黄鸭一号"` → 直接用；`"销售/管理 试点"` → `销售管理试点`。

### 多项目共存怎么办

一个 cwd 下可以同时存放多个项目的 wiki —— `wiki/projects/9001-成都项目甲/`
和 `wiki/projects/9002-成都项目乙/` 并存。用户切项目时（CLI 全局
active-project 变了，由 `xiaobao-cli project use` 命令 写入
`~/.xiaobao/active-project.json`），sync / ingest
**只动当前 project 目录**，老项目的 wiki 不受影响。

### SCHEMA.md / index.md / log.md 项目独立

每个项目有自己的标签词表（话题分类 / 话术分类）、自己的索引、自己的入库
日志。如果两个项目想共享词表，用软链接或者复制；默认是**每项目独立**。

---

## 2. Layer 1 — `raw/audio/` 三层目录（在项目目录下）

录音原始数据按 **顾问 / 日期 / 录音** 三层嵌套，挂在项目目录下：

```
wiki/projects/{projectId}-{projectName}/
└── raw/
    └── audio/
        ├── {userId}-{saleName}/         # 第 1 层：置业顾问（user-id 锚稳定，名字给人看）
        │   ├── 2026-05-09/              # 第 2 层：录音发生日期（startTime 的日期）
        │   │   ├── 12345.md             # 第 3 层：单条录音（文件名 = audioId）
        │   │   ├── 12346.md
        │   │   └── 12347.md
        │   └── 2026-05-10/
        │       └── 12348.md
        └── 200-李四/
            └── 2026-05-09/
                └── 12349.md
```

### 为什么用 `{userId}-{saleName}` 作目录名

- `userId`（前缀）保证**稳定唯一**：即使顾问改名 / 离职后重新入职，路径
  不会乱
- `saleName`（后缀）保证**人能直接看懂**：浏览 `raw/audio/` 时无需查 id
- 顾问改名是低频事件，路径漂移可接受；ingest 阶段从 frontmatter 拿
  `consultant_user_id` 关联（不依赖路径里的名字字符串）

### saleName 字符 sanitize

- 删除：空格、`/` `\` `:` `*` `?` `"` `<` `>` `|`
- 保留：中文 / 字母 / 数字 / `-` / `.`

示例：`"张 三·王"` → `张三王`，最终目录 `100-张三王/`

### Layer 1 不可变

`raw/audio/` 下任何文件**只写一次**：
- audio-wiki sync 阶段写入
- 后续 ingest 阶段**只读**
- 即使录音数据变化，也不 overwrite —— 业务上不应该出现

---

## 3. Layer 1 录音文件 frontmatter

每条 `raw/audio/.../{audioId}.md` 的 frontmatter 必填字段：

```yaml
---
# 出处与稳定锚点
source: wangxiaobao-audio
audio_id: 12345                          # 主键，跟文件名一致
file_id: "..."                           # 上游 fileId
file_url: "..."                          # 18000 秒过期的播放链接（仅出处参考）

# 多租户隔离锚
tenant_id: "395809723556831232"          # CLI active-project.tenantId
project_id: "434616948240678912"         # CLI active-project.projectId

# 时间锚（LocalDateTime 不带时区，跟上游 API 一致）
recorded_start: "2026-05-09 10:23:11"
recorded_end:   "2026-05-09 10:35:42"
duration_sec:   751

# 置业顾问关联（ingest 时建 wikilink 用）
consultant_user_id: 100
consultant_name:    张三

# 说话人占比（来自 xiaobao-cli audio text 的 talkRatios）
talk_ratios:
  - role: 销售
    ratio: 0.62
  - role: 客户
    ratio: 0.38

# Layer 关系（让 LLM 一眼分清层级）
layer: raw
parent_consultant: "[[consultants/100-张三]]"   # wikilink，指向 Layer 2 顾问页
---
```

正文：把 `xiaobao-cli audio text` 返回的 `texts[]` 按 "speaker: content"
逐行排好。每行可带时间戳：

```
[10:23:15] 销售：您好张总，我是旺小宝的小张，咱们那个项目...
[10:23:22] 客户：嗯嗯你说
...
```

---

## 4. Layer 2 — 三层知识页

ingest 阶段从 `raw/audio/` 提炼出知识页，按"顾问 → 客户/话题 → 话术"组织：

```
wiki/projects/{projectId}-{projectName}/
├── consultants/                # ┐
│   ├── 100-张三.md             # │ 第 1 层：置业顾问画像
│   └── 200-李四.md             # ┘
├── customers/                  # ┐
│   ├── 王总.md                 # │ 第 2 层（A）：客户画像
│   └── 李女士.md               # ┘
├── topics/                     # ┐
│   ├── 户型疑虑.md             # │ 第 2 层（B）：话题/场景
│   └── 价格异议.md             # ┘
└── scripts/                    # ┐
    ├── 破冰寒暄.md             # │ 第 3 层：可复用话术
    └── 户型介绍.md             # ┘
```

> 第 2 层有两个并列子类（客户 / 话题），它们之间不分先后；scripts/
> 是从 topics 进一步抽象出的"可复用话术"。

### 3.1 `consultants/{userId}-{saleName}.md` — 置业顾问画像

```yaml
---
layer: consultant
consultant_user_id: 100
consultant_name:    张三
tags: [置业顾问, consultant]            # 标签必须来自 SCHEMA.md 词表

# 至少 2 个 wikilinks
recent_audios:
  - "[[raw/audio/100-张三/2026-05-09/12345]]"
  - "[[raw/audio/100-张三/2026-05-09/12346]]"
top_customers:                          # 高频对接客户
  - "[[customers/王总]]"
  - "[[customers/李女士]]"
top_topics:
  - "[[topics/户型疑虑]]"
  - "[[topics/价格异议]]"

# 时间维度（按月聚合，让顾问表现可追踪）
monthly_stats:
  "2026-05":
    audio_count: 23
    avg_duration_min: 12
    new_customers: 5
---
```

正文：人话总结这位顾问的沟通风格、擅长话题、典型客户类型、近期表现。
正文要引用至少 2 条 raw audio 作为证据，比如：

> 张三在「价格异议」话题处理上有稳定模式（见 [[raw/audio/100-张三/2026-05-09/12345]]
> 第 8 分钟），通常先共情再给方案……

### 3.2 `customers/{customerName}.md` — 客户画像

```yaml
---
layer: customer
customer_name: 王总
tags: [客户]

# 跟客户对接的顾问（可能不止一位）
consultants:
  - "[[consultants/100-张三]]"
audio_references:                       # 至少 2 个
  - "[[raw/audio/100-张三/2026-05-09/12345]]"
  - "[[raw/audio/100-张三/2026-05-12/12389]]"
related_topics:
  - "[[topics/户型疑虑]]"
  - "[[topics/价格异议]]"

# 跟进状态（业务字段，可选）
status: 跟进中                          # 跟进中 / 已成交 / 已流失
first_contact: "2026-05-09"
last_contact:  "2026-05-12"
audio_count:   3
---
```

正文：客户兴趣点、决策路径、关心议题、跟进历史时间线。

### 3.3 `topics/{topic}.md` — 话题/场景

```yaml
---
layer: topic
topic: 户型疑虑
tags: [话题, 销售场景]

# 跟话题相关的录音 + 客户 + 顾问处理范式
audio_references:                       # 至少 2 个
  - "[[raw/audio/100-张三/2026-05-09/12345]]"
  - "[[raw/audio/200-李四/2026-05-10/12349]]"
customers:
  - "[[customers/王总]]"
consultants:
  - "[[consultants/100-张三]]"
related_scripts:
  - "[[scripts/户型介绍]]"
---
```

正文：这个话题客户常问的具体问题、销售常用回应、最佳实践。

### 3.4 `scripts/{scriptName}.md` — 可复用话术

```yaml
---
layer: script
script_name: 户型介绍
tags: [话术, 销售话术]

source_topics:                          # 这条话术从哪些话题抽象来
  - "[[topics/户型疑虑]]"
source_audios:                          # 至少 2 个实际录音作为出处
  - "[[raw/audio/100-张三/2026-05-09/12345]]"
  - "[[raw/audio/100-张三/2026-05-12/12389]]"
contributors:                           # 哪些顾问贡献了这个话术
  - "[[consultants/100-张三]]"
---
```

正文：完整可复用的话术模板，分段写"开场 / 引导 / 异议处理 / 收尾"。引用
实际录音片段作为证据。

---

## 5. Layer 3 — index / log / SCHEMA

每个项目独立一套 Layer 3 文件，都在 `wiki/projects/{projectId}-{projectName}/`
根下：

| 文件 | 作用 | 谁维护 |
| --- | --- | --- |
| `index.md` | 本项目索引：entity / concept 名 → wikilink + 出现次数 | ingest 每次跑完追加新条目 |
| `log.md` | 本项目增量同步日志：每次 ingest 写一行（时间 + 新增页数 + 跳过数） | ingest 每次跑完 append 一行 |
| `SCHEMA.md` | 本项目稳定词表：话题分类 / 标签词汇 / 话术分类 | **人**维护，ingest 只读 |

### SCHEMA.md 词表结构（示例）

```markdown
# wangxiaobao audio wiki schema

## 话题词表（topics/）
- 户型疑虑
- 价格异议
- 周末看房
- 物业咨询
- 学区房
- ...

## 话术词表（scripts/）
- 破冰寒暄
- 户型介绍
- 成交逼定
- 异议处理
- 客户关怀
- ...

## 标签词表（tags 字段值）
- 置业顾问
- consultant
- 客户
- 话题
- 销售场景
- 话术
- 销售话术
```

ingest 阶段创建 Layer 2 页时：
- `tags` 字段值必须从 SCHEMA.md「标签词表」选
- `topic` / `script_name` 字段值必须从对应词表选
- 遇到词表外的新词 → **不要私自创建**，先提示用户加进 SCHEMA.md 再 ingest

---

## 6. Wikilinks 规则

继承 [`llm-wiki-ingest.md`](llm-wiki-ingest.md) 的"每页至少 2 个 wikilinks"约束。
针对本业务，**最小连接图**：

| 页类型 | 必须 wikilink 到 |
| --- | --- |
| `raw/audio/.../*.md` | 1 个 `parent_consultant` |
| `consultants/*.md` | ≥ 2 个 `recent_audios` 或 `top_customers` |
| `customers/*.md` | ≥ 1 个 `consultants` + ≥ 2 个 `audio_references` |
| `topics/*.md` | ≥ 2 个 `audio_references` + ≥ 1 个 `customers` 或 `consultants` |
| `scripts/*.md` | ≥ 1 个 `source_topics` + ≥ 2 个 `source_audios` |

raw/ 是 Layer 1 不可变，wikilink 只指向 Layer 2，**不被其他页指向（除了
顾问页的 `recent_audios`）** —— 这样删一条 raw 不会破坏 Layer 2 网络。

---

## 7. ingest 入库流程（业务版）

通用 ingest 流程见 [`llm-wiki-ingest.md`](llm-wiki-ingest.md)。本业务的具体
落地步骤：

所有路径都在当前项目目录下（`wiki/projects/{projectId}-{projectName}/`）：

1. 从 CLI active-project state（`~/.xiaobao/active-project.json`）
   读 `projectId` / `projectName` → 定位项目目录
2. 读项目目录下 `SCHEMA.md`（拿到话题/话术/标签词表）
3. 读项目目录下 `index.md`（拿到已存在的 entity/concept 列表）
4. 读最近的项目目录下 `log.md`（拿到上次 ingest 截止时间）
5. 扫描项目目录下 `raw/audio/` 下**新于 log 截止时间**的所有录音文件
6. 对每条 raw audio：
   - 从 frontmatter 拿 `consultant_user_id` → 找/建 `consultants/<id>-<name>.md`
   - 从正文识别 **客户名 / 主要话题** → 找/建 `customers/...` + `topics/...`
   - 如果话题有清晰可复用话术 → 找/建 `scripts/...`
   - 4 层之间建立 wikilinks
7. 更新项目目录下 `index.md`：新建的 entity / concept 加进索引
8. 写项目目录下 `log.md` 一行：`2026-05-12T14:30:00 ingest: new=12 update=8 skip=3`

**绝不要**跨项目读写——一次 ingest 只动一个项目的目录。

---

## 8. 常见错误与排查

- **创建 Layer 2 页时 tag 不在 SCHEMA.md 词表** — 不要私自新建词。先 prompt
  用户：「这个 tag/topic/script 名称 SCHEMA.md 里没有，要加进词表后再 ingest 吗？」
- **同一客户两个顾问对接 → customers 页冲突** — 一个 customer 文件，
  `consultants` 列表里两个 wikilink；按时间线写跟进历史，不要分两个文件
- **顾问改名** — `consultants/{userId}-{oldName}.md` 改成
  `consultants/{userId}-{newName}.md`（git mv 保留历史），所有指向它的
  wikilink 用编辑器批量替换。**不要**两个文件并存
- **wikilinks 数量不够** — Layer 2 页强约束 ≥ 2 个 wikilinks。如果 ingest
  阶段确实拿不到 2 个有效引用，**先不创建这页**，把这条 raw audio 留到下次
  ingest 累积够引用再建（避免"孤儿页"污染知识图）
