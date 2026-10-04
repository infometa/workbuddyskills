---
name: wangxiaobao-admin-sales-report
version: 0.1.0
description: "旺小宝公司经营数据查询（super-admin，独立白名单）：按日期区间返回 出库金额(outStockAmount) 与 回款/入库金额(receiveAmount)，按 项目组(--by project，默认) 或 战区(--by zone) 分组。只读。高频命令: xiaobao-cli admin sales-report --from <yyyy-MM-dd> --to <yyyy-MM-dd> [--by project|zone]。何时用：用户问 公司业绩/经营数据/出库/回款/入库金额/各项目组业绩/各战区业绩/业绩排名/某月做了多少。注：独立白名单控制（与其它命令的白名单无关），返回引导文案时原样告知用户并停止；不需要激活项目；两个维度出库合计存在口径差，汇报须注明口径。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli admin sales-report --help"
---

# 旺小宝公司经营数据（出库 / 回款）

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（登录 / 输出协议 / 错误码 等通用约定）。

`xiaobao-cli admin sales-report` 查询公司级经营数据（数据源：内网金蝶报表，经 ai-open 代理）。

## 执行前必读
- **super-admin 能力，独立白名单**：与其它命令的白名单**互相独立**，且**名单为空 = 全拒**。若返回 `data: "不在白名单中，若有需求请联系19136123281"`，**原样告知用户并停止，不要重试**。
- 需要登录（token），**不需要激活项目**。
- 日期为**闭区间**（`--from 2026-07-01 --to 2026-07-31` 含首尾两天），格式 `yyyy-MM-dd`。
- 只读，不写文件。

## 快速索引
| 用户意图 | 命令 |
| --- | --- |
| 某月各项目组业绩 | `admin sales-report --from 2026-07-01 --to 2026-07-31`（默认 --by project） |
| 某月各战区业绩 | `admin sales-report --from ... --to ... --by zone` |
| 两个维度都要 | 调两次（--by project + --by zone），并注意口径差（见下） |
| 时间说法（本月/上月/最近 7 天） | 换算成 from/to 再调 |

## 核心约束与坑（来自实测）
1. **出库 vs 回款口径**：`outStockAmount` = 出库，`receiveAmount` = 回款（入库）。
2. **两个维度合计对不上是数据源特性不是 bug**：入库合计两维度一致，但**出库合计恒是项目组 > 战区**（每月差 0.4~3.6 万，部分出库单归得到项目组归不到战区）。**汇报公司总业绩必须注明口径**（建议用项目组口径）。
3. **负数是正常的**：出库可为负（退货/红字冲销），如实呈现，不要过滤。
4. **返回 0 不等于失败**：未来区间、无业务区间正常返回 0；先确认区间合理再下结论。
5. **日期写反**：ai-open 已拦截（返回 400 "startDate 不能晚于 endDate"），不会再静默返回全 0。

## 响应字段
```jsonc
{ "code": "0", "data": {
    "totalReceiveAmount": 7546423.51,      // 回款(入库)合计
    "totalOutStockAmount": 7809705.90,     // 出库合计
    "data": [                               // 按出库金额降序（接口原序）
      { "name": "人脸识别项目组",
        "values": { "receiveAmount": 4102679.69, "outStockAmount": 4176741.33 } }
    ] } }
```
CLI 再包一层 → 读 `resp.data.data.*`。展示时给出 名称 / 回款 / 出库 / 出库占比，负数保留。

## 常见错误
- **`data` 是"不在白名单中…"文案** → 原样转告用户，停止（联系 19136123281 开通）。
- **401** → `auth login --no-wait --force` 重登。
- **400 日期问题** → 检查 yyyy-MM-dd 格式与 from<=to。
- **全 0** → 先确认区间是否合理（未来区间/无业务），不要报"接口挂了"。
