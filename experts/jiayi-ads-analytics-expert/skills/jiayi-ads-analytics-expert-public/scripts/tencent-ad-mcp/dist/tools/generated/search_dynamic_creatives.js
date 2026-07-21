// Auto-generated from Go SDK — module: search_dynamic_creatives
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerSearchDynamicCreativesTools(server) {
    server.tool("search_dynamic_creatives_add", "创建搜索动态创意", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/search_dynamic_creatives/add", merged));
    });
    server.tool("search_dynamic_creatives_update", "更新搜索创意", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/search_dynamic_creatives/update", merged));
    });
}
//# sourceMappingURL=search_dynamic_creatives.js.map