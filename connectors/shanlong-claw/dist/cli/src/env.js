"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.extractEnvPath = extractEnvPath;
exports.stripEnvPathFromArgs = stripEnvPathFromArgs;
exports.loadEnvFiles = loadEnvFiles;
exports.getEnv = getEnv;
exports.resolveBaseUrl = resolveBaseUrl;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const constants_1 = require("./constants");
const token_cache_1 = require("./token-cache");
const BIZ_PARAM_KEYS = new Set([
    'SL_CY7_GROUP_ID',
    'SL_CY7_STORE_ID',
    'SL_CY7_BRAND_ID',
    'SL_CRM_GROUP_ID',
    'SL_CRM_GC_ID',
    'SL_CRM_STORE_ID',
    'SL_SCM_GROUP_ID',
    'SL_SCM_STORE_ID',
    'SL_UNIFIED_G_ID',
    'omShopCodes',
    'cy_omShopCodes',
    'crm_omShopCodes',
    'scm_omShopCodes',
    'omShopCodeOrgNameMap',
]);
const TOKEN_JSON_FIRST_KEYS = new Set([
    'SL_CRM_SLY_TOKEN',
]);
const TOKEN_BACKED_ENV_KEY_MAP = {
    SL_USER_ID: ['SL_USER_ID', 'user_id', 'userId'],
    SL_GROUP_ID: ['SL_GROUP_ID', 'orgId'],
    SL_ORG_NAME: ['SL_ORG_NAME', 'orgName'],
};
function parseCsvSet(value) {
    return new Set(value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean));
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
function readTokenBackedEnv(key) {
    if (BIZ_PARAM_KEYS.has(key)) {
        const rawBizParams = (0, token_cache_1.loadTokenValue)('biz_params');
        if (!rawBizParams || typeof rawBizParams !== 'object' || Array.isArray(rawBizParams)) {
            return '';
        }
        const bizValue = rawBizParams[key];
        return typeof bizValue === 'string' && bizValue ? bizValue : '';
    }
    if (key === 'SL_CRM_SLY_TOKEN') {
        const slyToken = (0, token_cache_1.loadTokenValue)('sly_remote_token');
        if (typeof slyToken === 'string' && slyToken) {
            return slyToken;
        }
    }
    const tokenKeys = TOKEN_BACKED_ENV_KEY_MAP[key];
    if (tokenKeys) {
        for (const tokenKey of tokenKeys) {
            const value = (0, token_cache_1.loadTokenValue)(tokenKey);
            if (typeof value === 'string' && value) {
                return value;
            }
        }
    }
    const directValue = (0, token_cache_1.loadTokenValue)(key);
    return typeof directValue === 'string' && directValue ? directValue : '';
}
function parseEnvLine(line) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) {
        return null;
    }
    const exportPrefix = trimmed.startsWith('export ') ? trimmed.slice(7).trim() : trimmed;
    const separatorIndex = exportPrefix.indexOf('=');
    if (separatorIndex <= 0) {
        return null;
    }
    const key = exportPrefix.slice(0, separatorIndex).trim();
    if (!key) {
        return null;
    }
    let value = exportPrefix.slice(separatorIndex + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"'))
        || (value.startsWith('\'') && value.endsWith('\''))) {
        value = value.slice(1, -1);
    }
    return [key, value];
}
function parseEnvFile(filePath) {
    if (!fs_1.default.existsSync(filePath)) {
        return {};
    }
    const content = fs_1.default.readFileSync(filePath, 'utf-8');
    const result = {};
    for (const line of content.split(/\r?\n/)) {
        const parsed = parseEnvLine(line);
        if (parsed) {
            const [key, value] = parsed;
            result[key] = value;
        }
    }
    return result;
}
function resolveEnvFile(targetPath) {
    if (!fs_1.default.existsSync(targetPath)) {
        return path_1.default.join(targetPath, '.env');
    }
    return fs_1.default.statSync(targetPath).isDirectory() ? path_1.default.join(targetPath, '.env') : targetPath;
}
function applyEnvValues(values, protectedKeys) {
    for (const [key, value] of Object.entries(values)) {
        if (!protectedKeys.has(key)) {
            process.env[key] = value;
        }
    }
}
function extractEnvPath(args) {
    for (let index = 0; index < args.length; index += 1) {
        if (args[index] === '--envPath' && args[index + 1]) {
            return args[index + 1];
        }
    }
    return '';
}
/** 路由前去掉 `--envPath <path>`（已由 loadEnvFiles 消费），避免误当作 domain。 */
function stripEnvPathFromArgs(args) {
    const out = [];
    for (let i = 0; i < args.length; i += 1) {
        if (args[i] === '--envPath' && args[i + 1]) {
            i += 1;
            continue;
        }
        out.push(args[i]);
    }
    return out;
}
function loadEnvFiles(envPath = '') {
    const systemKeys = new Set(Object.keys(process.env));
    // ~/.slclaw/.env 是主配置（生产环境），优先级最高
    const cliHome = process.env.SL_CLI_HOME
        || path_1.default.join(process.env.HOME || process.env.USERPROFILE || '', '.slclaw');
    const cliHomeEnv = path_1.default.join(cliHome, '.env');
    if (fs_1.default.existsSync(cliHomeEnv)) {
        applyEnvValues(parseEnvFile(cliHomeEnv), systemKeys);
    }
    // CWD .env 作为补充（不覆盖已有值）
    const alreadySet = new Set(Object.keys(process.env).filter((k) => process.env[k]));
    const cwdEnvFile = path_1.default.join(process.cwd(), '.env');
    if (path_1.default.resolve(cwdEnvFile) !== path_1.default.resolve(cliHomeEnv)) {
        applyEnvValues(parseEnvFile(cwdEnvFile), alreadySet);
    }
    if (envPath) {
        const resolvedTarget = path_1.default.resolve(process.cwd(), envPath);
        const extraEnvFile = resolveEnvFile(resolvedTarget);
        if (path_1.default.resolve(extraEnvFile) !== path_1.default.resolve(cwdEnvFile)
            && path_1.default.resolve(extraEnvFile) !== path_1.default.resolve(cliHomeEnv)) {
            applyEnvValues(parseEnvFile(extraEnvFile), alreadySet);
        }
    }
}
function getEnv(key, fallback = '') {
    if (TOKEN_BACKED_ENV_KEY_MAP[key] && process.env[key]) {
        return process.env[key] || fallback;
    }
    if (BIZ_PARAM_KEYS.has(key) && isBizParamLocked(key) && process.env[key]) {
        return process.env[key] || fallback;
    }
    if (BIZ_PARAM_KEYS.has(key) || TOKEN_JSON_FIRST_KEYS.has(key) || TOKEN_BACKED_ENV_KEY_MAP[key]) {
        const tokenStoreValue = readTokenBackedEnv(key);
        if (tokenStoreValue) {
            return tokenStoreValue;
        }
    }
    return process.env[key] || fallback;
}
function isExplicitTrue(value) {
    return ['true', '1', 'yes'].includes(value.toLowerCase());
}
function isExplicitFalse(value) {
    return ['false', '0', 'no'].includes(value.toLowerCase());
}
function resolveBaseUrl(product, envBaseUrlKey) {
    const gatewayHost = getEnv('SL_GATEWAY_HOST');
    const perProductFlag = getEnv(`SL_${product.toUpperCase()}_VIA_GATEWAY`);
    const explicitBaseUrl = getEnv(envBaseUrlKey);
    // If a product-specific base URL is configured, respect it first.
    // This lets commands store only the suffix path while the full prefix
    // comes from .env (for example SL_DC_API_BASE_URL=https://.../aiproxy).
    if (explicitBaseUrl) {
        return { url: explicitBaseUrl, viaGateway: false };
    }
    if (perProductFlag && isExplicitFalse(perProductFlag)) {
        return { url: explicitBaseUrl, viaGateway: false };
    }
    if (perProductFlag && isExplicitTrue(perProductFlag) && gatewayHost && constants_1.GATEWAY_ROUTE_PREFIX[product]) {
        const host = gatewayHost.replace(/\/+$/, '');
        return { url: `${host}/${constants_1.GATEWAY_ROUTE_PREFIX[product]}`, viaGateway: true };
    }
    if (!perProductFlag && gatewayHost && constants_1.GATEWAY_ROUTE_PREFIX[product]) {
        const host = gatewayHost.replace(/\/+$/, '');
        return { url: `${host}/${constants_1.GATEWAY_ROUTE_PREFIX[product]}`, viaGateway: true };
    }
    return { url: explicitBaseUrl, viaGateway: false };
}
