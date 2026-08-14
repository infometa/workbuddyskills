/**
 * AgentChat Widget v3.3.0 — 浮动 AI 对话组件（多会话 + 持久化）
 *
 * 用法:
 *   <script src="chat-widget.js"></script>
 *   <script>
 *     AgentChat.init({ agentName: 'my-agent', owner: 'staff-name' });
 *   </script>
 *
 * v3.0.0 新增:
 *   - 会话上下文持久化：刷新页面不丢失对话历史
 *   - 多会话切换：侧边栏管理多个对话，可切换/重命名/删除
 *   - 双重保障：localStorage 缓存 + 服务端会话 API 兜底
 *
 * v3.2.0 新增:
 *   - 流式回复可终止：发送中按钮切换为「停止」，点击立即中断（AbortController）
 *   - 回复中可切换/新建会话：自动终止当前流，无需二次确认
 *   - 终止后保留已生成的部分内容并持久化
 *
 * v3.3.0 新增:
 *   - 面板拖拽缩放：左上角 / 上边 / 左边拖拽调整尺寸
 *   - 尺寸持久化：刷新后恢复上次面板大小
 *
 * 架构（单文件 IIFE，模块化内部结构）:
 *   ┌─ Store       会话状态 + localStorage 持久化
 *   ├─ ApiClient   HTTP 封装（invoke / session CRUD）
 *   ├─ Renderer    Markdown 渲染（零依赖，XSS 安全）
 *   ├─ SSE         流式事件解析
 *   ├─ Resizer     面板拖拽缩放（上/左/左上角）+ 尺寸持久化
 *   └─ UI          面板 + 侧边栏 + 消息渲染
 *
 * SSE 事件契约（与 agent-server 对接）:
 *   {type: 'thread',   threadId}         — 会话 ID（raw_tid）
 *   {type: 'text',     content}          — 流式文本 chunk
 *   {type: 'tool_start', name, input}    — 工具调用开始
 *   {type: 'tool_end',   name, output}   — 工具调用结束
 *   {type: 'done',     content}          — 流结束，content 为完整文本
 *   {type: 'error',    message}          — 错误
 *
 * threadId 约定:
 *   - 前端生成 raw_tid（如 'thread-abc123'），发 invoke 时传 raw_tid
 *   - 服务端组装完整 thread_id = '{owner}:{agent}:{staff}:{raw_tid}'，存入 checkpointer + chat_sessions
 *   - 前端从 list_sessions 响应获取 staffName，自行组装完整 thread_id 用于会话 API
 */
!(function () {
  'use strict';

  var WIDGET_VERSION = '3.3.0';

  // localStorage 单会话最大消息数（超出时仅保留最近 N 条，避免容量溢出）
  var MAX_MESSAGES_PER_SESSION = 200;
  // localStorage 最大会话数（超出时淘汰最旧的）
  var MAX_SESSIONS = 100;

  // ============================================================================
  // 样式
  // ============================================================================

  var styles = [
    '#chat-btn{position:fixed;bottom:24px;right:24px;width:56px;height:56px;border:none;cursor:pointer;z-index:9999;display:flex;align-items:center;justify-content:center}',
    '#chat-btn:hover{transform:scale(1.05)}',
    '#chat-panel{display:none;position:fixed;bottom:24px;right:24px;width:480px;height:560px;background:#fff;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.15);z-index:9998;flex-direction:column;overflow:hidden}',
    '#chat-panel.open{display:flex}',
    '#chat-hdr{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:14px 16px;font-weight:600;display:flex;justify-content:space-between;align-items:center;font-size:15px}',
    '#chat-hdr .hdr-actions{display:flex;align-items:center;gap:8px}',
    '#chat-toggle-sidebar{cursor:pointer;font-size:16px;border:none;background:rgba(255,255,255,0.2);color:#fff;width:28px;height:28px;border-radius:4px;display:flex;align-items:center;justify-content:center;line-height:1}',
    '#chat-toggle-sidebar:hover{background:rgba(255,255,255,0.35)}',
    '#chat-reset{cursor:pointer;font-size:13px;border:none;background:rgba(255,255,255,0.2);color:#fff;padding:4px 10px;border-radius:4px;line-height:1.4}',
    '#chat-reset:hover{background:rgba(255,255,255,0.35)}',
    '#chat-close{cursor:pointer;font-size:20px;border:none;background:none;color:#fff;padding:0 4px;line-height:1}',
    // 面板缩放手柄（上边 / 左边 / 左上角）
    '.chat-resize{position:absolute;z-index:2;touch-action:none;-webkit-user-select:none;user-select:none}',
    '.chat-resize-n{top:0;left:0;right:0;height:6px;cursor:ns-resize}',
    '.chat-resize-w{top:0;left:0;bottom:0;width:6px;cursor:ew-resize}',
    '.chat-resize-nw{top:0;left:0;width:16px;height:16px;cursor:nwse-resize;z-index:3}',
    '.chat-resize-n:hover,.chat-resize-w:hover,.chat-resize-nw:hover{background:rgba(102,126,234,0.25)}',
    'body.chat-resizing{user-select:none}',
    // 主体布局：侧边栏 + 消息区
    '#chat-body{flex:1;display:flex;overflow:hidden}',
    '#chat-sidebar{width:160px;border-right:1px solid #eee;display:none;flex-direction:column;background:#fafafa;overflow:hidden}',
    '#chat-sidebar.open{display:flex}',
    '#chat-sidebar-list{flex:1;overflow-y:auto;padding:8px 0}',
    '#chat-sidebar-empty{padding:20px 12px;color:#bbb;font-size:12px;text-align:center}',
    '.session-item{padding:8px 12px;cursor:pointer;border-left:3px solid transparent;transition:background 0.15s;position:relative}',
    '.session-item:hover{background:#f0f0f4}',
    '.session-item.active{background:#ede9f5;border-left-color:#667eea}',
    '.session-item .session-title{font-size:13px;color:#333;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:16px}',
    '.session-item .session-time{font-size:11px;color:#aaa;margin-top:2px}',
    '.session-item .session-del{position:absolute;right:8px;top:50%;transform:translateY(-50%);opacity:0;color:#e74c3c;cursor:pointer;font-size:14px}',
    '.session-item:hover .session-del{opacity:0.6}',
    '.session-item .session-del:hover{opacity:1}',
    '.session-item .session-edit{position:absolute;right:26px;top:50%;transform:translateY(-50%);opacity:0;color:#999;cursor:pointer;font-size:13px}',
    '.session-item:hover .session-edit{opacity:0.6}',
    '.session-item .session-edit:hover{opacity:1}',
    '.session-edit-input{width:100%;border:1px solid #667eea;border-radius:3px;padding:4px 6px;font-size:13px;box-sizing:border-box}',
    '#chat-msgs{flex:1;overflow-y:auto;padding:12px 16px;background:#f8f9fb}',
    '#chat-ftr{display:flex;padding:10px 12px;gap:8px;border-top:1px solid #eee;align-items:flex-end}',
    '#chat-input{flex:1;border:1px solid #e0e0e0;border-radius:8px;padding:10px 14px;font-size:14px;outline:none;resize:none;max-height:100px;line-height:1.5}',
    '#chat-input:focus{border-color:#667eea}',
    '#chat-send{background:#667eea;color:#fff;border:none;border-radius:8px;padding:10px 16px;cursor:pointer;font-size:14px;white-space:nowrap}',
    '#chat-send:disabled{opacity:0.5;cursor:not-allowed}',
    // 消息样式
    '.msg-user{width:fit-content;max-width:85%;padding:10px 14px;border-radius:12px 12px 4px 12px;font-size:14px;line-height:1.5;margin-bottom:8px;margin-left:auto;background:#667eea;color:#fff;word-wrap:break-word}',
    '.msg-agent{width:fit-content;max-width:85%;padding:10px 14px;border-radius:12px 12px 12px 4px;font-size:14px;line-height:1.6;margin-bottom:8px;margin-right:auto;background:#fff;color:#333;box-shadow:0 1px 3px rgba(0,0,0,0.08);word-wrap:break-word;overflow-wrap:anywhere}',
    '.msg-tool{width:fit-content;max-width:85%;padding:6px 10px;border-radius:8px;font-size:12px;margin-bottom:8px;margin-right:auto;background:#fff8e1;color:#8d6e00;word-wrap:break-word}',
    '.msg-error{width:fit-content;max-width:85%;padding:6px 10px;border-radius:8px;font-size:12px;margin-bottom:8px;margin-right:auto;background:#fde8e8;color:#c0341d;word-wrap:break-word}',
    '.msg-typing{color:#999;font-size:12px;margin-bottom:8px}',
    '.tool-status{font-size:12px;color:#888;margin-bottom:6px;display:flex;align-items:center;gap:4px}',
    '.tool-status .dot{width:6px;height:6px;border-radius:50%;background:#667eea;animation:pulse 1s infinite}',
    '@keyframes pulse{0%,100%{opacity:0.3}50%{opacity:1}}',
    '.tool-card{margin-bottom:8px;margin-right:auto;max-width:85%}',
    '.tool-card>summary{cursor:pointer;font-size:12px;color:#666;background:#f5f5f8;padding:5px 12px;border-radius:16px;display:inline-flex;align-items:center;gap:5px;user-select:none;list-style:none;transition:background 0.15s}',
    '.tool-card>summary::-webkit-details-marker{display:none}',
    '.tool-card>summary::before{content:"▸";font-size:10px;color:#999;transition:transform 0.15s}',
    '.tool-card[open]>summary::before{transform:rotate(90deg)}',
    '.tool-card>summary:hover{background:#ececf1}',
    '.tool-card .tool-list{margin-top:6px;display:flex;flex-direction:column;gap:4px}',
    '.tool-card .tool-item{border:1px solid #eee;border-radius:8px;overflow:hidden}',
    '.tool-card .tool-item>summary{cursor:pointer;font-size:12px;padding:6px 12px;background:#fafafa;user-select:none;list-style:none;display:flex;align-items:center;gap:5px;transition:background 0.15s}',
    '.tool-card .tool-item>summary::-webkit-details-marker{display:none}',
    '.tool-card .tool-item>summary::before{content:"▸";font-size:10px;color:#bbb;transition:transform 0.15s}',
    '.tool-card .tool-item[open]>summary::before{transform:rotate(90deg)}',
    '.tool-card .tool-item>summary:hover{background:#f0f0f4}',
    '.tool-card .tool-item .tool-name{font-weight:500;color:#333;flex:1}',
    '.tool-card .tool-detail{padding:8px 12px;background:#fafafa;font-size:11px;color:#888;display:flex;flex-direction:column;gap:6px}',
    '.tool-card .tool-detail .tool-io-label{font-weight:600;color:#555;margin-bottom:2px}',
    '.tool-card .tool-detail .tool-io-content{word-break:break-all;white-space:pre-wrap;max-height:120px;overflow-y:auto;line-height:1.5;font-family:Consolas,Monaco,"Courier New",monospace;font-size:11px;color:#999;background:#fff;padding:6px 8px;border-radius:4px;border:1px solid #f0f0f0}',
    // Markdown 排版
    '.msg-agent p{margin:0 0 8px 0}.msg-agent p:last-child{margin-bottom:0}',
    '.msg-agent h1{font-size:18px;margin:10px 0 6px 0;font-weight:600}.msg-agent h2{font-size:16px;margin:10px 0 6px 0;font-weight:600}.msg-agent h3{font-size:15px;margin:8px 0 4px 0;font-weight:600}',
    '.msg-agent ul,.msg-agent ol{margin:4px 0 8px 0;padding-left:20px}.msg-agent li{margin:2px 0}',
    '.msg-agent code{background:#f0f0f4;padding:1px 5px;border-radius:3px;font-size:13px;font-family:Consolas,Monaco,"Courier New",monospace;color:#c0341d}',
    '.msg-agent pre{background:#1e1e2e;color:#e0e0e0;padding:10px 12px;border-radius:8px;overflow-x:auto;margin:6px 0 8px 0;font-size:13px;line-height:1.4}',
    '.msg-agent pre code{background:none;color:inherit;padding:0;font-size:inherit}',
    '.msg-agent a{color:#667eea;text-decoration:none}.msg-agent a:hover{text-decoration:underline}',
    '.msg-agent blockquote{border-left:3px solid #ddd;margin:6px 0;padding:2px 10px;color:#888;background:#fafafa;border-radius:0 4px 4px 0}',
    '.msg-agent table{border-collapse:collapse;margin:6px 0;font-size:13px}.msg-agent th,.msg-agent td{border:1px solid #e0e0e0;padding:4px 8px}.msg-agent th{background:#f5f5f8;font-weight:600}',
    '.msg-agent hr{border:none;border-top:1px solid #eee;margin:10px 0}'
  ];

  function injectStyles() {
    var s = document.createElement('style');
    s.textContent = styles.join('\n');
    document.head.appendChild(s);
  }

  // ============================================================================
  // 工具函数
  // ============================================================================

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function createThrottledRenderer() {
    var rafId = null;
    var pendingFn = null;
    return function throttle(fn) {
      pendingFn = fn;
      if (rafId !== null) return;
      rafId = requestAnimationFrame(function () {
        rafId = null;
        if (pendingFn) {
          var f = pendingFn;
          pendingFn = null;
          f();
        }
      });
    };
  }

  function formatRelativeTime(ts) {
    if (!ts) return '';
    var now = Date.now();
    var diff = now - ts;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
    if (diff < 604800000) return Math.floor(diff / 86400000) + '天前';
    var d = new Date(ts);
    return (d.getMonth() + 1) + '/' + d.getDate();
  }

  // ============================================================================
  // Markdown 渲染器（保持 v2 实现，零依赖，XSS 安全）
  // ============================================================================

  function renderMarkdown(text) {
    if (!text) return '';
    var raw = escapeHtml(text);
    var codeBlocks = [];
    raw = raw.replace(/```(\w*)\n?([\s\S]*?)```/g, function (_, lang, code) {
      var idx = codeBlocks.length;
      codeBlocks.push('<pre><code>' + code.replace(/\n$/, '') + '</code></pre>');
      return '\u0000CODEBLOCK' + idx + '\u0000';
    });
    raw = raw.replace(/```(\w*)\n?([\s\S]*)$/, function (_, lang, code) {
      var idx = codeBlocks.length;
      codeBlocks.push('<pre><code>' + code.replace(/\n$/, '') + '</code></pre>');
      return '\u0000CODEBLOCK' + idx + '\u0000';
    });
    var lines = raw.split('\n');
    var out = [];
    var inList = false, listType = '';
    var inQuote = false;
    function closeList() { if (inList) { out.push('</' + listType + '>'); inList = false; } }
    function closeQuote() { if (inQuote) { out.push('</blockquote>'); inQuote = false; } }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var trimmed = line.trim();
      var cbMatch = trimmed.match(/^\u0000CODEBLOCK(\d+)\u0000$/);
      if (cbMatch) { closeList(); closeQuote(); out.push(codeBlocks[parseInt(cbMatch[1])]); continue; }
      if (trimmed === '') { closeList(); closeQuote(); continue; }
      if (/^---+$/.test(trimmed)) { closeList(); closeQuote(); out.push('<hr>'); continue; }
      var hMatch = trimmed.match(/^(#{1,3})\s+(.+)$/);
      if (hMatch) { closeList(); closeQuote(); var level = hMatch[1].length; out.push('<h' + level + '>' + hMatch[2] + '</h' + level + '>'); continue; }
      if (trimmed.charAt(0) === '>' && trimmed.charAt(1) === ' ') {
        closeList();
        if (!inQuote) { out.push('<blockquote>'); inQuote = true; }
        out.push('<p>' + trimmed.substring(2) + '</p>');
        continue;
      } else { closeQuote(); }
      if (/^[-*]\s+/.test(trimmed)) {
        if (!inList || listType !== 'ul') { closeList(); out.push('<ul>'); inList = true; listType = 'ul'; }
        out.push('<li>' + trimmed.replace(/^[-*]\s+/, '') + '</li>');
        continue;
      }
      if (/^\d+\.\s+/.test(trimmed)) {
        if (!inList || listType !== 'ol') { closeList(); out.push('<ol>'); inList = true; listType = 'ol'; }
        out.push('<li>' + trimmed.replace(/^\d+\.\s+/, '') + '</li>');
        continue;
      }
      if (/^\|.*\|$/.test(trimmed) && i + 1 < lines.length && /^\|[\s:|-]+\|$/.test(lines[i + 1].trim())) {
        closeList(); closeQuote();
        var headerCells = trimmed.slice(1, -1).split('|').map(function (c) { return c.trim(); });
        var tableHtml = '<table><thead><tr>';
        for (var h = 0; h < headerCells.length; h++) tableHtml += '<th>' + headerCells[h] + '</th>';
        tableHtml += '</tr></thead><tbody>';
        i += 2;
        while (i < lines.length && /^\|.*\|$/.test(lines[i].trim())) {
          var cells = lines[i].trim().slice(1, -1).split('|').map(function (c) { return c.trim(); });
          tableHtml += '<tr>';
          for (var c = 0; c < cells.length; c++) tableHtml += '<td>' + cells[c] + '</td>';
          tableHtml += '</tr>';
          i++;
        }
        i--;
        tableHtml += '</tbody></table>';
        out.push(tableHtml);
        continue;
      }
      closeList(); closeQuote();
      out.push('<p>' + trimmed + '</p>');
    }
    closeList(); closeQuote();
    var html = out.join('\n');
    var inlineCodes = [];
    html = html.replace(/`([^`]+)`/g, function (_, code) {
      var idx = inlineCodes.length;
      inlineCodes.push('<code>' + code + '</code>');
      return '\u0001INLINE' + idx + '\u0001';
    });
    html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/(^|[^\*])\*([^\*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, function (_, txt, url) {
      return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + txt + '</a>';
    });
    html = html.replace(/\u0001INLINE(\d+)\u0001/g, function (_, idx) {
      return inlineCodes[parseInt(idx)];
    });
    return html;
  }

  // ============================================================================
  // SSE 流解析器
  // ============================================================================

  async function parseSSEStream(reader, onEvent) {
    var decoder = new TextDecoder();
    var buf = '';
    async function processLine(line) {
      if (line.indexOf('data: ') !== 0) return;
      var payload = line.substring(6);
      try {
        var data = JSON.parse(payload);
        await onEvent(data);
      } catch (e) { /* 忽略不完整 chunk */ }
    }
    while (true) {
      var chunk = await reader.read();
      if (chunk.done) break;
      buf += decoder.decode(chunk.value, { stream: true });
      var lines = buf.split('\n');
      buf = lines.pop() || '';
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trimEnd();
        if (line) await processLine(line);
      }
    }
    var tail = decoder.decode();
    if (tail) buf += tail;
    buf = buf.trim();
    if (buf) { await processLine(buf); buf = ''; }
  }

  // ============================================================================
  // Store 模块 — 会话状态 + localStorage 持久化
  // ============================================================================

  /**
   * 创建会话状态管理器。
   *
   * localStorage key: agentchat:sessions:{agentName}:{owner}
   * 结构: { activeThreadId, sessions: [{threadId, title, createdAt, updatedAt, messages}] }
   *
   * threadId 为完整格式（{owner}:{agent}:{staff}:{raw}），用于服务端会话 API。
   */
  function createStore(agentName, owner) {
    var STORAGE_KEY = 'agentchat:sessions:' + agentName + ':' + owner;
    var state = { activeThreadId: null, sessions: [] };

    function load() {
      try {
        var raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          var parsed = JSON.parse(raw);
          state.activeThreadId = parsed.activeThreadId || null;
          state.sessions = parsed.sessions || [];
        }
      } catch (e) { /* localStorage 不可用或数据损坏，忽略 */ }
    }

    function save() {
      try {
        // 淘汰超限会话（保留最近 MAX_SESSIONS 个）
        if (state.sessions.length > MAX_SESSIONS) {
          state.sessions = state.sessions.slice(0, MAX_SESSIONS);
        }
        // 单会话消息超限时裁剪
        for (var i = 0; i < state.sessions.length; i++) {
          var s = state.sessions[i];
          if (s.messages && s.messages.length > MAX_MESSAGES_PER_SESSION) {
            s.messages = s.messages.slice(-MAX_MESSAGES_PER_SESSION);
          }
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      } catch (e) { /* 容量溢出等，静默失败 */ }
    }

    function findSession(threadId) {
      for (var i = 0; i < state.sessions.length; i++) {
        if (state.sessions[i].threadId === threadId) return state.sessions[i];
      }
      return null;
    }

    function createSession(threadId, title) {
      var session = {
        threadId: threadId,
        title: title || '新对话',
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messages: []
      };
      state.sessions.unshift(session);
      state.activeThreadId = threadId;
      save();
      return session;
    }

    function switchSession(threadId) {
      if (findSession(threadId)) {
        state.activeThreadId = threadId;
        save();
        return true;
      }
      return false;
    }

    function deleteSession(threadId) {
      for (var i = 0; i < state.sessions.length; i++) {
        if (state.sessions[i].threadId === threadId) {
          state.sessions.splice(i, 1);
          break;
        }
      }
      if (state.activeThreadId === threadId) {
        state.activeThreadId = state.sessions.length > 0 ? state.sessions[0].threadId : null;
      }
      save();
    }

    function renameSession(threadId, title) {
      var s = findSession(threadId);
      if (s) { s.title = title; s.updatedAt = Date.now(); save(); }
    }

    function addMessage(threadId, msg) {
      var s = findSession(threadId);
      if (s) {
        s.messages.push(msg);
        s.updatedAt = Date.now();
        // 单会话消息超限裁剪
        if (s.messages.length > MAX_MESSAGES_PER_SESSION) {
          s.messages = s.messages.slice(-MAX_MESSAGES_PER_SESSION);
        }
        save();
      }
    }

    function updateLastMessage(threadId, msg) {
      var s = findSession(threadId);
      if (s && s.messages.length > 0) {
        s.messages[s.messages.length - 1] = msg;
        s.updatedAt = Date.now();
        save();
      }
    }

    function getActiveSession() {
      return state.activeThreadId ? findSession(state.activeThreadId) : null;
    }

    function setActive(threadId) {
      state.activeThreadId = threadId;
      save();
    }

    // 从服务端会话列表同步（合并 meta，不覆盖本地消息）
    function mergeFromServer(serverSessions, staffName, agentName, owner) {
      // 修正本地 threadId 格式：staffName 未知时创建的会话 threadId 为 raw 格式（无冒号），
      // 获取 staffName 后补全为完整格式 {owner}:{agent}:{staff}:{raw}，避免与服务端不匹配。
      if (staffName) {
        for (var i = 0; i < state.sessions.length; i++) {
          var s = state.sessions[i];
          if (s.threadId.indexOf(':') === -1) {
            s.threadId = owner + ':' + agentName + ':' + staffName + ':' + s.threadId;
          }
        }
        if (state.activeThreadId && state.activeThreadId.indexOf(':') === -1) {
          state.activeThreadId = owner + ':' + agentName + ':' + staffName + ':' + state.activeThreadId;
        }
      }

      var localMap = {};
      for (var j = 0; j < state.sessions.length; j++) {
        localMap[state.sessions[j].threadId] = state.sessions[j];
      }
      var newSessions = [];
      for (var k = 0; k < serverSessions.length; k++) {
        var ss = serverSessions[k];
        var fullTid = ss.threadId;
        var local = localMap[fullTid];
        if (local) {
          // 保留本地消息，更新 meta
          local.title = ss.title || local.title;
          // createdAt/updatedAt 用服务端时间戳更准确
          newSessions.push(local);
          delete localMap[fullTid];
        } else {
          // 服务端有但本地没有 → 新建空会话（消息懒加载）
          newSessions.push({
            threadId: fullTid,
            title: ss.title || '新对话',
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: [],
            _needLoad: true  // 标记需要从服务端加载消息
          });
        }
      }
      // 本地有但服务端没有的会话：保留（可能是刚创建还未同步，或服务端删除但本地仍想保留）
      for (var key in localMap) {
        if (localMap.hasOwnProperty(key)) {
          newSessions.push(localMap[key]);
        }
      }
      // 按更新时间倒序
      newSessions.sort(function (a, b) { return (b.updatedAt || 0) - (a.updatedAt || 0); });
      state.sessions = newSessions;
      if (!state.activeThreadId && newSessions.length > 0) {
        state.activeThreadId = newSessions[0].threadId;
      }
      save();
    }

    load();
    return {
      get state() { return state; },
      load: load,
      save: save,
      findSession: findSession,
      createSession: createSession,
      switchSession: switchSession,
      deleteSession: deleteSession,
      renameSession: renameSession,
      addMessage: addMessage,
      updateLastMessage: updateLastMessage,
      getActiveSession: getActiveSession,
      setActive: setActive,
      mergeFromServer: mergeFromServer,
    };
  }

  // ============================================================================
  // ApiClient 模块 — HTTP 封装
  // ============================================================================

  function createApiClient(serviceUrl, agentName, owner) {
    var base = serviceUrl || '';

    function buildFullThreadId(rawTid, staffName) {
      return owner + ':' + agentName + ':' + staffName + ':' + rawTid;
    }

    async function invoke(rawTid, message, context, signal) {
      var payload = { agentName: agentName, threadId: rawTid, message: message };
      if (owner) payload.owner = owner;
      if (context) payload.context = context;
      return fetch(base + '/api/agent/invoke', {
        method: 'POST',
        credentials: 'include',
        redirect: 'manual',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: signal
      });
    }

    async function listSessions() {
      var url = base + '/api/session/list?agentName=' + encodeURIComponent(agentName) +
                '&owner=' + encodeURIComponent(owner);
      var resp = await fetch(url, { credentials: 'include', redirect: 'manual' });
      if (!resp.ok) throw new Error('list sessions HTTP ' + resp.status);
      return resp.json();
    }

    async function getMessages(fullThreadId) {
      var resp = await fetch(base + '/api/session/' + encodeURIComponent(fullThreadId) + '/messages',
        { credentials: 'include', redirect: 'manual' });
      if (!resp.ok) throw new Error('get messages HTTP ' + resp.status);
      return resp.json();
    }

    async function renameSession(fullThreadId, title) {
      var resp = await fetch(base + '/api/session/' + encodeURIComponent(fullThreadId) + '/rename', {
        method: 'POST',
        credentials: 'include',
        redirect: 'manual',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title })
      });
      if (!resp.ok) throw new Error('rename session HTTP ' + resp.status);
      return resp.json();
    }

    async function deleteSession(fullThreadId) {
      var resp = await fetch(base + '/api/session/' + encodeURIComponent(fullThreadId), {
        method: 'DELETE',
        credentials: 'include',
        redirect: 'manual'
      });
      if (!resp.ok) throw new Error('delete session HTTP ' + resp.status);
      return resp.json();
    }

    return {
      buildFullThreadId: buildFullThreadId,
      invoke: invoke,
      listSessions: listSessions,
      getMessages: getMessages,
      renameSession: renameSession,
      deleteSession: deleteSession,
    };
  }

  // ============================================================================
  // Resizer 模块 — 面板拖拽缩放（上/左/左上角）+ 尺寸持久化
  // ============================================================================

  /**
   * 创建面板缩放手柄。面板锚定右下角，可拖拽方向为「上边 / 左边 / 左上角」：
   *   - n  : 上边   → 仅改高度
   *   - w  : 左边   → 仅改宽度
   *   - nw : 左上角 → 同时改宽高
   *
   * 尺寸持久化 key: agentchat:size:{agentName}:{owner}，本模块自管，不依赖 Store。
   */
  function createResizer(panel, agentName, owner) {
    var STORAGE_KEY = 'agentchat:size:' + agentName + ':' + owner;
    var MIN_WIDTH = 320;
    var MIN_HEIGHT = 360;
    var GAP = 24; // 面板与视口左右/上下留白

    // 方向 → 手柄配置（axis 决定改宽 / 改高 / 两者都改）
    var DIRS = {
      n:  { cls: 'chat-resize-n',  axis: 'h' },
      w:  { cls: 'chat-resize-w',  axis: 'w' },
      nw: { cls: 'chat-resize-nw', axis: 'both' }
    };

    var activeDir = null;
    var startX = 0, startY = 0, startW = 0, startH = 0;

    function maxWidth() { return Math.max(MIN_WIDTH, window.innerWidth - GAP * 2); }
    function maxHeight() { return Math.max(MIN_HEIGHT, window.innerHeight - GAP * 2); }
    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

    function onDown(e, dir) {
      e.preventDefault();
      activeDir = dir;
      startX = e.clientX;
      startY = e.clientY;
      startW = panel.offsetWidth;
      startH = panel.offsetHeight;
      e.currentTarget.setPointerCapture(e.pointerId);
      document.body.classList.add('chat-resizing');
    }

    function onMove(e) {
      if (!activeDir) return;
      var axis = DIRS[activeDir].axis;
      var w = startW, h = startH;
      if (axis === 'w' || axis === 'both') {
        w = clamp(startW + (startX - e.clientX), MIN_WIDTH, maxWidth());
      }
      if (axis === 'h' || axis === 'both') {
        h = clamp(startH + (startY - e.clientY), MIN_HEIGHT, maxHeight());
      }
      panel.style.width = w + 'px';
      panel.style.height = h + 'px';
    }

    function onUp() {
      if (!activeDir) return;
      activeDir = null;
      document.body.classList.remove('chat-resizing');
      persist();
    }

    function persist() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          width: panel.offsetWidth,
          height: panel.offsetHeight
        }));
      } catch (e) { /* 容量溢出等，静默失败 */ }
    }

    function restore() {
      try {
        var raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        var size = JSON.parse(raw);
        if (typeof size.width === 'number' && typeof size.height === 'number') {
          panel.style.width = clamp(size.width, MIN_WIDTH, maxWidth()) + 'px';
          panel.style.height = clamp(size.height, MIN_HEIGHT, maxHeight()) + 'px';
        }
      } catch (e) { /* 数据损坏，忽略 */ }
    }

    var handles = [];
    var dirs = Object.keys(DIRS);
    for (var i = 0; i < dirs.length; i++) {
      (function (dir) {
        var handle = document.createElement('div');
        handle.className = 'chat-resize ' + DIRS[dir].cls;
        handle.addEventListener('pointerdown', function (e) { onDown(e, dir); });
        handle.addEventListener('pointermove', onMove);
        handle.addEventListener('pointerup', onUp);
        handle.addEventListener('pointercancel', onUp);
        panel.appendChild(handle);
        handles.push(handle);
      })(dirs[i]);
    }

    restore();

    // 销毁：移除手柄 DOM 并复位全局拖拽态，供面板销毁/重载时调用
    function destroy() {
      for (var i = 0; i < handles.length; i++) {
        if (handles[i].parentNode) handles[i].parentNode.removeChild(handles[i]);
      }
      handles = [];
      document.body.classList.remove('chat-resizing');
    }

    return { destroy: destroy };
  }

  // ============================================================================
  // UI 模块 — 面板 + 侧边栏 + 消息渲染
  // ============================================================================

  function createPanel(config, agentName, owner, autoOpen) {
    var title = config.title || 'AI 助手';
    var api = createApiClient(config.serviceUrl, agentName, owner);
    var store = createStore(agentName, owner);
    var staffName = '';

    // ---- DOM 构建 ----

    var panelHtml =
      '<div id="chat-hdr">' +
      '<span>' + escapeHtml(title) + '</span>' +
      '<div class="hdr-actions">' +
      '<button id="chat-toggle-sidebar" title="会话列表">☰</button>' +
      '<button id="chat-reset" title="新建对话">+ 新对话</button>' +
      '<span id="chat-close">✕</span>' +
      '</div>' +
      '</div>' +
      '<div id="chat-body">' +
        '<div id="chat-sidebar">' +
          '<div id="chat-sidebar-list"></div>' +
        '</div>' +
        '<div id="chat-main" style="flex:1;display:flex;flex-direction:column;overflow:hidden">' +
          '<div id="chat-msgs"></div>' +
          '<div id="chat-ftr">' +
            '<textarea id="chat-input" rows="1" placeholder="输入消息..."></textarea>' +
            '<button id="chat-send">发送</button>' +
          '</div>' +
        '</div>' +
      '</div>';

    var btn = document.createElement('div');
    btn.id = 'chat-btn';
    btn.innerHTML = '<img src="agent-entry-widget-icon.svg" style="width:56px;height:56px" alt="AI助手">';

    var panel = document.createElement('div');
    panel.id = 'chat-panel';
    panel.innerHTML = panelHtml;
    document.body.appendChild(btn);
    document.body.appendChild(panel);

    // ---- DOM 引用 ----
    var sidebar = panel.querySelector('#chat-sidebar');
    var sidebarList = panel.querySelector('#chat-sidebar-list');
    var msgs = panel.querySelector('#chat-msgs');
    var inp = panel.querySelector('#chat-input');
    var sendBtn = panel.querySelector('#chat-send');
    var closeBtn = panel.querySelector('#chat-close');
    var resetBtn = panel.querySelector('#chat-reset');
    var toggleSidebarBtn = panel.querySelector('#chat-toggle-sidebar');

    // 面板拖拽缩放（上/左/左上角），并自动恢复上次尺寸
    createResizer(panel, agentName, owner);

    // ---- 状态 ----
    var sidebarOpen = false;
    // 当前活跃的流控制器（无则 null），「发送中」状态由 activeStream 是否为空推导
    var activeStream = null;
    // UI 代际：每次「发送新消息」或「切换/新建会话（重渲染消息区）」时递增，
    // 流控制器捕获自身代际，与之不符即视为已作废，回调不再写 UI。
    var streamGen = 0;

    // ---- 事件绑定 ----

    var sessionsInitialized = false;

    function openPanel() {
      panel.classList.add('open');
      btn.style.display = 'none';
      inp.focus();
      // 首次打开时初始化会话（无论本地是否有缓存，都需要同步服务端 + 渲染）
      if (!sessionsInitialized) {
        sessionsInitialized = true;
        initSessions();
      }
    }

    btn.onclick = openPanel;

    // URL 参数 ?chat=open 时自动展开面板
    if (autoOpen) openPanel();

    closeBtn.onclick = function () {
      panel.classList.remove('open');
      btn.style.display = 'flex';
    };

    toggleSidebarBtn.onclick = function () {
      sidebarOpen = !sidebarOpen;
      sidebar.classList.toggle('open', sidebarOpen);
    };

    resetBtn.onclick = function () {
      // 回复中新建会话：先终止当前流，再新建（无二次确认）
      stopStreaming();
      createNewSession();
    };

    inp.addEventListener('input', function () {
      inp.style.height = 'auto';
      inp.style.height = Math.min(inp.scrollHeight, 100) + 'px';
    });

    inp.onkeydown = function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
      }
    };

    sendBtn.onclick = function () {
      if (activeStream) {
        // 发送中 → 点击即停止
        stopStreaming();
      } else {
        send();
      }
    };

    // ---- 会话初始化 ----

    async function initSessions() {
      try {
        var resp = await api.listSessions();
        staffName = resp.staffName || '';
        store.mergeFromServer(resp.items || [], staffName, agentName, owner);
        renderSidebar();
        // 若有活跃会话，渲染消息；否则新建一个
        var active = store.getActiveSession();
        if (active) {
          await renderSessionMessages(active);
        } else {
          createNewSession();
        }
      } catch (e) {
        // 服务端不可达（如未登录），降级为本地模式
        if (!store.state.sessions.length) {
          createNewSession();
        } else {
          renderSidebar();
          var active2 = store.getActiveSession();
          if (active2) renderSessionMessages(active2, true);
        }
      }
    }

    function createNewSession() {
      var rawTid = 't' + Date.now() + Math.random().toString(36).substr(2, 4);
      var fullTid = staffName ? api.buildFullThreadId(rawTid, staffName) : rawTid;
      var session = store.createSession(fullTid, '新对话');
      renderSidebar();
      renderSessionMessages(session, true);
      inp.focus();
    }

    // ---- 侧边栏渲染 ----

    function renderSidebar() {
      var sessions = store.state.sessions;
      if (!sessions.length) {
        sidebarList.innerHTML = '<div id="chat-sidebar-empty">暂无会话</div>';
        return;
      }
      var activeId = store.state.activeThreadId;
      var html = '';
      for (var i = 0; i < sessions.length; i++) {
        var s = sessions[i];
        var isActive = s.threadId === activeId;
        var timeStr = formatRelativeTime(s.updatedAt || s.createdAt);
        html +=
          '<div class="session-item' + (isActive ? ' active' : '') + '" data-tid="' + escapeHtml(s.threadId) + '">' +
            '<div class="session-title">' + escapeHtml(s.title || '新对话') + '</div>' +
            '<div class="session-time">' + escapeHtml(timeStr) + '</div>' +
            '<span class="session-edit" data-action="edit" title="重命名">✎</span>' +
            '<span class="session-del" data-action="delete" title="删除">✕</span>' +
          '</div>';
      }
      sidebarList.innerHTML = html;
    }

    // 侧边栏事件委托
    sidebarList.addEventListener('click', function (e) {
      var target = e.target;
      // 找到 .session-item
      var item = target.closest ? target.closest('.session-item') : null;
      if (!item) return;
      var tid = item.getAttribute('data-tid');
      var action = target.getAttribute('data-action');

      if (action === 'delete') {
        e.stopPropagation();
        handleDeleteSession(tid);
      } else if (action === 'edit') {
        e.stopPropagation();
        handleRenameSession(tid, item);
      } else {
        // 点击会话项本身 → 切换（回复中会先终止当前流再切换）
        handleSwitchSession(tid);
      }
    });

    function handleSwitchSession(tid) {
      // 回复中切换会话：先终止当前流，再切换
      stopStreaming();
      if (store.switchSession(tid)) {
        renderSidebar();
        var s = store.findSession(tid);
        if (s) renderSessionMessages(s);
        inp.focus();
      }
    }

    async function handleDeleteSession(tid) {
      var s = store.findSession(tid);
      if (!s) return;
      if (!confirm('删除会话「' + (s.title || '新对话') + '」？此操作不可恢复。')) return;

      // 1. 删除服务端会话（meta + checkpoint）
      try {
        await api.deleteSession(tid);
      } catch (e) { /* 服务端删除失败，继续删本地 */ }

      // 2. 删除本地
      store.deleteSession(tid);
      renderSidebar();

      // 3. 若删的是当前活跃会话，切换到第一个
      var active = store.getActiveSession();
      if (active) {
        renderSessionMessages(active);
      } else {
        createNewSession();
      }
    }

    function handleRenameSession(tid, itemEl) {
      var s = store.findSession(tid);
      if (!s) return;
      var titleEl = itemEl.querySelector('.session-title');
      var oldTitle = s.title || '';
      var input = document.createElement('input');
      input.type = 'text';
      input.className = 'session-edit-input';
      input.value = oldTitle;
      titleEl.replaceWith(input);
      input.focus();
      input.select();

      async function commit() {
        var newTitle = input.value.trim() || oldTitle;
        if (newTitle !== oldTitle) {
          store.renameSession(tid, newTitle);
          // 同步到服务端
          try { await api.renameSession(tid, newTitle); } catch (e) { /* 静默 */ }
        }
        renderSidebar();
      }

      input.onblur = commit;
      input.onkeydown = function (e) {
        if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
        if (e.key === 'Escape') { input.value = oldTitle; input.blur(); }
      };
    }

    // ---- 消息区渲染 ----

    async function renderSessionMessages(session, skipServerLoad) {
      // 消息区上下文即将切换，作废进行中流的 UI 写权限
      streamGen++;
      msgs.innerHTML = '';

      // 若本地无消息但服务端可能有（_needLoad 标记或本地为空），懒加载
      if (!session.messages.length && !skipServerLoad && session._needLoad !== false && staffName) {
        try {
          var resp = await api.getMessages(session.threadId);
          if (resp.messages && resp.messages.length) {
            session.messages = resp.messages;
            session._needLoad = false;
            store.save();
          } else if (resp.messages) {
            // 服务端确认无消息（新会话首轮）→ 标记已加载
            session._needLoad = false;
          }
          // 网络异常等 → 保留 _needLoad，允许下次刷新重试
        } catch (e) { /* 加载失败，保留 _needLoad 允许重试 */ }
      }

      if (!session.messages.length) {
        var empty = document.createElement('div');
        empty.className = 'msg-typing';
        empty.textContent = '开始新的对话...';
        msgs.appendChild(empty);
        scrollToEnd();
        return;
      }

      for (var i = 0; i < session.messages.length; i++) {
        var m = session.messages[i];
        renderMessage(m);
      }
      scrollToEnd();
    }

    function renderMessage(msg) {
      if (msg.role === 'user') {
        addMsg('user', msg.content, false);
      } else if (msg.role === 'agent') {
        var el = addMsg('agent', msg.content, true);
        if (msg.tools && msg.tools.length) {
          flushToolCard(null, msg.tools);
        }
      }
    }

    function scrollToEnd() {
      msgs.scrollTop = msgs.scrollHeight;
    }

    function addMsg(cls, txt, isMarkdown) {
      var d = document.createElement('div');
      d.className = 'msg-' + cls;
      if (isMarkdown) d.innerHTML = renderMarkdown(txt);
      else d.textContent = txt;
      msgs.appendChild(d);
      scrollToEnd();
      return d;
    }

    function createToolStatus() {
      var el = document.createElement('div');
      el.className = 'tool-status';
      el.innerHTML = '<span class="dot"></span><span class="text">正在调用工具...</span>';
      msgs.appendChild(el);
      scrollToEnd();
      return el;
    }

    function flushToolCard(statusEl, tools) {
      if (!tools || tools.length === 0) {
        if (statusEl) statusEl.remove();
        return;
      }
      var card = document.createElement('details');
      card.className = 'tool-card';
      var summary = document.createElement('summary');
      summary.textContent = '使用了 ' + tools.length + ' 个工具';
      card.appendChild(summary);
      var list = document.createElement('div');
      list.className = 'tool-list';
      for (var i = 0; i < tools.length; i++) {
        var t = tools[i];
        var item = document.createElement('details');
        item.className = 'tool-item';
        var itemSummary = document.createElement('summary');
        var nameSpan = document.createElement('span');
        nameSpan.className = 'tool-name';
        nameSpan.textContent = t.name;
        itemSummary.appendChild(nameSpan);
        item.appendChild(itemSummary);
        var detail = document.createElement('div');
        detail.className = 'tool-detail';
        if (t.input) {
          var inputLabel = document.createElement('div');
          inputLabel.className = 'tool-io-label';
          inputLabel.textContent = '输入';
          var inputContent = document.createElement('div');
          inputContent.className = 'tool-io-content';
          inputContent.textContent = t.input;
          detail.appendChild(inputLabel);
          detail.appendChild(inputContent);
        }
        if (t.output) {
          var outputLabel = document.createElement('div');
          outputLabel.className = 'tool-io-label';
          outputLabel.textContent = '输出';
          var outputContent = document.createElement('div');
          outputContent.className = 'tool-io-content';
          outputContent.textContent = t.output;
          detail.appendChild(outputLabel);
          detail.appendChild(outputContent);
        }
        if (!t.input && !t.output) {
          var empty = document.createElement('div');
          empty.className = 'tool-io-content';
          empty.textContent = '(无输入输出)';
          detail.appendChild(empty);
        }
        item.appendChild(detail);
        list.appendChild(item);
      }
      card.appendChild(list);
      if (statusEl && statusEl.parentNode) {
        statusEl.parentNode.replaceChild(card, statusEl);
      } else {
        msgs.appendChild(card);
      }
      scrollToEnd();
    }

    // ---- 发送 & 流式接收 ----

    // 流控制器：收敛单次流式请求的全部状态，统一生命周期管理。
    // gen 捕获创建时的 UI 代际，与 panel.streamGen 比对判断是否已被「切换/新建会话」作废。
    function createStream(session, txt) {
      var stream = {
        gen: streamGen,
        abortController: new AbortController(),
        session: session,
        txt: txt,
        typingEl: null,
        msgEl: null,
        content: '',
        pendingTools: [],
        toolStatusEl: null,
        gotAnyResponse: false,
        agentMsg: { role: 'agent', content: '', tools: [] },
        throttledRender: createThrottledRenderer(),
      };
      stream.isStale = function () { return stream.gen !== streamGen; };
      return stream;
    }

    // 终止当前活跃流并立即复位 UI，允许立刻发起新会话的发送。
    function stopStreaming() {
      if (!activeStream) return;
      activeStream.abortController.abort();
      activeStream = null;
      sendBtn.textContent = '发送';
      inp.focus();
    }

    // —— 流式状态操作（纯 UI 逻辑，不涉及传输层）——

    // 待渲染的工具调用落盘为卡片，并复位流式文本态（供下一段文本重新开始）
    function finalizePendingTools(stream) {
      if (stream.pendingTools.length > 0) {
        flushToolCard(stream.toolStatusEl, stream.pendingTools);
        stream.toolStatusEl = null;
        stream.pendingTools = [];
        stream.msgEl = null;
        stream.content = '';
      }
    }

    function updateStreamToolStatus(stream, toolName) {
      if (!stream.toolStatusEl) stream.toolStatusEl = createToolStatus();
      var textEl = stream.toolStatusEl.querySelector('.text');
      if (textEl) textEl.textContent = '正在调用: ' + toolName;
    }

    // 回填工具输出：从后往前匹配最近一个同名且尚未拿到 output 的条目
    function fillToolOutput(tools, data) {
      for (var i = tools.length - 1; i >= 0; i--) {
        if (tools[i].name === (data.name || '?') && !tools[i].output) {
          tools[i].output = data.output || '';
          break;
        }
      }
    }

    // SSE 事件 → 流式状态更新
    function handleStreamEvent(stream, data) {
      switch (data.type) {
        case 'thread':
          // 服务端返回 raw_tid，确认一致
          break;
        case 'text':
          stream.gotAnyResponse = true;
          finalizePendingTools(stream);
          stream.content += data.content || '';
          stream.agentMsg.content = stream.content;
          stream.throttledRender(function () {
            if (stream.isStale()) return;
            if (stream.msgEl) {
              stream.msgEl.innerHTML = renderMarkdown(stream.content);
            } else {
              stream.msgEl = addMsg('agent', stream.content, true);
            }
            scrollToEnd();
          });
          break;
        case 'tool_start':
          stream.gotAnyResponse = true;
          stream.pendingTools.push({ name: data.name || '?', input: data.input || '', output: '' });
          stream.agentMsg.tools.push({ name: data.name || '?', input: data.input || '', output: '' });
          updateStreamToolStatus(stream, data.name || '?');
          break;
        case 'tool_end':
          fillToolOutput(stream.pendingTools, data);
          fillToolOutput(stream.agentMsg.tools, data);
          if (stream.toolStatusEl) {
            var textEl = stream.toolStatusEl.querySelector('.text');
            if (textEl) textEl.textContent = '已完成 ' + stream.pendingTools.length + ' 个工具调用...';
          }
          break;
        case 'done':
          stream.gotAnyResponse = true;
          finalizePendingTools(stream);
          if (data.content) {
            stream.agentMsg.content = data.content;
            if (stream.msgEl) {
              stream.msgEl.innerHTML = renderMarkdown(data.content);
            } else {
              stream.msgEl = addMsg('agent', data.content, true);
            }
          }
          break;
        case 'error':
          finalizePendingTools(stream);
          addMsg('error', '❌ ' + (data.message || '服务端错误'));
          break;
      }
    }

    // 持久化已生成内容（正常结束 / 主动停止 / 被切换作废 三种场景共用）
    function persistStream(stream) {
      if (stream.agentMsg.content || (stream.agentMsg.tools && stream.agentMsg.tools.length)) {
        store.addMessage(stream.session.threadId, stream.agentMsg);
      }
    }

    async function send() {
      var txt = inp.value.trim();
      if (!txt || activeStream) return;

      var session = store.getActiveSession();
      if (!session) {
        createNewSession();
        session = store.getActiveSession();
        if (!session) return;
      }

      // 开启新一轮流：递增代际 + 创建控制器
      streamGen++;
      var stream = createStream(session, txt);
      activeStream = stream;
      sendBtn.textContent = '停止';
      inp.value = '';
      inp.style.height = 'auto';

      // 立即渲染用户消息并持久化
      addMsg('user', txt);
      store.addMessage(session.threadId, { role: 'user', content: txt, tools: [] });

      // 思考中提示
      stream.typingEl = document.createElement('div');
      stream.typingEl.className = 'msg-typing';
      stream.typingEl.textContent = '思考中...';
      msgs.appendChild(stream.typingEl);
      scrollToEnd();

      try {
        var rawTid = session.threadId.split(':').pop();
        var resp = await api.invoke(rawTid, txt, undefined, stream.abortController.signal);

        // Gateway 无 OA cookie 时返回 302
        if (resp.type === 'opaqueredirect' || resp.status === 0 || resp.status === 302) {
          stream.typingEl.remove();
          addMsg('tool', '⚠️ 需要登录OA账号，请在弹出的页面完成登录后重试');
          window.open('https://hrai.prod.hrainative.woa.com', '_blank');
          return;
        }
        if (resp.status === 401) {
          stream.typingEl.remove();
          addMsg('tool', '⚠️ 登录已过期，正在刷新...');
          setTimeout(function () { location.reload(); }, 1500);
          return;
        }
        if (!resp.ok) throw new Error('HTTP ' + resp.status);

        stream.typingEl.remove();

        await parseSSEStream(resp.body.getReader(), function (data) {
          if (stream.isStale()) return;
          handleStreamEvent(stream, data);
        });

        // 流结束后若已切换上下文，仅持久化已生成内容，不再更新标题 / 收尾 UI
        if (stream.isStale()) {
          persistStream(stream);
          return;
        }

        finalizePendingTools(stream);
        persistStream(stream);

        // 若会话标题仍是默认"新对话"，用首条用户消息更新
        if (session.title === '新对话' && txt) {
          var newTitle = txt.substring(0, 30);
          store.renameSession(session.threadId, newTitle);
          renderSidebar();
          // 异步同步到服务端（不阻塞）
          api.renameSession(session.threadId, newTitle).catch(function () {});
        }

        if (!stream.gotAnyResponse) {
          addMsg('agent', '(无响应)');
          store.addMessage(session.threadId, { role: 'agent', content: '(无响应)', tools: [] });
        }

      } catch (err) {
        if (stream.isStale()) {
          // 已被切换/新建会话作废：仅保留已生成内容到旧会话，不写 UI、不复位共享状态
          persistStream(stream);
          return;
        }
        stream.typingEl.remove();
        if (err.name === 'AbortError') {
          // 主动停止：保留已生成内容并提示
          persistStream(stream);
          addMsg('tool', '⏹ 已停止生成');
        } else {
          addMsg('error', '❌ ' + (err.message || '未知错误'));
        }
      } finally {
        // 仅「我仍是活跃流」时复位共享状态，避免误伤新会话的发送
        if (activeStream === stream) {
          activeStream = null;
          sendBtn.textContent = '发送';
          inp.focus();
        }
      }
    }
  }

  // ============================================================================
  // serviceUrl 推断（保持 v2 逻辑）
  // ============================================================================

  function inferServiceUrl() {
    var host = '';
    try { host = window.location.hostname || ''; } catch (e) { }
    if (host.indexOf('.prod.hrainative.woa.com') !== -1) {
      return 'https://agent-server.prod.hrainative.woa.com';
    }
    if (host.indexOf('.app.hrainative.woa.com') !== -1) {
      return 'https://agent-server.app.hrainative.woa.com';
    }
    return 'https://agent-server.app.hrainative.woa.com';
  }

  // ============================================================================
  // 公开 API
  // ============================================================================

  window.AgentChat = {
    version: WIDGET_VERSION,
    init: function (config) {
      config = config || {};
      var meta = {};
      try {
        var mn = document.querySelector('meta[name="agent-name"]');
        var mo = document.querySelector('meta[name="agent-owner"]');
        if (mn) meta.agentName = mn.getAttribute('content');
        if (mo) meta.owner = mo.getAttribute('content');
      } catch (e) { }

      var resolvedAgentName = config.agentName || meta.agentName || 'agent';
      var resolvedOwner = config.owner || meta.owner || '';
      var resolvedServiceUrl = config.serviceUrl || inferServiceUrl();

      var shouldAutoOpen = false;
      try {
        var qs = new URLSearchParams(window.location.search);
        var qa = qs.get('agent') || qs.get('agentName');
        if (qa) resolvedAgentName = qa;
        var qo = qs.get('owner');
        if (qo) resolvedOwner = qo;
        var qsrv = qs.get('server') || qs.get('serviceUrl');
        if (qsrv) resolvedServiceUrl = qsrv;
        var qchat = qs.get('chat');
        shouldAutoOpen = (qchat === 'open' || qchat === '1' || qchat === 'true');
      } catch (e) { }

      config.serviceUrl = resolvedServiceUrl;

      // 可见性检查：agent 禁用时不渲染任何 DOM
      fetch(resolvedServiceUrl + '/api/agent/' + encodeURIComponent(resolvedAgentName)
          + '/visibility?owner=' + encodeURIComponent(resolvedOwner),
          { credentials: 'include', redirect: 'manual' })
        .then(function (r) { return r.ok ? r.json() : { visible: false }; })
        .then(function (d) {
          if (d.visible) {
            injectStyles();
            createPanel(config, resolvedAgentName, resolvedOwner, shouldAutoOpen);
          }
        })
        .catch(function () { /* 网络失败不渲染 */ });
    }
  };
})();
