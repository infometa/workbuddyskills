#!/usr/bin/env node
// ensure-chrome-cn.mjs — 从国内镜像(阿里 npmmirror)预置 Remotion 的 chrome-headless-shell,
// 避开 storage.googleapis.com(国内慢/打不开)。放到 Remotion 期望的缓存目录后,
// `remotion browser ensure` 即视为已装、跳过官方下载;镜像失败则由 install 脚本回退官方源。
//
// 自动算平台/版本/缓存路径(与 Remotion 内部一致),不写死。输出(给 install 脚本消费):
//   已存在且版本匹配 → 打印 "PRESENT"
//   需下载 → 打印 "<镜像URL>\t<解压目标目录>\t<可执行文件路径>\t<VERSION文件路径>\t<版本号>"
// ⚠️ Remotion 除查二进制外还查 <cache>/chrome-headless-shell/VERSION(内容=版本号)是否 == 锁定版本,
//   不写 VERSION 会被判「版本不符」重下官方源。故解压后必须把版本号写进该 VERSION 文件。
import os from "node:os";
import path from "node:path";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url)); // = render/

function platform() {
  const a = os.arch();
  switch (os.platform()) {
    case "darwin": return a === "arm64" ? "mac-arm64" : "mac-x64";
    case "linux": return a === "arm64" ? "linux-arm64" : "linux64";
    case "win32": return "win64";
    default: throw new Error("unsupported platform: " + os.platform());
  }
}

// 从已安装的 @remotion/renderer 读出它锁定的 chrome 版本(随 remotion 升级自动跟随)。
function testedVersion() {
  const esm = path.join(HERE, "node_modules", "@remotion", "renderer", "dist", "esm", "index.mjs");
  const m = readFileSync(esm, "utf8").match(/TESTED_VERSION\s*=\s*"([0-9.]+)"/);
  if (!m) throw new Error("无法从 @remotion/renderer 读取 TESTED_VERSION");
  return m[1];
}

const plat = platform();
const ver = testedVersion();
// Remotion(npm 安装)缓存: <render>/node_modules/.remotion/chrome-headless-shell/{VERSION, <platform>/...}
const cacheRoot = path.join(HERE, "node_modules", ".remotion", "chrome-headless-shell");
const versionFile = path.join(cacheRoot, "VERSION");
const folderPath = path.join(cacheRoot, plat);
const exe = path.join(
  folderPath,
  `chrome-headless-shell-${plat}`,
  plat === "win64" ? "chrome-headless-shell.exe" : "chrome-headless-shell",
);

// 已存在需同时满足:二进制在 + VERSION 文件内容 == 锁定版本(否则 Remotion 判版本不符会重下)。
const versionOk = existsSync(versionFile) && readFileSync(versionFile, "utf8").trim() === ver;
if (existsSync(exe) && versionOk) {
  process.stdout.write("PRESENT");
} else {
  const url = `https://cdn.npmmirror.com/binaries/chrome-for-testing/${ver}/${plat}/chrome-headless-shell-${plat}.zip`;
  process.stdout.write(`${url}\t${folderPath}\t${exe}\t${versionFile}\t${ver}`);
}
