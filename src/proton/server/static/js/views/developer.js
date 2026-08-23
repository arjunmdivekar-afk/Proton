/**
 * Proton Web UI - Developer Server Dashboard Controller
 */

import { api } from '../api.js';
import { state, events } from '../state.js';

export function initDeveloperView() {
  const statusToggle = document.getElementById('dev-status-toggle');
  const reachabilityEl = document.getElementById('dev-reachability-url');
  const copyReachabilityBtn = document.getElementById('dev-copy-reachability');
  const loadedModelsList = document.getElementById('dev-loaded-models');
  const logsContainer = document.getElementById('dev-logs-stream');
  const clearLogsBtn = document.getElementById('dev-clear-logs');
  const loadModelBtn = document.getElementById('dev-load-model-btn');

  async function loadStatus() {
    try {
      const data = await api.getDevStatus();
      if (reachabilityEl) reachabilityEl.innerText = data.reachability;

      if (loadedModelsList) {
        loadedModelsList.innerHTML = '';
        if (data.loaded_models && data.loaded_models.length > 0) {
          data.loaded_models.forEach(m => {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.flex = '1';
            card.style.minWidth = '240px';
            card.innerHTML = `
              <div class="card-header" style="margin-bottom: 6px;">
                <span class="card-title" style="font-size: 13.5px;">🤖 ${m.id}</span>
                ${m.is_default ? '<span class="badge badge-emerald">Default</span>' : ''}
              </div>
              <div style="font-size: 12px; color: var(--text-secondary); display: flex; gap: 12px;">
                <span>Params: <strong>${m.parameters}</strong></span>
                <span>Size: <strong>${m.size_gb.toFixed(1)} GB</strong></span>
              </div>
            `;
            loadedModelsList.appendChild(card);
          });
        } else {
          loadedModelsList.innerHTML = '<div style="color: var(--text-muted); font-size: 13px;">No models currently loaded in memory.</div>';
        }
      }
    } catch (err) {
      console.error('Error loading developer status:', err);
    }
  }

  async function loadLogs() {
    if (!logsContainer) return;
    try {
      const data = await api.getDevLogs();
      logsContainer.innerHTML = '';
      if (data.logs) {
        data.logs.forEach(appendLog);
      }
    } catch (err) {
      console.error('Error loading developer logs:', err);
    }
  }

  function appendLog(log) {
    if (!logsContainer) return;
    const row = document.createElement('div');
    row.className = 'log-entry';
    const lvlClass = log.level === 'ERROR' ? 'log-level-error' : (log.level === 'INFO' ? 'log-level-info' : 'log-level-debug');
    row.innerHTML = `
      <span class="log-time">${log.timestamp}</span>
      <span class="${lvlClass}">[${log.level}]</span>
      <span style="color: var(--accent-purple); font-weight: 500;">[${log.tag}]</span>
      <span style="color: #cbd5e1;">${escapeHtml(log.message)}</span>
    `;
    logsContainer.appendChild(row);
    logsContainer.scrollTop = logsContainer.scrollHeight;
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  if (copyReachabilityBtn && reachabilityEl) {
    copyReachabilityBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(reachabilityEl.innerText);
      events.emit('toast:show', { message: 'Reachability URL copied to clipboard!', type: 'success' });
    });
  }

  if (clearLogsBtn) {
    clearLogsBtn.addEventListener('click', async () => {
      await api.clearDevLogs();
      logsContainer.innerHTML = '';
    });
  }

  if (loadModelBtn) {
    loadModelBtn.addEventListener('click', () => {
      events.emit('navigate', '/models');
    });
  }

  loadStatus();
  loadLogs();
}
