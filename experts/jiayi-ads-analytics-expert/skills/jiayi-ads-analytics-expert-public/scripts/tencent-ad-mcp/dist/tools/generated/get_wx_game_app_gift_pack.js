// Auto-generated from Go SDK — module: get_wx_game_app_gift_pack
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerGetWxGameAppGiftPackTools(server) {
    server.tool("get_wx_game_app_gift_pack_get", "获取游戏中心礼包", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/get_wx_game_app_gift_pack/get", merged));
    });
}
//# sourceMappingURL=get_wx_game_app_gift_pack.js.map