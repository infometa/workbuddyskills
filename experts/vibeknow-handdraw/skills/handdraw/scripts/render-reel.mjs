// render-reel.mjs — 把多幕手绘串成一条带转场的成片(单次 remotion 渲染)。
// 用法见文件末尾 CLI 的 Usage 字符串(唯一真相源,别在这里再抄一份)。
// manifest 由 build-manifest.mjs 生成,每幕形如:
//   { data?, gt, audio?, narration?, seconds?, static? }   // static=true 的降级页无 data
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import fs from "node:fs";
import path from "node:path";

const exec = promisify(execFile);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const RB = process.env.REMOTION_BUILD || path.resolve(HERE, "../../../render");
const FPS = 30;
const GT_HOLD_SEC = 1.2;

// remotion 渲染并发度。**默认保守设 2**,而不是让 remotion 用它自己的缺省(约 核数/2,
// 8 核就是 4 个 chrome-headless-shell 并行渲帧,每个还可能多标签页)。
// 本专家跑在**用户个人电脑**上、同时还在跑 WorkBuddy 本身 —— 并发拉满会把机器占死、
// 进程调度开销飙升,反而更慢。宁可渲染慢一点,也要留足系统余量。
// 需要时用环境变量 HANDDRAW_RENDER_CONCURRENCY 调(1 = 最省资源,数字越大越快越吃机器)。
const RENDER_CONCURRENCY = Math.max(1, parseInt(process.env.HANDDRAW_RENDER_CONCURRENCY || "2", 10) || 2);

async function audioDurationSec(file) {
  const { stdout } = await exec("ffprobe", ["-v","error","-show_entries","format=duration","-of","csv=p=0", file], { maxBuffer: 1 << 20 });
  const d = parseFloat(String(stdout).trim());
  if (!isFinite(d) || d <= 0) throw new Error(`无法读取音频时长: ${file}`);
  return d;
}

// 画幅比例。合成尺寸由 props 驱动(calcReelMetadata 直接用 props.width/height),所以
// 任意比例都能出。这里给出支持的档位 —— 用「短边 = 1080」为基准定义,再由 resolution 缩放。
//
//   horizontal 16:9 (默认) → 1920×1080
//   vertical    9:16       → 1080×1920
//   square      1:1        → 1080×1080
//   classic     4:3        → 1440×1080
//   portrait43  3:4        → 1080×1440
export const ASPECTS = {
  horizontal: { w: 16, h: 9 },
  vertical: { w: 9, h: 16 },
  square: { w: 1, h: 1 },
  classic: { w: 4, h: 3 },   // 4:3 横
  portrait43: { w: 3, h: 4 },   // 3:4 竖
};
export const MAX_SHORT_EDGE = 1080;
export const DEFAULT_ASPECT = "horizontal";   // 唯一真相源(出图校验/绘制/渲染共用)
// 默认档位 —— **全流程唯一真相源**(出图校验 / 绘制 / 渲染 都引用它,改这里一处即可)。
// 720p 是发布的合理下限(540p 偏糊);再往上出图更贵,由用户明示。
export const DEFAULT_RESOLUTION = "720p";

// H.264 要求偶数边长。导出供 check-images 复用,避免两处各写一份取偶逻辑。
export const even = (n) => { const r = Math.round(n); return r % 2 === 0 ? r : r + 1; };

// 比例 → 基准合成尺寸(短边固定 1080,长边按比例推算并取偶数)。
export function compositionSize(aspect = DEFAULT_ASPECT) {
  const a = ASPECTS[String(aspect).trim().toLowerCase()];
  if (!a) throw new Error(`不支持的画幅 ${aspect}(可选 ${Object.keys(ASPECTS).join(" / ")})`);
  return a.w >= a.h
    ? { width: even(Math.round((MAX_SHORT_EDGE * a.w) / a.h)), height: MAX_SHORT_EDGE }
    : { width: MAX_SHORT_EDGE, height: even(Math.round((MAX_SHORT_EDGE * a.h) / a.w)) };
}

// 成片分辨率:用「短边」表达,如 540p / 720p / 1080p。scale = 短边/1080。
//
// **默认 720p**:540p 实测偏糊,720p 是发布的合理下限。再往上(1080p)出图会更贵
// —— 出图是花 WorkBuddy 积分的(渲染只花本地时间),所以更高档位由用户明示。
//
// **上限 1080p**:合成短边就 1080,再往上只是放大插值 —— 只会糊、只会让文件变大。
// 超过上限**不报错,自动压到 1080p**(并告知),避免因为用户随口说个 4K 就把流程卡死。
export function parseResolution(resolution) {
  const raw = String(resolution ?? DEFAULT_RESOLUTION).trim().toLowerCase();
  const m = raw.match(/^(\d+)\s*p?$/);
  if (!m) throw new Error(`看不懂的分辨率 ${resolution}(用短边表示,如 540p / 720p / 1080p)`);
  const want = parseInt(m[1], 10);
  if (!(want > 0)) throw new Error(`分辨率必须为正数,得 ${resolution}`);
  const shortEdge = Math.min(want, MAX_SHORT_EDGE);
  return { shortEdge, scale: shortEdge / MAX_SHORT_EDGE, clamped: want > MAX_SHORT_EDGE, requested: want };
}

// 尺寸只由 aspect × resolution 决定 —— **不再提供 scale 覆盖**。
// 原因:scale 会绕过 resolution,让成片尺寸与 check-images 已校验过的出图尺寸不匹配,
// 直接破坏「出图 = 成片」这条一致性保证。要小尺寸就传 --resolution 540p。
export async function renderReel({ scenes, out, aspect = DEFAULT_ASPECT, transition = "fade", sceneSeconds = 4, transitionSeconds = 0.5, tailSeconds = 1.0, resolution = DEFAULT_RESOLUTION }) {
  const r = parseResolution(resolution);
  const scale = r.scale;
  let clampNote = null;
  if (r.clamped) {
    clampNote = `已自动压到 ${MAX_SHORT_EDGE}p(请求 ${r.requested}p 超过上限;合成短边就 1080,再放大只会糊)`;
    console.error(`[render] ⚠️ ${clampNote}`);
  }
  if (!Array.isArray(scenes) || scenes.length === 0) throw new Error("scenes 为空");
  const { width: W, height: H } = compositionSize(aspect);   // 不认识的画幅会直接报错,不再静默当横版
  const transitionFrames = Math.max(1, Math.round(transitionSeconds * FPS));
  const defaultFrames = Math.max(transitionFrames + 1, Math.round(sceneSeconds * FPS));

  // 数据写进「输出文件同级」的工作区 public,渲染只读包内工程、不写工作区外(无需沙箱授权)。
  const pub = path.join(path.dirname(path.resolve(out)), ".hdprev-public");
  const hdprev = path.join(pub, "hdprev");
  fs.mkdirSync(hdprev, { recursive: true });

  const reelScenes = [];
  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    const isStatic = !!s.static;                    // 降级页:原图定格,无绘制数据
    if (!s.gt) throw new Error(`第 ${i + 1} 幕缺 gt`);
    if (!isStatic && !s.data) throw new Error(`第 ${i + 1} 幕缺 data(非降级页需绘制数据)`);
    fs.copyFileSync(s.gt, path.join(hdprev, `scene${i}.jpg`));
    let svgDataUrl;
    if (!isStatic) {
      fs.copyFileSync(s.data, path.join(hdprev, `scene${i}.json`));
      svgDataUrl = `hdprev/scene${i}.json`;
    }
    let frames = s.seconds ? Math.max(transitionFrames + 1, Math.round(s.seconds * FPS)) : defaultFrames;
    let audioUrl;
    if (s.audio) {
      const ext = path.extname(s.audio) || ".mp3";
      fs.copyFileSync(s.audio, path.join(hdprev, `scene${i}${ext}`));
      audioUrl = `hdprev/scene${i}${ext}`;
      if (!s.seconds) {
        const dur = await audioDurationSec(path.resolve(s.audio));
        frames = Math.max(transitionFrames + 1, Math.round((dur + tailSeconds) * FPS));
      }
    }
    reelScenes.push({ svgDataUrl, gtImageUrl: `hdprev/scene${i}.jpg`, audioUrl, narration: s.narration, static: isStatic, durationInFrames: frames });
  }

  const props = JSON.stringify({ scenes: reelScenes, transition, transitionFrames, width: W, height: H, fps: FPS, gtHoldSec: GT_HOLD_SEC });

  // ⚠️ 关键:**先渲到临时文件,校验通过后再原子改名**成 out。
  //
  // Remotion 是「边渲染边往输出文件写」的。若直接渲到 out,渲染期间 out 就已经存在、但只是个
  // 半截文件(几十 KB 且还在长大)。1080p 渲染很慢,调用方(agent)的命令超时后去看文件,
  // 就会读到「几十兆的视频显示成 xx 字节」或「刚要建还没建出来 → 找不到」。
  // 改成临时文件 + rename(同目录,原子)后:**渲染完成前 out 根本不存在**,一旦出现就一定是
  // 完整且可播的 —— 调用方只要轮询 out 是否存在即可,不会再读到半成品。
  const tmp = out + ".part.mp4";
  await exec("npx", ["remotion", "render", "handdraw-smoke.tsx", "HandDrawReel", tmp,
    `--props=${props}`, `--public-dir=${pub}`, `--scale=${scale}`,
    `--concurrency=${RENDER_CONCURRENCY}`, "--log=error"],   // 限并发,别把用户机器占死
    { cwd: RB, maxBuffer: 1 << 26 });

  // 校验:必须真有视频流且时长 > 0,否则宁可报错也不要把坏文件改名成 out。
  const info = await probeVideo(tmp).catch((e) => { throw new Error(`成片校验失败(${tmp}): ${e.message}`); });
  if (!info.width || !info.height || !(info.durationSec > 0) || !(info.bytes > 0)) {
    fs.rmSync(tmp, { force: true });
    throw new Error(`渲染产物无效(无视频流/时长为0): ${JSON.stringify(info)}`);
  }
  fs.renameSync(tmp, out);   // 原子:out 一出现就是完整的
  return { out, ...info, ...(clampNote ? { clamped: clampNote } : {}) };
}

// ffprobe 探测成片:宽高 / 时长 / 字节数。用于「改名前校验」+ 给调用方返回可直接汇报的信息。
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
  const get = (flag) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : undefined; };
  const manifest = get("--manifest");
  const out = get("--out");
  if (!manifest || !out) {
    console.error("Usage: node render-reel.mjs --manifest <scenes.json> --out <out.mp4> [--aspect horizontal|vertical] [--resolution 720p|1080p|540p] [--transition fade|slide|wipe] [--scene-seconds 4] [--transition-seconds 0.5] [--tail-seconds 1.0]");
    process.exit(1);
  }
  const scenes = JSON.parse(fs.readFileSync(manifest, "utf8"));
  renderReel({
    scenes, out,
    aspect: get("--aspect") || DEFAULT_ASPECT,
    transition: get("--transition") || "fade",
    sceneSeconds: parseFloat(get("--scene-seconds") || "4"),
    transitionSeconds: parseFloat(get("--transition-seconds") || "0.5"),
    tailSeconds: parseFloat(get("--tail-seconds") || "1.0"),
    resolution: get("--resolution") || DEFAULT_RESOLUTION,   // 默认 720p;按用户要求给,超 1080p 自动压
  })
    // 直接把「已校验」的成片信息打成 JSON —— 调用方(agent)拿它汇报即可,
    // **不要再自己去 ls/stat**:那正是读到半截文件、报出「几十兆显示 xx 字节」的来源。
    .then((r) => process.stdout.write(JSON.stringify({ status: "done", ...r })))
    .catch((e) => { console.error(String((e && e.message) || e)); process.exit(1); });
}
