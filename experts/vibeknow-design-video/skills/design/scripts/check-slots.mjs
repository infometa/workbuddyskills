#!/usr/bin/env node
// check-slots.mjs — 掏钱前(出图 ImageGen / 合旁白 tts 之前)的本地 slot 校验 CLI。
// 只管"填得对不对"(layout 存在 / 必填齐 / 没超长 / textArray 没超 maxItems),
// 不掺时长判断——此时原始 NN.scene.json 可能还没写 durationInFrames(SOP 里它可选,
// 由 build-manifest 后填,来自显式值/音频推导/默认值),也还没有 NN.mp3。
// scene-schema.mjs 的 validateScenes 无条件要求 durationInFrames > 0,
// 所以这里在校验前给每屏注入占位时长(不改原始 NN.scene.json,不透传给 validateScenes 之外的任何地方),
// 避免"还没定时长"被误判成不合格。
import fs from "node:fs";
import path from "node:path";
import { validateScenes, findMissingNumbers } from "./scene-schema.mjs";
import { resolveBundle } from "./resolve-bundle.mjs";

// 缺省 manifest 走 resolveBundle():已 unlock 解锁完整 manifest(50 主题)则校验对完整主题库,
// 否则对自带免费 manifest(只认 serious-dark)。版式(layout)全部免费,不受此门禁影响。
const DEFAULT_MANIFEST = () => resolveBundle().manifestPath;
const PLACEHOLDER_DURATION = 120; // 与 build-manifest.mjs 的 DEFAULT_DURATION_FRAMES 一致,仅用于绕过校验,不写回文件

// JOBDIR 下所有 NN.scene.json 的编号,按数值升序(与 build-manifest.mjs 的收号逻辑一致口径)。
function collectSceneNumbers(jobdir) {
  const nums = [];
  for (const f of fs.readdirSync(jobdir)) {
    const m = f.match(/^(\d{2,})\.scene\.json$/);
    if (m) nums.push(m[1]);
  }
  nums.sort((a, b) => Number(a) - Number(b));
  return nums;
}

// 纯逻辑:给定 JOBDIR + manifest 路径,返回 { ok, problems? , count? }。供 CLI 与测试直接调用。
export function checkSlots(jobdir, manifestPath = DEFAULT_MANIFEST()) {
  const numbers = collectSceneNumbers(jobdir);
  if (numbers.length === 0) {
    return { ok: false, problems: [{ n: 0, reason: `JOBDIR 下没有找到任何 NN.scene.json: ${jobdir}` }] };
  }
  // 与 build-manifest.mjs 的 assertContiguous 口径对齐的闸:已有 NN.scene.json 号从最小到最大不能缺号
  // (不要求从 01 开始)。这里必须在 build-manifest 之前拦,否则要等到出图/配音后才会报错,太晚。
  const missingNumbers = findMissingNumbers(numbers);
  if (missingNumbers.length > 0) {
    return { ok: false, problems: [{ n: 0, reason: `场景编号不连续,缺: ${missingNumbers.join(",")}` }] };
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const scenes = numbers.map((nn) => {
    const raw = JSON.parse(fs.readFileSync(path.join(jobdir, `${nn}.scene.json`), "utf8"));
    // 关键:别把原始 scene 直接透传给 validateScenes——注入占位时长后再校验,
    // 这样 check-slots 只拦 slot 合规问题,不因"还没定时长"误拒。
    return { ...raw, durationInFrames: raw.durationInFrames ?? PLACEHOLDER_DURATION };
  });
  const v = validateScenes(scenes, manifest);
  if (!v.ok) return { ok: false, problems: v.errors };
  return { ok: true, count: scenes.length };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const jobdir = process.argv[2];
  if (!jobdir) { console.error("用法: check-slots.mjs <JOBDIR>"); process.exit(1); }
  try {
    const result = checkSlots(jobdir);
    process.stdout.write(JSON.stringify(result) + "\n");
    process.exit(result.ok ? 0 : 4);
  } catch (e) {
    console.error(String(e.message || e));
    process.exit(1);
  }
}
