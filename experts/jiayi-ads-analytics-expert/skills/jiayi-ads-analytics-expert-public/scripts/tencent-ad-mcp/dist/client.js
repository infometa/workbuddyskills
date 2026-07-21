import { randomBytes } from "crypto";
import { config } from "./config.js";
import { refreshToken } from "./auth.js";
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;
function generateNonce() {
    return randomBytes(16).toString("hex");
}
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
async function rawRequest(path, method, params) {
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const nonce = generateNonce();
    const commonParams = {
        access_token: config.accessToken,
        timestamp,
        nonce,
    };
    let url;
    let body;
    const headers = {
        Accept: "application/json",
    };
    if (method === "GET") {
        const qs = new URLSearchParams(commonParams);
        if (params) {
            for (const [k, v] of Object.entries(params)) {
                if (v === undefined || v === null)
                    continue;
                if (Array.isArray(v) || typeof v === "object") {
                    qs.set(k, JSON.stringify(v));
                }
                else {
                    qs.set(k, String(v));
                }
            }
        }
        url = `${config.baseUrl}${path}?${qs}`;
    }
    else {
        const qs = new URLSearchParams(commonParams);
        url = `${config.baseUrl}${path}?${qs}`;
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(params ?? {});
    }
    const resp = await fetch(url, { method, headers, body });
    return (await resp.json());
}
export async function apiRequest(path, method, params) {
    let lastError = null;
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        const result = await rawRequest(path, method, params);
        // Success
        if (result.code === 0)
            return result;
        // Token expired — try refresh once
        if ((result.code === 11002 || result.code === 11005) &&
            attempt === 0 &&
            config.refreshToken) {
            try {
                await refreshToken();
                continue; // Retry with new token
            }
            catch (refreshErr) {
                return result; // Return original error if refresh fails
            }
        }
        // Rate limited — retry with backoff
        if (result.code === 11100 && attempt < MAX_RETRIES) {
            await sleep(RETRY_DELAY_MS * (attempt + 1));
            continue;
        }
        // Non-retryable error
        return result;
    }
    throw lastError ?? new Error("Unexpected retry exhaustion");
}
/** Convenience: GET request */
export function apiGet(path, params) {
    return apiRequest(path, "GET", params);
}
/** Convenience: POST request */
export function apiPost(path, params) {
    return apiRequest(path, "POST", params);
}
//# sourceMappingURL=client.js.map