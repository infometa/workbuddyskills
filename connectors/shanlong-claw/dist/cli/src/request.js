"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.makeRequest = makeRequest;
const http_1 = __importDefault(require("http"));
const https_1 = __importDefault(require("https"));
const crypto_1 = require("crypto");
const env_1 = require("./env");
const logger_1 = require("./logger");
const token_cache_1 = require("./token-cache");
const crm_encrypt_1 = require("./utils/crm-encrypt");
const http_timeout_1 = require("./utils/http-timeout");
const parse_cysms_json_1 = require("./parse-cysms-json");
function makeRequest(baseUrl, endpoint, sessionToken, bodyData, product, headerOverrides = {}, requestOptions = {}) {
    return new Promise((resolve, reject) => {
        const base = baseUrl.replace(/\/+$/, '');
        let ep = endpoint.path.startsWith('/') ? endpoint.path : `/${endpoint.path}`;
        let body = { ...bodyData };
        const rawForm = typeof requestOptions.rawFormBody === 'string' && requestOptions.rawFormBody.trim()
            ? requestOptions.rawFormBody
            : null;
        const consumedPathParams = new Set();
        ep = ep.replace(/:(\w+)/g, (match, paramName) => {
            if (body[paramName] !== undefined) {
                const value = String(body[paramName]);
                consumedPathParams.add(paramName);
                return encodeURIComponent(value);
            }
            return match;
        });
        for (const p of consumedPathParams)
            delete body[p];
        if (product === 'crm' && sessionToken && !rawForm) {
            body.sessionId = sessionToken;
        }
        const method = (endpoint.method || 'POST').toUpperCase();
        const isGet = method === 'GET';
        if (product === 'crm' && !isGet && !rawForm) {
            const cached = (0, token_cache_1.loadTokenCache)();
            let crmPublicKey = requestOptions.crmPublicKeyOverride || cached.crm_public_key?.token || (0, env_1.getEnv)('SL_CRM_PUBLIC_KEY');
            if (crmPublicKey) {
                body = (0, crm_encrypt_1.encryptCrmBody)(body, crmPublicKey, ep);
            }
            else {
                (0, logger_1.debugLog)('CRM ENCRYPT', '未设置可用 CRM 公钥（override / 缓存 / SL_CRM_PUBLIC_KEY），跳过 RSA 加密。运行 sl crm-key 获取公钥');
            }
        }
        if (product === 'report' && sessionToken) {
            ep = ep + (ep.includes('?') ? '&' : '?') + `token=${encodeURIComponent(sessionToken)}&prevent302=true`;
        }
        const entries = Object.entries(body).filter(([, value]) => value !== undefined && value !== '');
        const querySeparator = ep.includes('?') ? '&' : '?';
        const queryString = isGet && entries.length > 0
            ? `${querySeparator}${entries.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`).join('&')}`
            : '';
        const postData = isGet
            ? ''
            : (rawForm !== null ? rawForm : JSON.stringify(body));
        const fullUrl = `${base}${ep}${queryString}`;
        const url = new URL(fullUrl);
        const mod = url.protocol === 'https:' ? https_1.default : http_1.default;
        const headers = {};
        if (!isGet) {
            headers['Content-Type'] = rawForm !== null
                ? 'application/x-www-form-urlencoded'
                : 'application/json';
            headers['Content-Length'] = Buffer.byteLength(postData);
        }
        if (product === 'cy7' && sessionToken) {
            headers['Access-Token-Shop'] = sessionToken;
            headers['Locale'] = 'zh_CN';
            headers['request-source-trace'] = 'sl-cli-terminal';
            const storeId = (0, env_1.getEnv)('SL_CY7_STORE_ID');
            if (storeId) {
                headers.shopId = storeId;
            }
        }
        if (product === 'crm') {
            const companyId = (0, env_1.getEnv)('SL_CRM_GROUP_ID');
            if (companyId) {
                headers['Tcsl-Shardingfield'] = 'company_id';
                headers['Tcsl-Shardingkey'] = companyId;
            }
            const slyToken = (0, env_1.getEnv)('SL_CRM_SLY_TOKEN');
            if (slyToken) {
                headers.sly_token = slyToken;
            }
        }
        if (product === 'scm' && sessionToken) {
            headers.Authorization = `${sessionToken}`;
            headers['Locale'] = 'zh_CN';
            headers['request-source-trace'] = 'sl-cli-terminal';
        }
        if (product === 'scm' && sessionToken && ep.includes('/analysis/query')) {
            const origin = (0, env_1.getEnv)('SL_ANALYSIS_ORIGIN', `${url.protocol}//${url.host}`);
            const refererBase = origin.replace(/\/+$/, '');
            headers['Accept-Language'] = (0, env_1.getEnv)('SL_ANALYSIS_ACCEPT_LANGUAGE', 'zh-CN,zh;q=0.9,my;q=0.8');
            headers.Origin = origin;
            headers.Referer = (0, env_1.getEnv)('SL_ANALYSIS_REFERER', `${refererBase}/`);
            if (!('tasTraceId' in headerOverrides)) {
                headers.tasTraceId = (0, env_1.getEnv)('SL_ANALYSIS_TAS_TRACE_ID') || (0, crypto_1.randomUUID)();
            }
        }
        if (product === 'dc') {
            const dcOrigin = (0, env_1.getEnv)('SL_DC_ORIGIN', 'https://poc-datacube.tcsl.com.cn');
            headers.Origin = dcOrigin;
            headers.Referer = `${dcOrigin}/main/sqlDevelop`;
        }
        if (product === 'report') {
            headers['Locale'] = 'zh_CN';
            const jsessionid = (0, token_cache_1.loadTokenValue)('report_jsessionid');
            if (typeof jsessionid === 'string' && jsessionid) {
                headers['Cookie'] = `JSESSIONID=${jsessionid}`;
                (0, logger_1.debugLog)('REPORT COOKIE', `JSESSIONID 已缓存 → token.json`);
            }
        }
        if (!product && sessionToken) {
            headers['Access-Token-Shop'] = sessionToken;
            headers.sessionId = sessionToken;
        }
        Object.assign(headers, headerOverrides);
        let debugBody = body;
        if (isGet) {
            debugBody = '(GET 请求，参数已转为 query string)';
        }
        else if (rawForm !== null) {
            debugBody = `[application/x-www-form-urlencoded, ${Buffer.byteLength(postData)} bytes]`;
        }
        else if (postData) {
            try {
                debugBody = JSON.parse(postData);
            }
            catch {
                debugBody = postData.length > 2000 ? `${postData.slice(0, 2000)}…` : postData;
            }
        }
        (0, logger_1.debugLog)('REQUEST', {
            method,
            url: fullUrl,
            headers,
            body: debugBody,
        });
        const startTime = Date.now();
        const timeoutMs = (0, http_timeout_1.getRequestTimeoutMs)();
        const req = mod.request({
            hostname: url.hostname,
            port: url.port || (url.protocol === 'https:' ? 443 : 80),
            path: `${url.pathname}${url.search}`,
            method,
            headers,
        }, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += String(chunk);
            });
            res.on('end', () => {
                if (product === 'report') {
                    const setCookies = res.headers['set-cookie'];
                    if (setCookies) {
                        for (const cookie of Array.isArray(setCookies) ? setCookies : [setCookies]) {
                            const match = cookie.match(/JSESSIONID=([^;]+)/);
                            if (match) {
                                (0, logger_1.debugLog)('REPORT COOKIE', `JSESSIONID=${match[1]} (响应返回，登录流程已自动管理)`);
                            }
                        }
                    }
                }
                const elapsed = Date.now() - startTime;
                try {
                    const parsed = product === 'cysms' ? (0, parse_cysms_json_1.parseCysmsJson)(data) : JSON.parse(data);
                    (0, logger_1.debugLog)(`RESPONSE (${res.statusCode}, ${elapsed}ms)`, {
                        statusCode: res.statusCode,
                        headers: res.headers,
                        body: JSON.stringify(parsed).length > 2000
                            ? `${JSON.stringify(parsed).substring(0, 2000)}... (truncated)`
                            : parsed,
                    });
                    const enriched = typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)
                        ? { ...parsed, _httpStatus: res.statusCode }
                        : parsed;
                    resolve(enriched);
                }
                catch {
                    (0, logger_1.debugLog)(`RESPONSE (${res.statusCode}, ${elapsed}ms, non-JSON)`, data.substring(0, 1000));
                    resolve({ raw: data, statusCode: res.statusCode });
                }
            });
        });
        req.on('error', (error) => {
            (0, logger_1.debugLog)('REQUEST ERROR', error.message);
            reject(error);
        });
        req.setTimeout(timeoutMs, () => {
            req.destroy(new Error(`请求超时（${timeoutMs}ms）: ${fullUrl}`));
        });
        if (postData) {
            req.write(postData);
        }
        req.end();
    });
}
