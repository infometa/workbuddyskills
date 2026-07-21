/**
 * 后端 API 客户端
 * ──────────────────────────────────────────
 * 封装对代理服务的 HTTP 调用。
 *
 * 设计原则：
 *   - 插件只是「薄客户端」，所有业务决策（provider 选择、额度扣减、限流）由后端完成
 *   - 认证方式：API Key（通过 X-API-Key 请求头传递）
 *   - 不暴露任何后端内部路由结构、认证协议、Provider 类型
 */
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
// ──────────────────────────────────────────
//  内部：基础请求层（不导出）
// ──────────────────────────────────────────
/** 从 .mcp.json 读取的缓存配置 */
var _mcpConfig = null;
/**
 * 从 .mcp.json 中读取环境变量配置（fallback）
 * 当 CodeBuddy 启动 MCP server 时未正确透传环境变量时使用
 */
function loadMcpConfig() {
    var _a, _b;
    if (_mcpConfig !== null)
        return _mcpConfig;
    _mcpConfig = {};
    try {
        // 从当前文件位置向上查找 .mcp.json
        var __filename_1 = fileURLToPath(import.meta.url);
        var __dirname_1 = dirname(__filename_1);
        // server/dist/tools/ai-image/ -> 项目根 (4 级向上)
        var possiblePaths = [
            resolve(__dirname_1, '../../../../.mcp.json'), // 从 dist/tools/ai-image/ 到项目根
            resolve(__dirname_1, '../../../.mcp.json'), // 从 dist/tools/ 到项目根
            resolve(process.cwd(), '.mcp.json'), // 当前工作目录
        ];
        for (var _i = 0, possiblePaths_1 = possiblePaths; _i < possiblePaths_1.length; _i++) {
            var mcpPath = possiblePaths_1[_i];
            if (existsSync(mcpPath)) {
                var content = readFileSync(mcpPath, 'utf-8');
                var json = JSON.parse(content);
                var serverEnv = ((_b = (_a = json === null || json === void 0 ? void 0 : json.mcpServers) === null || _a === void 0 ? void 0 : _a['godot-mcp']) === null || _b === void 0 ? void 0 : _b.env) || {};
                _mcpConfig = {
                    backendUrl: serverEnv.GODOT_BACKEND_URL,
                    apiKey: serverEnv.GODOT_API_KEY,
                };
                break;
            }
        }
    }
    catch (_c) {
        // 忽略读取错误
    }
    return _mcpConfig;
}
/** 后端服务地址 */
function getBaseURL() {
    if (process.env.GODOT_BACKEND_URL)
        return process.env.GODOT_BACKEND_URL;
    return loadMcpConfig().backendUrl || 'http://localhost:8080';
}
/** 用户 API Key（由管理员分配） */
function getApiKey() {
    if (process.env.GODOT_API_KEY)
        return process.env.GODOT_API_KEY;
    return loadMcpConfig().apiKey || '';
}
/** 通用请求封装 */
function request(path_1) {
    return __awaiter(this, arguments, void 0, function (path, options) {
        var _a, method, body, extraHeaders, url, headers, apiKey, fetchOptions, response, data, error_1;
        if (options === void 0) { options = {}; }
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _a = options.method, method = _a === void 0 ? 'GET' : _a, body = options.body, extraHeaders = options.headers;
                    url = "".concat(getBaseURL()).concat(path);
                    headers = __assign({ 'Content-Type': 'application/json' }, extraHeaders);
                    apiKey = getApiKey();
                    if (apiKey) {
                        headers['X-API-Key'] = apiKey;
                    }
                    fetchOptions = { method: method, headers: headers };
                    if (body) {
                        fetchOptions.body = JSON.stringify(body);
                    }
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, fetch(url, fetchOptions)];
                case 2:
                    response = _b.sent();
                    return [4 /*yield*/, response.json()];
                case 3:
                    data = _b.sent();
                    return [2 /*return*/, { ok: response.ok, status: response.status, data: data }];
                case 4:
                    error_1 = _b.sent();
                    return [2 /*return*/, {
                            ok: false,
                            status: 0,
                            data: { error: "\u7F51\u7EDC\u9519\u8BEF: ".concat(error_1.message) },
                        }];
                case 5: return [2 /*return*/];
            }
        });
    });
}
// ──────────────────────────────────────────
//  对外导出：插件可见的 API（仅 3 个方法）
// ──────────────────────────────────────────
/**
 * 查询当前用户的剩余额度
 *
 * @returns 成功时返回 remainingQuota / totalQuota / usedQuota
 */
export function apiGetQuota() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, request('/v1/quota/balance')];
        });
    });
}
/**
 * 请求后端生成图片
 *
 * 后端自动处理：provider 路由、额度扣减、限流、日志记录
 * 插件端只需传入提示词和基本参数
 */
export function apiGenerateImage(params) {
    return __awaiter(this, void 0, void 0, function () {
        var body;
        var _a;
        return __generator(this, function (_b) {
            body = {
                prompt: params.prompt,
            };
            if (params.optimizedPrompt)
                body.optimizedPrompt = params.optimizedPrompt;
            if (params.width)
                body.width = params.width;
            if (params.height)
                body.height = params.height;
            if (params.style)
                body.style = params.style;
            if ((_a = params.referenceImages) === null || _a === void 0 ? void 0 : _a.length)
                body.imageUrls = params.referenceImages;
            return [2 /*return*/, request('/v1/image/generate', {
                    method: 'POST',
                    body: body,
                })];
        });
    });
}
/**
 * 验证 API Key 是否有效
 */
export function apiVerifyKey() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, request('/api/auth/verify', {
                    method: 'POST',
                })];
        });
    });
}
//# sourceMappingURL=api-client.js.map