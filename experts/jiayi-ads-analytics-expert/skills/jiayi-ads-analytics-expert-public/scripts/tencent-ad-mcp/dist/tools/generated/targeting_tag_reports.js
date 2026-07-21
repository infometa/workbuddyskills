// Auto-generated from Go SDK — module: targeting_tag_reports
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerTargetingTagReportsTools(server) {
    server.tool("targeting_tag_reports_get", "获取定向标签报表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/targeting_tag_reports/get", merged));
    });
}
//# sourceMappingURL=targeting_tag_reports.js.map