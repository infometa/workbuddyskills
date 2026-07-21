import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
const filteringSchema = z.array(z.object({
    field: z.string(),
    operator: z.string(),
    values: z.array(z.string()),
}));
export function registerAdgroupTools(server) {
    server.tool("adgroups_get", "获取广告组列表 (Get ad groups)", {
        account_id: z.number().describe("广告主账户ID"),
        filtering: filteringSchema.optional().describe("过滤条件"),
        page: z.number().optional().default(1),
        page_size: z.number().optional().default(10),
        fields: z.array(z.string()).optional().describe("返回字段列表"),
    }, async (params) => jsonText(await apiGet("/adgroups/get", params)));
    server.tool("adgroups_add", "创建广告组 (Create ad group)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_name: z.string().describe("广告组名称"),
        marketing_goal: z.string().describe("营销目的，如 MARKETING_GOAL_PRODUCT_SALES"),
        marketing_sub_goal: z.string().optional().describe("营销子目标"),
        marketing_carrier_type: z.string().optional().describe("营销载体类型"),
        begin_date: z.string().optional().describe("开始日期 YYYY-MM-DD"),
        end_date: z.string().optional().describe("结束日期 YYYY-MM-DD"),
        bid_amount: z.number().optional().describe("出价，单位分"),
        optimization_goal: z.string().optional().describe("优化目标"),
        daily_budget: z.number().optional().describe("日预算，单位分"),
        site_set: z.array(z.string()).optional().describe("投放版位"),
        configured_status: z.string().optional().describe("广告组状态"),
        bid_mode: z.string().optional().describe("出价方式"),
        smart_bid_type: z.string().optional().describe("智能出价类型"),
    }, async (params) => jsonText(await apiPost("/adgroups/add", params)));
    server.tool("adgroups_update", "更新广告组 (Update ad group)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_id: z.number().describe("广告组ID"),
        adgroup_name: z.string().optional().describe("广告组名称"),
        begin_date: z.string().optional().describe("开始日期"),
        end_date: z.string().optional().describe("结束日期"),
        bid_amount: z.number().optional().describe("出价，单位分"),
        daily_budget: z.number().optional().describe("日预算，单位分"),
        configured_status: z.string().optional().describe("广告组状态"),
    }, async (params) => jsonText(await apiPost("/adgroups/update", params)));
    server.tool("adgroups_delete", "删除广告组 (Delete ad group)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_id: z.number().describe("广告组ID"),
    }, async (params) => jsonText(await apiPost("/adgroups/delete", params)));
    server.tool("adgroups_update_configured_status", "更新广告组状态 (Update ad group status: enable/pause)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_id: z.number().describe("广告组ID"),
        configured_status: z.string().describe("状态：AD_STATUS_NORMAL / AD_STATUS_SUSPEND"),
    }, async (params) => jsonText(await apiPost("/adgroups/update_configured_status", params)));
    server.tool("adgroups_update_daily_budget", "更新广告组日预算 (Update ad group daily budget)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_id: z.number().describe("广告组ID"),
        daily_budget: z.number().describe("日预算，单位分"),
    }, async (params) => jsonText(await apiPost("/adgroups/update_daily_budget", params)));
    server.tool("adgroups_update_bid_amount", "更新广告组出价 (Update ad group bid amount)", {
        account_id: z.number().describe("广告主账户ID"),
        adgroup_id: z.number().describe("广告组ID"),
        bid_amount: z.number().describe("出价，单位分"),
    }, async (params) => jsonText(await apiPost("/adgroups/update_bid_amount", params)));
}
//# sourceMappingURL=adgroups.js.map