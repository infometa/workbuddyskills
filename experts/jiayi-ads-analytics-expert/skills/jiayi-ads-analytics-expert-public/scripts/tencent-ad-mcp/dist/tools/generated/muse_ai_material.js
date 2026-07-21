// Auto-generated from Go SDK — module: muse_ai_material
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMuseAiMaterialTools(server) {
    server.tool("muse_ai_material_add", "选择并保存妙思AI素材接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/muse_ai_material/add", merged));
    });
}
//# sourceMappingURL=muse_ai_material.js.map