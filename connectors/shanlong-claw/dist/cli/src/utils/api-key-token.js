"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildApiKeySignedHeaders = buildApiKeySignedHeaders;
exports.hasApiKeyTokenConfig = hasApiKeyTokenConfig;
exports.acquireBusinessTokensByApiKey = acquireBusinessTokensByApiKey;
const crypto_1 = require("crypto");
const env_1 = require("../env");
const logger_1 = require("../logger");
const http_timeout_1 = require("./http-timeout");
const RESPONSE_TOKEN_KEY_MAP = {
    ScmToken: 'fxscmToken',
    fxscmToken: 'fxscmToken',
    Cy7Token: 'wuuxiangCyToken',
    wuuxiangCyToken: 'wuuxiangCyToken',
    Cy7OldToken: 'cy7OldToken',
    cy7OldToken: 'cy7OldToken',
    Crm8Token: 'crm8Token',
    crm8Token: 'crm8Token',
    WxctToken: 'Wxcttoken',
    Wxcttoken: 'Wxcttoken',
    wxctToken: 'Wxcttoken',
    Cy7ReporterToken: 'cy7reporterToken',
    cy7reporterToken: 'cy7reporterToken',
    ReportToken: 'cy7reporterToken',
    reportToken: 'cy7reporterToken',
};
function normalizeBaseUrl(baseUrl) {
    return baseUrl.replace(/\/+$/, '');
}
function requireValue(value, label) {
    if (!value) {
        throw new Error(`缺少 ${label}`);
    }
    return value;
}
function buildSwapUrl(options) {
    const explicitUrl = options.url || (0, env_1.getEnv)('SL_API_KEY_SWAP_URL');
    if (explicitUrl) {
        return explicitUrl;
    }
    const baseUrl = requireValue(options.baseUrl || (0, env_1.getEnv)('SL_API_KEY_BASEURL') || (0, env_1.getEnv)('SL_SLY_BASEURL'), 'SL_API_KEY_BASEURL 或 SL_SLY_BASEURL');
    return `${normalizeBaseUrl(baseUrl)}/newProxy/auth-center/api/ano/account/apikey/swap`;
}
function buildApiKeySignedHeaders(appId, appSecret, body) {
    const nonce = String((0, crypto_1.randomInt)(0, 1000000)).padStart(6, '0');
    const timestamp = String(Date.now());
    const signatureText = `${appId}${nonce}${timestamp}${body}`;
    const signature = (0, crypto_1.createHmac)('sha256', appSecret).update(signatureText).digest('hex');
    return {
        'Content-Type': 'application/json;charset=UTF-8',
        'tcsl-bp-appid': appId,
        'tcsl-bp-nonce': nonce,
        'tcsl-bp-timestamp': timestamp,
        'tcsl-bp-signature': signature,
    };
}
function assertApiKeyTokenSuccess(response) {
    const code = response.code !== undefined ? String(response.code) : '';
    if (response.success === false || (code && code !== '2000' && code !== '200')) {
        const codeText = code ? ` code=${code}` : '';
        const messageText = response.message ? ` message=${response.message}` : '';
        throw new Error(`API Key 换 Token 业务错误:${codeText}${messageText}`.trim());
    }
}
function normalizeTokens(data) {
    const tokens = {};
    if (!data) {
        return tokens;
    }
    for (const [responseKey, storeKey] of Object.entries(RESPONSE_TOKEN_KEY_MAP)) {
        const value = data[responseKey];
        if (typeof value === 'string' && value) {
            tokens[storeKey] = value;
        }
    }
    const slyToken = data.slyToken;
    if (typeof slyToken === 'string' && slyToken) {
        tokens.slyToken = slyToken;
    }
    else if (slyToken && typeof slyToken === 'object' && !Array.isArray(slyToken)) {
        tokens.slyToken = JSON.stringify(slyToken);
    }
    return tokens;
}
function hasApiKeyTokenConfig() {
    return !!(0, env_1.getEnv)('SL_API_KEY').trim();
}
async function acquireBusinessTokensByApiKey(options = {}) {
    const apiKey = requireValue((options.apiKey || (0, env_1.getEnv)('SL_API_KEY')).trim(), 'SL_API_KEY');
    // appId/appSecret 已不再需要（新接口无需 HMAC 签名）
    // const appId = requireValue(options.appId || getEnv('SL_OPEN_API_APP_ID'), 'SL_OPEN_API_APP_ID');
    // const appSecret = requireValue(options.appSecret || getEnv('SL_OPEN_API_APP_SECRET'), 'SL_OPEN_API_APP_SECRET');
    const url = buildSwapUrl(options);
    const body = JSON.stringify({ apiKey });
    const headers = { 'Content-Type': 'application/json;charset=UTF-8' };
    (0, logger_1.debugLog)('API KEY TOKEN REQUEST', {
        method: 'POST',
        url,
        body,
    });
    const response = await (0, http_timeout_1.fetchWithTimeout)(url, {
        method: 'POST',
        headers,
        body,
    }, 'API Key 换 Token', (0, http_timeout_1.getRequestTimeoutMs)('SL_API_KEY_TOKEN_TIMEOUT_MS'));
    const text = await response.text();
    if (!response.ok) {
        throw new Error(`API Key 换 Token HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`);
    }
    let parsed;
    try {
        parsed = JSON.parse(text);
    }
    catch {
        throw new Error(`API Key 换 Token 接口返回非 JSON: ${text.slice(0, 200)}`);
    }
    (0, logger_1.debugLog)('API KEY TOKEN RESPONSE', {
        status: response.status,
        url,
        body: parsed,
    });
    assertApiKeyTokenSuccess(parsed);
    return {
        response: parsed,
        tokens: normalizeTokens(parsed.data),
    };
}
