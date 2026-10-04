---
name: wangxiaobao-customer-query
version: 0.1.0
description: "旺小宝客户画像分页查询：按 置业顾问 / 客户姓名 / 手机号 / 画像关键词（dynamic_tags JSON LIKE） / 最后来访时间窗 维度过滤，排序固定 last_visit_time DESC。只读、不写文件、无副作用。高频命令: xiaobao-cli customer list [--user-id <id>] [--user-name <n>] [--customer-name <n>] [--customer-phone <p>] [--portrait <kw>] [--from <date>] [--to <date>] [--page N] [--size N]。何时用：用户问客户列表/我的客户/高意向客户/近期来访客户/某顾问名下的客户/某顾问这周新增哪些客户/姓张的客户/手机号 138 的客户/5 月份来过的客户；按画像找如高意向/价格敏感/看四房用 --portrait。注：顾问名→user-id 先用 xiaobao-cli consultant list 反查；要来访记录走 visit-query；要录音元数据走 audio-query。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli customer --help"
---

# 旺小宝客户分页查询

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli customer list` 查当前激活项目的客户画像列表。
零副作用，鼓励放心调用。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：命令内部自动读，如果返回 `NO_ACTIVE_PROJECT` 就跑
  `wangxiaobao-switch-project` skill
- **数据权限隔离**：后端按"当前用户授权可见的顾问范围"过滤（普通顾问看自己 /
  团队长看团队 / 项目管理员看全项目）。当前用户无权访问的顾问名下客户**看不到**——
  这不是 bug
- LocalDateTime 格式：`yyyy-MM-dd HH:mm:ss`（空格分隔），CLI 自动转 ISO
- **不要**写文件、出报告

---

## 快速索引：意图 → 工具

| 用户意图                       | 命令                | 关键参数                           |
| ------------------------------ | -------------------------- | ---------------------------------- |
| 列全部客户（最近来访的在前）   | `xiaobao-cli customer list`   | `--page` / `--size`                    |
| 看某顾问名下客户               | `xiaobao-cli consultant list` → `xiaobao-cli customer list` | `--user-id <反查的 id>` |
| 按客户画像找                   | `xiaobao-cli customer list`   | `--portrait 高意向` 等            |
| 按客户姓名 / 手机号模糊        | `xiaobao-cli customer list`   | `--customer-name` / `--customer-phone`   |
| 按最后来访时间筛               | `xiaobao-cli customer list`   | `--from` / `--to`              |
| 估算总数                       | `xiaobao-cli customer list`   | `--page 1 --size 1`，只读 `total`   |

---

## 核心约束

### 1. 按顾问筛 —— 先反查 user-id，不要硬猜

用户说"张三的客户"——**不要**直接传 `userName: "张三"`（虽然支持但是 LIKE 模糊）。
正确做法：

1. 调 `xiaobao-cli consultant list` 拿当前授权范围内的顾问列表
2. 找 `userName === "张三"` 的 `--user-id`
3. 调 `xiaobao-cli customer list { userId: <张三的 userId> }` 精确过滤

如果 list-consultants 里**找不到张三**——说明当前用户没权限看张三名下数据，
告诉用户"当前账号无权访问销售『张三』"，不要再硬试。

### 2. portrait 单关键词，越短越宽

后端在 `dynamic_tags` JSON 文本上 `LIKE '%xxx%'`。所以：

- `--portrait 高意向` 命中 `{"高意向客户":"高意向客户"}` / `{"AI意向判定":"高意向"}` 等
- `--portrait 价格` 命中 `{"抗性点":"价格"}` 等
- 不要传完整 JSON / key=value 形式（不支持，反而匹不到）

### 3. 时间窗：用户没明确说就推断

| 用户说法     | fromDate / toDate                                |
| ------------ | ------------------------------------------------ |
| "今天来访"   | 今天 00:00:00 / 明天 00:00:00                    |
| "本周"       | 周一 00:00:00 / 今天 23:59:59                    |
| "上周"       | 上周一 / 本周一                                  |
| "5 月份"     | 2026-05-01 00:00:00 / 2026-06-01 00:00:00        |
| "近一个月"   | 30 天前 / now                                    |

用户明确给时间则按字面用。

### 4. 分页：page 从 **1** 开始

PageParam 默认 `--page 1 --size 10`。传 `page: 0` 报错。`--size` 上限 500。

### 5. 响应外层

`xiaobao-cli customer list` 返回：

```jsonc
{
  "code": "0",
  "msg":  "success",
  "data": {
    "page": 1, "size": 10, "total": 47,
    "content": [
      {
        "customerId":   "1685535452481236993",
        "customerName": "屈哥",
        "customerPhone": "173****7325",
        "intentLevel":   "A",
        "aiIntentLevel": "A",
        "lastVisitTime": "2023-07-30 14:01:03",
        "userId":   270078834689187840,
        "userName": "兰鸿建",
        "userInfo": { /* 顾问详情 */ },
        "dynamicTags": { "高意向客户": "高意向客户", "抗性点": "配套", ... }
      }
    ]
  }
}
```

CLI 又包一层 `{ status, ok, data }` —— 取数据用 `resp.data.data.content`。

---

## 使用场景示例

### 场景 1：列我能看到的高意向客户

```bash
xiaobao-cli customer list --portrait 高意向 --page 1 --size 20
```

渲染：

```
共 12 位高意向客户（最近来访在前）:
1. 屈哥 · 173****7325 · 顾问兰鸿建 · 最后来访 2023-07-30
2. 曹女士 · 186****1938 · 顾问兰鸿建 · 最后来访 2023-07-30
...
```

### 场景 2：陈平名下的客户

```bash
# step 1: 反查陈平的 user-id
xiaobao-cli consultant list

# step 2: 假设找到陈平的 userId = 270078836362715136
# step 3: 用 --user-id 过滤
xiaobao-cli customer list --user-id 270078836362715136 --page 1 --size 20
```

### 场景 3：5 月来访的客户里抗性是价格的

```bash
xiaobao-cli customer list --portrait 价格 --from "2026-05-01 00:00:00" --to "2026-06-01 00:00:00"
```

### 场景 4：估算总数

```bash
xiaobao-cli customer list --page 1 --size 1
```

回复：「当前授权范围下共 1247 位客户」。

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 跑 `wangxiaobao-switch-project` skill
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登
- **`total: 0`** — 时间窗口 / 过滤条件没匹配到，**或**当前用户授权范围为空
  （新人顾问刚入职 / 团队成员被移走等）
- **顾问名找不到** — 不在当前用户授权可见范围内；不要硬调 list_customers 试
- **画像匹配不准** — portrait 太长 / 太具体导致 LIKE 不命中；改短关键词
