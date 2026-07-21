// Auto-generated from Go SDK — module: batch_async_requests
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerBatchAsyncRequestsTools(server) {
    server.tool("batch_async_requests_add", "创建批量异步请求任务", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/batch_async_requests/add", merged));
    });
    server.tool("batch_async_requests_get", "获取批量异步请求任务列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/batch_async_requests/get", merged));
    });
}
//# sourceMappingURL=batch_async_requests.js.map