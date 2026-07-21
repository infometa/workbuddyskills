// Auto-generated from Go SDK — module: leads_call_virtual_number
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLeadsCallVirtualNumberTools(server) {
    server.tool("leads_call_virtual_number_get", "获取中间号", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/leads_call_virtual_number/get", merged));
    });
}
//# sourceMappingURL=leads_call_virtual_number.js.map