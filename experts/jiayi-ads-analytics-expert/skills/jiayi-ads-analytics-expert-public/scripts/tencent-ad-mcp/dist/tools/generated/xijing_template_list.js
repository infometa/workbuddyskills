// Auto-generated from Go SDK — module: xijing_template_list
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerXijingTemplateListTools(server) {
    server.tool("xijing_template_list_get", "获取蹊径落地页模板列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/xijing_template_list/get", merged));
    });
}
//# sourceMappingURL=xijing_template_list.js.map