/**
 * MCP Tool: import-to-godot
 * 将生成的图片导入到 Godot 项目目录
 */
import { z } from 'zod';
import type { MCPTool } from '../../utils/types.js';
declare const importToGodotSchema: z.ZodObject<{
    sourcePath: z.ZodString;
    targetDir: z.ZodString;
    fileName: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    sourcePath: string;
    targetDir: string;
    fileName?: string | undefined;
}, {
    sourcePath: string;
    targetDir: string;
    fileName?: string | undefined;
}>;
type ImportToGodotArgs = z.infer<typeof importToGodotSchema>;
export declare const importToGodotTool: MCPTool<ImportToGodotArgs>;
export {};
