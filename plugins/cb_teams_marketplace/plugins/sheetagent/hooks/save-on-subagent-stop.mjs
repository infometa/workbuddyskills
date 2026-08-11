#!/usr/bin/env node
/**
 * SubagentStop hook — 子代理完成时自动保存编辑器池中的脏文件。
 */
import { appendFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const LOG_FILE = join(tmpdir(), "save-on-subagent-stop.log");

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}`;
  process.stderr.write(line + "\n");
  try { appendFileSync(LOG_FILE, line + "\n"); } catch {}
}

const UPSTREAM_URL =
  process.env.TENCENT_DOCS_LOCAL_MCP?.trim() ||
  process.env.SHEET_LOCAL_UPSTREAM_URL?.trim() ||
  "http://127.0.0.1:39099/mcp";

const TIMEOUT_MS = 10_000;

log(`hook started, upstream=${UPSTREAM_URL}`);

async function eatStdin() {
  let data = "";
  process.stdin.setEncoding("utf8");
  for await (const chunk of process.stdin) data += chunk;
  log(`stdin received, ${data.length} bytes`);
  return data;
}

/** 发送 JSON-RPC requests 到上游。自动处理 MCP session。 */
let sessionId = null;

async function mcpJsonRpc(method, params = {}) {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
  };
  if (sessionId) headers["Mcp-Session-Id"] = sessionId;

  const body = JSON.stringify({ jsonrpc: "2.0", method, params, id: 1 });

  log(`>> ${method} ${JSON.stringify(params).slice(0, 200)}`);
  let res;
  try {
    res = await fetch(UPSTREAM_URL, {
      method: "POST", headers, body,
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (e) {
    log(`<< fetch error: ${e.message}`);
    throw e;
  }

  const sid = res.headers.get("mcp-session-id");
  if (sid) { sessionId = sid; log(`session-id: ${sid}`); }

  const text = await res.text();
  log(`<< HTTP ${res.status}, ${text.length} bytes: ${text.slice(0, 500)}`);

  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);

  // Try JSON parse; if it fails, try SSE parse
  try {
    return JSON.parse(text);
  } catch {
    // Parse SSE: "data: {...}\n\n"
    const events = [];
    for (const line of text.split("\n")) {
      if (line.startsWith("data: ")) {
        try { events.push(JSON.parse(line.slice(6))); } catch {}
      }
    }
    if (events.length > 0) return events[events.length - 1]; // last event
    throw new Error(`unparseable response: ${text.slice(0, 200)}`);
  }
}

async function mcpInitialize() {
  log("initializing MCP session...");
  try {
    const res = await mcpJsonRpc("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "save-on-subagent-stop", version: "1.0.0" },
    });
    log(`initialize response: ${JSON.stringify(res).slice(0, 200)}`);
    return true;
  } catch (e) {
    log(`initialize failed: ${e.message}`);
    return false;
  }
}

/** 提取 MCP tools/call 结果的文本与错误状态。 */
function readToolResult(res) {
  const result = res?.result ?? {};
  const isError = result.isError === true;
  const text = (result.content || [])
    .filter((c) => c?.type === "text")
    .map((c) => c.text)
    .join("\n");
  return { isError, text };
}

/**
 * 保存单个文件；对"文件被占用"做有限重试。
 * @returns {Promise<{ok: boolean, occupied: boolean, message: string}>}
 */
async function saveWithRetry(fileId, maxAttempts = 3) {
  let lastOccupied = false;
  let lastMessage = "";
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    let res;
    try {
      res = await mcpJsonRpc("tools/call", {
        name: "save_file",
        arguments: { file_id: fileId },
      });
    } catch (e) {
      log(`save failed (attempt ${attempt}): ${e.message}`);
      return { ok: false, occupied: false, message: e.message };
    }

    const { isError, text } = readToolResult(res);
    if (!isError) {
      log(`save ok: ${text.slice(0, 200)}`);
      return { ok: true, occupied: false, message: text };
    }

    const occupied = /occupied|被占用|10201/i.test(text);
    lastOccupied = occupied;
    lastMessage = text;
    log(`save error (attempt ${attempt}/${maxAttempts}): ${text.slice(0, 200)}`);
    if (!occupied || attempt === maxAttempts) {
      return { ok: false, occupied, message: text };
    }

    // 文件被占用：等待后重试，给上游/外部程序释放锁的时间
    await new Promise((r) => setTimeout(r, 1500));
  }
  return { ok: false, occupied: lastOccupied, message: lastMessage };
}

async function main() {
  const stdinRaw = await eatStdin();
  let payload = {};
  try { payload = JSON.parse(stdinRaw); } catch {}
  const stopHookActive = payload.stop_hook_active === true;
  const eventName = payload.hook_event_name || "unknown";
  log(`event=${eventName}, stop_hook_active=${stopHookActive}`);

  try {
    // 尝试直接调 tools/call
    let poolResult;
    try {
      poolResult = await mcpJsonRpc("tools/call", {
        name: "get_pool_status",
        arguments: {},
      });
    } catch (e) {
      log(`direct call failed (${e.message}), trying with initialize...`);
      if (await mcpInitialize()) {
        poolResult = await mcpJsonRpc("tools/call", {
          name: "get_pool_status",
          arguments: {},
        });
      } else {
        throw e;
      }
    }

    const content = poolResult?.result?.content || [];
    log(`pool has ${content.length} content items`);

    for (const item of content) {
      if (item.type !== "text") continue;
      let data;
      try { data = JSON.parse(item.text); } catch { continue; }

      const editors = data?.open_editors || [];
      log(`found ${editors.length} editors, dirty=${editors.filter(e => e.is_dirty).length}`);

      for (const editor of editors) {
        if (!editor.is_dirty || !editor.file_id) continue;

        log(`saving: file_id=${editor.file_id}, path=${editor.file_path}`);
        const r = await saveWithRetry(editor.file_id);
        if (!r.ok) {
          const path = editor.file_path || editor.file_id;
          log(`unsaved: ${path}${r.occupied ? " (occupied)" : ""} — ${(r.message || "").slice(0, 120)}`);
        }
      }
    }
  } catch (e) {
    log(`fatal: ${e.message}${e.stack ? '\n' + e.stack : ''}`);
  }

  log("hook finished");
  process.exit(0);
}

main();
