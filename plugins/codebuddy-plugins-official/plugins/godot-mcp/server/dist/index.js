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
import { FastMCP } from 'fastmcp';
/**
 * Godot MCP Server (4.23 重构版)
 * ──────────────────────────────────────────────────────────────────────────
 * 严格遵循 docs/需求文档/4.23.md 的分工：
 *   ✓ MCP 只暴露「对 Godot 编辑器的单元操作」门面：
 *       - build_godot_scene  : 接收完整场景树，server 端拆解为 create_node /
 *                              update_node_property / create_script / save_scene
 *                              等单元命令逐一执行
 *       - get_debug_errors / get_script_errors / get_editor_output
 *                            : 编辑器运行时的错误/日志单元查询
 *   ✗ 部署、构建、模板复制、环境探测、意图路由、active-game.json 维护、
 *     Godot 编辑器下载/启动 等所有「非编辑器单元操作」的逻辑，全部下放到
 *     skills/godot-deploy、skills/godot-new、skills/godot-dev、
 *     skills/godot-debug 中由 Agent 直接驱动 shell / 文件系统。
 *   ✗ 不再注册 godot_deploy 与 godot_dev_router —— 这两个工具违反了
 *     4.23.md「MCP 只做编辑器单元操作」的边界。
 */
import { getConnectionManager } from './utils/connection_manager.js';
import { getProjectRegistry } from './utils/project_registry.js';
import { projectTools } from './tools/project/edit.js';
import { debugTools } from './tools/debug/inspect.js';
import { aiImageTools } from './tools/ai-image/index.js';
// 资源（read-only 的编辑器/工程查询，本质也是单元操作，保留）
import { sceneListResource, sceneStructureResource, } from './resources/scene_resources.js';
import { scriptResource, scriptListResource, scriptMetadataResource, } from './resources/script_resources.js';
import { projectStructureResource, projectSettingsResource, projectResourcesResource, } from './resources/project_resources.js';
import { editorStateResource, selectedNodeResource, currentScriptResource, } from './resources/editor_resources.js';
function main() {
    return __awaiter(this, void 0, void 0, function () {
        var server, _i, projectTools_1, tool, _a, debugTools_1, tool, _b, aiImageTools_1, tool, manager, registry, projects, godot, cleanup;
        return __generator(this, function (_c) {
            console.error('Starting Godot MCP server (4.23 unit-only edition)...');
            server = new FastMCP({
                name: 'GodotMCP',
                version: '2.0.0',
            });
            // ── 唯一的「场景修改」门面 ─────────────────────────────────────────────
            // 4.23.md：「mcp对项目的修改，所有场景的修改合并为一个工具，需要传递完整的
            //           最终需要的场景树结构，然后内部用单元的方法实现」
            for (_i = 0, projectTools_1 = projectTools; _i < projectTools_1.length; _i++) {
                tool = projectTools_1[_i];
                server.addTool(tool);
            }
            // ── Debug 单元查询门面 ────────────────────────────────────────────────
            for (_a = 0, debugTools_1 = debugTools; _a < debugTools_1.length; _a++) {
                tool = debugTools_1[_a];
                server.addTool(tool);
            }
            // ── AI 生图工具（内部工具，仅供 Skill 编排调用） ──────────────────────
            for (_b = 0, aiImageTools_1 = aiImageTools; _b < aiImageTools_1.length; _b++) {
                tool = aiImageTools_1[_b];
                server.addTool(tool);
            }
            // 资源
            server.addResource(sceneListResource);
            server.addResource(scriptListResource);
            server.addResource(projectStructureResource);
            server.addResource(projectSettingsResource);
            server.addResource(projectResourcesResource);
            server.addResource(editorStateResource);
            server.addResource(selectedNodeResource);
            server.addResource(currentScriptResource);
            server.addResource(sceneStructureResource);
            server.addResource(scriptResource);
            server.addResource(scriptMetadataResource);
            manager = getConnectionManager();
            registry = getProjectRegistry();
            projects = registry.listProjects();
            if (projects.length > 0) {
                console.error("Found ".concat(projects.length, " registered project(s), connecting in background..."));
                manager.connectAll().catch(function (err) {
                    console.warn("Background connectAll failed: ".concat(err.message));
                });
            }
            else {
                try {
                    godot = manager.getConnection();
                    godot.connect().then(function () { return console.error('Successfully connected to Godot WebSocket server'); }, function (err) {
                        console.warn("Could not connect to Godot: ".concat(err.message));
                        console.warn('Will retry connection when Godot-bound commands are executed');
                    });
                }
                catch (error) {
                    console.warn("Could not initialize Godot connection: ".concat(error.message));
                }
            }
            server.start({ transportType: 'stdio' });
            console.error('Godot MCP server started');
            cleanup = function () {
                console.error('Shutting down Godot MCP server...');
                manager.disconnectAll();
                process.exit(0);
            };
            process.on('SIGINT', cleanup);
            process.on('SIGTERM', cleanup);
            return [2 /*return*/];
        });
    });
}
main().catch(function (error) {
    console.error('Failed to start Godot MCP server:', error);
    process.exit(1);
});
//# sourceMappingURL=index.js.map