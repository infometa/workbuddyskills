// Auto-generated from Go SDK — module: xijing_page_interactive
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerXijingPageInteractiveTools(server) {
    server.tool("xijing_page_interactive_add", "蹊径-创建互动落地页", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/xijing_page_interactive/add", merged));
    });
}
//# sourceMappingURL=xijing_page_interactive.js.map