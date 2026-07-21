// Auto-generated from Go SDK — module: review_element_prereview_results
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerReviewElementPrereviewResultsTools(server) {
    server.tool("review_element_prereview_results_get", "查询元素的预审结果", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/review_element_prereview_results/get", merged));
    });
}
//# sourceMappingURL=review_element_prereview_results.js.map