// Auto-generated from Go SDK — module: leads_voip_call_token
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLeadsVoipCallTokenTools(server) {
    server.tool("leads_voip_call_token_get", "获取网络电话token", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/leads_voip_call_token/get", merged));
    });
}
//# sourceMappingURL=leads_voip_call_token.js.map