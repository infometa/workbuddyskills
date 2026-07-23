// tts-microsoft.mjs — 用微软 edge-tts(免费、免登录、不扣积分)合成旁白,产出 NN.mp3 + 时长。
// 是手绘专家 TTS 的「默认引擎」;vibeknow 远端 TTS 为可选高级音色(需登录+积分)。
// 依赖:python3 + edge_tts(由 setup-env.mjs / `run.mjs init` 首用自装)。ffprobe 读时长(随 chrome/render 环境已具备)。
// 调用方式走 `python3 -m edge_tts`(而非依赖 --user 装出的 CLI 是否在 PATH)。
import { spawnSync } from "node:child_process";
import { existsSync, statSync, mkdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";

export const DEFAULT_MS_VOICE = "zh-CN-XiaoxiaoNeural";

// 构造 edge_tts 命令行参数(抽出来便于测试)。文本经 args 数组传入,无需 shell 转义。
export function buildEdgeTtsArgs(text, voice, out) {
  return ["-m", "edge_tts", "--voice", voice, "--text", text, "--write-media", out];
}

// ffprobe 读音频时长(秒)。失败返回 null(时长非必需:render-reel 无时长会用默认秒数)。
function probeDurationSec(file) {
  const r = spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file], { encoding: "utf8" });
  if (r.status !== 0) return null;
  const d = parseFloat(String(r.stdout).trim());
  return isFinite(d) && d > 0 ? d : null;
}

// 合成旁白。out 指定则直接落该路径(如 <JOBDIR>/NN.mp3);否则落临时文件。
export function synthesizeMicrosoft(text, { voice, out } = {}) {
  if (!text || !String(text).trim()) throw new Error("microsoft tts: 需要文案");
  const v = voice || process.env.VOICE_ID || DEFAULT_MS_VOICE;
  const dest = out || join(tmpdir(), `hdtts_ms_${process.pid}_${Date.now()}.mp3`);
  // edge-tts --write-media 自己创建文件;失败时清理可能残留的半成品,避免 build-manifest 误当音频。
  const cleanup = () => { try { if (existsSync(dest)) rmSync(dest, { force: true }); } catch { /* noop */ } };
  const r = spawnSync("python3", buildEdgeTtsArgs(String(text), v, dest), { encoding: "utf8" });
  if (r.error && r.error.code === "ENOENT") {
    cleanup();
    throw new Error("未找到 python3 —— 微软 TTS 需要 python3 + edge_tts,请先运行 `run.mjs init`");
  }
  if (r.status !== 0) {
    cleanup();
    const msg = String(r.stderr || r.stdout || "").trim();
    if (/No module named ['"]?edge_tts/.test(msg)) {
      throw new Error("未安装 edge_tts —— 请先运行 `run.mjs init`(会 pip install --user edge-tts)");
    }
    throw new Error(`edge-tts 合成失败: ${msg.slice(0, 300)}`);
  }
  if (!existsSync(dest) || statSync(dest).size === 0) {
    cleanup();
    throw new Error(`edge-tts 未产出音频(空文件): ${dest}`);
  }
  return { audio_path: dest, duration_sec: probeDurationSec(dest), engine: "microsoft", voice: v };
}

// CLI(便于单独调试):node tts-microsoft.mjs "<文案>" [--voice V] [--out FILE]
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const get = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const text = args.find((a) => !a.startsWith("--"));
  if (!text) { console.error('Usage: node tts-microsoft.mjs "<文案>" [--voice V] [--out FILE]'); process.exit(1); }
  const out = get("--out");
  if (out) { try { mkdirSync(dirname(out), { recursive: true }); } catch { /* noop */ } }
  try {
    process.stdout.write(JSON.stringify(synthesizeMicrosoft(text, { voice: get("--voice"), out })));
  } catch (e) { console.error(String((e && e.message) || e)); process.exit(1); }
}
