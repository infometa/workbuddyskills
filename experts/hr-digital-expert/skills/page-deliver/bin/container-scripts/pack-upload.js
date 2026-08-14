#!/usr/bin/env node
/**
 * pack-upload — 打包用户项目 + 上传到 deliver-api / COS
 *
 * 零依赖、纯 Node.js 内置模块。
 * 由 page-deliver skill 携带，CLI 部署时上传到 AnyDev 容器 /data/services/bin/pack-upload。
 *
 * 用法:
 *   PACK_PROJECT_ID=my-app-20260601 PACK_PROJECT_DIR=/data/services/apps/my-app-20260601 node pack-upload.js
 *   DELIVER_API_URL=http://deliver-api-test.woa.com:8080  (可选的，默认测试环境)
 *   node pack-upload.js --version
 *
 * 输出 (stdout, 单行 JSON):
 *   {"status":"ok","projectId":"...","version":2,"cosKey":"..."}
 *   {"status":"error","code":"PACK_FAILED","reason":"...","hint":"...","retryable":true}
 */
'use strict';

const VERSION = '0.1.3';
const { execSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const https = require('https');
const os = require('os');
const path = require('path');

// ============================================================================
// HRGW 认证（硬编码, 与 deliver-timer 一致）
// ============================================================================
const HRGW_APP_NAME  = process.env.HRGW_APP_NAME || 'hrit_manager';
const HRGW_APP_TOKEN = process.env.HRGW_APP_TOKEN || '';

// ============================================================================
// Dockerfile 默认模板（内置 fallback）
// 完整维护版本见 SKILL_DIR/assets/templates/dockerfile/
// ============================================================================
const DOCKERFILE_TMPL_NODE = `FROM mirrors.tencent.com/hrit/oa-node-runtime:v1

LABEL version="v1.0"

WORKDIR /app

# 先 COPY package.json，利用 Docker 层缓存
COPY package.json ./
RUN npm install

# 拷贝源码（排除 node_modules、data/ 等运行时目录由 .dockerignore 处理）
COPY . .

# 给 prod-deploy.sh 可执行权限（作为 ENTRYPOINT 直接执行需要）
RUN chmod +x /app/.agent/scripts/*.sh 2>/dev/null || true

# 生产环境变量
ENV PORT=3000
ENV MONGO_URI=mongodb://{{PROJECT_ID}}-mongo:27017
ENV AGENT_SVR_ENV=prod

EXPOSE 3000 9999

# ENTRYPOINT：优先执行 prod-deploy.sh（启动 MCP Bridge + 注册 Agent），
# 脚本不存在或 SKIP_PROD_DEPLOY=1 时直接 exec CMD（node server.js）
# 注意：bash -c 必须用 -- 分隔脚本和 $@ 参数，否则 CMD 不会正确映射到 $@
ENTRYPOINT ["bash", "-c", "if [ -f /app/.agent/scripts/prod-deploy.sh ] && [ \\\"\${SKIP_PROD_DEPLOY}\\\" != 1 ]; then /app/.agent/scripts/prod-deploy.sh \\\"$@\\\"; else exec \\\"$@\\\"; fi", "--"]
CMD ["node", "server.js"]
`;

const DOCKERFILE_TMPL_PYTHON = `FROM csighub.tencentyun.com/garen/base:tencentos4

# 安装 Python 3.11
RUN dnf install -y python3.11 python3.11-pip && \\
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \\
    ln -sf /usr/bin/python3.11 /usr/bin/python && \\
    ln -sf /usr/bin/pip3.11 /usr/bin/pip && \\
    python3 --version && pip --version && \\
    dnf clean all && rm -rf /var/cache/dnf

# 预装公共依赖（与 AnyDev 镜像保持一致）
RUN pip install --no-cache-dir \\
    flask \\
    gunicorn \\
    pymongo \\
    python-dotenv \\
    requests

WORKDIR /app

# 先 COPY requirements.txt，利用 Docker 层缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝源码（排除 venv/、__pycache__/ 等由 .dockerignore 处理）
COPY . .

# 生产环境变量
ENV PORT=3000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV MONGO_URI=mongodb://{{PROJECT_ID}}-mongo:27017

EXPOSE 3000
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "120", "app:app"]
`;

// ============================================================================
// 工具函数
// ============================================================================
function exitError(code, reason, hint, retryable) {
  const out = { status: 'error', code, reason, hint, retryable };
  process.stdout.write(JSON.stringify(out) + '\n');
  process.exit(1);
}

function result(status, data) {
  const out = { status, ...data };
  process.stdout.write(JSON.stringify(out) + '\n');
}

function hrSign () {
  const ts = Date.now().toString();
  const raw = HRGW_APP_NAME + HRGW_APP_TOKEN + ts;
  const sig = crypto.createHash('sha256').update(raw).digest('hex');
  return {
    'hrgw-appname': HRGW_APP_NAME,
    'hrgw-timestamp': ts,
    'hrgw-signature': sig,
  };
}

function httpRequest (method, url, opts = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const mod = u.protocol === 'https:' ? https : http;
    const headers = { ...hrSign(), ...opts.headers };
    const req = mod.request(u, { method, headers, timeout: opts.timeout || 300000 }, (res) => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) });
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('request timeout')); });
    if (opts.body) req.write(opts.body);
    req.end();
  });
}

function apiGet(baseURL, path) {
  return httpRequest('GET', baseURL + path);
}

async function apiPost(baseURL, path, formData) {
  // 手动构造 multipart — 零外部依赖
  const boundary = '----PackUpload' + Date.now();
  const CRLF = '\r\n';
  const parts = [];
  for (const [name, val] of Object.entries(formData)) {
    parts.push(
      `--${boundary}${CRLF}` +
      `Content-Disposition: form-data; name="${name}"${CRLF}${CRLF}` +
      `${val}${CRLF}`
    );
  }
  parts.push(`--${boundary}--${CRLF}`);
  const body = parts.join('');

  const res = await httpRequest('POST', baseURL + path, {
    body,
    headers: { 'Content-Type': `multipart/form-data; boundary=${boundary}` },
  });
  return res;
}

// ============================================================================
// 版本查询: 调 deliver-api db_latest → current + 1
// ============================================================================
async function resolveVersion(baseURL, projectId) {
  const res = await apiGet(baseURL, `/openapi/archives/db_latest?projectId=${encodeURIComponent(projectId)}`);
  const body = res.body.toString();

  let apiResp;
  try { apiResp = JSON.parse(body); } catch (e) {
    throw new Error(`parse response: ${e.message}`);
  }

  if (apiResp.code === 400) throw new Error(`project not found: ${apiResp.message}`);
  // 404 = no archive yet → start at v1
  if (apiResp.code === 404) return 1;
  if (apiResp.code !== 0) throw new Error(`api error code=${apiResp.code}: ${apiResp.message}`);

  const archive = apiResp.data;
  const cur = parseInt((archive.version || '').replace('v', ''), 10) || 0;
  return cur + 1;
}

// ============================================================================
// Dockerfile ENV 强制归一
// 生产 mongo sidecar 地址由 projectId 唯一决定，服务端口固定 3000。项目里写成别的
// 值（旧 projectId、localhost、8080 等）都会让容器连错库或健康检查失败，
// 故打包时无条件重写为规范值。
// ============================================================================
const PROD_PORT = '3000';

function mongoUriFor(projectId) {
  return `mongodb://${projectId}-mongo:27017`;
}

/**
 * 把 Dockerfile 里的 `ENV <name>` 强制改为 value，该 ENV 缺失时插入一条。
 * value 不能含空格（`mongodb://…` / `3000` 均满足），否则调用方需自行加引号。
 */
function enforceEnv(content, name, value) {
  const lines = content.split('\n');

  // 反斜杠续行会把一条指令拆到多行，按「逻辑指令」而非物理行遍历，
  // 否则续行片段会被误判成独立指令（或整段被 legacy 分支吞掉）。
  const instrs = [];  // { start, end, text }  end 为 inclusive 行号
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*(#|$)/.test(lines[i])) continue;
    const start = i;
    while (i < lines.length - 1 && /\\\s*$/.test(lines[i])) i++;
    instrs.push({ start, end: i, text: lines.slice(start, i + 1).join('\n') });
  }

  const envKeywordRe = /^\s*ENV\s+/i;   // ENV 关键字大小写不敏感（Docker 语义）
  const isEnv = x => envKeywordRe.test(x.text);
  const argsOf = x => x.text.slice(x.text.match(envKeywordRe)[0].length);
  // 变量名大小写敏感（Docker 语义），故以下两个正则不加 /i；
  // `(^|\s)` 边界顺带避免误伤 MY_PORT= 之类的同后缀变量名。
  const legacyRe = new RegExp(`^${name}\\s+[^=\\s]`);                              // `ENV NAME value`（无 =）
  const assignRe = new RegExp(`(^|\\s)${name}\\s*=\\s*(?:"[^"]*"|'[^']*'|\\S*)`);  // `ENV A=1 NAME=v B=2`
  const targets = instrs.filter(x => isEnv(x) && (legacyRe.test(argsOf(x)) || assignRe.test(argsOf(x))));

  if (targets.length > 0) {
    // 从后往前改，避免多行指令替换后行号错位
    for (const instr of targets.reverse()) {
      const indent = (instr.text.match(/^\s*/) || [''])[0];
      // legacy 形式的值是指令剩余全部内容 → 整条重写；
      // 赋值形式只换该变量的值，保留同指令里的其他变量。
      const replacement = legacyRe.test(argsOf(instr))
        ? `${indent}ENV ${name}=${value}`
        : instr.text.replace(assignRe, `$1${name}=${value}`);
      lines.splice(instr.start, instr.end - instr.start + 1, ...replacement.split('\n'));
    }
    return lines.join('\n');
  }

  // 缺失 → 补一条。优先跟在最后一条 ENV 之后，其次插到 EXPOSE/ENTRYPOINT/CMD 之前，
  // 兜底追加到末尾。
  const lastEnv = [...instrs].reverse().find(isEnv);
  let at;
  if (lastEnv) {
    at = lastEnv.end + 1;
  } else {
    const boundary = instrs.find(x => /^\s*(EXPOSE|ENTRYPOINT|CMD)\s/i.test(x.text));
    at = boundary ? boundary.start : lines.length;
  }

  lines.splice(at, 0, `ENV ${name}=${value}`);
  return lines.join('\n');
}

function enforceDockerfileEnv(content, projectId) {
  const withPort = enforceEnv(content, 'PORT', PROD_PORT);
  return enforceEnv(withPort, 'MONGO_URI', mongoUriFor(projectId));
}

// ============================================================================
// 打包: zip 项目目录 + 处理 Dockerfile（保留已有 / 按类型注入默认模板）
// ============================================================================
function createArchive(projectDir, projectId, version, projectType) {
  const zipName = `${projectId}-v${version}.zip`;
  const zipPath = path.join(os.tmpdir(), zipName);

  // 1. 复制到临时目录
  const tmpDir = path.join(os.tmpdir(), `pack-${projectId}-${Date.now()}`);
  fs.mkdirSync(tmpDir, { recursive: true });
  execSync(`cp -a "${projectDir}/." "${tmpDir}/"`, { stdio: 'pipe' });

  // 2. 删除需排除的通用目录 & 文件
  const rmDirs = [path.join(tmpDir, 'node_modules'), path.join(tmpDir, '.git')];
  for (const d of rmDirs) {
    if (fs.existsSync(d)) execSync(`rm -rf "${d}"`, { stdio: 'pipe' });
  }
  // Python 项目额外排除
  if (projectType === 'python') {
    const pyExcludes = ['__pycache__', '.venv', 'venv', 'env', '.pytest_cache',
      '*.egg-info', 'dist', 'build'];
    for (const name of pyExcludes) {
      try {
        const p = name.includes('*')
          ? tmpDir : path.join(tmpDir, name);
        if (name.includes('*')) {
          execSync(`find "${p}" -name '${name}' -type f -delete`, { stdio: 'pipe' });
        } else if (fs.existsSync(p)) {
          execSync(`rm -rf "${p}"`, { stdio: 'pipe' });
        }
      } catch (_) {}
    }
    // 删除 .pyc / .pyo 文件
    try { execSync(`find "${tmpDir}" -name '*.py[co]' -type f -delete`, { stdio: 'pipe' }); } catch (_) {}
  }
  // 删除 *.log 文件
  try { execSync(`find "${tmpDir}" -name '*.log' -type f -delete`, { stdio: 'pipe' }); } catch (_) {}

  // 3. Dockerfile 处理：保留已有并替换 {{PROJECT_ID}}，无则按类型注入默认模板
  //    两种情况都强制归一 ENV PORT=3000 与 ENV MONGO_URI=mongodb://{projectId}-mongo:27017
  const dockerfile = path.join(tmpDir, 'Dockerfile');
  if (fs.existsSync(dockerfile)) {
    // 已有 Dockerfile → 保留，替换 {{PROJECT_ID}} 占位符（仅改打包副本，不回写项目目录）
    const raw = fs.readFileSync(dockerfile, 'utf-8').replace(/{{PROJECT_ID}}/g, projectId);
    fs.writeFileSync(dockerfile, enforceDockerfileEnv(raw, projectId));
  } else {
    // 无 Dockerfile → 按 projectType 选默认模板注入，同步落盘到项目根目录
    const tmpl = projectType === 'python' ? DOCKERFILE_TMPL_PYTHON : DOCKERFILE_TMPL_NODE;
    const dockerfileContent = enforceDockerfileEnv(tmpl.replace(/{{PROJECT_ID}}/g, projectId), projectId);
    fs.writeFileSync(dockerfile, dockerfileContent);
    fs.writeFileSync(path.join(projectDir, 'Dockerfile'), dockerfileContent);
  }

  // 3. zip 打包（AnyDev 镜像已预装 zip）
  execSync(`cd "${tmpDir}" && zip -qr "${zipPath}" .`, { stdio: 'pipe' });

  // 4. 清理临时目录
  execSync(`rm -rf "${tmpDir}"`, { stdio: 'pipe' });

  return { zipPath, zipName };
}

// ============================================================================
// 上传: multipart → deliver-api /openapi/archives/upload
// ============================================================================
async function uploadArchive(baseURL, zipPath, zipName, projectId, version, staffName) {
  const zipBuf = fs.readFileSync(zipPath);

  // 手动构造 multipart（零外部依赖）
  const boundary = '----PackUpload' + Date.now();
  const CRLF = '\r\n';
  const nowMs = Date.now();
  const fields = {
    projectId,
    version: `v${version}`,
    lastUptime: nowMs.toString(),
    lastModTime: Math.floor(nowMs / 1000).toString(),
  };
  // staffName 可选：传了就直接用，避免服务端再查 DB
  if (staffName) {
    fields.staffName = staffName;
  }

  let bodyParts = '';
  for (const [name, val] of Object.entries(fields)) {
    bodyParts +=
      `--${boundary}${CRLF}` +
      `Content-Disposition: form-data; name="${name}"${CRLF}${CRLF}` +
      `${val}${CRLF}`;
  }
  bodyParts +=
    `--${boundary}${CRLF}` +
    `Content-Disposition: form-data; name="file"; filename="${zipName}"${CRLF}` +
    `Content-Type: application/zip${CRLF}${CRLF}`;

  const headBuf = Buffer.from(bodyParts, 'utf8');
  const tailBuf = Buffer.from(`${CRLF}--${boundary}--${CRLF}`, 'utf8');

  const body = Buffer.concat([headBuf, zipBuf, tailBuf]);

  const res = await httpRequest('POST', baseURL + '/openapi/archives/upload', {
    body,
    headers: { 'Content-Type': `multipart/form-data; boundary=${boundary}` },
  });

  const respBody = res.body.toString();
  if (res.status !== 200) {
    throw new Error(`upload failed status=${res.status} body=${respBody}`);
  }

  let apiResp;
  try { apiResp = JSON.parse(respBody); } catch (e) {
    throw new Error(`parse response: ${e.message}`);
  }

  if (apiResp.code !== 0) {
    throw new Error(`api error code=${apiResp.code}: ${apiResp.message}`);
  }
}

// ============================================================================
// main
// ============================================================================
(async function main() {
  // --version
  if (process.argv.includes('--version') || process.argv.includes('-version')) {
    process.stdout.write(VERSION + '\n');
    process.exit(0);
  }

  const projectId = (process.env.PACK_PROJECT_ID || '').trim();
  const projectDir = (process.env.PACK_PROJECT_DIR || '').trim();
  const projectType = (process.env.PACK_PROJECT_TYPE || '').trim() || 'node';
  const staffName = (process.env.PACK_STAFF_NAME || '').trim();
  const baseURL = (process.env.DELIVER_API_URL || '').trim() || 'http://deliver-api-test.woa.com:8080';

  if (!projectId || !projectDir) {
    exitError('MISSING_PARAMS', 'PACK_PROJECT_ID and PACK_PROJECT_DIR are required',
      'Set both env vars and re-run', false);
  }

  if (!fs.existsSync(projectDir)) {
    exitError('INVALID_DIR', `project directory not found: ${projectDir}`,
      'Check PACK_PROJECT_DIR points to an existing directory', false);
  }

  let newVersion;
  try {
    newVersion = await resolveVersion(baseURL, projectId);
  } catch (e) {
    exitError('VERSION_FAILED', e.message,
      'Ensure the deliver-api is reachable and the project exists', true);
  }

  let zipPath, zipName;
  try {
    const archive = createArchive(projectDir, projectId, newVersion, projectType);
    zipPath = archive.zipPath; zipName = archive.zipName;
  } catch (e) {
    exitError('PACK_FAILED', `failed to create archive: ${e.message}`,
      'Check project directory structure and retry. For large node_modules, it is automatically excluded.', true);
  }

  try {
    await uploadArchive(baseURL, zipPath, zipName, projectId, newVersion, staffName);
  } catch (e) {
    try { fs.unlinkSync(zipPath); } catch (_) {}
    exitError('UPLOAD_FAILED', `failed to upload archive: ${e.message}`,
      'Ensure deliver-api is reachable and retry. Network timeout may occur for large archives.', true);
  }

  try { fs.unlinkSync(zipPath); } catch (_) {}

  result('ok', {
    projectId,
    version: newVersion,
    cosKey: `(auto-generated by deliver-api) ${projectId}/v${newVersion}`,
  });
})();
