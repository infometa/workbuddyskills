/**
 * MCP Tool: get-user-quota
 * 查询当前用户剩余额度
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
import { apiGetQuota } from './api-client.js';
var getUserQuotaSchema = z.object({}).strict();
export var getUserQuotaTool = {
    name: 'query_quota',
    description: '查询当前用户的剩余生图额度。' +
        '返回 totalQuota（总额度）、usedQuota（已使用）、remainingQuota（剩余）。',
    parameters: getUserQuotaSchema,
    execute: function (_args) { return __awaiter(void 0, void 0, void 0, function () {
        var result, remaining, total;
        var _a, _b, _c;
        return __generator(this, function (_d) {
            switch (_d.label) {
                case 0: return [4 /*yield*/, apiGetQuota()];
                case 1:
                    result = _d.sent();
                    if (!result.ok) {
                        if (result.status === 401) {
                            return [2 /*return*/, JSON.stringify({
                                    error: 'AUTH_REQUIRED',
                                    message: 'API Key 无效或未配置，请检查 GODOT_API_KEY 环境变量',
                                })];
                        }
                        if (result.status === 403) {
                            return [2 /*return*/, JSON.stringify({
                                    error: 'KEY_DISABLED',
                                    message: 'API Key 已被禁用，请联系管理员',
                                })];
                        }
                        if (result.status === 402) {
                            return [2 /*return*/, JSON.stringify({
                                    error: 'INSUFFICIENT_QUOTA',
                                    message: '额度不足，请联系管理员增加额度',
                                    remainingQuota: 0,
                                })];
                        }
                        return [2 /*return*/, JSON.stringify({
                                error: 'SERVICE_ERROR',
                                message: '查询额度失败，请稍后重试',
                            })];
                    }
                    remaining = (_a = result.data.remainingQuota) !== null && _a !== void 0 ? _a : 0;
                    total = (_b = result.data.totalQuota) !== null && _b !== void 0 ? _b : 0;
                    return [2 /*return*/, JSON.stringify({
                            totalQuota: total,
                            usedQuota: (_c = result.data.usedQuota) !== null && _c !== void 0 ? _c : 0,
                            remainingQuota: remaining,
                            sufficient: remaining >= 1,
                            message: remaining >= 1
                                ? "\u5269\u4F59\u989D\u5EA6\uFF1A".concat(remaining, "/").concat(total)
                                : '额度不足，请联系管理员申请更多额度',
                        })];
            }
        });
    }); },
};
//# sourceMappingURL=get-user-quota.js.map