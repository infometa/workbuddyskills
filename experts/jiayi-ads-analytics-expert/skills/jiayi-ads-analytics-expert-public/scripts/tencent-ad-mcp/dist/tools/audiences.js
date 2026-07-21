import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAudienceTools(server) {
    server.tool("custom_audiences_get", "获取自定义人群列表 (Get custom audiences)", {
        account_id: z.number().describe("广告主账户ID"),
        filtering: z
            .array(z.object({
            field: z.string(),
            operator: z.string(),
            values: z.array(z.string()),
        }))
            .optional(),
        page: z.number().optional().default(1),
        page_size: z.number().optional().default(10),
        fields: z.array(z.string()).optional(),
    }, async (params) => jsonText(await apiGet("/custom_audiences/get", params)));
    server.tool("custom_audiences_add", "创建自定义人群 (Create custom audience)", {
        account_id: z.number().describe("广告主账户ID"),
        audience_name: z.string().describe("人群名称"),
        audience_type: z.string().describe("人群类型"),
        description: z.string().optional().describe("人群描述"),
    }, async (params) => jsonText(await apiPost("/custom_audiences/add", params)));
    server.tool("custom_audiences_update", "更新自定义人群 (Update custom audience)", {
        account_id: z.number().describe("广告主账户ID"),
        audience_id: z.number().describe("人群ID"),
        audience_name: z.string().optional().describe("人群名称"),
        description: z.string().optional().describe("人群描述"),
    }, async (params) => jsonText(await apiPost("/custom_audiences/update", params)));
    server.tool("custom_audiences_delete", "删除自定义人群 (Delete custom audience)", {
        account_id: z.number().describe("广告主账户ID"),
        audience_id: z.number().describe("人群ID"),
    }, async (params) => jsonText(await apiPost("/custom_audiences/delete", params)));
    server.tool("targetings_get", "获取定向详情 (Get targeting details)", {
        account_id: z.number().describe("广告主账户ID"),
        targeting_id: z.number().optional().describe("定向ID"),
        fields: z.array(z.string()).optional(),
    }, async (params) => jsonText(await apiPost("/targetings/get", params)));
}
//# sourceMappingURL=audiences.js.map