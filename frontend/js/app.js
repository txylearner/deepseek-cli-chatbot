(function () {
  'use strict';

  var PALETTES = ['default', 'sakura', 'teal', 'sakura-teal'];

  var I18N = {
    zh: {
      'brand.name': 'DeepSeek 对话助手',
      'newChat': '新对话',
      'recent': '最近会话',
      'status.saved': '数据已保存到 SQLite',
      'status.offline': '无法连接后端',
      'header.title': '对话',
      'header.subtitle': '与 DeepSeek 实时对话',
      'docs': '接口文档',
      'clear': '清空',
      'clear.title': '清空当前会话',
      'menu.title': '打开会话列表',
      'input.placeholder': '给 DeepSeek 发消息…',
      'input.hint': 'Enter 发送 · Shift+Enter 换行',
      'input.note': '对话内容会保存到 SQLite，刷新或重启服务后仍然在',
      'theme.toLight': '切换到浅色',
      'theme.toDark': '切换到深色',
      'send.send': '发送',
      'send.stop': '停止生成',
      'scroll.bottom': '回到底部',
      'palette.title': '背景颜色',
      'palette.short': '背景',
      'palette.default': '经典蓝',
      'palette.sakura': '樱花粉',
      'palette.teal': '青绿色',
      'palette.sakuraTeal': '樱花青绿渐变',
      'empty.title': '开始一段新对话',
      'empty.sub': '把问题交给 DeepSeek：回答会逐字出现，对话会自动保存到 SQLite。',
      'suggest.1.title': '写一段代码',
      'suggest.1.desc': '用 Python 写冒泡排序',
      'suggest.1.prompt': '用 Python 写一个冒泡排序，并加注释',
      'suggest.2.title': '解释概念',
      'suggest.2.desc': 'SQLite 索引是什么',
      'suggest.2.prompt': '解释一下 SQLite 的索引',
      'suggest.3.title': '润色文字',
      'suggest.3.desc': '把这段话改得更正式',
      'suggest.3.prompt': '帮我把这段话改得更正式：这个方案我觉得还行，就是有点慢',
      'suggest.4.title': '随便聊聊',
      'suggest.4.desc': '讲个笑话',
      'suggest.4.prompt': '讲个笑话',
      'session.new': '新对话',
      'session.messages': '{n} 条消息',
      'session.delete': '删除会话',
      'copy': '复制',
      'copied': '已复制',
      'toast.deleted': '会话已删除',
      'toast.deleteFailed': '删除失败',
      'toast.networkDelete': '网络异常，删除失败',
      'toast.offline': '无法连接后端，请检查服务是否启动',
      'toast.loadFailed': '加载会话失败',
      'toast.requestFailed': '请求失败，请检查后端或模型配置',
      'toast.copyFailed': '复制失败，请手动选择',
      'msg.stopped': '*(已停止生成)*',
      'msg.requestError': '请求失败：',
      'msg.me': '你',
      'msg.assistant': 'DeepSeek'
    },
    en: {
      'brand.name': 'DeepSeek Chat',
      'newChat': 'New chat',
      'recent': 'Recent chats',
      'status.saved': 'Saved to SQLite',
      'status.offline': 'Backend offline',
      'header.title': 'Chat',
      'header.subtitle': 'Chat with DeepSeek in real time',
      'docs': 'API docs',
      'clear': 'Clear',
      'clear.title': 'Clear current chat',
      'menu.title': 'Open chat list',
      'input.placeholder': 'Message DeepSeek…',
      'input.hint': 'Enter to send · Shift+Enter for newline',
      'input.note': 'Messages are saved to SQLite and survive a refresh or restart',
      'theme.toLight': 'Switch to light',
      'theme.toDark': 'Switch to dark',
      'send.send': 'Send',
      'send.stop': 'Stop generating',
      'scroll.bottom': 'Back to bottom',
      'palette.title': 'Background color',
      'palette.short': 'Bg',
      'palette.default': 'Classic blue',
      'palette.sakura': 'Sakura pink',
      'palette.teal': 'Teal green',
      'palette.sakuraTeal': 'Sakura × teal',
      'empty.title': 'Start a new conversation',
      'empty.sub': 'Ask DeepSeek anything — replies stream in and are saved to SQLite.',
      'suggest.1.title': 'Write some code',
      'suggest.1.desc': 'Bubble sort in Python',
      'suggest.1.prompt': 'Write an annotated bubble sort in Python',
      'suggest.2.title': 'Explain a concept',
      'suggest.2.desc': 'What is a SQLite index?',
      'suggest.2.prompt': 'Explain SQLite indexes',
      'suggest.3.title': 'Polish writing',
      'suggest.3.desc': 'Make this sound more formal',
      'suggest.3.prompt': 'Make this more formal: this plan seems okay, just a bit slow',
      'suggest.4.title': 'Just chat',
      'suggest.4.desc': 'Tell me a joke',
      'suggest.4.prompt': 'Tell me a joke',
      'session.new': 'New chat',
      'session.messages': '{n} messages',
      'session.delete': 'Delete chat',
      'copy': 'Copy',
      'copied': 'Copied',
      'toast.deleted': 'Chat deleted',
      'toast.deleteFailed': 'Delete failed',
      'toast.networkDelete': 'Network error, delete failed',
      'toast.offline': 'Backend offline. Check that the server is running.',
      'toast.loadFailed': 'Failed to load chat',
      'toast.requestFailed': 'Request failed. Check the backend or model settings.',
      'toast.copyFailed': 'Copy failed. Select the text manually.',
      'msg.stopped': '*(stopped)*',
      'msg.requestError': 'Request failed: ',
      'msg.me': 'You',
      'msg.assistant': 'DeepSeek'
    }
  };

  var state = {
    sessionId: newSessionId(),
    sessions: [],
    sending: false,
    controller: null,
    theme: localStorage.getItem('chatbot-theme') || 'dark',
    lang: localStorage.getItem('chatbot-lang') || 'zh',
    palette: localStorage.getItem('chatbot-palette') || 'default',
    online: true
  };

  if (state.lang !== 'zh' && state.lang !== 'en') state.lang = 'zh';
  if (PALETTES.indexOf(state.palette) === -1) state.palette = 'default';

  var els = {
    messages: document.getElementById('messages'),
    list: document.getElementById('session-list'),
    input: document.getElementById('input'),
    send: document.getElementById('send'),
    newChat: document.getElementById('new-chat'),
    clearChat: document.getElementById('clear-chat'),
    theme: document.getElementById('theme-toggle'),
    lang: document.getElementById('lang-toggle'),
    menu: document.getElementById('menu-toggle'),
    overlay: document.getElementById('sidebar-overlay'),
    sidebar: document.getElementById('sidebar'),
    scrollBottom: document.getElementById('scroll-bottom'),
    toast: document.getElementById('toast'),
    charCount: document.getElementById('char-count'),
    sessionCount: document.getElementById('session-count'),
    storageState: document.getElementById('storage-state'),
    paletteToggle: document.getElementById('palette-toggle'),
    palettePopover: document.getElementById('palette-popover')
  };

  var CODE_TICK = '\u0060';
  var CODE_SPAN = new RegExp(CODE_TICK + '([^' + CODE_TICK + ']+)' + CODE_TICK, 'g');
  var FENCE = CODE_TICK + CODE_TICK + CODE_TICK;
  var toastTimer = null;

  function t(key, params) {
    var table = I18N[state.lang] || I18N.zh;
    var value = table[key];
    if (value == null) value = I18N.zh[key];
    if (value == null) value = key;
    if (params) {
      Object.keys(params).forEach(function (name) {
        value = String(value).split('{' + name + '}').join(params[name]);
      });
    }
    return value;
  }

  function newSessionId() {
    return 'web-' + Math.random().toString(36).slice(2, 8);
  }

  function pad(n) {
    return n < 10 ? '0' + n : '' + n;
  }

  function formatTime(value) {
    if (!value) return '';
    var date = new Date(value);
    if (isNaN(date.getTime())) return '';
    return pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + ' ' +
      pad(date.getHours()) + ':' + pad(date.getMinutes());
  }

  function formatNow() {
    var date = new Date();
    return pad(date.getHours()) + ':' + pad(date.getMinutes());
  }

  function setStorageState(text) {
    if (els.storageState) els.storageState.textContent = text;
  }

  function applyConnectionState() {
    setStorageState(state.online ? t('status.saved') : t('status.offline'));
  }

  function showToast(text, type) {
    if (!els.toast) return;
    els.toast.textContent = text;
    els.toast.className = 'toast show' + (type ? ' ' + type : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      els.toast.className = 'toast';
    }, 2400);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement('textarea');
      area.value = text;
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.appendChild(area);
      area.select();
      try {
        document.execCommand('copy');
        resolve();
      } catch (err) {
        reject(err);
      }
      document.body.removeChild(area);
    });
  }

  function scrollToBottom(behavior) {
    if (!els.messages) return;
    els.messages.scrollTo({ top: els.messages.scrollHeight, behavior: behavior || 'auto' });
    updateScrollButton();
  }

  function updateScrollButton() {
    if (!els.scrollBottom || !els.messages) return;
    var gap = els.messages.scrollHeight - els.messages.scrollTop - els.messages.clientHeight;
    els.scrollBottom.hidden = gap < 200;
  }

  function toggleSidebar(open) {
    if (!els.sidebar || !els.overlay) return;
    els.sidebar.classList.toggle('open', !!open);
    els.overlay.classList.toggle('show', !!open);
  }

  function closeSidebar() {
    toggleSidebar(false);
  }

  function openPalette() {
    if (els.palettePopover) els.palettePopover.hidden = false;
  }

  function closePalette() {
    if (els.palettePopover) els.palettePopover.hidden = true;
  }

  function togglePalette() {
    if (!els.palettePopover) return;
    els.palettePopover.hidden = !els.palettePopover.hidden;
  }

  /* ---------- 主题、语言、背景色 ---------- */
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    if (els.theme) {
      els.theme.textContent = state.theme === 'dark' ? '☀' : '☾';
      var title = state.theme === 'dark' ? t('theme.toLight') : t('theme.toDark');
      els.theme.title = title;
      els.theme.setAttribute('aria-label', title);
    }
  }

  function applyPalette() {
    document.documentElement.setAttribute('data-palette', state.palette);
    document.querySelectorAll('.palette-option').forEach(function (button) {
      button.classList.toggle('active', button.getAttribute('data-palette') === state.palette);
    });
  }

  function applyLanguage() {
    document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
    document.title = t('brand.name');

    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      el.setAttribute('placeholder', t(el.getAttribute('data-i18n-placeholder')));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      el.title = t(el.getAttribute('data-i18n-title'));
    });
    document.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
    });

    if (els.lang) {
      els.lang.textContent = state.lang === 'zh' ? 'EN' : '中';
      var langTitle = state.lang === 'zh' ? 'Switch to English' : '切换到中文';
      els.lang.title = langTitle;
      els.lang.setAttribute('aria-label', langTitle);
    }
    if (els.theme) {
      var themeTitle = state.theme === 'dark' ? t('theme.toLight') : t('theme.toDark');
      els.theme.title = themeTitle;
      els.theme.setAttribute('aria-label', themeTitle);
    }
    if (els.send) {
      var sendTitle = state.sending ? t('send.stop') : t('send.send');
      els.send.title = sendTitle;
      els.send.setAttribute('aria-label', sendTitle);
    }

    document.querySelectorAll('.copy-code').forEach(function (button) {
      button.textContent = t('copy');
    });
    document.querySelectorAll('.msg.user .avatar').forEach(function (avatar) {
      avatar.textContent = t('msg.me');
    });

    applyConnectionState();
    renderSidebar();
    refreshEmpty();
  }

  if (els.theme) {
    els.theme.addEventListener('click', function () {
      state.theme = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('chatbot-theme', state.theme);
      applyTheme();
    });
  }

  if (els.lang) {
    els.lang.addEventListener('click', function () {
      state.lang = state.lang === 'zh' ? 'en' : 'zh';
      localStorage.setItem('chatbot-lang', state.lang);
      applyLanguage();
    });
  }

  if (els.paletteToggle) {
    els.paletteToggle.addEventListener('click', function (ev) {
      ev.stopPropagation();
      togglePalette();
    });
  }

  document.querySelectorAll('.palette-option').forEach(function (button) {
    button.addEventListener('click', function () {
      var palette = button.getAttribute('data-palette');
      if (palette && PALETTES.indexOf(palette) !== -1) {
        state.palette = palette;
        localStorage.setItem('chatbot-palette', state.palette);
        applyPalette();
      }
      closePalette();
    });
  });

  document.addEventListener('click', function (ev) {
    var target = ev.target;
    var inside = target && target.closest ? target.closest('.palette-wrap') : null;
    if (!inside) closePalette();
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
        out.push(
          '<div class="code-block">' +
            '<div class="code-head">' +
              '<span class="code-lang">' + escapeHtml(lang || 'text') + '</span>' +
              '<button type="button" class="copy-code">' + escapeHtml(t('copy')) + '</button>' +
            '</div>' +
            '<pre><code class="lang-' + escapeHtml(lang) + '">' +
              escapeHtml(body.replace(/\n$/, '')) +
            '</code></pre>' +
          '</div>'
        );
      } else {
        out.push(renderBlocks(parts[i]));
      }
    }
    return out.join('');
  }

  /* ---------- 消息 ---------- */
  function clearMessages() {
    els.messages.innerHTML = '';
    if (els.scrollBottom) els.scrollBottom.hidden = true;
  }

  function showEmpty() {
    var box = document.createElement('div');
    box.className = 'empty';

    var mark = document.createElement('div');
    mark.className = 'empty-mark whale';

    var title = document.createElement('div');
    title.className = 'empty-title';
    title.textContent = t('empty.title');

    var sub = document.createElement('div');
    sub.className = 'empty-sub';
    sub.textContent = t('empty.sub');

    var grid = document.createElement('div');
    grid.className = 'suggestions';

    var items = [
      { icon: '⌘', title: t('suggest.1.title'), desc: t('suggest.1.desc'), prompt: t('suggest.1.prompt') },
      { icon: 'Aa', title: t('suggest.2.title'), desc: t('suggest.2.desc'), prompt: t('suggest.2.prompt') },
      { icon: '✎', title: t('suggest.3.title'), desc: t('suggest.3.desc'), prompt: t('suggest.3.prompt') },
      { icon: '✦', title: t('suggest.4.title'), desc: t('suggest.4.desc'), prompt: t('suggest.4.prompt') }
    ];

    items.forEach(function (item) {
      var card = document.createElement('button');
      card.type = 'button';
      card.className = 'suggestion';

      var icon = document.createElement('span');
      icon.className = 'suggestion-icon';
      icon.textContent = item.icon;

      var text = document.createElement('span');
      text.className = 'suggestion-text';

      var name = document.createElement('span');
      name.className = 'suggestion-title';
      name.textContent = item.title;

      var desc = document.createElement('span');
      desc.className = 'suggestion-desc';
      desc.textContent = item.desc;

      text.appendChild(name);
      text.appendChild(desc);
      card.appendChild(icon);
      card.appendChild(text);
      card.addEventListener('click', function () {
        els.input.value = item.prompt;
        autoGrow();
        updateCharCount();
        els.input.focus();
      });
      grid.appendChild(card);
    });

    box.appendChild(mark);
    box.appendChild(title);
    box.appendChild(sub);
    box.appendChild(grid);
    els.messages.appendChild(box);
  }

  function refreshEmpty() {
    var empty = els.messages ? els.messages.querySelector('.empty') : null;
    if (!empty) return;
    els.messages.removeChild(empty);
    showEmpty();
  }

  function addMessage(role, timeText) {
    var empty = els.messages.querySelector('.empty');
    if (empty) els.messages.removeChild(empty);

    var row = document.createElement('div');
    row.className = 'msg ' + role;

    var avatar = document.createElement('div');
    avatar.className = 'avatar';
    if (role === 'user') {
      avatar.textContent = t('msg.me');
    } else {
      avatar.classList.add('whale');
    }

    var body = document.createElement('div');
    body.className = 'msg-body';

    var head = document.createElement('div');
    head.className = 'msg-head';

    if (role !== 'user') {
      var name = document.createElement('span');
      name.className = 'msg-name';
      name.textContent = t('msg.assistant');
      head.appendChild(name);
    }

    if (timeText) {
      var time = document.createElement('span');
      time.className = 'msg-time';
      time.textContent = timeText;
      head.appendChild(time);
    }

    var bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (head.childNodes.length) body.appendChild(head);
    body.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(body);
    els.messages.appendChild(row);
    scrollToBottom();
    return bubble;
  }

  function paint(el, text, streaming) {
    el.innerHTML = renderMarkdown(text) + (streaming ? '<span class="caret"></span>' : '');
    scrollToBottom();
  }

  /* ---------- 会话 ---------- */
  function renderSidebar() {
    if (!els.list) return;
    var sessions = state.sessions.slice();
    var hasCurrent = sessions.some(function (item) { return item.id === state.sessionId; });
    if (!hasCurrent) {
      sessions.unshift({ id: state.sessionId, title: t('session.new'), message_count: 0, updated_at: '', draft: true });
    }

    els.list.innerHTML = '';
    if (els.sessionCount) els.sessionCount.textContent = String(state.sessions.length);

    sessions.forEach(function (session) {
      var row = document.createElement('div');
      row.className = 'session' +
        (session.id === state.sessionId ? ' active' : '') +
        (session.draft ? ' draft' : '');
      row.title = session.id;

      var text = document.createElement('div');
      text.className = 'session-text';

      var name = document.createElement('span');
      name.className = 'session-name';
      name.textContent = (session.title || '').trim() || t('session.new');
      text.appendChild(name);

      var parts = [];
      if (session.message_count) parts.push(t('session.messages', { n: session.message_count }));
      var time = formatTime(session.updated_at);
      if (time) parts.push(time);
      if (parts.length) {
        var meta = document.createElement('span');
        meta.className = 'session-meta';
        meta.textContent = parts.join(' · ');
        text.appendChild(meta);
      }

      var del = document.createElement('button');
      del.type = 'button';
      del.className = 'session-del';
      del.textContent = '×';
      del.title = t('session.delete');
      del.setAttribute('aria-label', t('session.delete'));
      del.addEventListener('click', function (ev) {
        ev.stopPropagation();
        removeSession(session.id);
      });

      row.appendChild(text);
      row.appendChild(del);
      row.addEventListener('click', function () {
        if (session.draft) { els.input.focus(); return; }
        if (!state.sending) openSession(session.id);
      });
      els.list.appendChild(row);
    });
  }

  function loadSessions() {
    fetch('/sessions/overview')
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(function (data) {
        state.sessions = data.sessions || [];
        state.online = true;
        applyConnectionState();
        renderSidebar();
      })
      .catch(function () {
        state.sessions = [];
        state.online = false;
        applyConnectionState();
        showToast(t('toast.offline'), 'error');
        renderSidebar();
      });
  }

  function openSession(id) {
    state.sessionId = id;
    renderSidebar();
    clearMessages();
    closeSidebar();
    try {
      history.replaceState(null, '', '?session=' + encodeURIComponent(id));
    } catch (err) { /* ignore */ }

    fetch('/sessions/' + encodeURIComponent(id) + '/messages')
      .then(function (response) {
        return response.status === 404 ? null : response.json();
      })
      .then(function (data) {
        if (!data) { showEmpty(); return; }
        var messages = data.messages || [];
        messages.forEach(function (m) {
          var bubble = addMessage(m.role === 'user' ? 'user' : 'assistant');
          if (m.role === 'user') bubble.textContent = m.content;
          else bubble.innerHTML = renderMarkdown(m.content);
        });
        if (!messages.length) showEmpty();
      })
      .catch(function () {
        showEmpty();
        showToast(t('toast.loadFailed'), 'error');
      });
  }

  function removeSession(id) {
    fetch('/sessions/' + encodeURIComponent(id), { method: 'DELETE' })
      .then(function (response) {
        if (response.ok) showToast(t('toast.deleted'));
        else if (response.status !== 404) showToast(t('toast.deleteFailed'), 'error');
      })
      .catch(function () {
        showToast(t('toast.networkDelete'), 'error');
      })
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
    closeSidebar();
    closePalette();
    try {
      history.replaceState(null, '', location.pathname);
    } catch (err) { /* ignore */ }
    els.input.focus();
  }

  /* ---------- 发送 ---------- */
  function setSending(flag) {
    state.sending = flag;
    var title = flag ? t('send.stop') : t('send.send');
    els.send.textContent = flag ? '■' : '↑';
    els.send.title = title;
    els.send.setAttribute('aria-label', title);
    els.send.classList.toggle('stop', flag);
  }

  function autoGrow() {
    els.input.style.height = 'auto';
    els.input.style.height = Math.min(els.input.scrollHeight, 200) + 'px';
  }

  function updateCharCount() {
    if (!els.charCount) return;
    var length = els.input.value.length;
    els.charCount.textContent = length ? String(length) : '';
  }

  function send() {
    if (state.sending) { stopStreaming(); return; }
    var text = els.input.value.trim();
    if (!text) { els.input.focus(); return; }

    els.input.value = '';
    autoGrow();
    updateCharCount();
    setSending(true);

    var userBubble = addMessage('user');
    userBubble.textContent = text;

    var aiBubble = addMessage('assistant', formatNow());
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
            throw new Error('HTTP ' + res.status + ': ' + body);
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
          paint(aiBubble, (acc || '') + '\n\n' + t('msg.stopped'), false);
        } else {
          aiBubble.classList.add('error');
          aiBubble.textContent = t('msg.requestError') + err.message;
          showToast(t('toast.requestFailed'), 'error');
        }
      })
      .finally(function () {
        state.controller = null;
        setSending(false);
        if (acc) paint(aiBubble, acc, false);
        loadSessions();
        updateScrollButton();
      });
  }

  function stopStreaming() {
    if (state.controller) state.controller.abort();
  }

  /* ---------- 事件绑定 ---------- */
  if (els.send) els.send.addEventListener('click', send);

  if (els.input) {
    els.input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' && !ev.shiftKey && !ev.isComposing) {
        ev.preventDefault();
        send();
      }
    });
    els.input.addEventListener('input', function () {
      autoGrow();
      updateCharCount();
    });
  }

  if (els.newChat) {
    els.newChat.addEventListener('click', function () {
      if (state.controller) state.controller.abort();
      startNewChat();
    });
  }

  if (els.clearChat) {
    els.clearChat.addEventListener('click', function () {
      removeSession(state.sessionId);
    });
  }

  if (els.menu) {
    els.menu.addEventListener('click', function () {
      toggleSidebar(true);
    });
  }

  if (els.overlay) {
    els.overlay.addEventListener('click', closeSidebar);
  }

  if (els.messages) {
    els.messages.addEventListener('scroll', updateScrollButton);
    els.messages.addEventListener('click', function (ev) {
      var target = ev.target;
      var btn = target && target.closest ? target.closest('.copy-code') : null;
      if (!btn) return;
      var block = btn.closest('.code-block');
      var code = block ? block.querySelector('code') : null;
      if (!code) return;
      copyText(code.textContent)
        .then(function () {
          btn.textContent = t('copied');
          setTimeout(function () { btn.textContent = t('copy'); }, 1500);
        })
        .catch(function () {
          showToast(t('toast.copyFailed'), 'error');
        });
    });
  }

  if (els.scrollBottom) {
    els.scrollBottom.addEventListener('click', function () {
      scrollToBottom('smooth');
    });
  }

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      closeSidebar();
      closePalette();
    }
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
  applyPalette();
  applyLanguage();
  showEmpty();
  renderSidebar();
  loadSessions();
  updateCharCount();
  els.input.focus();

  var initialSession = new URLSearchParams(location.search).get('session');
  if (initialSession) openSession(initialSession);
})();
