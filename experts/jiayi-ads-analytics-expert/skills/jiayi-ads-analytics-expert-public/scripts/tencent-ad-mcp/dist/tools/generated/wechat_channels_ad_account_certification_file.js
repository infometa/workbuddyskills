// Auto-generated from Go SDK — module: wechat_channels_ad_account_certification_file
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatChannelsAdAccountCertificationFileTools(server) {
    server.tool("wechat_channels_ad_account_certification_file_add", "视频号开户资质上传", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_channels_ad_account_certification_file/add", merged));
    });
}
//# sourceMappingURL=wechat_channels_ad_account_certification_file.js.map