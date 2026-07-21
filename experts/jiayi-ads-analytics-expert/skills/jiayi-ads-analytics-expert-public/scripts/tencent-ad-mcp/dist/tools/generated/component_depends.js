// Auto-generated from Go SDK — module: component_depends
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerComponentDependsTools(server) {
    server.tool("component_depends_get", "查询创意组件字段选项对于其他组件的依赖信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/component_depends/get", merged));
    });
}
//# sourceMappingURL=component_depends.js.map