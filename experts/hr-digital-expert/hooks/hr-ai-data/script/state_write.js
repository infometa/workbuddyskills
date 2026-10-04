// =============================================================================
// state_write.js — 会话状态写入器（供模型通过 Bash 调用）
// =============================================================================
// 【为什么需要它】
// 模型若用 Edit/Write 工具改会话状态文件，该文件会通过 ACP 协议的 toolInfoFromToolUse
// 上报 locations:[{path:file_path}] 给 IDE，出现在「文件列表 / 保留 / 撤销」面板中，
// 用户一点「撤销」即回滚 risk_status，导致 hook 状态机失效。
// Bash 工具的 ACP 上报只有 {title, kind:"execute", content}，不含 locations，
// 因此改由模型执行 Bash 命令写状态，面板不会出现文件条目，也没有可撤销的 diff。
//
// 【为什么不让模型直接用 shell 重定向写 JSON】
// 手写 JSON 经 shell 传递需处理引号/转义/编码，跨 bash 与 PowerShell 行为不一致，
// 极易写出损坏的 JSON 导致状态丢失。本脚本让模型只传「字段名 + 值」，
// JSON 的读取-合并-写回全部由 Node 完成，保证与原 patchJSON 语义完全一致。
//
// 用法（三种子命令，覆盖原 Edit/Write 的全部用途）：
//   node state_write.js set    <file> <key> <value> [<key> <value> ...]   指定字段赋值（可多对）
//   node state_write.js append <file> <arrayKey> <value>                  数组末尾追加（去重）
//   node state_write.js now    <file> <key>                              字段设为当前 ISO 时间
// 说明：
//   - set/append/now 均为「读取-合并-写回」，其他字段一律保持不变（等价于原 patchJSON）。
//   - 文件或父目录不存在时自动创建；内容损坏时按空对象重建，避免卡死状态机。
//   - 路径含空格时用引号包裹整个参数。

const fs = require('fs');
const path = require('path');

function readJSON(fp) {
  try { return fs.existsSync(fp) ? (JSON.parse(fs.readFileSync(fp, 'utf8')) || {}) : {}; }
  catch (_) { return {}; }
}

function writeJSON(fp, obj) {
  const dir = path.dirname(fp);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(fp, JSON.stringify(obj, null, 2), 'utf8');
}

function main() {
  const argv = process.argv.slice(2);
  const action = argv[0];
  const file = argv[1];
  const rest = argv.slice(2);

  if (!action || !file) {
    console.error('用法: node state_write.js <set|append|now> <file> ...');
    process.exit(2);
  }

  const obj = readJSON(file);

  if (action === 'set') {
    if (rest.length === 0 || rest.length % 2 !== 0) {
      console.error('set 需要成对的 <key> <value> 参数');
      process.exit(2);
    }
    for (let i = 0; i < rest.length; i += 2) obj[rest[i]] = rest[i + 1];
  } else if (action === 'now') {
    if (rest.length !== 1) { console.error('now 需要 <key> 参数'); process.exit(2); }
    obj[rest[0]] = new Date().toISOString();
  } else if (action === 'append') {
    if (rest.length !== 2) { console.error('append 需要 <arrayKey> <value> 参数'); process.exit(2); }
    const k = rest[0];
    if (!Array.isArray(obj[k])) obj[k] = [];
    if (obj[k].indexOf(rest[1]) < 0) obj[k].push(rest[1]);
  } else {
    console.error('未知子命令: ' + action + '（应为 set / append / now）');
    process.exit(2);
  }

  try {
    writeJSON(file, obj);
    console.log('OK ' + action + ' -> ' + file);
  } catch (err) {
    console.error('写入失败: ' + (err && err.message));
    process.exit(1);
  }
}

main();
