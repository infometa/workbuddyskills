/**
 * MCP Tool: import-to-godot
 * 将生成的图片导入到 Godot 项目目录
 */

import { z } from 'zod';
import fs from 'fs';
import path from 'path';
import type { MCPTool } from '../../utils/types.js';

const importToGodotSchema = z.object({
  sourcePath: z
    .string()
    .describe('源图片的本地绝对路径'),
  targetDir: z
    .string()
    .describe(
      '目标目录的绝对路径（Godot 项目内），如 D:/workspace/game1/assets/icons'
    ),
  fileName: z
    .string()
    .optional()
    .describe('目标文件名（含扩展名），默认保持源文件名'),
});

type ImportToGodotArgs = z.infer<typeof importToGodotSchema>;

export const importToGodotTool: MCPTool<ImportToGodotArgs> = {
  name: 'import_to_godot',
  description:
    '将本地图片文件复制到 Godot 项目目录中。' +
    '需要提供源图片的绝对路径和目标目录。' +
    '复制完成后 Godot 编辑器会自动 reimport 该资源。',
  parameters: importToGodotSchema,
  execute: async (args: ImportToGodotArgs): Promise<string> => {
    const { sourcePath, targetDir, fileName } = args;

    // 检查源文件存在
    if (!fs.existsSync(sourcePath)) {
      return JSON.stringify({
        error: 'SOURCE_NOT_FOUND',
        message: `源文件不存在: ${sourcePath}`,
      });
    }

    // 创建目标目录
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    // 确定目标文件名
    const targetFileName = fileName || path.basename(sourcePath);
    const targetPath = path.join(targetDir, targetFileName);

    try {
      // 复制文件
      fs.copyFileSync(sourcePath, targetPath);

      // 计算相对于 Godot 项目的 res:// 路径（尽力推断）
      let resPath = targetPath;
      const projectGodotIndex = targetPath.replace(/\\/g, '/').indexOf('/project.godot');
      if (projectGodotIndex === -1) {
        // 尝试从路径中推断项目根目录
        const parts = targetPath.replace(/\\/g, '/').split('/');
        for (let i = parts.length - 1; i >= 0; i--) {
          const candidate = parts.slice(0, i + 1).join('/');
          if (fs.existsSync(path.join(candidate, 'project.godot'))) {
            resPath = 'res://' + targetPath.replace(/\\/g, '/').substring(candidate.length + 1);
            break;
          }
        }
      }

      return JSON.stringify({
        success: true,
        localPath: targetPath,
        resPath,
        message: `图片已导入到 ${targetPath}`,
      });
    } catch (error) {
      return JSON.stringify({
        error: 'COPY_FAILED',
        message: `复制文件失败: ${(error as Error).message}`,
      });
    }
  },
};
