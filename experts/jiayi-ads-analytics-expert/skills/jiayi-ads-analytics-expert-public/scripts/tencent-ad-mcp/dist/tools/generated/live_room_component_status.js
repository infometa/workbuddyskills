// Auto-generated from Go SDK — module: live_room_component_status
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLiveRoomComponentStatusTools(server) {
    server.tool("live_room_component_status_update", "更新直播间组件状态", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/live_room_component_status/update", merged));
    });
}
//# sourceMappingURL=live_room_component_status.js.map