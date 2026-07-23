// workspace.mjs — 为一次手绘生成创建/定位「job 工作目录」,把落盘位置与命名固定下来,
// 让输出可寻、多次会话(换主题重生 / 改某一页)不互相覆盖。
//
// 用法:
//   node workspace.mjs new --topic "白雪公主"
//     → 新建并打印一个 job 目录的绝对路径。本次生成的所有文件都放这个目录下。
//
// 目录: ${HANDDRAW_OUT_DIR:-<当前工作目录>}/<主题slug>-<YYMMDD-HHMMSS>/
//   ⚠️ 默认落在「当前工作目录」下(沙箱可写区);不要放家目录/绝对路径外部——沙箱会拒绝写入。
// 约定布局(见 SKILL.md「落盘约定」):
//   01.png 01.vec.json 01.mp3   ← 第1页:出图 / handdraw 绘制数据 / 旁白音频
//   02.png 02.vec.json 02.mp3   ← 第2页 ...
//   scenes.json                  ← render-reel 的分镜清单(manifest)
//   成片.mp4                     ← 最终输出(固定名,便于寻找/覆盖)
//   .hdprev-public/              ← render 脚本自动生成的临时目录
import { join, isAbsolute, resolve } from "node:path";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

// 主题 → 文件系统安全 slug(保留中文,去掉不安全字符,限长)
export function slug(topic) {
  const s = String(topic || "handdraw")
    .trim()
    .replace(/[\/\\:*?"<>|\s]+/gu, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  return (s || "handdraw").slice(0, 24);
}

export function stamp(d = new Date()) {
  const p = (n) => String(n).padStart(2, "0");
  return `${String(d.getFullYear()).slice(2)}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

// 新建一个 job 目录并返回其绝对路径。
// base 默认 = 当前工作目录(沙箱可写区)。可用 HANDDRAW_OUT_DIR 覆盖(相对路径按 cwd 解析)。
export function newJobDir(topic, base) {
  const raw = base || process.env.HANDDRAW_OUT_DIR || process.cwd();
  const root = isAbsolute(raw) ? raw : resolve(process.cwd(), raw);
  const dir = join(root, `${slug(topic)}-${stamp()}`);
  mkdirSync(dir, { recursive: true });
  return dir;
}

// CLI
if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  const args = process.argv.slice(2);
  const get = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  if (args[0] === "new") {
    process.stdout.write(newJobDir(get("--topic")));
  } else {
    console.error('Usage: node workspace.mjs new --topic "<主题>"');
    process.exit(1);
  }
}
