// setup-env.mjs — 首次使用时把设计专家自带的运行依赖装好，让「纯源码 zip」安装后能自洽运行。
// 装:① 渲染依赖(@remotion/renderer + react,装在本目录,package.json 已在计划1建好)
//    ② chrome-headless-shell(程序化 ensureBrowser,失败不致命——首次 render 也会自动下)
//    ③ edge-tts(默认 TTS 引擎)
// 幂等:已装则秒过。依赖装进本目录的 node_modules(已 .gitignore,不提交)。
// 用法:  node skills/design/scripts/setup-env.mjs        (可加 --quiet)
import { spawnSync, execFileSync } from "node:child_process";
import { existsSync, writeFileSync, mkdtempSync, mkdirSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));   // design-expert/skills/design/scripts
const quiet = process.argv.includes("--quiet");
const log = (...a) => { if (!quiet) console.log("[setup]", ...a); };
const run = (cmd, args) => execFileSync(cmd, args, { stdio: quiet ? "ignore" : "inherit" });

let did = false;

// ① 渲染依赖 —— 装在 scripts 目录自身(而非独立的 render/ 子目录)。
if (!existsSync(path.join(HERE, "node_modules"))) {
  log("装渲染依赖(@remotion/renderer + react)…");
  const r = spawnSync("npm", ["install", "--silent"], { cwd: HERE, stdio: quiet ? "ignore" : "inherit" });
  if (r.status !== 0) {
    throw new Error(`npm install 失败(exit ${r.status}): ${String(r.stderr || r.stdout || "")}`.slice(0, 2000));
  }
  did = true;
} else {
  log("渲染依赖已就绪。");
}

// ② chrome-headless-shell —— 国内镜像(npmmirror)优先,失败回退官方源(storage.googleapis.com 国内慢/打不开)。
// 失败仍不致命:首次 renderMedia 时 @remotion/renderer 也会自动补下。
try {
  const cn = execFileSync("node", [path.join(HERE, "ensure-chrome-cn.mjs")], { cwd: HERE }).toString().trim();
  if (cn === "PRESENT") {
    log("chrome-headless-shell 已就绪。");
  } else {
    const [url, folder, , verfile, ver] = cn.split("\t");
    log("从国内镜像拉 chrome-headless-shell:", url);
    const tmp = mkdtempSync(path.join(os.tmpdir(), "ds-chs-"));
    try {
      run("curl", ["-fL", "--retry", "2", "--connect-timeout", "15", "-o", path.join(tmp, "chs.zip"), url]);
      mkdirSync(folder, { recursive: true });   // unzip 不建不存在的父目录,先建好
      run("unzip", ["-q", "-o", path.join(tmp, "chs.zip"), "-d", folder]);
      writeFileSync(verfile, ver);   // ⚠️ 必须写 VERSION,否则 remotion 判版本不符会重下官方源
      log("镜像安装完成(VERSION=" + ver + ")。"); did = true;
    } catch (e) {
      log("镜像下载失败,回退官方源:", String((e && e.message) || e));
      const { ensureBrowser } = await import("@remotion/renderer");
      await ensureBrowser();
    } finally {
      rmSync(tmp, { recursive: true, force: true });
    }
  }
} catch (e) {
  // ensure-chrome-cn 本身跑不起来(如依赖未装全)→ 直接走官方源兜底。
  log("镜像预置跳过(", String((e && e.message) || e), "),回退官方源。");
  try {
    const { ensureBrowser } = await import("@remotion/renderer");
    await ensureBrowser();
  } catch (e2) {
    log("⚠️ chrome 准备失败(不致命,首次 render 会自动下):", String((e2 && e2.message) || e2));
  }
}

// ③ edge-tts — 默认 TTS 引擎(微软免费音色)。幂等:已装则秒过。装失败不致命(仍可手动补装)。
try {
  execFileSync("python3", ["-m", "edge_tts", "--list-voices"], { stdio: "ignore" });
  log("edge-tts 已就绪。");
} catch {
  log("装 edge-tts(微软免费 TTS)…");
  try {
    execFileSync("python3", ["-m", "pip", "install", "--user", "--quiet", "edge-tts"], { stdio: quiet ? "ignore" : "inherit" });
    execFileSync("python3", ["-m", "edge_tts", "--list-voices"], { stdio: "ignore" }); // 装后自检
    log("edge-tts 安装完成。"); did = true;
  } catch (e) {
    log("⚠️ edge-tts 安装失败,旁白 TTS 暂不可用:", String((e && e.message) || e));
  }
}

log(did ? "环境准备完成 ✅" : "环境已就绪，无需安装 ✅");
