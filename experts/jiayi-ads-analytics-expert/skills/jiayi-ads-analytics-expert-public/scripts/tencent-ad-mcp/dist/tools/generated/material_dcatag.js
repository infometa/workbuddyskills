// Auto-generated from Go SDK — module: material_dcatag
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMaterialDcatagTools(server) {
    server.tool("material_dcatag_add", "素材DCA标签绑定新增", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/material_dcatag/add", merged));
    });
    server.tool("material_dcatag_get", "素材DCA标签绑定查询", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/material_dcatag/get", merged));
    });
}
//# sourceMappingURL=material_dcatag.js.map