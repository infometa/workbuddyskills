// Auto-generated from Go SDK — module: operation_log_list
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerOperationLogListTools(server) {
    server.tool("operation_log_list_get", "获取操作日志列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/operation_log_list/get", merged));
    });
}
//# sourceMappingURL=operation_log_list.js.map