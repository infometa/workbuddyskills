/**
 * AI Image 生图工具模块
 *
 * 提供 4 个内部 MCP 工具，仅供 Skill 编排调用：
 *   1. check_auth       - 检查 API Key 配置状态
 *   2. get_user_quota    - 查询当前用户剩余额度
 *   3. generate_image    - 请求后端生成图片并下载到本地
 *   4. import_to_godot   - 将图片导入到 Godot 项目目录
 */

import type { MCPTool } from '../../utils/types.js';
import { checkAuthTool } from './check-auth.js';
import { getUserQuotaTool } from './get-user-quota.js';
import { generateImageTool } from './generate-image.js';
import { importToGodotTool } from './import-to-godot.js';

export const aiImageTools: MCPTool[] = [
  checkAuthTool,
  getUserQuotaTool,
  generateImageTool,
  importToGodotTool,
];
