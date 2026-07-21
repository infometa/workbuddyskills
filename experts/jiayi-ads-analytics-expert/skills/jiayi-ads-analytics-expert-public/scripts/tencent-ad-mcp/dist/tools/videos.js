import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerVideoTools(server) {
    server.tool("videos_get", "获取视频素材列表 (Get videos)", {
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
        fields: z.array(z.string()).optional(),
    }, async (params) => jsonText(await apiGet("/videos/get", params)));
    server.tool("videos_delete", "删除视频素材 (Delete video)", {
        account_id: z.number().describe("广告主账户ID"),
        video_id: z.string().describe("视频ID"),
    }, async (params) => jsonText(await apiPost("/videos/delete", params)));
    server.tool("videos_update", "更新视频素材信息 (Update video info)", {
        account_id: z.number().describe("广告主账户ID"),
        video_id: z.string().describe("视频ID"),
        description: z.string().optional().describe("视频描述"),
    }, async (params) => jsonText(await apiPost("/videos/update", params)));
}
//# sourceMappingURL=videos.js.map