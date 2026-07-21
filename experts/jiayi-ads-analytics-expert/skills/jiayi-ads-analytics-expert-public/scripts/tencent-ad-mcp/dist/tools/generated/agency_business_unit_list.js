// Auto-generated from Go SDK — module: agency_business_unit_list
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAgencyBusinessUnitListTools(server) {
    server.tool("agency_business_unit_list_get", "查询服务商业务单元列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/agency_business_unit_list/get", merged));
    });
}
//# sourceMappingURL=agency_business_unit_list.js.map