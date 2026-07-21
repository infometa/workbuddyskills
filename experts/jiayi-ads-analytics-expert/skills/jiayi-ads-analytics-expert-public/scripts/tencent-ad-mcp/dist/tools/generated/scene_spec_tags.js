// Auto-generated from Go SDK — module: scene_spec_tags
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerSceneSpecTagsTools(server) {
    server.tool("scene_spec_tags_get", "获取场景定向标签", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/scene_spec_tags/get", merged));
    });
}
//# sourceMappingURL=scene_spec_tags.js.map