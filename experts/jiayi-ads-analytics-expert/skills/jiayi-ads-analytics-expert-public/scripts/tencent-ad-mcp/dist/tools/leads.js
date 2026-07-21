import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerLeadTools(server) {
    server.tool("leads_list_get", "获取线索列表 (Get leads list)", {
        account_id: z.number().describe("广告主账户ID"),
        time_range: z.object({
            start_time: z.string().describe("开始时间 YYYY-MM-DD HH:mm:ss"),
            end_time: z.string().describe("结束时间 YYYY-MM-DD HH:mm:ss"),
        }),
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
    }, async (params) => jsonText(await apiGet("/leads_list/get", params)));
    server.tool("leads_add", "创建线索 (Create lead)", {
        account_id: z.number().describe("广告主账户ID"),
        lead_name: z.string().describe("线索名称"),
        lead_phone: z.string().optional().describe("线索电话"),
    }, async (params) => jsonText(await apiPost("/leads/add", params)));
    server.tool("leads_update", "更新线索 (Update lead)", {
        account_id: z.number().describe("广告主账户ID"),
        lead_id: z.number().describe("线索ID"),
        lead_name: z.string().optional().describe("线索名称"),
    }, async (params) => jsonText(await apiPost("/leads/update", params)));
    server.tool("leads_claim_update", "认领线索 (Claim lead)", {
        account_id: z.number().describe("广告主账户ID"),
        lead_clue_id: z.number().describe("线索ID"),
    }, async (params) => jsonText(await apiPost("/leads_claim/update", params)));
}
//# sourceMappingURL=leads.js.map