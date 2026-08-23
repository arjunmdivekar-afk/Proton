/**
 * Proton Web UI - Global Ctrl+K Command Palette
 */

import { router } from './router.js';
import { api } from './api.js';
import { events } from './state.js';

export function initCommandPalette() {
  const overlay = document.getElementById('palette-overlay');
  const input = document.getElementById('palette-input');
  const resultsList = document.getElementById('palette-results');
  if (!overlay || !input || !resultsList) return;

  const commands = [
    { id: 'chat', title: 'Chat', category: 'Navigation', action: () => router.navigate('/chat') },
    { id: 'agent', title: 'New Agent Goal', category: 'Action', action: () => router.navigate('/agent') },
    { id: 'terminal', title: 'Open Terminal', category: 'Developer', action: () => router.navigate('/terminal') },
    { id: 'workspace', title: 'Workspace Explorer & Diff', category: 'Workspace', action: () => router.navigate('/workspace') },
    { id: 'developer', title: 'Developer Dashboard', category: 'Developer', action: () => router.navigate('/developer') },
    { id: 'models', title: 'Models & Hub', category: 'Model Hub', action: () => router.navigate('/models') },
    { id: 'graphrag', title: 'GraphRAG Code Intelligence', category: 'Intelligence', action: () => router.navigate('/graphrag') },
    { id: 'tasks', title: 'Tasks Kanban', category: 'Tasks', action: () => router.navigate('/tasks') },
    { id: 'memory', title: 'Memory Store', category: 'Memory', action: () => router.navigate('/memory') },
    { id: 'index', title: 'Index Project Codebase', category: 'Action', action: async () => {
      await api.indexGraph();
      events.emit('toast:show', { message: 'Workspace indexing started!', type: 'success' });
      router.navigate('/graphrag');
    }},
    { id: 'docs', title: 'API Documentation', category: 'API', action: () => window.open('/docs', '_blank') },
    { id: 'doctor', title: 'Proton Doctor Diagnostics', category: 'Diagnostics', action: () => router.navigate('/diagnostics') },
    { id: 'settings', title: 'Settings', category: 'Configuration', action: () => router.navigate('/settings') },
  ];

  let selectedIndex = 0;
  let filteredCommands = [...commands];

  function openPalette() {
    overlay.classList.add('active');
    input.value = '';
    filterCommands('');
    setTimeout(() => input.focus(), 50);
  }

  function closePalette() {
    overlay.classList.remove('active');
  }

  function filterCommands(query) {
    const q = query.toLowerCase().trim();
    filteredCommands = commands.filter(c => c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q));
    selectedIndex = 0;
    renderResults();
  }

  function renderResults() {
    resultsList.innerHTML = '';
    if (filteredCommands.length === 0) {
      resultsList.innerHTML = '<div style="padding: 12px; text-align: center; color: var(--text-muted); font-size: 12px;">No commands found.</div>';
      return;
    }

    filteredCommands.forEach((cmd, idx) => {
      const item = document.createElement('div');
      item.className = `palette-item ${idx === selectedIndex ? 'selected' : ''}`;
      item.innerHTML = `
        <div class="palette-item-left">
          <span class="palette-item-title">${cmd.title}</span>
        </div>
        <span class="palette-item-category">${cmd.category}</span>
      `;
      item.addEventListener('click', () => {
        closePalette();
        cmd.action();
      });
      resultsList.appendChild(item);
    });
  }

  // Keyboard navigation & Shortcuts
  window.addEventListener('keydown', (e) => {
    // Open on Ctrl + K or Cmd + K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (overlay.classList.contains('active')) {
        closePalette();
      } else {
        openPalette();
      }
    }

    if (!overlay.classList.contains('active')) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      closePalette();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = (selectedIndex + 1) % filteredCommands.length;
      renderResults();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = (selectedIndex - 1 + filteredCommands.length) % filteredCommands.length;
      renderResults();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        closePalette();
        filteredCommands[selectedIndex].action();
      }
    }
  });

  input.addEventListener('input', (e) => filterCommands(e.target.value));
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closePalette();
  });

  // Header trigger button
  const triggerBtn = document.getElementById('palette-trigger-btn');
  if (triggerBtn) {
    triggerBtn.addEventListener('click', openPalette);
  }
}
