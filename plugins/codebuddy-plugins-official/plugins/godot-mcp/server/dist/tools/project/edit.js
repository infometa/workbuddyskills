/**
 * Godot 场景一键构建门面工具（Scene Builder Facade）
 *
 * ⚠️ 设计原则（参考 docs/概念梳理/mcp的非完全披露方法.md
 *                 与 docs/概念梳理/mcp工具数量过多后的处理方案.md）：
 *   - 原来散落的 operate_node / operate_script / operate_scene / run_project /
 *     get_project_info / scan_project_modules 等工具，全部下沉为模块私有的
 *     internal* 函数，**不注册为 MCP 工具**，外部 Agent 完全看不到。
 *   - 仅对外暴露 1 个门面工具 `build_godot_scene`，接收声明式的场景树规格，
 *     在 server 端一次性按层级创建：场景 → 嵌套节点 → 设置属性 → 附着脚本 → 保存。
 *   - 这样把"几十次小工具调用 + AI 自己编排顺序"的脆弱流程，
 *     收敛成"一次结构化输入 + server 端确定性构建"的稳定流程。
 *
 * 对外门面：
 *   build_godot_scene({ scenePath, root, saveAfter?, openInEditor?, project? })
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
import { getGodotConnection } from '../../utils/godot_connection.js';
// 递归 zod schema（使用 z.lazy 处理 children）
var nodeSpecSchema = z.lazy(function () {
    return z
        .object({
        name: z.string().describe('节点名（在父节点下唯一）'),
        type: z
            .string()
            .describe('Godot 节点类型，例如 Node2D / Sprite2D / CharacterBody2D / Camera2D / Control'),
        properties: z
            .record(z.any())
            .optional()
            .describe('可选的节点属性。Vector2 用 [x,y]；Vector3 用 [x,y,z]；Color 用 [r,g,b,a] (0-1)；rotation 单位为弧度'),
        script: z
            .object({
            path: z.string().describe('脚本资源路径，如 res://scripts/player.gd'),
            content: z.string().describe('完整 GDScript 内容'),
        })
            .optional()
            .describe('可选：创建脚本并附着到该节点'),
        children: z.array(nodeSpecSchema).optional().describe('子节点列表（递归）'),
    })
        .strict();
});
var buildSceneSchema = z
    .object({
    scenePath: z
        .string()
        .describe('场景保存路径，必须以 res:// 开头并以 .tscn 结尾，例如 res://scenes/main.tscn'),
    root: nodeSpecSchema.describe('场景根节点完整规格，包含类型、属性、脚本、子节点。整棵场景树会被一次性创建'),
    saveAfter: z.boolean().optional().describe('构建完成后是否调用 save_scene，默认 true'),
    openInEditor: z
        .boolean()
        .optional()
        .describe('构建完成后是否在编辑器里打开该场景，默认 true'),
    project: z.string().optional().describe('目标项目名（多项目场景下使用，默认 active 项目）'),
})
    .strict();
function internalCreateScene(godot, scenePath, rootType) {
    return __awaiter(this, void 0, void 0, function () {
        var r, fallbackRootName;
        var _a, _b, _c, _d;
        return __generator(this, function (_e) {
            switch (_e.label) {
                case 0: return [4 /*yield*/, godot.sendCommand('create_scene', {
                        path: scenePath,
                        root_node_type: rootType,
                    })];
                case 1:
                    r = _e.sent();
                    fallbackRootName = (_b = (_a = scenePath
                        .split('/')
                        .pop()) === null || _a === void 0 ? void 0 : _a.replace(/\.tscn$/, '')) !== null && _b !== void 0 ? _b : 'Root';
                    return [2 /*return*/, {
                            scenePath: (_c = r.scene_path) !== null && _c !== void 0 ? _c : scenePath,
                            rootName: (_d = r.root_node_name) !== null && _d !== void 0 ? _d : fallbackRootName,
                        }];
            }
        });
    });
}
function internalRenameRootIfNeeded(godot, currentRootPath, desiredName, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var currentName, newPath, err_1;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    currentName = (_a = currentRootPath.split('/').pop()) !== null && _a !== void 0 ? _a : '';
                    if (currentName === desiredName)
                        return [2 /*return*/, currentRootPath];
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, godot.sendCommand('update_node_property', {
                            node_path: currentRootPath,
                            property: 'name',
                            value: desiredName,
                        })];
                case 2:
                    _b.sent();
                    newPath = currentRootPath.replace(/[^/]+$/, desiredName);
                    logs.push({
                        ok: true,
                        action: 'rename_root',
                        target: currentRootPath,
                        message: "\u6839\u8282\u70B9\u91CD\u547D\u540D\u4E3A \"".concat(desiredName, "\""),
                    });
                    return [2 /*return*/, newPath];
                case 3:
                    err_1 = _b.sent();
                    logs.push({
                        ok: false,
                        action: 'rename_root',
                        target: currentRootPath,
                        message: "\u6839\u8282\u70B9\u91CD\u547D\u540D\u5931\u8D25\uFF1A".concat(err_1.message, "\uFF08\u4FDD\u7559\u539F\u540D\u7EE7\u7EED\uFF09"),
                    });
                    return [2 /*return*/, currentRootPath];
                case 4: return [2 /*return*/];
            }
        });
    });
}
function internalApplyProperties(godot, nodePath, properties, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var _i, _a, _b, property, value, err_2;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    if (!properties)
                        return [2 /*return*/];
                    _i = 0, _a = Object.entries(properties);
                    _c.label = 1;
                case 1:
                    if (!(_i < _a.length)) return [3 /*break*/, 6];
                    _b = _a[_i], property = _b[0], value = _b[1];
                    _c.label = 2;
                case 2:
                    _c.trys.push([2, 4, , 5]);
                    return [4 /*yield*/, godot.sendCommand('update_node_property', { node_path: nodePath, property: property, value: value })];
                case 3:
                    _c.sent();
                    logs.push({
                        ok: true,
                        action: 'set_property',
                        target: nodePath,
                        message: "".concat(property, " = ").concat(JSON.stringify(value)),
                    });
                    return [3 /*break*/, 5];
                case 4:
                    err_2 = _c.sent();
                    logs.push({
                        ok: false,
                        action: 'set_property',
                        target: nodePath,
                        message: "\u8BBE\u7F6E ".concat(property, " \u5931\u8D25\uFF1A").concat(err_2.message),
                    });
                    return [3 /*break*/, 5];
                case 5:
                    _i++;
                    return [3 /*break*/, 1];
                case 6: return [2 /*return*/];
            }
        });
    });
}
function internalAttachScript(godot, nodePath, script, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var err_3;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!script)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, godot.sendCommand('create_script', {
                            script_path: script.path,
                            content: script.content,
                            node_path: nodePath,
                        })];
                case 2:
                    _a.sent();
                    logs.push({
                        ok: true,
                        action: 'attach_script',
                        target: nodePath,
                        message: "\u5DF2\u521B\u5EFA\u5E76\u9644\u7740\u811A\u672C ".concat(script.path),
                    });
                    return [3 /*break*/, 4];
                case 3:
                    err_3 = _a.sent();
                    logs.push({
                        ok: false,
                        action: 'attach_script',
                        target: nodePath,
                        message: "\u811A\u672C\u9644\u7740\u5931\u8D25 (".concat(script.path, ")\uFF1A").concat(err_3.message),
                    });
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    });
}
function internalCreateChild(godot, parentPath, spec, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var r, childPath, err_4;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _b.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, godot.sendCommand('create_node', {
                            parent_path: parentPath,
                            node_type: spec.type,
                            node_name: spec.name,
                        })];
                case 1:
                    r = _b.sent();
                    childPath = (_a = r.node_path) !== null && _a !== void 0 ? _a : "".concat(parentPath, "/").concat(spec.name);
                    logs.push({
                        ok: true,
                        action: 'create_node',
                        target: childPath,
                        message: "\u521B\u5EFA ".concat(spec.type, " \"").concat(spec.name, "\""),
                    });
                    return [2 /*return*/, childPath];
                case 2:
                    err_4 = _b.sent();
                    logs.push({
                        ok: false,
                        action: 'create_node',
                        target: "".concat(parentPath, "/").concat(spec.name),
                        message: "\u521B\u5EFA\u8282\u70B9\u5931\u8D25\uFF1A".concat(err_4.message),
                    });
                    return [2 /*return*/, null];
                case 3: return [2 /*return*/];
            }
        });
    });
}
/**
 * 递归构建子树：先创建当前节点 → 设置属性 → 附着脚本 → 递归创建子节点
 * 注意：根节点由 create_scene 自动创建，不走这个函数，从 children 开始才走。
 */
function internalBuildSubtree(godot, parentPath, spec, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var childPath, _i, _a, child;
        var _b;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: return [4 /*yield*/, internalCreateChild(godot, parentPath, spec, logs)];
                case 1:
                    childPath = _c.sent();
                    if (!childPath)
                        return [2 /*return*/]; // 创建失败时跳过该子树（已记录日志）
                    return [4 /*yield*/, internalApplyProperties(godot, childPath, spec.properties, logs)];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, internalAttachScript(godot, childPath, spec.script, logs)];
                case 3:
                    _c.sent();
                    if (!((_b = spec.children) === null || _b === void 0 ? void 0 : _b.length)) return [3 /*break*/, 7];
                    _i = 0, _a = spec.children;
                    _c.label = 4;
                case 4:
                    if (!(_i < _a.length)) return [3 /*break*/, 7];
                    child = _a[_i];
                    return [4 /*yield*/, internalBuildSubtree(godot, childPath, child, logs)];
                case 5:
                    _c.sent();
                    _c.label = 6;
                case 6:
                    _i++;
                    return [3 /*break*/, 4];
                case 7: return [2 /*return*/];
            }
        });
    });
}
function internalSaveScene(godot, scenePath, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var err_5;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, godot.sendCommand('save_scene', { path: scenePath })];
                case 1:
                    _a.sent();
                    logs.push({ ok: true, action: 'save_scene', target: scenePath, message: '场景已保存' });
                    return [3 /*break*/, 3];
                case 2:
                    err_5 = _a.sent();
                    logs.push({
                        ok: false,
                        action: 'save_scene',
                        target: scenePath,
                        message: "\u4FDD\u5B58\u5931\u8D25\uFF1A".concat(err_5.message),
                    });
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function internalOpenScene(godot, scenePath, logs) {
    return __awaiter(this, void 0, void 0, function () {
        var err_6;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, godot.sendCommand('open_scene', { path: scenePath })];
                case 1:
                    _a.sent();
                    logs.push({ ok: true, action: 'open_scene', target: scenePath, message: '场景已在编辑器打开' });
                    return [3 /*break*/, 3];
                case 2:
                    err_6 = _a.sent();
                    logs.push({
                        ok: false,
                        action: 'open_scene',
                        target: scenePath,
                        message: "\u6253\u5F00\u5931\u8D25\uFF1A".concat(err_6.message),
                    });
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
// ---------------------------------------------------------------------------
// Report formatter
// ---------------------------------------------------------------------------
function buildReport(scenePath, rootPath, logs) {
    var total = logs.length;
    var failed = logs.filter(function (l) { return !l.ok; }).length;
    var header = failed === 0
        ? "\u2713 \u573A\u666F\u6784\u5EFA\u5B8C\u6210\uFF1A".concat(scenePath, "\n  \u6839\u8282\u70B9\uFF1A").concat(rootPath, "\n  \u5171 ").concat(total, " \u6B65\u5168\u90E8\u6210\u529F\u3002")
        : "\u2717 \u573A\u666F\u6784\u5EFA\u90E8\u5206\u5931\u8D25\uFF1A".concat(scenePath, "\n  \u6839\u8282\u70B9\uFF1A").concat(rootPath, "\n  \u5171 ").concat(total, " \u6B65\uFF0C\u5176\u4E2D ").concat(failed, " \u6B65\u5931\u8D25\u3002");
    var lines = logs.map(function (l) { return "  ".concat(l.ok ? '✓' : '✗', " [").concat(l.action, "] ").concat(l.target, " \u2014 ").concat(l.message); });
    return "".concat(header, "\n").concat(lines.join('\n'));
}
// ---------------------------------------------------------------------------
// Public facade tool — the ONLY thing exported from this module
// ---------------------------------------------------------------------------
var buildGodotSceneTool = {
    name: 'build_godot_scene',
    description: '【场景构建门面】根据声明式的场景树规格，一次性创建完整的 Godot 场景：' +
        '内部按顺序自动执行 create_scene → 重命名根节点 → 应用根节点属性/脚本 → ' +
        '递归创建所有子节点 → 设置属性 → 附着脚本 → 可选 save_scene + open_scene。' +
        '调用方只需要给一个声明式的 root 树（包含 name/type/properties/script/children），' +
        '不需要再分多次调用 create_node / update_node_property / create_script / save_scene。' +
        '【前置条件】工作区已有 project.godot，并且 Godot 编辑器正在运行且已启用 GodotMCP 插件。' +
        '若任何子步骤失败，会继续完成其他可独立的步骤，并在返回的 report 中标注每一步的成败。',
    parameters: buildSceneSchema,
    execute: function (args) { return __awaiter(void 0, void 0, void 0, function () {
        var scenePath, root, _a, saveAfter, _b, openInEditor, project, godot, logs, rootPath, created, err_7, _i, _c, child;
        var _d;
        return __generator(this, function (_e) {
            switch (_e.label) {
                case 0:
                    scenePath = args.scenePath, root = args.root, _a = args.saveAfter, saveAfter = _a === void 0 ? true : _a, _b = args.openInEditor, openInEditor = _b === void 0 ? true : _b, project = args.project;
                    if (!scenePath.startsWith('res://') || !scenePath.endsWith('.tscn')) {
                        throw new Error("scenePath \u5FC5\u987B\u4EE5 res:// \u5F00\u5934\u5E76\u4EE5 .tscn \u7ED3\u5C3E\uFF0C\u5F53\u524D\u503C\uFF1A".concat(scenePath));
                    }
                    godot = getGodotConnection(project);
                    logs = [];
                    _e.label = 1;
                case 1:
                    _e.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, internalCreateScene(godot, scenePath, root.type)];
                case 2:
                    created = _e.sent();
                    rootPath = "/root/".concat(created.rootName);
                    logs.push({
                        ok: true,
                        action: 'create_scene',
                        target: created.scenePath,
                        message: "\u5DF2\u521B\u5EFA\u573A\u666F\uFF0C\u6839\u8282\u70B9 ".concat(created.rootName, " (").concat(root.type, ")"),
                    });
                    return [3 /*break*/, 4];
                case 3:
                    err_7 = _e.sent();
                    throw new Error("build_godot_scene \u5931\u8D25\uFF1Acreate_scene \u9636\u6BB5\u65E0\u6CD5\u7EE7\u7EED \u2014 ".concat(err_7.message));
                case 4: return [4 /*yield*/, internalRenameRootIfNeeded(godot, rootPath, root.name, logs)];
                case 5:
                    // Step 2: 根节点重命名（如需要）+ 属性 + 脚本
                    rootPath = _e.sent();
                    return [4 /*yield*/, internalApplyProperties(godot, rootPath, root.properties, logs)];
                case 6:
                    _e.sent();
                    return [4 /*yield*/, internalAttachScript(godot, rootPath, root.script, logs)];
                case 7:
                    _e.sent();
                    if (!((_d = root.children) === null || _d === void 0 ? void 0 : _d.length)) return [3 /*break*/, 11];
                    _i = 0, _c = root.children;
                    _e.label = 8;
                case 8:
                    if (!(_i < _c.length)) return [3 /*break*/, 11];
                    child = _c[_i];
                    return [4 /*yield*/, internalBuildSubtree(godot, rootPath, child, logs)];
                case 9:
                    _e.sent();
                    _e.label = 10;
                case 10:
                    _i++;
                    return [3 /*break*/, 8];
                case 11:
                    if (!saveAfter) return [3 /*break*/, 13];
                    return [4 /*yield*/, internalSaveScene(godot, scenePath, logs)];
                case 12:
                    _e.sent();
                    _e.label = 13;
                case 13:
                    if (!openInEditor) return [3 /*break*/, 15];
                    return [4 /*yield*/, internalOpenScene(godot, scenePath, logs)];
                case 14:
                    _e.sent();
                    _e.label = 15;
                case 15: return [2 /*return*/, buildReport(scenePath, rootPath, logs)];
            }
        });
    }); },
};
/**
 * 对外导出的工具列表：只有 1 个门面工具。
 * 所有 internal* 函数都是模块私有，外部 Agent 看不到、无法调用。
 */
export var projectTools = [buildGodotSceneTool];
//# sourceMappingURL=edit.js.map