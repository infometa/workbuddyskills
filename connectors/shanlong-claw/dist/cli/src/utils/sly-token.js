"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.acquireSlyToken = acquireSlyToken;
const crypto_1 = require("crypto");
const logger_1 = require("../logger");
const env_1 = require("../env");
const http_timeout_1 = require("./http-timeout");
function normalizeBaseUrl(baseUrl) {
    return baseUrl.replace(/\/+$/, '');
}
function buildSlyUrl(baseUrl, path) {
    return `${normalizeBaseUrl(baseUrl)}${path}`;
}
function requireEnvValue(value, envKey) {
    if (!value) {
        throw new Error(`缺少环境变量 ${envKey}`);
    }
    return value;
}
function toPemPublicKey(publicKey) {
    if (publicKey.includes('BEGIN PUBLIC KEY')) {
        return publicKey;
    }
    const normalized = publicKey.replace(/\s+/g, '');
    const lines = normalized.match(/.{1,64}/g) || [];
    return `-----BEGIN PUBLIC KEY-----\n${lines.join('\n')}\n-----END PUBLIC KEY-----`;
}
function encryptSlyPayload(publicKey, mobile, password) {
    const payload = JSON.stringify({ mobile, password });
    const buffer = Buffer.from(payload, 'utf-8');
    return (0, crypto_1.publicEncrypt)({
        key: toPemPublicKey(publicKey),
        padding: crypto_1.constants.RSA_PKCS1_PADDING,
    }, buffer).toString('base64');
}
function readPrincipalUserName(principal, fallback) {
    return principal?.userName
        || principal?.nickName
        || principal?.name
        || principal?.realName
        || principal?.mobile
        || fallback;
}
async function postJson(url, body, contentType) {
    (0, logger_1.debugLog)('SLY REQUEST', {
        method: 'POST',
        url,
        body: body || '(empty)',
    });
    const response = await (0, http_timeout_1.fetchWithTimeout)(url, {
        method: 'POST',
        headers: body
            ? { 'Content-Type': contentType || 'application/json;charset=UTF-8' }
            : undefined,
        body,
    }, 'SLY 接口', (0, http_timeout_1.getRequestTimeoutMs)('SL_SLY_TIMEOUT_MS'));
    const text = await response.text();
    if (!response.ok) {
        throw new Error(`SLY 接口 HTTP 错误: ${response.status} ${response.statusText} - ${text.slice(0, 200)}`);
    }
    let parsed;
    try {
        parsed = JSON.parse(text);
    }
    catch {
        throw new Error(`SLY 接口返回非 JSON: ${text.slice(0, 200)}`);
    }
    (0, logger_1.debugLog)('SLY RESPONSE', {
        status: response.status,
        url,
        body: parsed,
    });
    return parsed;
}
async function acquireSlyToken(options = {}) {
    const baseUrl = requireEnvValue(options.baseUrl || (0, env_1.getEnv)('SL_SLY_BASEURL'), 'SL_SLY_BASEURL');
    const mobile = requireEnvValue(options.mobile || (0, env_1.getEnv)('SL_SLY_USERNAME'), 'SL_SLY_USERNAME');
    const password = requireEnvValue(options.password || (0, env_1.getEnv)('SL_SLY_PASSWORD'), 'SL_SLY_PASSWORD');
    const publicKeyResponse = await postJson(buildSlyUrl(baseUrl, '/newProxy/auth-center/api/ano/rsa/key/publick'));
    const publicKey = publicKeyResponse.data?.publicKey;
    if (!publicKey) {
        throw new Error('SLY 公钥接口未返回 data.publicKey');
    }
    const encryptedBody = encryptSlyPayload(publicKey, mobile, password);
    const loginResponse = await postJson(buildSlyUrl(baseUrl, '/newProxy/auth-center/api/ano/login/mobile'), encryptedBody, 'application/json;charset=UTF-8');
    const token = loginResponse.data?.token;
    const principal = loginResponse.data?.principal;
    const rawUserId = principal?.userId;
    const rawAccountId = principal?.accountId;
    if (!token) {
        throw new Error('SLY 登录接口未返回 data.token');
    }
    if (rawUserId === undefined || rawUserId === null || rawUserId === '') {
        throw new Error('SLY 登录接口未返回 data.principal.userId');
    }
    if (rawAccountId === undefined || rawAccountId === null || rawAccountId === '') {
        throw new Error('SLY 登录接口未返回 data.principal.accountId');
    }
    return {
        token,
        userId: String(rawUserId),
        accountId: String(rawAccountId),
        userName: readPrincipalUserName(principal, mobile),
        orgId: principal?.orgId !== undefined && principal.orgId !== null ? String(principal.orgId) : undefined,
        orgCode: principal?.orgCode,
        orgName: principal?.orgName,
        orgType: principal?.orgType,
        rootId: principal?.rootId !== undefined && principal.rootId !== null ? String(principal.rootId) : undefined,
        rootCode: principal?.rootCode,
        rootName: principal?.rootName,
    };
}
