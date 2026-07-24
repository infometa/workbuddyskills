"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.acquireApiKeyRelation = acquireApiKeyRelation;
const env_1 = require("../env");
const logger_1 = require("../logger");
const http_timeout_1 = require("./http-timeout");
const api_key_token_1 = require("./api-key-token");
const DEFAULT_OPEN_API_APP_ID = '37b67b84473a4067e2e0';
const DEFAULT_OPEN_API_APP_SECRET = 'xwyTiBiEigQtvQXN5oTMSSelDXDOAM6dGc0jOhpFTnzbNaxCGdMnZxB6';
const API_KEY_RELATION_PATH = '/newProxy/basic-data/open/api/relation/list';
function normalizeBaseUrl(baseUrl) {
    return baseUrl.replace(/\/+$/, '');
}
function requireValue(value, label) {
    if (!value) {
        throw new Error(`缺少 ${label}`);
    }
    return value;
}
function buildRelationUrl(options) {
    const explicitUrl = options.url || (0, env_1.getEnv)('SL_API_KEY_RELATION_URL');
    if (explicitUrl) {
        return explicitUrl;
    }
    const baseUrl = requireValue(options.baseUrl || (0, env_1.getEnv)('SL_API_KEY_RELATION_BASEURL') || (0, env_1.getEnv)('SL_API_KEY_BASEURL') || (0, env_1.getEnv)('SL_SLY_BASEURL'), 'SL_API_KEY_RELATION_BASEURL 或 SL_API_KEY_BASEURL 或 SL_SLY_BASEURL');
    return `${normalizeBaseUrl(baseUrl)}${API_KEY_RELATION_PATH}`;
}
function assertApiKeyRelationSuccess(response) {
    const code = response.code !== undefined ? String(response.code) : '';
    if (response.success === false || (code && code !== '2000' && code !== '200')) {
        const codeText = code ? ` code=${code}` : '';
        const messageText = response.message ? ` message=${response.message}` : '';
        throw new Error(`API Key 开通关系接口业务错误:${codeText}${messageText}`.trim());
    }
}
function asRecord(value) {
    return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}
function asString(value) {
    return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
}
function defaultRank(item) {
    return Number(item.isDefault) === 0 ? 0 : 1;
}
function readRelationRoot(response) {
    const root = asRecord(response.data);
    if (!root) {
        return null;
    }
    return root;
}
function normalizeRelationData(root) {
    if (!root) {
        return {};
    }
    const items = Array.isArray(root.list) ? root.list : [];
    const sortedItems = items
        .map((item) => asRecord(item))
        .filter((item) => !!item)
        .sort((left, right) => defaultRank(left) - defaultRank(right));
    const gcode = [];
    const omCorpCode = asString(root.omCorpCode);
    const orgName = asString(root.orgName);
    for (const item of sortedItems) {
        const productCode = asString(item.productCode);
        const bizCorpCode = asString(item.bizCorpCode);
        if (!productCode || !bizCorpCode) {
            continue;
        }
        gcode.push({
            productCode,
            bizCorpCode,
            omCorpCode,
            orgName: asString(item.bizCorpName) || orgName,
            orgCode: asString(root.orgCode),
        });
    }
    if (gcode.length === 0 && omCorpCode) {
        gcode.push({
            productCode: '',
            omCorpCode,
            orgName,
            orgCode: asString(root.orgCode),
        });
    }
    return { gcode };
}
async function acquireApiKeyRelation(options = {}) {
    const apiKey = requireValue((options.apiKey || (0, env_1.getEnv)('SL_API_KEY')).trim(), 'SL_API_KEY');
    const appId = options.appId || (0, env_1.getEnv)('SL_OPEN_API_APP_ID') || DEFAULT_OPEN_API_APP_ID;
    const appSecret = options.appSecret || (0, env_1.getEnv)('SL_OPEN_API_APP_SECRET') || DEFAULT_OPEN_API_APP_SECRET;
    const url = buildRelationUrl(options);
    const body = JSON.stringify({ apiKey });
    (0, logger_1.debugLog)('API KEY RELATION REQUEST', {
        method: 'POST',
        url,
        body,
    });
    const response = await (0, http_timeout_1.fetchWithTimeout)(url, {
        method: 'POST',
        headers: (0, api_key_token_1.buildApiKeySignedHeaders)(appId, appSecret, body),
        body,
    }, 'API Key 开通关系接口', (0, http_timeout_1.getRequestTimeoutMs)('SL_API_KEY_RELATION_TIMEOUT_MS'));
    const text = await response.text();
    if (!response.ok) {
        throw new Error(`API Key 开通关系接口 HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`);
    }
    let parsed;
    try {
        parsed = JSON.parse(text);
    }
    catch {
        throw new Error(`API Key 开通关系接口返回非 JSON: ${text.slice(0, 200)}`);
    }
    (0, logger_1.debugLog)('API KEY RELATION RESPONSE', {
        status: response.status,
        url,
        body: parsed,
    });
    assertApiKeyRelationSuccess(parsed);
    const root = readRelationRoot(parsed);
    return {
        response: parsed,
        data: normalizeRelationData(root),
        accountId: asString(root?.accountId),
        orgId: asString(root?.orgId),
        orgName: asString(root?.orgName),
    };
}
