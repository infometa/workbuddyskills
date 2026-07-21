// Auto-generated from Go SDK — module: wechat_pages_custom
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatPagesCustomTools(server) {
    server.tool("wechat_pages_custom_add", "基于组件创建微信原生页", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_pages_custom/add", merged));
    });
}
//# sourceMappingURL=wechat_pages_custom.js.map