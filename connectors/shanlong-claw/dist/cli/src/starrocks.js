"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeStarrocksCommand = executeStarrocksCommand;
const env_1 = require("./env");
const body_1 = require("./body");
const logger_1 = require("./logger");
const output_1 = require("./output");
const flags_1 = require("./flags");
const token_cache_1 = require("./token-cache");
const MCP_PROTOCOL_VERSION = '2025-06-18';
const MCP_ACCEPT = 'application/json, text/event-stream';
let requestId = 0;
let sessionId = null;
let headerOverrides = {};
function nextId() {
    requestId += 1;
    return String(requestId);
}
function readStarrocksUrl() {
    const raw = ((0, env_1.getEnv)('MCP_STARROCKS_URL') || (0, env_1.getEnv)('MCP_URL')).trim();
    if (!raw) {
        console.error('✗ 请在 .env 中设置 MCP_STARROCKS_URL');
        process.exit(1);
    }
    return raw;
}
function assertReadOnlyQuery(query) {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
        console.error('✗ 请通过 --query 传入 SQL');
        process.exit(1);
    }
    if (!normalized.startsWith('select') && !normalized.startsWith('with')) {
        console.error('✗ starrocks read-query 只允许 SELECT 或 WITH 开头的只读查询');
        process.exit(1);
    }
    if (/\b(insert|update|delete|drop|alter|create|truncate)\b/.test(normalized)) {
        console.error('✗ 检测到非只读 SQL 关键字，已拒绝执行');
        process.exit(1);
    }
}
function resolveSqlPlaceholders(query) {
    return query.replace(/#\{([A-Za-z0-9_]+)\}/g, (match, key) => {
        const value = (0, env_1.getEnv)(key);
        return value ? value : match;
    });
}
function buildHeaders() {
    const groupCode = (0, env_1.getEnv)('SL_UNIFIED_G_ID').trim();
    const accountId = ((0, env_1.getEnv)('SL_USER_ID') || (0, env_1.getEnv)('SL_ACCOUNT_ID') || String((0, token_cache_1.loadTokenValue)('user_id') || '')).trim();
    const corpId = (0, env_1.getEnv)('SL_SLY_CORP_ID').trim();
    const headers = {
        'Content-Type': 'application/json',
        Accept: MCP_ACCEPT,
        'mcp-protocol-version': MCP_PROTOCOL_VERSION,
        'LJC_ACCESS_TOKEN': (0, env_1.getEnv)('SL_DC_MCP_ACCESS_ID') || (0, env_1.getEnv)('SL_DC_LJC_ACCESS_TOKEN'),
    };
    if (sessionId) {
        headers['mcp-session-id'] = sessionId;
    }
    Object.assign(headers, headerOverrides);
    if (groupCode) {
        headers.group_code = groupCode;
    }
    if (accountId) {
        headers.sly_accountId = accountId;
    }
    if (corpId) {
        headers.sly_corpId = corpId;
    }
    const apiKey = (0, env_1.getEnv)('SL_API_KEY').trim();
    if (apiKey) {
        headers.sly_key = apiKey;
    }
    return headers;
}
function parseHeaderOverrides(raw) {
    if (!raw) {
        return {};
    }
    let parsed;
    try {
        parsed = JSON.parse(raw);
    }
    catch {
        console.error('✗ --header 必须是 JSON 对象');
        process.exit(1);
    }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        console.error('✗ --header 必须是 JSON 对象');
        process.exit(1);
    }
    const result = {};
    for (const [key, value] of Object.entries(parsed)) {
        if (typeof value === 'string' || typeof value === 'number') {
            result[key] = String(value);
            continue;
        }
        if (typeof value === 'boolean') {
            result[key] = value ? 'true' : 'false';
            continue;
        }
        console.error(`✗ --header.${key} 必须是 string / number / boolean`);
        process.exit(1);
    }
    return result;
}
function tryParseJson(text) {
    if (!text) {
        return null;
    }
    try {
        return JSON.parse(text);
    }
    catch {
        return null;
    }
}
async function parseMcpResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('text/event-stream')) {
        const text = await response.text();
        const line = text.split('\n').find((item) => item.startsWith('data: '));
        if (!line) {
            throw new Error('SSE 响应中未找到 data 字段');
        }
        return JSON.parse(line.slice(6));
    }
    return await response.json();
}
async function postMcp(body) {
    const url = readStarrocksUrl();
    const headers = buildHeaders();
    const payload = JSON.stringify(body);
    (0, logger_1.debugLog)('STARROCKS MCP REQUEST', {
        method: 'POST',
        url,
        headers,
        body,
    });
    let response;
    try {
        response = await fetch(url, {
            method: 'POST',
            headers,
            body: payload,
        });
    }
    catch (error) {
        if ((0, logger_1.isVerbose)()) {
            const cause = error instanceof Error && 'cause' in error
                ? error.cause
                : undefined;
            (0, logger_1.debugLog)('STARROCKS MCP FETCH ERROR', error instanceof Error ? {
                name: error.name,
                message: error.message,
                cause: cause instanceof Error ? {
                    name: cause.name,
                    message: cause.message,
                } : cause,
            } : String(error));
        }
        throw error;
    }
    if ((0, logger_1.isVerbose)()) {
        const responseText = await response.clone().text();
        (0, logger_1.debugLog)('STARROCKS MCP RESPONSE', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            body: tryParseJson(responseText) ?? responseText,
        });
    }
    return response;
}
async function ensureSession() {
    if (sessionId) {
        return;
    }
    const response = await postMcp({
        jsonrpc: '2.0',
        id: nextId(),
        method: 'initialize',
        params: {
            protocolVersion: MCP_PROTOCOL_VERSION,
            capabilities: {},
            clientInfo: { name: 'slclaw-cli-starrocks', version: '1.0.0' },
        },
    });
    if (!response.ok) {
        throw new Error(`MCP initialize 请求失败: ${response.status}`);
    }
    const sid = response.headers.get('mcp-session-id');
    if (!sid) {
        return;
    }
    sessionId = sid;
    await postMcp({
        jsonrpc: '2.0',
        method: 'notifications/initialized',
        params: {},
    });
}
function readMcpResult(data) {
    const error = data.error;
    if (error && typeof error === 'object') {
        const message = error.message;
        throw new Error(`MCP 错误: ${typeof message === 'string' ? message : JSON.stringify(error)}`);
    }
    const result = data.result && typeof data.result === 'object'
        ? data.result
        : data;
    if (result.structuredContent) {
        return result.structuredContent;
    }
    const content = Array.isArray(result.content) ? result.content : [];
    const text = content
        .map((item) => {
        if (item && typeof item === 'object' && 'text' in item) {
            return String(item.text ?? '');
        }
        return JSON.stringify(item);
    })
        .join('\n');
    const parsed = tryParseJson(text);
    return parsed ?? {
        content,
        text,
        raw: result,
    };
}
async function callReadQuery(query, db) {
    await ensureSession();
    const toolArgs = { query };
    if (db) {
        toolArgs.db = db;
    }
    const response = await postMcp({
        jsonrpc: '2.0',
        id: nextId(),
        method: 'tools/call',
        params: {
            name: 'read_query',
            arguments: toolArgs,
        },
    });
    if (!response.ok) {
        throw new Error(`MCP 请求失败: ${response.status}`);
    }
    return readMcpResult(await parseMcpResponse(response));
}
async function executeStarrocksCommand(args) {
    if (args[0] !== 'starrocks') {
        return false;
    }
    if (args[1] !== 'read-query') {
        return false;
    }
    const flags = (0, flags_1.parseFlags)(args.slice(2));
    if (flags.help === 'true' || flags.h === 'true') {
        return false;
    }
    headerOverrides = parseHeaderOverrides(flags.header);
    if ((0, logger_1.isVerbose)() && Object.keys(headerOverrides).length > 0) {
        (0, logger_1.debugLog)('STARROCKS HEADER 覆盖层 (--header)', headerOverrides);
    }
    const rawQuery = flags.query || flags.sql || '';
    const query = resolveSqlPlaceholders(rawQuery);
    if ((0, logger_1.isVerbose)() && rawQuery !== query) {
        (0, logger_1.debugLog)('STARROCKS SQL 占位符替换', { before: rawQuery, after: query });
    }
    assertReadOnlyQuery(query);
    try {
        const result = await callReadQuery(query, flags.db);
        (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags));
    }
    catch (error) {
        console.error(error instanceof Error ? error.message : String(error));
        process.exit(1);
    }
    return true;
}
