// Auto-generated from Go SDK — module: batch_async_request_specification
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerBatchAsyncRequestSpecificationTools(server) {
    server.tool("batch_async_request_specification_get", "获取批量异步请求任务详情", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/batch_async_request_specification/get", merged));
    });
}
//# sourceMappingURL=batch_async_request_specification.js.map