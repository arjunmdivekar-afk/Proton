/**
 * Proton Web UI - Categorized Memory Explorer Controller
 */

import { api } from '../api.js';
import { events } from '../state.js';

export function initMemoryView() {
  const memoryList = document.getElementById('memory-cards-grid');
  const addMemoryBtn = document.getElementById('add-memory-btn');
  const categoryFilters = document.querySelectorAll('.memory-filter-btn');

  let activeCategory = 'all';

  async function loadMemories() {
    if (!memoryList) return;
    memoryList.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Loading memory store...</div>';

    try {
      const data = await api.getMemories(activeCategory === 'all' ? null : activeCategory);
      memoryList.innerHTML = '';
      const memories = data.memories || [];

      if (memories.length === 0) {
        memoryList.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No memory entries stored in this category.</div>';
        return;
      }

      memories.forEach(mem => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div class="card-header" style="margin-bottom: 6px;">
            <span class="badge badge-purple">${mem.category || 'Fact'}</span>
            <button class="btn-ghost btn-sm" style="padding: 2px 6px;">✕</button>
          </div>
          <p style="font-size: 13px; color: var(--text-primary); line-height: 1.5;">${mem.content}</p>
          <span style="font-size: 11px; color: var(--text-dim); margin-top: 6px;">${mem.created_at || 'Saved in long-term memory'}</span>
        `;

        card.querySelector('button').addEventListener('click', async () => {
          if (confirm('Delete this memory item?')) {
            await api.deleteMemory(mem.id);
            events.emit('toast:show', { message: 'Memory deleted', type: 'info' });
            loadMemories();
          }
        });

        memoryList.appendChild(card);
      });
    } catch (err) {
      memoryList.innerHTML = `<div style="color: var(--accent-rose); padding: 20px;">Error: ${err.message}</div>`;
    }
  }

  categoryFilters.forEach(btn => {
    btn.addEventListener('click', () => {
      categoryFilters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCategory = btn.getAttribute('data-category') || 'all';
      loadMemories();
    });
  });

  if (addMemoryBtn) {
    addMemoryBtn.addEventListener('click', async () => {
      const content = prompt('Enter fact or rule to persist into Proton Long-Term Memory:');
      if (!content) return;
      const cat = prompt('Enter category (project_facts / preferences / rules / context):', 'project_facts') || 'project_facts';
      try {
        await api.addMemory(content, cat);
        events.emit('toast:show', { message: 'Memory stored!', type: 'success' });
        loadMemories();
      } catch (err) {
        events.emit('toast:show', { message: `Failed to store memory: ${err.message}`, type: 'error' });
      }
    });
  }

  loadMemories();
}
