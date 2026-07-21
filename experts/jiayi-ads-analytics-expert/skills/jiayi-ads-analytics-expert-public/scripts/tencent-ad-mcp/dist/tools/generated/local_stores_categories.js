// Auto-generated from Go SDK — module: local_stores_categories
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLocalStoresCategoriesTools(server) {
    server.tool("local_stores_categories_get", "查询门店类目", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/local_stores_categories/get", merged));
    });
}
//# sourceMappingURL=local_stores_categories.js.map