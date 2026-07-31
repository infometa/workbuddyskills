// ========================================================================
// sse.js — 命令实时推送通道
// 负责：SSE 连接（connectSSE）、HTTP 轮询降级（startPolling）
// 依赖：utils.js（log）、executor.js（executeOp，需后加载）
// ========================================================================

var _evtSource = null;
var _sseConnected = false;        // SSE 是否成功建立
var _sseFailedAt = 0;             // SSE 第一次出错的时间
var _pollTimer = null;            // 轮询定时器
var _pollingActive = false;       // 是否已切换到轮询模式

// 轮询降级：每 1 秒拉取一次 /api/command-poll
var _pollingReadyNotified = false;  // 轮询模式下只发一次就绪通知
function startPolling() {
  if (_pollingActive) return;
  _pollingActive = true;
  log('SSE 不可用（代理环境），切换到 HTTP 轮询模式 (1s 间隔)', 'warn');
  _pollTimer = setInterval(function() {
    fetch('/api/command-poll', { cache: 'no-store' })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        // 轮询首次成功时，发就绪通知（SSE 模式由 onopen 负责）
        if (!_pollingReadyNotified) {
          _pollingReadyNotified = true;
          fetch('/api/ready', { method: 'POST', cache: 'no-store' }).catch(function(){});
        }
        var cmds = d.commands || [];
        cmds.forEach(function(cmd) {
          executeOp(cmd).catch(function(e) {
            log('执行失败 [' + (cmd.op || '') + ']: ' + e.message, 'error');
          });
        });
      })
      .catch(function(e) {
        // 轮询失败时静默，不干扰 UI
      });
  }, 1000);
}

function connectSSE() {
  if (_evtSource) return;
  var src = new EventSource('/api/events');
  src.onmessage = function(event) {
    _sseConnected = true;
    // 如果已经在轮询，停止轮询（切回 SSE）
    if (_pollingActive) {
      clearInterval(_pollTimer);
      _pollingActive = false;
      log('SSE 恢复，停止轮询模式');
    }
    try {
      var cmd = JSON.parse(event.data);
      executeOp(cmd).catch(function(e) {
        log('执行失败 [' + (cmd.op || '') + ']: ' + e.message, 'error');
      });
    } catch(e) {
      log('SSE 解析失败: ' + e.message, 'error');
    }
  };
  src.onerror = function() {
    if (!_sseConnected) {
      // 从未连接成功
      if (_sseFailedAt === 0) _sseFailedAt = Date.now();
      // 等待 3 秒后切换到轮询
      if (Date.now() - _sseFailedAt > 3000 && !_pollingActive) {
        startPolling();
      }
    }
    // EventSource 会自动重连，无需额外处理
  };
  src.onopen = function() {
    _sseConnected = true;
    log('SSE 实时通道已连接');
    // 连接成功时清空 SSE 失败计时
    _sseFailedAt = 0;
    // 如果之前切换到了轮询，停止轮询
    if (_pollingActive) {
      clearInterval(_pollTimer);
      _pollingActive = false;
      log('SSE 已建立，停止轮询');
    }
    // 通知服务端：Mol* 已就绪，可以推送 get_pdb 命令
    fetch('/api/ready', { method: 'POST', cache: 'no-store' }).catch(function(){});
  };
  _evtSource = src;
  // 3 秒后检查是否需要启动轮询降级
  setTimeout(function() {
    if (!_sseConnected && !_pollingActive) {
      startPolling();
    }
  }, 3000);
}
