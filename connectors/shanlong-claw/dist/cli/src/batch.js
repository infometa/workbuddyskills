"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeBatchCommand = executeBatchCommand;
const fs_1 = __importDefault(require("fs"));
const body_1 = require("./body");
const commands_1 = require("./commands");
const crm_public_key_1 = require("./crm-public-key");
const error_audit_1 = require("./error-audit");
const env_1 = require("./env");
const flags_1 = require("./flags");
const request_1 = require("./request");
const token_cache_1 = require("./token-cache");
const token_1 = require("./token");
function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function readCode(result) {
    if (!result || typeof result !== 'object')
        return undefined;
    const record = result;
    return typeof record.code === 'string' || typeof record.code === 'number' ? record.code : undefined;
}
function isExplicitFailure(result) {
    if (!result || typeof result !== 'object' || Array.isArray(result))
        return false;
    return result.success === false;
}
function isRawResponse(result) {
    return !!result && typeof result === 'object' && 'raw' in result;
}
function hasAuth(auth) {
    return !!auth.sessionToken || Object.keys(auth.headers || {}).length > 0;
}
function parseJsonObjectFlag(flags, key) {
    const raw = flags[key];
    if (!raw)
        return {};
    try {
        const parsed = JSON.parse(raw);
        if (!isPlainObject(parsed))
            throw new Error(`--${key} 必须是 JSON 对象`);
        return parsed;
    }
    catch (error) {
        throw new Error(`解析 --${key} 失败: ${error instanceof Error ? error.message : String(error)}`);
    }
}
const domainCache = new Map();
const productTokenRefreshPromises = new Map();
let cysmsTaskChain = Promise.resolve();
function refreshProductAuthOnce(product) {
    const existing = productTokenRefreshPromises.get(product);
    if (existing)
        return existing;
    const promise = (0, token_1.refreshRequestAuth)(product)
        .then(async (auth) => {
        if (auth && hasAuth(auth)) {
            await (0, token_1.syncCySAfterSlCredentialPersist)();
        }
        return auth || null;
    });
    productTokenRefreshPromises.set(product, promise);
    return promise;
}
async function ensureAuth(product, domain) {
    let auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, (0, token_1.getRequestAuth)(product));
    if (!hasAuth(auth)) {
        auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, (await refreshProductAuthOnce(product)) || { sessionToken: null });
        if (!hasAuth(auth)) {
            throw new Error(`${product.toUpperCase()} Token 不可用`);
        }
    }
    return auth;
}
async function executeDomainTask(args) {
    const domain = args[0];
    const action = args[1];
    if (!domainCache.has(domain)) {
        domainCache.set(domain, (0, commands_1.loadCommandsMerged)(domain));
    }
    const domainData = await domainCache.get(domain);
    if (!domainData)
        throw new Error(`未知域: ${domain}`);
    const cmd = domainData.commands.find((c) => c.action === action);
    if (!cmd)
        throw new Error(`未知命令: sl ${domain} ${action}`);
    const flags = (0, flags_1.parseFlags)(args.slice(2));
    const jsonParams = parseJsonObjectFlag(flags, 'params');
    const jsonBody = parseJsonObjectFlag(flags, 'body');
    const headerOverrides = {};
    const rawHeader = parseJsonObjectFlag(flags, 'header');
    for (const [k, v] of Object.entries(rawHeader)) {
        if (typeof v === 'string' || typeof v === 'number')
            headerOverrides[k] = v;
        else if (typeof v === 'boolean')
            headerOverrides[k] = v ? 'true' : 'false';
    }
    const maxSecurityLevel = (0, env_1.getEnv)('SL_MAX_SECURITY_LEVEL', '');
    if (maxSecurityLevel) {
        const levelOrder = { S1: 1, S2: 2, S3: 3, S4: 4 };
        const cmdLevel = cmd.security_level || 'S1';
        if ((levelOrder[cmdLevel] || 1) > (levelOrder[maxSecurityLevel] || 4)) {
            throw new Error(`安全级别拦截: ${domain} ${action} 为 ${cmdLevel}，限制 ${maxSecurityLevel}`);
        }
    }
    const product = cmd.product || 'cy7';
    const resolved = (0, env_1.resolveBaseUrl)(product, cmd.env_mapping._baseUrl);
    if (!resolved.url)
        throw new Error(`缺少 ${cmd.env_mapping._baseUrl} 或 SL_GATEWAY_HOST`);
    let auth = await ensureAuth(product, domain);
    if (product === 'crm') {
        const cached = (0, token_cache_1.loadTokenCache)();
        if (!cached.crm_public_key?.token && !(0, env_1.getEnv)('SL_CRM_PUBLIC_KEY')) {
            try {
                await (0, crm_public_key_1.refreshAndCacheCrmPublicKey)(resolved.url, auth, { allowLoginKeyFallback: true });
            }
            catch { /* non-fatal */ }
        }
    }
    const body = (0, body_1.buildBody)(cmd, flags, { params: jsonParams, body: jsonBody });
    let result = await (0, request_1.makeRequest)(resolved.url, cmd.endpoint, auth.sessionToken, body, product, { ...(auth.headers || {}), ...headerOverrides });
    const tokenExpired = (0, token_1.isTokenExpiredResponse)(result, product);
    if (tokenExpired || isExplicitFailure(result)) {
        const refreshedAuth = await refreshProductAuthOnce(product);
        if (refreshedAuth && hasAuth(refreshedAuth)) {
            auth = (0, token_1.mergeScmAnalysisAuthFromEnv)(domain, refreshedAuth);
            result = await (0, request_1.makeRequest)(resolved.url, cmd.endpoint, auth.sessionToken, body, product, { ...(auth.headers || {}), ...headerOverrides });
        }
    }
    if (isRawResponse(result)) {
        throw new Error(`响应非 JSON: ${result.raw.substring(0, 200)}`);
    }
    return result;
}
async function executeCysmsBatchTask(args) {
    const cysmsAction = args[1];
    if (cysmsAction !== 'business-situation' && cysmsAction !== 'getshops') {
        throw new Error(`batch 模式暂不支持 cysms ${cysmsAction}，请用 sl cysms ${cysmsAction} 独立执行`);
    }
    const { executeCysmsCommand } = await Promise.resolve().then(() => __importStar(require('./cysms')));
    const originalLog = console.log;
    const originalError = console.error;
    let capturedOutput = undefined;
    console.log = (data, ..._rest) => {
        if (typeof data === 'string') {
            try {
                capturedOutput = JSON.parse(data);
            }
            catch {
                capturedOutput = data;
            }
        }
        else {
            capturedOutput = data;
        }
    };
    console.error = (..._args) => { };
    const origExit = process.exit;
    let exitCalled = false;
    process.exit = ((code) => {
        exitCalled = true;
        throw new Error(`cysms process.exit(${code})`);
    });
    try {
        await executeCysmsCommand(args);
        return capturedOutput;
    }
    catch (err) {
        if (exitCalled)
            throw new Error(`cysms ${cysmsAction} 执行失败`);
        throw err;
    }
    finally {
        console.log = originalLog;
        console.error = originalError;
        process.exit = origExit;
    }
}
async function executeCysmsBatchTaskSerialized(args) {
    const previous = cysmsTaskChain;
    let release;
    cysmsTaskChain = new Promise((resolve) => {
        release = resolve;
    });
    await previous;
    try {
        return await executeCysmsBatchTask(args);
    }
    finally {
        release();
    }
}
async function executeTask(task) {
    const start = Date.now();
    try {
        const args = task.args;
        if (!args || args.length < 2) {
            throw new Error('任务参数不足，至少需要 domain + action');
        }
        let result;
        if (args[0] === 'cysms') {
            result = await executeCysmsBatchTaskSerialized(args);
        }
        else {
            result = await executeDomainTask(args);
        }
        return {
            id: task.id,
            status: 'ok',
            data: result,
            elapsed_ms: Date.now() - start,
        };
    }
    catch (error) {
        return {
            id: task.id,
            status: 'error',
            error: error instanceof Error ? error.message : String(error),
            elapsed_ms: Date.now() - start,
        };
    }
}
function limitConcurrency(tasks, limit) {
    return new Promise((resolve) => {
        const results = new Array(tasks.length);
        let nextIndex = 0;
        let completedCount = 0;
        function runNext() {
            if (nextIndex >= tasks.length)
                return;
            const index = nextIndex++;
            tasks[index]().then((result) => {
                results[index] = result;
                completedCount++;
                if (completedCount === tasks.length) {
                    resolve(results);
                }
                else {
                    runNext();
                }
            });
        }
        const initialBatch = Math.min(limit, tasks.length);
        for (let i = 0; i < initialBatch; i++) {
            runNext();
        }
    });
}
function readStdin() {
    return new Promise((resolve, reject) => {
        const chunks = [];
        process.stdin.on('data', (chunk) => chunks.push(chunk));
        process.stdin.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
        process.stdin.on('error', reject);
        if (process.stdin.isTTY) {
            resolve('');
        }
    });
}
async function executeBatchCommand(cliArgs) {
    if (cliArgs[0] !== 'batch')
        return false;
    const flags = (0, flags_1.parseFlags)(cliArgs.slice(1));
    const concurrency = Math.max(1, Number(flags.concurrency || flags.c || '6'));
    const filePath = flags.file || flags.f;
    let inputText;
    if (filePath) {
        if (!fs_1.default.existsSync(filePath)) {
            console.error(`✗ batch 输入文件不存在: ${filePath}`);
            process.exit(1);
        }
        inputText = fs_1.default.readFileSync(filePath, 'utf-8');
    }
    else {
        inputText = await readStdin();
        if (!inputText.trim()) {
            console.error('✗ batch 模式需要 JSON 输入（通过 stdin 或 --file）');
            console.error('格式: echo \'{"tasks":[{"id":"t1","args":["general","action","--params","..."]}]}\' | sl batch');
            process.exit(1);
        }
    }
    let input;
    try {
        input = JSON.parse(inputText);
    }
    catch (error) {
        console.error(`✗ JSON 解析失败: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
    if (!Array.isArray(input.tasks) || input.tasks.length === 0) {
        console.error('✗ tasks 数组为空');
        process.exit(1);
    }
    const limit = input.concurrency || concurrency;
    const totalStart = Date.now();
    console.error(`→ sl batch: ${input.tasks.length} 个任务, 并发=${limit}`);
    const taskFns = input.tasks.map((task) => () => executeTask(task));
    const results = await limitConcurrency(taskFns, limit);
    const okCount = results.filter((r) => r.status === 'ok').length;
    const failedCount = results.length - okCount;
    const totalElapsed = Date.now() - totalStart;
    if (failedCount > 0) {
        (0, error_audit_1.recordErrorEventSync)({
            source: 'sl-cli',
            kind: 'batch_task_failures',
            severity: 'error',
            message: `sl batch ${failedCount}/${results.length} tasks failed`,
            args: ['batch'],
            cwd: process.cwd(),
            elapsed_ms: totalElapsed,
            status: failedCount === results.length ? 'failed' : 'partial',
            context: {
                concurrency: limit,
                failed_tasks: results
                    .filter((r) => r.status !== 'ok')
                    .slice(0, 30)
                    .map((r) => ({
                    id: r.id,
                    status: r.status,
                    error: r.error || '',
                    elapsed_ms: r.elapsed_ms,
                })),
            },
        });
    }
    console.error(`✓ batch 完成: ${okCount}/${results.length} 成功, ${totalElapsed}ms`);
    const output = {
        results,
        elapsed_ms: totalElapsed,
        summary: { total: results.length, ok: okCount, failed: failedCount },
    };
    console.log(JSON.stringify(output));
    return true;
}
