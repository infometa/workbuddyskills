// Auto-generated from Go SDK — module: custom_audience_estimations
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerCustomAudienceEstimationsTools(server) {
    server.tool("custom_audience_estimations_get", "人群覆盖数预估", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/custom_audience_estimations/get", merged));
    });
}
//# sourceMappingURL=custom_audience_estimations.js.map