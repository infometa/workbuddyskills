# 抽题契约（MCP brush_draw 工具）

抽题调 `gaodun-job` MCP 工具 `brush_draw`（tools/call，name=brush_draw），OAuth 自动发现；不手动自签 token、不硬编码 token。工具内部调后端刷题抽题接口，该接口仍无认证——不发送 Authentication、不索取 token（见铁律）。

请求字段全部可选：projectId、industryId、jobId、questionTag、batchYear、excludeQuestionIds。**excludeQuestionIds 的元素是字符串**（题目 ID 为 32 位十六进制字符串，取自上一题返回的 `question.questionId`，不是整数）；**调用时直接传字符串数组，不要 `{"item": ...}` 包装**，正确格式如 `{"projectId": 100520929, "excludeQuestionIds": ["9130b2029fe04084a08ebd3e5d49780c"]}`；排除列表最多按最近 200 个生效，请求体永远不含答案。每题 finalize 或跳过后，把该题 questionId 追加进会话的排除集，下次抽题一并传入，避免重复出题。

响应 result={question,emptyReason}。MCP 工具将 result 规范化输出为 data，供会话流程读取。有题时 question 非空且 emptyReason=null；question=null 时必须先读 emptyReason：NO_QUESTION 表示条件下无题，EXHAUSTED 表示题池被排除集耗尽。

工具验证 HTTP 200 与业务 status==0，保留 requestId。`brush_draw` 工具实现见 dyson 服务端 mcp brush 包（BrushDrawTool）。

胶囊入口先用 `scripts/capsule_config.py` 装配 payload（`capsule-id` → drawFilters 与 sessionInit），再调 `brush_draw`；data/capsules.json 与工具侧 classpath 资源 `data/brush-capsules.json`（与 Python 侧同源）对齐。胶囊 ID 不得与手工 projectId/industryId/jobId/questionTag/batchYear 参数混用；excludeQuestionIds 可继续追加。输出除 requestId/data 外包含 sessionInit，供会话直接初始化。

失败时停止，不自动重试，不转调旧 page/recommend、submit/report 或用户态接口。对用户只展示友好说明和 requestId。工具内部调后端刷题抽题接口不索取 token；入口层 `gaodun-job` MCP 端点的 OAuth 由 MCP 客户端自动处理，不属本条范围。
