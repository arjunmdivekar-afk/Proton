/**
 * Proton Web UI - Tasks Kanban Controller
 */

import { api } from '../api.js';
import { events } from '../state.js';

export function initTasksView() {
  const columns = {
    backlog: document.getElementById('kanban-col-backlog'),
    todo: document.getElementById('kanban-col-todo'),
    in_progress: document.getElementById('kanban-col-in_progress'),
    review: document.getElementById('kanban-col-review'),
    done: document.getElementById('kanban-col-done'),
  };
  const addTaskBtn = document.getElementById('add-task-btn');

  async function loadTasks() {
    try {
      const data = await api.getTasks();
      // Clear columns
      Object.values(columns).forEach(col => { if (col) col.innerHTML = ''; });

      const tasks = data.tasks || [
        { id: '1', title: 'Implement Web UI layout', description: 'Create responsive glassmorphic UI components', priority: 'high', status: 'in_progress' },
        { id: '2', title: 'Test Model Hub GGUF streaming', description: 'Verify token streaming with local Llama 3.2', priority: 'critical', status: 'done' },
        { id: '3', title: 'Add LAN WiFi server sharing', description: 'Show reachable IP address in header and developer dashboard', priority: 'high', status: 'done' },
      ];

      tasks.forEach(renderTaskCard);
    } catch (err) {
      console.error('Error loading tasks:', err);
    }
  }

  function renderTaskCard(task) {
    const colKey = task.status || 'todo';
    const container = columns[colKey] || columns.todo;
    if (!container) return;

    const card = document.createElement('div');
    card.className = 'task-card';
    const badgeColor = task.priority === 'critical' ? 'badge-rose' : (task.priority === 'high' ? 'badge-amber' : 'badge-cyan');

    card.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span class="badge ${badgeColor}">${task.priority || 'Normal'}</span>
        <span style="font-size: 11px; color: var(--text-dim);">#${task.id}</span>
      </div>
      <strong style="color: var(--text-primary); font-size: 13.5px;">${task.title}</strong>
      <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">${task.description || ''}</p>
      <div style="margin-top: 6px; display: flex; gap: 6px;">
        <button class="btn btn-secondary btn-sm" style="flex: 1; padding: 3px 6px;" title="Delegate to Autonomous Agent">🤖 Run with Agent</button>
      </div>
    `;

    card.querySelector('button').addEventListener('click', () => {
      events.emit('toast:show', { message: `Delegating "${task.title}" to Autonomous Agent...`, type: 'info' });
      events.emit('navigate', '/agent');
    });

    container.appendChild(card);
  }

  if (addTaskBtn) {
    addTaskBtn.addEventListener('click', async () => {
      const title = prompt('Enter new task title:');
      if (!title) return;
      const desc = prompt('Enter task description:') || '';
      try {
        await api.createTask(title, desc);
        events.emit('toast:show', { message: 'Task created!', type: 'success' });
        loadTasks();
      } catch (err) {
        events.emit('toast:show', { message: `Failed to create task: ${err.message}`, type: 'error' });
      }
    });
  }

  loadTasks();
}
