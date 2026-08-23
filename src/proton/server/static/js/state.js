/**
 * Proton Web UI - Centralized Reactive State & EventBus
 */

class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      for (const cb of this.listeners.get(event)) {
        try {
          cb(data);
        } catch (err) {
          console.error(`Error in event listener for '${event}':`, err);
        }
      }
    }
  }
}

export const events = new EventBus();

export const state = {
  // Global App State
  activeRoute: '/chat',
  activeConnection: 'proton-hub',
  activeModel: 'llama-3.2-1b-instruct',
  isStreaming: false,
  hardwareMode: 'auto',
  systemStatus: {
    status: 'running',
    version: '2.6.4',
    lan_url: 'http://127.0.0.1:8787',
    reachability: 'http://127.0.0.1:8787',
    active_connection: 'Proton Model Hub (Local Models)',
    active_model: 'Llama-3.2-1B-Instruct',
    hardware: { cpu_percent: 12, ram_percent: 45, total_ram_gb: 16 },
  },

  // Chat State
  sessions: [],
  currentSessionId: 'default',
  currentMessages: [],
  tokenSpeed: 0,
  contextUsage: { current: 0, max: 128000 },

  // Terminal State
  terminalHistory: [],
  isProcessRunning: false,
  activePid: null,

  // Workspace State
  workspaceTree: null,
  activeFile: null,
  activeFileContent: '',
  hasUnsavedChanges: false,

  // Tasks State
  tasks: [],

  // Memory State
  memories: [],

  // Settings State
  settings: {
    theme: 'dark-sleek',
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    system_prompt: 'You are Proton, an autonomous AI coding and system intelligence assistant.',
    strict_approval: true,
    device_mode: 'auto',
    streaming: true,
  },
};

// Persistence helper
export function loadPersistedState() {
  try {
    const saved = localStorage.getItem('proton_web_settings');
    if (saved) {
      Object.assign(state.settings, JSON.parse(saved));
    }
  } catch (e) {}
}

export function saveSettings(newSettings) {
  Object.assign(state.settings, newSettings);
  localStorage.setItem('proton_web_settings', JSON.stringify(state.settings));
  events.emit('settings:updated', state.settings);
}
