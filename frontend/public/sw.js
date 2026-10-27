// Offline app shell only. API responses are never cached.
const NAME = 'cinearis-shell-v1';
const SHELL = ['/', '/manifest.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(NAME).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const req = event.request;
  const path = new URL(req.url);
  if (req.method !== 'GET' || path.origin !== self.location.origin || path.pathname.startsWith('/api/')) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('/')));
  }
});
