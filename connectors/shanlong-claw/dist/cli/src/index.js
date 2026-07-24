#!/usr/bin/env node
"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const body_1 = require("./body");
const commands_1 = require("./commands");
const crm_public_key_1 = require("./crm-public-key");
const cy7_omshop_store_map_1 = require("./cy7-omshop-store-map");
const env_1 = require("./env");
const flags_1 = require("./flags");
const logger_1 = require("./logger");
const output_1 = require("./output");
const request_1 = require("./request");
const token_cache_1 = require("./token-cache");
const token_1 = require("./token");
const connector_1 = require("./connector");
const batch_1 = require("./batch");
const cysms_1 = require("./cysms");
const error_audit_1 = require("./error-audit");
const showdoc_1 = require("./showdoc");
const starrocks_1 = require("./starrocks");
const policy_loader_1 = require("./policy-loader");
const policy_evaluator_1 = require("./policy-evaluator");
const policy_core_1 = require("./policy-core");
const policy_help_1 = require("./policy-help");
const CY7_REFERENCE_DATACUBE_BASE_URL = '';
const CY7_REFERENCE_DATACUBE_TASK_IDS = new Set([
    '260622102438001062',
    '260622153850001063',
    '260622164020001064',
    '260623110917001065',
    '260623111154001066',
    '260623134219001067',
]);
function enforceConnectorSecurityLevel() {
    if (process.env.SL_MAX_SECURITY_LEVEL) {
        return;
    }
    try {
        const connectorMode = (0, token_cache_1.loadTokenValue)('connector_mode');
        if (connectorMode
            && typeof connectorMode === 'object'
            && connectorMode.mode === 'workbuddy') {
            process.env.SL_MAX_SECURITY_LEVEL = 'S1';
        }
    }
    catch {
        // token.json 读取失败不影响正常流程
    }
}
function readCliVersion() {
    const packagePaths = [
        path_1.default.resolve(__dirname, '../../../package.json'),
        path_1.default.resolve(__dirname, '../../package.json'),
    ];
    for (const packagePath of packagePaths) {
        if (!fs_1.default.existsSync(packagePath)) {
            continue;
        }
        const packageJson = JSON.parse(fs_1.default.readFileSync(packagePath, 'utf-8'));
        if (packageJson.version) {
            return packageJson.version;
        }
    }
    return 'unknown';
}
function readCode(result) {
    if (!result || typeof result !== 'object') {
        return undefined;
    }
    const record = result;
    return typeof record.code === 'string' || typeof record.code === 'number' ? record.code : undefined;
}
function readMessage(result) {
    if (!result || typeof result !== 'object') {
        return '';
    }
    const record = result;
    const value = [record.message, record.msg].find((item) => typeof item === 'string');
    return typeof value === 'string' ? value : '';
}
function isRawResponse(result) {
    return !!result && typeof result === 'object' && 'raw' in result;
}
function isExplicitFailure(result) {
    if (!result || typeof result !== 'object' || Array.isArray(result)) {
        return false;
    }
    return result.success === false;
}
function hasAuth(auth) {
    return !!auth.sessionToken || Object.keys(auth.headers || {}).length > 0;
}
function readCommandExeTaskId(cmd) {
    if (cmd.action.startsWith('task-')) {
        return cmd.action.slice('task-'.length);
    }
    const parameter = (cmd.parameters || []).find((item) => item.name === 'exeTaskId');
    const value = parameter?.default;
    return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
}
function buildDataCubeWhereCommand(action) {
    if (!/^task-[A-Za-z0-9_-]+$/.test(action)) {
        return null;
    }
    const taskId = action.slice('task-'.length);
    return {
        command: `sl datacube_where ${action}`,
        domain: 'datacube_where',
        action,
        name: 'DataCube where 条件查询',
        description: `DataCube 整段 where 参数模式，运行时动态 Task。默认 exeTaskId=${taskId}，如执行任务 ID 不同请显式传 --exeTaskId。`,
        product: 'dc',
        perspective: 'store',
        category: 'query',
        security_level: 'S1',
        endpoint: {
            method: 'POST',
            path: '/lb/api/dc/dev/external/excByTaskId',
        },
        env_mapping: {
            _baseUrl: 'SL_DC_API_BASE_URL',
            _sessionToken: 'SL_DC_SESSION_TOKEN',
            group_code: 'SL_UNIFIED_G_ID',
            cy_group_code: 'SL_CY7_GROUP_ID',
            shopid: 'cy_omShopCodes',
        },
        parameters: [
            {
                name: 'exeTaskId',
                type: 'string',
                required: true,
                description: 'DataCube 执行任务 ID；动态命令默认使用 task-* 后缀，可通过 --exeTaskId 覆盖。',
                default: taskId,
                example: taskId,
            },
            {
                name: 'title',
                type: 'string',
                required: true,
                description: 'SELECT 后的列清单，会作为 #{title} 传入 DataCube。',
                default: '*',
                example: 'group_code,ts_code',
            },
            {
                name: 'where',
                type: 'string',
                required: false,
                description: '完整 where 条件，不含 where 关键字；前导 and 会被去掉，不传时使用 1=1。',
                default: '1=1',
                example: "used_time >= '2026-07-01'",
            },
            {
                name: 'group_code',
                type: 'string',
                required: false,
                description: '统一集团号，运行时从 SL_UNIFIED_G_ID 自动注入。',
                default: '',
                example: 'G091619',
            },
            {
                name: 'cy_group_code',
                type: 'string',
                required: false,
                description: '餐饮 7 集团号，运行时从 SL_CY7_GROUP_ID 自动注入。',
                default: '',
                example: '301',
            },
            {
                name: 'shopid',
                type: 'string',
                required: false,
                description: '门店编码，可传单个或逗号分隔多个；会按 cy_omShopCodes 白名单过滤。',
                default: '',
                example: 'C146651',
            },
            {
                name: 'store_code',
                type: 'string',
                required: false,
                description: '运行时自动注入，值与过滤后的 shopid 一致。',
                default: '',
                example: 'C146651',
            },
            {
                name: 'limit',
                type: 'string',
                required: false,
                description: '返回条数限制，不传默认 100。',
                default: '100',
                example: '100',
            },
        ],
        source_file: `datacube:${taskId}`,
        source_function: 'externalExcByTaskIdWhereDynamic',
    };
}
function buildScmDataCubeWhereCommand(action) {
    if (!/^task-[A-Za-z0-9_-]+$/.test(action)) {
        return null;
    }
    const taskId = action.slice('task-'.length);
    return {
        command: `sl scm_datacube_where ${action}`,
        domain: 'scm_datacube_where',
        action,
        name: '供应链 DataCube 条件查询',
        description: `供应链 DataCube 整段 where 参数模式。默认 exeTaskId=${taskId}，可通过 --exeTaskId 覆盖。集团和门店范围由当前供应链授权自动注入。`,
        product: 'dc',
        perspective: 'store',
        category: 'query',
        security_level: 'S1',
        endpoint: {
            method: 'POST',
            path: '/lb/api/dc/dev/external/excByTaskId',
        },
        env_mapping: {
            _baseUrl: 'SL_DC_API_BASE_URL',
            _sessionToken: 'SL_DC_SESSION_TOKEN',
        },
        parameters: [
            { name: 'exeTaskId', type: 'string', required: true, description: 'DataCube 执行任务 ID。默认使用 task-* 后缀，可通过 --exeTaskId 覆盖。', default: taskId, example: taskId },
            { name: 'title', type: 'string', required: true, description: 'SELECT 后的列清单，会作为 #{title} 传入 DataCube。', default: '*', example: 'group_code,organ_code' },
            { name: 'where', type: 'string', required: false, description: '完整 where 条件，不含 where 关键字；不传时使用 1=1。group_code 和 store_code 由 CLI 自动注入。', default: '1=1', example: "biz_date >= '2026-07-01'" },
            { name: 'group_code', type: 'string', required: false, description: '运行时从 SL_SCM_GROUP_ID 自动注入，不能由调用方覆盖。', default: '' },
            { name: 'shopid', type: 'string', required: false, description: '可选门店编码列表；仅允许选择 scm_omShopCodes 中已授权的门店，最终注入为 store_code。', default: '', example: "'21142','19535'" },
            { name: 'store_code', type: 'string', required: false, description: '运行时从 scm_omShopCodes 自动注入，不能由调用方覆盖。', default: '' },
            { name: 'limit', type: 'string', required: false, description: '返回条数限制，不传默认 100。', default: '100', example: '100' },
        ],
        source_file: `datacube:${taskId}`,
        source_function: 'externalExcByTaskIdScmWhereDynamic',
    };
}
function buildCrmDataCubeWhereCommand(action) {
    if (!/^task-[A-Za-z0-9_-]+$/.test(action)) {
        return null;
    }
    const taskId = action.slice('task-'.length);
    return {
        command: `sl crm_datacube_where ${action}`,
        domain: 'crm_datacube_where',
        action,
        name: 'CRM DataCube 条件查询',
        description: `CRM DataCube 整段 where 参数模式。默认 exeTaskId=${taskId}，可通过 --exeTaskId 覆盖。CRM 集团和门店范围由当前授权自动注入。`,
        product: 'dc',
        perspective: 'store',
        category: 'query',
        security_level: 'S1',
        endpoint: {
            method: 'POST',
            path: '/lb/api/dc/dev/external/excByTaskId',
        },
        env_mapping: {
            _baseUrl: 'SL_DC_API_BASE_URL',
            _sessionToken: 'SL_DC_SESSION_TOKEN',
            crm_group_code: 'SL_CRM_GROUP_ID',
            shopid: 'crm_omShopCodes',
        },
        parameters: [
            { name: 'exeTaskId', type: 'string', required: true, description: 'DataCube 执行任务 ID。默认使用 task-* 后缀，可通过 --exeTaskId 覆盖。', default: taskId, example: taskId },
            { name: 'title', type: 'string', required: true, description: 'SELECT 后的列清单，会作为 #{title} 传入 DataCube。', default: '*', example: 'store_name,consume_amount' },
            { name: 'where', type: 'string', required: false, description: '完整 where 条件，不含 where 关键字；不传时使用 1=1。crm_group_code 和 store_code 由 CLI 自动注入。', default: '1=1', example: "consume_time >= '2026-07-01'" },
            { name: 'crm_group_code', type: 'string', required: false, description: '运行时从 SL_CRM_GROUP_ID 自动注入，不能由调用方覆盖。', default: '' },
            { name: 'shopid', type: 'string', required: false, description: '可选门店编码列表；仅允许选择 crm_omShopCodes 中已授权的门店，最终同时注入为 shopid / store_code。', default: '', example: 'C146651' },
            { name: 'store_code', type: 'string', required: false, description: '运行时从过滤后的 shopid 自动注入，不能由调用方覆盖。', default: '' },
            { name: 'limit', type: 'string', required: false, description: '返回条数限制，不传默认 100。', default: '100', example: '100' },
        ],
        source_file: `datacube:${taskId}`,
        source_function: 'externalExcByTaskIdCrmWhereDynamic',
    };
}
function resolveDatacubeBaseUrlForCommand(cmd, resolved) {
    const taskId = readCommandExeTaskId(cmd);
    if (cmd.product === 'dc' && CY7_REFERENCE_DATACUBE_TASK_IDS.has(taskId)) {
        return {
            url: (0, env_1.getEnv)('SL_DC_CY7_TASK_API_BASE_URL', CY7_REFERENCE_DATACUBE_BASE_URL),
            viaGateway: false,
            routedToReference: true,
        };
    }
    return { ...resolved, routedToReference: false };
}
function isCrmPublicKeyFailure(result) {
    const message = readMessage(result);
    return /解密失败|decrypt|public\s*key|公钥|rsa|pem|asn1/i.test(message);
}
function isCrmPublicKeyError(error) {
    const message = error instanceof Error ? error.message : String(error);
    return /decrypt|public key|pem|rsa|asn1/i.test(message);
}
function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function rejectUsageDisplay(command) {
    console.error(`CLI usage display is disabled: ${command}`);
    process.exit(1);
}
async function ensureTokensIfApiKeyPresent() {
    const apiKey = (process.env.SL_API_KEY || '').trim();
    if (!apiKey)
        return;
    const store = (0, token_cache_1.loadTokenStore)();
    const hasAnyToken = ['wuuxiangCyToken', 'crm8Token', 'fxscmToken', 'sly_remote_token']
        .some((key) => typeof store[key] === 'string' && store[key].length > 0);
    if (hasAnyToken)
        return;
    console.error('→ 首次运行，正在自动初始化 Token...');
    try {
        await (0, token_1.refreshRequestAuth)('cy7');
        (0, token_1.loadBizParamsToEnv)();
        console.error('✓ Token 初始化完成');
    }
    catch {
        console.error('⚠ Token 自动初始化失败，部分命令可能不可用');
    }
}
function enforceCorePolicy(args, policyContext) {
    if (!policyContext.enabled) {
        return false;
    }
    const route = (0, policy_core_1.resolveCoreRoute)(args);
    if (route.kind === 'help') {
        (0, policy_help_1.printPolicyCoreHelp)(policyContext, route.family, route.commandId);
        return true;
    }
    if (route.kind === 'unknown') {
        (0, policy_evaluator_1.denyPolicyCommand)(`${route.family}.unknown`);
    }
    if (route.kind === 'command'
        && !(0, policy_evaluator_1.isCoreCommandAllowed)(policyContext.policy, route.commandId)) {
        (0, policy_evaluator_1.denyPolicyCommand)(route.commandId);
    }
    return false;
}
function rejectUnknownDomain(domain, policyContext) {
    if (policyContext.enabled) {
        console.error(`未知域: ${domain}`);
        const allowed = (0, policy_help_1.getPolicyAllowedDomains)(policyContext);
        if (allowed.length > 0 && policyContext.policy.help.enabled) {
            console.error('运行 sl domains 查看允许的域');
        }
        process.exit(1);
    }
    console.error(`未知域: ${domain}`);
    console.error('运行 sl domains 查看所有可用域');
    process.exit(1);
}
function rejectUnknownAction(domain, action, policyContext) {
    if (policyContext.enabled) {
        console.error(`未知命令: sl ${domain} ${action}`);
        if (policyContext.policy.help.enabled) {
            console.error(`运行 sl ${domain} --help 查看可用命令`);
        }
        process.exit(1);
    }
    console.error(`未知命令: sl ${domain} ${action}`);
    console.error(`运行 sl ${domain} --help 查看可用命令`);
    process.exit(1);
}
function parseJsonObjectFlag(flags, key) {
    const raw = flags[key];
    if (!raw) {
        return {};
    }
    try {
        const parsed = JSON.parse(raw);
        if (!isPlainObject(parsed)) {
            throw new Error(`--${key} 必须是 JSON 对象`);
        }
        return parsed;
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`✗ 解析 --${key} 失败: ${message}`);
        console.error(`  原始内容: ${raw}`);
        process.exit(1);
    }
}
function parseHeaderOverrides(flags) {
    const parsed = parseJsonObjectFlag(flags, 'header');
    const headerOverrides = {};
    for (const [key, value] of Object.entries(parsed)) {
        if (typeof value === 'string' || typeof value === 'number') {
            headerOverrides[key] = value;
            continue;
        }
        if (typeof value === 'boolean') {
            headerOverrides[key] = value ? 'true' : 'false';
            continue;
        }
        console.error(`✗ --header.${key} 必须是 string / number / boolean`);
        process.exit(1);
    }
    return headerOverrides;
}
/**
 * CRM 数据概览页全部命令共用前端枚举：1=按天，2=按月。
 * 只在命令注册表明确声明 dateType 参数时生效，避免影响其它命令域
 * （例如 DataCube 的 dateType 具有不同语义）。
 */
const CRM_DATA_OVERVIEW_DATETIME_PARAMETERS = new Set([
    'beginDate',
    'endDate',
    'preBeginDate',
    'preEndDate',
]);
const GENERAL_CONSUME_BASE_INFO_DATETIME_PARAMETERS = [
    'beginDate',
    'endDate',
    'preBeginDate',
    'preEndDate',
];
function getEffectiveCommandParameter(name, flags, jsonParams, jsonBody) {
    return jsonBody[name] ?? jsonParams[name] ?? flags[name];
}
function isValidDateTime(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2}) ([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$/.exec(value);
    if (!match) {
        return false;
    }
    const [, year, month, day, hour, minute, second] = match;
    const parsed = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute), Number(second)));
    return parsed.getUTCFullYear() === Number(year)
        && parsed.getUTCMonth() === Number(month) - 1
        && parsed.getUTCDate() === Number(day)
        && parsed.getUTCHours() === Number(hour)
        && parsed.getUTCMinutes() === Number(minute)
        && parsed.getUTCSeconds() === Number(second);
}
function getCrmDateTimeParameters(cmd) {
    if (cmd.domain === 'crm_data_overview') {
        return (cmd.parameters || [])
            .filter((parameter) => CRM_DATA_OVERVIEW_DATETIME_PARAMETERS.has(parameter.name))
            .map((parameter) => parameter.name);
    }
    if (cmd.domain === 'general' && cmd.action === 'get-consume-base-info') {
        return GENERAL_CONSUME_BASE_INFO_DATETIME_PARAMETERS;
    }
    return [];
}
function validateCrmDateParameters(cmd, flags, jsonParams, jsonBody) {
    const dateTypeParameter = (cmd.parameters || []).find((parameter) => parameter.name === 'dateType');
    const requiresDateTypeValidation = (cmd.domain === 'crm_data_overview' && !!dateTypeParameter)
        || (cmd.domain === 'general' && cmd.action === 'get-consume-base-info');
    if (requiresDateTypeValidation) {
        const value = getEffectiveCommandParameter('dateType', flags, jsonParams, jsonBody)
            ?? dateTypeParameter?.default;
        if (value === 1 || value === 2 || value === '1' || value === '2') {
            // continue validating datetime parameters below
        }
        else {
            console.error(`✗ sl ${cmd.domain} ${cmd.action}：--dateType 仅支持 1（按天）或 2（按月），收到: ${String(value)}`);
            process.exit(1);
        }
    }
    for (const parameterName of getCrmDateTimeParameters(cmd)) {
        const parameter = (cmd.parameters || []).find((item) => item.name === parameterName);
        const dateTime = getEffectiveCommandParameter(parameterName, flags, jsonParams, jsonBody);
        if (dateTime === undefined && !parameter?.required) {
            continue;
        }
        if (typeof dateTime !== 'string' || !isValidDateTime(dateTime)) {
            console.error(`✗ sl ${cmd.domain} ${cmd.action}：--${parameterName} 必须是有效的 yyyy-MM-dd HH:mm:ss，收到: ${String(dateTime)}`);
            process.exit(1);
        }
    }
}
async function executeRequestWithCrmKeyRecovery(baseUrl, endpoint, auth, body, product, headerOverrides = {}, options = {}) {
    const reqOpts = {
        crmPublicKeyOverride: options.crmPublicKeyOverride,
        rawFormBody: options.rawFormBody ?? null,
    };
    try {
        return await (0, request_1.makeRequest)(baseUrl, endpoint, auth.sessionToken, body, product, { ...(auth.headers || {}), ...headerOverrides }, reqOpts);
    }
    catch (error) {
        if (product !== 'crm' || !options.allowCrmKeyRefresh || !isCrmPublicKeyError(error)) {
            throw error;
        }
        console.error('⚠ CRM 公钥本地加密失败，尝试自动刷新...');
        const freshKey = await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(baseUrl, auth, { allowLoginKeyFallback: true });
        if (!freshKey) {
            throw error;
        }
        return (0, request_1.makeRequest)(baseUrl, endpoint, auth.sessionToken, body, product, { ...(auth.headers || {}), ...headerOverrides }, { ...reqOpts, crmPublicKeyOverride: freshKey });
    }
}
async function fetchCrmPublicKey() {
    const product = 'crm';
    const resolved = (0, env_1.resolveBaseUrl)(product, 'SL_CRM_API_BASE_URL');
    if (!resolved.url) {
        console.error('请设置 SL_CRM_API_BASE_URL 或 SL_GATEWAY_HOST');
        process.exit(1);
    }
    const finalKey = await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(resolved.url, (0, token_1.getRequestAuth)(product), {
        verbose: true,
        allowLoginKeyFallback: true,
    });
    if (!finalKey) {
        console.error('✗ 未获取到任何公钥');
        process.exit(1);
    }
    console.log('公钥内容:');
    console.log(finalKey);
    console.log('');
    console.log('也可添加到 .env:');
    console.log(`export SL_CRM_PUBLIC_KEY="${finalKey}"`);
}
function readStoreIdNameList() {
    const raw = (0, env_1.getEnv)('omShopCodeOrgNameMap');
    if (!raw) {
        return [];
    }
    try {
        const parsed = JSON.parse(raw);
        if (!isPlainObject(parsed)) {
            return [];
        }
        return Object.entries(parsed)
            .filter(([omShopCode, orgName]) => omShopCode && typeof orgName === 'string')
            .map(([omShopCode, orgName]) => ({
            omShopCode,
            orgName: orgName,
        }));
    }
    catch {
        return [];
    }
}
function normalizeKeyword(value) {
    return value.trim().toLowerCase();
}
function readKeywordArg(flags, positional = '') {
    if (Object.prototype.hasOwnProperty.call(flags, 'name')) {
        return flags.name;
    }
    if (Object.prototype.hasOwnProperty.call(flags, 'keyword')) {
        return flags.keyword;
    }
    return positional;
}
function readPositionalArg(args) {
    for (let index = 0; index < args.length; index += 1) {
        const arg = args[index];
        if (arg.startsWith('--')) {
            const eqIndex = arg.indexOf('=');
            if (eqIndex < 0 && args[index + 1] !== undefined && !args[index + 1].startsWith('--')) {
                index += 1;
            }
            continue;
        }
        if (arg.startsWith('-')) {
            const eqIndex = arg.indexOf('=');
            if (eqIndex < 0 && args[index + 1] !== undefined && !args[index + 1].startsWith('-')) {
                index += 1;
            }
            continue;
        }
        return arg;
    }
    return '';
}
function isEmptyStoreKeyword(keyword) {
    return !keyword || keyword === 'null';
}
function findCy7OmshopStoreRows(keyword) {
    return (0, cy7_omshop_store_map_1.findCy7OmshopStoresByKeyword)(keyword).map((item) => ({
        type: 'cy7',
        omShopCode: item.omShopCode,
        orgName: item.orgName,
        source: cy7_omshop_store_map_1.CY7_OMSHOP_STORE_MAP_FILE,
    }));
}
async function executeCy7OmshopCommand(args) {
    if (args[0] !== 'cy7-omshop' && args[0] !== 'cy7-omshop-store') {
        return false;
    }
    if (args[1] !== 'find' && args[1] !== 'lookup') {
        console.log('用法:');
        console.log('  sl cy7-omshop find --name <门店关键词> [--format json|table|csv]');
        console.log('  sl cy7-omshop lookup --keyword <门店关键词> [--format json|table|csv]');
        return true;
    }
    const flags = (0, flags_1.parseFlags)(args.slice(2));
    const positional = readPositionalArg(args.slice(2));
    const keyword = normalizeKeyword(readKeywordArg(flags, positional));
    const rows = findCy7OmshopStoreRows(keyword);
    if (rows.length === 0) {
        console.error(`✗ 当前工作区 ${cy7_omshop_store_map_1.CY7_OMSHOP_STORE_MAP_FILE} 未匹配到门店，请先执行 sl token refresh dc 生成缓存，或换更准确的关键词`);
        process.exit(1);
    }
    (0, output_1.formatOutput)(rows, (0, body_1.getFormat)(flags));
    return true;
}
async function executeStoreCommand(args) {
    if (args[0] !== 'store') {
        return false;
    }
    if (args[1] !== 'find' && args[1] !== 'lookup') {
        console.log('用法:');
        console.log('  sl store find --type crm|cy7 --name <门店关键词> [--format json|table|csv]');
        console.log('  sl store lookup --type crm|cy7 --keyword <门店关键词>');
        return true;
    }
    const flags = (0, flags_1.parseFlags)(args.slice(2));
    const type = (flags.type || flags.product || '').toLowerCase();
    if (type !== 'crm' && type !== 'cy7') {
        console.error('✗ 请通过 --type crm|cy7 指定查询 CRM 还是 CY7 门店');
        process.exit(1);
    }
    const positional = readPositionalArg(args.slice(2));
    const keyword = normalizeKeyword(readKeywordArg(flags, positional));
    const stores = readStoreIdNameList();
    if (stores.length === 0) {
        console.error('✗ token.json.biz_params 中没有 omShopCode 门店清单，请先执行 sl token refresh dc');
        process.exit(1);
    }
    const rows = stores
        .filter((item) => (isEmptyStoreKeyword(keyword)
        || item.orgName.toLowerCase().includes(keyword)
        || item.omShopCode.toLowerCase().includes(keyword)))
        .map((item) => ({
        type,
        omShopCode: item.omShopCode,
        orgName: item.orgName,
    }));
    (0, output_1.formatOutput)(rows, (0, body_1.getFormat)(flags));
    return true;
}
async function executeTokenCommand(args) {
    if (args[0] !== 'token') {
        return false;
    }
    if (args[1] === 'refresh-crm-gc-id') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const explicitGroupId = flags['group-id'] || flags['crm-group-id'] || '';
        if (explicitGroupId === 'true') {
            console.error('✗ --group-id 缺少参数值');
            process.exit(1);
        }
        console.error('→ 正在按最终 SL_CRM_GROUP_ID 刷新 SL_CRM_GC_ID...');
        const result = await (0, token_1.refreshCrmGcId)(explicitGroupId);
        console.log(`✓ 已写入 token.json: SL_CRM_GROUP_ID=${result.crmGroupId}, SL_CRM_GC_ID=${result.crmGcId}`);
        return true;
    }
    if (args[1] === 'refresh') {
        const product = args.slice(2).find((a) => !a.startsWith('-')) || 'all';
        const products = product === 'all' ? ['cy7', 'crm', 'scm', 'dc'] : [product];
        for (const p of products) {
            console.error(`→ 正在刷新 ${p.toUpperCase()} Token (API Key 或 SLY → switchToken)...`);
            const auth = await (0, token_1.refreshRequestAuth)(p);
            if (auth) {
                console.error(`✓ ${p.toUpperCase()} Token 刷新成功`);
            }
            else {
                console.error(`✗ ${p.toUpperCase()} Token 刷新失败，请检查 API Key 或 SLY 账号配置`);
            }
        }
        await (0, token_1.syncCySAfterSlCredentialPersist)();
        return true;
    }
    if (args[1] === 'show') {
        console.log(JSON.stringify((0, token_cache_1.loadTokenStore)(), null, 2));
        return true;
    }
    if (args[1] === 'clear') {
        (0, token_cache_1.clearTokenCache)();
        console.log('Token 缓存已清除');
        return true;
    }
    console.log('用法:');
    console.log('  sl token refresh [cy7|crm|scm|dc|all]  刷新 Token');
    console.log('  sl token refresh-crm-gc-id [--group-id <集团号>]  按最终 CRM Group 刷新 GC ID');
    console.log('  sl token show                       查看缓存的 Token');
    console.log('  sl token clear                      清除 Token 缓存');
    return true;
}
async function executeViewCommand(args) {
    if (args[0] !== 'view') {
        return false;
    }
    console.error('✗ sl view 相关指令已禁用，禁止使用视角切换功能');
    process.exit(1);
}
async function main() {
    const rawArgs = process.argv.slice(2);
    (0, error_audit_1.installErrorAudit)({ source: 'sl-cli', args: rawArgs, version: readCliVersion() });
    if (rawArgs.includes('--verbose') || rawArgs.includes('-v')) {
        (0, logger_1.setVerbose)(true);
    }
    (0, env_1.loadEnvFiles)((0, env_1.extractEnvPath)(rawArgs));
    const args = (0, env_1.stripEnvPathFromArgs)(rawArgs);
    if (args[0] === '--version' || args[0] === '-v') {
        console.log(readCliVersion());
        return;
    }
    const policyContext = (0, policy_loader_1.loadPolicyContext)();
    if (enforceCorePolicy(args, policyContext)) {
        return;
    }
    if (await (0, connector_1.executeConnectorCommand)(args)) {
        return;
    }
    await ensureTokensIfApiKeyPresent();
    (0, token_1.loadBizParamsToEnv)();
    enforceConnectorSecurityLevel();
    if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
        if (policyContext.enabled) {
            (0, policy_help_1.printPolicyRootHelp)(policyContext);
            return;
        }
        rejectUsageDisplay(args.length === 0 ? 'sl' : `sl ${args[0]}`);
    }
    if (await (0, batch_1.executeBatchCommand)(args)) {
        return;
    }
    if (await executeTokenCommand(args)) {
        return;
    }
    if (await executeViewCommand(args)) {
        return;
    }
    if (await executeCy7OmshopCommand(args)) {
        return;
    }
    if (await executeStoreCommand(args)) {
        return;
    }
    if (await (0, cysms_1.executeCysmsCommand)(args)) {
        return;
    }
    if (await (0, showdoc_1.executeShowdocCommand)(args)) {
        return;
    }
    if (await (0, starrocks_1.executeStarrocksCommand)(args)) {
        return;
    }
    if (args[0] === 'crm-key') {
        await fetchCrmPublicKey();
        return;
    }
    if (args[0] === 'domains') {
        if (policyContext.enabled) {
            if (!policyContext.policy.help.enabled) {
                (0, policy_help_1.printPolicyHelpDisabled)();
            }
            (0, policy_help_1.printPolicyDomains)(policyContext);
            return;
        }
        rejectUsageDisplay('sl domains');
    }
    const domain = args[0];
    const mergedDomainData = await (0, commands_1.loadCommandsMerged)(domain);
    const domainData = mergedDomainData && policyContext.enabled
        ? (0, policy_evaluator_1.filterDomainFile)(policyContext.evaluator, mergedDomainData)
        : mergedDomainData;
    if (!domainData || (policyContext.enabled && domainData.commands.length === 0)) {
        rejectUnknownDomain(domain, policyContext);
    }
    if (args.length === 1 || args[1] === '--help' || args[1] === '-h') {
        if (policyContext.enabled) {
            (0, policy_help_1.printPolicyDomainHelp)(policyContext, domain, domainData);
            return;
        }
        rejectUsageDisplay(args.length === 1 ? `sl ${domain}` : `sl ${domain} ${args[1]}`);
    }
    const action = args[1];
    const flags = (0, flags_1.parseFlags)(args.slice(2));
    const jsonParams = parseJsonObjectFlag(flags, 'params');
    const jsonBody = parseJsonObjectFlag(flags, 'body');
    const headerOverrides = parseHeaderOverrides(flags);
    let cmd = domainData.commands.find((item) => item.action === action)
        || (domain === 'datacube_where' ? buildDataCubeWhereCommand(action) : null)
        || (domain === 'scm_datacube_where' ? buildScmDataCubeWhereCommand(action) : null)
        || (domain === 'crm_datacube_where' ? buildCrmDataCubeWhereCommand(action) : null);
    if (!cmd && policyContext.enabled && mergedDomainData) {
        const catalogCmd = mergedDomainData.commands.find((item) => item.action === action);
        if (catalogCmd && !(0, policy_evaluator_1.isBusinessCommandAllowed)(policyContext.evaluator, catalogCmd)) {
            (0, policy_evaluator_1.denyPolicyCommand)((0, policy_evaluator_1.getBusinessCommandId)(catalogCmd));
        }
    }
    if (!cmd) {
        rejectUnknownAction(domain, action, policyContext);
    }
    if (policyContext.enabled && !(0, policy_evaluator_1.isBusinessCommandAllowed)(policyContext.evaluator, cmd)) {
        (0, policy_evaluator_1.denyPolicyCommand)((0, policy_evaluator_1.getBusinessCommandId)(cmd));
    }
    if (flags.help === 'true' || flags.h === 'true') {
        if (policyContext.enabled) {
            (0, policy_help_1.printPolicyCommandHelp)(policyContext, domain, cmd);
            return;
        }
        rejectUsageDisplay(`sl ${domain} ${action} ${flags.help === 'true' ? '--help' : '-h'}`);
    }
    validateCrmDateParameters(cmd, flags, jsonParams, jsonBody);
    // S1 隔离：环境变量 SL_MAX_SECURITY_LEVEL 限制可执行的最高安全级别
    const maxSecurityLevel = (0, env_1.getEnv)('SL_MAX_SECURITY_LEVEL', '');
    if (maxSecurityLevel) {
        const levelOrder = { S1: 1, S2: 2, S3: 3, S4: 4 };
        const cmdLevel = cmd.security_level || 'S1';
        const maxAllowed = levelOrder[maxSecurityLevel] || 4;
        const cmdLevelNum = levelOrder[cmdLevel] || 1;
        if (cmdLevelNum > maxAllowed) {
            console.error(`🚫 安全级别拦截: 命令 ${domain} ${action} 为 ${cmdLevel}，当前环境限制最高 ${maxSecurityLevel}`);
            console.error(`   该命令涉及${cmdLevel === 'S2' ? '可控写入' : cmdLevel === 'S3' ? '风险操作' : '高危破坏'}，在当前环境不允许执行`);
            console.error(`   如需执行，请切换到全量环境（移除 SL_MAX_SECURITY_LEVEL 配置）`);
            process.exit(1);
        }
    }
    const product = cmd.product || 'cy7';
    let resolved = (0, env_1.resolveBaseUrl)(product, cmd.env_mapping._baseUrl);
    resolved = resolveDatacubeBaseUrlForCommand(cmd, resolved);
    if (!resolved.url) {
        console.error(`请设置环境变量 ${cmd.env_mapping._baseUrl} 或 SL_GATEWAY_HOST`);
        console.error('参考: generated/cli/env-template.sh');
        process.exit(1);
    }
    const currentEnv = (0, env_1.getEnv)('SL_ENV', 'unknown');
    const envLabel = currentEnv === 'prod' ? '正式' : currentEnv === 'test' ? '测试' : currentEnv;
    if (resolved.viaGateway) {
        console.error(`📡 [${envLabel}] ${product.toUpperCase()} 通过代理网关`);
    }
    else if (resolved.routedToReference) {
        console.error(`DC CY7 reference direct: ${resolved.url}`);
    }
    else {
        console.error(`🔗 [${envLabel}] ${product.toUpperCase()} 直连`);
    }
    let auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, (0, token_1.getRequestAuth)(product));
    if (!hasAuth(auth)) {
        console.error(`⚠ 未找到 ${product.toUpperCase()} Token，尝试自动换取...`);
        auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, await (0, token_1.refreshRequestAuth)(product) || { sessionToken: null });
        if (!hasAuth(auth)) {
            console.error(`请设置环境变量 ${cmd.env_mapping._sessionToken}`);
            process.exit(1);
        }
        await (0, token_1.syncCySAfterSlCredentialPersist)();
    }
    if (product === 'report') {
        const reportSession = (0, token_cache_1.loadTokenValue)('report_session_token');
        if (!reportSession) {
            console.error('→ 报表中心会话未建立，自动执行三步登录...');
            const refreshedAuth = await (0, token_1.refreshRequestAuth)(product);
            if (refreshedAuth && hasAuth(refreshedAuth)) {
                auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, refreshedAuth);
                await (0, token_1.syncCySAfterSlCredentialPersist)();
            }
            else {
                console.error('⚠ 报表中心三步登录失败，将使用 subToken 直连');
            }
        }
    }
    if (product === 'crm') {
        const cached = (0, token_cache_1.loadTokenCache)();
        if (!cached.crm_public_key?.token && !(0, env_1.getEnv)('SL_CRM_PUBLIC_KEY')) {
            console.error('→ CRM 公钥未缓存，自动获取中...');
            try {
                await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(resolved.url, auth, { allowLoginKeyFallback: true });
            }
            catch {
                console.error('⚠ CRM 公钥自动获取失败，请求可能因加密缺失而被拒绝');
            }
        }
    }
    const bodyFilePath = flags.bodyFile || flags['body-file'];
    let rawFormBody = null;
    if (bodyFilePath) {
        const abs = path_1.default.isAbsolute(bodyFilePath) ? bodyFilePath : path_1.default.resolve(process.cwd(), bodyFilePath);
        if (!fs_1.default.existsSync(abs)) {
            console.error(`✗ --body-file 文件不存在: ${abs}`);
            process.exit(1);
        }
        rawFormBody = fs_1.default.readFileSync(abs, 'utf-8');
    }
    if (cmd.endpoint.body_format === 'form') {
        if (!rawFormBody || !rawFormBody.trim()) {
            console.error('✗ 本命令为 application/x-www-form-urlencoded，请使用 --body-file <path> 传入与浏览器/curl 一致的原始 body（单行或整段文本，勿再 JSON 包装）');
            process.exit(1);
        }
    }
    else if (rawFormBody) {
        console.error('✗ --body-file 仅用于 sl scm_analysis query-form；JSON 接口请用 --body');
        process.exit(1);
    }
    const body = rawFormBody ? {} : (0, body_1.buildBody)(cmd, flags, { params: jsonParams, body: jsonBody });
    const displayUrl = resolved.url.replace(/\/+$/, '') + (cmd.endpoint.path.startsWith('/') ? '' : '/') + cmd.endpoint.path;
    console.error(`→ ${cmd.endpoint.method} ${displayUrl}`);
    console.error(`  产品: ${product} | 视角: ${cmd.perspective} | 认证: ${(0, body_1.getAuthMode)(product)}`);
    if (rawFormBody) {
        if ((0, logger_1.isVerbose)()) {
            const preview = rawFormBody.length > 2000 ? `${rawFormBody.slice(0, 2000)}…` : rawFormBody;
            console.error('┌─── FORM BODY (--body-file) ───');
            console.error(preview);
            console.error('└──────────────────────────────');
        }
    }
    else {
        (0, body_1.printBodyBuildDetails)(cmd, flags, body, { params: jsonParams, body: jsonBody });
    }
    if ((0, logger_1.isVerbose)() && Object.keys(headerOverrides).length > 0) {
        console.error('┌─── HEADER 覆盖层 (--header) ───');
        console.error(JSON.stringify(headerOverrides, null, 2));
        console.error('└──────────────────────────────');
    }
    console.error('');
    try {
        let result = await executeRequestWithCrmKeyRecovery(resolved.url, cmd.endpoint, auth, body, product, headerOverrides, { allowCrmKeyRefresh: true, rawFormBody });
        const tokenExpired = (0, token_1.isTokenExpiredResponse)(result, product);
        if (tokenExpired || isExplicitFailure(result)) {
            console.error(tokenExpired
                ? '⚠ Token 已过期，尝试自动刷新...'
                : '⚠ 请求返回 success=false，尝试自动刷新 Token 后重试一次...');
            const refreshedAuth = await (0, token_1.refreshRequestAuth)(product);
            if (refreshedAuth && hasAuth(refreshedAuth)) {
                auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, refreshedAuth);
                result = await executeRequestWithCrmKeyRecovery(resolved.url, cmd.endpoint, auth, body, product, headerOverrides, { allowCrmKeyRefresh: true, rawFormBody });
                await (0, token_1.syncCySAfterSlCredentialPersist)();
            }
            else {
                console.error('Token 刷新失败，返回原始结果');
            }
        }
        if (product === 'crm' && isCrmPublicKeyFailure(result)) {
            console.error('⚠ CRM 公钥可能已失效，尝试自动刷新...');
            const freshKey = await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(resolved.url, auth, { allowLoginKeyFallback: true });
            if (freshKey) {
                result = await executeRequestWithCrmKeyRecovery(resolved.url, cmd.endpoint, auth, body, product, headerOverrides, { crmPublicKeyOverride: freshKey, allowCrmKeyRefresh: false, rawFormBody });
            }
            else {
                console.error('CRM 公钥刷新失败，返回原始结果');
            }
        }
        if (isRawResponse(result)) {
            if (product === 'report' && /系统异常|alert|302|login/i.test(result.raw)) {
                console.error('⚠ 报表中心会话失效，自动刷新三步登录...');
                const refreshedAuth = await (0, token_1.refreshRequestAuth)(product);
                if (refreshedAuth && hasAuth(refreshedAuth)) {
                    auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, refreshedAuth);
                    result = await executeRequestWithCrmKeyRecovery(resolved.url, cmd.endpoint, auth, body, product, headerOverrides, {});
                    await (0, token_1.syncCySAfterSlCredentialPersist)();
                }
            }
            if (isRawResponse(result)) {
                console.error(`⚠ 响应非 JSON: ${result.raw.substring(0, 200)}`);
                if (!(0, logger_1.isVerbose)()) {
                    console.error('  提示: 添加 --verbose 查看完整请求详情');
                }
                process.exit(1);
            }
        }
        const code = readCode(result);
        if (code !== undefined && code !== '0' && code !== '200' && code !== 0 && code !== 200) {
            console.error(`⚠ 业务错误: code=${code}, message=${readMessage(result)}`);
            if (!(0, logger_1.isVerbose)()) {
                console.error('  提示: 添加 --verbose 查看完整请求/响应详情');
            }
        }
        (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags), cmd);
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`请求失败: ${message}`);
        if (!(0, logger_1.isVerbose)()) {
            console.error('  提示: 添加 --verbose 查看完整请求详情');
        }
        process.exit(1);
    }
}
main().catch((error) => {
    console.error(error);
    process.exit(1);
});
