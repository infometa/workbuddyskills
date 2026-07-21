// Auto-generated from Go SDK — module: user_organization_authentication
import { z } from "zod/v4";
import { apiGet } from "../../client.js";
const jsonText = (data) => ({
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
export function registerUserOrganizationAuthenticationTools(server) {
    server.tool("user_organization_authentication_get", "查询用户组织认证", {
        account_id: z.number().optional().describe("广告主账户ID"),
        params: z.record(z.string(), z.unknown()).optional().describe("其他请求参数 (key-value)"),
    }, async ({ account_id, params }) => {
        const merged = { ...params, ...(account_id != null ? { account_id } : {}) };
        return jsonText(await apiGet("/user_organization_authentication/get", merged));
    });
}
//# sourceMappingURL=user_organization_authentication.js.map