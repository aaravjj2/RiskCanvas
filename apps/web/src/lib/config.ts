/**
 * Application Configuration
 * Manages runtime settings including DEMO mode and authentication
 * Enhanced in v2.0 with auth token management
 */

// Auth mode detection
export type AuthMode = 'demo' | 'none' | 'entra';

export function getAuthMode(): AuthMode {
  // DEMO mode takes precedence
  if (isDemoMode()) {
    return 'demo';
  }
  
  // Check env var for auth mode
  const envAuthMode = import.meta.env.VITE_AUTH_MODE;
  if (envAuthMode === 'entra') {
    return 'entra';
  }
  
  // Default: none (no auth required)
  return 'none';
}

// Check if DEMO mode is enabled via env var or localStorage
export function isDemoMode(): boolean {
  // Check localStorage override first
  const localStorageValue = localStorage.getItem('RC_DEMO_MODE');
  if (localStorageValue !== null) {
    return localStorageValue === 'true';
  }
  
  // Check env var (set at build time)
  const envValue = import.meta.env.VITE_DEMO_MODE;
  if (envValue !== undefined) {
    return envValue === 'true';
  }
  
  // Default to false
  return false;
}

// Auth token management (v2.0+)
const AUTH_TOKEN_KEY = 'RC_AUTH_TOKEN';

export function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token: string) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function getAuthHeaders(): Record<string, string> {
  const authMode = getAuthMode();
  
  // DEMO mode: use demo headers
  if (authMode === 'demo') {
    return getDemoHeaders();
  }
  
  // Entra mode: use Authorization bearer token
  if (authMode === 'entra') {
    const token = getAuthToken();
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
      };
    }
  }
  
  // None mode: check if demo headers are available (backward compat)
  const demoHeaders = getDemoHeaders();
  if (Object.keys(demoHeaders).length > 0) {
    return demoHeaders;
  }
  
  return {};
}

export function setDemoMode(enabled: boolean) {
  localStorage.setItem('RC_DEMO_MODE', enabled.toString());
  // Reload to apply changes
  window.location.reload();
}

export function getDemoHeaders(): Record<string, string> {
  if (isDemoMode()) {
    return {
      'x-demo-user': 'demo-user',
      'x-demo-role': 'admin',
    };
  }
  return {};
}

export const config = {
  getAuthMode,
  isDemoMode,
  setDemoMode,
  getDemoHeaders,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  getAuthHeaders,
};
