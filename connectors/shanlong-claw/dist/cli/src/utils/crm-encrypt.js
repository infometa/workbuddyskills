"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.crmRsaEncrypt = crmRsaEncrypt;
exports.shouldEncryptCrmBody = shouldEncryptCrmBody;
exports.encryptCrmBody = encryptCrmBody;
const crypto_1 = require("crypto");
const logger_1 = require("../logger");
const RSA_MAX_CHUNK_BYTES = 117;
function toPemPublicKey(raw) {
    if (raw.includes('BEGIN PUBLIC KEY')) {
        return raw;
    }
    const clean = raw.replace(/\s+/g, '');
    const lines = clean.match(/.{1,64}/g) || [];
    return `-----BEGIN PUBLIC KEY-----\n${lines.join('\n')}\n-----END PUBLIC KEY-----`;
}
function utf8ByteLength(char) {
    const code = char.charCodeAt(0);
    if (code <= 0x7f)
        return 1;
    if (code <= 0x7ff)
        return 2;
    if (code <= 0xffff)
        return 3;
    return 4;
}
/**
 * CRM RSA 分段加密 — 严格复刻 kotler-front/packages/utils/src/rasCrypt.ts
 *
 * RSA 1024 位密钥单次加密上限 117 字节。原始前端在 bitLen > 117 时
 * 执行两次 i--（显式 + subStart=i-- 的后置递减），导致每段实际切在
 * ≤116 字节处。后端解密按 128 字节块拆分，必须与前端分段一致。
 */
function crmRsaEncrypt(plainText, publicKey) {
    const pem = toPemPublicKey(publicKey);
    const chunks = [];
    let subStart = 0;
    let bitLen = 0;
    for (let i = 0; i < plainText.length; i++) {
        bitLen += utf8ByteLength(plainText[i]);
        if (bitLen > RSA_MAX_CHUNK_BYTES) {
            // 与原始 rasCrypt.ts 完全一致的双退位逻辑
            i--;
            const chunk = plainText.substring(subStart, i);
            chunks.push((0, crypto_1.publicEncrypt)({ key: pem, padding: crypto_1.constants.RSA_PKCS1_PADDING }, Buffer.from(chunk, 'utf-8')));
            subStart = i--;
            bitLen = 0;
        }
    }
    const tail = plainText.substring(subStart);
    if (tail) {
        chunks.push((0, crypto_1.publicEncrypt)({ key: pem, padding: crypto_1.constants.RSA_PKCS1_PADDING }, Buffer.from(tail, 'utf-8')));
    }
    return Buffer.concat(chunks).toString('base64');
}
const NO_ENCRYPT_PATHS = new Set([
    '/crm7auth/login/kotler/loginKey.do',
    '/crm7auth/login/kotler/login.do',
    '/crm7auth/login/kotler/logout.do',
    '/crm7auth/login/kotler/dragonButlerLogin',
    '/kotler-base-admin/function/init',
    '/crm7auth/user/kotler/updateLastEmp.do',
    '/crm7auth/user/kotler/saveEditUserName.do',
    '/crm7auth/user/kotler/saveEditUserPassword.do',
    '/crm7auth/emp/kotler/getEmpCompanyList',
    '/crm7auth/login/kotler/sendSms.do',
    '/crm7auth/login/kotler/smsVerify.do',
    '/crm7auth/login/kotler/register.do',
    '/crm7auth/chatgpt/getAiAnswerSort',
    '/crm7auth/chatgpt/getAiAnswerHistory',
    '/crm7auth/chatgpt/getAiChartData',
]);
function shouldEncryptCrmBody(endpointPath) {
    return !NO_ENCRYPT_PATHS.has(endpointPath);
}
function encryptCrmBody(body, publicKey, endpointPath) {
    if (!shouldEncryptCrmBody(endpointPath)) {
        (0, logger_1.debugLog)('CRM ENCRYPT', `跳过加密 (白名单): ${endpointPath}`);
        return body;
    }
    const { sessionId, ...payload } = body;
    if (Object.keys(payload).length === 0) {
        (0, logger_1.debugLog)('CRM ENCRYPT', `跳过加密 (无业务参数): ${endpointPath}`);
        return body;
    }
    const jsonStr = JSON.stringify(payload);
    const encrypted = crmRsaEncrypt(jsonStr, publicKey);
    (0, logger_1.debugLog)('CRM ENCRYPT', {
        path: endpointPath,
        original: payload,
        originalJson: jsonStr,
        encryptedLength: encrypted.length,
    });
    const result = { param: encrypted };
    if (sessionId) {
        result.sessionId = sessionId;
    }
    return result;
}
