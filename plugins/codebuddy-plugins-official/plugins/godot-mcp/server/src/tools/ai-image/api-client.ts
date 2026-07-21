/**
 * 后端 API 客户端
 * ──────────────────────────────────────────
 * 封装对代理服务的 HTTP 调用。
 *
 * 设计原则：
 *   - 插件只是「薄客户端」，所有业务决策（provider 选择、额度扣减、限流）由后端完成
 *   - 认证方式：API Key（通过 X-API-Key 请求头传递）
 *   - 不暴露任何后端内部路由结构、认证协议、Provider 类型
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

// ──────────────────────────────────────────
//  内部：基础请求层（不导出）
// ──────────────────────────────────────────

/** 从 .mcp.json 读取的缓存配置 */
let _mcpConfig: { backendUrl?: string; apiKey?: string } | null = null;

/**
 * 从 .mcp.json 中读取环境变量配置（fallback）
 * 当 CodeBuddy 启动 MCP server 时未正确透传环境变量时使用
 */
function loadMcpConfig(): { backendUrl?: string; apiKey?: string } {
  if (_mcpConfig !== null) return _mcpConfig;
  _mcpConfig = {};

  try {
    // 从当前文件位置向上查找 .mcp.json
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = dirname(__filename);
    // server/dist/tools/ai-image/ -> 项目根 (4 级向上)
    const possiblePaths = [
      resolve(__dirname, '../../../../.mcp.json'),   // 从 dist/tools/ai-image/ 到项目根
      resolve(__dirname, '../../../.mcp.json'),      // 从 dist/tools/ 到项目根
      resolve(process.cwd(), '.mcp.json'),           // 当前工作目录
    ];

    for (const mcpPath of possiblePaths) {
      if (existsSync(mcpPath)) {
        const content = readFileSync(mcpPath, 'utf-8');
        const json = JSON.parse(content);
        const serverEnv =
          json?.mcpServers?.['godot-mcp']?.env || {};
        _mcpConfig = {
          backendUrl: serverEnv.GODOT_BACKEND_URL,
          apiKey: serverEnv.GODOT_API_KEY,
        };
        break;
      }
    }
  } catch {
    // 忽略读取错误
  }
  return _mcpConfig;
}

/** 后端服务地址 */
function getBaseURL(): string {
  if (process.env.GODOT_BACKEND_URL) return process.env.GODOT_BACKEND_URL;
  return loadMcpConfig().backendUrl || 'http://localhost:8080';
}

/** 用户 API Key（由管理员分配） */
function getApiKey(): string {
  if (process.env.GODOT_API_KEY) return process.env.GODOT_API_KEY;
  return loadMcpConfig().apiKey || '';
}

/** 通用请求封装 */
async function request<T = any>(
  path: string,
  options: {
    method?: string;
    body?: any;
    headers?: Record<string, string>;
  } = {}
): Promise<{ ok: boolean; status: number; data: T }> {
  const { method = 'GET', body, headers: extraHeaders } = options;
  const url = `${getBaseURL()}${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };

  // 注入 API Key
  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const fetchOptions: RequestInit = { method, headers };
  if (body) {
    fetchOptions.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, fetchOptions);
    const data = await response.json();
    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      data: { error: `网络错误: ${(error as Error).message}` } as T,
    };
  }
}

// ──────────────────────────────────────────
//  对外导出：插件可见的 API（仅 3 个方法）
// ──────────────────────────────────────────

/**
 * 查询当前用户的剩余额度
 *
 * @returns 成功时返回 remainingQuota / totalQuota / usedQuota
 */
export async function apiGetQuota() {
  return request<{
    remainingQuota: number;
    totalQuota: number;
    usedQuota: number;
    keyName: string;
    status: string;
  }>('/v1/quota/balance');
}

/**
 * 生成图片的请求参数
 * 只暴露用户需要感知的字段，Provider 选择等细节由后端自动处理
 */
export interface GenerateImageParams {
  /** 用户原始提示词（必填） */
  prompt: string;
  /** 优化后的提示词（Skill 层处理后传入） */
  optimizedPrompt?: string;
  /** 图片宽度 */
  width?: number;
  /** 图片高度 */
  height?: number;
  /** 图片风格：pixel / realistic / anime / watercolor / flat */
  style?: string;
  /** 参考图像 URL（图生图时使用） */
  referenceImages?: string[];
}

/**
 * 生成图片的返回结果
 */
export interface GenerateImageResult {
  /** 生成记录 ID */
  id: string;
  /** 状态 */
  status: string;
  /** 图片 URL（可供下载） */
  imageUrl: string;
  /** 图片 base64 数据（部分 provider 返回） */
  imageData?: string;
  /** 耗时（毫秒） */
  durationMs: number;
  /** 优化后的提示词（部分 provider 返回） */
  revisedPrompt?: string;
  /** 本次消耗的额度 */
  costQuota?: number;
  /** 剩余额度 */
  remainingQuota?: number;
  /** 错误信息 */
  error?: string;
  message?: string;
}

/**
 * 请求后端生成图片
 *
 * 后端自动处理：provider 路由、额度扣减、限流、日志记录
 * 插件端只需传入提示词和基本参数
 */
export async function apiGenerateImage(params: GenerateImageParams) {
  // 映射为后端接受的字段名（隐藏内部字段命名）
  const body: Record<string, any> = {
    prompt: params.prompt,
  };
  if (params.optimizedPrompt) body.optimizedPrompt = params.optimizedPrompt;
  if (params.width) body.width = params.width;
  if (params.height) body.height = params.height;
  if (params.style) body.style = params.style;
  if (params.referenceImages?.length) body.imageUrls = params.referenceImages;

  return request<GenerateImageResult>('/v1/image/generate', {
    method: 'POST',
    body,
  });
}

/**
 * 验证 API Key 是否有效
 */
export async function apiVerifyKey() {
  return request<{
    valid: boolean;
    keyName: string;
    role: string;
    remainingQuota: number;
    totalQuota: number;
  }>('/api/auth/verify', {
    method: 'POST',
  });
}
