// Auto-generated from Go SDK — module: game_feature_tags
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerGameFeatureTagsTools(server) {
    server.tool("game_feature_tags_get", "获取游戏特征标签", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/game_feature_tags/get", merged));
    });
}
//# sourceMappingURL=game_feature_tags.js.map