/**
 * MCP Tool: generate-image
 * 请求后端生成图片，下载到本地临时目录
 *
 * 设计原则：用户只需要提供「想要什么图」，
 * 具体用哪个模型、走哪个 provider、扣多少额度，全部由后端自动处理。
 */
import { z } from 'zod';
import type { MCPTool } from '../../utils/types.js';
declare const generateImageSchema: z.ZodObject<{
    prompt: z.ZodString;
    optimizedPrompt: z.ZodOptional<z.ZodString>;
    width: z.ZodOptional<z.ZodNumber>;
    height: z.ZodOptional<z.ZodNumber>;
    style: z.ZodOptional<z.ZodEnum<["pixel", "realistic", "anime", "watercolor", "flat"]>>;
    referenceImages: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
    outputDir: z.ZodOptional<z.ZodString>;
    fileName: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    prompt: string;
    optimizedPrompt?: string | undefined;
    width?: number | undefined;
    height?: number | undefined;
    style?: "flat" | "pixel" | "realistic" | "anime" | "watercolor" | undefined;
    referenceImages?: string[] | undefined;
    outputDir?: string | undefined;
    fileName?: string | undefined;
}, {
    prompt: string;
    optimizedPrompt?: string | undefined;
    width?: number | undefined;
    height?: number | undefined;
    style?: "flat" | "pixel" | "realistic" | "anime" | "watercolor" | undefined;
    referenceImages?: string[] | undefined;
    outputDir?: string | undefined;
    fileName?: string | undefined;
}>;
type GenerateImageArgs = z.infer<typeof generateImageSchema>;
export declare const generateImageTool: MCPTool<GenerateImageArgs>;
export {};
