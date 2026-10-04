#!/usr/bin/env node
// SessionEnd Handler：会话结束时清理会话状态文件。
//
// 输入 (stdin JSON)：
//   { "session_id": "...", "transcript_path": "...", "cwd": "...", "hook_event_name": "SessionEnd", "reason": "other" }
// 输出 (stdout JSON)：
//   { "continue": true, "systemMessage": "..." }
//
// 删除对象（会话状态文件，位于 transcript 目录）：
//   - hook_bash.json
//   - hook_mcp_a.json
//   - hook_mcp_b.json
//   - hook_mcp_c.json
// 保留对象：hook_hr_marker.json（数仓查询标记）
//
// 设计原则（遵循 SessionEnd 官方文档）：
//   - 幂等：文件不存在时跳过，多次执行结果一致
//   - 永不阻塞：所有逻辑 try/catch，异常也返回 continue: true
//   - 快速执行：仅文件删除操作，无网络请求

'use strict';

const fs = require('fs');
const path = require('path');

// 会话状态文件（保留 hook_hr_marker.json）
const STATE_FILES = [
  'hook_bash.json',
  'hook_tool.json',
  'hook_mcp_a.json',
  'hook_mcp_b.json',
  'hook_mcp_c.json'
];

function readStdin() {
  return new Promise((resolve) => {
    let raw = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => { raw += c; });
    process.stdin.on('end', () => {
      try { resolve(JSON.parse(raw)); } catch (_) { resolve({ raw }); }
    });
    process.stdin.on('error', () => resolve({}));
  });
}

function main() {
  return new Promise((resolve) => {
    readStdin().then((inputData) => {
      const transcriptPath = inputData.transcript_path || '';
      const deleted = [];
      const notFound = [];

      // 会话状态文件在 transcript 文件所在目录
      const dir = transcriptPath ? path.dirname(transcriptPath) : '';
      if (dir && fs.existsSync(dir)) {
        for (const name of STATE_FILES) {
          const fp = path.join(dir, name);
          try {
            if (fs.existsSync(fp)) {
              fs.unlinkSync(fp);
              deleted.push(name);
            } else {
              notFound.push(name);
            }
          } catch (_) {
            // 删除失败静默处理，不阻塞会话结束
            notFound.push(name);
          }
        }
      }

      const parts = [];
      if (deleted.length) parts.push('已删除: ' + deleted.join(', '));
      if (notFound.length) parts.push('未找到: ' + notFound.join(', '));
      const msg = '会话状态清理完成。' + (parts.length ? parts.join('；') : '');

      resolve({ continue: true, systemMessage: msg });
    });
  });
}

main().then((out) => {
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
}).catch(() => {
  // 永不阻塞：异常也返回 continue
  try { process.stdout.write(JSON.stringify({ continue: true, systemMessage: '会话状态清理执行异常' })); } catch (_) {}
  process.exit(0);
});
