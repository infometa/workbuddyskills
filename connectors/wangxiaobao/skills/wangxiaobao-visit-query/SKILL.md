---
name: wangxiaobao-visit-query
version: 0.1.0
description: "旺小宝客户来访分页查询：按 客户 ID / 客户姓名（模糊触发后端 JOIN）/ 来访时间窗 过滤，排序固定 visit_time DESC。每条 visit 直接带 audios 录音列表（含 audioId / fileId / startTime / duration / 签名 fileUrl），问这次来访打了几条录音 / 录音多长 / fileUrl 时不必再调 audio list。只读、不写文件、无副作用。高频命令: xiaobao-cli visit list [--customer-id <id>] [--customer-name <n>] [--from <date>] [--to <date>] [--page N] [--size N]。何时用：用户问今天到访/本周来访列表/最近来访/某客户最近几次来访/上周哪些客户来访/姓张客户什么时候来过/某次到访打了几条录音/录音 fileUrl/盘客完成没；任何看到访名单/接待记录/话术命中的开放式查询。注：customer-id 比 customer-name 精确，先用 xiaobao-cli customer list 反查 wang_id；要客户画像走 customer-query；要录音元数据走 audio-query。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli visit --help"
---

# 旺小宝来访分页查询

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli visit list` 查当前激活项目的来访记录。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：命令内部自动读，缺失返回 `NO_ACTIVE_PROJECT`
- **数据权限隔离**：跟客户接口一样，按当前用户授权可见顾问范围过滤
- LocalDateTime 格式：`yyyy-MM-dd HH:mm:ss`（空格分隔），CLI 自动转
- **不要**写文件、出报告

---

## 快速索引：意图 → 工具

| 用户意图                       | 命令             | 关键参数                                |
| ------------------------------ | ----------------------- | --------------------------------------- |
| 列时间窗内的全部来访           | `xiaobao-cli visit list`   | `--from` / `--to`                   |
| 看某客户的来访历史             | `xiaobao-cli customer list` → `xiaobao-cli visit list` | `--customer-id 反查的 wang_id` |
| 按客户名字模糊找来访           | `xiaobao-cli visit list`   | `--customer-name 张`                    |
| **看某次来访的录音详情**       | `xiaobao-cli visit list`   | 直接读返回里的 `audios[]`（含 fileUrl） |
| 估算总数                       | `xiaobao-cli visit list`   | `--page 1 --size 1`，只读 `total`        |

---

## 核心约束

### 1. 客户名 vs 客户 ID —— 优先 ID，更准更快

用户说"李女士最近几次来访"——**优先**走两步：

1. 调 `xiaobao-cli customer list { customerName: "李女士" }` 反查到 `--customer-id`
2. 调 `xiaobao-cli visit list { customerId: <wang_id> }` 拿来访历史

直接传 `--customer-name` 也能用（后端 JOIN customer_profile 模糊匹配），但：
- 同名客户可能有多个（重名 "李女士"），结果混在一起不好辨认
- JOIN 慢于纯 visit 表查询

### 2. 时间窗：用户没明确说就推断

| 用户说法     | fromDate / toDate                                |
| ------------ | ------------------------------------------------ |
| "今天到访"   | 今天 00:00:00 / 明天 00:00:00                    |
| "本周来访"   | 周一 00:00:00 / 今天 23:59:59                    |
| "上周末"     | 上周六 00:00:00 / 本周一 00:00:00                |
| "5 月份"     | 2026-05-01 00:00:00 / 2026-06-01 00:00:00        |
| "最近 3 次"  | 不传时间窗，只看 `content[]` 前 3 条             |

### 3. 分页：page 从 **1** 开始；size 上限 500

跟其他接口一样。

### 4. 响应字段重点

```jsonc
{
  "code": "0",
  "data": {
    "page": 1, "size": 10, "total": 23,
    "content": [
      {
        "visitId":   "...",
        "customerId": "1685535452481236993",      // = wang_id，可传回 customers 查
        "visitTime": "2023-07-30 14:01:03",
        "visitCount": 1,                           // 第几次到访
        "visitTimer": 1439184,                     // 来访总秒数
        "audioCount": 3,                           // 关联录音条数（= audios.length）
        "audios": [                                // ★ 录音详情列表，按 startTime 升序
          {
            "audioId":   9001,
            "fileId":    "abc",
            "startTime": "2023-07-30 14:01:15",
            "endTime":   "2023-07-30 14:08:42",
            "duration":  447,                      // 秒
            "fileSize":  3145728,
            "hasValid":  1,                        // 0 无效 / 1 有效
            "status":    4,                        // 0 转存中/1 转文本/2 待分析/3 分析中/4 完成
            "userId":    270078834689187840,
            "fileUrl":   "https://oss.../abc?sign=..."  // 18000 秒过期
          }
        ],
        "userId": 270078834689187840,
        "userName": "兰鸿建",                       // 实际接待顾问
        "belongUserId":   ...,
        "belongUserName": "兰鸿建",                // 客户归属顾问（可能跟接待不同）
        "userInfo": { /* 顾问详情 */ },
        "pankeStatus": "已完成",                    // 盘客状态
        "isPankeCompleted": 1,
        "requireSpeechTotal": 8, "requireSpeechHit": 5,
        "salesSpeechTotal":   12, "salesSpeechHit": 9
      }
    ]
  }
}
```

CLI 又包一层 → `resp.data.data.content`。

`requireSpeechHitDetail` / `salesSpeechHitDetail` 是 JSON 文本，**默认不展示给用户**
（除非用户明确问"具体哪条话术命中了"）。

### 5. 接待 vs 归属：解释差异

- `userId / userName` = **实际接待**（这次来访是谁陪同的）
- `belongUserId / belongUserName` = **客户归属**（客户档案里登记的归属销售）

正常情况两者一致；不一致时可能是：
- 销售 A 不在岗，同事 B 帮忙接待 A 的客户
- 客户重新分配过

用户问"张三接待了几个"——按 `userId == 张三`；问"张三名下客户来访"——按 `belongUserId == 张三`
（**但本 命令当前不支持按 belongUserId 过滤**，需先用 customers 反查再 customerId 过滤）。

---

## 使用场景示例

### 场景 1：今天到访列表

```bash
xiaobao-cli visit list --from "2026-05-13 00:00:00" --to "2026-05-14 00:00:00"
```

渲染：

```
今天共 18 次到访（按时间倒序）:
1. 屈哥 · 14:01 · 接待:兰鸿建 · 第 1 次 · 12 分 · 录音 3
2. 曹女士 · 13:45 · 接待:陈平 · 第 2 次 · 25 分 · 录音 2
...
```

### 场景 2：李女士最近 3 次来访

```bash
# step 1: 反查 wang_id
xiaobao-cli customer list --customer-name 李女士 --size 20

# step 2: 假设找到 customerId = 270072120829026305
xiaobao-cli visit list --customer-id 270072120829026305 --page 1 --size 3
```

### 场景 3：上周末来访高峰

```bash
xiaobao-cli visit list --from "2026-05-10 00:00:00" --to "2026-05-12 00:00:00" --page 1 --size 50
```

后处理：按 hour 聚合 → 报告"周日下午 14-16 点是峰值"。

### 场景 4：用客户名直接模糊

```bash
# 不知道具体客户 ID，先用名字模糊
xiaobao-cli visit list --customer-name 张 --from "2026-05-01 00:00:00" --size 20
```

回复："姓张的客户 5 月来访共 8 次，分布在 3 位客户：张先生(133****0692) 来 3 次..."

### 场景 5：直接看某次到访的录音详情

```bash
xiaobao-cli visit list --customer-id 1685535452481236993 --page 1 --size 5
```

每条 visit 已带 `audios[]`，**不必再调** `xiaobao-cli audio list`：

```
屈哥 · 2023-07-30 14:01:03 · 接待:兰鸿建 · 12 分 · 3 条录音：
  1. audioId=9001 · 14:01:15 ~ 14:08:42 · 7 分 · 状态:分析完成
     fileUrl: https://oss.../abc?sign=...
  2. audioId=9002 · 14:09:00 ~ 14:11:30 · 2 分 · 状态:分析完成
  3. audioId=9003 · 14:12:00 ~ 14:15:30 · 3 分 · 状态:分析完成
```

> 想看某条录音的**转录文本**还是要单独调 `xiaobao-cli audio text`，
> `audios[]` 里只有元数据 + 签名 URL，没有 transcript。

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 跑 `wangxiaobao-switch-project` skill
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登
- **`total: 0`** — 时间窗内确实没数据，或当前用户授权范围内没有匹配的接待顾问
- **customerName 模糊但没匹到** — 客户名拼写差异（"李女士" vs "李小姐"）；
  改用 `xiaobao-cli customer list` 反查精确 customerId
- **接待顾问跟归属顾问不一致** — 正常业务情况（同事代接待），不是 bug；
  必要时跟用户解释
