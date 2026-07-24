"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.refreshAndCacheCrmPublicKey = refreshAndCacheCrmPublicKey;
const token_cache_1 = require("./token-cache");
const request_1 = require("./request");
function extractPublicKey(result) {
    if (!result || typeof result !== 'object') {
        return '';
    }
    const record = result;
    const data = record.data;
    return typeof data?.publicKey === 'string' ? data.publicKey : '';
}
function readResultMessage(result) {
    if (!result || typeof result !== 'object') {
        return '';
    }
    const record = result;
    const value = [record.message, record.msg].find((item) => typeof item === 'string');
    return typeof value === 'string' ? value : '';
}
async function refreshAndCacheCrmPublicKey(baseUrl, auth, options = {}) {
    const verbose = !!options.verbose;
    let loginKey = '';
    try {
        if (verbose) {
            console.error('→ Step 1: 从 loginKey.do 获取公钥...');
        }
        const result = await (0, request_1.makeRequest)(baseUrl, { path: '/crm7auth/login/kotler/loginKey.do', method: 'POST' }, null, {}, 'crm');
        loginKey = extractPublicKey(result);
        if (verbose) {
            if (loginKey) {
                console.error(`✓ loginKey.do 公钥: ${loginKey.substring(0, 40)}...`);
            }
            else {
                console.error('✗ loginKey.do 未返回公钥');
                console.error(JSON.stringify(result, null, 2).substring(0, 300));
            }
        }
    }
    catch (error) {
        if (verbose) {
            const message = error instanceof Error ? error.message : String(error);
            console.error(`✗ loginKey.do 请求失败: ${message}`);
        }
    }
    let initKey = '';
    if (auth.sessionToken) {
        try {
            if (verbose) {
                console.error('→ Step 2: 从 init 接口获取 API 公钥（init 不加密，仅需 sessionId）...');
            }
            const result = await (0, request_1.makeRequest)(baseUrl, { path: '/kotler-base-admin/function/init', method: 'POST' }, auth.sessionToken, {}, 'crm', auth.headers);
            initKey = extractPublicKey(result);
            if (verbose) {
                if (initKey) {
                    console.error(`✓ init 公钥: ${initKey.substring(0, 40)}...`);
                }
                else {
                    const code = result && typeof result === 'object' ? result.code : '';
                    console.error(`  init 返回: code=${code} msg=${readResultMessage(result)}`);
                }
            }
        }
        catch (error) {
            if (verbose) {
                const message = error instanceof Error ? error.message : String(error);
                console.error(`  init 请求失败: ${message}，使用 loginKey 作为兜底`);
            }
        }
    }
    else if (verbose) {
        console.error('→ Step 2: 跳过 init（无 sessionId，配置 SL_CRM_SESSION_TOKEN 后可获取 init 公钥）');
        console.error('  ⚠ 仅使用 loginKey.do 公钥，此公钥可能仅用于登录加密，API 调用可能解密失败！');
    }
    const finalKey = initKey || (options.allowLoginKeyFallback ? loginKey : '');
    if (!finalKey) {
        if (verbose && loginKey && auth.sessionToken) {
            console.error('⚠ 已获取 loginKey.do 公钥，但 init 公钥获取失败；为避免污染本地缓存，本次不写入 crm_public_key');
        }
        return null;
    }
    (0, token_cache_1.cacheToken)('crm_public_key', finalKey);
    if (verbose) {
        const source = initKey ? 'init' : 'loginKey.do';
        const keysMatch = loginKey && initKey
            ? (loginKey === initKey ? '✓ 两个公钥相同' : '⚠ 两个公钥不同！使用 init 公钥')
            : '';
        console.log('');
        console.log(`✓ CRM RSA 公钥获取成功（来源: ${source}）${keysMatch ? ` — ${keysMatch}` : ''}`);
        console.log('');
    }
    return finalKey;
}
