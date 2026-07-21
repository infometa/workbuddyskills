// Auto-generated from Go SDK — module: punish_metrics
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerPunishMetricsTools(server) {
    server.tool("punish_metrics_get", "获取处罚指标数据", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/punish_metrics/get", merged));
    });
}
//# sourceMappingURL=punish_metrics.js.map