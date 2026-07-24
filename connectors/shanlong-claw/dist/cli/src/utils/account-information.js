"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.acquireAccountInformation = acquireAccountInformation;
const env_1 = require("../env");
const logger_1 = require("../logger");
const http_timeout_1 = require("./http-timeout");
const ACCOUNT_INFORMATION_PATH = '/newProxy/basic-data/api/ano/get/account/information';
function normalizeBaseUrl(baseUrl) {
    return baseUrl.replace(/\/+$/, '');
}
function requireValue(value, label) {
    if (!value) {
        throw new Error(`缺少 ${label}`);
    }
    return value;
}
function buildAccountInformationUrl(options) {
    const explicitUrl = options.url || (0, env_1.getEnv)('SL_ACCOUNT_INFORMATION_URL');
    if (explicitUrl) {
        return explicitUrl;
    }
    const baseUrl = requireValue(options.baseUrl || (0, env_1.getEnv)('SL_ACCOUNT_INFORMATION_BASEURL') || (0, env_1.getEnv)('SL_API_KEY_BASEURL') || (0, env_1.getEnv)('SL_SLY_BASEURL'), 'SL_ACCOUNT_INFORMATION_BASEURL 或 SL_SLY_BASEURL');
    return `${normalizeBaseUrl(baseUrl)}${ACCOUNT_INFORMATION_PATH}`;
}
function assertAccountInformationSuccess(response) {
    const code = response.code !== undefined ? String(response.code) : '';
    if (response.success === false || (code && code !== '2000' && code !== '200')) {
        const codeText = code ? ` code=${code}` : '';
        const messageText = response.message ? ` message=${response.message}` : '';
        throw new Error(`账号信息接口业务错误:${codeText}${messageText}`.trim());
    }
}
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isSwitchTokenData(value) {
    return isRecord(value) && (Array.isArray(value.ccode) || Array.isArray(value.gcode) || isRecord(value.tokens));
}
function normalizeId(value) {
    return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
}
function recordMatchesGroup(record, groupId) {
    if (!groupId) {
        return false;
    }
    const directKeys = [
        'groupId',
        'accountId',
        'orgId',
        'rootId',
        'corpId',
        'id',
    ];
    return directKeys.some((key) => normalizeId(record[key]) === groupId);
}
function filterEntriesByGroup(entries, groupId) {
    if (!Array.isArray(entries)) {
        return undefined;
    }
    if (!groupId) {
        return entries;
    }
    const matched = entries.filter((entry) => isRecord(entry) && recordMatchesGroup(entry, groupId));
    return matched.length > 0 ? matched : entries;
}
function normalizeSwitchTokenData(data, groupId) {
    const ccode = filterEntriesByGroup(data.ccode, groupId);
    const gcode = filterEntriesByGroup(data.gcode, groupId);
    const matchedGroup = !!groupId && ((Array.isArray(data.ccode) && data.ccode.some((entry) => isRecord(entry) && recordMatchesGroup(entry, groupId)))
        || (Array.isArray(data.gcode) && data.gcode.some((entry) => isRecord(entry) && recordMatchesGroup(entry, groupId))));
    return {
        data: {
            ...data,
            ...(ccode ? { ccode: ccode } : {}),
            ...(gcode ? { gcode: gcode } : {}),
        },
        matchedGroup,
    };
}
function findSwitchTokenData(value, groupId, preferGroupMatch) {
    if (isSwitchTokenData(value)) {
        const normalized = normalizeSwitchTokenData(value, groupId);
        if (!preferGroupMatch || normalized.matchedGroup) {
            return normalized;
        }
        return null;
    }
    if (Array.isArray(value)) {
        for (const item of value) {
            const found = findSwitchTokenData(item, groupId, preferGroupMatch);
            if (found && (!preferGroupMatch || found.matchedGroup)) {
                return found;
            }
        }
        return preferGroupMatch ? null : value.map((item) => findSwitchTokenData(item, groupId, false)).find(Boolean) || null;
    }
    if (!isRecord(value)) {
        return null;
    }
    if (preferGroupMatch && recordMatchesGroup(value, groupId)) {
        const ownData = findSwitchTokenData({ ...value, groupId: undefined, accountId: undefined, orgId: undefined, rootId: undefined, corpId: undefined, id: undefined }, groupId, false);
        if (ownData) {
            return { data: ownData.data, matchedGroup: true };
        }
    }
    for (const child of Object.values(value)) {
        const found = findSwitchTokenData(child, groupId, preferGroupMatch);
        if (found) {
            return found;
        }
    }
    return null;
}
function extractAccountInformationData(response, groupId) {
    const root = response.data ?? response;
    const matched = findSwitchTokenData(root, groupId, true);
    if (matched) {
        return matched;
    }
    const fallback = findSwitchTokenData(root, groupId, false);
    if (fallback) {
        return fallback;
    }
    return { data: {}, matchedGroup: false };
}
async function acquireAccountInformation(options = {}) {
    const userId = requireValue((options.userId || (0, env_1.getEnv)('SL_USER_ID')).trim(), 'SL_USER_ID');
    const groupId = (options.groupId || (0, env_1.getEnv)('SL_GROUP_ID')).trim();
    const url = buildAccountInformationUrl(options);
    const body = JSON.stringify({
        accountIds: [userId],
    });
    (0, logger_1.debugLog)('ACCOUNT INFORMATION REQUEST', {
        method: 'POST',
        url,
        body,
    });
    const response = await (0, http_timeout_1.fetchWithTimeout)(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=UTF-8',
        },
        body,
    }, '账号信息接口', (0, http_timeout_1.getRequestTimeoutMs)('SL_ACCOUNT_INFORMATION_TIMEOUT_MS'));
    const text = await response.text();
    if (!response.ok) {
        throw new Error(`账号信息接口 HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`);
    }
    let parsed;
    try {
        parsed = JSON.parse(text);
    }
    catch {
        throw new Error(`账号信息接口返回非 JSON: ${text.slice(0, 200)}`);
    }
    (0, logger_1.debugLog)('ACCOUNT INFORMATION RESPONSE', {
        status: response.status,
        url,
        body: parsed,
    });
    assertAccountInformationSuccess(parsed);
    const extracted = extractAccountInformationData(parsed, groupId);
    return {
        response: parsed,
        data: extracted.data,
        matchedGroup: extracted.matchedGroup,
    };
}
