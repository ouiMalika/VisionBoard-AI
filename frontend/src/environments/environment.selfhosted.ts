// Used by Dockerfile.prod (self-hosted Oracle Cloud build).
// demoMode is off — the real backend is available via nginx proxy.
export const environment = {
  production: true,
  demoMode: false,
  apiUrl: '/api',
};
