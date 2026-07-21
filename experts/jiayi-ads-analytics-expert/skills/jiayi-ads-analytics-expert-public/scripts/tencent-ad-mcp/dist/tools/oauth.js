import { z } from "zod/v4";
import { refreshToken, exchangeAuthCode } from "../auth.js";
import { config } from "../config.js";
export function registerOAuthTools(server) {
    server.tool("oauth_refresh_token", "刷新 access_token (Refresh access token)", {}, async () => {
        try {
            const result = await refreshToken();
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            success: true,
                            access_token: result.accessToken,
                            refresh_token: result.refreshToken,
                        }, null, 2),
                    },
                ],
            };
        }
        catch (err) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Token 刷新失败: ${err instanceof Error ? err.message : String(err)}`,
                    },
                ],
                isError: true,
            };
        }
    });
    server.tool("oauth_exchange_code", "用授权码换取 token (Exchange authorization code for token)", {
        authorization_code: z.string().describe("OAuth 授权码"),
        redirect_uri: z.string().describe("回调地址"),
    }, async ({ authorization_code, redirect_uri }) => {
        try {
            const result = await exchangeAuthCode(authorization_code, redirect_uri);
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            success: true,
                            access_token: result.accessToken,
                            refresh_token: result.refreshToken,
                        }, null, 2),
                    },
                ],
            };
        }
        catch (err) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Token 交换失败: ${err instanceof Error ? err.message : String(err)}`,
                    },
                ],
                isError: true,
            };
        }
    });
    server.tool("oauth_get_authorize_url", "获取 OAuth 授权链接 (Get OAuth authorize URL)", {
        redirect_uri: z.string().describe("回调地址"),
        state: z.string().optional().describe("自定义 state 参数"),
    }, async ({ redirect_uri, state }) => {
        const params = new URLSearchParams({
            client_id: config.clientId,
            redirect_uri,
            state: state ?? "",
        });
        const url = `https://developers.e.qq.com/oauth/authorize?${params}`;
        return {
            content: [
                {
                    type: "text",
                    text: `请在浏览器中打开以下链接完成授权:\n${url}`,
                },
            ],
        };
    });
}
//# sourceMappingURL=oauth.js.map