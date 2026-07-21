// Auto-generated from Go SDK — module: data_source_dispatch
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerDataSourceDispatchTools(server) {
    server.tool("data_source_dispatch_get", "数据源分发关系获取", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/data_source_dispatch/get", merged));
    });
}
//# sourceMappingURL=data_source_dispatch.js.map