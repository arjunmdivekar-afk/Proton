/**
 * Proton Web UI - Files & Workspace Explorer Controller
 */

import { api } from '../api.js';
import { state, events } from '../state.js';

export function initWorkspaceView() {
  const treeContainer = document.getElementById('workspace-file-tree');
  const editor = document.getElementById('workspace-editor-area');
  const filePathEl = document.getElementById('active-file-path');
  const saveBtn = document.getElementById('workspace-save-btn');
  const diffBtn = document.getElementById('workspace-diff-btn');
  const searchInput = document.getElementById('workspace-search-input');
  const searchResults = document.getElementById('workspace-search-results');
  const changesTab = document.getElementById('workspace-changes-list');

  let currentFilePath = '';
  let originalContent = '';

  async function loadTree() {
    if (!treeContainer) return;
    try {
      const data = await api.getWorkspaceTree();
      treeContainer.innerHTML = '';
      if (data.tree) {
        renderTreeNode(data.tree, treeContainer);
      }
    } catch (err) {
      treeContainer.innerHTML = `<div style="color: var(--accent-rose); padding: 8px;">Error loading tree: ${err.message}</div>`;
    }
  }

  function renderTreeNode(node, container) {
    const el = document.createElement('div');
    const isDir = node.is_dir;
    el.className = 'tree-node';
    el.innerHTML = `
      <span style="font-size: 14px;">${isDir ? '📁' : getFileIcon(node.name)}</span>
      <span style="flex: 1; overflow: hidden; text-overflow: ellipsis;">${node.name}</span>
      ${!isDir && node.size ? `<span style="color: var(--text-dim); font-size: 11px;">${(node.size / 1024).toFixed(1)}K</span>` : ''}
    `;

    if (isDir) {
      const childrenContainer = document.createElement('div');
      childrenContainer.style.paddingLeft = '14px';
      childrenContainer.style.display = 'none';

      el.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = childrenContainer.style.display === 'block';
        childrenContainer.style.display = isOpen ? 'none' : 'block';
        el.querySelector('span').innerText = isOpen ? '📁' : '📂';
      });

      container.appendChild(el);
      container.appendChild(childrenContainer);

      if (node.children) {
        node.children.forEach(child => renderTreeNode(child, childrenContainer));
      }
    } else {
      el.addEventListener('click', () => openFile(node.path));
      container.appendChild(el);
    }
  }

  function getFileIcon(name) {
    if (name.endsWith('.py')) return '🐍';
    if (name.endsWith('.js') || name.endsWith('.ts')) return '📜';
    if (name.endsWith('.html')) return '🌐';
    if (name.endsWith('.css')) return '🎨';
    if (name.endsWith('.json') || name.endsWith('.yaml') || name.endsWith('.toml')) return '⚙️';
    if (name.endsWith('.md')) return '📝';
    return '📄';
  }

  async function openFile(path) {
    if (!path) return;
    try {
      const data = await api.readWorkspaceFile(path);
      currentFilePath = path;
      originalContent = data.content;
      if (filePathEl) filePathEl.innerText = path;
      if (editor) {
        editor.value = data.content;
        editor.readOnly = false;
      }
      document.querySelectorAll('.tree-node').forEach(n => n.classList.remove('selected'));
    } catch (err) {
      events.emit('toast:show', { message: `Error opening ${path}: ${err.message}`, type: 'error' });
    }
  }

  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      if (!currentFilePath) return;
      try {
        await api.writeWorkspaceFile(currentFilePath, editor.value);
        originalContent = editor.value;
        events.emit('toast:show', { message: `Saved ${currentFilePath}`, type: 'success' });
        loadTree();
        loadAgentChanges();
      } catch (err) {
        events.emit('toast:show', { message: `Save failed: ${err.message}`, type: 'error' });
      }
    });
  }

  if (diffBtn) {
    diffBtn.addEventListener('click', async () => {
      if (!currentFilePath) return;
      try {
        const data = await api.getFileDiff(currentFilePath, editor.value);
        if (!data.has_changes) {
          events.emit('toast:show', { message: 'No changes detected in file.', type: 'info' });
          return;
        }
        alert(`=== Unified Diff for ${currentFilePath} ===\n\n${data.diff_text}`);
      } catch (err) {
        events.emit('toast:show', { message: `Diff error: ${err.message}`, type: 'error' });
      }
    });
  }

  // Workspace Search
  if (searchInput) {
    searchInput.addEventListener('input', async () => {
      const q = searchInput.value.trim();
      if (!q || q.length < 2) {
        if (searchResults) searchResults.innerHTML = '';
        return;
      }
      try {
        const data = await api.searchWorkspace(q);
        if (!searchResults) return;
        searchResults.innerHTML = '';
        data.results.forEach(res => {
          const item = document.createElement('div');
          item.className = 'session-item';
          item.innerHTML = `<div><strong style="color: var(--accent-cyan);">${res.file}:${res.line_number}</strong><br/><span style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(res.line_content)}</span></div>`;
          item.addEventListener('click', () => openFile(res.file));
          searchResults.appendChild(item);
        });
      } catch (e) {}
    });
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  async function loadAgentChanges() {
    if (!changesTab) return;
    try {
      const data = await api.getAgentChanges();
      changesTab.innerHTML = '';
      if (!data.changes || data.changes.length === 0) {
        changesTab.innerHTML = '<div style="padding: 10px; color: var(--text-muted); font-size: 12px;">No session changes yet.</div>';
        return;
      }
      data.changes.forEach(c => {
        const el = document.createElement('div');
        el.className = 'session-item';
        el.innerHTML = `<span><strong>${c.action.toUpperCase()}</strong>: ${c.path}</span>`;
        el.addEventListener('click', () => openFile(c.path));
        changesTab.appendChild(el);
      });
    } catch (e) {}
  }

  loadTree();
  loadAgentChanges();
}
