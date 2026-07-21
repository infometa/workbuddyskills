/**
 * MCP Tool: get-user-quota
 * 查询当前用户剩余额度
 */

import { z } from 'zod';
import type { MCPTool } from '../../utils/types.js';
import { apiGetQuota } from './api-client.js';

const getUserQuotaSchema = z.object({}).strict();

type GetUserQuotaArgs = z.infer<typeof getUserQuotaSchema>;

export const getUserQuotaTool: MCPTool<GetUserQuotaArgs> = {
  name: 'query_quota',
  description:
    '查询当前用户的剩余生图额度。' +
    '返回 totalQuota（总额度）、usedQuota（已使用）、remainingQuota（剩余）。',
  parameters: getUserQuotaSchema,
  execute: async (_args: GetUserQuotaArgs): Promise<string> => {
    const result = await apiGetQuota();

    if (!result.ok) {
      if (result.status === 401) {
        return JSON.stringify({
          error: 'AUTH_REQUIRED',
          message: 'API Key 无效或未配置，请检查 GODOT_API_KEY 环境变量',
        });
      }
      if (result.status === 403) {
        return JSON.stringify({
          error: 'KEY_DISABLED',
          message: 'API Key 已被禁用，请联系管理员',
        });
      }
      if (result.status === 402) {
        return JSON.stringify({
          error: 'INSUFFICIENT_QUOTA',
          message: '额度不足，请联系管理员增加额度',
          remainingQuota: 0,
        });
      }
      return JSON.stringify({
        error: 'SERVICE_ERROR',
        message: '查询额度失败，请稍后重试',
      });
    }

    const remaining = result.data.remainingQuota ?? 0;
    const total = result.data.totalQuota ?? 0;

    return JSON.stringify({
      totalQuota: total,
      usedQuota: result.data.usedQuota ?? 0,
      remainingQuota: remaining,
      sufficient: remaining >= 1,
      message: remaining >= 1
        ? `剩余额度：${remaining}/${total}`
        : '额度不足，请联系管理员申请更多额度',
    });
  },
};
