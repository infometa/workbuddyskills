// Auto-generated from Go SDK — module: business_unit_list
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerBusinessUnitListTools(server) {
    server.tool("business_unit_list_get", "查询业务单元列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/business_unit_list/get", merged));
    });
}
//# sourceMappingURL=business_unit_list.js.map