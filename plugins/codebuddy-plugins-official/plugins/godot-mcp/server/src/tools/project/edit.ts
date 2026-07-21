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

import { z } from 'zod';
import { getGodotConnection } from '../../utils/godot_connection.js';
import type { MCPTool, CommandResult } from '../../utils/types.js';

// ---------------------------------------------------------------------------
// Public schema (exposed to the Agent)
// ---------------------------------------------------------------------------

interface NodeSpec {
  name: string;
  type: string;
  properties?: Record<string, unknown>;
  script?: { path: string; content: string };
  children?: NodeSpec[];
}

// 递归 zod schema（使用 z.lazy 处理 children）
const nodeSpecSchema: z.ZodType<NodeSpec> = z.lazy(() =>
  z
    .object({
      name: z.string().describe('节点名（在父节点下唯一）'),
      type: z
        .string()
        .describe('Godot 节点类型，例如 Node2D / Sprite2D / CharacterBody2D / Camera2D / Control'),
      properties: z
        .record(z.any())
        .optional()
        .describe(
          '可选的节点属性。Vector2 用 [x,y]；Vector3 用 [x,y,z]；Color 用 [r,g,b,a] (0-1)；rotation 单位为弧度',
        ),
      script: z
        .object({
          path: z.string().describe('脚本资源路径，如 res://scripts/player.gd'),
          content: z.string().describe('完整 GDScript 内容'),
        })
        .optional()
        .describe('可选：创建脚本并附着到该节点'),
      children: z.array(nodeSpecSchema).optional().describe('子节点列表（递归）'),
    })
    .strict(),
);

const buildSceneSchema = z
  .object({
    scenePath: z
      .string()
      .describe('场景保存路径，必须以 res:// 开头并以 .tscn 结尾，例如 res://scenes/main.tscn'),
    root: nodeSpecSchema.describe(
      '场景根节点完整规格，包含类型、属性、脚本、子节点。整棵场景树会被一次性创建',
    ),
    saveAfter: z.boolean().optional().describe('构建完成后是否调用 save_scene，默认 true'),
    openInEditor: z
      .boolean()
      .optional()
      .describe('构建完成后是否在编辑器里打开该场景，默认 true'),
    project: z.string().optional().describe('目标项目名（多项目场景下使用，默认 active 项目）'),
  })
  .strict();

type BuildSceneArgs = z.infer<typeof buildSceneSchema>;

// ---------------------------------------------------------------------------
// Internal step functions (NOT registered as MCP tools)
// ---------------------------------------------------------------------------

interface StepLog {
  ok: boolean;
  action: string;
  target: string;
  message: string;
}

async function internalCreateScene(
  godot: ReturnType<typeof getGodotConnection>,
  scenePath: string,
  rootType: string,
): Promise<{ scenePath: string; rootName: string }> {
  const r = await godot.sendCommand<CommandResult>('create_scene', {
    path: scenePath,
    root_node_type: rootType,
  });
  // Godot 端 create_scene 返回的根节点名通常等于场景文件 basename（去扩展名）
  const fallbackRootName =
    scenePath
      .split('/')
      .pop()
      ?.replace(/\.tscn$/, '') ?? 'Root';
  return {
    scenePath: (r.scene_path as string) ?? scenePath,
    rootName: (r.root_node_name as string) ?? fallbackRootName,
  };
}

async function internalRenameRootIfNeeded(
  godot: ReturnType<typeof getGodotConnection>,
  currentRootPath: string,
  desiredName: string,
  logs: StepLog[],
): Promise<string> {
  const currentName = currentRootPath.split('/').pop() ?? '';
  if (currentName === desiredName) return currentRootPath;
  // Godot 端通过 update_node_property 改 name 即可重命名
  try {
    await godot.sendCommand('update_node_property', {
      node_path: currentRootPath,
      property: 'name',
      value: desiredName,
    });
    const newPath = currentRootPath.replace(/[^/]+$/, desiredName);
    logs.push({
      ok: true,
      action: 'rename_root',
      target: currentRootPath,
      message: `根节点重命名为 "${desiredName}"`,
    });
    return newPath;
  } catch (err) {
    logs.push({
      ok: false,
      action: 'rename_root',
      target: currentRootPath,
      message: `根节点重命名失败：${(err as Error).message}（保留原名继续）`,
    });
    return currentRootPath;
  }
}

async function internalApplyProperties(
  godot: ReturnType<typeof getGodotConnection>,
  nodePath: string,
  properties: Record<string, unknown> | undefined,
  logs: StepLog[],
): Promise<void> {
  if (!properties) return;
  for (const [property, value] of Object.entries(properties)) {
    try {
      await godot.sendCommand('update_node_property', { node_path: nodePath, property, value });
      logs.push({
        ok: true,
        action: 'set_property',
        target: nodePath,
        message: `${property} = ${JSON.stringify(value)}`,
      });
    } catch (err) {
      logs.push({
        ok: false,
        action: 'set_property',
        target: nodePath,
        message: `设置 ${property} 失败：${(err as Error).message}`,
      });
    }
  }
}

async function internalAttachScript(
  godot: ReturnType<typeof getGodotConnection>,
  nodePath: string,
  script: { path: string; content: string } | undefined,
  logs: StepLog[],
): Promise<void> {
  if (!script) return;
  try {
    await godot.sendCommand<CommandResult>('create_script', {
      script_path: script.path,
      content: script.content,
      node_path: nodePath,
    });
    logs.push({
      ok: true,
      action: 'attach_script',
      target: nodePath,
      message: `已创建并附着脚本 ${script.path}`,
    });
  } catch (err) {
    logs.push({
      ok: false,
      action: 'attach_script',
      target: nodePath,
      message: `脚本附着失败 (${script.path})：${(err as Error).message}`,
    });
  }
}

async function internalCreateChild(
  godot: ReturnType<typeof getGodotConnection>,
  parentPath: string,
  spec: NodeSpec,
  logs: StepLog[],
): Promise<string | null> {
  try {
    const r = await godot.sendCommand<CommandResult>('create_node', {
      parent_path: parentPath,
      node_type: spec.type,
      node_name: spec.name,
    });
    const childPath = (r.node_path as string) ?? `${parentPath}/${spec.name}`;
    logs.push({
      ok: true,
      action: 'create_node',
      target: childPath,
      message: `创建 ${spec.type} "${spec.name}"`,
    });
    return childPath;
  } catch (err) {
    logs.push({
      ok: false,
      action: 'create_node',
      target: `${parentPath}/${spec.name}`,
      message: `创建节点失败：${(err as Error).message}`,
    });
    return null;
  }
}

/**
 * 递归构建子树：先创建当前节点 → 设置属性 → 附着脚本 → 递归创建子节点
 * 注意：根节点由 create_scene 自动创建，不走这个函数，从 children 开始才走。
 */
async function internalBuildSubtree(
  godot: ReturnType<typeof getGodotConnection>,
  parentPath: string,
  spec: NodeSpec,
  logs: StepLog[],
): Promise<void> {
  const childPath = await internalCreateChild(godot, parentPath, spec, logs);
  if (!childPath) return; // 创建失败时跳过该子树（已记录日志）
  await internalApplyProperties(godot, childPath, spec.properties, logs);
  await internalAttachScript(godot, childPath, spec.script, logs);
  if (spec.children?.length) {
    for (const child of spec.children) {
      await internalBuildSubtree(godot, childPath, child, logs);
    }
  }
}

async function internalSaveScene(
  godot: ReturnType<typeof getGodotConnection>,
  scenePath: string,
  logs: StepLog[],
): Promise<void> {
  try {
    await godot.sendCommand('save_scene', { path: scenePath });
    logs.push({ ok: true, action: 'save_scene', target: scenePath, message: '场景已保存' });
  } catch (err) {
    logs.push({
      ok: false,
      action: 'save_scene',
      target: scenePath,
      message: `保存失败：${(err as Error).message}`,
    });
  }
}

async function internalOpenScene(
  godot: ReturnType<typeof getGodotConnection>,
  scenePath: string,
  logs: StepLog[],
): Promise<void> {
  try {
    await godot.sendCommand('open_scene', { path: scenePath });
    logs.push({ ok: true, action: 'open_scene', target: scenePath, message: '场景已在编辑器打开' });
  } catch (err) {
    logs.push({
      ok: false,
      action: 'open_scene',
      target: scenePath,
      message: `打开失败：${(err as Error).message}`,
    });
  }
}

// ---------------------------------------------------------------------------
// Report formatter
// ---------------------------------------------------------------------------

function buildReport(scenePath: string, rootPath: string, logs: StepLog[]): string {
  const total = logs.length;
  const failed = logs.filter(l => !l.ok).length;
  const header =
    failed === 0
      ? `✓ 场景构建完成：${scenePath}\n  根节点：${rootPath}\n  共 ${total} 步全部成功。`
      : `✗ 场景构建部分失败：${scenePath}\n  根节点：${rootPath}\n  共 ${total} 步，其中 ${failed} 步失败。`;
  const lines = logs.map(l => `  ${l.ok ? '✓' : '✗'} [${l.action}] ${l.target} — ${l.message}`);
  return `${header}\n${lines.join('\n')}`;
}

// ---------------------------------------------------------------------------
// Public facade tool — the ONLY thing exported from this module
// ---------------------------------------------------------------------------

const buildGodotSceneTool: MCPTool<BuildSceneArgs> = {
  name: 'build_godot_scene',
  description:
    '【场景构建门面】根据声明式的场景树规格，一次性创建完整的 Godot 场景：' +
    '内部按顺序自动执行 create_scene → 重命名根节点 → 应用根节点属性/脚本 → ' +
    '递归创建所有子节点 → 设置属性 → 附着脚本 → 可选 save_scene + open_scene。' +
    '调用方只需要给一个声明式的 root 树（包含 name/type/properties/script/children），' +
    '不需要再分多次调用 create_node / update_node_property / create_script / save_scene。' +
    '【前置条件】工作区已有 project.godot，并且 Godot 编辑器正在运行且已启用 GodotMCP 插件。' +
    '若任何子步骤失败，会继续完成其他可独立的步骤，并在返回的 report 中标注每一步的成败。',
  parameters: buildSceneSchema,
  execute: async (args: BuildSceneArgs): Promise<string> => {
    const { scenePath, root, saveAfter = true, openInEditor = true, project } = args;

    if (!scenePath.startsWith('res://') || !scenePath.endsWith('.tscn')) {
      throw new Error(
        `scenePath 必须以 res:// 开头并以 .tscn 结尾，当前值：${scenePath}`,
      );
    }

    const godot = getGodotConnection(project);
    const logs: StepLog[] = [];

    // Step 1: 创建场景（根节点由 Godot 端自动创建为 root.type）
    let rootPath: string;
    try {
      const created = await internalCreateScene(godot, scenePath, root.type);
      rootPath = `/root/${created.rootName}`;
      logs.push({
        ok: true,
        action: 'create_scene',
        target: created.scenePath,
        message: `已创建场景，根节点 ${created.rootName} (${root.type})`,
      });
    } catch (err) {
      throw new Error(`build_godot_scene 失败：create_scene 阶段无法继续 — ${(err as Error).message}`);
    }

    // Step 2: 根节点重命名（如需要）+ 属性 + 脚本
    rootPath = await internalRenameRootIfNeeded(godot, rootPath, root.name, logs);
    await internalApplyProperties(godot, rootPath, root.properties, logs);
    await internalAttachScript(godot, rootPath, root.script, logs);

    // Step 3: 递归创建所有子树
    if (root.children?.length) {
      for (const child of root.children) {
        await internalBuildSubtree(godot, rootPath, child, logs);
      }
    }

    // Step 4: 可选保存
    if (saveAfter) {
      await internalSaveScene(godot, scenePath, logs);
    }

    // Step 5: 可选在编辑器里打开
    if (openInEditor) {
      await internalOpenScene(godot, scenePath, logs);
    }

    return buildReport(scenePath, rootPath, logs);
  },
};

/**
 * 对外导出的工具列表：只有 1 个门面工具。
 * 所有 internal* 函数都是模块私有，外部 Agent 看不到、无法调用。
 */
export const projectTools: MCPTool[] = [buildGodotSceneTool];
