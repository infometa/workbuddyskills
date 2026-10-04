# 会话写入、凭证与未决结果

以下是旧资源的业务会话合同；OAuth画像beta不开放这些高级工具，也不接受其sessionRef/sessionToken/accessCode作为旧桥输入。OAuth重连与旧业务会话恢复不是同一个操作。

## 来源

- 激活访问码只能来自用户为当前步骤明确提供的值。
- 会话引用或令牌只能来自同一服务链返回，或当前 schema 明确接受的可验证来源。
- 不从 MCP session、event ID、request ID、trace、设备路径或匿名 hash 构造业务会话身份。

## 写入前

确认当前 `tools/list` 中存在目标工具、参数满足 schema、用户意图仍有效，并区分激活、权益预检、流程完结和登出。

## 结果分类

- 有成功业务回执：只报告该工具已确认的结果。
- 有明确业务失败：报告失败原因与安全下一步。
- HTTP/连接超时、SSE 中断、非 JSON-RPC、工具错误或缺失回执：标记 `outcome_unknown`；不得解释为成功或确定失败。

## 后续

只有当前工具面明确提供状态查询/恢复能力时，才按其 schema 回读。没有 `session_recover` 就不调用、不猜名、不承诺恢复。未知结果下不自动 logout，不生成新凭证重复 activate/finish，也不把会话未决误写成首值消费。
