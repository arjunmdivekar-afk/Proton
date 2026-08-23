/**
 * Proton Web UI - Autonomous Agent View Controller
 */

import { api } from '../api.js';
import { state, events } from '../state.js';

export function initAgentView() {
  const goalInput = document.getElementById('agent-goal-input');
  const runBtn = document.getElementById('agent-run-btn');
  const planContainer = document.getElementById('agent-plan-tree');
  const traceContainer = document.getElementById('agent-trace-log');

  async function handleRunGoal() {
    const goal = goalInput.value.trim();
    if (!goal) return;

    if (planContainer) {
      planContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--accent-cyan);"><span class="status-dot busy"></span> Decomposing autonomous goal into plan tree...</div>';
    }
    if (traceContainer) {
      traceContainer.innerHTML = '<div style="padding: 12px; color: var(--text-muted); font-size: 13px;">Agent execution started.</div>';
    }

    try {
      const planRes = await api.getAgentPlan(goal);
      if (planContainer && planRes.subtasks) {
        planContainer.innerHTML = '';
        planRes.subtasks.forEach((task, idx) => {
          const item = document.createElement('div');
          item.className = 'card';
          item.style.marginBottom = '10px';
          item.innerHTML = `
            <div class="card-header" style="margin-bottom: 4px;">
              <span class="card-title" style="font-size: 13.5px;">Step ${idx + 1}: ${task.title || task}</span>
              <span class="badge badge-emerald">Ready</span>
            </div>
            <p style="font-size: 12.5px; color: var(--text-secondary);">${task.description || ''}</p>
          `;
          planContainer.appendChild(item);
        });
      }

      const runRes = await api.runAgentGoal(goal);
      if (traceContainer) {
        const traceEl = document.createElement('div');
        traceEl.className = 'card';
        traceEl.style.marginTop = '12px';
        traceEl.innerHTML = `
          <div class="card-header"><span class="card-title">Execution Summary</span><span class="badge badge-cyan">${runRes.status || 'Complete'}</span></div>
          <pre style="background: #08090d; padding: 12px; border-radius: var(--radius-md); font-size: 12px; overflow-x: auto;"><code>${JSON.stringify(runRes, null, 2)}</code></pre>
        `;
        traceContainer.appendChild(traceEl);
      }
      events.emit('toast:show', { message: 'Agent goal completed!', type: 'success' });
    } catch (err) {
      if (traceContainer) {
        traceContainer.innerHTML = `<div style="color: var(--accent-rose); padding: 14px;">Agent Error: ${err.message}</div>`;
      }
    }
  }

  if (runBtn) runBtn.addEventListener('click', handleRunGoal);
}
