// Auto-generated from Go SDK — module: business_unit_account
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerBusinessUnitAccountTools(server) {
    server.tool("business_unit_account_get", "查询广告主账号所属的业务单元", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/business_unit_account/get", merged));
    });
    server.tool("business_unit_account_update", "修改客户业务单元帐户", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/business_unit_account/update", merged));
    });
}
//# sourceMappingURL=business_unit_account.js.map