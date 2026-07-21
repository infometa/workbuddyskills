// Auto-generated from Go SDK — module: rtaexp_dsp_tag_data
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerRtaexpDspTagDataTools(server) {
    server.tool("rtaexp_dsp_tag_data_get", "dsp_tag数据查询", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/rtaexp_dsp_tag_data/get", merged));
    });
}
//# sourceMappingURL=rtaexp_dsp_tag_data.js.map