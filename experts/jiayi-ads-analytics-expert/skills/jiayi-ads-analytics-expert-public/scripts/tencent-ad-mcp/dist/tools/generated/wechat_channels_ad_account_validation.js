// Auto-generated from Go SDK — module: wechat_channels_ad_account_validation
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatChannelsAdAccountValidationTools(server) {
    server.tool("wechat_channels_ad_account_validation_get", "视频号一键开户校验", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_channels_ad_account_validation/get", merged));
    });
}
//# sourceMappingURL=wechat_channels_ad_account_validation.js.map