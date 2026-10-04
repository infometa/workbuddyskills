---
name: wangxiaobao-customer-resistance-query
version: 0.1.0
description: "旺小宝客户抗性点（resistance）分页查询 —— AI 在客户对话里抽出的客户疑虑 / 反对 / 不满标签（价格高 / 户型差 / 地段差 / 装修不满 等）。schema 与 focus 镜像，仅底层 MV 表不同。按 visit/customer/audio ID 列表 + 一级/二级分类模糊 + 来访时间窗组合过滤，排序固定 visit_time DESC。每条 tag 带 customer + userInfo + audio + value_str + text_fragment。只读、不写文件。高频命令: xiaobao-cli resistance list [--visit-ids a,b] [--customer-ids a,b] [--audio-ids a,b] [--category <kw>] [--classification <kw>] [--from <date>] [--to <date>] [--page N] [--size N]。何时用：用户问客户抗性/客户疑虑/客户反对/客户嫌/客户担心/不满意/价格抗性/户型抗性/地段抗性/TOP 抗性原因/销售应对话术；用户想看销售应该重点准备哪些应对话术。注：客户名→wang_id 先用 xiaobao-cli customer list 反查；问关注/兴趣/偏好走 focus-query；问完整录音文本走 audio-query。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli resistance --help"
---

# 旺小宝客户抗性点查询

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli resistance list` 查 AI 抽出的客户抗性点标签。
跟关注点 skill 镜像，差别就是底层走 `mv_open_customer_resistance` 表 ——
**抗性 = 客户疑虑 / 反对 / 不满**（关注 = 客户主动表达的关心）。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：命令内部自动读，缺失返回 `NO_ACTIVE_PROJECT`
- **数据权限隔离**：按当前用户授权可见顾问范围过滤（普通顾问看自己 /
  团队长看团队 / 项目管理员看全项目）
- LocalDateTime 格式：`yyyy-MM-dd HH:mm:ss`（空格分隔），CLI 自动转
- **不要**写文件、出报告

---

## 快速索引：意图 → 工具

| 用户意图                             | 命令                            | 关键参数                           |
| ------------------------------------ | -------------------------------------- | ---------------------------------- |
| 列时段内全部抗性点                   | `xiaobao-cli resistance list`     | `--from` / `--to`              |
| 看某客户的抗性                       | `xiaobao-cli customer list` → `xiaobao-cli resistance list` | `--customer-ids <wang_id>` |
| 看某次到访的抗性                     | `xiaobao-cli resistance list`     | `--visit-ids <visit_id>`           |
| 看某条录音的抗性                     | `xiaobao-cli resistance list`     | `--audio-ids <audio_id>`           |
| 按分类找（一级）                     | `xiaobao-cli resistance list`     | `--category 价格` 等              |
| 按分类找（二级）                     | `xiaobao-cli resistance list`     | `--classification 价格因素`        |
| 估算总数                             | `xiaobao-cli resistance list`     | `--page 1 --size 1`，只读 `total`   |

---

## 核心约束

### 1. 客户名 → wang_id 反查

用户说"屈哥的抗性"——先调 `xiaobao-cli customer list { customerName: "屈哥" }` 拿到
`--customer-id`，再传 `--customer-ids` 数组。

### 2. 分类模糊：一级 + 二级二选一或同时用

```
category 一级常见值：户型 / 价格 / 环境 / 教育 / 交通 / 商业配套 / 装修 / 其他
classification 二级常见值：户型因素 / 价格因素 / 环境因素 / ... / 位置因素 / 发展因素
```

抗性点最常见是 **"价格因素"** —— 价格高、超预算、车位贵、维修基金贵等。
其次 **"户型因素"**（房间小 / 朝向不好 / 楼间距）和 **"位置因素"**（偏远 / 噪音）。

### 3. 时间窗：用户没明确说就推断

| 用户说法     | fromDate / toDate                                |
| ------------ | ------------------------------------------------ |
| "今天抗性"   | 今天 00:00:00 / 明天 00:00:00                    |
| "本周抗性"   | 周一 00:00:00 / 今天 23:59:59                    |
| "5 月份"     | 2026-05-01 00:00:00 / 2026-06-01 00:00:00        |

### 4. 响应字段重点

跟 focus 接口**完全镜像**（共享 `CustomerTagPageResp`），只是返回的是抗性点。

```jsonc
{
  "code": "0",
  "data": {
    "page": 1, "size": 10, "total": 89,
    "content": [
      {
        "id": "...",
        "visitId":   "510395382098829312",
        "audioId":   "1920802945878642689",
        "customerId": "510395381809422336",
        "textFragment": "车位都要十来万？",
        "startOffset": 2778940,
        "endOffset":   2780380,
        "keyStr":   "车位价格贵且与房价捆绑优惠",
        "valueStr": "客户觉得车位贵，且与房价优惠捆绑，如'车位都要十来万？...'",
        "category":       "价格因素",
        "classification": "价格因素",
        "visitTime": "2025-05-09 18:09:01",
        "customer":  { /* 客户信息 */ },
        "userInfo":  { /* 顾问信息 */ },
        "audio":     { /* 录音简要 + 签名 fileUrl */ }
      }
    ]
  }
}
```

### 5. 渲染给用户时

- **必显**：keyStr（抗性标题）+ valueStr（详细说明）+ visitTime + 客户名
- **可选**：category（分类标签，常见是"价格因素"/"户型因素"）+ textFragment（原文，省略号截断）
- **链接**：要听原录音给 `audio.fileUrl`

### 6. TOP 抗性原因聚合

用户问"我们项目客户最大的抗性是什么"——拉一页 `size: 100`，agent 后处理按
`--category` 聚合输出："5 月共 89 条抗性：价格因素 42 条（47%）/ 户型因素 23 条 /
环境因素 12 条 / ..."。

---

## 使用场景示例

### 场景 1：本月客户最主要的抗性

```bash
xiaobao-cli resistance list --from "2026-05-01 00:00:00" --to "2026-06-01 00:00:00" --page 1 --size 100
```

按 category 聚合 → "本月 89 条抗性中价格类占 47%，户型 26%，..."。

### 场景 2：价格抗性的具体说法

```bash
xiaobao-cli resistance list --category 价格 --page 1 --size 20
```

列出 20 条价格抗性原文，让 LLM 帮销售总结"客户主要嫌车位价高、楼层差价大、
南北向价差大..."。

### 场景 3：屈哥这次到访都嫌什么

```bash
xiaobao-cli resistance list --visit-ids 510395382098829312 --page 1 --size 50
```

### 场景 4：户型 + 时间窗组合

```bash
xiaobao-cli resistance list --category 户型 --from "2026-05-01 00:00:00" --to "2026-06-01 00:00:00"
```

回复："5 月户型抗性 23 条，主要集中在'房间小'（11）/'朝向不好'（5）/'楼间距'（4）..."。

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 跑 `wangxiaobao-switch-project` skill
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登
- **`total: 0`** — 过滤条件没匹配 / 该时段没数据 / 当前用户授权范围内没匹配的接待顾问
- **抗性点 vs 关注点**：跟 LLM 强调"抗性"是负面（疑虑/反对），"关注"是中性偏正
  （主动关心）；用户说"嫌弃 / 担心 / 不满"走抗性，"在意 / 关心 / 偏好"走关注
- **category 模糊命中过多** — 加 classification 二级分类收敛
