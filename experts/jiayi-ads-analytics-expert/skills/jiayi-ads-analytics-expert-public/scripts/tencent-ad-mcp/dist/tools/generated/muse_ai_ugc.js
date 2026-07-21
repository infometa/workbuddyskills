// Auto-generated from Go SDK — module: muse_ai_ugc
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMuseAiUgcTools(server) {
    server.tool("muse_ai_ugc_add", "二次编辑素材回传接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/muse_ai_ugc/add", merged));
    });
}
//# sourceMappingURL=muse_ai_ugc.js.map