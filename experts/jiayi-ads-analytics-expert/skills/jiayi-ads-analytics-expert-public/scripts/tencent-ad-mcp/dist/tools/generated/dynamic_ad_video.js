// Auto-generated from Go SDK — module: dynamic_ad_video
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerDynamicAdVideoTools(server) {
    server.tool("dynamic_ad_video_add", "创建用于广告投放的动态广告视频", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/dynamic_ad_video/add", merged));
    });
    server.tool("dynamic_ad_video_get", "获取广告投放的动态广告视频", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/dynamic_ad_video/get", merged));
    });
}
//# sourceMappingURL=dynamic_ad_video.js.map