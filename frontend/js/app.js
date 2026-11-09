(function () {
  'use strict';

  var state = {
    sessionId: newSessionId(),
    sessions: [],
    sending: false,
    controller: null,
    theme: localStorage.getItem('chatbot-theme') || 'dark'
  };

  var els = {
    messages: document.getElementById('messages'),
    list: document.getElementById('session-list'),
    input: document.getElementById('input'),
    send: document.getElementById('send'),
    newChat: document.getElementById('new-chat'),
    clearChat: document.getElementById('clear-chat'),
    theme: document.getElementById('theme-toggle')
  };

  var CODE_TICK = '\u0060';                    // 反引号
  var CODE_SPAN = new RegExp(CODE_TICK + '([^' + CODE_TICK + ']+)' + CODE_TICK, 'g');
  var FENCE = CODE_TICK + CODE_TICK + CODE_TICK;

  function newSessionId() {
    return 'web-' + Math.random().toString(36).slice(2, 8);
  }

  /* ---------- 主题 ---------- */
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    els.theme.textContent = state.theme === 'dark' ? '☀️' : '🌙';
  }

  els.theme.addEventListener('click', function () {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('chatbot-theme', state.theme);
    applyTheme();
  });

  /* ---------- 迷你 Markdown 渲染 ---------- */
  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function inline(raw) {
    var codes = [];
    var s = escapeHtml(raw);
    s = s.replace(CODE_SPAN, function (m, p1) {
      codes.push(p1);
      return '\u0000' + (codes.length - 1) + '\u0000';
    });
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    s = s.replace(/\u0000(\d+)\u0000/g, function (m, i) {
      return '<code>' + codes[Number(i)] + '</code>';
    });
    return s;
  }

  function isBlockStart(line) {
    return /^(#{1,6})\s+/.test(line) ||
      /^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line) ||
      /^\s*>\s?/.test(line) ||
      /^\s*([-*+])\s+/.test(line) ||
      /^\s*\d+[.)]\s+/.test(line);
  }

  function renderBlocks(text) {
    var lines = text.split('\n');
    var html = [];
    var i = 0;
    while (i < lines.length) {
      var line = lines[i];
      if (!line.trim()) { i++; continue; }

      var h = line.match(/^(#{1,6})\s+(.*)$/);
      if (h) {
        var lv = Math.min(h[1].length, 4);
        html.push('<h' + lv + '>' + inline(h[2]) + '</h' + lv + '>');
        i++; continue;
      }
      if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) { html.push('<hr>'); i++; continue; }

      if (/^\s*>\s?/.test(line)) {
        var quote = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
          quote.push(lines[i].replace(/^\s*>\s?/, ''));
          i++;
        }
        html.push('<blockquote>' + inline(quote.join('\n')).replace(/\n/g, '<br>') + '</blockquote>');
        continue;
      }

      if (/^\s*([-*+])\s+/.test(line)) {
        var items = [];
        while (i < lines.length && /^\s*([-*+])\s+/.test(lines[i])) {
          items.push('<li>' + inline(lines[i].replace(/^\s*[-*+]\s+/, '')) + '</li>');
          i++;
        }
        html.push('<ul>' + items.join('') + '</ul>');
        continue;
      }

      if (/^\s*\d+[.)]\s+/.test(line)) {
        var ordered = [];
        while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) {
          ordered.push('<li>' + inline(lines[i].replace(/^\s*\d+[.)]\s+/, '')) + '</li>');
          i++;
        }
        html.push('<ol>' + ordered.join('') + '</ol>');
        continue;
      }

      var para = [];
      while (i < lines.length && lines[i].trim() && !isBlockStart(lines[i])) {
        para.push(lines[i]);
        i++;
      }
      html.push('<p>' + inline(para.join('\n')).replace(/\n/g, '<br>') + '</p>');
    }
    return html.join('');
  }

  function renderMarkdown(text) {
    var parts = text.split(FENCE);
    var out = [];
    for (var i = 0; i < parts.length; i++) {
      if (i % 2 === 1) {
        var block = parts[i];
        var nl = block.indexOf('\n');
        var lang = nl >= 0 ? block.slice(0, nl).trim() : '';
        var body = nl >= 0 ? block.slice(nl + 1) : block;
        out.push('<pre><code class="lang-' + escapeHtml(lang) + '">' + escapeHtml(body.replace(/\n$/, '')) + '</code></pre>');
      } else {
        out.push(renderBlocks(parts[i]));
      }
    }
    return out.join('');
  }

  /* ---------- 消息渲染 ---------- */
  function scrollToBottom() {
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function clearMessages() {
    els.messages.innerHTML = '';
  }

  function showEmpty() {
    var box = document.createElement('div');
    box.className = 'empty';
    var title = document.createElement('div');
    title.className = 'empty-title';
    title.textContent = '开始一段新对话';
    box.appendChild(title);

    var subtitle = document.createElement('div');
    subtitle.className = 'empty-sub';
    subtitle.textContent = '消息会写入 SQLite（chat.db），刷新页面或重启服务后仍然在。';
    box.appendChild(subtitle);

    var chips = document.createElement('div');
    chips.className = 'chips';
    ['解释单词 apple', '用 Python 写一个冒泡排序', '帮我把这句话改得更地道', '讲个笑话'].forEach(function (t) {
      var b = document.createElement('button');
      b.className = 'chip';
      b.textContent = t;
      b.addEventListener('click', function () {
        els.input.value = t;
        els.input.focus();
        autoGrow();
      });
      chips.appendChild(b);
    });
    box.appendChild(chips);
    els.messages.appendChild(box);
  }

  function addMessage(role) {
    var empty = els.messages.querySelector('.empty');
    if (empty) els.messages.removeChild(empty);
    var wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    var bubble = document.createElement('div');
    bubble.className = 'bubble';
    wrap.appendChild(bubble);
    els.messages.appendChild(wrap);
    scrollToBottom();
    return bubble;
  }

  function paint(el, text, streaming) {
    el.innerHTML = renderMarkdown(text) + (streaming ? '<span class="caret"></span>' : '');
    scrollToBottom();
  }

  /* ---------- 会话 ---------- */
  function formatTime(value) {
    if (!value) return '';
    var date = new Date(value);
    if (isNaN(date.getTime())) return '';
    var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
    return pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + ' ' +
      pad(date.getHours()) + ':' + pad(date.getMinutes());
  }

  function setStorageState(text) {
    var el = document.getElementById('storage-state');
    if (el) el.textContent = text;
  }

  function renderSidebar() {
    var sessions = state.sessions.slice();
    var hasCurrent = sessions.some(function (item) { return item.id === state.sessionId; });
    if (!hasCurrent) {
      sessions.unshift({ id: state.sessionId, title: '新对话', message_count: 0, updated_at: '' });
    }

    els.list.innerHTML = '';
    sessions.forEach(function (session) {
      var row = document.createElement('div');
      row.className = 'session' + (session.id === state.sessionId ? ' active' : '');
      row.title = session.id;

      var text = document.createElement('div');
      text.className = 'session-text';

      var name = document.createElement('span');
      name.className = 'session-name';
      name.textContent = (session.title || '').trim() || '新对话';

      var meta = document.createElement('span');
      meta.className = 'session-meta';
      var parts = [];
      if (session.message_count) parts.push(session.message_count + ' 条消息');
      var time = formatTime(session.updated_at);
      if (time) parts.push(time);
      meta.textContent = parts.join(' · ');

      text.appendChild(name);
      text.appendChild(meta);

      var del = document.createElement('button');
      del.className = 'session-del';
      del.textContent = '×';
      del.title = '删除会话';
      del.addEventListener('click', function (ev) {
        ev.stopPropagation();
        removeSession(session.id);
      });

      row.appendChild(text);
      row.appendChild(del);
      row.addEventListener('click', function () {
        if (!state.sending) openSession(session.id);
      });
      els.list.appendChild(row);
    });
  }

  function loadSessions() {
    fetch('/sessions/overview')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        state.sessions = data.sessions || [];
        setStorageState('会话已保存到 SQLite · 重启后仍在');
        renderSidebar();
      })
      .catch(function () {
        state.sessions = [];
        setStorageState('无法连接后端，请检查服务是否启动');
        renderSidebar();
      });
  }

  function openSession(id) {
    state.sessionId = id;
    renderSidebar();
    clearMessages();
    fetch('/sessions/' + encodeURIComponent(id) + '/messages')
      .then(function (r) { return r.status === 404 ? null : r.json(); })
      .then(function (data) {
        if (!data) { showEmpty(); return; }
        (data.messages || []).forEach(function (m) {
          var bubble = addMessage(m.role === 'user' ? 'user' : 'assistant');
          if (m.role === 'user') bubble.textContent = m.content;
          else bubble.innerHTML = renderMarkdown(m.content);
        });
        if (!(data.messages || []).length) showEmpty();
      })
      .catch(function () { showEmpty(); });
  }

  function removeSession(id) {
    fetch('/sessions/' + encodeURIComponent(id), { method: 'DELETE' })
      .catch(function () { })
      .finally(function () {
        if (id === state.sessionId) startNewChat();
        loadSessions();
      });
  }

  function startNewChat() {
    if (state.controller) state.controller.abort();
    state.sessionId = newSessionId();
    clearMessages();
    showEmpty();
    renderSidebar();
    els.input.focus();
  }

  /* ---------- 发送 ---------- */
  function setSending(flag) {
    state.sending = flag;
    els.send.textContent = flag ? '■' : '↑';
    els.send.title = flag ? '停止生成' : '发送';
    els.send.classList.toggle('stop', flag);
  }

  function autoGrow() {
    els.input.style.height = 'auto';
    els.input.style.height = Math.min(els.input.scrollHeight, 180) + 'px';
  }

  function send() {
    if (state.sending) { stopStreaming(); return; }
    var text = els.input.value.trim();
    if (!text) return;

    els.input.value = '';
    autoGrow();
    setSending(true);

    var userBubble = addMessage('user');
    userBubble.textContent = text;

    var aiBubble = addMessage('assistant');
    aiBubble.innerHTML = '<span class="caret"></span>';

    var acc = '';
    state.controller = new AbortController();

    fetch('/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId, message: text }),
      signal: state.controller.signal
    })
      .then(function (res) {
        if (!res.ok) {
          return res.text().then(function (body) {
            throw new Error('HTTP ' + res.status + '：' + body);
          });
        }
        var reader = res.body.getReader();
        var decoder = new TextDecoder('utf-8');
        return (function pump() {
          return reader.read().then(function (chunk) {
            if (chunk.done) return;
            acc += decoder.decode(chunk.value, { stream: true });
            paint(aiBubble, acc, true);
            return pump();
          });
        })();
      })
      .catch(function (err) {
        if (err.name === 'AbortError') {
          paint(aiBubble, (acc || '') + '\n\n*(已停止生成)*', false);
        } else {
          aiBubble.classList.add('error');
          aiBubble.textContent = '请求失败：' + err.message;
        }
      })
      .finally(function () {
        state.controller = null;
        setSending(false);
        if (acc) paint(aiBubble, acc, false);
        loadSessions();
      });
  }

  function stopStreaming() {
    if (state.controller) state.controller.abort();
  }

  /* ---------- 事件绑定 ---------- */
  els.send.addEventListener('click', send);

  els.input.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter' && !ev.shiftKey && !ev.isComposing) {
      ev.preventDefault();
      send();
    }
  });

  els.input.addEventListener('input', autoGrow);

  els.newChat.addEventListener('click', function () {
    if (state.controller) state.controller.abort();
    startNewChat();
  });

  els.clearChat.addEventListener('click', function () {
    removeSession(state.sessionId);
  });

  /* 前端代码最终必须下发到浏览器，这里只提高随手查看的门槛；
     真正的保护是：业务逻辑、提示词和 Key 都留在后端。 */
  document.addEventListener('keydown', function (ev) {
    var key = (ev.key || '').toUpperCase();
    if (ev.key === 'F12' ||
        (ev.ctrlKey && ev.shiftKey && (key === 'I' || key === 'J' || key === 'C')) ||
        (ev.ctrlKey && key === 'U')) {
      ev.preventDefault();
    }
  });

  /* ---------- 启动 ---------- */
  applyTheme();
  showEmpty();
  renderSidebar();
  loadSessions();
  els.input.focus();
})();
