// Auto-generated from Go SDK — module: element_appeal_review
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerElementAppealReviewTools(server) {
    server.tool("element_appeal_review_add", "发起元素申诉复审", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/element_appeal_review/add", merged));
    });
    server.tool("element_appeal_review_get", "获取元素申诉复审结果", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/element_appeal_review/get", merged));
    });
}
//# sourceMappingURL=element_appeal_review.js.map