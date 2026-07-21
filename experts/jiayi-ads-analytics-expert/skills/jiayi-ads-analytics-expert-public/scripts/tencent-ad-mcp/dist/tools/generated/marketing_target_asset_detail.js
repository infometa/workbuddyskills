// Auto-generated from Go SDK — module: marketing_target_asset_detail
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMarketingTargetAssetDetailTools(server) {
    server.tool("marketing_target_asset_detail_get", "获取推广内容资产详情", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/marketing_target_asset_detail/get", merged));
    });
}
//# sourceMappingURL=marketing_target_asset_detail.js.map