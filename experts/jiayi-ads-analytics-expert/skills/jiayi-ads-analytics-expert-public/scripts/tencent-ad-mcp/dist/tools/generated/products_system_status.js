// Auto-generated from Go SDK — module: products_system_status
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProductsSystemStatusTools(server) {
    server.tool("products_system_status_get", "获取审核失败的商品", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/products_system_status/get", merged));
    });
}
//# sourceMappingURL=products_system_status.js.map