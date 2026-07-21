/**
 * MCP Tool: check-auth
 * 检查 API Key 配置状态
 */
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
import { z } from 'zod';
import { apiVerifyKey } from './api-client.js';
var checkAuthSchema = z.object({
    action: z
        .enum(['check', 'login-url'])
        .optional()
        .describe('check=检查当前 API Key 状态（默认）; login-url=返回配置指引'),
});
export var checkAuthTool = {
    name: 'verify_api_key',
    description: '检查用户 API Key 配置状态。返回 JSON 格式的认证状态信息，' +
        '包括是否已配置 API Key、Key 是否有效、用户名等。' +
        'action=login-url 时返回配置指引。',
    parameters: checkAuthSchema,
    execute: function (args) { return __awaiter(void 0, void 0, void 0, function () {
        var action, _a, apiKey, verifyResult, errorMsg;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    action = args.action || 'check';
                    _a = action;
                    switch (_a) {
                        case 'check': return [3 /*break*/, 1];
                        case 'login-url': return [3 /*break*/, 3];
                    }
                    return [3 /*break*/, 4];
                case 1:
                    apiKey = process.env.GODOT_API_KEY;
                    if (!apiKey) {
                        return [2 /*return*/, JSON.stringify({
                                authenticated: false,
                                message: '未配置 API Key。请在环境变量 GODOT_API_KEY 中设置您的 API Key。',
                                configGuide: '请联系管理员获取 API Key，然后在 .mcp.json 中的 env.GODOT_API_KEY 字段填入。',
                            })];
                    }
                    return [4 /*yield*/, apiVerifyKey()];
                case 2:
                    verifyResult = _b.sent();
                    if (verifyResult.ok && verifyResult.data.valid) {
                        return [2 /*return*/, JSON.stringify({
                                authenticated: true,
                                keyName: verifyResult.data.keyName,
                                role: verifyResult.data.role,
                                remainingQuota: verifyResult.data.remainingQuota,
                                totalQuota: verifyResult.data.totalQuota,
                                message: "\u5DF2\u8BA4\u8BC1\uFF1A".concat(verifyResult.data.keyName, "\uFF0C\u5269\u4F59\u989D\u5EA6 ").concat(verifyResult.data.remainingQuota),
                            })];
                    }
                    errorMsg = verifyResult.status === 401
                        ? 'API Key 无效或已过期，请联系管理员。'
                        : verifyResult.status === 403
                            ? 'API Key 已被禁用。'
                            : "\u9A8C\u8BC1\u5931\u8D25 (HTTP ".concat(verifyResult.status, ")");
                    return [2 /*return*/, JSON.stringify({
                            authenticated: false,
                            message: errorMsg,
                            configGuide: '请检查 GODOT_API_KEY 环境变量是否正确，或联系管理员获取新的 API Key。',
                        })];
                case 3:
                    {
                        return [2 /*return*/, JSON.stringify({
                                configGuide: 'API Key 认证模式无需登录 URL。请联系管理员获取 API Key，' +
                                    '然后在 .mcp.json 中的 env.GODOT_API_KEY 字段填入即可。',
                                message: '请联系管理员获取 API Key',
                            })];
                    }
                    _b.label = 4;
                case 4: throw new Error("Unknown action: ".concat(action));
            }
        });
    }); },
};
//# sourceMappingURL=check-auth.js.map