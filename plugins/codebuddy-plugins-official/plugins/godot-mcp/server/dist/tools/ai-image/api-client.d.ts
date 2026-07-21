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
/**
 * 查询当前用户的剩余额度
 *
 * @returns 成功时返回 remainingQuota / totalQuota / usedQuota
 */
export declare function apiGetQuota(): Promise<{
    ok: boolean;
    status: number;
    data: {
        remainingQuota: number;
        totalQuota: number;
        usedQuota: number;
        keyName: string;
        status: string;
    };
}>;
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
export declare function apiGenerateImage(params: GenerateImageParams): Promise<{
    ok: boolean;
    status: number;
    data: GenerateImageResult;
}>;
/**
 * 验证 API Key 是否有效
 */
export declare function apiVerifyKey(): Promise<{
    ok: boolean;
    status: number;
    data: {
        valid: boolean;
        keyName: string;
        role: string;
        remainingQuota: number;
        totalQuota: number;
    };
}>;
