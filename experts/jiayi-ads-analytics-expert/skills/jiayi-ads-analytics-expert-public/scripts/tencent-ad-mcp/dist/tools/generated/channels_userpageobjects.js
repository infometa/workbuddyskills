// Auto-generated from Go SDK — module: channels_userpageobjects
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerChannelsUserpageobjectsTools(server) {
    server.tool("channels_userpageobjects_get", "获取视频号动态列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/channels_userpageobjects/get", merged));
    });
}
//# sourceMappingURL=channels_userpageobjects.js.map