// Auto-generated from Go SDK — module: keyword_recommend
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerKeywordRecommendTools(server) {
    server.tool("keyword_recommend_get", "获取关键词推荐结果", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/keyword_recommend/get", merged));
    });
}
//# sourceMappingURL=keyword_recommend.js.map