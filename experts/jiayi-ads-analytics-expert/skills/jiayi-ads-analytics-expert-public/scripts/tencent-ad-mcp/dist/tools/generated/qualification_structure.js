// Auto-generated from Go SDK — module: qualification_structure
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerQualificationStructureTools(server) {
    server.tool("qualification_structure_get", "获取广告主资质结构", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/qualification_structure/get", merged));
    });
}
//# sourceMappingURL=qualification_structure.js.map