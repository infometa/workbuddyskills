// Auto-generated from Go SDK — module: programmed_material_mappings
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProgrammedMaterialMappingsTools(server) {
    server.tool("programmed_material_mappings_get", "获取衍生素材映射关系接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/programmed_material_mappings/get", merged));
    });
}
//# sourceMappingURL=programmed_material_mappings.js.map