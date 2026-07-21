// Auto-generated from Go SDK — module: wechat_channels_ad_account
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatChannelsAdAccountTools(server) {
    server.tool("wechat_channels_ad_account_add", "视频号开户", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_channels_ad_account/add", merged));
    });
    server.tool("wechat_channels_ad_account_delete", "删除开户记录", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_channels_ad_account/delete", merged));
    });
    server.tool("wechat_channels_ad_account_get", "查询视频号开户记录", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_channels_ad_account/get", merged));
    });
    server.tool("wechat_channels_ad_account_update", "视频号开户修改", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_channels_ad_account/update", merged));
    });
}
//# sourceMappingURL=wechat_channels_ad_account.js.map