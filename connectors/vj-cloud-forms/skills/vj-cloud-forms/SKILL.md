---
name: vj-cloud-forms
description: 微加云表单查询与统计。当用户想查找/查看/统计微加(51vj)云表单数据时使用——考勤打卡、请假审批、客户信息、订单等业务表单的字段查询和多维聚合分析。
---

# 微加云表单(vj-cloud-forms)

查询与统计当前企业在微加平台上的云表单数据。首次调用会自动弹出企业微信扫码授权,扫码确认后即可使用。

## 工具清单

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `vj_channel_list` | 列出当前企业可用的表单应用 | 无 |
| `vj_formdef_search` | 按名称查表单,返回 `def_key` | `name`(必填,表单名称) |
| `vj_formdef_detail` | 按 `def_key` 查表单字段树 | `key`(必填,来自 search 结果) |
| `vj_formdef_aggregate` | 表单数据分组聚合统计 | 见下 |
| `vj_auth` | 凭证诊断(status)与修复(logout) | `action`: status / logout |

## 标准调用链

1. **查字段**:`vj_formdef_search(name=表单名)` → `vj_formdef_detail(key=def_key)` → 向用户呈现字段树。
2. **统计分析**(必须先完成前两步):search 拿 `def_key` → detail 拿字段 `id` → 按用户需求确定维度与指标 → `vj_formdef_aggregate`。

## vj_formdef_aggregate 参数语义

服务端固定携带 `data_authority: authority`(只统计当前用户可见的数据),调用方无需关心。

- `def_keys`:表单 key 数组(单表统计传 1 个)。
- `row_fields` / `col_fields`:行/列维度 `[{id, name, format}]`;仅日期字段 `format` 可填 `day/week/month/quarter/year`,其余填 `""`。
- `metrics`:指标 `[{id, name, stat_method}]`(不含其他字段);`stat_method` 仅允许 `count / distinct_count / sum / avg / max / min`,`sum/avg/max/min` 仅数值字段。
- `query_fields`(可选筛选)`[{id, type, params}]`:
  - 文本:`equal / not_equal / contains / not_contains / equal_any / not_equal_any / empty / not_empty`
  - 数字:`equal / not_equal / empty / not_empty / range`(params 用数字,如 `[1]` 或 `[1,5]`)
  - 日期:`equal / not_equal / not_empty / range`;`equal` 的 params 可用 `today / this_week / this_month / last_month / this_year` 等枚举,`range` 的 params 用 `["YYYY-MM-DD","YYYY-MM-DD"]`
  - `type=range` 必须带 `range` 参数:`gt / gte / lt / lte` 或组合如 `"gte,lte"`

## 使用注意

- **表单名称尽量用前缀**:搜索按「精确 > 前缀 > 包含」排序,子串居中的关键词可能漏召回(搜「获取打卡」比「打卡记录」稳)。拿到结果后以返回的准确名称为准。
- **def_key 必须原样复制**:1~19 位纯数字(bigint),从 search 返回值复制给 detail/aggregate 时不要改写成数字、科学计数法或浮点(如 `9.8e+17`),否则本地校验会拒(`INVALID_ARGS`)。
- **search 只返回最相关结果**:不要向用户提及或推测其他应用下存在同名表单;无结果就按「未找到该表单」处理。
- **错误处理**:
  - 返回 `UNAUTHENTICATED` → 调 `vj_auth(action=status)` 诊断:`session_invalid` 时调 `vj_auth(action=logout)` 修复(客户端会自动引导重新扫码);其余未登录/过期态提示用户重新发起授权。
  - 返回 `INVALID_ARGS` → 按消息修正参数(维度/指标的闭合枚举本地即拦截)。
  - 返回 `GATEWAY_ERROR` → 查看 `gateway_response` 里的网关原始响应定位。
- **凭证有效期**:扫码授权后随网关会话 7 天有效,到期客户端会自动引导重扫,无需用户干预。
