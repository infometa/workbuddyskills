// Auto-generated from Go SDK — module: creative_template_previews
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerCreativeTemplatePreviewsTools(server) {
    server.tool("creative_template_previews_get", "获取广告创意预览", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/creative_template_previews/get", merged));
    });
}
//# sourceMappingURL=creative_template_previews.js.map