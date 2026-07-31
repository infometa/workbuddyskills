// ========================================================================
// utils.js — 工具函数
// 负责：日志记录 (log/renderLog/escHtml)、状态显示 (setStatus/hideStatus)、
//       颜色转换 (hexToInt)、格式判断 (guessFormat)
// ========================================================================

var _logVisible = false;
var _debugMode = (new URLSearchParams(location.search)).get('debug') === '1';
var _logLines = [];

function log(msg, level) {
  var ts = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  var entry = '[' + ts + '] ' + msg;
  _logLines.push({ text: entry, level: level || 'ok' });
  if (_logLines.length > 40) _logLines.shift();
  console.log('[pdb-viewer]', msg);
  renderLog();
  // [DBG-LOG] 调试日志推送（依赖 debug-logger.js）
  window.__dbgLog && __dbgLog(msg, level || 'info');
}

function renderLog() {
  var el = document.getElementById('cmd-log');
  if (!el) return;
  el.innerHTML = _logLines.map(function(l) {
    var cls = l.level === 'error' ? 'log-err' : l.level === 'warn' ? 'log-warn' : 'log-ok';
    return '<div class="log-line ' + cls + '">' + escHtml(l.text) + '</div>';
  }).join('');
  el.scrollTop = el.scrollHeight;
  // 仅 debug 模式自动展示日志面板；正式发布默认隐藏
  if (_debugMode && !_logVisible && _logLines.length > 0) {
    el.classList.add('visible');
    _logVisible = true;
  }
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setStatus(text, kind) {
  var el = document.getElementById('status');
  if (!el) return;
  el.textContent = text;
  el.classList.remove('loading','error','ok','hidden');
  if (kind) el.classList.add(kind);
}

function hideStatus(delay) {
  setTimeout(function() {
    var el = document.getElementById('status');
    if (el) el.classList.add('hidden');
  }, delay || 1500);
}

function hexToInt(cssColor) {
  var s = (cssColor || '').replace('#','');
  if (!s) return 0xffffff;
  return parseInt(s, 16) || 0xffffff;
}

function guessFormat(name) {
  var n = (name || '').toLowerCase();
  if (n.endsWith('.cif') || n.endsWith('.mmcif')) return 'mmcif';
  if (n.endsWith('.bcif')) return 'bcif';
  return 'pdb';
}
