// Auto-generated from Go SDK — module: wallet_edit
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWalletEditTools(server) {
    server.tool("wallet_edit_add", "编辑共享钱包基础信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wallet_edit/add", merged));
    });
}
//# sourceMappingURL=wallet_edit.js.map