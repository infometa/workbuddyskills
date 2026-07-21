// Auto-generated from Go SDK — module: component_element_urge_review
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerComponentElementUrgeReviewTools(server) {
    server.tool("component_element_urge_review_add", "创意组件元素催审", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/component_element_urge_review/add", merged));
    });
    server.tool("component_element_urge_review_get", "获取创意组件元素催审状态", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/component_element_urge_review/get", merged));
    });
}
//# sourceMappingURL=component_element_urge_review.js.map