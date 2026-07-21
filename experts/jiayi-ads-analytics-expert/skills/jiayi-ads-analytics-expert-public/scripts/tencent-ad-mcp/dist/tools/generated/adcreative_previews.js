// Auto-generated from Go SDK — module: adcreative_previews
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAdcreativePreviewsTools(server) {
    server.tool("adcreative_previews_add", "绑定广告预览受众", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/adcreative_previews/add", merged));
    });
}
//# sourceMappingURL=adcreative_previews.js.map