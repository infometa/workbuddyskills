// scripts/lib/safe-output.js
// Helpers for rendering untrusted log content into Markdown / chat UI safely.
// Node built-ins only.

const URL_RE = /https?:\/\/[^\s'"<>`\])}]+/gi;
const BASIC_AUTH_RE = /Authorization:\s*Basic\s+[A-Za-z0-9+/=]+/gi;
const BEARER_AUTH_RE = /Authorization:\s*Bearer\s+[^\s,;|]+/gi;
const SECRET_RE = /\b(token|password|passwd|secret|signature|sign|x-cos-security-token|x-amz-[a-z0-9-]+)\s*[:=]\s*([^\s,;|]+)/gi;
const ANSI_RE = /\x1B\[[0-?]*[ -/]*[@-~]/g;
const BIDI_RE = /[\u202A-\u202E\u2066-\u2069]/g;
const UNSAFE_CONTROL_RE = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g;

function toText(value) {
  return value == null ? '' : String(value);
}

export function stripUnsafeControlChars(input) {
  return toText(input)
    .replace(ANSI_RE, '')
    .replace(BIDI_RE, '')
    .replace(UNSAFE_CONTROL_RE, '');
}

export function redactSensitiveText(input) {
  return stripUnsafeControlChars(input)
    .replace(BASIC_AUTH_RE, 'Authorization: <redacted>')
    .replace(BEARER_AUTH_RE, 'Authorization: <redacted>')
    .replace(URL_RE, '<redacted-url>')
    .replace(SECRET_RE, '$1=<redacted>');
}

export function truncateText(input, maxChars = 1000) {
  const text = toText(input);
  const max = Number(maxChars);
  if (!Number.isFinite(max) || max <= 0 || text.length <= max) return text;
  return `${text.slice(0, Math.max(0, max - 1))}…`;
}

export function neutralizeMarkdown(input) {
  return toText(input)
    .replace(/</g, '‹')
    .replace(/>/g, '›')
    .replace(/\[/g, '［')
    .replace(/\]/g, '］')
    .replace(/\(/g, '（')
    .replace(/\)/g, '）');
}

export function safeMarkdownTableCell(input, { maxChars = 280 } = {}) {
  return truncateText(
    neutralizeMarkdown(redactSensitiveText(input))
      .replace(/\|/g, '│')
      .replace(/\s+/g, ' ')
      .trim(),
    maxChars,
  );
}

function maxBacktickRun(text) {
  let max = 0;
  for (const match of toText(text).matchAll(/`+/g)) {
    max = Math.max(max, match[0].length);
  }
  return max;
}

export function safeCodeBlock(input, lang = 'text') {
  const text = redactSensitiveText(input);
  const fence = '`'.repeat(Math.max(3, maxBacktickRun(text) + 1));
  const language = String(lang || 'text').replace(/[^a-z0-9_-]/gi, '') || 'text';
  return `${fence}${language}\n${text}\n${fence}`;
}

export function safeEvidenceLine(lineNo, text, { maxChars = 1000 } = {}) {
  const sanitized = truncateText(
    redactSensitiveText(text)
      .replace(/\|/g, '│')
      .replace(/\r?\n/g, ' ↩ '),
    maxChars,
  );
  return `L${lineNo}: ${sanitized}`;
}
