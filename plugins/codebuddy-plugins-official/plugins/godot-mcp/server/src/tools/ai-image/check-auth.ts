/**
 * MCP Tool: check-auth
 * 检查 API Key 配置状态
 */

import { z } from 'zod';
import type { MCPTool } from '../../utils/types.js';
import { apiVerifyKey } from './api-client.js';

const checkAuthSchema = z.object({
  action: z
    .enum(['check', 'login-url'])
    .optional()
    .describe(
      'check=检查当前 API Key 状态（默认）; login-url=返回配置指引'
    ),
});

type CheckAuthArgs = z.infer<typeof checkAuthSchema>;

export const checkAuthTool: MCPTool<CheckAuthArgs> = {
  name: 'verify_api_key',
  description:
    '检查用户 API Key 配置状态。返回 JSON 格式的认证状态信息，' +
    '包括是否已配置 API Key、Key 是否有效、用户名等。' +
    'action=login-url 时返回配置指引。',
  parameters: checkAuthSchema,
  execute: async (args: CheckAuthArgs): Promise<string> => {
    const action = args.action || 'check';

    switch (action) {
      case 'check': {
        const apiKey = process.env.GODOT_API_KEY;
        if (!apiKey) {
          return JSON.stringify({
            authenticated: false,
            message:
              '未配置 API Key。请在环境变量 GODOT_API_KEY 中设置您的 API Key。',
            configGuide:
              '请联系管理员获取 API Key，然后在 .mcp.json 中的 env.GODOT_API_KEY 字段填入。',
          });
        }

        // 向后端验证 API Key
        const verifyResult = await apiVerifyKey();

        if (verifyResult.ok && verifyResult.data.valid) {
          return JSON.stringify({
            authenticated: true,
            keyName: verifyResult.data.keyName,
            role: verifyResult.data.role,
            remainingQuota: verifyResult.data.remainingQuota,
            totalQuota: verifyResult.data.totalQuota,
            message: `已认证：${verifyResult.data.keyName}，剩余额度 ${verifyResult.data.remainingQuota}`,
          });
        }

        // Key 无效
        const errorMsg =
          verifyResult.status === 401
            ? 'API Key 无效或已过期，请联系管理员。'
            : verifyResult.status === 403
              ? 'API Key 已被禁用。'
              : `验证失败 (HTTP ${verifyResult.status})`;

        return JSON.stringify({
          authenticated: false,
          message: errorMsg,
          configGuide:
            '请检查 GODOT_API_KEY 环境变量是否正确，或联系管理员获取新的 API Key。',
        });
      }

      case 'login-url': {
        return JSON.stringify({
          configGuide:
            'API Key 认证模式无需登录 URL。请联系管理员获取 API Key，' +
            '然后在 .mcp.json 中的 env.GODOT_API_KEY 字段填入即可。',
          message: '请联系管理员获取 API Key',
        });
      }

      default:
        throw new Error(`Unknown action: ${action}`);
    }
  },
};
