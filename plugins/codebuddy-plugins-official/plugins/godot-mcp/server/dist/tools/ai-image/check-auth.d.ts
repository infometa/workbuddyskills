/**
 * MCP Tool: check-auth
 * 检查 API Key 配置状态
 */
import { z } from 'zod';
import type { MCPTool } from '../../utils/types.js';
declare const checkAuthSchema: z.ZodObject<{
    action: z.ZodOptional<z.ZodEnum<["check", "login-url"]>>;
}, "strip", z.ZodTypeAny, {
    action?: "check" | "login-url" | undefined;
}, {
    action?: "check" | "login-url" | undefined;
}>;
type CheckAuthArgs = z.infer<typeof checkAuthSchema>;
export declare const checkAuthTool: MCPTool<CheckAuthArgs>;
export {};
