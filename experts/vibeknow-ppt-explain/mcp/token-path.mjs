// token-path.mjs — 登录态 token 的固定存储路径（代码内确定，不依赖 env 注入）。
// 关键：MCP server(读) 与登录流程(写) 必须用同一个路径，否则「登录了却读不到」。
// WB_TOKEN_FILE 仍可覆盖（测试/特殊部署）；缺省落在用户目录下的固定位置。
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { mkdirSync } from "node:fs";

export function tokenFilePath() {
  return process.env.WB_TOKEN_FILE || join(homedir(), ".workbuddy", "vibeknow-ppt-explain", "token.json");
}

export function ensureTokenDir() {
  mkdirSync(dirname(tokenFilePath()), { recursive: true });
}
