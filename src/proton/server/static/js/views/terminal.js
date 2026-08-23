/**
 * Proton Web UI - Interactive Terminal View Controller
 */

import { api } from '../api.js';
import { state, events } from '../state.js';

export function initTerminalView() {
  const consoleEl = document.getElementById('terminal-console');
  const inputEl = document.getElementById('terminal-input-field');
  const statusChip = document.getElementById('terminal-process-status');
  const stopBtn = document.getElementById('terminal-stop-btn');
  const clearBtn = document.getElementById('terminal-clear-btn');
  const pwdEl = document.getElementById('terminal-pwd');

  let history = [];
  let historyIdx = -1;
  let currentCwd = '.';

  function appendOutput(text, type = 'stdout') {
    if (!consoleEl) return;
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    if (type === 'command') {
      line.innerHTML = `<span style="color: var(--accent-cyan); font-weight: bold;">$ </span>${escapeHtml(text)}`;
    } else if (type === 'error') {
      line.style.color = 'var(--accent-rose)';
      line.innerText = text;
    } else {
      line.innerText = text;
    }
    consoleEl.appendChild(line);
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  async function executeCommand(cmd) {
    if (!cmd.trim()) return;

    // Handle client-side 'clear'
    if (cmd.trim() === 'clear' || cmd.trim() === 'cls') {
      consoleEl.innerHTML = '';
      return;
    }

    history.push(cmd);
    historyIdx = history.length;
    appendOutput(cmd, 'command');

    if (statusChip) statusChip.innerHTML = '<span class="status-dot busy"></span> Running...';
    if (stopBtn) stopBtn.style.display = 'inline-flex';

    try {
      const res = await api.runTerminalCommand(cmd, currentCwd);
      if (res.cwd) {
        currentCwd = res.cwd;
        if (pwdEl) pwdEl.innerText = res.cwd;
      }
      if (res.stdout) appendOutput(res.stdout, 'stdout');
      if (res.stderr) appendOutput(res.stderr, 'error');
      if (res.exit_code !== 0 && !res.stderr) {
        appendOutput(`[Process exited with code ${res.exit_code}]`, 'error');
      }
    } catch (err) {
      appendOutput(`Execution Error: ${err.message}`, 'error');
    } finally {
      if (statusChip) statusChip.innerHTML = '<span class="status-dot online"></span> Ready';
      if (stopBtn) stopBtn.style.display = 'none';
    }
  }

  if (inputEl) {
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const cmd = inputEl.value;
        inputEl.value = '';
        executeCommand(cmd);
      } else if (e.key === 'ArrowUp') {
        if (history.length > 0 && historyIdx > 0) {
          historyIdx--;
          inputEl.value = history[historyIdx] || '';
        }
      } else if (e.key === 'ArrowDown') {
        if (historyIdx < history.length - 1) {
          historyIdx++;
          inputEl.value = history[historyIdx] || '';
        } else {
          historyIdx = history.length;
          inputEl.value = '';
        }
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener('click', async () => {
      await api.stopTerminalProcess();
      appendOutput('[Terminated by user]', 'error');
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      consoleEl.innerHTML = '';
    });
  }

  // Welcome line
  if (consoleEl && consoleEl.children.length === 0) {
    appendOutput('Proton Terminal Shell v2.6.4 [Windows/PowerShell ready]', 'stdout');
    appendOutput('Type any command (e.g. `dir`, `git status`, `python --version`) and press ENTER.', 'stdout');
  }
}
