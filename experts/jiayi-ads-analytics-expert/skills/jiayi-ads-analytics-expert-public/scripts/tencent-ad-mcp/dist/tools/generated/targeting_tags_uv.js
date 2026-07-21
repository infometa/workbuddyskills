// Auto-generated from Go SDK — module: targeting_tags_uv
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerTargetingTagsUvTools(server) {
    server.tool("targeting_tags_uv_get", "获取行为/兴趣/意向标签覆盖人群数", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/targeting_tags_uv/get", merged));
    });
}
//# sourceMappingURL=targeting_tags_uv.js.map