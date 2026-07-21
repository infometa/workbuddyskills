// Auto-generated from Go SDK — module: programmed_commponent_result
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerProgrammedCommponentResultTools(server) {
    server.tool("programmed_commponent_result_get", "组件化创意衍生成品查询接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/programmed_commponent_result/get", merged));
    });
}
//# sourceMappingURL=programmed_commponent_result.js.map