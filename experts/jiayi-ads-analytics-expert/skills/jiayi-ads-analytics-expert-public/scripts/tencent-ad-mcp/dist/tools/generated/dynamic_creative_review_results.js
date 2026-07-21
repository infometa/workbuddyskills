// Auto-generated from Go SDK — module: dynamic_creative_review_results
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerDynamicCreativeReviewResultsTools(server) {
    server.tool("dynamic_creative_review_results_get", "查询动态创意审核结果", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/dynamic_creative_review_results/get", merged));
    });
}
//# sourceMappingURL=dynamic_creative_review_results.js.map