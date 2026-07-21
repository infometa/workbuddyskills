// Auto-generated from Go SDK — module: conversion_link_asset_available
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerConversionLinkAssetAvailableTools(server) {
    server.tool("conversion_link_asset_available_get", "获取可投放链路列表", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/conversion_link_asset_available/get", merged));
    });
}
//# sourceMappingURL=conversion_link_asset_available.js.map