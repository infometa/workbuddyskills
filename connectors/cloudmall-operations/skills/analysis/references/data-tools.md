# 当前 Agent 分析工具契约

服务器查询仅通过 `当前运行时的 Capability 分析执行器`（入参形态分本地编码/服务端编码两种，见下文契约）。沿用当前授权和用户权限；分析入口要求租户全量分析管理员权限，不支持仅具有门店或受限数据范围的账号；服务器固定路由、租户隔离、表白名单和只读检查。禁止直接访问内部服务、传递凭证或身份/租户/服务路由参数，禁止绕过拒绝结果。六项业务对象查询由原查询技能处理。

> 能力索引（前缀 `ops.analysis.`）：table.structure 表结构查询 · metric.search 指标口径查询 · metric.query 指标数据查询 · sql.execute 单条 SQL 执行 · sql.batch 批量 SQL 执行

## 业务日期与 SQL 传参（按运行时形态）

执行器有两种入参形态，以当前运行时的工具说明为准：

**本地编码形态**（参数 `{action, input}`）：先用 Bash 运行 `python3 "<技能目录>/scripts/encode_sql.py" --today` 获取 Asia/Shanghai 业务日期（固定 UTC+08:00），不受电脑本地时区影响。Windows 可换 `py -3`。数据 T+1 不代表"昨天"要再减一天；明确实际可用日期。通过本地文件工具保存完整 UTF-8 SQL 为 `query.sql`，SQL 不放入 shell 命令、环境变量或命令替换。

```bash
python3 "<技能目录>/scripts/encode_sql.py" "<本地目录>/query.sql"
python3 "<技能目录>/scripts/encode_sql.py" --batch "<本地目录>/current.sql" "<本地目录>/previous.sql"
```

读取 stdout 的 JSON 原样作为工具参数（不是字符串，也不要再套 input）。单条形状 `{ "action":"sql_execute", "input":{"sqlBase64":"...","maxRows":1000,"maxPreviewRows":100} }`；批量形状 `{ "action":"sql_batch", "input":{"sqls":[{"sqlBase64":"...","maxRows":1000,"maxPreviewRows":100}]} }`。仅标准严格 Base64、UTF-8；禁止明文 sql 参数、手工编码猜测、编码失败时明文回退。

**服务端编码形态**（参数 `{capabilityId, summary, input}`）：**三个参数均必填，缺一会被执行器校验拒绝**。`summary` 为一句话说明本次查询目的（如"查询近 7 天交易大盘 GMV 与支付人数"），供调用审计与结果追踪使用，禁止留空或填无意义内容。业务日期用本地命令工具执行 `date '+%Y%m%d'`；SQL 以明文 `sql` 字段直传 input，服务端负责编码，禁止传 sqlBase64 或自行编码，禁止写入文件。单条 `capabilityId` 为 `ops.analysis.sql.execute`，input 形如 `{"sql":"SELECT ...","maxRows":1000,"maxPreviewRows":100}`；批量 `capabilityId` 为 `ops.analysis.sql.batch`，input 形如 `{"sqls":[{"sql":"SELECT ...","maxRows":1000,"maxPreviewRows":100}]}`。调用示例：

```json
{"capabilityId": "ops.analysis.sql.batch", "summary": "查询近 7 天交易大盘 GMV/支付人数/退款率", "input": {"sqls": [{"sql": "SELECT ...", "maxRows": 1000, "maxPreviewRows": 100}]}}
```

通用约束：每条 SQL 非空且最多 32768 字节；批量 1 到 10 条。maxRows/maxPreviewRows 为 1 到 1000 的整数，默认 1000/100。仅 SELECT。

## 五个 action

| action | input（camelCase） | 用途 |
|---|---|---|
| table_structure | domains?: string, tablePattern?: string, domainName?: string, includeColumns?: boolean | 查表结构，写 SQL 前必查；tablePattern 优先，其次 domains，均空为全部 |
| metric_search | keyword: string, queryType: definition 或 sql_context, domain?: TRADE/PRODUCT/USER/MARKETING/DIMENSION | 指标口径或 SQL 上下文；名称/英文逗号分隔别名精确匹配 |
| metric_query | metrics: string[]（1 到 10）, dateRange: {start,end}（yyyyMMdd）, dimensions?: DimensionFilter[], groupBy?: string[], limit?: integer（1 到 1000）, maxPreview?: integer（1 到 1000，默认 100） | 按指标编码、维度、日期取数 |
| sql_execute | sqlBase64: string（本地编码形态）或 sql: string 明文（服务端编码形态）, maxRows?: integer, maxPreviewRows?: integer | 仅 SELECT |
| sql_batch | sqls: SQL 输入数组（1 到 10） | 独立查询可批量，依赖查询分批 |

DimensionFilter：`{field: string, op?: "="|"IN"|"NOT IN"|"LIKE"|"BETWEEN", value: string|number|array}`，按实际工具 schema 与指标字段选择，缺省 op 为 `=`。示例：

```json
{"action":"table_structure","input":{"domains":"商品,营销","includeColumns":true}}
```
```json
{"action":"metric_search","input":{"keyword":"GMV","queryType":"definition","domain":"TRADE"}}
```
```json
{"action":"metric_query","input":{"metrics":["pay_order_cnt","pay_uv"],"dateRange":{"start":"20260901","end":"20260907"},"dimensions":[{"field":"scene_type","value":"分享"}],"groupBy":["imp_date"],"limit":1000}}
```

诊断表如 `app_anomaly_attribution_detection_di`、`dwm_sales_refund_attr_di` 可能不归属主题域，使用 tablePattern 精确查询；仍须服务器白名单与实际权限允许。仅使用返回确认的字段。

## 结果与失败处理

以当前运行时返回的实际结构化结果为准；上游结果包装由服务处理，不把传输层状态当成业务成功判断。SQL 数据通常含 columns、previewData、actualRows；预览受行数及响应预算限制，actualRows 不等于无限制全表总数。previewTruncated 表示预览行数小于实际返回行数，rowLimitReached 表示到达查询行数上限、可能还有更多数据；这两者与结果传输预算产生的 truncated 分开判断，不得按样本推断全量。报告必须说明截断、部分失败、空值或缺失数据，不用缺失值冒充零。查询返回空时先确认该表最近有数据的日期范围再下结论（报表宽表 T+1 且各维度表覆盖可能不齐，处理纪律见 `sql_templates_Q.md` 通用约束）。批量逐项判断成功，仅用已成功数据，不将整批完成当成全部成功。

**结构化错误（sql_execute / sql_batch / metric_query 失败时）**：返回 `data.success=false`（单条）或 `results[].success=false`（批量），并携带 `errorCode`、`errorMessage`（服务端脱敏）、`objectName`（涉事表/列，可空）、`hint`（处置建议）。errorCode 枚举：`INPUT_REJECTED`（安全校验拒绝，按 errorMessage 调整）、`SQL_OBJECT_NOT_FOUND`（表不存在——换 table_structure 返回的可用表，不要重试同名表）、`SQL_COLUMN_NOT_FOUND`（列不存在——先查表结构再改写）、`SQL_SYNTAX`（修正语句，最多重试一次）、`SQL_TIMEOUT`（缩小时间范围或拆分）、`SQL_PERMISSION`（告知用户联系管理员，不要重试）、`SQL_CONNECTION`（稍后重试一次）、`SQL_EXEC_ERROR`（检查条件后重试一次）。按 errorCode 决定改写、换表、缩小范围或上报，不盲目重试；`SQL_OBJECT_NOT_FOUND` 连续出现时向用户说明该表在此环境不可用。

权限或认证拒绝时按当前运行时提示重新授权或联系管理员；不得改身份、改用内部入口或绕过权限。明确字段/语法错误先刷新表结构，再读 sql-few-shots.md，最多修正重试一次；无响应同参数最多重试一次。不要向用户暴露原始 SQL、数据库字段或认证细节。
