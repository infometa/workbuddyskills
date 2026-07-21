// Auto-generated from Go SDK — module: xijing_complex_template
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerXijingComplexTemplateTools(server) {
    server.tool("xijing_complex_template_get", "获取蹊径落地页互动模板配置", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/xijing_complex_template/get", merged));
    });
}
//# sourceMappingURL=xijing_complex_template.js.map