// Auto-generated from Go SDK — module: material_dcaset
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMaterialDcasetTools(server) {
    server.tool("material_dcaset_add", "素材DCA集合绑定新增", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/material_dcaset/add", merged));
    });
}
//# sourceMappingURL=material_dcaset.js.map