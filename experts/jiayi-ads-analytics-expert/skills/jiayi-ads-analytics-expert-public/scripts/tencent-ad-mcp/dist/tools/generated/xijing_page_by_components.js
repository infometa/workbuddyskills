// Auto-generated from Go SDK — module: xijing_page_by_components
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerXijingPageByComponentsTools(server) {
    server.tool("xijing_page_by_components_add", "蹊径-基于组件创建落地页", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/xijing_page_by_components/add", merged));
    });
}
//# sourceMappingURL=xijing_page_by_components.js.map