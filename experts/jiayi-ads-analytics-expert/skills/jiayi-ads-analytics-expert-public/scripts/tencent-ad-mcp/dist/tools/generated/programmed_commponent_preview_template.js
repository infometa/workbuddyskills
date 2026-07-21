// Auto-generated from Go SDK — module: programmed_commponent_preview_template
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProgrammedCommponentPreviewTemplateTools(server) {
    server.tool("programmed_commponent_preview_template_update", "组件化创意衍生预览模版替换接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/programmed_commponent_preview_template/update", merged));
    });
}
//# sourceMappingURL=programmed_commponent_preview_template.js.map