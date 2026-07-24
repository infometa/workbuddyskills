"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.installErrorAudit = installErrorAudit;
exports.recordErrorEventSync = recordErrorEventSync;
const crypto_1 = __importDefault(require("crypto"));
const fs_1 = __importDefault(require("fs"));
const os_1 = __importDefault(require("os"));
const path_1 = __importDefault(require("path"));
const LOG_RELATIVE_PATH = path_1.default.join('logs', 'openclaw-error-events.ndjson');
const MAX_LOG_BYTES = 10 * 1024 * 1024;
const MAX_STRING_LENGTH = 4000;
const MAX_STDERR_LINES = 80;
let installed = false;
let wroteExitEvent = false;
let installOptions = null;
let originalConsoleError = null;
const stderrTail = [];
function installErrorAudit(options) {
    if (installed || isDisabled())
        return;
    installed = true;
    installOptions = options;
    originalConsoleError = console.error;
    console.error = (...args) => {
        captureStderr(args);
        originalConsoleError?.(...args);
    };
    process.on('exit', (code) => {
        if (!code || wroteExitEvent)
            return;
        wroteExitEvent = true;
        recordErrorEventSync({
            source: options.source,
            kind: 'process_exit',
            severity: 'error',
            message: stderrTail.slice(-12).join('\n') || `process exited with code ${code}`,
            args: sanitizeCliArgs(options.args),
            cwd: process.cwd(),
            exit_code: code,
            context: {
                cli_version: options.version || 'unknown',
                stderr_tail: stderrTail,
            },
        });
    });
}
function recordErrorEventSync(event) {
    if (isDisabled())
        return;
    try {
        const agentRoot = findAgentRoot(process.cwd(), Array.isArray(event.args) ? event.args : installOptions?.args || []);
        const logFile = process.env.OPENCLAW_ERROR_LOG_FILE
            ? path_1.default.resolve(process.env.OPENCLAW_ERROR_LOG_FILE)
            : path_1.default.join(agentRoot, LOG_RELATIVE_PATH);
        rotateIfNeeded(logFile);
        fs_1.default.mkdirSync(path_1.default.dirname(logFile), { recursive: true });
        const payload = sanitizeValue({
            schema: 'openclaw-error-event/v1',
            event_id: createEventId(),
            recorded_at: new Date().toISOString(),
            agent_root: agentRoot,
            host: os_1.default.hostname(),
            pid: process.pid,
            node: process.version,
            ...event,
        });
        fs_1.default.appendFileSync(logFile, `${JSON.stringify(payload)}\n`, 'utf8');
    }
    catch {
        // Error logging must never break the user-facing command.
    }
}
function isDisabled() {
    return /^(1|true|yes)$/i.test(String(process.env.OPENCLAW_ERROR_LOG_DISABLED || ''));
}
function captureStderr(args) {
    const line = redactString(args.map((item) => {
        if (typeof item === 'string')
            return item;
        if (item instanceof Error)
            return item.stack || item.message;
        try {
            return JSON.stringify(item);
        }
        catch {
            return String(item);
        }
    }).join(' '));
    stderrTail.push(truncate(line, MAX_STRING_LENGTH));
    while (stderrTail.length > MAX_STDERR_LINES)
        stderrTail.shift();
}
function findAgentRoot(startDir, args = []) {
    const envPath = extractEnvPath(args);
    const starts = [envPath, startDir].filter(Boolean);
    for (const start of starts) {
        const root = findUp(start, (dir) => fs_1.default.existsSync(path_1.default.join(dir, '.env')) && fs_1.default.existsSync(path_1.default.join(dir, 'skills')));
        if (root)
            return root;
    }
    return path_1.default.resolve(startDir || process.cwd());
}
function extractEnvPath(args) {
    const values = args.map((x) => String(x));
    const index = values.indexOf('--envPath');
    if (index < 0 || !values[index + 1])
        return '';
    const raw = path_1.default.resolve(process.cwd(), values[index + 1]);
    try {
        const stat = fs_1.default.statSync(raw);
        return stat.isDirectory() ? raw : path_1.default.dirname(raw);
    }
    catch {
        return raw;
    }
}
function findUp(startDir, predicate) {
    let dir = path_1.default.resolve(startDir);
    try {
        if (fs_1.default.existsSync(dir) && !fs_1.default.statSync(dir).isDirectory())
            dir = path_1.default.dirname(dir);
    }
    catch {
        // Continue with resolved value.
    }
    for (;;) {
        if (predicate(dir))
            return dir;
        const parent = path_1.default.dirname(dir);
        if (parent === dir)
            return '';
        dir = parent;
    }
}
function rotateIfNeeded(logFile) {
    try {
        if (!fs_1.default.existsSync(logFile))
            return;
        const stat = fs_1.default.statSync(logFile);
        if (stat.size <= MAX_LOG_BYTES)
            return;
        const rotated = `${logFile}.1`;
        try {
            fs_1.default.rmSync(rotated, { force: true });
        }
        catch {
            // ignore
        }
        fs_1.default.renameSync(logFile, rotated);
    }
    catch {
        // ignore
    }
}
function createEventId() {
    return crypto_1.default
        .createHash('sha256')
        .update(`${Date.now()}-${process.pid}-${Math.random()}`)
        .digest('hex')
        .slice(0, 24);
}
function sanitizeCliArgs(args) {
    const out = [];
    const redactNext = new Set(['--body', '--params', '--header']);
    for (let i = 0; i < args.length; i += 1) {
        const cur = String(args[i]);
        out.push(redactString(cur));
        if (redactNext.has(cur) && i + 1 < args.length) {
            out.push('[REDACTED]');
            i += 1;
        }
    }
    return out;
}
function sanitizeValue(value, depth = 0) {
    if (depth > 5)
        return '[DEPTH_LIMIT]';
    if (typeof value === 'string')
        return redactString(truncate(value, MAX_STRING_LENGTH));
    if (typeof value === 'number' || typeof value === 'boolean' || value === null || value === undefined)
        return value;
    if (value instanceof Error) {
        return {
            name: value.name,
            message: redactString(truncate(value.message, MAX_STRING_LENGTH)),
            stack: redactString(truncate(value.stack || '', MAX_STRING_LENGTH * 2)),
        };
    }
    if (Array.isArray(value))
        return value.slice(0, 80).map((item) => sanitizeValue(item, depth + 1));
    if (typeof value === 'object') {
        const out = {};
        for (const [key, item] of Object.entries(value)) {
            if (isSensitiveKey(key)) {
                out[key] = '[REDACTED]';
            }
            else {
                out[key] = sanitizeValue(item, depth + 1);
            }
        }
        return out;
    }
    return redactString(String(value));
}
function isSensitiveKey(key) {
    return /token|authorization|cookie|password|passwd|secret|api[_-]?key|encryptData|credential|session/i.test(key);
}
function redactString(input) {
    return input
        .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, 'Bearer [REDACTED]')
        .replace(/[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}/g, '[REDACTED_JWT]')
        .replace(/((?:token|authorization|cookie|password|passwd|secret|api[_-]?key|encryptData|access_token|refresh_token|fxscmToken|sly_remote_token)\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,}]+)/gi, '$1[REDACTED]')
        .replace(/(Access-Token-Shop|Fx-Token|Sly-Token|sly_token)(\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,}]+)/gi, '$1$2[REDACTED]');
}
function truncate(text, maxLength) {
    if (text.length <= maxLength)
        return text;
    return `${text.slice(0, maxLength)}...[truncated ${text.length - maxLength} chars]`;
}
