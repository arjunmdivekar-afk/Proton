/**
 * Proton Web UI - Enterprise Settings Page Controller
 */

import { state, saveSettings, events } from '../state.js';
import { api } from '../api.js';

export function initSettingsView() {
  const navItems = document.querySelectorAll('.settings-nav-item');
  const sections = document.querySelectorAll('.settings-section');

  // Input bindings
  const tempInput = document.getElementById('settings-temperature');
  const tempVal = document.getElementById('settings-temp-val');
  const topPInput = document.getElementById('settings-top-p');
  const topPVal = document.getElementById('settings-top-p-val');
  const maxTokInput = document.getElementById('settings-max-tokens');
  const systemPromptInput = document.getElementById('settings-system-prompt');
  const themeSelect = document.getElementById('settings-theme');
  const saveBtn = document.getElementById('settings-save-btn');

  // Section Tab Switcher
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const targetSec = item.getAttribute('data-section');
      sections.forEach(s => {
        s.style.display = s.id === `section-${targetSec}` ? 'block' : 'none';
      });
    });
  });

  // Sliders real-time feedback
  if (tempInput && tempVal) {
    tempInput.value = state.settings.temperature;
    tempVal.innerText = state.settings.temperature;
    tempInput.addEventListener('input', (e) => { tempVal.innerText = e.target.value; });
  }

  if (topPInput && topPVal) {
    topPInput.value = state.settings.top_p;
    topPVal.innerText = state.settings.top_p;
    topPInput.addEventListener('input', (e) => { topPVal.innerText = e.target.value; });
  }

  if (maxTokInput) maxTokInput.value = state.settings.max_tokens;
  if (systemPromptInput) systemPromptInput.value = state.settings.system_prompt;
  if (themeSelect) themeSelect.value = state.settings.theme;

  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      saveSettings({
        temperature: parseFloat(tempInput.value),
        top_p: parseFloat(topPInput.value),
        max_tokens: parseInt(maxTokInput.value, 10),
        system_prompt: systemPromptInput.value,
        theme: themeSelect.value,
      });
      events.emit('toast:show', { message: 'All platform settings saved successfully!', type: 'success' });
    });
  }
}
