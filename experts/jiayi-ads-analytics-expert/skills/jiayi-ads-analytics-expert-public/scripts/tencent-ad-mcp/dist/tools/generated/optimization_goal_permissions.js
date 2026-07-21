// Auto-generated from Go SDK — module: optimization_goal_permissions
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerOptimizationGoalPermissionsTools(server) {
    server.tool("optimization_goal_permissions_get", "查询优化目标权限", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/optimization_goal_permissions/get", merged));
    });
}
//# sourceMappingURL=optimization_goal_permissions.js.map