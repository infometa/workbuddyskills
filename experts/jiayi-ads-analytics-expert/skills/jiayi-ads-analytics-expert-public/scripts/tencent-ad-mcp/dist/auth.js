import { writeFileSync } from "fs";
import { config } from "./config.js";
export async function refreshToken() {
    const params = new URLSearchParams({
        client_id: config.clientId,
        client_secret: config.clientSecret,
        grant_type: "refresh_token",
        refresh_token: config.refreshToken,
    });
    const url = `${config.baseUrl}/oauth/token?${params}`;
    const resp = await fetch(url);
    const json = (await resp.json());
    if (json.code !== 0 || !json.data) {
        throw new Error(`Token refresh failed: [${json.code}] ${json.message_cn || json.message}`);
    }
    const { access_token, refresh_token } = json.data;
    // Update in-memory config
    config.accessToken = access_token;
    config.refreshToken = refresh_token;
    // Persist to file
    try {
        writeFileSync(config.tokenFile, JSON.stringify({ access_token, refresh_token, updated_at: new Date().toISOString() }, null, 2));
    }
    catch {
        // Non-fatal: token still works in memory
    }
    return { accessToken: access_token, refreshToken: refresh_token };
}
export async function exchangeAuthCode(authorizationCode, redirectUri) {
    const params = new URLSearchParams({
        client_id: config.clientId,
        client_secret: config.clientSecret,
        grant_type: "authorization_code",
        authorization_code: authorizationCode,
        redirect_uri: redirectUri,
    });
    const url = `${config.baseUrl}/oauth/token?${params}`;
    const resp = await fetch(url);
    const json = (await resp.json());
    if (json.code !== 0 || !json.data) {
        throw new Error(`Token exchange failed: [${json.code}] ${json.message_cn || json.message}`);
    }
    const { access_token, refresh_token } = json.data;
    config.accessToken = access_token;
    config.refreshToken = refresh_token;
    try {
        writeFileSync(config.tokenFile, JSON.stringify({ access_token, refresh_token, updated_at: new Date().toISOString() }, null, 2));
    }
    catch {
        // Non-fatal
    }
    return { accessToken: access_token, refreshToken: refresh_token };
}
//# sourceMappingURL=auth.js.map