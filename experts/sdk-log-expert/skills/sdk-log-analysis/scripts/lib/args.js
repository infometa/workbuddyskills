const PREVIEW_DISABLED = new Set(['0', 'false', 'off', 'no', '']);

export function isPreviewEnabled() {
  const v = String(process.env.SDK_LOG_PREVIEW ?? '1').trim().toLowerCase();
  return !PREVIEW_DISABLED.has(v);
}

export function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) {
      out._.push(a);
      continue;
    }
    const eq = a.indexOf('=');
    if (eq >= 0) {
      out[a.slice(2, eq)] = a.slice(eq + 1);
      continue;
    }
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next == null || next.startsWith('--')) out[key] = 'true';
    else {
      out[key] = next;
      i++;
    }
  }
  return out;
}

export function fail(message, code = 1) {
  process.stderr.write(`[error] ${message}\n`);
  process.exit(code);
}

export function info(message) {
  process.stderr.write(`[info]  ${message}\n`);
}

export function parseTimeArg(value) {
  if (value == null || value === '') return null;
  const s = String(value);
  if (/^\d{10,13}$/.test(s)) {
    const n = Number(s);
    return s.length === 10 ? n * 1000 : n;
  }
  const m = s.match(/^(\d{4})[-/](\d{2})[-/](\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/);
  if (m) return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]).getTime();
  const t = Date.parse(s);
  if (!Number.isNaN(t)) return t;
  fail(`无法解析时间: ${value}`);
}

export function formatTs(ms) {
  const d = new Date(ms);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export function makeSessionId(prefix = 'log') {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  const ts = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
  return `${prefix}-${ts}-${Math.random().toString(16).slice(2, 8)}`;
}
