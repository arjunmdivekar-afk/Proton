/**
 * Proton Web UI - Security & Audit Log Controller
 */

import { api } from '../api.js';
import { events } from '../state.js';

export function initSecurityView() {
  const policyRadioStrict = document.getElementById('security-policy-strict');
  const policyRadioSandbox = document.getElementById('security-policy-sandbox');
  const policyRadioAutonomous = document.getElementById('security-policy-autonomous');
  const auditTable = document.getElementById('security-audit-table-body');

  async function loadPolicy() {
    try {
      const data = await api.getSecurityPolicy();
      if (policyRadioStrict) policyRadioStrict.checked = data.strict_approval ?? true;
      if (policyRadioSandbox) policyRadioSandbox.checked = data.sandbox_mode ?? true;
    } catch (e) {}
  }

  async function loadAuditLogs() {
    if (!auditTable) return;
    try {
      const data = await api.getAuditLogs();
      auditTable.innerHTML = '';
      const logs = data.audit_logs || [];

      if (logs.length === 0) {
        auditTable.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No audit events recorded in current session.</td></tr>';
        return;
      }

      logs.forEach(log => {
        const tr = document.createElement('tr');
        const isAllowed = log.allowed ?? true;
        tr.innerHTML = `
          <td style="font-family: var(--font-mono); font-size: 11.5px; color: var(--text-dim);">${log.timestamp || 'Just now'}</td>
          <td><span class="badge ${isAllowed ? 'badge-emerald' : 'badge-rose'}">${log.action_type || 'Execution'}</span></td>
          <td><strong>${log.tool_name || 'System'}</strong></td>
          <td style="font-family: var(--font-mono); font-size: 12px;">${escapeHtml(log.target || log.command || '')}</td>
          <td><span class="badge ${isAllowed ? 'badge-cyan' : 'badge-amber'}">${isAllowed ? 'Allowed' : 'Blocked'}</span></td>
        `;
        auditTable.appendChild(tr);
      });
    } catch (e) {}
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function updatePolicy() {
    const isStrict = policyRadioStrict ? policyRadioStrict.checked : true;
    const isSandbox = policyRadioSandbox ? policyRadioSandbox.checked : true;
    api.setSecurityPolicy(isStrict, isSandbox);
    events.emit('toast:show', { message: 'Security policy updated successfully!', type: 'success' });
  }

  if (policyRadioStrict) policyRadioStrict.addEventListener('change', updatePolicy);
  if (policyRadioSandbox) policyRadioSandbox.addEventListener('change', updatePolicy);
  if (policyRadioAutonomous) policyRadioAutonomous.addEventListener('change', updatePolicy);

  loadPolicy();
  loadAuditLogs();
}
