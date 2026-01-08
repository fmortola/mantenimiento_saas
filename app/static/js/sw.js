// Service Worker para PWA
// IMPORTANTE: Incrementar VERSION cuando se hagan cambios para forzar actualización
const VERSION = '1.1.4';
const CACHE_NAME = `servicio-tecnico-v${VERSION}`;
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'
];

// Instalación - se activa inmediatamente
self.addEventListener('install', event => {
    console.log(`[SW] Instalando versión ${VERSION}`);
    self.skipWaiting(); // Forzar activación inmediata
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Cache abierto');
                return cache.addAll(urlsToCache);
            })
    );
});

// Activación - limpiar caches antiguos y notificar clientes
self.addEventListener('activate', event => {
    console.log(`[SW] Activando versión ${VERSION}`);
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Eliminando cache antiguo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Tomar control de todos los clientes inmediatamente
            return self.clients.claim();
        }).then(() => {
            // Notificar a todos los clientes que hay una nueva versión
            return self.clients.matchAll().then(clients => {
                clients.forEach(client => {
                    client.postMessage({
                        type: 'SW_UPDATED',
                        version: VERSION
                    });
                });
            });
        })
    );
});

// Fetch - Network first, fallback to cache
self.addEventListener('fetch', event => {
    // Solo cachear requests GET
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clone la respuesta
                const responseToCache = response.clone();

                // Guardar en cache
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(event.request, responseToCache);
                    });

                return response;
            })
            .catch(() => {
                // Si falla, buscar en cache
                return caches.match(event.request)
                    .then(response => {
                        if (response) {
                            return response;
                        }

                        // Página offline por defecto
                        if (event.request.mode === 'navigate') {
                            return caches.match('/');
                        }

                        return new Response('Offline');
                    });
            })
    );
});

// Mensaje desde el cliente (para obtener versión)
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: VERSION });
    }

    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Push Notifications
self.addEventListener('push', event => {
    console.log('[SW] Push recibido:', event);

    let data = {};
    if (event.data) {
        data = event.data.json();
    }

    const title = data.title || 'Servicio Técnico';
    const options = {
        body: data.body || 'Nueva notificación',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/'
        },
        actions: [
            { action: 'open', title: 'Ver' },
            { action: 'close', title: 'Cerrar' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Click en notificación
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    const url = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Si ya hay una ventana abierta, enfocarla
                for (const client of clientList) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Si no, abrir una nueva
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});
