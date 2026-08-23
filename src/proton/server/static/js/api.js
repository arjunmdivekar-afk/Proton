/**
 * Proton Web UI - Unified REST & SSE API Client
 */

const BASE_URL = window.location.origin;

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const data = await res.json();
        if (data.detail) errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } catch (e) {}
      throw new Error(errorMsg);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${path}:`, err);
    throw err;
  }
}

export const api = {
  // System & Health
  getHealth: () => request('/v1/health'),
  getDoctor: () => request('/v1/doctor/run', { method: 'POST' }),

  // Developer Dashboard & Logs
  getDevStatus: () => request('/v1/developer/status'),
  getDevLogs: () => request('/v1/developer/logs'),
  clearDevLogs: () => request('/v1/developer/logs/clear', { method: 'POST' }),

  // Chat Streaming
  streamChat: async (messages, model, options = {}, onToken, onDone, onError) => {
    const url = `${BASE_URL}/v1/chat/completions`;
    const payload = {
      messages,
      model: model || undefined,
      stream: true,
      temperature: options.temperature ?? 0.7,
      max_tokens: options.max_tokens ?? 2048,
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Chat API error ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete chunk in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.substring(6).trim();
            if (dataStr === '[DONE]') {
              if (onDone) onDone();
              return;
            }
            try {
              const data = JSON.parse(dataStr);
              const delta = data.choices?.[0]?.delta?.content || data.delta || '';
              if (delta && onToken) {
                onToken(delta);
              }
            } catch (e) {
              // Plain text or keepalive chunk
            }
          }
        }
      }
      if (onDone) onDone();
    } catch (err) {
      if (onError) onError(err);
      else console.error('streamChat error:', err);
    }
  },

  // Autonomous Agent
  runAgentGoal: (goal, max_steps = 10) => request('/v1/agent/run', {
    method: 'POST',
    body: JSON.stringify({ goal, max_steps }),
  }),
  getAgentPlan: (goal) => request('/v1/agent/plan', {
    method: 'POST',
    body: JSON.stringify({ goal }),
  }),

  // Terminal Runner
  runTerminalCommand: (command, cwd = null) => request('/v1/terminal/run', {
    method: 'POST',
    body: JSON.stringify({ command, cwd }),
  }),
  stopTerminalProcess: () => request('/v1/terminal/stop', { method: 'POST' }),
  getTerminalHistory: () => request('/v1/terminal/history'),
  getTerminalStatus: () => request('/v1/terminal/status'),

  // Workspace Files
  getWorkspaceTree: (max_depth = 4) => request(`/v1/workspace/tree?max_depth=${max_depth}`),
  readWorkspaceFile: (path) => request(`/v1/workspace/file?path=${encodeURIComponent(path)}`),
  writeWorkspaceFile: (path, content) => request('/v1/workspace/file', {
    method: 'POST',
    body: JSON.stringify({ path, content }),
  }),
  searchWorkspace: (query) => request('/v1/workspace/search', {
    method: 'POST',
    body: JSON.stringify({ query }),
  }),
  getFileDiff: (path, modified_content) => request('/v1/workspace/diff', {
    method: 'POST',
    body: JSON.stringify({ path, modified_content }),
  }),
  getAgentChanges: () => request('/v1/workspace/agent-changes'),

  // Model Hub & Connections
  searchHubModels: (query = '', page = 1) => request(`/v1/models/hub/search?q=${encodeURIComponent(query)}&page=${page}`),
  listInstalledModels: () => request('/v1/models'),
  getConnections: () => request('/v1/connection/list'),
  setActiveConnection: (connection_id) => request('/v1/connection/active', {
    method: 'POST',
    body: JSON.stringify({ connection_id }),
  }),
  setActiveModel: (model) => request('/v1/config/model', {
    method: 'POST',
    body: JSON.stringify({ model }),
  }),
  setDeviceMode: (mode) => request('/v1/config/device-mode', {
    method: 'POST',
    body: JSON.stringify({ mode }),
  }),

  // GraphRAG & Code Search
  indexGraph: () => request('/v1/graph/index', { method: 'POST' }),
  getGraphStructure: () => request('/v1/graph/structure'),
  searchGraph: (query) => request('/v1/graph/search', {
    method: 'POST',
    body: JSON.stringify({ query }),
  }),

  // Tasks Kanban
  getTasks: () => request('/v1/tasks'),
  createTask: (title, description, priority = 'normal') => request('/v1/tasks', {
    method: 'POST',
    body: JSON.stringify({ title, description, priority }),
  }),
  updateTaskStatus: (taskId, status) => request(`/v1/tasks/${taskId}/status`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  }),
  deleteTask: (taskId) => request(`/v1/tasks/${taskId}`, { method: 'DELETE' }),

  // Memory Store
  getMemories: (category = null) => request(`/v1/memory${category ? `?category=${category}` : ''}`),
  addMemory: (content, category = 'project_facts') => request('/v1/memory', {
    method: 'POST',
    body: JSON.stringify({ content, category }),
  }),
  deleteMemory: (memoryId) => request(`/v1/memory/${memoryId}`, { method: 'DELETE' }),

  // Security Policies
  getSecurityPolicy: () => request('/v1/security/policy'),
  setSecurityPolicy: (strict_approval, sandbox_mode) => request('/v1/security/policy', {
    method: 'POST',
    body: JSON.stringify({ strict_approval, sandbox_mode }),
  }),
  getAuditLogs: () => request('/v1/security/audit'),
};
