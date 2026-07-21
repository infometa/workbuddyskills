// Auto-generated from Go SDK — module: dynamic_ad_image_templates
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerDynamicAdImageTemplatesTools(server) {
    server.tool("dynamic_ad_image_templates_get", "获取动态商品图片模板", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/dynamic_ad_image_templates/get", merged));
    });
}
//# sourceMappingURL=dynamic_ad_image_templates.js.map