#!/usr/bin/env node
import { openAsBlob } from 'node:fs';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function check(value, code) {
  if (!value) throw new Error(code);
}

// Only unwrap supported MCP envelopes. Signed field values remain opaque strings.
function ticketFrom(value, depth = 0) {
  check(depth < 6, 'INVALID_TICKET');
  if (typeof value === 'string') return ticketFrom(JSON.parse(value), depth + 1);
  check(value && typeof value === 'object' && !value.isError, 'INVALID_TICKET');
  if (value.upload) return value;
  if (value.structuredContent) return ticketFrom(value.structuredContent, depth + 1);
  if (value.result) return ticketFrom(value.result, depth + 1);
  const texts = value.content?.filter(item => item.type === 'text');
  check(texts?.length === 1, 'INVALID_TICKET');
  return ticketFrom(texts[0].text, depth + 1);
}

function validate(ticket, size) {
  const { upload } = ticket;
  check(upload.method === 'POST', 'INVALID_METHOD');
  const url = new URL(upload.url);
  check(url.protocol === 'https:' && !url.username && !url.password && !url.port &&
    !url.search && !url.hash && url.pathname === '/' &&
    /^[a-z0-9-]+\.oss-[a-z0-9-]+\.aliyuncs\.com$/.test(url.hostname), 'UNTRUSTED_UPLOAD_HOST');
  const fields = upload.fields;
  check(fields && typeof fields === 'object' && !Array.isArray(fields), 'INVALID_FIELDS');
  for (const [name, value] of Object.entries(fields)) {
    check(/^[A-Za-z0-9_-]+$/.test(name) && typeof value === 'string' &&
      !['file', 'authorization', 'cookie'].includes(name.toLowerCase()), 'INVALID_FIELDS');
  }
  check(typeof fields.policy === 'string' && /^[A-Za-z0-9+/]+={0,2}$/.test(fields.policy) &&
    fields.policy.length <= 65536 && /^[a-f0-9]{64}$/.test(fields['x-oss-signature']), 'INVALID_TICKET');
  const policy = JSON.parse(Buffer.from(fields.policy, 'base64').toString('utf8'));
  check(Date.parse(policy.expiration) > Date.now(), 'EXPIRED_TICKET');
  check(Array.isArray(policy.conditions), 'INVALID_POLICY');
  for (const condition of policy.conditions) {
    if (Array.isArray(condition)) {
      const [op, field, value] = condition;
      if (op === 'content-length-range') {
        check(Number.isSafeInteger(field) && Number.isSafeInteger(value) && size >= field && size <= value, 'FILE_SIZE_MISMATCH');
      } else {
        check(op === 'eq' && typeof field === 'string' && field.startsWith('$'), 'UNSUPPORTED_POLICY');
        check(fields[field.slice(1)] === value, 'POLICY_FIELD_MISMATCH');
      }
    } else {
      check(condition && typeof condition === 'object', 'INVALID_POLICY');
      for (const [name, value] of Object.entries(condition)) {
        check((name === 'bucket' ? url.hostname.split('.')[0] : fields[name]) === value, 'POLICY_FIELD_MISMATCH');
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
  } finally { await reader.cancel().catch(() => {}); }
  const result = {};
  for (const tag of ['Code', 'RequestId', 'EC']) {
    const value = text.match(new RegExp('<' + tag + '>([A-Za-z0-9_-]{1,128})</' + tag + '>'))?.[1];
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
  form.append('file', await openAsBlob(filename, { type: fields['Content-Type'] }), path.basename(filename));
  try {
    const response = await fetchImpl(ticket.upload.url, {
      method: 'POST', body: form, redirect: 'manual', signal: AbortSignal.timeout(180000),
    });
    if (response.status === 200) {
      await response.body?.cancel();
      return { ok: true, http_status: 200, next_action: 'complete_agent_file_upload' };
    }
    return { ok: false, http_status: response.status, ...await errorDetails(response), next_action: 'get_agent_file_upload' };
  } catch {
    return { ok: false, error: 'TRANSFER_RESULT_UNKNOWN', next_action: 'get_agent_file_upload' };
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const [ticketPath, filename, ...extra] = process.argv.slice(2);
    check(ticketPath && filename && extra.length === 0, 'USAGE: node scripts/upload.mjs response.json file');
    check((await stat(ticketPath)).size <= 1048576, 'TICKET_TOO_LARGE');
    const result = await uploadFile(JSON.parse(await readFile(ticketPath, 'utf8')), filename);
    console.log(JSON.stringify(result));
    if (!result.ok) process.exitCode = 1;
  } catch {
    console.error(JSON.stringify({ ok: false, error: 'LOCAL_UPLOAD_VALIDATION_FAILED', next_action: 'check_original_ticket_and_file' }));
    process.exitCode = 1;
  }
}
