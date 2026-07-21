// Auto-generated from Go SDK — module: user_action_set_reports
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerUserActionSetReportsTools(server) {
    server.tool("user_action_set_reports_get", "获取用户行为数据源报表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/user_action_set_reports/get", merged));
    });
}
//# sourceMappingURL=user_action_set_reports.js.map