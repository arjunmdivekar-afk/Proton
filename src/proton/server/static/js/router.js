/**
 * Proton Web UI - Client-Side HTML5 History SPA Router
 */

import { state, events } from './state.js';

class Router {
  constructor() {
    this.routes = new Map();
    window.addEventListener('popstate', () => this.resolve());
  }

  addRoute(path, handler) {
    this.routes.set(path, handler);
  }

  navigate(path, replace = false) {
    if (replace) {
      window.history.replaceState(null, '', path);
    } else {
      window.history.pushState(null, '', path);
    }
    this.resolve();
  }

  resolve() {
    const fullPath = window.location.pathname || '/chat';
    const cleanPath = fullPath.replace(/\/$/, '') || '/chat';
    state.activeRoute = cleanPath;

    // Parse route parameters, e.g. /chat/session-123 or /tasks/task-456
    let matchedHandler = null;
    let params = {};

    for (const [routePattern, handler] of this.routes.entries()) {
      if (routePattern === cleanPath) {
        matchedHandler = handler;
        break;
      }

      // Check parameterized routes: /chat/:id
      const patternParts = routePattern.split('/');
      const pathParts = cleanPath.split('/');

      if (patternParts.length === pathParts.length) {
        let isMatch = true;
        const currentParams = {};

        for (let i = 0; i < patternParts.length; i++) {
          if (patternParts[i].startsWith(':')) {
            const paramName = patternParts[i].slice(1);
            currentParams[paramName] = pathParts[i];
          } else if (patternParts[i] !== pathParts[i]) {
            isMatch = false;
            break;
          }
        }

        if (isMatch) {
          matchedHandler = handler;
          params = currentParams;
          break;
        }
      }
    }

    if (!matchedHandler) {
      // Default fallback to chat
      this.navigate('/chat', true);
      return;
    }

    // Update active tab styling in sidebar
    const baseTab = cleanPath.split('/')[1] || 'chat';
    document.querySelectorAll('.nav-item').forEach(el => {
      const targetRoute = el.getAttribute('data-route') || '';
      el.classList.toggle('active', targetRoute.startsWith(`/${baseTab}`));
    });

    // Hide all view panels and show the active one
    document.querySelectorAll('.view-panel').forEach(panel => {
      panel.classList.remove('active');
    });

    const targetPanel = document.getElementById(`view-${baseTab}`) || document.getElementById('view-chat');
    if (targetPanel) {
      targetPanel.classList.add('active');
    }

    // Execute route handler
    matchedHandler(params);
    events.emit('route:changed', { path: cleanPath, params });
  }
}

export const router = new Router();
