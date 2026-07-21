/**
 * MCP Tool: generate-image
 * 请求后端生成图片，下载到本地临时目录
 *
 * 设计原则：用户只需要提供「想要什么图」，
 * 具体用哪个模型、走哪个 provider、扣多少额度，全部由后端自动处理。
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
import fs from 'fs';
import path from 'path';
import { apiGenerateImage } from './api-client.js';
var generateImageSchema = z.object({
    prompt: z.string().describe('用户原始提示词（描述想要生成的图片内容）'),
    optimizedPrompt: z
        .string()
        .optional()
        .describe('Skill 优化后的提示词（推荐传入，会替代 prompt 发送给生图服务）'),
    width: z.number().int().optional().describe('图片宽度（像素），默认由服务端决定'),
    height: z.number().int().optional().describe('图片高度（像素），默认由服务端决定'),
    style: z
        .enum(['pixel', 'realistic', 'anime', 'watercolor', 'flat'])
        .optional()
        .describe('图片风格'),
    referenceImages: z
        .array(z.string())
        .optional()
        .describe('参考图像 URL 列表（图生图时使用，最多 3 张）'),
    outputDir: z
        .string()
        .optional()
        .describe('图片保存的目录（绝对路径），默认为系统临时目录'),
    fileName: z
        .string()
        .optional()
        .describe('保存的文件名（不含扩展名），默认自动生成'),
});
export var generateImageTool = {
    name: 'generate_image',
    description: '请求后端生成 AI 图片。' +
        '自动扣减额度，失败时自动退还。' +
        '成功时返回本地图片路径和剩余额度。',
    parameters: generateImageSchema,
    execute: function (args) { return __awaiter(void 0, void 0, void 0, function () {
        var result, imageUrl, imageData, localPath, outputDir, fileName, imageResponse, imageBuffer, _a, _b, imageBuffer, downloadError_1;
        var _c, _d;
        return __generator(this, function (_e) {
            switch (_e.label) {
                case 0: return [4 /*yield*/, apiGenerateImage({
                        prompt: args.prompt,
                        optimizedPrompt: args.optimizedPrompt,
                        width: args.width,
                        height: args.height,
                        style: args.style,
                        referenceImages: args.referenceImages,
                    })];
                case 1:
                    result = _e.sent();
                    if (!result.ok) {
                        return [2 /*return*/, JSON.stringify({
                                error: ((_c = result.data) === null || _c === void 0 ? void 0 : _c.error) || 'GENERATION_FAILED',
                                message: ((_d = result.data) === null || _d === void 0 ? void 0 : _d.message) || '图片生成失败',
                            })];
                    }
                    imageUrl = result.data.imageUrl;
                    imageData = result.data.imageData;
                    localPath = '';
                    _e.label = 2;
                case 2:
                    _e.trys.push([2, 7, , 8]);
                    outputDir = args.outputDir || getTempDir();
                    if (!fs.existsSync(outputDir)) {
                        fs.mkdirSync(outputDir, { recursive: true });
                    }
                    fileName = (args.fileName || "generated_".concat(Date.now())) + '.png';
                    localPath = path.join(outputDir, fileName);
                    if (!imageUrl) return [3 /*break*/, 5];
                    return [4 /*yield*/, fetch(imageUrl)];
                case 3:
                    imageResponse = _e.sent();
                    _b = (_a = Buffer).from;
                    return [4 /*yield*/, imageResponse.arrayBuffer()];
                case 4:
                    imageBuffer = _b.apply(_a, [_e.sent()]);
                    fs.writeFileSync(localPath, imageBuffer);
                    return [3 /*break*/, 6];
                case 5:
                    if (imageData) {
                        imageBuffer = Buffer.from(imageData, 'base64');
                        fs.writeFileSync(localPath, imageBuffer);
                    }
                    else {
                        return [2 /*return*/, JSON.stringify({
                                status: 'SUCCESS',
                                localPath: null,
                                durationMs: result.data.durationMs,
                                message: '图片已生成但未返回图片数据',
                            })];
                    }
                    _e.label = 6;
                case 6: return [3 /*break*/, 8];
                case 7:
                    downloadError_1 = _e.sent();
                    // 下载/保存失败但图片已生成
                    return [2 /*return*/, JSON.stringify({
                            status: 'SUCCESS',
                            localPath: null,
                            downloadError: downloadError_1.message,
                            durationMs: result.data.durationMs,
                            message: "\u56FE\u7247\u5DF2\u751F\u6210\u4F46\u4FDD\u5B58\u5230\u672C\u5730\u5931\u8D25",
                        })];
                case 8: return [2 /*return*/, JSON.stringify({
                        status: 'SUCCESS',
                        localPath: localPath,
                        durationMs: result.data.durationMs,
                        revisedPrompt: result.data.revisedPrompt,
                        costQuota: result.data.costQuota,
                        remainingQuota: result.data.remainingQuota,
                        message: "\u56FE\u7247\u5DF2\u751F\u6210\u5E76\u4E0B\u8F7D\u5230 ".concat(localPath),
                    })];
            }
        });
    }); },
};
function getTempDir() {
    var base = process.env.CODEBUDDY_PLUGIN_DATA ||
        process.env.CLAUDE_PLUGIN_DATA ||
        path.join(process.env.HOME || process.env.USERPROFILE || '.', '.godot-mcp');
    return path.join(base, 'generated-images');
}
//# sourceMappingURL=generate-image.js.map