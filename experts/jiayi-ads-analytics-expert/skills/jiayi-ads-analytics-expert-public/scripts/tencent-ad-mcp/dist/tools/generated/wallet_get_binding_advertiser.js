// Auto-generated from Go SDK — module: wallet_get_binding_advertiser
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWalletGetBindingAdvertiserTools(server) {
    server.tool("wallet_get_binding_advertiser_get", "查询单个共享钱包下的关联账户信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wallet_get_binding_advertiser/get", merged));
    });
}
//# sourceMappingURL=wallet_get_binding_advertiser.js.map