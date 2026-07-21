// Auto-generated from Go SDK — module: programmed_template
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProgrammedTemplateTools(server) {
    server.tool("programmed_template_get", "获取模板列表接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/programmed_template/get", merged));
    });
}
//# sourceMappingURL=programmed_template.js.map