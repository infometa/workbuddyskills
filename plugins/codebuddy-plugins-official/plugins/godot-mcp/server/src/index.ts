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
import {
  sceneListResource,
  sceneStructureResource,
} from './resources/scene_resources.js';
import {
  scriptResource,
  scriptListResource,
  scriptMetadataResource,
} from './resources/script_resources.js';
import {
  projectStructureResource,
  projectSettingsResource,
  projectResourcesResource,
} from './resources/project_resources.js';
import {
  editorStateResource,
  selectedNodeResource,
  currentScriptResource,
} from './resources/editor_resources.js';

async function main() {
  console.error('Starting Godot MCP server (4.23 unit-only edition)...');

  const server = new FastMCP({
    name: 'GodotMCP',
    version: '2.0.0',
  });

  // ── 唯一的「场景修改」门面 ─────────────────────────────────────────────
  // 4.23.md：「mcp对项目的修改，所有场景的修改合并为一个工具，需要传递完整的
  //           最终需要的场景树结构，然后内部用单元的方法实现」
  for (const tool of projectTools) {
    server.addTool(tool);
  }

  // ── Debug 单元查询门面 ────────────────────────────────────────────────
  for (const tool of debugTools) {
    server.addTool(tool);
  }

  // ── AI 生图工具（内部工具，仅供 Skill 编排调用） ──────────────────────
  for (const tool of aiImageTools) {
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

  // 后台连接 Godot：MCP 启动不阻塞，由 Skill 在用户用自然语言触发部署/开发时
  // 负责确认 Godot 编辑器是否已经在监听。
  const manager = getConnectionManager();
  const registry = getProjectRegistry();
  const projects = registry.listProjects();

  if (projects.length > 0) {
    console.error(
      `Found ${projects.length} registered project(s), connecting in background...`,
    );
    manager.connectAll().catch((err) => {
      console.warn(`Background connectAll failed: ${(err as Error).message}`);
    });
  } else {
    try {
      const godot = manager.getConnection();
      godot.connect().then(
        () => console.error('Successfully connected to Godot WebSocket server'),
        (err: Error) => {
          console.warn(`Could not connect to Godot: ${err.message}`);
          console.warn('Will retry connection when Godot-bound commands are executed');
        },
      );
    } catch (error) {
      console.warn(`Could not initialize Godot connection: ${(error as Error).message}`);
    }
  }

  server.start({ transportType: 'stdio' });
  console.error('Godot MCP server started');

  const cleanup = () => {
    console.error('Shutting down Godot MCP server...');
    manager.disconnectAll();
    process.exit(0);
  };
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
}

main().catch((error) => {
  console.error('Failed to start Godot MCP server:', error);
  process.exit(1);
});
