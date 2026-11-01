/** Local upload adapter: inspect originals; then send bytes using narrow, short-lived grants. */
import { constants } from "node:fs";
import { lstat, open, readFile, rm, writeFile } from "node:fs/promises";
import { basename, extname, isAbsolute, resolve } from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
const LIMIT = 20 * 1024 * 1024;
const mimeTypes = {
  ".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".webp": "image/webp", ".gif": "image/gif", ".txt": "text/plain", ".csv": "text/csv",
  ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
};
const digest = bytes => createHash("sha256").update(bytes).digest("hex");
function validatePaths(pathList) {
  if (!Array.isArray(pathList) || pathList.length < 1 || pathList.length > 10 ||
      pathList.some(path => typeof path !== "string" || !isAbsolute(path))) throw new Error("path_list must contain 1–10 explicit absolute original file paths");
  if (new Set(pathList).size !== pathList.length) throw new Error("Duplicate file path");
}
async function original(path) {
  // No shell execution or symlink following; bound reads protect against changed files.
  const chosen = await lstat(path);
  if (!chosen.isFile() || chosen.isSymbolicLink()) throw new Error("Only explicit regular original files are accepted");
  const handle = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const stat = await handle.stat();
    if (stat.ino !== chosen.ino || stat.dev !== chosen.dev) throw new Error("Original changed while opening");
    if (!stat.isFile() || stat.size < 1 || stat.size > LIMIT) throw new Error("Original must be a regular nonempty file no larger than 20MB");
    const bytes = Buffer.alloc(stat.size + 1);
    let length = 0;
    while (length < bytes.length) {
      const read = await handle.read(bytes, length, bytes.length - length, length);
      if (!read.bytesRead) break;
      length += read.bytesRead;
    }
    if (length !== stat.size) throw new Error("Original changed while being read");
    return bytes.subarray(0, length);
  } finally { await handle.close(); }
}
export async function inspectFiles(pathList) {
  validatePaths(pathList);
  const files = [];
  for (const path of pathList) {
    const mime_type = mimeTypes[extname(path).toLowerCase()];
    if (!mime_type) throw new Error("Unsupported file extension");
    const bytes = await original(path);
    files.push({ name: basename(path), size: bytes.length, sha256: digest(bytes), mime_type });
  }
  return { files };
}
function validatePlan(plan, pathList, origin) {
  const base = new URL(origin);
  if (base.protocol !== "https:" || base.username || base.password || base.pathname !== "/" || base.search || base.hash) throw new Error("Use the explicitly approved SealAI HTTPS origin");
  if (!plan || !Array.isArray(plan.files) || plan.files.length !== pathList.length) throw new Error("Plan must match every selected original");
  const ids = new Set();
  for (const [i, grant] of plan.files.entries()) {
    if (typeof grant.file_id !== "string" || !/^[a-f0-9-]{36}$/.test(grant.file_id) || ids.has(grant.file_id)) throw new Error("Invalid or duplicate upload ID");
    ids.add(grant.file_id);
    const target = new URL(grant.upload_url);
    if (target.href !== `${base.origin}/api/mcp/finance/uploads/${grant.file_id}` ||
        grant.name !== basename(pathList[i]) || !/^[A-Za-z0-9_-]{43}$/.test(grant.upload_token) ||
        !Number.isFinite(grant.expires_at) || grant.expires_at <= Date.now()) throw new Error("Upload grant does not match the approved origin, file or lifetime");
  }
}
export async function uploadFiles(pathList, plan, origin, request = fetch) {
  validatePaths(pathList);
  validatePlan(plan, pathList, origin);
  const files = [];
  for (const [i, path] of pathList.entries()) {
    const grant = plan.files[i];
    try {
      const bytes = await original(path);
      if (bytes.length !== grant.size || digest(bytes) !== grant.sha256 || mimeTypes[extname(path).toLowerCase()] !== grant.mime_type) throw new Error("Original changed after inspection");
      const response = await request(grant.upload_url, {
        method: "POST", redirect: "error", signal: AbortSignal.timeout(90_000),
        headers: { Authorization: `Bearer ${grant.upload_token}`, "Content-Type": "application/octet-stream" },
        body: bytes,
      });
      if (!response.ok) throw new Error(`Upload failed with HTTP ${response.status}`);
      const result = await response.json();
      if (result.file_id !== grant.file_id || result.sha256 !== grant.sha256 || result.size !== bytes.length || result.text !== grant.name || result.mimeType !== grant.mime_type || result.uri !== `${new URL(origin).origin}/api/mcp/finance/files/${grant.file_id}`) throw new Error("Upload receipt mismatch");
      files.push({ path, status: "uploaded", ...result });
    } catch {
      // Never echo credentials, URLs with secrets, arbitrary server text or file contents.
      files.push({ path, file_id: grant.file_id, status: "failed_or_uncertain", message: "Check MCP upload status before retrying; preserve originals and do not submit an incomplete draft." });
    }
  }
  return { files, complete: files.every(file => file.status === "uploaded") };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [command, ...args] = process.argv.slice(2);
  const flags = {};
  for (let i = 0; i < args.length; i += 2) flags[args[i]] = args[i + 1];
  try {
    const paths = JSON.parse(await readFile(flags["--paths"], "utf8"));
    if (command === "inspect") {
      console.log(JSON.stringify(await inspectFiles(paths), null, 2));
    } else if (command === "upload") {
      const planPath = flags["--plan"];
      try {
        const planHandle = await open(planPath, constants.O_RDONLY | constants.O_NOFOLLOW);
        let plan;
        try {
          await planHandle.chmod(0o600);
          const stat = await planHandle.stat();
          if (!stat.isFile() || stat.size > 65536) throw new Error("Invalid plan file");
          plan = JSON.parse(await planHandle.readFile("utf8"));
        } finally { await planHandle.close(); }
        const result = await uploadFiles(paths, plan, flags["--origin"]);
        if (flags["--result"]) await writeFile(flags["--result"], JSON.stringify(result, null, 2), { mode: 0o600, flag: "wx" });
        console.log(JSON.stringify(result, null, 2));
        if (!result.complete) process.exitCode = 1;
      } finally { await rm(planPath, { force: true }); }
    } else throw new Error("Usage: inspect --paths <json-array-file> OR upload --paths <json-array-file> --plan <short-lived-grants-json> --origin <approved-https-origin> [--result <new-json-file>]");
  } catch { console.error("Upload adapter failed; verify explicit paths, plan and approved origin. No credentials were logged."); process.exitCode = 1; }
}
