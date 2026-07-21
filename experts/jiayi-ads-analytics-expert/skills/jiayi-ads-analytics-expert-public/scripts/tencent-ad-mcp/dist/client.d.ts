import type { ApiResponse } from "./types.js";
export declare function apiRequest(path: string, method: "GET" | "POST", params?: Record<string, unknown>): Promise<ApiResponse>;
/** Convenience: GET request */
export declare function apiGet(path: string, params?: Record<string, unknown>): Promise<ApiResponse>;
/** Convenience: POST request */
export declare function apiPost(path: string, params?: Record<string, unknown>): Promise<ApiResponse>;
//# sourceMappingURL=client.d.ts.map