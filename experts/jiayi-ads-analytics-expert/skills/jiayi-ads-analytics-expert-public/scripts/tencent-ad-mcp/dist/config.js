import { readFileSync, existsSync } from "fs";
import { homedir } from "os";
import { join } from "path";
const TOKEN_FILE = process.env.TENCENT_AD_TOKEN_FILE || join(homedir(), ".tencent-ad-token.json");
function loadPersistedTokens() {
    if (!existsSync(TOKEN_FILE))
        return null;
    try {
        return JSON.parse(readFileSync(TOKEN_FILE, "utf-8"));
    }
    catch {
        return null;
    }
}
const persisted = loadPersistedTokens();
export const config = {
    baseUrl: "https://api.e.qq.com/v3.0",
    clientId: process.env.TENCENT_AD_CLIENT_ID ?? "",
    clientSecret: process.env.TENCENT_AD_CLIENT_SECRET ?? "",
    accessToken: persisted?.access_token ?? process.env.TENCENT_AD_ACCESS_TOKEN ?? "",
    refreshToken: persisted?.refresh_token ?? process.env.TENCENT_AD_REFRESH_TOKEN ?? "",
    accountId: process.env.TENCENT_AD_ACCOUNT_ID ?? "",
    tokenFile: TOKEN_FILE,
};
//# sourceMappingURL=config.js.map