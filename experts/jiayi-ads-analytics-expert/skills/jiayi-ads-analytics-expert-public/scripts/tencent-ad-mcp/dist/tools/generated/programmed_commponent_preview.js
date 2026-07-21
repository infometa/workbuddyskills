// Auto-generated from Go SDK — module: programmed_commponent_preview
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProgrammedCommponentPreviewTools(server) {
    server.tool("programmed_commponent_preview_add", "组件化创意衍生预览创建接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/programmed_commponent_preview/add", merged));
    });
    server.tool("programmed_commponent_preview_delete", "组件化创意衍生预览删除接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/programmed_commponent_preview/delete", merged));
    });
    server.tool("programmed_commponent_preview_get", "组件化创意衍生预览查询接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/programmed_commponent_preview/get", merged));
    });
    server.tool("programmed_commponent_preview_update", "组件化创意衍生预览更新接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/programmed_commponent_preview/update", merged));
    });
}
//# sourceMappingURL=programmed_commponent_preview.js.map