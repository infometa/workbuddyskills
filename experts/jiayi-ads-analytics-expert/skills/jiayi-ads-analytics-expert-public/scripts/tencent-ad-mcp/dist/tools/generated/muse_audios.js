// Auto-generated from Go SDK — module: muse_audios
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMuseAudiosTools(server) {
    server.tool("muse_audios_get", "获取妙思版权音频列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/muse_audios/get", merged));
    });
}
//# sourceMappingURL=muse_audios.js.map