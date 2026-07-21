// Auto-generated from Go SDK — module: marketing_target_types
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMarketingTargetTypesTools(server) {
    server.tool("marketing_target_types_get", "获取可投放推广内容资产类型名称", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/marketing_target_types/get", merged));
    });
}
//# sourceMappingURL=marketing_target_types.js.map