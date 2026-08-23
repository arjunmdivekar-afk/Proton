/**
 * Proton Web UI - Chat Studio View Controller
 */

import { api } from '../api.js';
import { state, events } from '../state.js';

export function initChatView() {
  const messagesContainer = document.getElementById('chat-messages');
  const textarea = document.getElementById('chat-prompt-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const sessionList = document.getElementById('chat-session-list');
  const newChatBtn = document.getElementById('new-chat-btn');
  const tokSpeedEl = document.getElementById('hud-tok-speed');
  const latencyEl = document.getElementById('hud-latency');
  const contextEl = document.getElementById('hud-context');

  let currentChat = { id: 'default', title: 'General Conversation', messages: [] };

  // Load chat sessions from local storage
  function loadSessions() {
    try {
      const saved = localStorage.getItem('proton_chat_sessions');
      state.sessions = saved ? JSON.parse(saved) : [{ id: 'default', title: 'General Conversation', messages: [] }];
    } catch (e) {
      state.sessions = [{ id: 'default', title: 'General Conversation', messages: [] }];
    }
    renderSessionList();
  }

  function saveSessions() {
    localStorage.setItem('proton_chat_sessions', JSON.stringify(state.sessions));
  }

  function renderSessionList() {
    if (!sessionList) return;
    sessionList.innerHTML = '';
    state.sessions.forEach(s => {
      const el = document.createElement('div');
      el.className = `session-item ${s.id === currentChat.id ? 'active' : ''}`;
      el.innerHTML = `
        <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">💬 ${s.title}</span>
        <button class="btn-ghost btn-sm" style="padding:2px 4px;" title="Delete">✕</button>
      `;
      el.querySelector('button').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm(`Delete "${s.title}"?`)) {
          state.sessions = state.sessions.filter(item => item.id !== s.id);
          if (currentChat.id === s.id) {
            currentChat = state.sessions[0] || { id: 'default', title: 'New Conversation', messages: [] };
          }
          saveSessions();
          renderSessionList();
          renderMessages();
        }
      });
      el.addEventListener('click', () => switchSession(s.id));
      sessionList.appendChild(el);
    });
  }

  function switchSession(sessionId) {
    const target = state.sessions.find(s => s.id === sessionId);
    if (target) {
      currentChat = target;
      renderSessionList();
      renderMessages();
    }
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      const newId = `session-${Date.now()}`;
      const newSession = { id: newId, title: `Chat ${state.sessions.length + 1}`, messages: [] };
      state.sessions.unshift(newSession);
      currentChat = newSession;
      saveSessions();
      renderSessionList();
      renderMessages();
    });
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let formatted = text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/```([\w-]+)?\n([\s\S]*?)```/g, (m, lang, code) => {
        return `<pre><button class="code-copy-btn" onclick="navigator.clipboard.writeText(decodeURIComponent('${encodeURIComponent(code)}'))">Copy</button><code class="language-${lang || 'text'}">${code}</code></pre>`;
      })
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
    return formatted;
  }

  function renderMessages() {
    if (!messagesContainer) return;
    messagesContainer.innerHTML = '';

    if (currentChat.messages.length === 0) {
      messagesContainer.innerHTML = `
        <div style="margin: auto; text-align: center; color: var(--text-muted); max-width: 400px;">
          <h3 style="color: var(--text-primary); font-size: 16px; font-weight: 500; margin-bottom: 6px;">How can Proton help you today?</h3>
          <p style="font-size: 13px; color: var(--text-secondary);">Ask code questions, execute terminal commands, or trigger autonomous tasks.</p>
        </div>
      `;
      return;
    }

    currentChat.messages.forEach(msg => {
      appendMessageBubble(msg.role, msg.content);
    });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendMessageBubble(role, content) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    row.innerHTML = `
      <div class="message-avatar">${role === 'user' ? 'U' : 'P'}</div>
      <div class="message-bubble">${formatMarkdown(content)}</div>
    `;
    messagesContainer.appendChild(row);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return row.querySelector('.message-bubble');
  }

  // Sidebar toggle
  const toggleHistoryBtn = document.getElementById('toggle-chat-history');
  const chatSidebar = document.getElementById('chat-sidebar');
  if (toggleHistoryBtn && chatSidebar) {
    toggleHistoryBtn.addEventListener('click', () => {
      chatSidebar.classList.toggle('hidden');
    });
  }

  async function handleSend() {
    const text = textarea.value.trim();
    if (!text || state.isStreaming) return;

    textarea.value = '';
    textarea.style.height = '42px';

    // Auto-update session title from first prompt
    if (currentChat.messages.length === 0) {
      currentChat.title = text.slice(0, 24) + (text.length > 24 ? '...' : '');
      renderSessionList();
    }

    // Append User Message
    currentChat.messages.push({ role: 'user', content: text });
    appendMessageBubble('user', text);
    saveSessions();

    // Prepare Assistant Bubble
    const assistantBubble = appendMessageBubble('assistant', '');
    let assistantText = '';
    state.isStreaming = true;

    const tStart = performance.now();
    let tokenCount = 0;

    await api.streamChat(
      currentChat.messages,
      state.activeModel,
      { temperature: state.settings.temperature, max_tokens: state.settings.max_tokens },
      (delta) => {
        assistantText += delta;
        tokenCount++;
        assistantBubble.innerHTML = formatMarkdown(assistantText);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Update token speed HUD
        const elapsedSec = (performance.now() - tStart) / 1000;
        const tokPerSec = elapsedSec > 0 ? (tokenCount / elapsedSec).toFixed(1) : '0.0';
        if (tokSpeedEl) tokSpeedEl.innerText = `${tokPerSec} tok/s`;
      },
      () => {
        state.isStreaming = false;
        const totalDuration = ((performance.now() - tStart)).toFixed(0);
        if (latencyEl) latencyEl.innerText = `${totalDuration} ms`;
        currentChat.messages.push({ role: 'assistant', content: assistantText });
        saveSessions();
      },
      (err) => {
        state.isStreaming = false;
        assistantBubble.innerHTML = `<span style="color: var(--accent-rose);">[Error: ${err.message}]</span>`;
      }
    );
  }

  if (sendBtn) sendBtn.addEventListener('click', handleSend);
  if (textarea) {
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }

  loadSessions();
  renderMessages();

  // Export Chat Trigger
  const exportBtn = document.getElementById('chat-export-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentChat, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `${currentChat.title.replace(/\s+/g, '_')}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }
}
