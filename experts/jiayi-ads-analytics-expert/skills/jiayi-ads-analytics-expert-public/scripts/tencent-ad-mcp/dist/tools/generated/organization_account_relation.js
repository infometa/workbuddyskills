// Auto-generated from Go SDK — module: organization_account_relation
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerOrganizationAccountRelationTools(server) {
    server.tool("organization_account_relation_get", "查询组织下广告账户信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/organization_account_relation/get", merged));
    });
}
//# sourceMappingURL=organization_account_relation.js.map