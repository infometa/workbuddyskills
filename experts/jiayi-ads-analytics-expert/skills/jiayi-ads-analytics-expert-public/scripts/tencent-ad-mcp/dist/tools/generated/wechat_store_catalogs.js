// Auto-generated from Go SDK — module: wechat_store_catalogs
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatStoreCatalogsTools(server) {
    server.tool("wechat_store_catalogs_get", "获取微信小店商品库", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_store_catalogs/get", merged));
    });
}
//# sourceMappingURL=wechat_store_catalogs.js.map