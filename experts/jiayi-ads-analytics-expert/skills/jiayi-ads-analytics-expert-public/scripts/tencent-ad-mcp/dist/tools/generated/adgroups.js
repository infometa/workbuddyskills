// Auto-generated from Go SDK — module: adgroups
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAdgroupsTools(server) {
    server.tool("adgroups_update_datetime", "批量修改广告投放起止时间", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/adgroups/update_datetime", merged));
    });
}
//# sourceMappingURL=adgroups.js.map