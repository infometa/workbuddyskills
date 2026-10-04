---
name: wangxiaobao-visit-summary-query
version: 0.1.0
description: "旺小宝来访接待总结查询：按 客户ID(wang_id)/来访ID/时间窗(≤7天)/模板(template) 分页拉取每次来访的 AI 接待总结，按 客户×来访×总结项 三层嵌套（每个总结项 question=模板名、reply=该模板的总结答案）。--template 指定查询某个接待总结模板的结果（精确匹配模板名，非自由问句）。只读、不写文件、无副作用。高频命令: xiaobao-cli visit summary [--customer-id <id>] [--visit-id <id>] [--from <date>] [--to <date>] [--template <模板名>] [--page N] [--size N]。何时用：用户问某客户上次来访聊了啥/这次接待总结/接待要点/AI 怎么总结这次到访/某模板(如\"客户需求\"\"抗性分析\")的总结结果/最近来访的接待小结。注：visit-id 为空时 from/to 必填且窗口≤7天；customer-id 先用 xiaobao-cli customer list 反查 wang_id；要来访列表/录音走 visit-query；要录音原文走 audio-query。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli visit summary --help"
---

# 旺小宝来访接待总结查询

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli visit summary` 查当前激活项目里每次来访的 **AI 接待总结**（模板中心按模板生成的 question → reply）。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：命令内部自动读，缺失返回 `NO_ACTIVE_PROJECT`
- **数据权限隔离**：跟来访接口一样，按当前用户授权可见顾问范围过滤
- **时间窗 ≤ 7 天**：`visit-id` 为空时 `from`/`to` 必填，且窗口最长 7 天（超出后端自动截断为 to 往前 7 天）
- LocalDateTime 格式：`yyyy-MM-dd HH:mm:ss`（空格分隔），CLI 自动转
- **不要**写文件、出报告

---

## 快速索引：意图 → 工具

| 用户意图 | 命令 | 关键参数 |
| --- | --- | --- |
| 看某次来访的接待总结 | `xiaobao-cli visit summary` | `--visit-id <id>`（from/to 可省） |
| 看某客户近期来访总结 | `xiaobao-cli customer list` → `xiaobao-cli visit summary` | `--customer-id 反查的 wang_id` + 时间窗 |
| 看某时间窗内全部接待总结 | `xiaobao-cli visit summary` | `--from` / `--to`（≤7 天） |
| 只看某个模板的总结结果 | `xiaobao-cli visit summary` | `--template "客户需求"` |

---

## 核心约束

### 1. visit-id 优先；无 visit-id 时时间窗必填且 ≤ 7 天

- 已知具体某次来访 → `--visit-id`，可省略时间窗。
- 否则 `--from`/`--to` 必填；窗口跨度超 7 天会被后端截断（只保留靠近 `to` 的最后 7 天）。

| 用户说法 | fromDate / toDate |
| --- | --- |
| "今天来访总结" | 今天 00:00:00 / 明天 00:00:00 |
| "本周接待小结" | 周一 00:00:00 / 今天 23:59:59 |
| "最近一次来访" | 先 `visit list` 拿最近 visitId，再按 `--visit-id` 查 |

### 2. 客户 ID 用 customer list 反查

用户说"李女士上次来访聊了啥"——先 `xiaobao-cli customer list --customer-name 李女士` 反查 `wang_id`，再 `xiaobao-cli visit summary --customer-id <wang_id> --from ... --to ...`。

### 3. --template 是模板名精确匹配

`--template` 指定查询**某个接待总结模板**的结果（如 "客户需求"、"抗性分析"、"下一步跟进建议"），精确匹配模板名，不是自由问句。不传则返回该次来访的全部模板总结。要列出有哪些模板，先不带 `--template` 查一次，从返回的 `summaries[].question` 看模板名。

### 4. 按 visit_id 分页

`page` 从 1 开始，`size` 默认 10、**上限 100**。分页粒度是来访（visit_id），不是客户也不是总结条目。

### 5. 响应字段重点

```jsonc
{
  "code": "0",
  "data": {
    "page": 1, "size": 10, "total": 23,        // total = 命中的来访数
    "content": [
      {
        "wangId": "1685535452481236993",          // 客户 ID
        "visits": [
          {
            "visitId":  "...",
            "visitTime": "2026-05-13 14:01:03",
            "summaries": [                          // ★ 该次来访的模板总结列表
              { "question": "客户需求", "reply": "关注三房、预算 300 万以内、看重学区..." },
              { "question": "抗性分析", "reply": "对楼层和价格有顾虑..." }
            ]
          }
        ]
      }
    ]
  }
}
```

CLI 又包一层 → `resp.data.data.content`。每个总结项 `question` = 模板名、`reply` = 该模板的 AI 总结答案。展示给用户时按 客户 → 来访 → 模板 三层组织。

---

## 使用场景示例

### 场景 1：看某次来访的接待总结

```bash
xiaobao-cli visit summary --visit-id 998877
```

### 场景 2：李女士本周来访都聊了什么

```bash
# step 1: 反查 wang_id
xiaobao-cli customer list --customer-name 李女士 --size 20
# step 2: 用 wang_id + 本周时间窗
xiaobao-cli visit summary --customer-id 270072120829026305 --from "2026-05-12 00:00:00" --to "2026-05-16 23:59:59"
```

### 场景 3：只看"客户需求"模板的总结

```bash
xiaobao-cli visit summary --from "2026-05-13 00:00:00" --to "2026-05-14 00:00:00" --template "客户需求"
```

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 跑 `wangxiaobao-switch-project` skill
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登
- **`from 与 to 不能为空`** — 没传 `--visit-id` 时必须给时间窗
- **`to 必须晚于 from`** — 时间窗方向反了
- **`total: 0`** — 窗口内没有已完成分析的来访总结，或当前用户授权范围内无匹配
- **想看录音原文 / 列来访** — 录音转录走 `wangxiaobao-audio-query`；来访列表 + 录音走 `wangxiaobao-visit-query`
