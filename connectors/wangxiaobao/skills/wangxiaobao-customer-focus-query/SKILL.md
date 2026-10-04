---
name: wangxiaobao-customer-focus-query
version: 0.1.0
description: "旺小宝客户关注点（focus）分页查询 —— AI 在客户对话里抽出的客户主动表达的关心标签（学区 / 户型 / 价格优惠 / 配套等）。按 visit/customer/audio ID 列表（IN） + 一级分类（category LIKE） + 二级分类（classification LIKE） + 来访时间窗组合过滤，排序固定 visit_time DESC。每条 tag 已带 customer + userInfo + audio + value_str（详细说明） + text_fragment（录音原文片段）。只读、不写文件。高频命令: xiaobao-cli focus list [--visit-ids a,b] [--customer-ids a,b] [--audio-ids a,b] [--category <kw>] [--classification <kw>] [--from <date>] [--to <date>] [--page N] [--size N]。何时用：用户问客户关注点/客户最在意什么/客户关心什么/客户问得最多/某客户的关注点/某次到访或某条录音里的关注点/户型 价格 学区 交通 商业配套类关注点/5 月份的关注点。注：客户名→wang_id 先用 xiaobao-cli customer list 反查；问抗性/疑虑/反对走 resistance-query；问完整录音文本走 audio-query。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli focus --help"
---

# 旺小宝客户关注点查询

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli focus list` 查 AI 抽出的客户关注点标签。
跟抗性点 skill 镜像，差别就是底层走 `mv_open_customer_focus` 表。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：命令内部自动读，缺失返回 `NO_ACTIVE_PROJECT`
- **数据权限隔离**：按当前用户授权可见顾问范围过滤（普通顾问看自己 /
  团队长看团队 / 项目管理员看全项目）
- LocalDateTime 格式：`yyyy-MM-dd HH:mm:ss`（空格分隔），CLI 自动转
- **不要**写文件、出报告

---

## 快速索引：意图 → 工具

| 用户意图                             | 命令                       | 关键参数                           |
| ------------------------------------ | --------------------------------- | ---------------------------------- |
| 列时段内全部关注点                   | `xiaobao-cli focus list`     | `--from` / `--to`              |
| 看某客户的关注点                     | `xiaobao-cli customer list` → `xiaobao-cli focus list` | `--customer-ids <wang_id>` |
| 看某次到访的关注点                   | `xiaobao-cli focus list`     | `--visit-ids <visit_id>`           |
| 看某条录音的关注点                   | `xiaobao-cli focus list`     | `--audio-ids <audio_id>`           |
| 按分类找（一级）                     | `xiaobao-cli focus list`     | `--category 户型` 等              |
| 按分类找（二级）                     | `xiaobao-cli focus list`     | `--classification 户型因素`        |
| 估算总数                             | `xiaobao-cli focus list`     | `--page 1 --size 1`，只读 `total`   |

---

## 核心约束

### 1. 客户名 → wang_id 反查

用户说"屈哥的关注点"——先调 `xiaobao-cli customer list { customerName: "屈哥" }`
拿到 `--customer-id`（= wang_id），再传给 `--customer-ids` 数组（即使只有一个也用数组）。

### 2. 分类模糊：一级 + 二级二选一或同时用

```
category 一级常见值：户型 / 价格 / 环境 / 教育 / 交通 / 商业配套 / 装修 / 其他
classification 二级常见值：户型因素 / 价格因素 / 环境因素 / ... / 位置因素 / 发展因素
```

模糊关键词越短越宽：`--category 户型` 同时命中 "户型因素" 和别的含 "户型" 的分类。

### 3. 时间窗：用户没明确说就推断

| 用户说法     | fromDate / toDate                                |
| ------------ | ------------------------------------------------ |
| "今天关注点" | 今天 00:00:00 / 明天 00:00:00                    |
| "本周关注点" | 周一 00:00:00 / 今天 23:59:59                    |
| "5 月份"     | 2026-05-01 00:00:00 / 2026-06-01 00:00:00        |
| "最近一个月" | 30 天前 / now                                    |

### 4. 响应字段重点

```jsonc
{
  "code": "0",
  "data": {
    "page": 1, "size": 10, "total": 47,
    "content": [
      {
        "id": "507495633116995584",                // tag 自身 ID
        "visitId": "507016570438942720",
        "audioId": "507494047338729472",
        "customerId": "507016570019512320",
        "textFragment": "新规户型我看了他们的那个四房的，还不错啊，",  // 录音原文片段
        "startOffset": 945120,                     // 在录音中的起始毫秒
        "endOffset":   949840,
        "keyStr":   "对盛世禧悦户型感兴趣",          // 简短描述
        "valueStr": "客户表示看了盛世禧悦的新规四房户型觉得不错...",  // 详细说明
        "category":       "户型因素",                // 一级
        "classification": "户型因素",                // 二级
        "visitTime": "2025-04-30 10:22:28",
        "customer": {                              // 批量补全
          "customerId": "507016570019512320",
          "customerName": "屈哥",
          "customerPhone": "173****7325",
          "intentLevel": "A",
          ...
        },
        "userInfo": { /* 接待顾问详情 */ },
        "audio": {                                 // 录音简要 + 签名 fileUrl
          "audioId": 507494047338729472,
          "fileId":  "507494045212213248",
          "startTime": "2025-04-30 10:22:50",
          "duration":  2263,
          "fileUrl":   "https://oss.../...?sign=..."
        }
      }
    ]
  }
}
```

CLI 又包一层 → 渲染用 `resp.data.data.content`。

### 5. 渲染给用户时只展示核心

- **必显**：keyStr（标题）+ valueStr（详细说明）+ visitTime + 客户名
- **可选**：category（分类标签）+ textFragment（原文，省略号截断）
- **链接**：如果用户要听原录音，给 `audio.fileUrl`（注意 18000 秒过期）

---

## 使用场景示例

### 场景 1：本月客户最在意什么

```bash
xiaobao-cli focus list --from "2026-05-01 00:00:00" --to "2026-06-01 00:00:00" --page 1 --size 50
```

后处理：按 `--category` 聚合 → "5 月份 87 条关注点：户型因素 28 条 / 价格因素 19 条 / ..."。

### 场景 2：屈哥本次到访的关注点

```bash
# step 1: 反查 wang_id（如果只知名字）
xiaobao-cli customer list --customer-name 屈哥

# step 2: 拿到 customerId = 507016570019512320，用 --customer-ids 过滤
xiaobao-cli focus list --customer-ids 507016570019512320 --page 1 --size 20
```

### 场景 3：户型相关关注点

```bash
xiaobao-cli focus list --category 户型 --page 1 --size 30
```

### 场景 4：特定录音里的关注点

```bash
xiaobao-cli focus list --audio-ids 507494047338729472 --page 1 --size 50
```

渲染：列出该录音里 AI 抽出的所有关注点，按 startOffset 升序展示原文 + 描述。

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 跑 `wangxiaobao-switch-project` skill
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登
- **`total: 0`** — 过滤条件没匹配 / 该时段没数据 / 当前用户授权范围内没匹配的接待顾问
- **传入的 ID 找不到对应数据** — 数据权限隔离把不属于授权顾问的 tag 过滤掉了；
  这是预期行为，不是 bug
- **category 模糊命中过多** — 加 classification 二级分类收敛
