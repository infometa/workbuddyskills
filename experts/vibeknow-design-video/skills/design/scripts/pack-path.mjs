// pack-path.mjs — 解锁标记文件在本地的固定存储路径。
// 单 bundle 模型:53 版式 + 全部主题的渲染数据、以及免费/完整两份 manifest.json,早已随插件
// 一起分发在 render-bundle/(manifest.json 免费 / manifest.full.json 完整),不用下载、不会有
// "下载版 vs 装机版对不上"的版本漂移。"解锁"只是在本地翻一个标记文件——
// 有标记 → resolve-bundle.mjs 读 manifest.full.json;没有 → 读 manifest.json。
// 标记由 MCP 工具 `verify_connection`(连接 VibeKnow 后调用,门禁在连接本身)通过之后,
// run.mjs `unlock` 创建。WB_DESIGN_UNLOCK_MARKER 可覆盖标记路径(测试隔离用);
// 缺省落在用户目录下的固定位置。
import { homedir } from "node:os";
import { join } from "node:path";

export function unlockMarkerPath() {
  return process.env.WB_DESIGN_UNLOCK_MARKER || join(homedir(), ".workbuddy", "vibeknow-design", "unlocked");
}
