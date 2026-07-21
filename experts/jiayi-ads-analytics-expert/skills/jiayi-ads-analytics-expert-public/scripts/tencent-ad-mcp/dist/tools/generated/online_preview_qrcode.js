// Auto-generated from Go SDK — module: online_preview_qrcode
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerOnlinePreviewQrcodeTools(server) {
    server.tool("online_preview_qrcode_get", "获取在线预览二维码", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/online_preview_qrcode/get", merged));
    });
}
//# sourceMappingURL=online_preview_qrcode.js.map