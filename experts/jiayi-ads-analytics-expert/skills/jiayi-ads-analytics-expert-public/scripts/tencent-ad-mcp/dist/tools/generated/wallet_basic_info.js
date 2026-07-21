// Auto-generated from Go SDK — module: wallet_basic_info
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWalletBasicInfoTools(server) {
    server.tool("wallet_basic_info_get", "通过钱包id去查询共享钱包基础信息", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wallet_basic_info/get", merged));
    });
}
//# sourceMappingURL=wallet_basic_info.js.map