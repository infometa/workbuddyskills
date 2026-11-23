# MCP 服务配置

对账所需的订单归属、结算利润明细全部通过 **eccang-mfc-reconcile** 提供的 MCP 工具获取。
脚本不再直连数据库，也不再内置任何库表 SQL 与账号口令。

## 连接信息

| 字段 | 值 |
|------|-----|
| 协议 | MCP Streamable HTTP（JSON-RPC 2.0） |
| 默认地址 | `https://datacenter.eccang.com/nexus/mcp/stream` |
| 覆盖方式 | 命令行 `--mcp-url <地址>`，或环境变量 `NEXUS_MCP_URL` |
| 本地联调 | `--mcp-url http://127.0.0.1:8070/nexus/mcp/stream` |
| 请求头 | `Content-Type: application/json`、`Accept: application/json, text/event-stream` |

经网关访问时地址形态为 `http://<域名>/nexus/mcp/stream`（网关路由未剥离前缀，与服务端路径一致）。

## 使用的工具

| 工具 | 入参 | 返回字段 |
|------|------|---------|
| `queryOrderByReferenceNo` | `orderId`（参考单号） | `companyCode`、`userAccount`、`platform` |
| `queryProfitSettlement` | `companyCode`、`userAccount`、`platform`、`startTime`、`endTime` | `orderId`、`settlementAmount`、`accountCheckResult` |

工具返回体为统一响应体 `{code, message, data, ...}`，脚本取 `data` 字段。

> 时间条件按平台区分：`platform` 为 `walmart` 时按**报告期间**过滤（`period_start_date` / `period_end_date`），
> 此时 `startTime` / `endTime` 传报告期间的开始/结束日期（`yyyy-MM-dd`，**日期粒度、不带时分秒**，服务端不会补
> `00:00:00` / `23:59:59`）；其它平台按 `statement_time` 过滤，纯日期会补全为当天的 `00:00:00` / `23:59:59`。

## 连通性自检

```bash
python scripts/walmart_mcp.py --list-tools
python scripts/walmart_mcp.py --call queryOrderByReferenceNo '{"orderId":"1234567890"}'
```

## 依赖

```bash
pip install openpyxl
```

> 历史说明：早期版本通过 `pg8000` 直连 Hologres（ERP 库 / BI 库）查询，脚本内写死了 SQL 与
> 连接口令，该方式已废弃。原先写入脚本与文档中的账号口令已进入 Git 历史，建议按安全要求轮换。
