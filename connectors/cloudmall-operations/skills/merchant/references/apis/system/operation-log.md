# 系统域 — 操作日志能力契约

> 概念知识：`references/domains/system.md`（日志字段、requestBody 翻译、脱敏纪律、采集边界）。
> 先取筛选选项，再按 `module`/`action` 检索；两个能力都只读。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：system.operation-log.filter-options 筛选选项 · system.operation-log.search 全站操作日志检索

---

## ✅ 操作日志筛选选项 — ops.system.operation-log.filter-options

无入参。通过 ES terms 聚合返回真实日志的 `modules`（模块 distinct）与 `actions`（动作 distinct），用于填充检索条件。

这是 `module`/`action` 的**唯一取值来源**：两者都是中文语义词（如 `促销管理`、`增加活动库存`），随真实日志持续变化，**不存在固定枚举，禁止凭猜测或英文/路径填写**。返回空数组表示当前范围内没有可用值；此时不要猜值，改用 `keyword` 或 `operatorName` 检索。

```json
{"capability":"ops.system.operation-log.filter-options","input":{},"summary":"获取操作日志的模块与动作筛选选项"}
```

---

## ✅ 全站操作日志检索 — ops.system.operation-log.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| module | String | 否 | 中文模块名，**精确匹配**；取值只能来自筛选选项 |
| action | String | 否 | 中文动作名，**精确匹配**（必须完全相等，否则零结果）；取值只能来自筛选选项 |
| operatorName | String | 否 | 操作人名称，模糊匹配 |
| keyword | String | 否 | 关键词，只匹配 `description` |
| level | String | 否 | 日志等级：`NORMAL` 或 `IMPORTANT` |
| startTime | String | 否 | 开始时间，`yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm:ss` |
| endTime | String | 否 | 结束时间，`yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm:ss` |
| cursor | String | 否 | 无状态游标；首查不传，加载更多时原样传入上次的 `nextCursor` |
| pageNum | Number | 否 | 兼容浅分页，从 1 开始；游标连续加载时固定传 1 或省略 |
| pageSize | Number | 是 | 每批条数，1～100 |

### 出参（原始数据）

返回 `records[]` / `total` / `pageNum` / `pageSize` / `nextCursor`，按发生时间**倒序**（最新在前）。继续加载时携带 `nextCursor` 并追加 records；`nextCursor=null` 表示没有更多。游标只含排序值、无 PIT。`records[]` 字段见 `../domains/system.md`。

`records[].requestBody` 是提交参数的 **JSON 字符串**，必须解析后翻译成业务语言再讲给用户，不能直接念字段名；回复时的脱敏口径见 `../domains/system.md` 的「输出脱敏纪律」。

翻译时优先用 `description`，再用 `httpMethod` + `uri` 定位到对应业务域的接口描述，照它的入参表逐字段翻译（字段名与取值同源）；定位方法与域映射表见 `../domains/system.md` 的「用 `uri` 关联业务域接口描述」。

### 调用示例

```json
{"capability":"ops.system.operation-log.search","input":{"pageSize":20},"summary":"检索本租户最近的操作日志"}
```

```json
{"capability":"ops.system.operation-log.search","input":{"module":"促销管理","action":"增加活动库存","level":"IMPORTANT","pageSize":20},"summary":"检索重要的促销活动库存增加记录"}
```

---

## 结论口径

- `total` 是命中总数；只有 `nextCursor=null` 才能断言「该条件下没有更多」。
- 业务码 `41001` 表示 cursor 无效，应保留筛选条件重新首查；`50001` 表示 ES 查询失败，不能解释为空数据。
- 查不到时优先怀疑采集边界（未开启采集的服务、纯查询动本不记日志、未登记语义），不要直接断言「没有发生」。
- `requestBody` 的脱敏只覆盖固定敏感键名且仅顶层：手机号、地址、邮箱、金额等不在其中，嵌套敏感键也会漏。回复前一律按「输出脱敏纪律」自行处理，不原样转述。
