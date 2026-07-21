// Auto-generated from Go SDK — module: muse_ai_task
import { z } from "zod/v4";
import { apiGet, apiPost } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerMuseAiTaskTools(server) {
    server.tool("muse_ai_task_add", "创建妙思任务接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiPost("/muse_ai_task/add", merged));
    });
    server.tool("muse_ai_task_get", "获取妙思任务结果接口", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/muse_ai_task/get", merged));
    });
}
//# sourceMappingURL=muse_ai_task.js.map