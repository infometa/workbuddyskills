// Auto-generated from Go SDK — module: dynamic_ad_images
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerDynamicAdImagesTools(server) {
    server.tool("dynamic_ad_images_add", "创建用于广告投放的动态广告图片", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/dynamic_ad_images/add", merged));
    });
    server.tool("dynamic_ad_images_get", "获取动态广告图片信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/dynamic_ad_images/get", merged));
    });
}
//# sourceMappingURL=dynamic_ad_images.js.map