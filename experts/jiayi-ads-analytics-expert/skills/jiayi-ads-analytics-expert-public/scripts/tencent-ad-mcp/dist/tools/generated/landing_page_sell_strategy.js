// Auto-generated from Go SDK — module: landing_page_sell_strategy
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLandingPageSellStrategyTools(server) {
    server.tool("landing_page_sell_strategy_add", "短剧售卖策略-创建售卖策略", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/landing_page_sell_strategy/add", merged));
    });
    server.tool("landing_page_sell_strategy_get", "短剧售卖策略-获取售卖策略列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/landing_page_sell_strategy/get", merged));
    });
}
//# sourceMappingURL=landing_page_sell_strategy.js.map