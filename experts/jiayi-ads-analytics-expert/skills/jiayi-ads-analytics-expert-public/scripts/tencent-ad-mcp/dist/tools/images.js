import { z } from "zod/v4";
import { apiGet, apiPost } from "../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerImageTools(server) {
    server.tool("images_get", "获取图片素材列表 (Get images)", {
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
    }, async (params) => jsonText(await apiGet("/images/get", params)));
    server.tool("images_add", "上传图片素材 (Upload image via URL or base64)", {
        account_id: z.number().describe("广告主账户ID"),
        upload_type: z.string().describe("上传方式: UPLOAD_TYPE_FILE / UPLOAD_TYPE_URL"),
        signature: z.string().describe("图片签名 (MD5)"),
        image_url: z.string().optional().describe("图片URL（upload_type=UPLOAD_TYPE_URL 时）"),
        description: z.string().optional().describe("图片描述"),
    }, async (params) => jsonText(await apiPost("/images/add", params)));
    server.tool("images_delete", "删除图片素材 (Delete image)", {
        account_id: z.number().describe("广告主账户ID"),
        image_id: z.string().describe("图片ID"),
    }, async (params) => jsonText(await apiPost("/images/delete", params)));
    server.tool("images_update", "更新图片素材信息 (Update image info)", {
        account_id: z.number().describe("广告主账户ID"),
        image_id: z.string().describe("图片ID"),
        description: z.string().optional().describe("图片描述"),
    }, async (params) => jsonText(await apiPost("/images/update", params)));
}
//# sourceMappingURL=images.js.map