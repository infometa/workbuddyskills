import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerAdvertiserTools(server) {
    server.tool("advertiser_get", "获取广告主信息 (Get advertiser info)", {
        account_id: z.number().optional().describe("广告主账户ID"),
        fields: z
            .array(z.string())
            .optional()
            .describe("返回字段列表，如 ['account_id','corporation_name']"),
        page: z.number().optional().default(1),
        page_size: z.number().optional().default(10),
    }, async (params) => jsonText(await apiGet("/advertiser/get", params)));
    server.tool("advertiser_add", "添加服务商子客 (Add sub-account under agency)", {
        account_id: z.number().describe("广告主账户ID"),
        corporation_name: z.string().describe("公司名称"),
        certification_image_id: z.string().optional().describe("资质图片ID"),
    }, async (params) => jsonText(await apiPost("/advertiser/add", params)));
    server.tool("advertiser_update", "更新广告主信息 (Update advertiser info)", {
        account_id: z.number().describe("广告主账户ID"),
        corporation_name: z.string().optional().describe("公司名称"),
        daily_budget: z.number().optional().describe("日预算，单位分"),
    }, async (params) => jsonText(await apiPost("/advertiser/update", params)));
    server.tool("advertiser_update_daily_budget", "更新广告主日预算 (Update advertiser daily budget)", {
        account_id: z.number().describe("广告主账户ID"),
        daily_budget: z.number().describe("日预算，单位分"),
    }, async (params) => jsonText(await apiPost("/advertiser/update_daily_budget", params)));
}
//# sourceMappingURL=advertiser.js.map