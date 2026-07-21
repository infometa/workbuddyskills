#!/usr/bin/env node
// get-token.js - WPS Authorization Tool (Node.js)
// Usage: node get-token.js [--auto-install-mcporter|-AutoInstallMcporter]

const runtimeRequire = typeof require === "function" ? require : null;

let fs;
let path;
let https;
let crypto;
let spawnSync;

const MCP_URL = "https://mcp-center.wps.cn/skill_hub/mcp";
const AUTH_EXCHANGE_URL =
  "https://api.wps.cn/office/v5/ai/skill_hub/wps_auth/exchange";
const AUTO_INSTALL_MCPORTER =
  process.argv.includes("--auto-install-mcporter") ||
  process.argv.includes("-AutoInstallMcporter");

async function importBuiltin(specifier) {
  const mod = await import(specifier);
  return mod.default || mod;
}

async function ensureNodeModules() {
  if (fs && path && https && crypto && spawnSync) {
    return;
  }

  if (runtimeRequire) {
    fs = runtimeRequire("node:fs");
    path = runtimeRequire("node:path");
    https = runtimeRequire("node:https");
    crypto = runtimeRequire("node:crypto");
    ({ spawnSync } = runtimeRequire("node:child_process"));
    return;
  }

  fs = await importBuiltin("node:fs");
  path = await importBuiltin("node:path");
  https = await importBuiltin("node:https");
  crypto = await importBuiltin("node:crypto");
  ({ spawnSync } = await importBuiltin("node:child_process"));
}

function getScriptDir() {
  const scriptPath = process.argv[1]
    ? path.resolve(process.argv[1])
    : path.join(process.cwd(), "get-token.js");

  return path.dirname(scriptPath);
}

function getLegacyEnvFile() {
  return path.join(getScriptDir(), ".env");
}

function getSkillFile() {
  return path.join(getScriptDir(), "SKILL.md");
}

function getSkillVersion() {
  const skillFile = getSkillFile();

  if (!fs.existsSync(skillFile)) {
    return "unknown";
  }

  for (const line of fs.readFileSync(skillFile, "utf8").split(/\r?\n/)) {
    const match = line.match(/^version:\s*(.+)/);
    if (match) {
      return match[1].trim();
    }
  }

  return "unknown";
}

function extractToken(resp) {
  if (resp && resp.data && resp.data.token) {
    return resp.data.token;
  }

  if (resp && resp.token) {
    return resp.token;
  }

  return null;
}

function extractExpires(resp) {
  if (resp && resp.data && resp.data.expires_in) {
    return Number.parseInt(resp.data.expires_in, 10) || 0;
  }

  if (resp && resp.expires_in) {
    return Number.parseInt(resp.expires_in, 10) || 0;
  }

  return 0;
}

function extractRespCode(resp) {
  if (resp && resp.code !== undefined && resp.code !== null) {
    return String(resp.code);
  }

  return "";
}

function quotePowerShellArgument(value) {
  return `'${String(value).replace(/'/g, "''")}'`;
}

function buildPowerShellCommand(command, args) {
  return `& ${quotePowerShellArgument(command)} ${args
    .map(quotePowerShellArgument)
    .join(" ")}`;
}

function trySpawnSync(command, args, options = {}) {
  if (process.platform === "win32") {
    return spawnSync(
      "powershell.exe",
      [
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        buildPowerShellCommand(command, args),
      ],
      {
        stdio: "ignore",
        windowsHide: true,
        shell: false,
        ...options,
      }
    );
  }

  return spawnSync(command, args, {
    stdio: "ignore",
    windowsHide: true,
    shell: false,
    ...options,
  });
}

function isCommandAvailable(command) {
  const result = trySpawnSync(command, ["--version"]);

  return !result.error && result.status === 0;
}

function runCommand(command, args, options = {}) {
  const result = trySpawnSync(command, args, options);

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    throw new Error(`${command} exited with code ${result.status}`);
  }

  return result;
}

function ensureMcporter() {
  if (isCommandAvailable("mcporter")) {
    return;
  }

  if (AUTO_INSTALL_MCPORTER) {
    if (isCommandAvailable("npm")) {
      try {
        runCommand("npm", ["install", "-g", "mcporter"]);
      } catch (error) {
        // Ignore install failure and keep the original error handling below.
      }
    } else {
      throw new Error(
        "mcporter is missing and npm is unavailable. Install mcporter manually or rerun with --auto-install-mcporter (or -AutoInstallMcporter) in an npm-enabled environment."
      );
    }
  }

  if (!isCommandAvailable("mcporter")) {
    throw new Error(
      "mcporter is required to save the kdocs config. Default behavior will not auto-install globally. Install mcporter manually, or rerun with --auto-install-mcporter (or -AutoInstallMcporter)."
    );
  }
}

function normalizeToken(token) {
  if (typeof token !== "string") {
    return "";
  }

  const trimmed = token.trim();
  if (!trimmed) {
    return "";
  }

  const match = trimmed.match(/^Bearer\s+(.+)$/i);
  return match ? match[1].trim() : trimmed;
}

function setMcporterConfig(token, version) {
  const normalizedToken = normalizeToken(token);

  if (!normalizedToken) {
    throw new Error("Cannot update mcporter config with an empty token.");
  }

  ensureMcporter();

  try {
    runCommand("mcporter", ["config", "remove", "kdocs"]);
  } catch (error) {
    // Ignore remove failures so we can overwrite the config below.
  }

  const mcArgs = [
    "config",
    "add",
    "kdocs",
    MCP_URL,
    "--header",
    `Authorization=Bearer ${normalizedToken}`,
    "--header",
    `X-Skill-Version=${version}`,
    "--transport",
    "http",
    "--scope",
    "home",
  ];

  runCommand("mcporter", mcArgs);
}

function removeLegacyEnvTokenKey() {
  const legacyEnvFile = getLegacyEnvFile();

  if (!fs.existsSync(legacyEnvFile)) {
    return;
  }

  try {
    const lines = fs.readFileSync(legacyEnvFile, "utf8").split(/\r?\n/);
    const kept = [];
    let hasToken = false;

    for (const line of lines) {
      if (line.startsWith("KINGSOFT_DOCS_TOKEN=")) {
        hasToken = true;
        continue;
      }
      kept.push(line);
    }

    if (!hasToken) {
      return;
    }

    const nonEmptyKept = kept.filter((line) => line !== "");

    if (nonEmptyKept.length === 0) {
      fs.rmSync(legacyEnvFile, { force: true });
      console.log(
        "[OK] Removed KINGSOFT_DOCS_TOKEN from .env and deleted empty .env file."
      );
      return;
    }

    fs.writeFileSync(legacyEnvFile, `${kept.join("\n")}\n`, "utf8");
    console.log(
      "[OK] Removed KINGSOFT_DOCS_TOKEN from .env while preserving other keys."
    );
  } catch (error) {
    // Keep parity with the shell/PowerShell versions: cleanup failure is non-fatal.
  }
}

function generateCode() {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().toLowerCase();
  }

  const bytes = crypto.randomBytes(16);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = bytes.toString("hex");

  return [
    hex.slice(0, 8),
    hex.slice(8, 12),
    hex.slice(12, 16),
    hex.slice(16, 20),
    hex.slice(20, 32),
  ].join("-");
}

function trySpawnSyncNative(command, args, options = {}) {
  return spawnSync(command, args, {
    stdio: "ignore",
    windowsHide: true,
    shell: false,
    ...options,
  });
}

function didCommandSucceed(result) {
  return Boolean(result) && !result.error && result.status === 0;
}

function openBrowser(url) {
  if (process.platform === "win32") {
    const windowsLaunchers = [
      [
        "powershell.exe",
        [
          "-NoProfile",
          "-NonInteractive",
          "-Command",
          `Start-Process ${quotePowerShellArgument(url)}`,
        ],
      ],
      ["explorer.exe", [url]],
      ["rundll32.exe", ["url.dll,FileProtocolHandler", url]],
      ["cmd.exe", ["/d", "/s", "/c", `start "" "${url}"`]],
    ];

    return windowsLaunchers.some(([command, args]) =>
      didCommandSucceed(trySpawnSyncNative(command, args))
    );
  }

  const opener = process.platform === "darwin" ? "open" : "xdg-open";
  return didCommandSucceed(trySpawnSyncNative(opener, [url]));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function postJson(url, payload) {
  const body = JSON.stringify(payload);

  return new Promise((resolve, reject) => {
    const req = https.request(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
      },
      (res) => {
        let raw = "";

        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          raw += chunk;
        });
        res.on("end", () => {
          try {
            resolve(raw ? JSON.parse(raw) : {});
          } catch (error) {
            reject(error);
          }
        });
      }
    );

    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  const code = generateCode();
  const cb = `https://api.wps.cn/office/v5/ai/skill_hub/users/callback?code=${code}`;
  const encodedCb = encodeURIComponent(cb);
  const loginUrl = `https://account.wps.cn/login?cb=${encodedCb}`;

  console.log("");
  console.log("Open the link below in your browser to sign in with your WPS account:");
  console.log("");
  console.log(`  ${loginUrl}`);
  console.log("");

  if (!openBrowser(loginUrl)) {
    console.log(
      "[!] Cannot open browser automatically. Please copy the link above manually."
    );
  }

  console.log("Waiting for login...");

  const timeoutSeconds = 300;
  const intervalSeconds = 1;
  const startTime = Date.now();
  let token = null;

  while (true) {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);

    if (elapsed >= timeoutSeconds) {
      console.log("");
      console.log("[!] Timed out. Please run the script again.");
      process.exit(1);
    }

    try {
      const resp = await postJson(AUTH_EXCHANGE_URL, { code });
      const rc = extractRespCode(resp);
      const tok = extractToken(resp);

      if (rc === "200" && tok) {
        token = tok;
        break;
      }

      if (rc === "202" && elapsed % 5 === 0) {
        process.stdout.write(".");
      }
    } catch (error) {
      // Network hiccup, keep polling.
    }

    await sleep(intervalSeconds * 1000);
  }

  console.log("");
  console.log("[OK] Login successful. kdocs Skill is ready.");

  try {
    setMcporterConfig(token, getSkillVersion());
    removeLegacyEnvTokenKey();
    console.log("[OK] Updated kdocs config in mcporter.");
  } catch (error) {
    console.log("[!] Failed to update mcporter config.");
    console.log(error.message);
    process.exit(1);
  }
}

async function run() {
  await ensureNodeModules();
  await main();
}

run().catch((error) => {
  console.log("[!] Failed to complete login.");
  console.log(error.message);
  process.exit(1);
});
