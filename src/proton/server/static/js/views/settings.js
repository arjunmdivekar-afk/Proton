/**
 * Proton Web UI - Enterprise Settings Page Controller
 */

import { state, saveSettings, events } from '../state.js';
import { api } from '../api.js';

export function initSettingsView() {
  const navItems = document.querySelectorAll('.settings-nav-item');
  const sections = document.querySelectorAll('.settings-section');

  // Input bindings
  const tempInput = document.getElementById('settings-temperature');
  const tempVal = document.getElementById('settings-temp-val');
  const topPInput = document.getElementById('settings-top-p');
  const topPVal = document.getElementById('settings-top-p-val');
  const maxTokInput = document.getElementById('settings-max-tokens');
  const systemPromptInput = document.getElementById('settings-system-prompt');
  const themeSelect = document.getElementById('settings-theme');
  const saveBtn = document.getElementById('settings-save-btn');

  // Providers Table
  const providersTbody = document.getElementById('settings-providers-tbody');
  const refreshProvidersBtn = document.getElementById('settings-refresh-providers');

  async function loadProviders() {
    if (!providersTbody) return;
    providersTbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:16px;">Testing and measuring latency for configured providers...</td></tr>';
    try {
      const data = await api.getConnections();
      providersTbody.innerHTML = '';
      const conns = data.connections || [];

      if (conns.length === 0) {
        providersTbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:16px;">No connections configured.</td></tr>';
        return;
      }

      conns.forEach(conn => {
        const tr = document.createElement('tr');
        const isOnline = conn.status === 'connected';
        const isActive = conn.is_active;
        const latencyText = conn.latency_ms !== null && conn.latency_ms !== undefined ? `${conn.latency_ms} ms` : '—';
        const latencyBadge = isOnline ? `<span class="badge badge-emerald">${latencyText}</span>` : `<span class="badge badge-rose">Offline</span>`;

        const isBuiltin = conn.id === 'proton-hub';
        const deleteBtnHtml = isBuiltin ? '' : `<button class="btn btn-ghost btn-sm btn-delete" title="Delete Connection" style="color:var(--text-dim);">✕</button>`;

        tr.innerHTML = `
          <td><span class="status-dot ${isOnline ? 'online' : ''}"></span></td>
          <td>
            <div style="font-weight:500; color:var(--text-primary);">${conn.name}</div>
            <div style="font-size:11px; color:var(--text-dim);">${conn.provider}</div>
          </td>
          <td><span style="font-family:var(--font-mono); font-size:12px; color:var(--text-secondary);">${conn.base_url}</span></td>
          <td>${latencyBadge}</td>
          <td>
            <div style="display:flex; gap:6px; align-items:center;">
              <button class="btn btn-secondary btn-sm btn-ping" title="Ping Endpoint">Ping</button>
              <button class="btn ${isActive ? 'btn-primary' : 'btn-secondary'} btn-sm btn-activate" ${isActive ? 'disabled' : ''}>
                ${isActive ? 'Active' : 'Set Active'}
              </button>
              ${deleteBtnHtml}
            </div>
          </td>
        `;

        const delBtn = tr.querySelector('.btn-delete');
        if (delBtn) {
          delBtn.addEventListener('click', async () => {
            if (confirm(`Remove connection profile "${conn.name}"?`)) {
              try {
                await api.deleteConnection(conn.id);
                events.emit('toast:show', { message: `Removed connection "${conn.name}"`, type: 'info' });
                loadProviders();
              } catch (e) {
                events.emit('toast:show', { message: `Delete failed: ${e.message}`, type: 'error' });
              }
            }
          });
        }

        tr.querySelector('.btn-ping').addEventListener('click', async (e) => {
          const btn = e.target;
          btn.disabled = true;
          btn.innerText = '...';
          try {
            const res = await api.testConnection(conn.id);
            if (res.success) {
              events.emit('toast:show', { message: `${conn.name} reachable! Latency: ${res.latency_ms} ms`, type: 'success' });
            } else {
              events.emit('toast:show', { message: `${conn.name} failed: ${res.error || 'unreachable'}`, type: 'error' });
            }
            loadProviders();
          } catch (err) {
            events.emit('toast:show', { message: `Ping error: ${err.message}`, type: 'error' });
          } finally {
            btn.disabled = false;
            btn.innerText = 'Ping';
          }
        });

        tr.querySelector('.btn-activate').addEventListener('click', async () => {
          try {
            await api.setActiveConnection(conn.id);
            state.activeConnection = conn.id;
            events.emit('toast:show', { message: `Switched active provider to ${conn.name}`, type: 'success' });
            loadProviders();
          } catch (err) {
            events.emit('toast:show', { message: `Failed to switch: ${err.message}`, type: 'error' });
          }
        });

        providersTbody.appendChild(tr);
      });
    } catch (err) {
      providersTbody.innerHTML = `<tr><td colspan="5" style="color:var(--accent-rose); padding:16px;">Failed to load providers: ${err.message}</td></tr>`;
    }
  }

  // Add Provider Modal
  const addModal = document.getElementById('add-provider-modal');
  const openModalBtn = document.getElementById('settings-add-provider-btn');
  const closeModalBtn = document.getElementById('close-add-provider-modal');
  const cancelModalBtn = document.getElementById('cancel-add-provider-btn');
  const saveModalBtn = document.getElementById('save-add-provider-btn');

  const provTypeSel = document.getElementById('new-provider-type');
  const provNameInput = document.getElementById('new-provider-name');
  const provUrlInput = document.getElementById('new-provider-url');
  const provKeyInput = document.getElementById('new-provider-key');

  if (provTypeSel && provUrlInput) {
    provTypeSel.addEventListener('change', () => {
      const val = provTypeSel.value;
      if (val === 'lmstudio') provUrlInput.value = 'http://127.0.0.1:1234/v1';
      else if (val === 'ollama') provUrlInput.value = 'http://127.0.0.1:11434/v1';
      else if (val === 'openai') provUrlInput.value = 'https://api.openai.com/v1';
      else if (val === 'anthropic') provUrlInput.value = 'https://api.anthropic.com/v1';
      else if (val === 'gemini') provUrlInput.value = 'https://generativelanguage.googleapis.com/v1';
    });
  }

  function openAddModal() {
    if (addModal) addModal.classList.add('active');
  }

  function closeAddModal() {
    if (addModal) addModal.classList.remove('active');
  }

  if (openModalBtn) openModalBtn.addEventListener('click', openAddModal);
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeAddModal);
  if (cancelModalBtn) cancelModalBtn.addEventListener('click', closeAddModal);

  if (saveModalBtn) {
    saveModalBtn.addEventListener('click', async () => {
      const name = (provNameInput && provNameInput.value.trim()) || 'Custom Inference';
      const provider = provTypeSel ? provTypeSel.value : 'lmstudio';
      const base_url = (provUrlInput && provUrlInput.value.trim()) || 'http://127.0.0.1:1234/v1';
      const api_key = (provKeyInput && provKeyInput.value.trim()) || null;

      saveModalBtn.disabled = true;
      saveModalBtn.innerText = 'Connecting...';

      try {
        await api.addConnection({ name, provider, base_url, api_key });
        events.emit('toast:show', { message: `Added "${name}" successfully!`, type: 'success' });
        closeAddModal();
        if (provNameInput) provNameInput.value = '';
        if (provKeyInput) provKeyInput.value = '';
        loadProviders();
      } catch (err) {
        events.emit('toast:show', { message: `Failed to add connection: ${err.message}`, type: 'error' });
      } finally {
        saveModalBtn.disabled = false;
        saveModalBtn.innerText = 'Save & Connect';
      }
    });
  }

  if (refreshProvidersBtn) {
    refreshProvidersBtn.addEventListener('click', loadProviders);
  }

  loadProviders();

  // Section Tab Switcher
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const targetSec = item.getAttribute('data-section');
      sections.forEach(s => {
        s.style.display = s.id === `section-${targetSec}` ? 'block' : 'none';
      });
    });
  });

  // Sliders real-time feedback
  if (tempInput && tempVal) {
    tempInput.value = state.settings.temperature;
    tempVal.innerText = state.settings.temperature;
    tempInput.addEventListener('input', (e) => { tempVal.innerText = e.target.value; });
  }

  if (topPInput && topPVal) {
    topPInput.value = state.settings.top_p;
    topPVal.innerText = state.settings.top_p;
    topPInput.addEventListener('input', (e) => { topPVal.innerText = e.target.value; });
  }

  if (maxTokInput) maxTokInput.value = state.settings.max_tokens;
  if (systemPromptInput) systemPromptInput.value = state.settings.system_prompt;
  if (themeSelect) themeSelect.value = state.settings.theme;

  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      saveSettings({
        temperature: parseFloat(tempInput ? tempInput.value : 0.7),
        top_p: parseFloat(topPInput ? topPInput.value : 0.9),
        max_tokens: parseInt(maxTokInput ? maxTokInput.value : 2048, 10),
        system_prompt: systemPromptInput ? systemPromptInput.value : '',
        theme: themeSelect ? themeSelect.value : 'dark-sleek',
      });
      events.emit('toast:show', { message: 'Settings saved successfully!', type: 'success' });
    });
  }
}
