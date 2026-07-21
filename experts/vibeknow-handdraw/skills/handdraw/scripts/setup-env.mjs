// setup-env.mjs — 首次使用时把专家自带的运行依赖装好，让「纯源码 zip」安装后能自洽运行。
// 装:① 渲染依赖(remotion+react) ② chrome-headless-shell(国内镜像优先) ③ edge-tts(默认 TTS 引擎)。
// (mcp/ 已零依赖 —— 客户端函数只用 Node 内置 fetch/FormData/fs,无需 npm install。)
// 幂等:已装则秒过。依赖装进「专家包内」(render/node_modules、render 的 .remotion 缓存)。
// 用法:  node skills/handdraw/scripts/setup-env.mjs        (可加 --quiet)
import { execFileSync } from "node:child_process";
import { existsSync, writeFileSync, mkdtempSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..", "..");        // 插件根(scripts→handdraw→skills→root)
const RENDER = path.join(ROOT, "render");
const quiet = process.argv.includes("--quiet");
const log = (...a) => { if (!quiet) console.log("[setup]", ...a); };
const run = (cmd, args, cwd) => execFileSync(cmd, args, { cwd, stdio: quiet ? "ignore" : "inherit" });

let did = false;

// ① 渲染依赖
if (!existsSync(path.join(RENDER, "node_modules"))) {
  log("装渲染依赖(remotion + react)…");
  run("npm", ["install", "--silent"], RENDER); did = true;
} else log("渲染依赖已就绪。");

// ② chrome-headless-shell — 国内镜像优先,失败回退官方源
try {
  const cn = execFileSync("node", [path.join(RENDER, "ensure-chrome-cn.mjs")], { cwd: RENDER }).toString().trim();
  if (cn === "PRESENT") {
    log("chrome-headless-shell 已就绪。");
  } else {
    const [url, folder, , verfile, ver] = cn.split("\t");
    log("从国内镜像拉 chrome-headless-shell:", url);
    const tmp = mkdtempSync(path.join(tmpdir(), "chs-"));
    try {
      run("curl", ["-fL", "--retry", "2", "--connect-timeout", "15", "-o", path.join(tmp, "chs.zip"), url]);
      mkdirSync(folder, { recursive: true });   // unzip 不会建不存在的父目录,先建好
      run("unzip", ["-q", "-o", path.join(tmp, "chs.zip"), "-d", folder]);
      writeFileSync(verfile, ver);   // ⚠️ 必须写 VERSION,否则 remotion 判版本不符会重下官方源
      log("镜像安装完成(VERSION=" + ver + ")。");
      did = true;
    } catch (e) {
      log("镜像下载失败,将回退官方源:", String((e && e.message) || e));
    } finally { rmSync(tmp, { recursive: true, force: true }); }
  }
} catch (e) {
  log("镜像预置跳过(", String((e && e.message) || e), "),回退官方源。");
}
// 校验/兜底:若上面已放好则 no-op;否则官方源(可能慢)
try { run("npx", ["--yes", "remotion", "browser", "ensure"], RENDER); } catch (e) {
  log("⚠️ chrome 准备失败,渲染可能不可用:", String((e && e.message) || e));
}

// ③ edge-tts — 默认 TTS 引擎(微软免费音色)。幂等:已装则秒过。装失败不致命(仍可用 vibeknow 引擎)。
try {
  execFileSync("python3", ["-m", "edge_tts", "--list-voices"], { stdio: "ignore" });
  log("edge-tts 已就绪。");
} catch {
  log("装 edge-tts(微软免费 TTS)…");
  try {
    run("python3", ["-m", "pip", "install", "--user", "--quiet", "edge-tts"]);
    execFileSync("python3", ["-m", "edge_tts", "--list-voices"], { stdio: "ignore" }); // 装后自检
    log("edge-tts 安装完成。"); did = true;
  } catch (e) {
    log("⚠️ edge-tts 安装失败,默认 TTS 不可用(可改用 vibeknow 引擎):", String((e && e.message) || e));
  }
}

log(did ? "环境准备完成 ✅" : "环境已就绪，无需安装 ✅");
