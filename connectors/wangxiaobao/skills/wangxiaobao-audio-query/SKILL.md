---
name: wangxiaobao-audio-query
version: 0.1.0
description: "旺小宝录音只读查询：按时间窗 + 可选顾问过滤分页查录音元数据列表（audioId / fileId / startTime / duration / 销售 / 签名 fileUrl），或按 audioId 查单条转录文本（含 talkRatios 说话人占比 + texts 分段 ASR）。不写文件、不动游标，是 wangxiaobao-audio-wiki 的探查/抽样版。高频命令: xiaobao-cli audio list --from --to [--user-id <id>] [--user-id-list a,b,c] [--page N] [--size N]、xiaobao-cli audio text <audio-id>。何时用：用户说看看有哪些录音/查录音/列录音/某销售本周打了几个电话/抽样几条录音文本预览/估个量/看一眼录音；任何看一眼录音而不触发同步入库归档意图的场景。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli audio --help"
---

# 旺小宝录音查询

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

只读探查录音。**没有副作用**——不写 wiki / 不推游标，
所以用错也没成本，鼓励放心调用。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`，未登录 / 过期就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：tenant/project 由 命令内部从
  `~/.xiaobao/active-project.json` 读，调用方不需要传任何
  tenant/project 参数。如果 命令 返回 `error: 'NO_ACTIVE_PROJECT'`，
  让用户跑 `wangxiaobao-switch-project` skill 后再重试
- **绝不要**写文件、推游标。即使用户随口说"顺便存一下"也要拦：
  那是 `wangxiaobao-audio-wiki` 的事，本 skill 一旦写盘就破坏了"只读"承诺
- LocalDateTime 字段格式：`yyyy-MM-dd HH:mm:ss`（**空格**分隔，不带时区）。
  pierre 框架的 Jackson 反序列化只认这个格式；带 `T` 或 `+08:00` 会被 CLI
  容错处理，但传空格形式最稳

---

## 快速索引：意图 → 工具

| 用户意图               | 命令                | 关键参数                                  |
| ---------------------- | -------------------------- | ----------------------------------------- |
| 列某时段所有录音元数据 | `xiaobao-cli audio list`       | `--from` / `--to`                     |
| 列某销售的录音         | `xiaobao-cli audio list`       | `+ --user-id <uid>`（多个销售用 `--user-id-list`） |
| 反查销售 user-id       | `xiaobao-cli consultant list` | 无参（拿当前用户授权范围内的所有顾问）   |
| 看总数 / 估个量        | `xiaobao-cli audio list`       | `--page 1 --size 1`，只读 `total`          |
| 翻页继续看             | `xiaobao-cli audio list`       | `--page` 递增                               |
| 看某条录音转录预览     | `xiaobao-cli audio text`   | `--audio-id`（从 list_audio 结果拿）         |

**命令 参数里没有** `tenantId` / `projectId` —— CLI 内部从激活项目状态读。
如果还没激活过项目，跑 `wangxiaobao-switch-project` skill 先设一次。

---

## 核心约束

### 1. 时间范围：用户没明确说就推断合理窗口

当用户没给具体时间，按用户的话推断一个**能覆盖意图**的窗口，而不是默认拉
最近 N 天造成超时。常见映射：

| 用户说法       | 解析                                                  |
| -------------- | ----------------------------------------------------- |
| "今天的录音"   | from = 今天 00:00:00, to = now                        |
| "上周二的录音" | from = 上周二 00:00:00, to = 上周三 00:00:00          |
| "5 月份的"     | from = 2026-05-01 00:00:00, to = 2026-06-01 00:00:00  |
| "最近几条"     | from = now - 1 day, to = now, size = 10               |

用户明确给时间时直接用，不要二次猜测。

### 2. 分页：page 从 **1** 开始

PageParam 默认 `--page 1 --size 10`，传 `page: 0` 上游会报错。读 `total` +
当前 `page * size` 判断是否还有下一页，需要时翻页；浏览概览时第 1 页通常
够用。`--size` 上限 500（schema 已限制），预览展示建议 20。

### 3. 按销售筛选：先反查 user-id 再过滤

不带 `--user-id` / `--user-id-list` 就拉**所有人**的录音。要筛某个销售：

- 用户能直接给 user-id（数字）→ 用 `--user-id <id>`（单个）或
  `userIdList: [<id1>, <id2>, ...]`（多个）
- 只知道名字 → 调 **`xiaobao-cli consultant list`**（无参），拿到当前用户
  授权范围内的所有顾问（含 `--user-name` / `--user-id`），按名字 match 后取 `--user-id`
  传给 `xiaobao-cli audio list`

> 已弃用做法："先 list_audio 不带 filter，再扫 content[].saleName 反查"——
> 这种 hack 在录音数据稀疏 / 时间窗短时找不到目标销售。**改用
> `xiaobao-cli consultant list` 反查**，精确且快。

### 4. 单条文本预览：按需调，不要全量

`xiaobao-cli audio text` 一次拿一条录音的转录。**只在用户挑了具体某条之
后再调**，不要 list 完顺手把每条都 get_audio_text 一遍——那是 sync skill
的事。一次会话 1-3 条样本预览足够。

### 5. 响应外层结构

`xiaobao-cli audio list` 和 `xiaobao-cli audio text` 都返回 pierre 框架的
`Result<T>` 包：

```jsonc
{
  "code": "0",   // 业务状态码，"0" 是成功
  "msg":  "success",
  "data": { ... }  // 真正的 payload
}
```

list_audio 里 `data` 又是 `PageResult<AudioPageResp>`：
`{ page, size, total, content[] }`，所以**取元数据数组**要写
`resp.data.data.content`（命令 不展开 envelope，原样返回）。

---

## 使用场景示例

### 场景 1：列今天所有录音

```bash
xiaobao-cli audio list --from "2026-05-12 00:00:00" --to "2026-05-12 23:59:59" --page 1 --size 20
```

渲染给用户（按 startTime desc，audioId 必须显示——后面取文本要用）：

```
共 145 条录音（第 1/8 页）

1. 张三 · 2026-05-12 10:23:11 ~ 10:35:42（12 分钟） · audioId=12345
2. 李四 · 2026-05-12 09:50:00 ~ 10:02:15（12 分钟） · audioId=12344
3. 王五 · 2026-05-12 09:10:00 ~ 09:25:11（15 分钟） · audioId=12343
...
```

### 场景 2：估算"上周末打了几个电话"

只关心 `total`，第 1 页就够：

```bash
xiaobao-cli audio list --from "2026-05-10 00:00:00" --to "2026-05-12 00:00:00" --page 1 --size 1
```

回复：「周末两天共 23 条录音，主要集中在周日下午」。

### 场景 3：取某条录音的转录预览

用户从场景 1 列表里挑了序号 1（audioId=12345）：

```bash
xiaobao-cli audio text 12345
```

渲染：

```
audioId 12345 · 张三 · 2026-05-12 10:23:11（12 分钟）
说话人占比：销售 62% / 客户 38%

转录：
[10:23:15] 销售：您好张总，我是旺小宝的小张，咱们那个项目...
[10:23:22] 客户：嗯嗯你说
[10:23:25] 销售：周末方便过来看下样板间吗？
...
```

### 场景 4：按销售名字筛 —— 用 list-consultants 反查

用户说"张三本周打了几个"——只知道名字：

1. 调 `xiaobao-cli consultant list`（无参）→ 拿到 `[{ userId, userName, ... }, ...]`
2. 在结果里找 `userName === "张三"` 的 `--user-id`
3. 调 `xiaobao-cli audio list` 带 `--user-id <张三的 userId>` + 本周时间窗

```bash
# step 1: 反查张三的 user-id
xiaobao-cli consultant list

# step 2: 假设找到张三的 userId = 100
# step 3: 用 --user-id 过滤
xiaobao-cli audio list --from "2026-05-06 00:00:00" --to "2026-05-13 00:00:00" --user-id 100 --page 1 --size 20
```

如果 list-consultants 里**找不到张三**——说明当前登录用户没权限看张三
（不在管理范围内 / 不在团队里）。提示用户"当前账号无权访问销售『张三』"，
不要硬调 list-audio 假装搜（也会因 dataPermission 拿不到）。

---

## 常见错误与排查

- **`code: "400"` / `msg: "消息转换异常"`** — fromDate/toDate 格式不对。
  必须 `yyyy-MM-dd HH:mm:ss` 空格分隔，不带时区。
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登，重试一次。
- **`total: 0`** — 时间窗口里确实没数据，或激活的租户/项目错了。
  让用户跑 `wangxiaobao-switch-project` skill 确认或重新激活项目。
- **`error: 'NO_ACTIVE_PROJECT'`** — 还没设过激活项目。让用户跑
  `wangxiaobao-switch-project` skill 后重试本 skill。
- **翻页拿不到下一页** — 检查 `--page` 是不是从 1 开始（不是 0），
  `page * size > total` 时已经到末页。
- **`saleName` 是空的** — 上游 user info 缺失，可以只用 `--user-id` 标识，
  跟用户说"该录音的销售信息上游缺失"。
- **想"批量转文本看看"** — 拦住：批量取文本是 `wangxiaobao-audio-wiki`
  的事（带写文件 + 推游标），本 skill 设计上每次会话最多预览 1-3 条。
