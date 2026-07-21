// Auto-generated from Go SDK — module: wechat_channels_ad_account_wechat_binding
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatChannelsAdAccountWechatBindingTools(server) {
    server.tool("wechat_channels_ad_account_wechat_binding_add", "视频号开户绑定微信号", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_channels_ad_account_wechat_binding/add", merged));
    });
    server.tool("wechat_channels_ad_account_wechat_binding_get", "视频号开户绑定微信状态查询", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_channels_ad_account_wechat_binding/get", merged));
    });
}
//# sourceMappingURL=wechat_channels_ad_account_wechat_binding.js.map