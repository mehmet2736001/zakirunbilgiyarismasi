// Zakirun Hâfızlık Yarışmaları - Service Worker (Offline PWA Engine)
const CACHE_NAME = 'zakirun-hafizlik-v1.0';
const STATIC_ASSETS = [
  '/',
  '/kuran_tv_bilgi_yarismasi.html',
  '/zakirun.com.woff2',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Network-first with cache fallback for HTML & static assets
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/kuran_tv_bilgi_yarismasi.html');
          }
          return new Response(JSON.stringify({ offline: true, error: "Çevrimdışı Mod" }), {
            headers: { 'Content-Type': 'application/json' }
          });
        });
      })
  );
});
