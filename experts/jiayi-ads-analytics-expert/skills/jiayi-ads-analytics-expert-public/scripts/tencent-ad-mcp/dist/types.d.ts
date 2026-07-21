export interface ApiResponse<T = unknown> {
    code: number;
    message: string;
    message_cn: string;
    data?: T;
    errors?: Array<{
        code: number;
        message: string;
        message_cn: string;
        field: string;
    }>;
}
export interface PageInfo {
    page: number;
    page_size: number;
    total_number: number;
    total_page: number;
}
export interface ListData<T = unknown> {
    list: T[];
    page_info: PageInfo;
}
//# sourceMappingURL=types.d.ts.map