// Auto-generated from Go SDK — module: video_channel_leads_data
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerVideoChannelLeadsDataTools(server) {
    server.tool("video_channel_leads_data_get", "获取线索数据", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/video_channel_leads_data/get", merged));
    });
}
//# sourceMappingURL=video_channel_leads_data.js.map