"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.refreshReportSession = refreshReportSession;
const http_1 = __importDefault(require("http"));
const https_1 = __importDefault(require("https"));
const logger_1 = require("../logger");
function httpGet(url, cookies) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(url);
        const mod = parsed.protocol === 'https:' ? https_1.default : http_1.default;
        const reqHeaders = {};
        if (cookies)
            reqHeaders.Cookie = cookies;
        const req = mod.request({
            hostname: parsed.hostname,
            port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
            path: parsed.pathname + parsed.search,
            method: 'GET',
            headers: reqHeaders,
        }, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += String(chunk); });
            res.on('end', () => resolve({ statusCode: res.statusCode || 0, headers: res.headers, body: data }));
        });
        req.on('error', reject);
        req.setTimeout(15000, () => { req.destroy(new Error('report login request timeout')); });
        req.end();
    });
}
function extractJsessionid(headers) {
    const raw = headers['set-cookie'];
    if (!raw)
        return null;
    const cookies = Array.isArray(raw) ? raw : [raw];
    for (const cookie of cookies) {
        const match = cookie.match(/JSESSIONID=([^;]+)/);
        if (match)
            return match[1];
    }
    return null;
}
function resolveRedirectUrl(location, baseUrl) {
    if (location.startsWith('http://') || location.startsWith('https://')) {
        return location;
    }
    const base = new URL(baseUrl);
    return `${base.protocol}//${base.host}${location.startsWith('/') ? '' : '/'}${location}`;
}
/**
 * 报表中心三步302跳转登录流程:
 *
 * Step 1: GET reportBaseUrl/canyin/report?subToken=xxx → 302 → cy7center?systemData=xxx
 * Step 2: GET cy7center?systemData=xxx              → 302 → reportBaseUrl/canyin/report?token=xxx
 * Step 3: GET reportBaseUrl/canyin/report?token=xxx  → 获取 JSESSIONID cookie
 *
 * 返回: { token: 真实token, jsessionid: 有效JSESSIONID }
 */
async function refreshReportSession(subToken, reportBaseUrl) {
    const base = reportBaseUrl.replace(/\/+$/, '');
    // === Step 1: subToken → 302 → cy7center ===
    const step1Url = `${base}/canyin/report`
        + `?key=postToken&value=%5Bobject+Object%5D`
        + `&subToken=${encodeURIComponent(subToken)}`
        + `&fullScreen=1&isFromSlyun=1&page=03010202`
        + `&isReportNewVersion=0&subProduct=005002`
        + `&system=shanglongCloud&postMessageToken=1&postType=postToken`;
    console.error('→ 报表中心登录 Step 1: subToken → cy7center...');
    (0, logger_1.debugLog)('REPORT LOGIN STEP 1', step1Url);
    const step1 = await httpGet(step1Url);
    const jsessionid1 = extractJsessionid(step1.headers);
    (0, logger_1.debugLog)('REPORT LOGIN STEP 1 RESULT', {
        status: step1.statusCode,
        location: step1.headers.location,
        jsessionid: jsessionid1,
    });
    if (step1.statusCode !== 302 || !step1.headers.location) {
        throw new Error(`报表中心登录 Step 1 失败: 期望 302 但返回 ${step1.statusCode}`
            + (step1.body ? ` body: ${step1.body.substring(0, 200)}` : ''));
    }
    // === Step 2: cy7center → 302 → report with real token ===
    const step2Url = resolveRedirectUrl(step1.headers.location, step1Url);
    console.error('→ 报表中心登录 Step 2: cy7center → 获取真实 token...');
    (0, logger_1.debugLog)('REPORT LOGIN STEP 2', step2Url);
    const step2 = await httpGet(step2Url);
    const jsessionid2 = extractJsessionid(step2.headers);
    (0, logger_1.debugLog)('REPORT LOGIN STEP 2 RESULT', {
        status: step2.statusCode,
        location: step2.headers.location,
        jsessionid: jsessionid2,
    });
    if (step2.statusCode !== 302 || !step2.headers.location) {
        throw new Error(`报表中心登录 Step 2 失败: 期望 302 但返回 ${step2.statusCode}`
            + (step2.body ? ` body: ${step2.body.substring(0, 200)}` : ''));
    }
    // === Step 3: 访问带 real token 的最终 URL → 获取 JSESSIONID ===
    const step3Url = resolveRedirectUrl(step2.headers.location, step2Url);
    const step3UrlObj = new URL(step3Url);
    const realToken = step3UrlObj.searchParams.get('token');
    if (!realToken) {
        throw new Error(`报表中心登录 Step 3: redirect URL 中未找到 token 参数: ${step3Url.substring(0, 200)}`);
    }
    console.error('→ 报表中心登录 Step 3: 获取 JSESSIONID...');
    (0, logger_1.debugLog)('REPORT LOGIN STEP 3', step3Url);
    const cookieStr = jsessionid1 ? `JSESSIONID=${jsessionid1}` : undefined;
    const step3 = await httpGet(step3Url, cookieStr);
    const jsessionid3 = extractJsessionid(step3.headers) || jsessionid2 || jsessionid1;
    (0, logger_1.debugLog)('REPORT LOGIN STEP 3 RESULT', {
        status: step3.statusCode,
        jsessionid: jsessionid3,
        hasToken: !!realToken,
    });
    if (!jsessionid3) {
        throw new Error('报表中心登录: 所有步骤均未返回 JSESSIONID');
    }
    console.error(`✓ 报表中心登录成功 (JSESSIONID=${jsessionid3.substring(0, 8)}...)`);
    return { token: realToken, jsessionid: jsessionid3 };
}
