// Auto-generated from Go SDK — module: agency_realtime_cost
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAgencyRealtimeCostTools(server) {
    server.tool("agency_realtime_cost_get", "服务商当日分账户实时消耗", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/agency_realtime_cost/get", merged));
    });
}
//# sourceMappingURL=agency_realtime_cost.js.map