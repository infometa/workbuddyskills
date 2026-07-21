// Auto-generated from Go SDK — module: product_items_detail
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProductItemsDetailTools(server) {
    server.tool("product_items_detail_get", "获取商品详情", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/product_items_detail/get", merged));
    });
}
//# sourceMappingURL=product_items_detail.js.map