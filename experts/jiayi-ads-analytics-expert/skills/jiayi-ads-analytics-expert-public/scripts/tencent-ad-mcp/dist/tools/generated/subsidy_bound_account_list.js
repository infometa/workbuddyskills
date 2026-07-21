// Auto-generated from Go SDK — module: subsidy_bound_account_list
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerSubsidyBoundAccountListTools(server) {
    server.tool("subsidy_bound_account_list_get", "获取补贴账号关联的广告主账号列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/subsidy_bound_account_list/get", merged));
    });
}
//# sourceMappingURL=subsidy_bound_account_list.js.map