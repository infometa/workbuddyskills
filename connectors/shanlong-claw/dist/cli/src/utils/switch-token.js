"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.switchBusinessToken = switchBusinessToken;
const logger_1 = require("../logger");
const env_1 = require("../env");
const token_cache_1 = require("../token-cache");
const http_timeout_1 = require("./http-timeout");
const TOKEN_HEADER_MAP = {
    wuuxiangCyToken: 'Access-Token-Shop',
    fxscmToken: 'Fx-Token',
    slyToken: 'Sly-Token',
    wxctToken: 'Wxcttoken',
    crm8Token: 'Wxcttoken',
};
function assertSwitchTokenSuccess(response) {
    if (response.success === false) {
        const codeText = response.code !== undefined ? ` code=${String(response.code)}` : '';
        const messageText = response.message ? ` message=${response.message}` : '';
        throw new Error(`switchToken 业务错误:${codeText}${messageText}`.trim());
    }
}
function normalizeBaseUrl(baseUrl) {
    return baseUrl.replace(/\/+$/, '');
}
function requireValue(value, label) {
    if (!value) {
        throw new Error(`缺少 ${label}`);
    }
    return value;
}
function readConfiguredOrgType() {
    const currentView = (0, token_cache_1.loadTokenValue)('current_view');
    if (currentView && typeof currentView === 'object' && !Array.isArray(currentView)) {
        const orgType = currentView.orgType;
        if (typeof orgType === 'number' && Number.isFinite(orgType)) {
            return orgType;
        }
        if (typeof orgType === 'string' && orgType.trim()) {
            const parsed = Number(orgType);
            if (Number.isFinite(parsed)) {
                return parsed;
            }
        }
    }
    const envOrgType = (0, env_1.getEnv)('SL_ORG_TYPE');
    if (envOrgType) {
        const parsed = Number(envOrgType);
        if (Number.isFinite(parsed)) {
            return parsed;
        }
    }
    return null;
}
const PRODUCT_TOKEN_KEYS = {
    cy7: ['wuuxiangCyToken'],
    crm: ['crm8Token', 'wxctToken', 'slyToken'],
    scm: ['fxscmToken'],
    report: ['cy7reporterToken'],
};
function buildTokenHeaders(tokens, product) {
    const headers = {};
    if (!tokens) {
        return headers;
    }
    const allowedKeys = product ? (PRODUCT_TOKEN_KEYS[product] || []) : Object.keys(TOKEN_HEADER_MAP);
    for (const [tokenKey, headerName] of Object.entries(TOKEN_HEADER_MAP)) {
        if (!allowedKeys.includes(tokenKey))
            continue;
        const tokenValue = tokens[tokenKey];
        if (tokenValue) {
            headers[headerName] = tokenValue;
        }
    }
    return headers;
}
async function switchBusinessToken(options) {
    const baseUrl = requireValue(options.baseUrl || (0, env_1.getEnv)('SL_AI_HOST'), 'SL_AI_HOST');
    const slyToken = requireValue(options.slyToken, 'slyToken');
    const accountId = requireValue(options.accountId, 'accountId');
    const userId = requireValue(options.userId, 'userId');
    const deviceType = options.deviceType || 'web';
    const url = `${normalizeBaseUrl(baseUrl)}/assistant/api/tools/switchToken`;
    const orgType = readConfiguredOrgType();
    const payload = {
        slyToken,
        deviceType,
        accountIds: [accountId],
        ...(orgType !== null ? { orgType } : {}),
    };
    (0, logger_1.debugLog)('SWITCH TOKEN REQUEST', {
        method: 'POST',
        url,
        body: payload,
    });
    const response = await (0, http_timeout_1.fetchWithTimeout)(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=UTF-8',
        },
        body: JSON.stringify(payload),
    }, 'switchToken', (0, http_timeout_1.getRequestTimeoutMs)('SL_SWITCH_TOKEN_TIMEOUT_MS'));
    const text = await response.text();
    if (!response.ok) {
        throw new Error(`switchToken HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`);
    }
    let parsed;
    try {
        parsed = JSON.parse(text);
    }
    catch {
        throw new Error(`switchToken 接口返回非 JSON: ${text.slice(0, 200)}`);
    }
    (0, logger_1.debugLog)('SWITCH TOKEN RESPONSE', {
        status: response.status,
        url,
        body: parsed,
    });
    assertSwitchTokenSuccess(parsed);
    return {
        slyToken,
        accountId,
        userId,
        response: parsed,
        tokens: parsed.data?.tokens || {},
        headers: buildTokenHeaders(parsed.data?.tokens, options.product),
    };
}
