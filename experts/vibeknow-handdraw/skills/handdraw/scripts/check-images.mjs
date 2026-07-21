// check-images.mjs — 出图尺寸预检:在【花积分绘制之前】把不合格的 NN.png 拦下来。
//
// 为什么必须有这道闸:出图尺寸是 agent 传给 ImageGen 的,SOP 里写多少它不一定照做
// (实测第一版的工程文件里,同一条视频的图有的 540 有的 720)。光靠文档约束不住,
// 得在真正会出事的地方做硬校验 —— 而且要放在**掏钱之前**。
//
// 校验四条(都是真会出事的,不是洁癖):
//   ① 宽高比必须匹配 aspect —— 比例不对 → 渲染时留黑边或被裁切。
//   ② 短边 ≥ 成片档位短边 —— 图比成片小 → 最后定格的画面被放大,糊。
//   ③ 长边 ≤ 1920         —— 服务端硬限,超了 handdraw 直接拒(白跑一趟)。
//   ④ 各页尺寸必须一致     —— 忽大忽小 → 成片里画面尺寸跳变。
import { execFileSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { join } from "node:path";
import { ASPECTS, compositionSize, parseResolution, even, DEFAULT_RESOLUTION, DEFAULT_ASPECT } from "./render-reel.mjs";

export const MAX_LONG_EDGE = 1920;   // 与 go-vibeknow 的 maxHanddrawLongEdge 对齐
const ASPECT_TOL = 0.02;             // 宽高比容差 2%(生图模型偶有 ±1px 取整)

// 目标短边 —— 复用 render-reel 的分辨率解析,保证出图与成片用的是**同一套定义**。
export function targetShortEdge(resolution = DEFAULT_RESOLUTION) {
  return parseResolution(resolution).shortEdge;
}

// 该档位下应当出的图:按合成画幅等比缩到目标短边(即「和成片同尺寸」)。
// 边长取偶数,避免生图模型给出奇数边导致后续处理麻烦。
export function recommendedSize(aspect = DEFAULT_ASPECT, resolution = DEFAULT_RESOLUTION) {
  const comp = compositionSize(aspect);                    // 短边 1080 的基准画幅
  const { scale } = parseResolution(resolution);           // 复用同一份换算,不再自己除 1080
  return { width: even(comp.width * scale), height: even(comp.height * scale) };
}

// 用 ffprobe 读图片宽高(ffprobe 已是本专家的既有依赖,渲染那边也在用)。
export function imageSize(file) {
  const out = execFileSync("ffprobe", ["-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height", "-of", "csv=p=0", file], { encoding: "utf8" });
  const [w, h] = String(out).trim().split(",").map((n) => parseInt(n, 10));
  if (!(w > 0) || !(h > 0)) throw new Error(`读不出图片尺寸: ${file}`);
  return { width: w, height: h };
}

// 纯逻辑校验(便于测试):sizes = [{name, width, height}]。
// 返回 { ok, expected, errors:[{name, size, reason}] }。
export function checkSizes(sizes, { aspect = DEFAULT_ASPECT, resolution = DEFAULT_RESOLUTION } = {}) {
  const short = targetShortEdge(resolution);
  const expected = recommendedSize(aspect, resolution);
  const a = ASPECTS[String(aspect).trim().toLowerCase()];
  if (!a) throw new Error(`不支持的画幅 ${aspect}(可选 ${Object.keys(ASPECTS).join(" / ")})`);
  const wantRatio = a.w / a.h;
  const errors = [];

  for (const s of sizes) {
    const ratio = s.width / s.height;
    const shortEdge = Math.min(s.width, s.height);
    const longEdge = Math.max(s.width, s.height);
    const size = `${s.width}x${s.height}`;

    if (Math.abs(ratio - wantRatio) / wantRatio > ASPECT_TOL) {
      errors.push({ name: s.name, size, reason: `宽高比不是 ${a.w}:${a.h}(${aspect}) → 渲染会留黑边/被裁切` });
      continue;   // 比例都错了,再报短边意义不大
    }
    if (shortEdge < short) {
      errors.push({ name: s.name, size, reason: `短边 ${shortEdge} < 成片档位 ${short} → 定格画面会被放大糊掉` });
      continue;
    }
    if (longEdge > MAX_LONG_EDGE) {
      errors.push({ name: s.name, size, reason: `长边 ${longEdge} > ${MAX_LONG_EDGE} → handdraw 服务端会直接拒` });
    }
  }

  // ④ 一致性:各页尺寸必须相同,否则成片里画面尺寸跳变。
  const uniq = [...new Set(sizes.map((s) => `${s.width}x${s.height}`))];
  if (uniq.length > 1) {
    errors.push({ name: "(全部)", size: uniq.join(" / "), reason: "各页出图尺寸不一致 → 成片里画面忽大忽小。所有页必须同尺寸" });
  }
  return { ok: errors.length === 0, expected, errors };
}

// 对 JOBDIR 下给定的一组图做预检(读真实尺寸后走 checkSizes)。
export function checkPageImages(files, opts) {
  const sizes = files.map((f) => ({ name: f.name, ...imageSize(f.path) }));
  return checkSizes(sizes, opts);
}

// 列出 JOBDIR 下所有 NN.png / NN.jpg(按页号升序)。
export function listPageImages(jobdir) {
  return readdirSync(jobdir)
    .filter((f) => /^\d+\.(png|jpe?g)$/i.test(f))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

// CLI:掏钱画之前先跑一遍尺寸预检。
//   node check-images.mjs <JOBDIR> [--aspect <画幅>] [--resolution <档位>]
// 合格 → 打印 {ok:true, expected} 并退 0;不合格 → 打印每页问题并退 4(与 handdraw-page 的绘制解耦,
// SOP 在逐页绘制前统一跑一次,一次性看清哪些页要重出图)。
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const jobdir = args.find((a) => !a.startsWith("--"));
  const flag = (name, def) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : def; };
  const aspect = flag("aspect", DEFAULT_ASPECT);
  const resolution = flag("resolution", DEFAULT_RESOLUTION);
  if (!jobdir) { console.error("Usage: node check-images.mjs <JOBDIR> [--aspect <画幅>] [--resolution <档位>]"); process.exit(1); }
  try {
    const pages = listPageImages(jobdir);
    if (pages.length === 0) { console.error(`${jobdir} 里没有 NN.png`); process.exit(1); }
    const check = checkPageImages(pages.map((f) => ({ name: f, path: join(jobdir, f) })), { aspect, resolution });
    if (check.ok) {
      process.stdout.write(JSON.stringify({ ok: true, expected: check.expected, aspect, resolution, pages: pages.length }));
    } else {
      process.stdout.write(JSON.stringify({
        ok: false, error: "bad_image_size",
        message: `出图尺寸不合格,请按 ${check.expected.width}x${check.expected.height} 重新出图后再画。`,
        expected: check.expected, aspect, resolution, problems: check.errors,
      }));
      process.exit(4);
    }
  } catch (e) { console.error(String((e && e.message) || e)); process.exit(1); }
}
