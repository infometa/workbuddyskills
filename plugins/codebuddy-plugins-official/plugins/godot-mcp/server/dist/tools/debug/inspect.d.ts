import { MCPTool } from '../../utils/types.js';
/**
 * Debug group: minimal toolkit for the debug-fix loop.
 *   1. get_debug_errors    → one-shot scan of the whole project
 *   2. get_script_errors   → drill into a single script for fix details
 *   3. get_editor_output   → raw editor log tail for runtime issues
 */
export declare const debugTools: MCPTool[];
