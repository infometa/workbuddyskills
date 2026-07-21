// Auto-generated from Go SDK — module: local_stores_address_parsing_result
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLocalStoresAddressParsingResultTools(server) {
    server.tool("local_stores_address_parsing_result_get", "解析门店地址", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/local_stores_address_parsing_result/get", merged));
    });
}
//# sourceMappingURL=local_stores_address_parsing_result.js.map