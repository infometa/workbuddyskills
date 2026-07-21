// Auto-generated from Go SDK — module: wallet_invoice
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWalletInvoiceTools(server) {
    server.tool("wallet_invoice_get", "共享钱包流水相关信息查询", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wallet_invoice/get", merged));
    });
}
//# sourceMappingURL=wallet_invoice.js.map