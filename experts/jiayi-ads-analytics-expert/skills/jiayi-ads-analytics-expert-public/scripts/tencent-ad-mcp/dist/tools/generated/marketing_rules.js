// Auto-generated from Go SDK — module: marketing_rules
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMarketingRulesTools(server) {
    server.tool("marketing_rules_get", "获取营销表达组合", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/marketing_rules/get", merged));
    });
}
//# sourceMappingURL=marketing_rules.js.map