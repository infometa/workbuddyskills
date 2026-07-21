#!/usr/bin/env node

const fs = require('fs');
const http = require('http');
const https = require('https');
const path = require('path');

const apiKey = process.env.REGION_INSIGHT_API_KEY;
const baseUrl = process.env.REGION_INSIGHT_MCP_BASE_URL || 'https://mcp.isjike.com';
const ssePath = '/mcp-servers/region-insight/sse';
const size = Number(process.argv[2] || 200);
const bridgePort = Number(process.env.REGION_INSIGHT_BRIDGE_PORT || 8787);
const resultsDir = path.join(__dirname, 'results');
const logDir = path.join(__dirname, 'log');
const endpointsOutput = path.join(logDir, 'session-endpoints.json');
const evidenceOutput = path.join(resultsDir, 'connection-evidence.json');
const bridgeFailuresOutput = path.join(logDir, 'bridge-failures.jsonl');
const sseDisconnectsOutput = path.join(logDir, 'sse-disconnects.jsonl');

if (!apiKey) {
  console.error('REGION_INSIGHT_API_KEY is required');
  process.exit(1);
}
if (!Number.isInteger(size) || size < 200) {
  console.error('session pool size must be an integer of at least 200');
  process.exit(1);
}
if (!Number.isInteger(bridgePort) || bridgePort < 1 || bridgePort > 65535) {
  console.error('REGION_INSIGHT_BRIDGE_PORT must be a valid TCP port');
  process.exit(1);
}

const sessions = [];
const startedAt = Date.now();
let requestSequence = 0;
let roundRobin = 0;
let unexpectedDisconnects = 0;
let bridgeFailureSamples = 0;
let bridge;
let evidenceTimer;

function parseEventStream(state, chunk, onMessage) {
  state.buffer += chunk.toString();
  const blocks = state.buffer.split(/\r?\n\r?\n/);
  state.buffer = blocks.pop() || '';
  for (const block of blocks) {
    const data = block
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n');
    if (data) onMessage(data);
  }
}

function settlePending(session, message) {
  if (!message || message.id === undefined || message.id === null) return;
  const key = String(message.id);
  const pending = session.pending.get(key);
  if (!pending) return;
  session.pending.delete(key);
  clearTimeout(pending.timer);
  if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
  else pending.resolve(message.result);
}

function errorDetail(error) {
  if (!error) return {};
  return {
    name: error.name,
    code: error.code,
    message: error.message,
  };
}

function writeSseDisconnect(session, source, error) {
  fs.appendFileSync(sseDisconnectsOutput, `${JSON.stringify({
    generated_at: new Date().toISOString(),
    session_index: session.index,
    source,
    initialized: session.initialized,
    endpoint: session.endpoint,
    connected_seconds: session.connectedAt ? Math.round((Date.now() - session.connectedAt) / 1000) : 0,
    pending_count: session.pending.size,
    error: errorDetail(error),
  })}\n`);
}

function connect(index) {
  return new Promise((resolve, reject) => {
    const state = {
      index,
      endpoint: '',
      stream: null,
      request: null,
      pending: new Map(),
      connectedAt: 0,
      disconnectedAt: 0,
      initialized: false,
      buffer: '',
    };
    let resolved = false;
    const request = https.request(`${baseUrl}${ssePath}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        Accept: 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      timeout: 30000,
    }, (response) => {
      if (response.statusCode !== 200) {
        response.resume();
        reject(new Error(`session ${index}: HTTP ${response.statusCode}`));
        return;
      }
      state.stream = response;
      state.request = request;
      response.on('data', (chunk) => {
        parseEventStream(state, chunk, (data) => {
          if (!state.endpoint && data.startsWith('/')) {
            state.endpoint = data;
            state.connectedAt = Date.now();
            resolved = true;
            resolve(state);
            return;
          }
          try {
            settlePending(state, JSON.parse(data));
          } catch (_error) {
            // Ignore keepalive or non-JSON SSE events.
          }
        });
      });
      const disconnected = (source, error) => {
        if (state.disconnectedAt) return;
        state.disconnectedAt = Date.now();
        if (state.initialized) unexpectedDisconnects += 1;
        writeSseDisconnect(state, source, error);
        for (const pending of state.pending.values()) {
          clearTimeout(pending.timer);
          pending.reject(error || new Error(`session ${index}: SSE disconnected`));
        }
        state.pending.clear();
        if (!resolved) reject(error || new Error(`session ${index}: SSE ended before endpoint`));
      };
      response.on('aborted', () => disconnected('response_aborted', new Error(`session ${index}: SSE aborted`)));
      response.on('error', (error) => disconnected('response_error', error));
      response.on('end', () => disconnected('response_end', new Error(`session ${index}: SSE ended`)));
      response.on('close', () => disconnected('response_close', new Error(`session ${index}: SSE response closed`)));
    });
    request.on('timeout', () => request.destroy(new Error(`session ${index}: timeout`)));
    request.on('error', (error) => {
      if (!resolved) reject(error);
    });
    request.end();
  });
}

function postMessage(session, method, params = {}, notification = false) {
  return new Promise((resolve, reject) => {
    const id = notification ? undefined : `${Date.now()}-${requestSequence++}`;
    const payload = { jsonrpc: '2.0', method, params };
    if (!notification) payload.id = id;
    const body = JSON.stringify(payload);

    if (!notification) {
      const timer = setTimeout(() => {
        session.pending.delete(String(id));
        reject(new Error(`${method}: timeout waiting for MCP response`));
      }, 30000);
      session.pending.set(String(id), { resolve, reject, timer });
    }

    const request = https.request(`${baseUrl}${session.endpoint}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        Accept: 'application/json, text/event-stream',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
      timeout: 30000,
    }, (response) => {
      let responseBody = '';
      response.on('data', (chunk) => { responseBody += chunk.toString(); });
      response.on('end', () => {
        if (response.statusCode < 200 || response.statusCode >= 300) {
          const pending = id === undefined ? null : session.pending.get(String(id));
          if (pending) {
            session.pending.delete(String(id));
            clearTimeout(pending.timer);
            pending.reject(new Error(`${method}: HTTP ${response.statusCode}`));
          } else if (notification) {
            reject(new Error(`${method}: HTTP ${response.statusCode}`));
          }
          return;
        }
        if (notification) {
          resolve();
          return;
        }
        if (!responseBody.trim()) return;
        const inlineState = { buffer: '' };
        parseEventStream(inlineState, `${responseBody}\n\n`, (data) => {
          try {
            settlePending(session, JSON.parse(data));
          } catch (_error) {
            // The logical response may still arrive on the SSE stream.
          }
        });
        try {
          settlePending(session, JSON.parse(responseBody));
        } catch (_error) {
          // The logical response may still arrive on the SSE stream.
        }
      });
    });
    request.on('timeout', () => request.destroy(new Error(`${method}: HTTP timeout`)));
    request.on('error', (error) => {
      if (notification) {
        reject(error);
        return;
      }
      const pending = session.pending.get(String(id));
      if (!pending) return;
      session.pending.delete(String(id));
      clearTimeout(pending.timer);
      pending.reject(error);
    });
    request.write(body);
    request.end();
  });
}

function activeSessions() {
  return sessions.filter((session) => session.initialized && !session.disconnectedAt);
}

function evidence() {
  const now = Date.now();
  const active = activeSessions();
  return {
    generated_at: new Date(now).toISOString(),
    target: `${baseUrl}${ssePath}`,
    requested_connections: size,
    initialized_connections: sessions.filter((session) => session.initialized).length,
    active_connections: active.length,
    unexpected_disconnects: unexpectedDisconnects,
    pool_uptime_seconds: Math.floor((now - startedAt) / 1000),
    minimum_active_connection_seconds: active.length
      ? Math.floor(Math.min(...active.map((session) => now - session.connectedAt)) / 1000)
      : 0,
  };
}

function writeEvidence() {
  fs.writeFileSync(evidenceOutput, JSON.stringify(evidence(), null, 2));
}

function startBridge() {
  bridge = http.createServer((request, response) => {
    if (request.method === 'GET' && request.url === '/status') {
      response.writeHead(200, { 'Content-Type': 'application/json' });
      response.end(JSON.stringify(evidence()));
      return;
    }
    if (request.method !== 'POST' || request.url !== '/call') {
      response.writeHead(404);
      response.end();
      return;
    }

    let body = '';
    request.on('data', (chunk) => { body += chunk.toString(); });
    request.on('end', async () => {
      const active = activeSessions();
      if (!active.length) {
        response.writeHead(503, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ ok: false, error: 'no active MCP sessions' }));
        return;
      }
      try {
        const parsed = JSON.parse(body);
        const call = parsed.call;
        if (!call || typeof call.name !== 'string' || typeof call.arguments !== 'object') {
          throw new Error('body.call must contain name and arguments');
        }
        const session = active[roundRobin++ % active.length];
        const start = process.hrtime.bigint();
        const result = await postMessage(session, 'tools/call', call);
        const durationMs = Number(process.hrtime.bigint() - start) / 1e6;
        if (result?.isError && bridgeFailureSamples < 20) {
          bridgeFailureSamples += 1;
          fs.appendFileSync(bridgeFailuresOutput, `${JSON.stringify({
            generated_at: new Date().toISOString(),
            tool: call.name,
            duration_ms: durationMs,
            session_index: session.index,
            is_error: true,
            content_preview: (result.content || [])
              .map((item) => item.text || item.content || '')
              .filter(Boolean)
              .join('\n')
              .slice(0, 2000),
          })}\n`);
        }
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({
          ok: !result?.isError,
          duration_ms: durationMs,
          result,
        }));
      } catch (error) {
        if (bridgeFailureSamples < 20) {
          bridgeFailureSamples += 1;
          fs.appendFileSync(bridgeFailuresOutput, `${JSON.stringify({
            generated_at: new Date().toISOString(),
            tool: 'unknown',
            transport_error: error.message,
          })}\n`);
        }
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ ok: false, error: error.message }));
      }
    });
  });
  return new Promise((resolve, reject) => {
    bridge.once('error', reject);
    bridge.listen(bridgePort, '127.0.0.1', resolve);
  });
}

async function main() {
  fs.mkdirSync(resultsDir, { recursive: true });
  fs.mkdirSync(logDir, { recursive: true });
  fs.writeFileSync(bridgeFailuresOutput, '');
  fs.writeFileSync(sseDisconnectsOutput, '');
  for (let start = 0; start < size; start += 10) {
    const connected = await Promise.all(
      Array.from({ length: Math.min(10, size - start) }, (_, offset) => connect(start + offset)),
    );
    await Promise.all(connected.map(async (session) => {
      await postMessage(session, 'initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'region-insight-load-test', version: '1.0.0' },
      });
      await postMessage(session, 'notifications/initialized', {}, true);
      session.initialized = true;
      sessions.push(session);
    }));
    console.log(`created and initialized ${sessions.length}/${size} MCP sessions`);
  }

  const tools = await postMessage(sessions[0], 'tools/list');
  const names = (tools.tools || []).map((tool) => tool.name).sort();
  const expected = [
    'post_region_insight_fence_poi_list',
    'post_region_insight_fence_poi_overview',
    'post_region_insight_poi_location',
  ];
  if (JSON.stringify(names) !== JSON.stringify(expected)) {
    throw new Error(`unexpected tools/list: ${names.join(', ')}`);
  }

  fs.writeFileSync(endpointsOutput, JSON.stringify({
    generated_at: new Date().toISOString(),
    target: `${baseUrl}${ssePath}`,
    count: sessions.length,
    tools: names,
    bridge_url: `http://127.0.0.1:${bridgePort}`,
  }, null, 2));
  writeEvidence();
  evidenceTimer = setInterval(writeEvidence, 10000);
  await startBridge();
  console.log(`load bridge listening on http://127.0.0.1:${bridgePort}`);
  console.log('keep this process running while k6 executes; press Ctrl+C to stop');

  const shutdown = () => {
    clearInterval(evidenceTimer);
    writeEvidence();
    if (bridge) bridge.close();
    for (const session of sessions) {
      session.initialized = false;
      if (session.stream) session.stream.destroy();
      if (session.request) session.request.destroy();
    }
    process.exit(0);
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
