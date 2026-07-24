"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeConnectorCommand = executeConnectorCommand;
const crypto_1 = __importDefault(require("crypto"));
const fs_1 = __importDefault(require("fs"));
const http_1 = __importDefault(require("http"));
const path_1 = __importDefault(require("path"));
const env_1 = require("./env");
const token_cache_1 = require("./token-cache");
const token_1 = require("./token");
const CONNECTOR_MODE_KEY = 'connector_mode';
const AUTH_TIMEOUT_MS = 300000; // 5 minutes
const PRODUCT_TOKEN_KEYS = {
    cy7: 'wuuxiangCyToken',
    crm: 'crm8Token',
    scm: 'fxscmToken',
    dc: 'sly_remote_token',
};
function readTokenString(key) {
    const value = (0, token_cache_1.loadTokenValue)(key);
    return typeof value === 'string' && value ? value : '';
}
function loadCliHomeEnv() {
    const cliHomePath = envFilePath();
    if (!fs_1.default.existsSync(cliHomePath))
        return;
    const content = fs_1.default.readFileSync(cliHomePath, 'utf-8');
    for (const line of content.split(/\r?\n/)) {
        const trimmed = line.replace(/^\s*export\s+/, '').trim();
        if (!trimmed || trimmed.startsWith('#'))
            continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx <= 0)
            continue;
        const key = trimmed.slice(0, eqIdx).trim();
        const value = trimmed.slice(eqIdx + 1).trim();
        if (value && !process.env[key]) {
            process.env[key] = value;
        }
    }
}
function readApiKey() {
    const fileKey = readApiKeyFromEnvFile();
    if (fileKey !== null)
        return fileKey;
    return (0, env_1.getEnv)('SL_API_KEY').trim();
}
function readApiKeyFromEnvFile() {
    const cliHomePath = envFilePath();
    if (!fs_1.default.existsSync(cliHomePath))
        return null;
    const content = fs_1.default.readFileSync(cliHomePath, 'utf-8');
    const match = content.match(/^[ \t]*(?:export[ \t]+)?SL_API_KEY[ \t]*=[ \t]*(.*)$/m);
    return match ? match[1].trim() : null;
}
function getAuthPageBaseUrl() {
    return (0, env_1.getEnv)('SL_CONNECTOR_AUTH_PAGE', 'https://sly.tcsl.com.cn/open/connector/auth');
}
function resolveCliHome() {
    return (0, env_1.getEnv)('SL_CLI_HOME', path_1.default.join(process.env.HOME || process.env.USERPROFILE || '.', '.slclaw'));
}
function envFilePath() {
    const cliHome = resolveCliHome();
    if (!fs_1.default.existsSync(cliHome)) {
        fs_1.default.mkdirSync(cliHome, { recursive: true });
    }
    return path_1.default.join(cliHome, '.env');
}
function readDefaultEnvTemplate() {
    const cliHome = resolveCliHome();
    const candidates = [
        path_1.default.join(cliHome, 'default.env'),
        path_1.default.resolve(__dirname, '../../../default.env'),
        path_1.default.resolve(__dirname, '../../default.env'),
    ];
    for (const candidate of candidates) {
        if (fs_1.default.existsSync(candidate)) {
            return fs_1.default.readFileSync(candidate, 'utf-8');
        }
    }
    return 'SL_ENV=prod\nSL_API_KEY=\n';
}
function ensureCliHomeEnvExists() {
    const filePath = envFilePath();
    if (!fs_1.default.existsSync(filePath)) {
        fs_1.default.writeFileSync(filePath, readDefaultEnvTemplate().replace(/\n*$/, '\n'), { encoding: 'utf-8', mode: 0o600 });
    }
}
function printConnectorStatus(authenticated) {
    console.log(JSON.stringify({ authenticated }));
}
function persistApiKeyToEnv(apiKey) {
    const filePath = envFilePath();
    ensureCliHomeEnvExists();
    const nextLine = `SL_API_KEY=${apiKey}`;
    let lines = fs_1.default.readFileSync(filePath, 'utf-8').split(/\r?\n/);
    const keyPattern = /^\s*(?:export\s+)?SL_API_KEY\s*=/;
    let replaced = false;
    lines = lines.map((line) => {
        if (keyPattern.test(line)) {
            replaced = true;
            return nextLine;
        }
        return line;
    });
    if (!replaced) {
        if (lines.length > 0 && lines[lines.length - 1] !== '') {
            lines.push('');
        }
        lines.push(nextLine);
    }
    fs_1.default.writeFileSync(filePath, lines.join('\n').replace(/\n*$/, '\n'), { encoding: 'utf-8', mode: 0o600 });
}
function clearApiKeyFromEnv() {
    const filePath = envFilePath();
    if (!fs_1.default.existsSync(filePath))
        return;
    const keyPattern = /^\s*(?:export\s+)?SL_API_KEY\s*=/;
    const lines = fs_1.default.readFileSync(filePath, 'utf-8')
        .split(/\r?\n/)
        .map((line) => (keyPattern.test(line) ? 'SL_API_KEY=' : line));
    fs_1.default.writeFileSync(filePath, lines.join('\n').replace(/\n*$/, '\n'), { encoding: 'utf-8', mode: 0o600 });
}
function hasProductToken() {
    return Object.values(PRODUCT_TOKEN_KEYS).some((key) => !!readTokenString(key));
}
function hasBizParams() {
    const raw = (0, token_cache_1.loadTokenValue)('biz_params');
    if (!raw || typeof raw !== 'object' || Array.isArray(raw))
        return false;
    const params = raw;
    return !!(params.SL_CY7_GROUP_ID
        || params.SL_CRM_GROUP_ID
        || params.SL_CRM_GC_ID
        || params.SL_SCM_GROUP_ID);
}
function markConnectorMode() {
    (0, token_cache_1.saveTokenValue)(CONNECTOR_MODE_KEY, {
        mode: 'workbuddy',
        authenticated_at: new Date().toISOString(),
        security_level: 'S1',
    });
}
async function refreshConnectorTokens() {
    const maxRetries = 2;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const auth = await (0, token_1.refreshRequestAuth)('cy7');
            if (auth && (auth.sessionToken || Object.keys(auth.headers || {}).length > 0)) {
                return true;
            }
            break;
        }
        catch (e) {
            const msg = e?.message || '';
            if (msg.includes('fetch failed') || msg.includes('ETIMEDOUT') || msg.includes('ECONNREFUSED')) {
                if (attempt < maxRetries) {
                    console.error(`⚠ 网络异常，${attempt}s 后重试 (${attempt}/${maxRetries})...`);
                    await new Promise(r => setTimeout(r, attempt * 1000));
                    continue;
                }
            }
            break;
        }
    }
    return hasProductToken();
}
function generateState() {
    return crypto_1.default.randomBytes(16).toString('hex');
}
function findAvailablePort() {
    return new Promise((resolve, reject) => {
        const server = http_1.default.createServer();
        server.listen(0, '127.0.0.1', () => {
            const addr = server.address();
            if (!addr || typeof addr === 'string') {
                server.close();
                reject(new Error('Failed to bind port'));
                return;
            }
            const port = addr.port;
            server.close(() => resolve(port));
        });
        server.on('error', reject);
    });
}
function buildAuthFormHtml(state) {
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>商龙餐饮 SaaS - 连接器认证</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f7fa;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.card{background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.08);padding:40px;max-width:420px;width:100%}
.logo{text-align:center;margin-bottom:24px}
.logo svg{width:48px;height:48px}
h1{font-size:20px;color:#1a1a1a;text-align:center;margin-bottom:8px}
.subtitle{font-size:14px;color:#666;text-align:center;margin-bottom:28px}
label{display:block;font-size:14px;color:#333;margin-bottom:6px;font-weight:500}
input[type="password"],input[type="text"]{width:100%;padding:12px 14px;border:1px solid #ddd;border-radius:8px;font-size:14px;transition:border-color .2s}
input:focus{outline:none;border-color:#1E88E5;box-shadow:0 0 0 3px rgba(30,136,229,0.1)}
.hint{font-size:12px;color:#999;margin-top:6px}
button{width:100%;padding:12px;background:#1E88E5;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:500;cursor:pointer;margin-top:20px;transition:background .2s}
button:hover{background:#1565C0}
button:disabled{background:#ccc;cursor:not-allowed}
.error{color:#e53935;font-size:13px;margin-top:8px;display:none}
.success{text-align:center;color:#43a047;font-size:16px;padding:40px 0}
</style>
</head>
<body>
<div class="card">
<div class="logo"><svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" rx="12" fill="#1E88E5"/><text x="32" y="42" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="28" fill="white">SL</text></svg></div>
<div id="form-view">
<h1>连接商龙餐饮 SaaS</h1>
<p class="subtitle">请输入商龙云 API Key 完成连接</p>
<form id="auth-form">
<label for="api-key">API Key</label>
<input type="password" id="api-key" name="api_key" placeholder="登录商龙云 → 开放平台 → API Key 管理" autocomplete="off" required>
<p class="hint">Key 仅存储在本机，不会上传到任何云端</p>
<p class="error" id="error-msg"></p>
<button type="submit" id="submit-btn">确认连接</button>
</form>
</div>
<div id="success-view" style="display:none">
<div class="success">
<p style="font-size:32px;margin-bottom:12px">✓</p>
<p>认证成功，可以关闭此页面</p>
</div>
</div>
</div>
<script>
const form=document.getElementById('auth-form');
const errorEl=document.getElementById('error-msg');
const btn=document.getElementById('submit-btn');
form.addEventListener('submit',async(e)=>{
  e.preventDefault();
  const key=document.getElementById('api-key').value.trim();
  if(!key){errorEl.textContent='请输入 API Key';errorEl.style.display='block';return;}
  btn.disabled=true;btn.textContent='连接中...';errorEl.style.display='none';
  try{
    const resp=await fetch('/callback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:key,state:'${state}'})});
    if(!resp.ok)throw new Error(await resp.text());
    document.getElementById('form-view').style.display='none';
    document.getElementById('success-view').style.display='block';
  }catch(err){
    errorEl.textContent=err.message||'连接失败，请重试';errorEl.style.display='block';
    btn.disabled=false;btn.textContent='确认连接';
  }
});
</script>
</body>
</html>`;
}
function buildSuccessHtml() {
    return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>认证成功</title></head><body style="display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif"><h2 style="color:#43a047">✓ 认证成功，可以关闭此页面</h2></body></html>`;
}
/**
 * Device Flow 本地认证服务器
 *
 * 启动本地 HTTP 服务，提供：
 * - GET /         → 返回 API Key 输入表单 HTML
 * - POST /callback → 接收 API Key，完成换票
 *
 * WorkBuddy 配置 authDeviceFlow:true 后不会 kill auth 进程，
 * CLI 自行等待用户提交后退出。
 */
function startAuthServer(port, state) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            server.close();
            reject(new Error('认证超时（5 分钟），请重新执行 sl connector auth'));
        }, AUTH_TIMEOUT_MS);
        const server = http_1.default.createServer((req, res) => {
            // CORS for local form submission
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
            if (req.method === 'OPTIONS') {
                res.writeHead(204);
                res.end();
                return;
            }
            if (req.method === 'GET' && (req.url === '/' || req.url === '/auth')) {
                res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                res.end(buildAuthFormHtml(state));
                return;
            }
            if (req.method === 'POST' && req.url === '/callback') {
                let body = '';
                req.on('data', (chunk) => { body += chunk.toString(); });
                req.on('end', () => {
                    try {
                        const data = JSON.parse(body);
                        if (data.state !== state) {
                            res.writeHead(403, { 'Content-Type': 'text/plain' });
                            res.end('state 校验失败');
                            return;
                        }
                        if (!data.key || !data.key.trim()) {
                            res.writeHead(400, { 'Content-Type': 'text/plain' });
                            res.end('API Key 不能为空');
                            return;
                        }
                        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                        res.end(buildSuccessHtml());
                        clearTimeout(timeout);
                        server.close();
                        resolve(data.key.trim());
                    }
                    catch {
                        res.writeHead(400, { 'Content-Type': 'text/plain' });
                        res.end('请求格式错误');
                    }
                });
                return;
            }
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('Not Found');
        });
        server.listen(port, '127.0.0.1', () => {
            // Server ready
        });
        server.on('error', (err) => {
            clearTimeout(timeout);
            reject(err);
        });
    });
}
/**
 * WorkBuddy Connector 认证 — Device Flow
 *
 * 流程:
 * 1. 启动本地 HTTP 服务器（含 API Key 输入表单）
 * 2. stdout 输出认证页 URL（WorkBuddy 提取后弹出 Device Code Modal）
 * 3. 用户在浏览器输入 API Key 并提交
 * 4. 本地服务器接收 Key → 写入凭证文件 → 换取业务 Token
 * 5. 写入 connector_mode=workbuddy → exit 0
 */
async function connectorAuth() {
    const existingKey = readApiKey();
    if (existingKey && hasProductToken()) {
        console.error('✓ 已认证，如需重新认证请先执行 sl connector unauth');
        printConnectorStatus(true);
        process.exit(0);
    }
    if (existingKey) {
        console.error('✓ 检测到已有 API Key，正在换取业务 Token...');
        process.env.SL_API_KEY = existingKey;
        loadCliHomeEnv();
        const ok = await refreshConnectorTokens();
        if (ok && hasProductToken()) {
            markConnectorMode();
            console.error('✓ 认证完成');
            printConnectorStatus(true);
            process.exit(0);
        }
        console.error('⚠ 已有 Key 换票失败，将打开认证页面重新输入');
    }
    const state = generateState();
    const port = await findAvailablePort();
    // 优先使用远程 HTTPS 认证页（部署在 sly.tcsl.com.cn）
    // 回退方案：本地 HTTP 服务器同时 serve 表单
    const remoteAuthPage = getAuthPageBaseUrl();
    const authUrl = `${remoteAuthPage}?port=${port}&state=${state}`;
    // stdout 输出 URL — WorkBuddy Device Flow 模式下提取此 URL 并展示给用户
    console.log(authUrl);
    console.error(`→ 等待浏览器认证... (本地回调: 127.0.0.1:${port})`);
    console.error(`  如浏览器未自动打开，请手动访问: http://127.0.0.1:${port}/`);
    let apiKey;
    try {
        apiKey = await startAuthServer(port, state);
    }
    catch (error) {
        const msg = error instanceof Error ? error.message : String(error);
        console.error(`✗ ${msg}`);
        process.exit(1);
    }
    // 持久化 API Key 并重新加载完整 env 配置
    process.env.SL_API_KEY = apiKey;
    persistApiKeyToEnv(apiKey);
    loadCliHomeEnv();
    console.error('✓ API Key 已保存');
    // 换取业务 Token
    console.error('→ 正在使用商龙云 Key 换取业务 Token...');
    const ok = await refreshConnectorTokens();
    if (!ok || !hasProductToken()) {
        console.error('✗ Token 换取失败，请检查商龙云 Key 是否有效或是否具备业务线权限');
        process.exit(1);
    }
    if (!hasBizParams()) {
        console.error('⚠ 未获取到业务参数，部分命令可能需要手动传参');
    }
    markConnectorMode();
    console.error('✓ 认证完成，连接器已就绪');
    process.exit(0);
}
async function connectorStatus() {
    if (!readApiKey()) {
        printConnectorStatus(false);
        process.exit(1);
    }
    if (!hasProductToken()) {
        const ok = await refreshConnectorTokens();
        if (!ok || !hasProductToken()) {
            printConnectorStatus(false);
            process.exit(1);
        }
        markConnectorMode();
    }
    printConnectorStatus(true);
    process.exit(0);
}
function connectorUnauth() {
    (0, token_cache_1.clearTokenCache)();
    clearApiKeyFromEnv();
    printConnectorStatus(false);
    process.exit(0);
}
function printConnectorHelp() {
    const mode = readApiKey() && hasProductToken() ? '已认证' : '未认证';
    console.log(`
用法: sl connector <command>

Commands:
  auth      认证（浏览器输入 API Key，本地完成换票）
  status    检查认证状态
  unauth    清除凭证和 Token 缓存

认证流程 (Device Flow):
  1. sl connector auth 启动本地服务 + 输出认证页 URL
  2. WorkBuddy 在浏览器打开认证页（或手动访问）
  3. 用户输入商龙云 API Key 并提交
  4. CLI 接收 Key → 换取产品 Token → 写入凭证
  5. 后续业务命令自动限制为 S1 只读安全级别

当前状态: ${mode}
凭证目录: ${resolveCliHome()}
`);
}
async function executeConnectorCommand(args) {
    if (args[0] !== 'connector') {
        return false;
    }
    ensureCliHomeEnvExists();
    loadCliHomeEnv();
    switch (args[1]) {
        case 'auth':
            await connectorAuth();
            return true;
        case 'status':
            await connectorStatus();
            return true;
        case 'unauth':
        case 'logout':
            connectorUnauth();
            return true;
        default:
            printConnectorHelp();
            return true;
    }
}
