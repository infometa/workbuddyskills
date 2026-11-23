#!/usr/bin/env node
import { openAsBlob, createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function check(value, code) {
  if (!value) throw new Error(code);
}

const TICKET_ENDPOINT = 'https://app.yihook.cn/api/mcp/file-upload-tickets';
const TRANSFER_CODE_PATTERN =
  /^([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})\.([A-Za-z0-9_-]{43})$/;

function ticketEndpoint(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error('UNTRUSTED_TICKET_ENDPOINT');
  }
  const production =
    url.protocol === 'https:' &&
    !url.port &&
    ['app.yihook.cn', 'app.yihook.ai'].includes(url.hostname);
  const loopback =
    ['http:', 'https:'].includes(url.protocol) &&
    ['localhost', '127.0.0.1'].includes(url.hostname);
  check(
    (production || loopback) &&
      value === url.href &&
      !url.username &&
      !url.password &&
      !url.search &&
      !url.hash &&
      url.pathname === '/api/mcp/file-upload-tickets',
    'UNTRUSTED_TICKET_ENDPOINT',
  );
  return url.href;
}

async function phase(name, run, onProgress = () => {}) {
  const started = performance.now();
  onProgress({ phase: name, state: 'started', elapsed_ms: 0 });
  const timer = setInterval(
    () =>
      onProgress({
        phase: name,
        state: 'running',
        elapsed_ms: Math.round(performance.now() - started),
      }),
    5000,
  );
  timer.unref();
  try {
    const result = await run();
    onProgress({
      phase: name,
      state: result?.ok === false ? 'failed' : 'completed',
      elapsed_ms: Math.round(performance.now() - started),
    });
    return result;
  } catch (error) {
    onProgress({
      phase: name,
      state: 'failed',
      elapsed_ms: Math.round(performance.now() - started),
    });
    throw error;
  } finally {
    clearInterval(timer);
  }
}

async function readTicket(response) {
  const reader = response.body?.getReader();
  check(reader, 'INVALID_TICKET_RESPONSE');
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.length;
      check(size <= 1048576, 'TICKET_TOO_LARGE');
      chunks.push(Buffer.from(part.value));
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new Error('INVALID_TICKET_RESPONSE');
  }
}

export async function uploadWithTransfer(
  code,
  filename,
  { fetchImpl = fetch, onProgress, ticketUrl = TICKET_ENDPOINT } = {},
) {
  const started = performance.now();
  const endpoint = ticketEndpoint(ticketUrl);
  const match =
    typeof code === 'string' ? code.match(TRANSFER_CODE_PATTERN) : null;
  check(match, 'INVALID_TRANSFER_CODE');
  const info = await stat(filename);
  check(info.isFile() && info.size > 0, 'INVALID_FILE');
  const ticketStarted = performance.now();
  const claimed = await phase(
    'ticket',
    async () => {
      let response;
      try {
        response = await fetchImpl(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code }),
          redirect: 'manual',
          signal: AbortSignal.timeout(30000),
        });
      } catch {
        return { ok: false, error: 'TICKET_RESULT_UNKNOWN' };
      }
      if (response.status !== 200) {
        await response.body?.cancel();
        return {
          ok: false,
          error: 'TICKET_CLAIM_FAILED',
          http_status: response.status,
        };
      }
      return { ok: true, ticket: await readTicket(response) };
    },
    onProgress,
  );
  const ticketMs = Math.round(performance.now() - ticketStarted);
  if (!claimed.ok)
    return {
      ...claimed,
      phase: 'ticket',
      next_action: 'get_agent_file_upload',
      timings_ms: {
        ticket_ms: ticketMs,
        total_ms: Math.round(performance.now() - started),
      },
    };
  const ticket = ticketFrom(claimed.ticket);
  check(ticket.upload_id === match[1], 'UPLOAD_SESSION_MISMATCH');
  check(ticket.size_bytes === info.size, 'FILE_SIZE_MISMATCH');
  check(/^[a-f0-9]{64}$/.test(ticket.sha256), 'INVALID_TICKET_RESPONSE');
  const validationStarted = performance.now();
  await phase(
    'file_validation',
    async () => {
      const hash = createHash('sha256');
      for await (const bytes of createReadStream(filename)) hash.update(bytes);
      check(hash.digest('hex') === ticket.sha256, 'FILE_HASH_MISMATCH');
    },
    onProgress,
  );
  const transferStarted = performance.now();
  const result = await phase(
    'transfer',
    () => uploadFile(ticket, filename, { fetchImpl }),
    onProgress,
  );
  return {
    ...result,
    phase: 'transfer',
    timings_ms: {
      ticket_ms: ticketMs,
      file_validation_ms: Math.round(transferStarted - validationStarted),
      transfer_ms: Math.round(performance.now() - transferStarted),
      total_ms: Math.round(performance.now() - started),
    },
  };
}

// Only unwrap supported MCP envelopes. Signed field values remain opaque strings.
function ticketFrom(value, depth = 0) {
  check(depth < 6, 'INVALID_TICKET');
  if (typeof value === 'string')
    return ticketFrom(JSON.parse(value), depth + 1);
  check(value && typeof value === 'object' && !value.isError, 'INVALID_TICKET');
  if (value.upload) return value;
  if (value.structuredContent)
    return ticketFrom(value.structuredContent, depth + 1);
  if (value.result) return ticketFrom(value.result, depth + 1);
  const texts = value.content?.filter((item) => item.type === 'text');
  check(texts?.length === 1, 'INVALID_TICKET');
  return ticketFrom(texts[0].text, depth + 1);
}

function validate(ticket, size) {
  const { upload } = ticket;
  check(upload.method === 'POST', 'INVALID_METHOD');
  const url = new URL(upload.url);
  check(
    url.protocol === 'https:' &&
      !url.username &&
      !url.password &&
      !url.port &&
      !url.search &&
      !url.hash &&
      url.pathname === '/' &&
      /^[a-z0-9-]+\.oss-[a-z0-9-]+\.aliyuncs\.com$/.test(url.hostname),
    'UNTRUSTED_UPLOAD_HOST',
  );
  const fields = upload.fields;
  check(
    fields && typeof fields === 'object' && !Array.isArray(fields),
    'INVALID_FIELDS',
  );
  for (const [name, value] of Object.entries(fields)) {
    check(
      /^[A-Za-z0-9_-]+$/.test(name) &&
        typeof value === 'string' &&
        !['file', 'authorization', 'cookie'].includes(name.toLowerCase()),
      'INVALID_FIELDS',
    );
  }
  check(
    typeof fields.policy === 'string' &&
      /^[A-Za-z0-9+/]+={0,2}$/.test(fields.policy) &&
      fields.policy.length <= 65536 &&
      /^[a-f0-9]{64}$/.test(fields['x-oss-signature']),
    'INVALID_TICKET',
  );
  const policy = JSON.parse(
    Buffer.from(fields.policy, 'base64').toString('utf8'),
  );
  check(Date.parse(policy.expiration) > Date.now(), 'EXPIRED_TICKET');
  check(Array.isArray(policy.conditions), 'INVALID_POLICY');
  for (const condition of policy.conditions) {
    if (Array.isArray(condition)) {
      const [op, field, value] = condition;
      if (op === 'content-length-range') {
        check(
          Number.isSafeInteger(field) &&
            Number.isSafeInteger(value) &&
            size >= field &&
            size <= value,
          'FILE_SIZE_MISMATCH',
        );
      } else {
        check(
          op === 'eq' && typeof field === 'string' && field.startsWith('$'),
          'UNSUPPORTED_POLICY',
        );
        check(fields[field.slice(1)] === value, 'POLICY_FIELD_MISMATCH');
      }
    } else {
      check(condition && typeof condition === 'object', 'INVALID_POLICY');
      for (const [name, value] of Object.entries(condition)) {
        check(
          (name === 'bucket' ? url.hostname.split('.')[0] : fields[name]) ===
            value,
          'POLICY_FIELD_MISMATCH',
        );
      }
    }
  }
  check(fields.key && fields['Content-Type'], 'INVALID_FIELDS');
}

async function errorDetails(response) {
  // Never print the OSS body: it may echo policy, credentials or signatures.
  const reader = response.body?.getReader();
  if (!reader) return {};
  let text = '';
  try {
    let size = 0;
    while (size < 16384) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.length;
      text += Buffer.from(part.value).toString('utf8');
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  const result = {};
  for (const tag of ['Code', 'RequestId', 'EC']) {
    const value = text.match(
      new RegExp('<' + tag + '>([A-Za-z0-9_-]{1,128})</' + tag + '>'),
    )?.[1];
    if (value) result[tag] = value;
  }
  return result;
}

export async function uploadFile(raw, filename, { fetchImpl = fetch } = {}) {
  const ticket = ticketFrom(raw);
  const info = await stat(filename);
  check(info.isFile() && info.size > 0, 'INVALID_FILE');
  validate(ticket, info.size);
  const fields = ticket.upload.fields;
  const form = new FormData();
  for (const [name, value] of Object.entries(fields)) form.append(name, value);
  form.append(
    'file',
    await openAsBlob(filename, { type: fields['Content-Type'] }),
    path.basename(filename),
  );
  try {
    const response = await fetchImpl(ticket.upload.url, {
      method: 'POST',
      body: form,
      redirect: 'manual',
      signal: AbortSignal.timeout(180000),
    });
    if (response.status === 200) {
      await response.body?.cancel();
      return {
        ok: true,
        http_status: 200,
        next_action: 'complete_agent_file_upload',
      };
    }
    return {
      ok: false,
      http_status: response.status,
      ...(await errorDetails(response)),
      next_action: 'get_agent_file_upload',
    };
  } catch {
    return {
      ok: false,
      error: 'TRANSFER_RESULT_UNKNOWN',
      next_action: 'get_agent_file_upload',
    };
  }
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  try {
    const args = process.argv.slice(2);
    const onProgress = (value) =>
      process.stderr.write(JSON.stringify(value) + '\n');
    let result;
    if (args[0] === '--transfer') {
      check(
        args.length === 3 || (args.length === 5 && args[3] === '--ticket-url'),
        'INVALID_ARGUMENTS',
      );
      result = await uploadWithTransfer(args[1], args[2], {
        onProgress,
        ticketUrl: args[4],
      });
    } else {
      const [ticketPath, filename, ...extra] = args;
      check(ticketPath && filename && extra.length === 0, 'INVALID_ARGUMENTS');
      check((await stat(ticketPath)).size <= 1048576, 'TICKET_TOO_LARGE');
      result = await phase(
        'transfer',
        async () =>
          uploadFile(JSON.parse(await readFile(ticketPath, 'utf8')), filename),
        onProgress,
      );
    }
    console.log(JSON.stringify(result));
    if (!result.ok) process.exitCode = 1;
  } catch (error) {
    const known = new Set([
      'INVALID_ARGUMENTS',
      'INVALID_TRANSFER_CODE',
      'INVALID_FILE',
      'INVALID_TICKET',
      'INVALID_TICKET_RESPONSE',
      'TICKET_TOO_LARGE',
      'INVALID_METHOD',
      'UNTRUSTED_UPLOAD_HOST',
      'UNTRUSTED_TICKET_ENDPOINT',
      'INVALID_FIELDS',
      'EXPIRED_TICKET',
      'INVALID_POLICY',
      'UNSUPPORTED_POLICY',
      'POLICY_FIELD_MISMATCH',
      'FILE_SIZE_MISMATCH',
      'FILE_HASH_MISMATCH',
      'UPLOAD_SESSION_MISMATCH',
    ]);
    const code = known.has(error.message)
      ? error.message
      : 'INVALID_FILE_OR_TICKET';
    console.error(
      JSON.stringify({
        ok: false,
        error: 'LOCAL_UPLOAD_VALIDATION_FAILED',
        code,
        next_action: 'check_upload_session_and_file',
      }),
    );
    process.exitCode = 1;
  }
}
