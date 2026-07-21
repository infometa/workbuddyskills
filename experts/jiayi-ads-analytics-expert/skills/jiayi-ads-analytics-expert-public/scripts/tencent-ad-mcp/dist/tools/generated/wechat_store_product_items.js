// Auto-generated from Go SDK — module: wechat_store_product_items
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatStoreProductItemsTools(server) {
    server.tool("wechat_store_product_items_get", "获取微信小店商品", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_store_product_items/get", merged));
    });
}
//# sourceMappingURL=wechat_store_product_items.js.map