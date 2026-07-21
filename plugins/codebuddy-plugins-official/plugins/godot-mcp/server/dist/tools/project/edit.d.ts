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
import type { MCPTool } from '../../utils/types.js';
/**
 * 对外导出的工具列表：只有 1 个门面工具。
 * 所有 internal* 函数都是模块私有，外部 Agent 看不到、无法调用。
 */
export declare const projectTools: MCPTool[];
