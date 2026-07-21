// Auto-generated from Go SDK — module: illegal_complaint
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerIllegalComplaintTools(server) {
    server.tool("illegal_complaint_add", "新增广告主违规申述", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/illegal_complaint/add", merged));
    });
    server.tool("illegal_complaint_get", "获取直客广告主违规申述列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/illegal_complaint/get", merged));
    });
}
//# sourceMappingURL=illegal_complaint.js.map