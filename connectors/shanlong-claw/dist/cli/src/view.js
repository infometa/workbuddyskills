"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.fetchViewList = fetchViewList;
exports.changeView = changeView;
const env_1 = require("./env");
const logger_1 = require("./logger");
const token_1 = require("./token");
const token_cache_1 = require("./token-cache");
const http_timeout_1 = require("./utils/http-timeout");
class ViewApiError extends Error {
    constructor(message, options = {}) {
        super(message);
        this.name = 'ViewApiError';
        this.statusCode = options.statusCode;
        this.code = options.code;
        this.businessMessage = options.businessMessage;
    }
}
function getViewBaseUrl() {
    const baseUrl = (0, env_1.getEnv)('SL_SLY_BASEURL');
    if (!baseUrl) {
        throw new Error('缺少环境变量 SL_SLY_BASEURL，view 接口需要使用当前环境的商龙云地址');
    }
    return baseUrl.replace(/\/+$/, '');
}
function buildAuthHeaders(session) {
    return {
        'Content-Type': 'application/json;charset=UTF-8',
        'tcsl-bp-token': session.token,
    };
}
function assertSuccess(response, label) {
    if (response.success === false) {
        throw new ViewApiError(`${label} 业务错误: code=${String(response.code || '')} message=${response.message || ''}`.trim(), {
            code: response.code,
            businessMessage: response.message,
        });
    }
    if (response.data === undefined) {
        throw new Error(`${label} 未返回 data`);
    }
    return response.data;
}
async function postViewJson(path, body, session) {
    const url = `${getViewBaseUrl()}${path}`;
    (0, logger_1.debugLog)('VIEW REQUEST', { method: 'POST', url, body });
    const response = await (0, http_timeout_1.fetchWithTimeout)(url, {
        method: 'POST',
        headers: buildAuthHeaders(session),
        body: JSON.stringify(body),
    }, '视角接口', (0, http_timeout_1.getRequestTimeoutMs)('SL_VIEW_TIMEOUT_MS'));
    const text = await response.text();
    let parsed;
    try {
        parsed = JSON.parse(text);
    }
    catch {
        if (!response.ok) {
            throw new ViewApiError(`视角接口 HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`, {
                statusCode: response.status,
            });
        }
        throw new Error(`视角接口返回非 JSON: ${text.slice(0, 200)}`);
    }
    (0, logger_1.debugLog)('VIEW RESPONSE', { status: response.status, url, body: parsed });
    const apiResponse = parsed;
    if (!response.ok) {
        throw new ViewApiError(`视角接口 HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`, {
            statusCode: response.status,
            code: apiResponse.code,
            businessMessage: apiResponse.message,
        });
    }
    return assertSuccess(apiResponse, path);
}
function isExpiredViewError(error) {
    if (!(error instanceof ViewApiError)) {
        return false;
    }
    const message = error.businessMessage || error.message;
    return error.statusCode === 401
        || error.code === 3000
        || /用户已经过期|登录.*过期|token.*过期|未登录|unauthorized/i.test(message);
}
async function withFreshSlyRetry(operation) {
    const session = await (0, token_1.ensureSlySession)();
    try {
        return await operation(session);
    }
    catch (error) {
        if (!isExpiredViewError(error)) {
            throw error;
        }
        console.error('⚠ 商龙云短 token 已过期，正在重新登录后重试...');
        const freshSession = await (0, token_1.ensureSlySession)({ forceRefresh: true });
        return operation(freshSession);
    }
}
function requireString(value, label) {
    if (value === undefined || value === '') {
        throw new Error(`缺少 ${label}`);
    }
    return String(value);
}
function readPrincipalUserName(principal) {
    return principal.userName
        || principal.nickName
        || principal.name
        || principal.realName
        || principal.mobile
        || undefined;
}
function parseRelationCode(value) {
    if (!value) {
        return null;
    }
    if (typeof value === 'object' && !Array.isArray(value)) {
        return value;
    }
    if (typeof value !== 'string') {
        return null;
    }
    try {
        const parsed = JSON.parse(value);
        return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
            ? parsed
            : null;
    }
    catch {
        return null;
    }
}
function buildDisplayValue(item) {
    const bizShopCode = item.bizShopCode || '';
    const subDomain = typeof item.subDomain === 'string' && item.subDomain.trim() ? item.subDomain.trim() : '';
    return subDomain ? `${bizShopCode} (${subDomain})` : bizShopCode;
}
function buildProductOpenSummary(orgId, relations) {
    if (relations.length === 0) {
        return undefined;
    }
    const first = relations[0];
    const products = relations.map((item) => {
        const relationCode = parseRelationCode(item.relationCode);
        return {
            productCode: item.productCode || '',
            productName: (item.productName || '').trim(),
            bizShopCode: item.bizShopCode || '',
            bizCorpCode: item.bizCorpCode || '',
            ...(item.subDomain ? { subDomain: item.subDomain } : {}),
            displayValue: buildDisplayValue(item),
            ...(relationCode ? { relationCode } : {}),
        };
    });
    const display = {};
    if (first.omShopCode) {
        display['运营平台门店号'] = first.omShopCode;
    }
    for (const item of products) {
        if (item.productName && item.displayValue) {
            display[item.productName] = item.displayValue;
        }
    }
    return {
        orgId,
        orgCode: first.orgCode || '',
        omShopCode: first.omShopCode || '',
        omShopName: first.omShopName || '',
        omCorpCode: first.omCorpCode || '',
        omCorpName: first.omCorpName || '',
        products,
        display,
    };
}
async function fetchProductOpenRelations(orgId, session) {
    return postViewJson('/newProxy/basic-data/api/product/open/relation/shop/list/orgid', { id: orgId }, session);
}
async function attachProductOpenInfo(items, session) {
    return Promise.all(items.map(async (item) => {
        if (item.orgType !== 3 || !item.id) {
            return item;
        }
        const relations = await fetchProductOpenRelations(item.id, session);
        return {
            ...item,
            productOpenSummary: buildProductOpenSummary(item.id, relations),
            productOpenRelations: relations.map((relation) => ({
                ...relation,
                relationCode: parseRelationCode(relation.relationCode) || relation.relationCode,
            })),
        };
    }));
}
async function fetchViewList() {
    return withFreshSlyRetry(async (session) => {
        const tree = await postViewJson('/newProxy/basic-data/api/login/org/tree', { orgText: '' }, session);
        const roots = tree.filter((item) => item.id);
        const lists = await Promise.all(roots.map((item) => postViewJson('/newProxy/basic-data/api/login/org/list', { orgId: item.id, orgText: '' }, session)));
        return attachProductOpenInfo(lists.flat(), session);
    });
}
async function changeView(orgId) {
    console.error(`→ 正在切换视角: ${orgId}`);
    const data = await withFreshSlyRetry((session) => postViewJson('/newProxy/auth-center/api/login/org/change', { orgId }, session));
    const token = requireString(data.token, 'data.token');
    const principal = data.principal || {};
    const userId = requireString(principal.userId, 'data.principal.userId');
    const accountId = requireString(principal.accountId, 'data.principal.accountId');
    const userName = readPrincipalUserName(principal);
    (0, token_1.persistSlySession)({ token, userId, accountId, userName });
    console.error(`✓ 视角已切换到 ${principal.orgName || orgId}，正在刷新业务 Token...`);
    await (0, token_1.refreshBusinessTokensFromSlySession)({ token, userId, accountId, userName });
    (0, token_cache_1.saveTokenValue)('current_view', {
        orgId: String(principal.orgId || orgId),
        orgCode: principal.orgCode || '',
        orgName: principal.orgName || '',
        orgType: principal.orgType || null,
        rootId: principal.rootId ? String(principal.rootId) : '',
        rootCode: principal.rootCode || '',
        rootName: principal.rootName || '',
        switched_at: new Date().toISOString(),
    });
    console.error('✓ 业务 Token 已刷新并写入 token.json');
    return data;
}
