"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.syncCySAfterSlCredentialPersist = syncCySAfterSlCredentialPersist;
exports.getToken = getToken;
exports.ensureSlySession = ensureSlySession;
exports.persistSlySession = persistSlySession;
exports.writeCy7OmshopStoreMapFromBizParams = writeCy7OmshopStoreMapFromBizParams;
exports.extractBizParamsFromSwitchToken = extractBizParamsFromSwitchToken;
exports.mergeBizParamsFromApiKeySources = mergeBizParamsFromApiKeySources;
exports.refreshCrmGcId = refreshCrmGcId;
exports.loadBizParamsToEnv = loadBizParamsToEnv;
exports.refreshBusinessTokensFromSlySession = refreshBusinessTokensFromSlySession;
exports.getRequestAuth = getRequestAuth;
exports.refreshRequestAuth = refreshRequestAuth;
exports.mergeScmAnalysisAuthFromEnv = mergeScmAnalysisAuthFromEnv;
exports.refreshToken = refreshToken;
exports.isTokenExpiredResponse = isTokenExpiredResponse;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const constants_1 = require("./constants");
const crm_public_key_1 = require("./crm-public-key");
const env_1 = require("./env");
const env_2 = require("./env");
const logger_1 = require("./logger");
const token_cache_1 = require("./token-cache");
const request_1 = require("./request");
const cysms_1 = require("./cysms");
const sly_token_1 = require("./utils/sly-token");
const report_login_1 = require("./utils/report-login");
const switch_token_1 = require("./utils/switch-token");
const api_key_token_1 = require("./utils/api-key-token");
const api_key_relation_1 = require("./utils/api-key-relation");
const account_information_1 = require("./utils/account-information");
/** SLY / switchToken 落盘后调度：若配置了 CY 开放 API 凭据，则后台同步鉴权与门店缓存；否则跳过 */
let pendingCySPostCredentialSync = null;
let lastCySPostCredentialSyncStartedAt = 0;
let pendingApiKeyBusinessTokens = null;
let cachedApiKeyBusinessTokens = null;
const API_KEY_BUSINESS_TOKEN_REUSE_MS = 30000;
async function syncCySAfterSlCredentialPersist() {
    const now = Date.now();
    if (pendingCySPostCredentialSync) {
        (0, logger_1.debugLog)('CYSMS AFTER SL CREDENTIAL', '已有后台同步任务在执行，跳过重复调度');
        return;
    }
    if (now - lastCySPostCredentialSyncStartedAt < 30000) {
        (0, logger_1.debugLog)('CYSMS AFTER SL CREDENTIAL', '30 秒内已调度过同步任务，跳过重复调度');
        return;
    }
    lastCySPostCredentialSyncStartedAt = now;
    pendingCySPostCredentialSync = (0, cysms_1.refreshCySAuthAfterSlCredentialSync)()
        .catch((error) => {
        (0, logger_1.debugLog)('CYSMS AFTER SL CREDENTIAL', error instanceof Error ? error.message : String(error));
    })
        .finally(() => {
        pendingCySPostCredentialSync = null;
    });
}
async function acquireBusinessTokensByApiKeyOnce() {
    const cached = cachedApiKeyBusinessTokens;
    if (cached && Date.now() - cached.cachedAt < API_KEY_BUSINESS_TOKEN_REUSE_MS) {
        return { result: cached.result, fromCache: true };
    }
    if (!pendingApiKeyBusinessTokens) {
        pendingApiKeyBusinessTokens = (0, api_key_token_1.acquireBusinessTokensByApiKey)()
            .then((result) => {
            cachedApiKeyBusinessTokens = { result, cachedAt: Date.now() };
            return result;
        })
            .finally(() => {
            pendingApiKeyBusinessTokens = null;
        });
    }
    return { result: await pendingApiKeyBusinessTokens, fromCache: false };
}
const PRODUCT_TOKEN_STORE_KEYS = {
    cy7: 'wuuxiangCyToken',
    crm: 'crm8Token',
    scm: 'fxscmToken',
    report: 'cy7reporterToken',
};
const PRODUCT_TOKEN_LEGACY_KEYS = {
    cy7: ['wuuxiang_cy_token'],
    crm: ['wxctToken', 'Wxcttoken'],
    scm: ['fxscm_token'],
    report: [],
};
const PRODUCT_REQUEST_HEADER_MAP = {
    cy7: 'Access-Token-Shop',
    crm: 'Wxcttoken',
    scm: 'Fx-Token',
    dc: '',
    report: '',
};
function readTokenField(result, tokenField) {
    if (!result || typeof result !== 'object') {
        return null;
    }
    const record = result;
    if (record.data && typeof record.data === 'object' && !Array.isArray(record.data)) {
        const data = record.data;
        if (typeof data[tokenField] === 'string') {
            return data[tokenField];
        }
    }
    if (typeof record[tokenField] === 'string') {
        return record[tokenField];
    }
    if (typeof record.data === 'string') {
        return record.data;
    }
    return typeof record.token === 'string' ? record.token : null;
}
function getToken(product) {
    const storeToken = readStoreToken(product);
    if (storeToken) {
        return storeToken;
    }
    const envKey = constants_1.TOKEN_ENV_MAP[product];
    return envKey ? (0, env_1.getEnv)(envKey) : '';
}
function readStoreString(keys) {
    for (const key of keys) {
        const value = (0, token_cache_1.loadTokenValue)(key);
        if (typeof value === 'string' && value) {
            return value;
        }
    }
    return '';
}
function isCachedTokenEntry(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value) && typeof value.token === 'string';
}
function readTokenEntry(key) {
    const value = (0, token_cache_1.loadTokenValue)(key);
    if (!isCachedTokenEntry(value)) {
        return null;
    }
    if (value.expires_at && Date.now() > value.expires_at) {
        return null;
    }
    return value;
}
function readStoreToken(product) {
    if (product === 'report') {
        const realToken = readStoreString(['report_session_token']);
        if (realToken)
            return realToken;
    }
    const primaryKey = PRODUCT_TOKEN_STORE_KEYS[product];
    const primaryToken = primaryKey ? readStoreString([primaryKey]) : '';
    if (primaryToken) {
        return primaryToken;
    }
    const legacyToken = readStoreString(PRODUCT_TOKEN_LEGACY_KEYS[product] || []);
    if (legacyToken) {
        persistProductToken(product, legacyToken);
        return legacyToken;
    }
    const legacyEntry = readTokenEntry(product);
    if (legacyEntry?.token) {
        persistProductToken(product, legacyEntry.token);
        return legacyEntry.token;
    }
    return '';
}
function getCachedSwitchSlyToken() {
    const slyToken = readStoreString(['sly_token']);
    if (slyToken) {
        return slyToken;
    }
    const legacyEntry = readTokenEntry('sly');
    if (legacyEntry?.token) {
        persistShortSlyToken(legacyEntry.token, legacyEntry.userId, legacyEntry.accountId, { userName: legacyEntry.userName });
        return legacyEntry.token;
    }
    return readStoreString(['sly_token', 'SLY_TOKEN'])
        || (0, env_1.getEnv)('SL_SLY_TOKEN');
}
function getCachedRequestSlyToken() {
    const remoteToken = readStoreString(['sly_remote_token']);
    if (remoteToken) {
        return remoteToken;
    }
    const legacyRemoteToken = readStoreString(['SL_CRM_SLY_TOKEN']);
    if (legacyRemoteToken) {
        persistRequestSlyToken(legacyRemoteToken);
        return legacyRemoteToken;
    }
    return (0, env_1.getEnv)('SL_CRM_SLY_TOKEN');
}
function persistShortSlyToken(token, userId, accountId, session = {}) {
    (0, token_cache_1.saveTokenValue)('sly_token', token);
    if (userId) {
        (0, token_cache_1.saveTokenValue)('user_id', userId);
    }
    if (session.userName) {
        (0, token_cache_1.saveTokenValue)('userName', session.userName);
    }
    if (accountId) {
        (0, token_cache_1.saveTokenValue)('accountId', accountId);
    }
    if (typeof session.orgType === 'number' && Number.isFinite(session.orgType)) {
        (0, token_cache_1.saveTokenValue)('current_view', {
            orgId: session.orgId || '',
            orgCode: session.orgCode || '',
            orgName: session.orgName || '',
            orgType: session.orgType,
            rootId: session.rootId || '',
            rootCode: session.rootCode || '',
            rootName: session.rootName || '',
            switched_at: new Date().toISOString(),
            source: 'sly_login',
        });
    }
}
function persistRequestSlyToken(token) {
    (0, token_cache_1.saveTokenValue)('sly_remote_token', token);
}
function persistApiKeyRelationIdentity(identity) {
    if (identity.accountId) {
        (0, token_cache_1.saveTokenValue)('SL_USER_ID', identity.accountId);
        (0, token_cache_1.saveTokenValue)('user_id', identity.accountId);
    }
    if (identity.orgId) {
        (0, token_cache_1.saveTokenValue)('SL_GROUP_ID', identity.orgId);
        (0, token_cache_1.saveTokenValue)('orgId', identity.orgId);
    }
    if (identity.orgName) {
        (0, token_cache_1.saveTokenValue)('SL_ORG_NAME', identity.orgName);
        (0, token_cache_1.saveTokenValue)('orgName', identity.orgName);
    }
}
function getCachedUserId() {
    const envUserId = (0, env_1.getEnv)('SL_USER_ID');
    if (envUserId) {
        return envUserId;
    }
    const legacyEntry = readTokenEntry('sly');
    if (legacyEntry?.userId) {
        return legacyEntry.userId;
    }
    return readStoreString(['SL_USER_ID', 'user_id', 'userId']);
}
function getCachedUserName() {
    const legacyEntry = readTokenEntry('sly');
    if (legacyEntry?.userName) {
        return legacyEntry.userName;
    }
    return readStoreString(['userName']) || (0, env_1.getEnv)('SL_USER_NAME') || (0, env_1.getEnv)('SL_SLY_USERNAME');
}
function getSwitchAccountId(product) {
    const productEnvKey = `SL_${product.toUpperCase()}_ACCOUNT_ID`;
    const legacyEntry = readTokenEntry('sly');
    return (0, env_1.getEnv)(productEnvKey)
        || (0, env_1.getEnv)('SL_ACCOUNT_ID')
        || (0, env_1.getEnv)('SL_GROUP_ID')
        || legacyEntry?.accountId
        || readStoreString(['SL_GROUP_ID', 'orgId', 'accountId', 'org_shop_id']);
}
function getSwitchDeviceType() {
    return readStoreString(['device_type']) || (0, env_1.getEnv)('SL_DEVICE_TYPE') || 'web';
}
function hasSlyLoginConfig() {
    return !!(0, env_1.getEnv)('SL_SLY_USERNAME') && !!(0, env_1.getEnv)('SL_SLY_PASSWORD');
}
async function ensureSlySession(options = {}) {
    const cachedToken = getCachedSwitchSlyToken();
    if (cachedToken && !options.forceRefresh) {
        return {
            token: cachedToken,
            userId: getCachedUserId() || undefined,
            userName: getCachedUserName() || undefined,
            accountId: readStoreString(['accountId']) || undefined,
        };
    }
    const freshSession = await (0, sly_token_1.acquireSlyToken)();
    persistShortSlyToken(freshSession.token, freshSession.userId, freshSession.accountId, freshSession);
    await syncCySAfterSlCredentialPersist();
    return freshSession;
}
function persistSlySession(session) {
    persistShortSlyToken(session.token, session.userId, session.accountId, session);
}
function normalizeAuthHeaders(product, headers) {
    if (!headers) {
        if (product === 'dc') {
            const slyHeader = getCachedRequestSlyToken();
            return slyHeader ? { 'Sly-Token': slyHeader } : {};
        }
        return {};
    }
    if (product === 'report') {
        return {};
    }
    const normalized = { ...headers };
    if (product === 'crm') {
        const slyHeader = normalized['Sly-Token'] || getCachedRequestSlyToken();
        if (slyHeader) {
            normalized.sly_token = slyHeader;
        }
    }
    if (product === 'dc') {
        const slyHeader = normalized['Sly-Token'] || getCachedRequestSlyToken();
        if (slyHeader) {
            normalized['Sly-Token'] = slyHeader;
        }
    }
    return normalized;
}
function getRequestHeaderName(product) {
    return PRODUCT_REQUEST_HEADER_MAP[product] || '';
}
function buildRequestAuth(product, token, headers) {
    const normalizedHeaders = normalizeAuthHeaders(product, headers);
    const requestHeaderName = getRequestHeaderName(product);
    if (token && requestHeaderName && !normalizedHeaders[requestHeaderName]) {
        normalizedHeaders[requestHeaderName] = token;
    }
    if (product === 'crm' && token && token.startsWith('Bearer ')) {
        return {
            sessionToken: null,
            headers: normalizedHeaders,
        };
    }
    return {
        sessionToken: token,
        headers: Object.keys(normalizedHeaders).length > 0 ? normalizedHeaders : undefined,
    };
}
function readBusinessTokenFromSwitch(product, tokens, headers) {
    const tokenKeys = [PRODUCT_TOKEN_STORE_KEYS[product], ...(PRODUCT_TOKEN_LEGACY_KEYS[product] || [])].filter(Boolean);
    for (const tokenKey of tokenKeys) {
        const tokenValue = tokens[tokenKey];
        if (tokenValue) {
            return tokenValue;
        }
    }
    const headerName = getRequestHeaderName(product);
    return headerName ? headers[headerName] || '' : '';
}
async function refreshSlyToken() {
    try {
        console.error('→ SLY 登录中...');
        const result = await (0, sly_token_1.acquireSlyToken)();
        persistShortSlyToken(result.token, result.userId, result.accountId, result);
        console.error('✓ SLY 登录成功');
        return result.token;
    }
    catch (error) {
        const msg = error instanceof Error ? error.message : String(error);
        console.error(`✗ SLY 登录失败: ${msg}`);
        console.error('  请检查 SL_SLY_BASEURL / SL_SLY_USERNAME / SL_SLY_PASSWORD');
        return null;
    }
}
function persistProductToken(product, token) {
    const primaryKey = PRODUCT_TOKEN_STORE_KEYS[product];
    if (!primaryKey) {
        return;
    }
    (0, token_cache_1.saveTokenValue)(primaryKey, token);
}
const PRODUCT_CODE_MAP = {
    '003': 'crm',
    '005': 'cy7',
    '012': 'cy7',
    '010': 'scm',
};
const CACHE_DIR_NAME = 'cache';
const CY7_OMSHOP_STORE_MAP_FILE = 'cy7-omshop-store-map.json';
const BIZ_PARAM_KEYS = [
    'SL_CY7_GROUP_ID',
    'SL_CY7_STORE_ID',
    'SL_CY7_BRAND_ID',
    'SL_CRM_GROUP_ID',
    'SL_CRM_STORE_ID',
    'SL_CRM_GC_ID',
    'SL_SCM_GROUP_ID',
    'SL_SCM_STORE_ID',
    'SL_UNIFIED_G_ID',
    'SL_SLY_CORP_ID',
    'omShopCodes',
    'cy_omShopCodes',
    'crm_omShopCodes',
    'scm_omShopCodes',
    'omShopCodeOrgNameMap',
];
const BIZ_PARAM_KEY_SET = new Set(BIZ_PARAM_KEYS);
function parseOmShopCodes(value) {
    return value
        .split(',')
        .map((item) => item.trim().replace(/^['"]|['"]$/g, ''))
        .filter(Boolean);
}
function parseOmShopCodeOrgNameMap(value) {
    if (!value) {
        return {};
    }
    try {
        const parsed = JSON.parse(value);
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
            return {};
        }
        const out = {};
        for (const [key, raw] of Object.entries(parsed)) {
            if (!key) {
                continue;
            }
            if (typeof raw === 'string') {
                out[key] = raw;
            }
            else if (typeof raw === 'number' && Number.isFinite(raw)) {
                out[key] = String(raw);
            }
        }
        return out;
    }
    catch {
        return {};
    }
}
function writeCy7OmshopStoreMapFromBizParams(params) {
    const codes = parseOmShopCodes(params.omShopCodes || '');
    if (codes.length === 0) {
        return;
    }
    const nameMap = parseOmShopCodeOrgNameMap(params.omShopCodeOrgNameMap || '');
    const cacheDir = path_1.default.join(process.cwd(), CACHE_DIR_NAME);
    fs_1.default.mkdirSync(cacheDir, { recursive: true });
    const omShopCodeOrgNameMap = JSON.stringify(Object.fromEntries(codes.map((code) => [code, nameMap[code] || ''])));
    const payload = {
        synced_at: new Date().toISOString(),
        source: 'token.biz_params',
        product: 'cy7',
        ...(params.SL_CY7_GROUP_ID ? { centerId: params.SL_CY7_GROUP_ID } : {}),
        ...(params.SL_UNIFIED_G_ID ? { groupNo: params.SL_UNIFIED_G_ID } : {}),
        // omShopCodes / stores[].omShopCode hold unified C-prefixed store codes for StarRocks store_code.
        omShopCodes: params.omShopCodes,
        omShopCodeOrgNameMap,
        stores: codes.map((code) => ({
            omShopCode: code,
            orgName: nameMap[code] || '',
        })),
    };
    fs_1.default.writeFileSync(path_1.default.join(cacheDir, CY7_OMSHOP_STORE_MAP_FILE), JSON.stringify(payload, null, 2), 'utf-8');
}
function parseCsvSet(value) {
    return new Set(value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean));
}
function isExplicitTrue(value) {
    return ['true', '1', 'yes'].includes(value.toLowerCase());
}
function getLockedBizParamKeys() {
    if (!isExplicitTrue(process.env.SL_LOCK_BIZ_PARAMS || '')) {
        return null;
    }
    const configuredKeys = parseCsvSet(process.env.SL_LOCK_BIZ_PARAM_KEYS || '');
    return configuredKeys.size > 0 ? configuredKeys : new Set(BIZ_PARAM_KEYS);
}
function isBizParamLocked(key) {
    const lockedKeys = getLockedBizParamKeys();
    return !!lockedKeys?.has(key);
}
function readCachedBizParams() {
    const params = {};
    const raw = (0, token_cache_1.loadTokenValue)('biz_params');
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
        for (const [key, value] of Object.entries(raw)) {
            if (typeof value === 'string') {
                params[key] = value;
            }
        }
    }
    for (const key of BIZ_PARAM_KEYS) {
        if (params[key]) {
            continue;
        }
        const value = (0, token_cache_1.loadTokenValue)(key);
        if (typeof value === 'string' && value) {
            params[key] = value;
        }
    }
    return params;
}
function applyBizParamLocks(params) {
    const lockedKeys = getLockedBizParamKeys();
    if (!lockedKeys) {
        return params;
    }
    const cachedParams = readCachedBizParams();
    const nextParams = { ...params };
    for (const key of lockedKeys) {
        if (!BIZ_PARAM_KEY_SET.has(key)) {
            continue;
        }
        const lockedValue = process.env[key] || cachedParams[key] || '';
        if (lockedValue) {
            nextParams[key] = lockedValue;
        }
    }
    return nextParams;
}
function getCy7BrandBaseUrl() {
    return (0, env_1.getEnv)('SL_CY7_BRAND_BASE_URL', 'https://open-internal-test.tcsl.com.cn/ai2cyweb/fast');
}
const CY7_BRAND_ENDPOINT = '/api/itembase/bigclass/brandClassTreeList';
function readRelationCodeValue(value) {
    return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
}
function resolveCrmGcId(data, crmGroupId) {
    if (!crmGroupId) {
        return '';
    }
    const entries = [...(data.gcode || []), ...(data.ccode || [])];
    for (const entry of entries) {
        const relationCode = entry.relationCode;
        if (!relationCode) {
            continue;
        }
        const relatedCrmGroupId = readRelationCodeValue(relationCode.crmGroupCode)
            || (entry.productCode === '003' ? readRelationCodeValue(entry.bizCorpCode) : '');
        if (relatedCrmGroupId !== crmGroupId) {
            continue;
        }
        const gcId = readRelationCodeValue(relationCode.gcId);
        if (gcId) {
            return gcId;
        }
    }
    return '';
}
function extractBizParams(data) {
    const params = {};
    const omShopCodes = new Map();
    const ccode = data.ccode || [];
    const gcode = data.gcode || [];
    for (const entry of ccode) {
        const product = PRODUCT_CODE_MAP[entry.productCode || ''];
        if (!product)
            continue;
        if (entry.omShopCode) {
            omShopCodes.set(entry.omShopCode, entry.orgName || '');
        }
        const prefix = `SL_${product.toUpperCase()}`;
        if (entry.bizCorpCode)
            params[`${prefix}_GROUP_ID`] = entry.bizCorpCode;
        if (entry.bizShopCode) {
            params[`${prefix}_STORE_ID`] = entry.bizShopCode;
        }
    }
    for (const entry of gcode) {
        const product = PRODUCT_CODE_MAP[entry.productCode || ''];
        if (!product)
            continue;
        const prefix = `SL_${product.toUpperCase()}`;
        if (entry.bizCorpCode && !params[`${prefix}_GROUP_ID`]) {
            params[`${prefix}_GROUP_ID`] = entry.bizCorpCode;
        }
        if (entry.omCorpCode && !params.SL_UNIFIED_G_ID) {
            params.SL_UNIFIED_G_ID = entry.omCorpCode;
        }
        const rel = entry.relationCode;
        if (!rel)
            continue;
        if (product === 'cy7') {
            if (typeof rel.cy7GroupId === 'string' && rel.cy7GroupId) {
                params[`${prefix}_GROUP_ID`] = rel.cy7GroupId;
            }
            if (typeof rel.cy7ShopId === 'string' && rel.cy7ShopId) {
                params[`${prefix}_STORE_ID`] = rel.cy7ShopId;
            }
            if (typeof rel.brandId === 'string' && rel.brandId) {
                params[`${prefix}_BRAND_ID`] = rel.brandId;
            }
        }
    }
    const crmGcId = resolveCrmGcId(data, params.SL_CRM_GROUP_ID || '');
    if (crmGcId) {
        params.SL_CRM_GC_ID = crmGcId;
    }
    if (omShopCodes.size > 0) {
        params.omShopCodes = Array.from(omShopCodes.keys()).map((code) => `'${code}'`).join(',');
        params.omShopCodeOrgNameMap = JSON.stringify(Object.fromEntries(omShopCodes));
    }
    const firstGcode = gcode[0] || ccode[0];
    if (firstGcode && firstGcode.orgId) {
        params.SL_SLY_CORP_ID = String(firstGcode.orgId);
    }
    return params;
}
/**
 * API Key 场景下，账号信息接口的 ccode 是全量门店；开通关系接口的 gcode
 * 则代表当前 API Key 在各产品线可用的集团。按“产品线 + bizCorpCode”交集
 * 取出有权限的 omShopCode，且不影响原有全量 omShopCodes。
 */
function extractAuthorizedOmShopCodes(accountInformationData, apiKeyRelationData) {
    const authorizedGroups = new Map();
    for (const entry of apiKeyRelationData.gcode || []) {
        const product = PRODUCT_CODE_MAP[entry.productCode || ''];
        if (!product || !entry.bizCorpCode)
            continue;
        const groups = authorizedGroups.get(product) || new Set();
        groups.add(entry.bizCorpCode);
        authorizedGroups.set(product, groups);
    }
    const codesByProduct = {
        cy7: new Set(),
        crm: new Set(),
        scm: new Set(),
    };
    for (const entry of accountInformationData.ccode || []) {
        const product = PRODUCT_CODE_MAP[entry.productCode || ''];
        if ((product !== 'cy7' && product !== 'crm' && product !== 'scm')
            || !entry.bizCorpCode
            || !entry.omShopCode
            || !authorizedGroups.get(product)?.has(entry.bizCorpCode)) {
            continue;
        }
        codesByProduct[product].add(entry.omShopCode);
    }
    const formatCodes = (codes) => Array.from(codes).map((code) => `'${code}'`).join(',');
    return {
        cy_omShopCodes: formatCodes(codesByProduct.cy7),
        crm_omShopCodes: formatCodes(codesByProduct.crm),
        scm_omShopCodes: formatCodes(codesByProduct.scm),
    };
}
function extractBizParamsFromSwitchToken(data) {
    return extractBizParams(data);
}
function mergeBizParamsFromApiKeySources(accountInformationData, apiKeyRelationData, hasAccountInformation, hasApiKeyRelation) {
    const accountInformationParams = extractBizParams(accountInformationData);
    const apiKeyRelationParams = extractBizParams(apiKeyRelationData);
    const params = {
        ...accountInformationParams,
        ...apiKeyRelationParams,
    };
    const crmGroupId = params.SL_CRM_GROUP_ID || '';
    if (crmGroupId) {
        const crmGcId = resolveCrmGcId(apiKeyRelationData, crmGroupId)
            || resolveCrmGcId(accountInformationData, crmGroupId)
            || (apiKeyRelationParams.SL_CRM_GROUP_ID === crmGroupId ? apiKeyRelationParams.SL_CRM_GC_ID : '')
            || (accountInformationParams.SL_CRM_GROUP_ID === crmGroupId ? accountInformationParams.SL_CRM_GC_ID : '');
        if (crmGcId) {
            params.SL_CRM_GC_ID = crmGcId;
        }
        else {
            delete params.SL_CRM_GC_ID;
        }
    }
    // 任一上游失败时保留已缓存的按产品线门店范围，避免把暂时不可用误判为无权限。
    if (hasAccountInformation && hasApiKeyRelation) {
        Object.assign(params, extractAuthorizedOmShopCodes(accountInformationData, apiKeyRelationData));
    }
    return params;
}
async function refreshCrmGcId(crmGroupIdOverride = '') {
    if (process.env.SL_TOKEN_READONLY === '1') {
        throw new Error('SL_TOKEN_READONLY=1，无法更新 token.json');
    }
    const crmGroupId = (crmGroupIdOverride
        || process.env.SL_CRM_GROUP_ID
        || (0, env_1.getEnv)('SL_CRM_GROUP_ID')).trim();
    if (!crmGroupId) {
        throw new Error('缺少 SL_CRM_GROUP_ID，请先设置环境变量或传入 --group-id');
    }
    const accountInformation = await (0, account_information_1.acquireAccountInformation)();
    const crmGcId = resolveCrmGcId(accountInformation.data, crmGroupId);
    if (!crmGcId) {
        throw new Error(`账号信息接口未找到 SL_CRM_GROUP_ID=${crmGroupId} 对应的 relationCode.gcId`);
    }
    const rawBizParams = (0, token_cache_1.loadTokenValue)('biz_params');
    const bizParams = rawBizParams
        && typeof rawBizParams === 'object'
        && !Array.isArray(rawBizParams)
        ? { ...rawBizParams }
        : {};
    bizParams.SL_CRM_GROUP_ID = crmGroupId;
    bizParams.SL_CRM_GC_ID = crmGcId;
    (0, token_cache_1.saveTokenValue)('biz_params', bizParams);
    process.env.SL_CRM_GROUP_ID = crmGroupId;
    process.env.SL_CRM_GC_ID = crmGcId;
    return { crmGroupId, crmGcId };
}
function persistBizParams(params, relationData) {
    const finalParams = applyBizParamLocks({
        ...readCachedBizParams(),
        ...params,
    });
    const finalCrmGroupId = finalParams.SL_CRM_GROUP_ID || '';
    if (relationData && finalCrmGroupId && !isBizParamLocked('SL_CRM_GC_ID')) {
        const finalCrmGcId = resolveCrmGcId(relationData, finalCrmGroupId);
        if (finalCrmGcId) {
            finalParams.SL_CRM_GC_ID = finalCrmGcId;
        }
        else if (finalCrmGroupId !== params.SL_CRM_GROUP_ID) {
            delete finalParams.SL_CRM_GC_ID;
        }
    }
    if (Object.keys(finalParams).length === 0)
        return finalParams;
    (0, token_cache_1.saveTokenValue)('biz_params', finalParams);
    try {
        writeCy7OmshopStoreMapFromBizParams(finalParams);
    }
    catch (error) {
        (0, logger_1.debugLog)('CY7 OMSHOP STORE MAP CACHE', error instanceof Error ? error.message : String(error));
    }
    (0, logger_1.debugLog)('BIZ PARAMS 提取', finalParams);
    return finalParams;
}
function readCy7BrandId(result) {
    if (!result || typeof result !== 'object' || Array.isArray(result)) {
        return '';
    }
    const data = result.data;
    if (!Array.isArray(data) || data.length === 0) {
        return '';
    }
    const firstItem = data[0];
    if (!firstItem || typeof firstItem !== 'object' || Array.isArray(firstItem)) {
        return '';
    }
    const brandId = firstItem.id;
    return typeof brandId === 'string' || typeof brandId === 'number' ? String(brandId) : '';
}
async function refreshCy7BrandId(sessionToken, storeId) {
    const result = await (0, request_1.makeRequest)(getCy7BrandBaseUrl(), { path: CY7_BRAND_ENDPOINT, method: 'POST' }, sessionToken, {}, 'cy7', { shopId: storeId });
    const brandId = readCy7BrandId(result);
    if (!brandId) {
        throw new Error('brandClassTreeList 未返回 data[0].id');
    }
    return brandId;
}
function persistCy7BrandId(brandId) {
    if (!brandId) {
        return;
    }
    const bizParams = readCachedBizParams();
    const lockedBrandId = process.env.SL_CY7_BRAND_ID || bizParams.SL_CY7_BRAND_ID || '';
    if (isBizParamLocked('SL_CY7_BRAND_ID') && lockedBrandId) {
        (0, logger_1.debugLog)('CY7 BRAND REFRESH', 'SL_CY7_BRAND_ID 已被 SL_LOCK_BIZ_PARAMS 锁定，跳过覆盖');
        return;
    }
    bizParams.SL_CY7_BRAND_ID = brandId;
    (0, token_cache_1.saveTokenValue)('biz_params', bizParams);
}
function loadBizParamsToEnv() {
    const params = {};
    const raw = (0, token_cache_1.loadTokenValue)('biz_params');
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
        for (const [key, value] of Object.entries(raw)) {
            if (typeof value === 'string' && value) {
                params[key] = value;
            }
        }
    }
    for (const [key, value] of Object.entries(params)) {
        if (typeof value === 'string' && value && !process.env[key]) {
            process.env[key] = value;
        }
    }
}
function persistAllBusinessTokens(tokens) {
    for (const [product, primaryKey] of Object.entries(PRODUCT_TOKEN_STORE_KEYS)) {
        const candidateKeys = [primaryKey, ...(PRODUCT_TOKEN_LEGACY_KEYS[product] || [])];
        const token = candidateKeys.map((key) => tokens[key]).find((value) => typeof value === 'string' && value);
        if (token) {
            persistProductToken(product, token);
        }
    }
}
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function safeParseBigIntJson(text) {
    const safe = text.replace(/:\s*(\d{16,})/g, ': "$1"');
    return JSON.parse(safe);
}
function decodeJwtPayload(jwt) {
    try {
        const parts = jwt.replace(/^Bearer\s+/i, '').split('.');
        if (parts.length < 2)
            return null;
        const payload = Buffer.from(parts[1], 'base64').toString('utf-8');
        const parsed = safeParseBigIntJson(payload);
        return isRecord(parsed) ? parsed : null;
    }
    catch {
        return null;
    }
}
function readStringField(record, keys) {
    for (const key of keys) {
        const value = record[key];
        if (typeof value === 'string' && value)
            return value;
        if (typeof value === 'number' && Number.isFinite(value))
            return String(value);
    }
    return '';
}
function findStringFieldDeep(value, keys, depth = 0) {
    if (depth > 5 || !isRecord(value)) {
        return '';
    }
    const direct = readStringField(value, keys);
    if (direct) {
        return direct;
    }
    for (const child of Object.values(value)) {
        if (isRecord(child)) {
            const found = findStringFieldDeep(child, keys, depth + 1);
            if (found) {
                return found;
            }
        }
        else if (Array.isArray(child)) {
            for (const item of child) {
                const found = findStringFieldDeep(item, keys, depth + 1);
                if (found) {
                    return found;
                }
            }
        }
    }
    return '';
}
function readFirstPayloadString(payloads, keys) {
    for (const payload of payloads) {
        const value = readStringField(payload, keys);
        if (value)
            return value;
    }
    return '';
}
function collectTokenPayloads(tokens) {
    return Object.values(tokens)
        .map((token) => (typeof token === 'string' ? decodeJwtPayload(token) : null))
        .filter((payload) => !!payload);
}
function extractBizParamsFromTokenJwts(tokens) {
    const params = {};
    const cy7Payloads = [tokens.cy7OldToken, tokens.wuuxiangCyToken]
        .map((token) => (typeof token === 'string' ? decodeJwtPayload(token) : null))
        .filter((payload) => !!payload);
    const cy7GroupId = readFirstPayloadString(cy7Payloads, ['groupId', 'centerId', 'corpId', 'shopId']);
    const cy7StoreId = readFirstPayloadString(cy7Payloads, ['shopId', 'storeId', 'bizShopCode']);
    const cy7BrandId = readFirstPayloadString(cy7Payloads, ['brandId']);
    if (cy7GroupId)
        params.SL_CY7_GROUP_ID = cy7GroupId;
    if (cy7StoreId)
        params.SL_CY7_STORE_ID = cy7StoreId;
    if (cy7BrandId)
        params.SL_CY7_BRAND_ID = cy7BrandId;
    const crmPayloads = [tokens.crm8Token, tokens.Wxcttoken]
        .map((token) => (typeof token === 'string' ? decodeJwtPayload(token) : null))
        .filter((payload) => !!payload);
    const crmGroupId = readFirstPayloadString(crmPayloads, ['companyId', 'company_id', 'groupId', 'corpId']);
    const crmStoreId = readFirstPayloadString(crmPayloads, ['storeId', 'shopId', 'bizShopCode']);
    const crmGcId = readFirstPayloadString(crmPayloads, ['gcId', 'gc_id']);
    if (crmGroupId)
        params.SL_CRM_GROUP_ID = crmGroupId;
    if (crmStoreId)
        params.SL_CRM_STORE_ID = crmStoreId;
    if (crmGcId)
        params.SL_CRM_GC_ID = crmGcId;
    const scmPayloads = [tokens.fxscmToken]
        .map((token) => (typeof token === 'string' ? decodeJwtPayload(token) : null))
        .filter((payload) => !!payload);
    const scmGroupId = readFirstPayloadString(scmPayloads, ['tenantId', 'companyId', 'groupId', 'corpId']);
    const scmStoreId = readFirstPayloadString(scmPayloads, ['storeId', 'shopId', 'bizShopCode']);
    if (scmGroupId)
        params.SL_SCM_GROUP_ID = scmGroupId;
    if (scmStoreId)
        params.SL_SCM_STORE_ID = scmStoreId;
    const unifiedGId = readFirstPayloadString([...cy7Payloads, ...crmPayloads, ...scmPayloads], ['omCorpCode', 'unifiedGId', 'unified_g_id', 'groupNo']);
    if (unifiedGId) {
        params.SL_UNIFIED_G_ID = unifiedGId;
    }
    return params;
}
function persistApiKeyIdentity(result) {
    const data = result.response.data || {};
    const payloads = collectTokenPayloads(result.tokens);
    const roots = [data, ...payloads];
    const userId = (0, env_1.getEnv)('SL_USER_ID')
        || roots.map((root) => findStringFieldDeep(root, ['userId', 'user_id', 'accountId', 'account_id'])).find(Boolean)
        || '';
    if (userId) {
        (0, token_cache_1.saveTokenValue)('user_id', userId);
        if (!process.env.SL_USER_ID) {
            process.env.SL_USER_ID = userId;
        }
    }
    const accountId = (0, env_1.getEnv)('SL_ACCOUNT_ID')
        || roots.map((root) => findStringFieldDeep(root, ['accountId', 'account_id', 'orgId', 'rootId'])).find(Boolean)
        || '';
    if (accountId) {
        (0, token_cache_1.saveTokenValue)('accountId', accountId);
        if (!process.env.SL_ACCOUNT_ID) {
            process.env.SL_ACCOUNT_ID = accountId;
        }
    }
    const userName = (0, env_1.getEnv)('SL_USER_NAME')
        || roots.map((root) => findStringFieldDeep(root, ['userName', 'user_name', 'nickName', 'name'])).find(Boolean)
        || '';
    if (userName) {
        (0, token_cache_1.saveTokenValue)('userName', userName);
        if (!process.env.SL_USER_NAME) {
            process.env.SL_USER_NAME = userName;
        }
    }
    const groupId = (0, env_1.getEnv)('SL_GROUP_ID')
        || roots.map((root) => findStringFieldDeep(root, ['groupId', 'corpId', 'rootId', 'orgId'])).find(Boolean)
        || '';
    if (groupId) {
        (0, token_cache_1.saveTokenValue)('SL_GROUP_ID', groupId);
        if (!process.env.SL_GROUP_ID) {
            process.env.SL_GROUP_ID = groupId;
        }
    }
}
function hasCachedBizParams() {
    return Object.keys(readCachedBizParams()).length > 0;
}
function findSwitchTokenDataDeep(value, depth = 0) {
    if (depth > 5) {
        return null;
    }
    if (isRecord(value)) {
        if (Array.isArray(value.ccode) || Array.isArray(value.gcode) || isRecord(value.tokens)) {
            return value;
        }
        for (const child of Object.values(value)) {
            const found = findSwitchTokenDataDeep(child, depth + 1);
            if (found)
                return found;
        }
    }
    if (Array.isArray(value)) {
        for (const item of value) {
            const found = findSwitchTokenDataDeep(item, depth + 1);
            if (found)
                return found;
        }
    }
    return null;
}
async function persistApiKeyResponseBizData(result) {
    const switchData = findSwitchTokenDataDeep(result.response.data);
    if (!switchData) {
        return false;
    }
    await persistSwitchTokenData({
        ...switchData,
        tokens: {
            ...(switchData.tokens || {}),
            ...result.tokens,
        },
    });
    return hasCachedBizParams();
}
async function refreshBusinessTokensByApiKey(product) {
    if (!(0, api_key_token_1.hasApiKeyTokenConfig)()) {
        return null;
    }
    console.error('→ 正在通过 API Key 换取业务 Token...');
    const { result, fromCache } = await acquireBusinessTokensByApiKeyOnce();
    console.error('✓ API Key 换 Token 返回成功，正在写入本地缓存...');
    if (fromCache) {
        const token = readBusinessTokenFromSwitch(product, result.tokens, {}) || getToken(product) || null;
        return buildRequestAuth(product, token, product === 'crm' ? { sly_token: getCachedRequestSlyToken() } : undefined);
    }
    if (result.tokens.slyToken) {
        persistRequestSlyToken(result.tokens.slyToken);
    }
    persistAllBusinessTokens(result.tokens);
    persistApiKeyIdentity(result);
    const responseBizParamsOk = await persistApiKeyResponseBizData(result);
    let apiKeyRelationData = {};
    let hasApiKeyRelation = false;
    try {
        console.error('→ 正在通过 API Key 开通关系接口刷新业务参数...');
        const relationInfo = await (0, api_key_relation_1.acquireApiKeyRelation)();
        apiKeyRelationData = relationInfo.data || {};
        hasApiKeyRelation = true;
        persistApiKeyRelationIdentity({
            accountId: relationInfo.accountId,
            orgId: relationInfo.orgId,
            orgName: relationInfo.orgName,
        });
        console.error('✓ API Key 开通关系业务参数已获取');
    }
    catch (error) {
        (0, logger_1.debugLog)('API KEY RELATION 失败', error instanceof Error ? error.message : String(error));
        console.error(`⚠ API Key 开通关系接口刷新业务参数失败: ${error instanceof Error ? error.message : String(error)}`);
    }
    let accountInformationData = {};
    let hasAccountInformation = false;
    try {
        console.error('→ 正在通过账号信息接口补充完整业务参数...');
        const accountInfo = await (0, account_information_1.acquireAccountInformation)();
        accountInformationData = accountInfo.data || {};
        hasAccountInformation = true;
        if (!accountInfo.matchedGroup && (0, env_1.getEnv)('SL_GROUP_ID')) {
            console.error('⚠ 账号信息接口未找到与 SL_GROUP_ID 匹配的节点，已使用接口返回的可用 ccode/gcode');
        }
        console.error('✓ 账号信息业务参数已获取');
    }
    catch (error) {
        (0, logger_1.debugLog)('ACCOUNT INFORMATION 失败', error instanceof Error ? error.message : String(error));
        console.error(`⚠ 账号信息接口刷新业务参数失败: ${error instanceof Error ? error.message : String(error)}`);
    }
    const mergedData = {
        tokens: {
            ...(accountInformationData.tokens || {}),
            ...(apiKeyRelationData.tokens || {}),
            ...result.tokens,
        },
        ccode: [
            ...(accountInformationData.ccode || []),
            ...(apiKeyRelationData.ccode || []),
        ],
        gcode: [
            ...(accountInformationData.gcode || []),
            ...(apiKeyRelationData.gcode || []),
        ],
    };
    const preferredBizParams = mergeBizParamsFromApiKeySources(accountInformationData, apiKeyRelationData, hasAccountInformation, hasApiKeyRelation);
    await persistSwitchTokenData(mergedData, {}, preferredBizParams);
    console.error('✓ 新旧接口业务参数已合并写入本地缓存');
    try {
        await syncCySAfterSlCredentialPersist();
    }
    catch (error) {
        (0, logger_1.debugLog)('CYSMS AFTER API KEY CREDENTIAL', error instanceof Error ? error.message : String(error));
    }
    const crmToken = readBusinessTokenFromSwitch('crm', result.tokens, {});
    if (crmToken) {
        const crmAuth = buildRequestAuth('crm', crmToken, { sly_token: getCachedRequestSlyToken() });
        const crmResolved = (0, env_2.resolveBaseUrl)('crm', 'SL_CRM_API_BASE_URL');
        if (crmResolved.url) {
            try {
                console.error('→ 正在刷新 CRM 公钥缓存...');
                await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(crmResolved.url, crmAuth, { allowLoginKeyFallback: true });
                console.error('✓ CRM 公钥缓存刷新完成');
            }
            catch {
                // keep token refresh successful even if CRM public key refresh fails
            }
        }
    }
    const token = readBusinessTokenFromSwitch(product, result.tokens, {}) || getToken(product) || null;
    if (product !== 'dc' && product !== 'report' && !token) {
        console.error(`API Key 换 Token 未返回 ${product.toUpperCase()} 可用 token，可能该 API Key 无此业务线权限`);
    }
    return buildRequestAuth(product, token, product === 'crm' ? { sly_token: getCachedRequestSlyToken() } : undefined);
}
async function persistSwitchTokenData(data, headers = {}, preferredBizParams = {}) {
    if (data.tokens?.slyToken) {
        persistRequestSlyToken(data.tokens.slyToken);
    }
    persistAllBusinessTokens(data.tokens || {});
    const bizParams = persistBizParams({
        ...extractBizParams(data),
        ...preferredBizParams,
    }, data);
    for (const [key, value] of Object.entries(bizParams)) {
        if (value && !process.env[key]) {
            process.env[key] = value;
        }
    }
    const cy7BusinessToken = readBusinessTokenFromSwitch('cy7', data.tokens || {}, headers) || getToken('cy7');
    const cy7StoreId = bizParams.SL_CY7_STORE_ID || (0, env_1.getEnv)('SL_CY7_STORE_ID');
    if (cy7BusinessToken && cy7StoreId) {
        try {
            console.error('→ 正在刷新 CY7 品牌信息...');
            const brandId = await refreshCy7BrandId(cy7BusinessToken, cy7StoreId);
            persistCy7BrandId(brandId);
            if (!isBizParamLocked('SL_CY7_BRAND_ID') || !process.env.SL_CY7_BRAND_ID) {
                process.env.SL_CY7_BRAND_ID = brandId;
            }
            console.error('✓ CY7 品牌信息已刷新');
        }
        catch (error) {
            (0, logger_1.debugLog)('CY7 BRAND REFRESH', error instanceof Error ? error.message : String(error));
        }
    }
}
async function refreshBusinessTokensFromSlySession(session) {
    persistShortSlyToken(session.token, session.userId, session.accountId, session);
    console.error('→ 正在通过 switchToken 换取业务 Token...');
    const result = await (0, switch_token_1.switchBusinessToken)({
        slyToken: session.token,
        accountId: session.accountId,
        userId: session.userId,
        deviceType: getSwitchDeviceType(),
    });
    console.error('✓ switchToken 返回成功，正在写入本地缓存...');
    await persistSwitchTokenData(result.response.data || {}, result.headers);
    try {
        await syncCySAfterSlCredentialPersist();
    }
    catch (error) {
        (0, logger_1.debugLog)('CYSMS AFTER SL CREDENTIAL', error instanceof Error ? error.message : String(error));
    }
    const crmToken = readBusinessTokenFromSwitch('crm', result.tokens, result.headers) || getToken('crm');
    const crmAuth = buildRequestAuth('crm', crmToken || null, { sly_token: getCachedRequestSlyToken() });
    const crmResolved = (0, env_2.resolveBaseUrl)('crm', 'SL_CRM_API_BASE_URL');
    if (crmResolved.url) {
        try {
            console.error('→ 正在刷新 CRM 公钥缓存...');
            await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(crmResolved.url, crmAuth, { allowLoginKeyFallback: true });
            console.error('✓ CRM 公钥缓存刷新完成');
        }
        catch {
            // keep view switch successful even if CRM public key refresh fails
        }
    }
}
async function switchProductToken(product, slyToken) {
    const accountId = getSwitchAccountId(product);
    const userId = getCachedUserId();
    if (!accountId || !userId) {
        console.error(`缺少 switchToken 所需参数: ${!accountId ? 'accountId ' : ''}${!userId ? 'userId' : ''}`.trim());
        return null;
    }
    const result = await (0, switch_token_1.switchBusinessToken)({
        slyToken,
        accountId,
        userId,
        deviceType: getSwitchDeviceType(),
        product: product === 'dc' ? undefined : product,
    });
    const headers = normalizeAuthHeaders(product, result.headers);
    await persistSwitchTokenData(result.response.data || {}, headers);
    const businessToken = readBusinessTokenFromSwitch(product, result.tokens, headers);
    const responseData = result.response.data;
    if (responseData) {
        const bizParams = extractBizParams(responseData);
        (0, logger_1.debugLog)('BIZ PARAMS 已刷新', bizParams);
    }
    if (product !== 'dc' && !businessToken) {
        console.error(`switchToken 未返回 ${product.toUpperCase()} 可用 token，可能该账号无此业务线权限`);
    }
    if (product === 'report') {
        const subToken = businessToken || getToken('report');
        if (subToken) {
            const reportResolved = (0, env_2.resolveBaseUrl)('report', 'SL_REPORT_API_BASE_URL');
            if (reportResolved.url) {
                try {
                    const loginResult = await (0, report_login_1.refreshReportSession)(subToken, reportResolved.url);
                    (0, token_cache_1.saveTokenValue)('report_session_token', loginResult.token);
                    (0, token_cache_1.saveTokenValue)('report_jsessionid', loginResult.jsessionid);
                    (0, logger_1.debugLog)('REPORT LOGIN', `token=${loginResult.token.substring(0, 30)}... jsessionid=${loginResult.jsessionid}`);
                    const reportAuth = buildRequestAuth(product, loginResult.token, headers);
                    return reportAuth;
                }
                catch (error) {
                    const msg = error instanceof Error ? error.message : String(error);
                    console.error(`⚠ 报表中心登录流程失败: ${msg}`);
                    console.error('  将使用 subToken 直连（部分接口可能返回异常）');
                }
            }
        }
    }
    const auth = buildRequestAuth(product, businessToken || getToken(product) || null, headers);
    if (product === 'crm') {
        const resolved = (0, env_2.resolveBaseUrl)(product, 'SL_CRM_API_BASE_URL');
        if (resolved.url) {
            try {
                await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(resolved.url, auth, { allowLoginKeyFallback: true });
            }
            catch {
                // keep token refresh successful even if CRM public key refresh fails
            }
        }
    }
    return auth;
}
function getRequestAuth(product) {
    const token = getToken(product) || null;
    if (product === 'dc') {
        const slyHeader = getCachedRequestSlyToken();
        return buildRequestAuth(product, null, slyHeader ? { 'Sly-Token': slyHeader } : undefined);
    }
    return buildRequestAuth(product, token, product === 'crm' ? { sly_token: getCachedRequestSlyToken() } : undefined);
}
async function refreshRequestAuth(product) {
    try {
        const apiKeyAuth = await refreshBusinessTokensByApiKey(product);
        if (apiKeyAuth && hasRequestAuth(apiKeyAuth)) {
            return apiKeyAuth;
        }
    }
    catch (error) {
        (0, logger_1.debugLog)('API Key 换 Token 失败', error instanceof Error ? error.message : String(error));
        console.error(`✗ API Key 换 Token 失败: ${error instanceof Error ? error.message : String(error)}`);
        return null;
    }
    // API Key 未提供该产品 Token
    if ((0, api_key_token_1.hasApiKeyTokenConfig)()) {
        console.error(`✗ API Key 未提供 ${product.toUpperCase()} 可用认证信息`);
        console.error('  请检查 SL_API_KEY 是否具备该业务线权限');
    }
    return null;
}
function stripBearer(token) {
    return token.startsWith('Bearer ') ? token.slice(7) : token;
}
function hasRequestAuth(auth) {
    return !!auth.sessionToken || Object.keys(auth.headers || {}).length > 0;
}
/** scm_analysis：若设置 SL_ANALYSIS_AUTHORIZATION_OVERRIDE，则用其覆盖 Authorization 与 Fx-Token（值与浏览器 Network 中 Authorization 一致）。 */
function mergeScmAnalysisAuthFromEnv(domain, auth) {
    if (domain !== 'scm_analysis') {
        return auth;
    }
    const override = (0, env_1.getEnv)('SL_ANALYSIS_AUTHORIZATION_OVERRIDE', '').trim();
    if (!override) {
        return auth;
    }
    const forFx = stripBearer(override);
    return {
        sessionToken: override,
        headers: {
            ...(auth.headers || {}),
            'Fx-Token': forFx,
        },
    };
}
async function refreshToken(product) {
    const config = constants_1.LOGIN_ENDPOINTS[product];
    if (!config) {
        console.error(`不支持的产品类型: ${product}`);
        return null;
    }
    const baseUrl = (0, env_1.getEnv)(config.envBaseUrl);
    const username = (0, env_1.getEnv)(config.envUsername);
    const password = (0, env_1.getEnv)(config.envPassword);
    if (!baseUrl || !username || !password) {
        console.error('Token 刷新需要以下环境变量:');
        console.error(`  ${config.envBaseUrl} (当前: ${baseUrl ? '已设置' : '未设置'})`);
        console.error(`  ${config.envUsername} (当前: ${username ? '已设置' : '未设置'})`);
        console.error(`  ${config.envPassword} (当前: ${password ? '已设置' : '未设置'})`);
        return null;
    }
    console.error(`→ 正在刷新 ${product.toUpperCase()} Token...`);
    try {
        const result = await (0, request_1.makeRequest)(baseUrl, { path: config.login, method: 'POST' }, null, { loginName: username, password }, product);
        const token = readTokenField(result, config.tokenField);
        if (!token) {
            console.error('✗ 登录响应中未找到 Token，响应:');
            console.error(JSON.stringify(result, null, 2).substring(0, 500));
            return null;
        }
        persistProductToken(product, token);
        console.error('✓ Token 刷新成功，已缓存 (有效期 2h)');
        return token;
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`✗ Token 刷新失败: ${message}`);
        return null;
    }
}
function isTokenExpiredResponse(result, product) {
    if (!result || typeof result !== 'object') {
        return false;
    }
    const record = result;
    if (product === 'cy7' && (record.result === -22 || record.code === '-22')) {
        return true;
    }
    if (product === 'crm') {
        if (record.code === '431' || record.code === 431) {
            const message = record.message;
            if (typeof message === 'string' && message && record.data === null) {
                return true;
            }
            return true;
        }
    }
    if (product === 'scm' && (record.code === 401 || record.code === '401' || record.status === 401
        || record.code === 100001 || record.code === '100001')) {
        return true;
    }
    const messageValue = [record.message, record.msg, record.error].find((item) => typeof item === 'string');
    const message = typeof messageValue === 'string' ? messageValue.toLowerCase() : '';
    if (product === 'dc' && (record.code === 4 || record.code === '4') && /token.*过期|token已过期/i.test(message)) {
        return true;
    }
    if (/解密失败|decrypt/i.test(message))
        return false;
    const httpStatus = record._httpStatus;
    if (httpStatus === 401 || httpStatus === 403) {
        return true;
    }
    const code = record.code || record.status || record.errcode;
    if (code === 401 || code === 403 || code === '401' || code === '403') {
        return true;
    }
    return /token.*expir|session.*expir|unauthorized|未登录|登录过期|token.*invalid|无效.*token|无法获取登录信息/i.test(message);
}
