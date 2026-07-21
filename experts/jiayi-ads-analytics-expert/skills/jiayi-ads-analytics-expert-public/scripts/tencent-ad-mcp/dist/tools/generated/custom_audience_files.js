// Auto-generated from Go SDK — module: custom_audience_files
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerCustomAudienceFilesTools(server) {
    server.tool("custom_audience_files_add", "上传客户人群数据文件", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/custom_audience_files/add", merged));
    });
    server.tool("custom_audience_files_get", "获取客户人群数据文件", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/custom_audience_files/get", merged));
    });
}
//# sourceMappingURL=custom_audience_files.js.map