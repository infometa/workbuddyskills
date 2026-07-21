// server.mjs — vibeknow 客户端库(零外部依赖)。导出 callHanddraw/callSynthesize/loadStyles/
// readTokenObj 等函数,供 skills/handdraw/scripts 下的 CLI(run.mjs / handdraw-page.mjs)经 Bash 调用。
// 原 stdio MCP 外壳已移除(WB 对自定义 MCP 连接器不稳,改走脚本+Bash,见 run.mjs)。所有外部调用经 go-vibeknow,需 JWT。
import { readFileSync, existsSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join, basename, extname } from "node:path";
import { tmpdir } from "node:os";
import { tokenFilePath } from "./token-path.mjs";

// 上传给 handdraw 的图**转成 JPEG q95**:handdraw 只需 RGB 像素喂 vtracer,PNG 的无损纯浪费带宽
// (一张 1280×720 手绘 PNG 约 1–1.5MB,JPEG q95 约 220–370KB,上行降到 ~1/5)。磁盘上的 NN.png
// 原样保留 —— 渲染仍用无损原图,这里只影响「上传的那一份字节」。
// 编码器优先级(取第一个可用):sips(mac 自带,精确 q95)→ magick/convert(ImageMagick)→ ffmpeg(已依赖,-q:v 2 ≈ q95)。
// 全不可用 → 回退原字节(png),绝不因编码失败而中断绘制。
function encodeUploadJpeg(imagePath) {
  const ext = extname(imagePath).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return null;
  const tmp = join(tmpdir(), `hdup_${process.pid}_${Date.now()}_${basename(imagePath, ext)}.jpg`);
  const tries = [
    ["sips", ["-s", "format", "jpeg", "-s", "formatOptions", "95", imagePath, "--out", tmp]],
    ["magick", [imagePath, "-quality", "95", tmp]],
    ["convert", [imagePath, "-quality", "95", tmp]],
    ["ffmpeg", ["-nostdin", "-loglevel", "error", "-y", "-i", imagePath, "-q:v", "2", tmp]],
  ];
  try {
    for (const [cmd, args] of tries) {
      const r = spawnSync(cmd, args, { stdio: "ignore" });
      if (r.status === 0 && existsSync(tmp)) {
        try { const b = readFileSync(tmp); if (b.length > 0) return b; } catch { /* try next */ }
      }
    }
    return null;
  } finally {
    // 把临时 JPEG 删掉 —— 只是用来读字节的中转,不删的话每页都在系统临时目录漏一个,反复跑越攒越多。
    try { if (existsSync(tmp)) rmSync(tmp, { force: true }); } catch { /* noop */ }
  }
}

// 要上传的字节 + content-type。⚠️ 文件名保持原 NN.png:服务端按 filename 回绑、客户端白名单也按原名匹配;
// 服务端用 DecodeConfig **嗅探真实格式**(不看扩展名),所以 png 文件名装 jpeg 字节没问题。
function uploadPayload(imagePath) {
  const jpeg = encodeUploadJpeg(imagePath);
  if (jpeg) return { bytes: jpeg, type: "image/jpeg" };
  const e = extname(imagePath).toLowerCase().replace(".", "");
  const type = (e === "jpg" || e === "jpeg") ? "image/jpeg" : e === "png" ? "image/png" : "application/octet-stream";
  return { bytes: readFileSync(imagePath), type };
}

// 风格目录默认走包内相对路径(server 在 mcp/，目录在 skills/handdraw/references/)。
const DEFAULT_STYLES = join(dirname(fileURLToPath(import.meta.url)), "..", "skills", "handdraw", "references", "styles.json");

// go-vibeknow 计费域错误码:积分不足(HTTP 200 + body code=100001)。单独成类,让上层
// (run.mjs / handdraw-page.mjs)能结构化识别 → 明确提示充值,而不是当成通用失败自由发挥。
export const CODE_INSUFFICIENT_CREDITS = 100001;
export class InsufficientCreditsError extends Error {
  constructor(service, tag) {
    super(`insufficient credits (${service})${tag ? ` [${tag}]` : ""}`);
    this.name = "InsufficientCreditsError";
    this.insufficientCredits = true;
    this.service = service;
  }
}

// 绘制数据是否真的有内容。
// ⚠️ 这是根治「静默写出空 vec.json」的防线:服务端曾返回 data:{}(HTTP 200),若直接落盘会被
// JSON.stringify 成 "{}",下游 build-manifest 只看文件存不存在 → 空数据一路穿到渲染,
// 结果是白幕/报错,而且这一页**还被计了费**。单页与批量两条路都必须过这一关。
export function hasDrawing(d) {
  const layer = (L) => L && typeof L === "object" && Array.isArray(L.paths) && L.paths.length > 0;
  return !!d && (layer(d.coarse) || layer(d.full));
}

// 每次调用时动态读取 STYLES_JSON，消除 env 固化
export function loadStyles() {
  const stylesPath = process.env.STYLES_JSON || DEFAULT_STYLES;
  if (!stylesPath || !existsSync(stylesPath)) return [];
  try {
    return JSON.parse(readFileSync(stylesPath, "utf8")).map(s => ({ id: s.id, name: s.name, desc: s.desc }));
  } catch {
    return [];
  }
}

// 默认走生产网关(按首段路由 /vibeknow → go-vibeknow)。本地/测试用 VIBEKNOW_BASE 覆盖。
const DEFAULT_VIBEKNOW = "https://vibeknow.com/vibeknow/v1";

// token 来源:先 env WB_TOKEN(测试/覆盖),再固定路径 token 文件(登录流程写入的同一路径)。
export function readTokenObj() {
  if (process.env.WB_TOKEN) return { access_token: process.env.WB_TOKEN, refresh_token: null };
  const f = tokenFilePath();
  if (f && existsSync(f)) {
    try { const j = JSON.parse(readFileSync(f, "utf8")); return { access_token: j.access_token || null, refresh_token: j.refresh_token || null }; }
    catch { return { access_token: null, refresh_token: null }; }
  }
  return { access_token: null, refresh_token: null };
}

export function readToken() { return readTokenObj().access_token; }

// 共用鉴权 fetch：读 token → 带 X-Authorization-Token 请求 → 401/403 时用 refresh_token 刷新重试一次 → 返回最终 Response。
// 调用方负责检查 r.ok 并抛特定错误（如 "tts HTTP 500"）。
async function authedFetch(url, init = {}) {
  let { access_token: token, refresh_token } = readTokenObj();
  if (!token) throw new Error("未登录:请先调用 `login` 工具(我会给你授权链接和验证码)完成登录");
  const doReq = (t) => fetch(url, { ...init, headers: { ...(init.headers || {}), "X-Authorization-Token": t } });
  let r = await doReq(token);
  if ((r.status === 401 || r.status === 403) && refresh_token) {
    try {
      const { refreshAccessToken } = await import("./auth-login.mjs");
      const tok = await refreshAccessToken({ refreshToken: refresh_token });
      token = tok.access_token;
      r = await doReq(token);
    } catch { /* fall through to friendly error */ }
  }
  if (r.status === 401 || r.status === 403) throw new Error("登录已过期或无效:请调用 `login` 工具重新登录");
  return r;
}

// 手绘绘制数据:上传本地图片 → POST ${VIBEKNOW_BASE}/handdraw(multipart, 字段 image) → 解 data 信封 → {coarse, full}。
// 服务端实现(矢量化/job-center 等)对插件不可见,插件只拿绘制数据。
// 手绘绘制。meta(可选)= { page, title, source }:计费元数据(页码/主题/来源 badge)。
// 逐页各扣各的:一页一次冻结→结算,积分明细一页一条(第 n 页)。
export async function callHanddraw(imagePath, meta = {}) {
  const base = process.env.VIBEKNOW_BASE || DEFAULT_VIBEKNOW;
  const { bytes, type } = uploadPayload(imagePath);   // 转 JPEG q95 再传(见 uploadPayload)
  const fd = new FormData();
  fd.append("image", new Blob([bytes], { type }), basename(imagePath)); // 文件名保持原样(服务端按名回绑)
  if (meta.page) fd.append("page", String(meta.page));
  if (meta.title) fd.append("title", String(meta.title));
  if (meta.source) fd.append("source", String(meta.source));
  // Do NOT set Content-Type header manually — fetch sets multipart/form-data boundary automatically.
  const r = await authedFetch(`${base}/handdraw`, { method: "POST", body: fd });
  // 抓一个可追踪 ID(便于对到 go-vibeknow / job-center 日志)
  const reqId = r.headers.get("x-request-id") || r.headers.get("x-trace-id") || r.headers.get("x-tt-logid") || "";
  const tag = `${basename(imagePath)}${reqId ? ` req=${reqId}` : ""}`;
  if (!r.ok) throw new Error(`handdraw HTTP ${r.status} [${tag}]`);
  const j = await r.json();
  // 积分不足:HTTP 200 + code=100001。必须先于空数据兜底判断,给出可识别的信号。
  if (j && j.code === CODE_INSUFFICIENT_CREDITS) throw new InsufficientCreditsError("handdraw", tag);
  if (j.error) throw new Error(`handdraw error: ${j.error} [${tag}]`);
  // 解标准信封 {code, data: {coarse, full}}
  const d = (j && typeof j.data === "object" && j.data !== null) ? j.data : j;
  // ⚠️ 绘制数据必须非空。服务端曾返回 data:{}(HTTP 200) → 这里若直接 return
  // {coarse:undefined,full:undefined} 会被 JSON.stringify 成 "{}" 静默写进 vec.json。
  // 改为炸出来,带上 request-id + 服务端 code/message,让调用方立刻知道哪页失败、去哪查。
  if (!hasDrawing(d)) {
    const meta = JSON.stringify({ code: j.code, message: j.message }).slice(0, 300);
    throw new Error(`handdraw 返回空绘制数据(无 coarse/full paths) [${tag}] resp=${meta}`);
  }
  // 必须返回 {coarse, full} 嵌套结构：HandDrawLayout 取 c.full（细节层）/ c.coarse（粗线稿）。
  return { coarse: d.coarse, full: d.full };
}

// 合成旁白:POST ${VIBEKNOW_BASE}/tts(带 JWT)→ 拿 audio_url → 下载到本地临时文件交给渲染。
// 401/403 时若有 refresh_token 自动刷新后重试一次;仍失败抛友好错误。
export async function callSynthesize(text, voice) {
  const base = process.env.VIBEKNOW_BASE || DEFAULT_VIBEKNOW;
  const body = JSON.stringify({ text, voice: voice || process.env.VOICE_ID || "" });
  const r = await authedFetch(`${base}/tts`, { method: "POST", headers: { "content-type": "application/json" }, body });
  if (!r.ok) throw new Error(`tts HTTP ${r.status}`);
  const j = await r.json();
  if (j && j.code === CODE_INSUFFICIENT_CREDITS) throw new InsufficientCreditsError("tts");
  if (j.error) throw new Error(j.error);
  const d = (j && typeof j.data === "object" && j.data !== null) ? j.data : j;
  const audioRes = await fetch(d.audio_url);
  if (!audioRes.ok) throw new Error(`audio download HTTP ${audioRes.status}`);
  const buf = Buffer.from(await audioRes.arrayBuffer());
  const ext = (d.audio_url.split("?")[0].match(/\.(\w+)$/) || [, "mp3"])[1];
  const out = join(tmpdir(), `hdtts_${process.pid}_${Date.now()}.${ext}`);
  writeFileSync(out, buf);
  return { audio_path: out, duration_sec: typeof d.duration_sec === "number" ? d.duration_sec : null };
}
