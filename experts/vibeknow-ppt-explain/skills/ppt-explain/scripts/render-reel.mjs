// render-reel.mjs — 把多页文档幕串成一条带运镜/转场/字幕的讲解成片(单次 remotion 渲染)。
// manifest 由 build-manifest.mjs 生成,每幕形如:{ gt, audio?, narration?, seconds? }。
// 画面 = 文档原页(objectFit contain)+ Ken Burns 运镜 + 底部字幕(见 render/layout/PptExplainLayout)。
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import fs from "node:fs";
import path from "node:path";
import { readTokenObj } from "../../../mcp/server.mjs";

const exec = promisify(execFile);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const RB = process.env.REMOTION_BUILD || path.resolve(HERE, "../../../render");
const FPS = 30;

// 渲染并发度:默认保守 2(专家跑在用户个人电脑上,还同时跑 WorkBuddy,拉满会占死机器)。
const RENDER_CONCURRENCY = Math.max(1, parseInt(process.env.PPT_RENDER_CONCURRENCY || "2", 10) || 2);

async function audioDurationSec(file) {
  const { stdout } = await exec("ffprobe", ["-v","error","-show_entries","format=duration","-of","csv=p=0", file], { maxBuffer: 1 << 20 });
  const d = parseFloat(String(stdout).trim());
  if (!isFinite(d) || d <= 0) throw new Error(`无法读取音频时长: ${file}`);
  return d;
}

// 画幅比例:短边 1080 基准,再由 resolution 缩放。与手绘同一套(全流程一致)。
export const ASPECTS = {
  horizontal: { w: 16, h: 9 },
  vertical: { w: 9, h: 16 },
  square: { w: 1, h: 1 },
  classic: { w: 4, h: 3 },
  portrait43: { w: 3, h: 4 },
};
export const MAX_SHORT_EDGE = 1080;
export const DEFAULT_ASPECT = "horizontal";
export const DEFAULT_RESOLUTION = "720p";
export const even = (n) => { const r = Math.round(n); return r % 2 === 0 ? r : r + 1; };

export function compositionSize(aspect = DEFAULT_ASPECT) {
  const a = ASPECTS[String(aspect).trim().toLowerCase()];
  if (!a) throw new Error(`不支持的画幅 ${aspect}(可选 ${Object.keys(ASPECTS).join(" / ")})`);
  return a.w >= a.h
    ? { width: even(Math.round((MAX_SHORT_EDGE * a.w) / a.h)), height: MAX_SHORT_EDGE }
    : { width: MAX_SHORT_EDGE, height: even(Math.round((MAX_SHORT_EDGE * a.h) / a.w)) };
}

export function parseResolution(resolution) {
  const raw = String(resolution ?? DEFAULT_RESOLUTION).trim().toLowerCase();
  const m = raw.match(/^(\d+)\s*p?$/);
  if (!m) throw new Error(`看不懂的分辨率 ${resolution}(用短边表示,如 540p / 720p / 1080p)`);
  const want = parseInt(m[1], 10);
  if (!(want > 0)) throw new Error(`分辨率必须为正数,得 ${resolution}`);
  const shortEdge = Math.min(want, MAX_SHORT_EDGE);
  return { shortEdge, scale: shortEdge / MAX_SHORT_EDGE, clamped: want > MAX_SHORT_EDGE, requested: want };
}

export async function renderReel({ scenes, out, aspect = DEFAULT_ASPECT, transition = "fade", subtitle = true, sceneSeconds = 4, transitionSeconds = 0.5, tailSeconds = 1.0, resolution = DEFAULT_RESOLUTION }) {
  const r = parseResolution(resolution);
  const scale = r.scale;
  let clampNote = null;
  if (r.clamped) {
    clampNote = `已自动压到 ${MAX_SHORT_EDGE}p(请求 ${r.requested}p 超过上限;合成短边就 1080,再放大只会糊)`;
    console.error(`[render] ⚠️ ${clampNote}`);
  }
  if (!Array.isArray(scenes) || scenes.length === 0) throw new Error("scenes 为空");
  const { width: W, height: H } = compositionSize(aspect);
  const transitionFrames = Math.max(1, Math.round(transitionSeconds * FPS));
  const defaultFrames = Math.max(transitionFrames + 1, Math.round(sceneSeconds * FPS));

  // 数据写进「输出文件同级」的工作区 public,渲染只读包内工程、不写工作区外(无需沙箱授权)。
  const pub = path.join(path.dirname(path.resolve(out)), ".pptprev-public");
  const prev = path.join(pub, "pptprev");
  fs.mkdirSync(prev, { recursive: true });

  const reelScenes = [];
  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    if (!s.gt) throw new Error(`第 ${i + 1} 幕缺 gt(页面图)`);
    const imgExt = path.extname(s.gt) || ".png";
    fs.copyFileSync(s.gt, path.join(prev, `scene${i}${imgExt}`));
    let frames = s.seconds ? Math.max(transitionFrames + 1, Math.round(s.seconds * FPS)) : defaultFrames;
    let audioUrl;
    if (s.audio) {
      const ext = path.extname(s.audio) || ".mp3";
      fs.copyFileSync(s.audio, path.join(prev, `scene${i}${ext}`));
      audioUrl = `pptprev/scene${i}${ext}`;
      if (!s.seconds) {
        const dur = await audioDurationSec(path.resolve(s.audio));
        frames = Math.max(transitionFrames + 1, Math.round((dur + tailSeconds) * FPS));
      }
    }
    reelScenes.push({ gtImageUrl: `pptprev/scene${i}${imgExt}`, audioUrl, narration: s.narration, durationInFrames: frames });
  }

  const props = JSON.stringify({ scenes: reelScenes, transition, transitionFrames, subtitle, width: W, height: H, fps: FPS });

  // 先渲到临时文件,ffprobe 校验通过后再原子 rename 成 out —— out 一旦出现就是完整可播的。
  const tmp = out + ".part.mp4";
  await exec("npx", ["remotion", "render", "ppt-reel.tsx", "PptReel", tmp,
    `--props=${props}`, `--public-dir=${pub}`, `--scale=${scale}`,
    `--concurrency=${RENDER_CONCURRENCY}`, "--log=error"],
    { cwd: RB, maxBuffer: 1 << 26 });

  const info = await probeVideo(tmp).catch((e) => { throw new Error(`成片校验失败(${tmp}): ${e.message}`); });
  if (!info.width || !info.height || !(info.durationSec > 0) || !(info.bytes > 0)) {
    fs.rmSync(tmp, { force: true });
    throw new Error(`渲染产物无效(无视频流/时长为0): ${JSON.stringify(info)}`);
  }
  fs.renameSync(tmp, out);
  return { out, ...info, ...(clampNote ? { clamped: clampNote } : {}) };
}

async function probeVideo(file) {
  const { stdout } = await exec("ffprobe", ["-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height", "-show_entries", "format=duration,size",
    "-of", "json", file], { maxBuffer: 1 << 22 });
  const j = JSON.parse(stdout);
  const st = (j.streams && j.streams[0]) || {};
  const fm = j.format || {};
  return {
    width: Number(st.width) || 0,
    height: Number(st.height) || 0,
    durationSec: Math.round((Number(fm.duration) || 0) * 100) / 100,
    bytes: Number(fm.size) || 0,
  };
}

// CLI
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  const args = process.argv.slice(2);
  const has = (flag) => args.includes(flag);
  const get = (flag) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : undefined; };
  const manifest = get("--manifest");
  const out = get("--out");
  if (!manifest || !out) {
    console.error("Usage: node render-reel.mjs --manifest <scenes.json> --out <out.mp4> [--aspect horizontal|vertical|square|classic] [--resolution 720p|1080p|540p] [--transition fade|slide|wipe] [--no-subtitle] [--scene-seconds 4] [--transition-seconds 0.5] [--tail-seconds 1.0]");
    process.exit(1);
  }
  // ★登录闸门★:成片必须登录(复用 vibeknow 账号 + 归因)。不是技术必需——
  // 渲染全在本地,但"拿到成片"这一步刻意 gate 在登录后。未登录 → 结构化提示 + 非0退出,
  // 由专家引导用户先 `node run.mjs login`。
  if (!readTokenObj().access_token) {
    process.stdout.write(JSON.stringify({
      status: "login_required",
      message: "成片需要先登录 vibeknow 账号,请先跑 `node run.mjs login` 完成登录后再渲染。",
    }));
    process.exit(3);
  }

  const scenes = JSON.parse(fs.readFileSync(manifest, "utf8"));
  renderReel({
    scenes, out,
    aspect: get("--aspect") || DEFAULT_ASPECT,
    transition: get("--transition") || "fade",
    subtitle: !has("--no-subtitle"),
    sceneSeconds: parseFloat(get("--scene-seconds") || "4"),
    transitionSeconds: parseFloat(get("--transition-seconds") || "0.5"),
    tailSeconds: parseFloat(get("--tail-seconds") || "1.0"),
    resolution: get("--resolution") || DEFAULT_RESOLUTION,
  })
    .then((r) => process.stdout.write(JSON.stringify({ status: "done", ...r })))
    .catch((e) => { console.error(String((e && e.message) || e)); process.exit(1); });
}
