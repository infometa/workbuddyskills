// Auto-generated from Go SDK — module: audience_grant_relations
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAudienceGrantRelationsTools(server) {
    server.tool("audience_grant_relations_add", "添加人群授权", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/audience_grant_relations/add", merged));
    });
    server.tool("audience_grant_relations_get", "获取人群授权信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/audience_grant_relations/get", merged));
    });
}
//# sourceMappingURL=audience_grant_relations.js.map