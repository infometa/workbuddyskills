---
name: wangxiaobao-admin-token-usage
version: 0.1.0
description: "旺小宝 LLM token 用量查询（super-admin，独立白名单）：按日期区间返回 输入(promptTokens)/输出(completionTokens)/总量(totalTokens) tokens，可按 模型/供应商/API Key/接入点/标签/状态 过滤。只读。高频命令: xiaobao-cli admin token-usage --from <yyyy-MM-dd> --to <yyyy-MM-dd> [--model <m>] [--provider <p>]。何时用：用户问 token 用量/token 消耗/用了多少 token/AI 用量统计/某模型或某供应商的用量/成本核算输入数据。注：独立白名单控制，返回引导文案时原样告知并停止；不需要激活项目；数据从 2026-04 起；日期闭区间；按月对比=逐月调多次。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli admin token-usage --help"
---

# 旺小宝 LLM Token 用量

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（登录 / 输出协议 / 错误码 等通用约定）。

`xiaobao-cli admin token-usage` 查询公司级 LLM token 用量（数据源：内网 AI Portal，经 ai-open 代理）。

## 执行前必读
- **super-admin 能力，独立白名单**：与其它命令的白名单**互相独立**，且**名单为空 = 全拒**。若返回 `data: "不在白名单中，若有需求请联系19136123281"`，**原样告知用户并停止，不要重试**。
- 需要登录（token），**不需要激活项目**。
- 日期为**闭区间**，格式 `yyyy-MM-dd`。
- 只读，不写文件。

## 快速索引
| 用户意图 | 命令 |
| --- | --- |
| 某月总用量 | `admin token-usage --from 2026-07-01 --to 2026-07-31` |
| 只看某模型 / 供应商 | `--model gpt-4.1-mini` / `--provider openai` |
| 只看某 Key / 接入点 | `--api-key <KEY>` / `--endpoint <EP>` |
| 按标签 | `--tag-key team --tag-value ai` |
| 只看失败请求 | `--status error` |
| 按月对比 | 逐月调多次（每月一个 from/to），自己汇总 |

## 核心约束与坑（来自实测）
1. **数据从 2026-04 开始**：更早区间一律返回 0——那是没数据，不是查询出错。
2. **闭区间**：`--from 2026-07-01 --to 2026-07-31` 含首尾两天。
3. **当天数据仍在增长**：含今天的区间两次调用结果会有差异；做对账用截至昨天的区间。
4. **接口返回整区间汇总，无分页**：要按月/按天拆分就按段多次调用（按天拆一年 = 300+ 次，不要这么干，按月拆）。
5. 筛选条件可任意组合。

## 响应字段
```jsonc
{ "code": "0", "data": {
    "promptTokens": 296215003449,       // 输入
    "completionTokens": 34882240321,    // 输出
    "totalTokens": 331097243770 } }     // 总量
```
CLI 再包一层 → 读 `resp.data.data.*`。大数字建议换算（如 331.10 B）展示。

## 常见错误
- **`data` 是"不在白名单中…"文案** → 原样转告用户，停止（联系 19136123281 开通）。
- **401** → `auth login --no-wait --force` 重登。
- **查 2026-04 之前区间得 0** → 说明"无数据"，不要说成"没用量/接口挂了"。
- **含今天的区间数字对不上** → 正常，当天数据在涨；对账用截至昨天。
