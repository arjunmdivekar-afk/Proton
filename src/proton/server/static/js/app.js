/**
 * Proton Web UI - Main Application Bootstrapper
 */

import { router } from './router.js';
import { state, events, loadPersistedState } from './state.js';
import { api } from './api.js';
import { initCommandPalette } from './palette.js';

// Views
import { initChatView } from './views/chat.js';
import { initAgentView } from './views/agent.js';
import { initTerminalView } from './views/terminal.js';
import { initWorkspaceView } from './views/workspace.js';
import { initDeveloperView } from './views/developer.js';
import { initModelsView } from './views/models.js';
import { initGraphView } from './views/graphrag.js';
import { initTasksView } from './views/tasks.js';
import { initMemoryView } from './views/memory.js';
import { initSecurityView } from './views/security.js';
import { initSettingsView } from './views/settings.js';
import { initDiagnosticsView } from './views/diagnostics.js';

function bootstrap() {
  loadPersistedState();

  // Initialize Router mapping
  router.addRoute('/', () => router.navigate('/chat', true));
  router.addRoute('/chat', (params) => {});
  router.addRoute('/chat/:id', (params) => {});
  router.addRoute('/agent', (params) => {});
  router.addRoute('/agent/:id', (params) => {});
  router.addRoute('/terminal', (params) => {});
  router.addRoute('/workspace', (params) => {});
  router.addRoute('/developer', (params) => {});
  router.addRoute('/models', (params) => {});
  router.addRoute('/graphrag', (params) => {});
  router.addRoute('/tasks', (params) => {});
  router.addRoute('/tasks/:id', (params) => {});
  router.addRoute('/memory', (params) => {});
  router.addRoute('/security', (params) => {});
  router.addRoute('/diagnostics', (params) => {});
  router.addRoute('/settings', (params) => {});

  // Initialize feature views
  try { initChatView(); } catch (e) { console.error("Error initializing Chat:", e); }
  try { initAgentView(); } catch (e) { console.error("Error initializing Agent:", e); }
  try { initTerminalView(); } catch (e) { console.error("Error initializing Terminal:", e); }
  try { initWorkspaceView(); } catch (e) { console.error("Error initializing Workspace:", e); }
  try { initDeveloperView(); } catch (e) { console.error("Error initializing Developer:", e); }
  try { initModelsView(); } catch (e) { console.error("Error initializing Models:", e); }
  try { initGraphView(); } catch (e) { console.error("Error initializing Graph:", e); }
  try { initTasksView(); } catch (e) { console.error("Error initializing Tasks:", e); }
  try { initMemoryView(); } catch (e) { console.error("Error initializing Memory:", e); }
  try { initSecurityView(); } catch (e) { console.error("Error initializing Security:", e); }
  try { initSettingsView(); } catch (e) { console.error("Error initializing Settings:", e); }
  try { initDiagnosticsView(); } catch (e) { console.error("Error initializing Diagnostics:", e); }

  // Initialize Command Palette (Ctrl + K)
  try { initCommandPalette(); } catch (e) { console.error("Error initializing Palette:", e); }

  // Setup Navigation Clicks
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const route = el.getAttribute('data-route') || '/chat';
      router.navigate(route);
    });
  });

  // Sidebar collapse toggle
  const sidebar = document.getElementById('app-sidebar');
  const collapseBtn = document.getElementById('sidebar-toggle-btn');
  if (collapseBtn && sidebar) {
    collapseBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
    });
  }

  // Toast listener
  events.on('toast:show', ({ message, type = 'info' }) => {
    showToast(message, type);
  });

  events.on('navigate', (route) => {
    router.navigate(route);
  });

  // Live telemetry polling in header
  async function pollTelemetry() {
    try {
      const data = await api.getHealth();
      if (data.system) {
        const cpuEl = document.getElementById('header-cpu-val');
        const ramEl = document.getElementById('header-ram-val');
        if (cpuEl) cpuEl.innerText = `${data.system.cpu_percent || 12}%`;
        if (ramEl) ramEl.innerText = `${data.system.ram_percent || 45}%`;
      }
    } catch (e) {}
  }

  setInterval(pollTelemetry, 5000);
  pollTelemetry();

  // Resolve initial route
  router.resolve();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootstrap);
} else {
  bootstrap();
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ')}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 200);
  }, 3500);
}
