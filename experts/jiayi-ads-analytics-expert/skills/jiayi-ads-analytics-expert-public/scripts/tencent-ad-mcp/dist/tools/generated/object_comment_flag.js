// Auto-generated from Go SDK — module: object_comment_flag
import { z } from "zod/v4";
import { apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerObjectCommentFlagTools(server) {
    server.tool("object_comment_flag_update", "设置视频号评论管理", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/object_comment_flag/update", merged));
    });
}
//# sourceMappingURL=object_comment_flag.js.map