// Auto-generated from Go SDK — module: fund_statements_detailed
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerFundStatementsDetailedTools(server) {
    server.tool("fund_statements_detailed_get", "获取资金流水", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/fund_statements_detailed/get", merged));
    });
}
//# sourceMappingURL=fund_statements_detailed.js.map