// Auto-generated from Go SDK — module: wx_game_playable_page
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerWxGamePlayablePageTools(server) {
    server.tool("wx_game_playable_page_get", "获取微信小游戏试玩页", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/wx_game_playable_page/get", merged));
    });
}
//# sourceMappingURL=wx_game_playable_page.js.map