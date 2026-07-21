// Auto-generated from Go SDK — module: wallet_transfer
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWalletTransferTools(server) {
    server.tool("wallet_transfer_add", "发起代理商与钱包之间转账", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wallet_transfer/add", merged));
    });
}
//# sourceMappingURL=wallet_transfer.js.map