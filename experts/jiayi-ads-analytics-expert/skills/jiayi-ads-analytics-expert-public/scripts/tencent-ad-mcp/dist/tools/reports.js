import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
const dateRangeSchema = z.object({
    start_date: z.string().describe("开始日期 YYYY-MM-DD"),
    end_date: z.string().describe("结束日期 YYYY-MM-DD"),
});
export function registerReportTools(server) {
    server.tool("daily_reports_get", "获取日报表数据 (Get daily reports)", {
        account_id: z.number().optional().describe("广告主账户ID"),
        level: z.string().describe("报表层级: REPORT_LEVEL_ADVERTISER / REPORT_LEVEL_CAMPAIGN / REPORT_LEVEL_ADGROUP / REPORT_LEVEL_AD"),
        date_range: dateRangeSchema.describe("日期范围"),
        group_by: z.array(z.string()).describe("分组字段"),
        fields: z.array(z.string()).describe("返回字段"),
        filtering: z
            .array(z.object({
            field: z.string(),
            operator: z.string(),
            values: z.array(z.string()),
        }))
            .optional(),
        page: z.number().optional().default(1),
        page_size: z.number().optional().default(10),
        order_by: z
            .array(z.object({ field: z.string(), order: z.string() }))
            .optional(),
    }, async (params) => jsonText(await apiGet("/daily_reports/get", params)));
    server.tool("hourly_reports_get", "获取时报表数据 (Get hourly reports)", {
        account_id: z.number().describe("广告主账户ID"),
        level: z.string().describe("报表层级"),
        date_range: z
            .object({
            start_date: z.string(),
            end_date: z.string(),
        })
            .describe("日期范围（最多3天）"),
        group_by: z.array(z.string()).describe("分组字段"),
        fields: z.array(z.string()).describe("返回字段"),
        filtering: z
            .array(z.object({
            field: z.string(),
            operator: z.string(),
            values: z.array(z.string()),
        }))
            .optional(),
        page: z.number().optional().default(1),
        page_size: z.number().optional().default(10),
    }, async (params) => jsonText(await apiGet("/hourly_reports/get", params)));
    server.tool("async_reports_add", "创建异步报表任务 (Create async report task)", {
        account_id: z.number().describe("广告主账户ID"),
        task_name: z.string().optional().describe("任务名称"),
        level: z.string().describe("报表层级"),
        date_range: dateRangeSchema,
        group_by: z.array(z.string()).describe("分组字段"),
        fields: z.array(z.string()).describe("返回字段"),
        filtering: z
            .array(z.object({
            field: z.string(),
            operator: z.string(),
            values: z.array(z.string()),
        }))
            .optional(),
    }, async (params) => jsonText(await apiPost("/async_reports/add", params)));
    server.tool("async_reports_get", "查询异步报表任务状态 (Get async report task status)", {
        account_id: z.number().optional().describe("广告主账户ID"),
        filtering: z
            .array(z.object({
            field: z.string(),
            operator: z.string(),
            values: z.array(z.string()),
        }))
            .optional(),
        page: z.number().optional().default(1),
        page_size: z.number().optional().default(10),
    }, async (params) => jsonText(await apiGet("/async_reports/get", params)));
    server.tool("async_report_files_get", "下载异步报表文件 (Get async report file download URL)", {
        account_id: z.number().describe("广告主账户ID"),
        task_id: z.number().describe("异步报表任务ID"),
    }, async (params) => jsonText(await apiGet("/async_report_files/get", params)));
}
//# sourceMappingURL=reports.js.map