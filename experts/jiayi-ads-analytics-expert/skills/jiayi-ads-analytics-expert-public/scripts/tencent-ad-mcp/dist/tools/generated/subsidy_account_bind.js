// Auto-generated from Go SDK — module: subsidy_account_bind
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerSubsidyAccountBindTools(server) {
    server.tool("subsidy_account_bind_add", "补贴账号绑定或解绑广告账户", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/subsidy_account_bind/add", merged));
    });
}
//# sourceMappingURL=subsidy_account_bind.js.map