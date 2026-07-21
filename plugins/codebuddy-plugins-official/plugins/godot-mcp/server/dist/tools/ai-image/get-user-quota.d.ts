/**
 * MCP Tool: get-user-quota
 * 查询当前用户剩余额度
 */
import { z } from 'zod';
import type { MCPTool } from '../../utils/types.js';
declare const getUserQuotaSchema: z.ZodObject<{}, "strict", z.ZodTypeAny, {}, {}>;
type GetUserQuotaArgs = z.infer<typeof getUserQuotaSchema>;
export declare const getUserQuotaTool: MCPTool<GetUserQuotaArgs>;
export {};
