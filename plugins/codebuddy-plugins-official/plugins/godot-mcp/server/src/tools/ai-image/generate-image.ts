/**
 * MCP Tool: generate-image
 * 请求后端生成图片，下载到本地临时目录
 *
 * 设计原则：用户只需要提供「想要什么图」，
 * 具体用哪个模型、走哪个 provider、扣多少额度，全部由后端自动处理。
 */

import { z } from 'zod';
import fs from 'fs';
import path from 'path';
import type { MCPTool } from '../../utils/types.js';
import { apiGenerateImage } from './api-client.js';

const generateImageSchema = z.object({
  prompt: z.string().describe('用户原始提示词（描述想要生成的图片内容）'),
  optimizedPrompt: z
    .string()
    .optional()
    .describe('Skill 优化后的提示词（推荐传入，会替代 prompt 发送给生图服务）'),
  width: z.number().int().optional().describe('图片宽度（像素），默认由服务端决定'),
  height: z.number().int().optional().describe('图片高度（像素），默认由服务端决定'),
  style: z
    .enum(['pixel', 'realistic', 'anime', 'watercolor', 'flat'])
    .optional()
    .describe('图片风格'),
  referenceImages: z
    .array(z.string())
    .optional()
    .describe('参考图像 URL 列表（图生图时使用，最多 3 张）'),
  outputDir: z
    .string()
    .optional()
    .describe('图片保存的目录（绝对路径），默认为系统临时目录'),
  fileName: z
    .string()
    .optional()
    .describe('保存的文件名（不含扩展名），默认自动生成'),
});

type GenerateImageArgs = z.infer<typeof generateImageSchema>;

export const generateImageTool: MCPTool<GenerateImageArgs> = {
  name: 'generate_image',
  description:
    '请求后端生成 AI 图片。' +
    '自动扣减额度，失败时自动退还。' +
    '成功时返回本地图片路径和剩余额度。',
  parameters: generateImageSchema,
  execute: async (args: GenerateImageArgs): Promise<string> => {
    // 请求后端生图
    const result = await apiGenerateImage({
      prompt: args.prompt,
      optimizedPrompt: args.optimizedPrompt,
      width: args.width,
      height: args.height,
      style: args.style,
      referenceImages: args.referenceImages,
    });

    if (!result.ok) {
      return JSON.stringify({
        error: result.data?.error || 'GENERATION_FAILED',
        message: result.data?.message || '图片生成失败',
      });
    }

    // 获取图片 URL 或 base64 数据
    const imageUrl = result.data.imageUrl;
    const imageData = result.data.imageData;
    let localPath = '';

    try {
      const outputDir = args.outputDir || getTempDir();
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      const fileName =
        (args.fileName || `generated_${Date.now()}`) + '.png';
      localPath = path.join(outputDir, fileName);

      if (imageUrl) {
        // 从 URL 下载图片
        const imageResponse = await fetch(imageUrl);
        const imageBuffer = Buffer.from(await imageResponse.arrayBuffer());
        fs.writeFileSync(localPath, imageBuffer);
      } else if (imageData) {
        // 从 base64 数据保存图片
        const imageBuffer = Buffer.from(imageData, 'base64');
        fs.writeFileSync(localPath, imageBuffer);
      } else {
        return JSON.stringify({
          status: 'SUCCESS',
          localPath: null,
          durationMs: result.data.durationMs,
          message: '图片已生成但未返回图片数据',
        });
      }
    } catch (downloadError) {
      // 下载/保存失败但图片已生成
      return JSON.stringify({
        status: 'SUCCESS',
        localPath: null,
        downloadError: (downloadError as Error).message,
        durationMs: result.data.durationMs,
        message: `图片已生成但保存到本地失败`,
      });
    }

    return JSON.stringify({
      status: 'SUCCESS',
      localPath,
      durationMs: result.data.durationMs,
      revisedPrompt: result.data.revisedPrompt,
      costQuota: result.data.costQuota,
      remainingQuota: result.data.remainingQuota,
      message: `图片已生成并下载到 ${localPath}`,
    });
  },
};

function getTempDir(): string {
  const base =
    process.env.CODEBUDDY_PLUGIN_DATA ||
    process.env.CLAUDE_PLUGIN_DATA ||
    path.join(
      process.env.HOME || process.env.USERPROFILE || '.',
      '.godot-mcp'
    );
  return path.join(base, 'generated-images');
}
