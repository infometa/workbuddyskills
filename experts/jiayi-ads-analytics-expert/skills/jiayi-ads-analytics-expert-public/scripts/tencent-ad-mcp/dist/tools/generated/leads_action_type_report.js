// Auto-generated from Go SDK — module: leads_action_type_report
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLeadsActionTypeReportTools(server) {
    server.tool("leads_action_type_report_add", "线索上报DMP平台", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/leads_action_type_report/add", merged));
    });
}
//# sourceMappingURL=leads_action_type_report.js.map