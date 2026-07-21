// Auto-generated from Go SDK — module: advertiser_daily_budget
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAdvertiserDailyBudgetTools(server) {
    server.tool("advertiser_daily_budget_get", "获取竞价广告账户日预算", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/advertiser_daily_budget/get", merged));
    });
    server.tool("advertiser_daily_budget_update", "更新竞价广告账户日预算", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/advertiser_daily_budget/update", merged));
    });
}
//# sourceMappingURL=advertiser_daily_budget.js.map