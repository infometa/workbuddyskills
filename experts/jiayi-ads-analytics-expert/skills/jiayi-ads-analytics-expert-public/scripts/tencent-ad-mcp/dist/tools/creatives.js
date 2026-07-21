import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerCreativeTools(server) {
    server.tool("dynamic_creatives_get", "获取创意列表 (Get dynamic creatives)", {
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
    }, async (params) => jsonText(await apiGet("/dynamic_creatives/get", params)));
    server.tool("dynamic_creatives_add", "创建创意 (Create dynamic creative)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_id: z.number().describe("广告组ID"),
        creative_components: z.record(z.string(), z.unknown()).optional().describe("创意组件"),
        creative_template_id: z.number().optional().describe("创意模板ID"),
    }, async (params) => jsonText(await apiPost("/dynamic_creatives/add", params)));
    server.tool("dynamic_creatives_update", "更新创意 (Update dynamic creative)", {
        account_id: z.number().describe("广告主账户ID"),
        dynamic_creative_id: z.number().describe("创意ID"),
        creative_components: z.record(z.string(), z.unknown()).optional().describe("创意组件"),
    }, async (params) => jsonText(await apiPost("/dynamic_creatives/update", params)));
    server.tool("dynamic_creatives_delete", "删除创意 (Delete dynamic creative)", {
        account_id: z.number().describe("广告主账户ID"),
        dynamic_creative_id: z.number().describe("创意ID"),
    }, async (params) => jsonText(await apiPost("/dynamic_creatives/delete", params)));
    server.tool("adcreative_previews_get", "获取创意预览 (Get creative previews)", {
        account_id: z.number().describe("广告主账户ID"),
        filtering: z
            .array(z.object({
            field: z.string(),
            operator: z.string(),
            values: z.array(z.string()),
        }))
            .describe("过滤条件"),
    }, async (params) => jsonText(await apiGet("/adcreative_previews/get", params)));
}
//# sourceMappingURL=creatives.js.map