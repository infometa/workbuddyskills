// Auto-generated from Go SDK — module: wechat_pages_csgroup_user
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatPagesCsgroupUserTools(server) {
    server.tool("wechat_pages_csgroup_user_get", "获取企业微信组件客服列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_pages_csgroup_user/get", merged));
    });
}
//# sourceMappingURL=wechat_pages_csgroup_user.js.map