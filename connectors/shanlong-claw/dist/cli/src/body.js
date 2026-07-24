"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildBody = buildBody;
exports.printBodyBuildDetails = printBodyBuildDetails;
exports.getFormat = getFormat;
exports.getAuthMode = getAuthMode;
const cy7_omshop_store_map_1 = require("./cy7-omshop-store-map");
const env_1 = require("./env");
const logger_1 = require("./logger");
const RESERVED_FLAG_KEYS = ['format', 'f', 'verbose', 'v', 'envPath', 'params', 'body', 'header', 'bodyFile', 'body-file'];
const DATACUBE_BIZ_PARAM_KEYS = new Set([
    'SL_CY7_GROUP_ID',
    'SL_CY7_STORE_ID',
    'SL_CY7_BRAND_ID',
    'SL_CRM_GC_ID',
    'SL_CRM_STORE_ID',
    'SL_SCM_GROUP_ID',
    'SL_SCM_STORE_ID',
    'SL_UNIFIED_G_ID',
    'omShopCodes',
    'cy_omShopCodes',
    'crm_omShopCodes',
    'scm_omShopCodes',
]);
const DATACUBE_AUTO_PARAM_KEYS = new Set(['cy_group_code', 'cy_store_code']);
const DATACUBE_WHERE_DOMAIN = 'datacube_where';
const SCM_DATACUBE_WHERE_DOMAIN = 'scm_datacube_where';
const CRM_DATACUBE_WHERE_DOMAIN = 'crm_datacube_where';
function hasParameter(cmd, name) {
    return (cmd.parameters || []).some((parameter) => parameter.name === name);
}
function legacyDataCubeParamName(cmd, name) {
    const hasCrmGroup = hasParameter(cmd, 'SL_CRM_GC_ID');
    const hasCy7Group = hasParameter(cmd, 'SL_CY7_GROUP_ID');
    const hasCyGroupCode = hasParameter(cmd, 'cy_group_code');
    const hasCrmStore = hasParameter(cmd, 'SL_CRM_STORE_ID');
    const hasCy7Store = hasParameter(cmd, 'SL_CY7_STORE_ID');
    const hasCyStoreCode = hasParameter(cmd, 'cy_store_code');
    if (name === 'crmGroupCode' || name === 'cyGroupCode' || name === 'groupCode') {
        if (name === 'cyGroupCode' && hasCyGroupCode)
            return 'cy_group_code';
        if (name === 'crmGroupCode' && hasCrmGroup)
            return 'SL_CRM_GC_ID';
        if (name === 'cyGroupCode' && hasCy7Group)
            return 'SL_CY7_GROUP_ID';
        if (hasCyGroupCode && !hasCrmGroup && !hasCy7Group)
            return 'cy_group_code';
        if (hasCrmGroup && !hasCy7Group)
            return 'SL_CRM_GC_ID';
        if (hasCy7Group && !hasCrmGroup)
            return 'SL_CY7_GROUP_ID';
    }
    if (name === 'crmStoreCode' ||
        name === 'crmStoreCodeCsv' ||
        name === 'cyStoreCode' ||
        name === 'cyStoreCodeCsv' ||
        name === 'storeCode' ||
        name === 'store-id' ||
        name === 'storeId' ||
        name === 'store-name' ||
        name === 'storename') {
        if ((name === 'cyStoreCode' ||
            name === 'cyStoreCodeCsv' ||
            name === 'store-id' ||
            name === 'storeId' ||
            name === 'store-name' ||
            name === 'storename') &&
            hasCyStoreCode) {
            return 'cy_store_code';
        }
        if ((name === 'crmStoreCode' || name === 'crmStoreCodeCsv') && hasCrmStore)
            return 'SL_CRM_STORE_ID';
        if ((name === 'cyStoreCode' || name === 'cyStoreCodeCsv') && hasCy7Store)
            return 'SL_CY7_STORE_ID';
        if (hasCyStoreCode && !hasCrmStore && !hasCy7Store)
            return 'cy_store_code';
        if (hasCrmStore && !hasCy7Store)
            return 'SL_CRM_STORE_ID';
        if (hasCy7Store && !hasCrmStore)
            return 'SL_CY7_STORE_ID';
    }
    return name;
}
function isReservedFlag(key) {
    return RESERVED_FLAG_KEYS.includes(key);
}
function canBeEmptyDataCubeBizParam(name) {
    return name.endsWith('_STORE_ID');
}
function getDataCubeAutoParam(cmd, name) {
    if (cmd.product !== 'dc') {
        return '';
    }
    if (name === 'cy_group_code') {
        return (0, env_1.getEnv)('SL_CY7_GROUP_ID');
    }
    if (name === 'cy_store_code') {
        return (0, cy7_omshop_store_map_1.readCy7OmshopStoreMap)().omShopCodes;
    }
    return '';
}
function isDataCubeWhereCommand(cmd) {
    return cmd.product === 'dc' && cmd.domain === DATACUBE_WHERE_DOMAIN;
}
function isScmDataCubeWhereCommand(cmd) {
    return cmd.product === 'dc' && cmd.domain === SCM_DATACUBE_WHERE_DOMAIN;
}
function isCrmDataCubeWhereCommand(cmd) {
    return cmd.product === 'dc' && cmd.domain === CRM_DATACUBE_WHERE_DOMAIN;
}
function readFirstString(record, keys) {
    for (const key of keys) {
        const value = record[key];
        if (typeof value === 'string' && value.trim()) {
            return value.trim();
        }
        if (typeof value === 'number' && Number.isFinite(value)) {
            return String(value);
        }
    }
    return '';
}
function formatSqlLiteral(value) {
    const raw = value.trim();
    if (/^'.*'$/.test(raw)) {
        return raw;
    }
    return `'${raw.replace(/'/g, "''")}'`;
}
function parseCommaValues(value) {
    return parseCommaTokens(value).map((token) => token.value);
}
function parseCommaTokens(value) {
    const trimmed = value.trim();
    const listValue = /^in\s*\((.*)\)$/is.test(trimmed)
        ? trimmed.replace(/^in\s*\((.*)\)$/is, '$1')
        : trimmed;
    return listValue
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
        .map((item) => {
        let normalized = item;
        if (normalized.startsWith("'")) {
            normalized = normalized.slice(1);
        }
        if (normalized.endsWith("'")) {
            normalized = normalized.slice(0, -1);
        }
        normalized = normalized.replace(/''/g, "'");
        return { raw: item, value: normalized };
    })
        .filter((item) => item.value);
}
function formatSqlList(tokens) {
    return tokens.map((token) => formatSqlLiteral(token.value)).join(',');
}
function normalizeWhereClause(where) {
    const normalized = where.trim().replace(/^and\b\s*/i, '').trim();
    return normalized || '1=1';
}
function splitTopLevelSqlExpressions(value) {
    const expressions = [];
    let start = 0;
    let depth = 0;
    let quote = null;
    for (let index = 0; index < value.length; index += 1) {
        const char = value[index];
        if (quote) {
            if (char === quote) {
                if (value[index + 1] === quote) {
                    index += 1;
                }
                else {
                    quote = null;
                }
            }
            continue;
        }
        if (char === "'" || char === '"') {
            quote = char;
        }
        else if (char === '(') {
            depth += 1;
        }
        else if (char === ')') {
            depth = Math.max(0, depth - 1);
        }
        else if (char === ',' && depth === 0) {
            const expression = value.slice(start, index).trim();
            if (expression)
                expressions.push(expression);
            start = index + 1;
        }
    }
    const expression = value.slice(start).trim();
    if (expression)
        expressions.push(expression);
    return expressions;
}
function stripSqlAlias(expression) {
    return expression.replace(/\s+as\s+(?:`[^`]+`|"[^"]+"|\[[^\]]+\]|[^\s]+)\s*$/i, '').trim();
}
function isAggregateExpression(expression) {
    return /\b(?:sum|count|avg|min|max)\s*\(/i.test(expression);
}
function isSimpleDimensionExpression(expression) {
    return /^[\w\u4e00-\u9fff.]+$/u.test(stripSqlAlias(expression));
}
function isConstantExpression(expression) {
    const normalized = stripSqlAlias(expression);
    return /^(?:null|true|false|[-+]?\d+(?:\.\d+)?|'(?:''|[^'])*'|"(?:""|[^"])*")$/is.test(normalized);
}
function validateDataCubeWhereQuery(title, where) {
    if (/\b(?:shopid|store_code)\b/i.test(where)) {
        throw new Error('DataCube 查询已拦截：门店范围不能写在 --where 中（包括 shopid IN/NOT IN 或 store_code 条件）。' +
            '请删除该条件，并改用 --shopid "in (\'<真实门店编码1>\',\'<真实门店编码2>\')" 传入保留门店的正向编码清单。');
    }
    if (/\blike\b/i.test(where)) {
        throw new Error('DataCube 查询已拦截：当前 datacube_where 不允许使用 LIKE 模糊匹配。' +
            '请改为 INSTR(<字段>, \'<关键词>\') > 0，例如 INSTR(结算方式名称, \'会员券\') > 0。');
    }
    const expressions = splitTopLevelSqlExpressions(title);
    const hasAggregate = expressions.some(isAggregateExpression);
    const dimensions = expressions
        .filter((expression) => !isAggregateExpression(expression))
        .map(stripSqlAlias)
        .filter((expression) => !isConstantExpression(expression));
    if (!hasAggregate || dimensions.length === 0) {
        return;
    }
    const groupByMatch = /\bgroup\s+by\s+(.+?)(?:\bhaving\b|\border\s+by\b|$)/is.exec(where);
    if (!groupByMatch) {
        throw new Error(`DataCube 查询已拦截：--title 同时包含聚合指标和维度字段（${dimensions.join('、')}），但 --where 缺少 GROUP BY。` +
            `请在筛选条件后追加 GROUP BY ${dimensions.join(',')}；例如：<原筛选条件> GROUP BY ${dimensions.join(',')} ORDER BY <指标>。`);
    }
    const normalizedGroupBy = groupByMatch[1].replace(/\s+/g, '').toLowerCase();
    const missingDimensions = dimensions
        .filter(isSimpleDimensionExpression)
        .filter((dimension) => !normalizedGroupBy.includes(dimension.replace(/\s+/g, '').toLowerCase()));
    if (missingDimensions.length > 0) {
        throw new Error(`DataCube 查询已拦截：GROUP BY 未包含 --title 中的全部维度字段，缺少：${missingDimensions.join('、')}。` +
            `请改为 GROUP BY ${dimensions.join(',')}，再执行查询。`);
    }
}
function applyDataCubeWhereContext(rest, cmd) {
    if (!isDataCubeWhereCommand(cmd)) {
        return;
    }
    const groupCode = (0, env_1.getEnv)('SL_UNIFIED_G_ID');
    const cyGroupCode = (0, env_1.getEnv)('SL_CY7_GROUP_ID');
    const allowedShopidTokens = parseCommaTokens((0, env_1.getEnv)('cy_omShopCodes'));
    const rawShopid = readFirstString(rest, ['shopid', 'shopId', 'shop-id'])
        || (0, env_1.getEnv)('cy_omShopCodes');
    const requestedShopids = parseCommaValues(rawShopid);
    const allowedByValue = new Map(allowedShopidTokens.map((token) => [token.value, token]));
    const seenShopids = new Set();
    const shopidTokens = requestedShopids
        .map((shopid) => allowedByValue.get(shopid))
        .filter((token) => !!token)
        .filter((token) => {
        if (seenShopids.has(token.value)) {
            return false;
        }
        seenShopids.add(token.value);
        return true;
    });
    const shopid = formatSqlList(shopidTokens);
    const where = normalizeWhereClause(readFirstString(rest, ['where']));
    const title = readFirstString(rest, ['title']);
    if (!groupCode) {
        throw new Error('缺少运行参数 group_code，请先登录或切换到包含 SL_UNIFIED_G_ID 的组织。');
    }
    if (!cyGroupCode) {
        throw new Error('缺少运行参数 cy_group_code，请先登录或切换到包含 SL_CY7_GROUP_ID 的组织。');
    }
    if (shopidTokens.length === 0) {
        throw new Error('缺少运行参数 shopid，请传入 --shopid，或先刷新 Token 以获取 cy_omShopCodes 门店权限。');
    }
    validateDataCubeWhereQuery(title, where);
    rest.where = where;
    rest.group_code = formatSqlLiteral(groupCode);
    rest.cy_group_code = formatSqlLiteral(cyGroupCode);
    rest.shopid = shopid;
    rest.store_code = shopid;
    for (const key of ['groupCode', 'group-code', 'ts_code', 'tsCode', 'ts-code', 'storeCode', 'store-code', 'shopId', 'shop-id']) {
        delete rest[key];
    }
}
function applyScmDataCubeWhereContext(rest, cmd) {
    if (!isScmDataCubeWhereCommand(cmd)) {
        return;
    }
    const groupCode = (0, env_1.getEnv)('SL_SCM_GROUP_ID');
    const allowedStoreCodeTokens = parseCommaTokens((0, env_1.getEnv)('scm_omShopCodes'));
    const rawShopid = readFirstString(rest, ['shopid', 'shopId', 'shop-id'])
        || (0, env_1.getEnv)('scm_omShopCodes');
    const requestedShopids = parseCommaValues(rawShopid);
    const allowedByValue = new Map(allowedStoreCodeTokens.map((token) => [token.value, token]));
    const seenShopids = new Set();
    const storeCodeTokens = requestedShopids
        .map((shopid) => allowedByValue.get(shopid))
        .filter((token) => !!token)
        .filter((token) => {
        if (seenShopids.has(token.value)) {
            return false;
        }
        seenShopids.add(token.value);
        return true;
    });
    const where = normalizeWhereClause(readFirstString(rest, ['where']));
    if (!groupCode) {
        throw new Error('缺少运行参数 group_code，请先登录或切换到包含 SL_SCM_GROUP_ID 的供应链组织。');
    }
    if (storeCodeTokens.length === 0) {
        throw new Error('缺少运行参数 shopid，请传入 --shopid，或先刷新 Token 以获取 scm_omShopCodes 门店权限。');
    }
    if (/\b(?:group_code|store_code)\b/i.test(where)) {
        throw new Error('供应链 DataCube 查询已拦截：--where 不能包含 group_code 或 store_code；CLI 会按当前供应链授权范围自动注入。');
    }
    for (const key of ['group_code', 'groupCode', 'group-code', 'store_code', 'storeCode', 'store-code', 'shopid', 'shopId', 'shop-id']) {
        delete rest[key];
    }
    rest.where = where;
    rest.group_code = formatSqlLiteral(groupCode);
    rest.store_code = formatSqlList(storeCodeTokens);
}
function applyCrmDataCubeWhereContext(rest, cmd) {
    if (!isCrmDataCubeWhereCommand(cmd)) {
        return;
    }
    const crmGroupCode = (0, env_1.getEnv)('SL_CRM_GROUP_ID');
    const allowedShopidTokens = parseCommaTokens((0, env_1.getEnv)('crm_omShopCodes'));
    const rawShopid = readFirstString(rest, ['shopid', 'shopId', 'shop-id'])
        || (0, env_1.getEnv)('crm_omShopCodes');
    const requestedShopids = parseCommaValues(rawShopid);
    const allowedByValue = new Map(allowedShopidTokens.map((token) => [token.value, token]));
    const seenShopids = new Set();
    const shopidTokens = requestedShopids
        .map((shopid) => allowedByValue.get(shopid))
        .filter((token) => !!token)
        .filter((token) => {
        if (seenShopids.has(token.value)) {
            return false;
        }
        seenShopids.add(token.value);
        return true;
    });
    const shopid = formatSqlList(shopidTokens);
    const where = normalizeWhereClause(readFirstString(rest, ['where']));
    const title = readFirstString(rest, ['title']);
    if (!crmGroupCode) {
        throw new Error('缺少运行参数 crm_group_code，请先登录或切换到包含 SL_CRM_GROUP_ID 的 CRM 组织。');
    }
    if (shopidTokens.length === 0) {
        throw new Error('缺少运行参数 shopid，请传入 --shopid，或先刷新 Token 以获取 crm_omShopCodes 门店权限。');
    }
    validateDataCubeWhereQuery(title, where);
    rest.where = where;
    rest.crm_group_code = formatSqlLiteral(crmGroupCode);
    rest.shopid = shopid;
    rest.store_code = shopid;
    for (const key of ['group_code', 'groupCode', 'group-code', 'crmGroupCode', 'crm-group-code', 'storeCode', 'store-code', 'shopId', 'shop-id']) {
        delete rest[key];
    }
}
function buildBody(cmd, flags, jsonLayers = {}) {
    const body = {};
    for (const [param, envKey] of Object.entries(cmd.env_mapping)) {
        if (!param.startsWith('_')) {
            const value = (0, env_1.getEnv)(envKey);
            if (value) {
                body[param] = value;
            }
        }
    }
    if (cmd.product === 'dc') {
        for (const parameter of cmd.parameters || []) {
            if (!DATACUBE_BIZ_PARAM_KEYS.has(parameter.name) || body[parameter.name] !== undefined) {
                continue;
            }
            const value = (0, env_1.getEnv)(parameter.name);
            if (value) {
                body[parameter.name] = value;
            }
        }
        for (const parameter of cmd.parameters || []) {
            if (body[parameter.name] !== undefined) {
                continue;
            }
            const value = getDataCubeAutoParam(cmd, parameter.name);
            if (value) {
                body[parameter.name] = value;
            }
        }
    }
    for (const parameter of cmd.parameters || []) {
        if (parameter.default !== undefined && body[parameter.name] === undefined) {
            body[parameter.name] = parameter.default;
        }
    }
    for (const [key, value] of Object.entries(flags)) {
        if (!isReservedFlag(key)) {
            body[cmd.product === 'dc' ? legacyDataCubeParamName(cmd, key) : key] = value;
        }
    }
    const merged = {
        ...body,
        ...(jsonLayers.params || {}),
        ...(jsonLayers.body || {}),
    };
    if (cmd.product === 'dc') {
        const { exeTaskId, paramMap, ...rest } = merged;
        const normalizedParamMap = (paramMap && typeof paramMap === 'object' && !Array.isArray(paramMap)
            ? { ...paramMap }
            : {});
        const rawCyStoreCode = rest.cy_store_code ?? normalizedParamMap.cy_store_code;
        if (typeof rawCyStoreCode === 'string' && rawCyStoreCode.trim()) {
            rest.cy_store_code = (0, cy7_omshop_store_map_1.resolveCy7OmshopStoreCodeForSql)(rawCyStoreCode);
        }
        applyDataCubeWhereContext(rest, cmd);
        applyScmDataCubeWhereContext(rest, cmd);
        applyCrmDataCubeWhereContext(rest, cmd);
        const missingBizParams = (cmd.parameters || [])
            .filter((parameter) => parameter.required && (DATACUBE_BIZ_PARAM_KEYS.has(parameter.name) || DATACUBE_AUTO_PARAM_KEYS.has(parameter.name)))
            .filter((parameter) => {
            const value = rest[parameter.name] ?? normalizedParamMap[parameter.name];
            return value === undefined || value === null || (value === '' && !canBeEmptyDataCubeBizParam(parameter.name));
        })
            .map((parameter) => parameter.name);
        if (missingBizParams.length > 0) {
            throw new Error(`缺少运行参数 ${missingBizParams.join(', ')}，请先登录或切换到包含对应业务参数的组织。`);
        }
        for (const [key, value] of Object.entries(rest)) {
            normalizedParamMap[key] = value;
        }
        return {
            exeTaskId,
            paramMap: normalizedParamMap,
        };
    }
    return merged;
}
function printBodyBuildDetails(cmd, flags, body, jsonLayers = {}) {
    if (!(0, logger_1.isVerbose)()) {
        return;
    }
    console.error('');
    console.error('┌─── BODY 构建明细 ───');
    console.error('│ 来源: env_mapping (自动填充):');
    for (const [param, envKey] of Object.entries(cmd.env_mapping)) {
        if (param.startsWith('_')) {
            continue;
        }
        const value = (0, env_1.getEnv)(envKey);
        console.error(`│   ${param} = ${value ? JSON.stringify(value) : `(未设置: ${envKey})`}`);
    }
    if (cmd.product === 'dc') {
        const bizParams = (cmd.parameters || []).filter((parameter) => DATACUBE_BIZ_PARAM_KEYS.has(parameter.name));
        if (bizParams.length > 0) {
            console.error('│ 来源: token.json.biz_params (DataCube 业务参数):');
            for (const parameter of bizParams) {
                const value = (0, env_1.getEnv)(parameter.name);
                console.error(`│   ${parameter.name} = ${value ? JSON.stringify(value) : '(未设置)'}`);
            }
        }
    }
    if ((cmd.parameters || []).length > 0) {
        console.error('│ 来源: parameters 默认值:');
        for (const parameter of cmd.parameters || []) {
            if (parameter.default !== undefined) {
                console.error(`│   ${parameter.name} = ${JSON.stringify(parameter.default)} (默认)`);
            }
        }
    }
    const userFlags = Object.entries(flags).filter(([key]) => !isReservedFlag(key));
    if (userFlags.length > 0) {
        console.error('│ 来源: CLI flags (用户传入):');
        for (const [key, value] of userFlags) {
            console.error(`│   ${key} = ${JSON.stringify(value)}`);
        }
    }
    if (jsonLayers.params && Object.keys(jsonLayers.params).length > 0) {
        console.error('│ 来源: --params JSON 合并层:');
        console.error(`│ ${JSON.stringify(jsonLayers.params, null, 2).split('\n').join('\n│ ')}`);
    }
    if (jsonLayers.body && Object.keys(jsonLayers.body).length > 0) {
        console.error('│ 来源: --body JSON 最终覆盖层:');
        console.error(`│ ${JSON.stringify(jsonLayers.body, null, 2).split('\n').join('\n│ ')}`);
    }
    console.error('│ ');
    console.error('│ 最终 body:');
    console.error(`│ ${JSON.stringify(body, null, 2).split('\n').join('\n│ ')}`);
    console.error(`└${'─'.repeat(22)}`);
}
function getFormat(flags) {
    return flags.format || flags.f || 'json';
}
function getAuthMode(product) {
    if (product === 'crm') {
        return 'body.sessionId';
    }
    if (product === 'scm') {
        return 'header.Authorization';
    }
    if (product === 'dc') {
        return 'header.Sly-Token';
    }
    if (product === 'report') {
        return 'url.token (复用CY7)';
    }
    return 'header.Access-Token-Shop';
}
