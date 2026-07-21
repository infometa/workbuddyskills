export declare function refreshToken(): Promise<{
    accessToken: string;
    refreshToken: string;
}>;
export declare function exchangeAuthCode(authorizationCode: string, redirectUri: string): Promise<{
    accessToken: string;
    refreshToken: string;
}>;
//# sourceMappingURL=auth.d.ts.map