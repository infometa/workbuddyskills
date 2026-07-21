// Auto-generated from Go SDK — module: dynamic_creative_previews
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerDynamicCreativePreviewsTools(server) {
    server.tool("dynamic_creative_previews_add", "3.0创意绑定在线预览", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/dynamic_creative_previews/add", merged));
    });
}
//# sourceMappingURL=dynamic_creative_previews.js.map