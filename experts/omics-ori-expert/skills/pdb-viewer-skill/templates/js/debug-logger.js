/**
 * debug-logger.js — pdb-viewer-skill 调试日志模块
 *
 * ╔══════════════════════════════════════════════════════════════╗
 * ║  [DBG-LOAD] 标记：此文件仅用于调试，发布前删除 script 标签  ║
 * ║  在 viewer.html 中查找 [DBG-LOAD] 注释行以快速定位          ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * 使用方式：
 *   业务代码调用: window.__dbgLog && __dbgLog('message', 'level')
 *   级别: 'info'(默认) | 'warn' | 'error' | 'ok'
 *
 * 发布清理方式：
 *   viewer.html 中注释掉 [DBG-LOAD] 那一行 script 标签即可
 *   → window.__dbgLog 变为 undefined
 *   → 所有 window.__dbgLog && __dbgLog(...) 调用自动短路，0 改动
 */
(function () {
  'use strict';

  var BASE = location.protocol + '//' + location.host;
  var _logBuffer = [];
  var _flushTimer = null;
  var _batchSize = 5;
  var _flushInterval = 200; // ms

  /**
   * 格式化时间戳
   */
  function _ts() {
    return new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  }

  /**
   * 实际发送日志到服务端 /api/log（批量）
   */
  function _flush() {
    if (_logBuffer.length === 0) return;
    var batch = _logBuffer.slice();
    _logBuffer = [];
    try {
      fetch(BASE + '/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch: batch }),
        keepalive: true
      }).catch(function () {});
    } catch (_e) {}
  }

  /**
   * 调度批量发送
   */
  function _scheduledFlush() {
    if (_flushTimer) return;
    _flushTimer = setTimeout(function () {
      _flushTimer = null;
      _flush();
    }, _flushInterval);
  }

  /**
   * 主日志函数 — 挂载到 window.__dbgLog
   * @param {string} msg    日志消息
   * @param {string} level  'info' | 'warn' | 'error' | 'ok'
   */
  function dbgLog(msg, level) {
    var lvl = level || 'info';
    var entry = { msg: String(msg), level: lvl, ts: _ts() };

    // console 输出
    if (lvl === 'error') {
      console.error('[pdb-viewer]', msg);
    } else if (lvl === 'warn') {
      console.warn('[pdb-viewer]', msg);
    } else {
      console.log('[pdb-viewer]', msg);
    }

    // 加入批量队列
    _logBuffer.push(entry);
    if (_logBuffer.length >= _batchSize) {
      if (_flushTimer) { clearTimeout(_flushTimer); _flushTimer = null; }
      _flush();
    } else {
      _scheduledFlush();
    }
  }

  // 挂载到全局，业务代码通过 window.__dbgLog && __dbgLog(msg, level) 调用
  window.__dbgLog = dbgLog;

  // 初始化诊断（加载时立刻发一条确认日志）
  dbgLog('debug-logger.js 已加载 — 调试模式启用', 'info');
  dbgLog('location: ' + location.href, 'info');

  // 检查 WebGL 可用性
  try {
    var c = document.createElement('canvas');
    var gl = c.getContext('webgl') || c.getContext('experimental-webgl');
    dbgLog(gl
      ? 'WebGL 可用 renderer=' + gl.getParameter(gl.RENDERER).substring(0, 50)
      : 'WebGL 不可用',
      gl ? 'info' : 'error'
    );
  } catch (e) {
    dbgLog('WebGL 检查失败: ' + e.message, 'warn');
  }

  // 页面卸载前强制 flush
  window.addEventListener('beforeunload', function () {
    if (_logBuffer.length > 0) _flush();
  });

})();
