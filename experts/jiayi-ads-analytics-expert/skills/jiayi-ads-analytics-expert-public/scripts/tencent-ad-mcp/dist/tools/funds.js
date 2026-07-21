import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerFundTools(server) {
    server.tool("funds_get", "获取资金账户信息 (Get fund account info)", {
        account_id: z.number().describe("广告主账户ID"),
        fields: z.array(z.string()).optional(),
    }, async (params) => jsonText(await apiGet("/funds/get", params)));
    server.tool("fund_transfer_add", "资金划转 (Transfer funds between accounts)", {
        account_id: z.number().describe("广告主账户ID"),
        amount: z.number().describe("划转金额，单位分"),
        transfer_type: z.string().describe("划转类型"),
        external_bill_no: z.string().optional().describe("外部单号"),
    }, async (params) => jsonText(await apiPost("/fund_transfer/add", params)));
}
//# sourceMappingURL=funds.js.map