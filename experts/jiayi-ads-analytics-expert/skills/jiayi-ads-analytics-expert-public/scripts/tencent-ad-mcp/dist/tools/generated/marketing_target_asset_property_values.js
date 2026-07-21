// Auto-generated from Go SDK — module: marketing_target_asset_property_values
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMarketingTargetAssetPropertyValuesTools(server) {
    server.tool("marketing_target_asset_property_values_get", "获取可用的推广内容资产属性值", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/marketing_target_asset_property_values/get", merged));
    });
}
//# sourceMappingURL=marketing_target_asset_property_values.js.map