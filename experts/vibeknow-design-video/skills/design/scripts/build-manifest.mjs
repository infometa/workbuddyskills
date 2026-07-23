// 把 JOBDIR 下的 NN.* 配对成 scenes.json:NN.scene.json 展开为场景,
// NN.bg.jpg|png 和 NN.mp3 转成 data: URI 内联(不传本地路径、不起 server)。
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { findMissingNumbers } from "./scene-schema.mjs";

const DEFAULT_DURATION_FRAMES = 120;
const FPS = 30;
const IMAGE_MIME = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png" };

function fileToDataUri(filePath, mime) {
  const base64 = fs.readFileSync(filePath).toString("base64");
  return `data:${mime};base64,${base64}`;
}

function findBgPath(jobdir, nn) {
  for (const ext of [".jpg", ".jpeg", ".png"]) {
    const p = path.join(jobdir, `${nn}.bg${ext}`);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function probeDurationSeconds(mp3Path) {
  try {
    const out = execFileSync("ffprobe", [
      "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3Path,
    ]).toString().trim();
    const dur = Number(out);
    return Number.isFinite(dur) && dur > 0 ? dur : null;
  } catch {
    return null;
  }
}

// JOBDIR 下所有 NN(两位数字)前缀,来自任意 NN.* 文件(scene.json/bg/mp3)。
function collectNumbers(jobdir) {
  const nums = new Set();
  for (const f of fs.readdirSync(jobdir)) {
    const m = f.match(/^(\d{2,})\./);
    if (m) nums.add(m[1]);
  }
  return [...nums].sort((a, b) => Number(a) - Number(b));
}

// 检查从最小号到最大号是否连续,不连续则报错并列出缺的号(如 01→05,报缺 02,03,04)。
// 连续性判定逻辑与 check-slots.mjs 共用(见 scene-schema.mjs 的 findMissingNumbers)。
function assertContiguous(numbers) {
  const missing = findMissingNumbers(numbers);
  if (missing.length > 0) {
    throw new Error(`场景编号不连续,缺: ${missing.join(",")}`);
  }
}

export function buildManifest(jobdir) {
  const numbers = collectNumbers(jobdir);
  assertContiguous(numbers);
  const scenes = [];
  for (const nn of numbers) {
    const scenePath = path.join(jobdir, `${nn}.scene.json`);
    if (!fs.existsSync(scenePath)) {
      throw new Error(`缺 ${nn}.scene.json(${nn} 号只有资源没有场景定义)`);
    }
    const { layout, slots, themeId, durationInFrames: explicitDuration } = JSON.parse(fs.readFileSync(scenePath, "utf8"));
    const scene = { layout, slots, themeId };

    const bgPath = findBgPath(jobdir, nn);
    if (bgPath) {
      const mime = IMAGE_MIME[path.extname(bgPath).toLowerCase()];
      scene.bgUrl = fileToDataUri(bgPath, mime);
    }

    const mp3Path = path.join(jobdir, `${nn}.mp3`);
    let audioDerived = null;
    if (fs.existsSync(mp3Path)) {
      scene.audioUrl = fileToDataUri(mp3Path, "audio/mpeg");
      const durSec = probeDurationSeconds(mp3Path);
      audioDerived = durSec != null ? Math.round(durSec * FPS) : null;
    }
    // 优先级:scene.json 显式值 > 音频推导 > 默认 120。
    scene.durationInFrames = explicitDuration ?? audioDerived ?? DEFAULT_DURATION_FRAMES;

    scenes.push(scene);
  }

  const scenesPath = path.join(jobdir, "scenes.json");
  fs.writeFileSync(scenesPath, JSON.stringify(scenes, null, 2));
  return scenesPath;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const jobdir = process.argv[2];
  if (!jobdir) { console.error("用法: build-manifest.mjs <JOBDIR>"); process.exit(1); }
  try {
    const out = buildManifest(jobdir);
    process.stdout.write(out);
  } catch (e) {
    console.error(String(e.message || e));
    process.exit(1);
  }
}
