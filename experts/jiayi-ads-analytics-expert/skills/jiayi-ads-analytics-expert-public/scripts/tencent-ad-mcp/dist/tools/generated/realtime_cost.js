// Auto-generated from Go SDK — module: realtime_cost
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerRealtimeCostTools(server) {
    server.tool("realtime_cost_get", "获取实时消耗", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/realtime_cost/get", merged));
    });
}
//# sourceMappingURL=realtime_cost.js.map