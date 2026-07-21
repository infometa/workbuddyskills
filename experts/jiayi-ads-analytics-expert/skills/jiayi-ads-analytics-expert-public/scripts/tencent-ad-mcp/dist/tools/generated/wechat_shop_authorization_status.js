// Auto-generated from Go SDK — module: wechat_shop_authorization_status
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatShopAuthorizationStatusTools(server) {
    server.tool("wechat_shop_authorization_status_update", "微信小店授权状态更新", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_shop_authorization_status/update", merged));
    });
}
//# sourceMappingURL=wechat_shop_authorization_status.js.map