// Auto-generated from Go SDK — module: official_landing_page_detail
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerOfficialLandingPageDetailTools(server) {
    server.tool("official_landing_page_detail_get", "官方落地页-获取落地页详情", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/official_landing_page_detail/get", merged));
    });
}
//# sourceMappingURL=official_landing_page_detail.js.map