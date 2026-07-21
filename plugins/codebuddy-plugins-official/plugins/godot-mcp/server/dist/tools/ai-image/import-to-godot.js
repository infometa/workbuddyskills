/**
 * MCP Tool: import-to-godot
 * 将生成的图片导入到 Godot 项目目录
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
var importToGodotSchema = z.object({
    sourcePath: z
        .string()
        .describe('源图片的本地绝对路径'),
    targetDir: z
        .string()
        .describe('目标目录的绝对路径（Godot 项目内），如 D:/workspace/game1/assets/icons'),
    fileName: z
        .string()
        .optional()
        .describe('目标文件名（含扩展名），默认保持源文件名'),
});
export var importToGodotTool = {
    name: 'import_to_godot',
    description: '将本地图片文件复制到 Godot 项目目录中。' +
        '需要提供源图片的绝对路径和目标目录。' +
        '复制完成后 Godot 编辑器会自动 reimport 该资源。',
    parameters: importToGodotSchema,
    execute: function (args) { return __awaiter(void 0, void 0, void 0, function () {
        var sourcePath, targetDir, fileName, targetFileName, targetPath, resPath, projectGodotIndex, parts, i, candidate;
        return __generator(this, function (_a) {
            sourcePath = args.sourcePath, targetDir = args.targetDir, fileName = args.fileName;
            // 检查源文件存在
            if (!fs.existsSync(sourcePath)) {
                return [2 /*return*/, JSON.stringify({
                        error: 'SOURCE_NOT_FOUND',
                        message: "\u6E90\u6587\u4EF6\u4E0D\u5B58\u5728: ".concat(sourcePath),
                    })];
            }
            // 创建目标目录
            if (!fs.existsSync(targetDir)) {
                fs.mkdirSync(targetDir, { recursive: true });
            }
            targetFileName = fileName || path.basename(sourcePath);
            targetPath = path.join(targetDir, targetFileName);
            try {
                // 复制文件
                fs.copyFileSync(sourcePath, targetPath);
                resPath = targetPath;
                projectGodotIndex = targetPath.replace(/\\/g, '/').indexOf('/project.godot');
                if (projectGodotIndex === -1) {
                    parts = targetPath.replace(/\\/g, '/').split('/');
                    for (i = parts.length - 1; i >= 0; i--) {
                        candidate = parts.slice(0, i + 1).join('/');
                        if (fs.existsSync(path.join(candidate, 'project.godot'))) {
                            resPath = 'res://' + targetPath.replace(/\\/g, '/').substring(candidate.length + 1);
                            break;
                        }
                    }
                }
                return [2 /*return*/, JSON.stringify({
                        success: true,
                        localPath: targetPath,
                        resPath: resPath,
                        message: "\u56FE\u7247\u5DF2\u5BFC\u5165\u5230 ".concat(targetPath),
                    })];
            }
            catch (error) {
                return [2 /*return*/, JSON.stringify({
                        error: 'COPY_FAILED',
                        message: "\u590D\u5236\u6587\u4EF6\u5931\u8D25: ".concat(error.message),
                    })];
            }
            return [2 /*return*/];
        });
    }); },
};
//# sourceMappingURL=import-to-godot.js.map