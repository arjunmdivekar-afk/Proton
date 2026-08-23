/**
 * Proton Web UI - Model Hub & Connection Switcher Controller
 */

import { api } from '../api.js';
import { state, events } from '../state.js';

export function initModelsView() {
  const searchInput = document.getElementById('hub-search-input');
  const modelsGrid = document.getElementById('hub-models-grid');
  const connectionsTable = document.getElementById('connections-table-body');
  const cpuRadio = document.getElementById('device-mode-cpu');
  const gpuRadio = document.getElementById('device-mode-gpu');
  const partialRadio = document.getElementById('device-mode-partial');

  async function loadHubModels(query = '') {
    if (!modelsGrid) return;
    modelsGrid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Searching Proton Model Hub catalog...</div>';
    try {
      const data = await api.searchHubModels(query);
      modelsGrid.innerHTML = '';
      if (!data.models || data.models.length === 0) {
        modelsGrid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No models found.</div>';
        return;
      }

      data.models.forEach(m => {
        const card = document.createElement('div');
        card.className = 'model-card';
        card.innerHTML = `
          <div class="card-header" style="margin-bottom: 0;">
            <strong style="color: var(--text-primary); font-size: 14px; overflow:hidden; text-overflow:ellipsis;">${m.id}</strong>
            <span class="badge badge-cyan">${m.parameters || 'Auto'}</span>
          </div>
          <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">${m.description || 'Hugging Face Transformers architecture'}</p>
          <div style="display: flex; gap: 12px; font-size: 11.5px; color: var(--text-muted);">
            <span>💾 ${m.size_display || 'Auto'}</span>
            <span>⬇️ ${m.downloads_display || '10k+'}</span>
            <span>⚖️ ${m.license || 'Apache-2.0'}</span>
          </div>
          <div style="margin-top: 6px; display: flex; gap: 8px;">
            <button class="btn btn-primary btn-sm" style="flex: 1;">Install / Set Default</button>
          </div>
        `;

        card.querySelector('button').addEventListener('click', async () => {
          events.emit('toast:show', { message: `Switching active model to ${m.id}...`, type: 'info' });
          await api.setActiveModel(m.id);
          events.emit('toast:show', { message: `Active model set to ${m.id}!`, type: 'success' });
          loadConnections();
        });

        modelsGrid.appendChild(card);
      });
    } catch (err) {
      modelsGrid.innerHTML = `<div style="color: var(--accent-rose); padding: 20px;">Error: ${err.message}</div>`;
    }
  }

  async function loadConnections() {
    if (!connectionsTable) return;
    try {
      const data = await api.getConnections();
      connectionsTable.innerHTML = '';
      if (!data.connections) return;

      data.connections.forEach(conn => {
        const tr = document.createElement('tr');
        const isOnline = conn.status === 'connected';
        tr.innerHTML = `
          <td><span class="status-dot ${isOnline ? 'online' : 'offline'}"></span> ${conn.status}</td>
          <td><strong>${conn.name}</strong> <span style="color: var(--text-dim);">(${conn.id})</span></td>
          <td><span class="badge badge-purple">${conn.provider}</span></td>
          <td><span style="font-family: var(--font-mono); font-size: 12px;">${conn.base_url || conn.endpoint}</span></td>
          <td>${conn.discovered_models ? conn.discovered_models.length : 0}</td>
          <td>${conn.latency_ms ? `${conn.latency_ms.toFixed(1)} ms` : (conn.provider === 'proton-hub' ? '0.1 ms' : '-')}</td>
          <td>
            <button class="btn btn-secondary btn-sm" ${conn.id === state.activeConnection ? 'disabled' : ''}>
              ${conn.id === state.activeConnection ? '★ Active' : 'Activate'}
            </button>
          </td>
        `;

        tr.querySelector('button').addEventListener('click', async () => {
          await api.setActiveConnection(conn.id);
          state.activeConnection = conn.id;
          events.emit('toast:show', { message: `Switched connection to ${conn.name}`, type: 'success' });
          loadConnections();
        });

        connectionsTable.appendChild(tr);
      });
    } catch (err) {
      console.error('Error loading connections:', err);
    }
  }

  // Device mode switches
  function setMode(mode) {
    api.setDeviceMode(mode);
    events.emit('toast:show', { message: `Hardware acceleration set to ${mode.toUpperCase()} mode`, type: 'success' });
  }

  if (cpuRadio) cpuRadio.addEventListener('change', () => setMode('cpu'));
  if (gpuRadio) gpuRadio.addEventListener('change', () => setMode('gpu'));
  if (partialRadio) partialRadio.addEventListener('change', () => setMode('partial'));

  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') loadHubModels(searchInput.value);
    });
  }

  loadHubModels('');
  loadConnections();
}
