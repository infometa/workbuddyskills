// Auto-generated from Go SDK — module: account_version
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAccountVersionTools(server) {
    server.tool("account_version_get", "获取广告主新版API投放状态版本", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/account_version/get", merged));
    });
}
//# sourceMappingURL=account_version.js.map