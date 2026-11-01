import { spawnSync } from "node:child_process";
import { accessSync, constants, existsSync, readFileSync, realpathSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// This bundled policy is validated by the connector builder, independently of CLI test evidence.
export const cliPolicy = Object.freeze(JSON.parse(readFileSync(new URL("./cli-policy.json", import.meta.url), "utf8")));

function fail(code, message) {
  throw Object.assign(new Error(message), { code });
}

export function npmEntry(env = process.env, platform = process.platform) {
  const searchPath = env[Object.keys(env).find((key) => key.toUpperCase() === "PATH") ?? "PATH"] ?? "";
  for (const directory of searchPath.split(platform === "win32" ? ";" : ":")) {
    if (!path.isAbsolute(directory)) continue;
    const executable = path.join(directory, platform === "win32" ? "npm.cmd" : "npm");
    try {
      accessSync(executable, platform === "win32" ? constants.F_OK : constants.X_OK);
      if (!statSync(executable).isFile()) continue;
    } catch { continue; }
    if (platform !== "win32") return { command: executable, args: [] };
    // Standard npm .cmd layout: execute its Node entry without cmd.exe or shell interpolation.
    const script = path.join(path.dirname(realpathSync(executable)), "node_modules/npm/bin/npm-cli.js");
    if (!existsSync(script)) fail("NPM_LAYOUT", "无法定位 npm.cmd 对应的 Node 入口，请检查宿主的 npm 安装。");
    return { command: process.execPath, args: [script] };
  }
  fail("NPM_MISSING", "未找到 npm，请在 WorkBuddy 托管的 Node.js 环境中运行。");
}

function stableVersion(version) {
  const match = typeof version === "string" && /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.exec(version);
  return match && match.slice(1).map(BigInt);
}

export function acceptsVersion(version) {
  const actual = stableVersion(version);
  const minimum = stableVersion(cliPolicy.minimumVersion);
  if (!actual || !minimum) return false;
  for (let i = 0; i < 3; i++) {
    if (actual[i] !== minimum[i]) return actual[i] > minimum[i];
  }
  return true;
}

export async function runLatest(args, { env = process.env, platform = process.platform, run = spawnSync, request = fetch } = {}) {
  const npm = npmEntry(env, platform);
  const options = { env, shell: false };
  const registry = `--registry=${cliPolicy.registry}`;
  // Node fetch has no persistent npm metadata cache (npm view may serve stale data on network errors).
  let version;
  try {
    const response = await request(new URL(`${cliPolicy.package}/${cliPolicy.tag}`, cliPolicy.registry), {
      signal: AbortSignal.timeout(15000), redirect: "error", headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("Registry response failed");
    version = (await response.json())?.version;
  } catch {
    fail("LATEST_UNAVAILABLE", "无法查询公网 npm latest；请检查网络后重试。本次未执行业务，也未回退到旧版本。");
  }
  if (!acceptsVersion(version)) {
    fail("LATEST_INVALID", `latest 必须指向不低于 ${cliPolicy.minimumVersion} 的稳定版本，本次未执行业务。`);
  }
  // Pin only this invocation's resolution. npm owns the versioned cache; never replace a running global CLI.
  const result = run(npm.command, [...npm.args, "exec", `--prefix=${path.dirname(fileURLToPath(import.meta.url))}`,
    "--yes", "--prefer-online", "--offline=false", "--include=optional",
    registry, "--fetch-retries=0", "--fetch-timeout=15000", `--package=${cliPolicy.package}@${version}`,
    "--", cliPolicy.bin, ...args], { ...options, stdio: "inherit" });
  if (result.error) fail("CLI_START_FAILED", "无法启动 latest CLI；未自动重试业务，请检查 npm 和终端环境。");
  return { version, status: result.status, signal: result.signal };
}

if (process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const result = await runLatest(process.argv.slice(2));
    if (result.signal) process.kill(process.pid, result.signal);
    else process.exitCode = result.status ?? 1;
  } catch (error) {
    process.stderr.write(`[connector:${error.code ?? "LAUNCH_FAILED"}] ${error.message}\n`);
    process.exitCode = 1;
  }
}
