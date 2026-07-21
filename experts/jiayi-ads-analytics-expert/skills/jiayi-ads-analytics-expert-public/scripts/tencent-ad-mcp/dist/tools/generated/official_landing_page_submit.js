// Auto-generated from Go SDK — module: official_landing_page_submit
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerOfficialLandingPageSubmitTools(server) {
    server.tool("official_landing_page_submit_update", "官方落地页-送审落地页", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/official_landing_page_submit/update", merged));
    });
}
//# sourceMappingURL=official_landing_page_submit.js.map