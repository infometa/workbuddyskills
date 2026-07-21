// Auto-generated from Go SDK — module: wechat_pages_csgrouplist
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWechatPagesCsgrouplistTools(server) {
    server.tool("wechat_pages_csgrouplist_add", "增加企业微信组件客服组", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_pages_csgrouplist/add", merged));
    });
    server.tool("wechat_pages_csgrouplist_get", "获取企业微信客服组列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wechat_pages_csgrouplist/get", merged));
    });
    server.tool("wechat_pages_csgrouplist_update", "更新企业微信组件客服组", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/wechat_pages_csgrouplist/update", merged));
    });
}
//# sourceMappingURL=wechat_pages_csgrouplist.js.map