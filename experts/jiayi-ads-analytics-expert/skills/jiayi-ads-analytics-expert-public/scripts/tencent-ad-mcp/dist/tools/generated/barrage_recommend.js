// Auto-generated from Go SDK — module: barrage_recommend
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerBarrageRecommendTools(server) {
    server.tool("barrage_recommend_get", "查询运营推荐弹幕列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/barrage_recommend/get", merged));
    });
}
//# sourceMappingURL=barrage_recommend.js.map