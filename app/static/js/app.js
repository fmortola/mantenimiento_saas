// ==================== NOTIFICACIONES ====================
function loadNotifications() {
    fetch('/api/notificaciones')
        .then(r => r.json())
        .then(data => {
            const badge = document.querySelector('.notif-badge');
            const list = document.getElementById('notif-list');

            if (data.no_leidas > 0) {
                badge.textContent = data.no_leidas;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }

            if (data.notificaciones.length > 0) {
                list.innerHTML = data.notificaciones.map(n => `
                    <a href="${n.url || '#'}" class="dropdown-item ${n.leida ? '' : 'bg-light'}">
                        <strong>${n.titulo}</strong>
                        <p class="mb-1 small">${n.mensaje}</p>
                        <small class="text-muted">${formatDate(n.fecha)}</small>
                    </a>
                `).join('');
            } else {
                list.innerHTML = '<p class="text-muted text-center small py-3">Sin notificaciones</p>';
            }
        })
        .catch(err => console.log('Error cargando notificaciones:', err));
}

// Marcar notificaciones como leídas al abrir el dropdown
function marcarNotificacionesLeidas() {
    fetch('/api/notificaciones/marcar-leidas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Ocultar badge
            const badge = document.querySelector('.notif-badge');
            if (badge) {
                badge.style.display = 'none';
            }
            // Quitar resaltado de notificaciones
            document.querySelectorAll('#notif-list .bg-light').forEach(el => {
                el.classList.remove('bg-light');
            });
        }
    })
    .catch(err => console.log('Error marcando notificaciones:', err));
}

// Inicializar listener del dropdown de notificaciones
document.addEventListener('DOMContentLoaded', function() {
    const notifDropdown = document.getElementById('notifDropdown');
    if (notifDropdown) {
        // Marcar como leídas al hacer clic en la campana
        notifDropdown.addEventListener('click', marcarNotificacionesLeidas);
    }
});

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = (now - date) / 1000;

    if (diff < 60) return 'Hace un momento';
    if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `Hace ${Math.floor(diff / 3600)} horas`;
    return date.toLocaleDateString('es-ES');
}

// ==================== PUSH NOTIFICATIONS ====================
async function initPushNotifications(registration) {
    try {
        // Solo suscribir si ya tiene permiso (no pedir aquí)
        if (Notification.permission !== 'granted') {
            console.log('Sin permiso de notificaciones, usar activarNotificaciones()');
            return;
        }

        // Obtener clave VAPID
        const response = await fetch('/api/push/vapid-public-key');
        const { publicKey } = await response.json();

        // Suscribirse
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(publicKey)
        });

        // Enviar suscripción al servidor
        await fetch('/api/push/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(subscription.toJSON())
        });

        console.log('Suscrito a notificaciones push');
    } catch (err) {
        console.log('Error en push notifications:', err);
    }
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// ==================== PWA INSTALL ====================
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;

    // Mostrar banner de instalación
    const banner = document.querySelector('.pwa-install-banner');
    if (banner) {
        banner.classList.add('show');
    }
});

function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('PWA instalada');
            }
            deferredPrompt = null;

            const banner = document.querySelector('.pwa-install-banner');
            if (banner) {
                banner.classList.remove('show');
            }
        });
    }
}

// ==================== UTILIDADES ====================
// Mostrar loading
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Confirmar antes de eliminar
document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function(e) {
        if (!confirm(this.dataset.confirm)) {
            e.preventDefault();
        }
    });
});

// Auto-hide alerts
document.querySelectorAll('.alert-dismissible').forEach(alert => {
    setTimeout(() => {
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.click();
        }
    }, 5000);
});

// ==================== CÁMARA / FOTOS ====================

// Clase para manejar la cámara en vivo
class CameraCapture {
    constructor(options = {}) {
        this.onCapture = options.onCapture || function() {};
        this.onError = options.onError || function() {};
        this.stream = null;
        this.modal = null;
    }

    // Abrir la cámara en un modal
    async open() {
        // Crear modal si no existe
        if (!this.modal) {
            this.createModal();
        }

        const video = document.getElementById('cameraVideo');
        const canvas = document.getElementById('cameraCanvas');

        try {
            // Solicitar acceso a la cámara trasera
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                },
                audio: false
            });

            video.srcObject = this.stream;
            await video.play();

            // Mostrar modal
            const bsModal = new bootstrap.Modal(this.modal);
            bsModal.show();

        } catch (err) {
            console.error('Error accediendo a la cámara:', err);
            // Si falla la cámara en vivo, usar input file como fallback
            this.fallbackToFileInput();
        }
    }

    // Tomar foto
    capture() {
        const video = document.getElementById('cameraVideo');
        const canvas = document.getElementById('cameraCanvas');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        const imageData = canvas.toDataURL('image/jpeg', 0.85);

        this.close();
        this.onCapture(imageData);
    }

    // Cerrar cámara
    close() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        const bsModal = bootstrap.Modal.getInstance(this.modal);
        if (bsModal) {
            bsModal.hide();
        }
    }

    // Fallback: usar input file tradicional
    fallbackToFileInput() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.capture = 'environment';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                const imageData = await this.compressImage(file);
                this.onCapture(imageData);
            }
        };

        input.click();
    }

    // Comprimir imagen
    compressImage(file, maxWidth = 1200, quality = 0.85) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;

                    if (width > maxWidth) {
                        height = (height * maxWidth) / width;
                        width = maxWidth;
                    }

                    canvas.width = width;
                    canvas.height = height;

                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    resolve(canvas.toDataURL('image/jpeg', quality));
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    }

    // Crear el modal de cámara
    createModal() {
        const modalHTML = `
            <div class="modal fade" id="cameraModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-fullscreen">
                    <div class="modal-content bg-dark">
                        <div class="modal-body p-0 d-flex flex-column">
                            <div class="flex-grow-1 position-relative overflow-hidden">
                                <video id="cameraVideo" autoplay playsinline class="w-100 h-100" style="object-fit: cover;"></video>
                                <canvas id="cameraCanvas" class="d-none"></canvas>
                            </div>
                            <div class="p-3 bg-dark d-flex justify-content-center align-items-center gap-4">
                                <button type="button" class="btn btn-outline-light btn-lg rounded-circle" onclick="window.currentCamera.close()" style="width: 60px; height: 60px;">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                                <button type="button" class="btn btn-light btn-lg rounded-circle" onclick="window.currentCamera.capture()" style="width: 80px; height: 80px;">
                                    <i class="bi bi-camera-fill fs-3"></i>
                                </button>
                                <button type="button" class="btn btn-outline-light btn-lg rounded-circle" onclick="window.currentCamera.switchCamera()" style="width: 60px; height: 60px;">
                                    <i class="bi bi-arrow-repeat"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('cameraModal');

        // Limpiar stream cuando se cierre el modal
        this.modal.addEventListener('hidden.bs.modal', () => {
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
        });
    }

    // Cambiar entre cámara frontal/trasera
    async switchCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }

        const video = document.getElementById('cameraVideo');
        const currentFacing = this.facingMode || 'environment';
        this.facingMode = currentFacing === 'environment' ? 'user' : 'environment';

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: this.facingMode,
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                },
                audio: false
            });

            video.srcObject = this.stream;
            await video.play();
        } catch (err) {
            console.error('Error cambiando cámara:', err);
        }
    }
}

// Función helper para abrir cámara fácilmente
function openCamera(callback) {
    const camera = new CameraCapture({
        onCapture: callback
    });
    window.currentCamera = camera;
    camera.open();
}

// Función para subir foto a una orden
function subirFotoOrden(ordenId, imageData, tipo = 'durante') {
    showLoading();

    fetch('/api/foto/subir', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            imagen: imageData,
            orden_id: ordenId,
            tipo: tipo
        })
    })
    .then(r => r.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            location.reload();
        } else {
            alert('Error al subir la foto');
        }
    })
    .catch(err => {
        hideLoading();
        console.error('Error:', err);
        alert('Error al subir la foto');
    });
}

// Función para subir foto a un mantenimiento
function subirFotoMantenimiento(mantId, equipoId, imageData) {
    showLoading();

    fetch('/api/foto/subir-mantenimiento', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            imagen: imageData,
            mantenimiento_id: mantId,
            equipo_id: equipoId
        })
    })
    .then(r => r.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            // Mostrar preview
            const preview = document.getElementById(`preview-${equipoId}`);
            if (preview) {
                preview.innerHTML = `<img src="${imageData}" class="img-thumbnail" style="max-height: 100px;">`;
            }
            // Guardar filename en input hidden
            const input = document.getElementById(`foto-${equipoId}`);
            if (input) {
                input.value = data.filename;
            }
        } else {
            alert('Error al subir la foto');
        }
    })
    .catch(err => {
        hideLoading();
        console.error('Error:', err);
        alert('Error al subir la foto');
    });
}

// Función legacy para compatibilidad
function capturePhoto(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(event) {
            preview.innerHTML = `<img src="${event.target.result}" class="img-fluid rounded">`;
        };
        reader.readAsDataURL(file);
    });
}

// Comprimir imagen antes de subir
async function compressImage(file, maxWidth = 1200, quality = 0.8) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = new Image();
            img.onload = function() {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;

                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }

                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                resolve(canvas.toDataURL('image/jpeg', quality));
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

// ==================== ACTUALIZACIÓN EN TIEMPO REAL ====================
function startAutoRefresh(callback, interval = 30000) {
    setInterval(callback, interval);
}

// Detectar si está online/offline
window.addEventListener('online', () => {
    console.log('Conexión restaurada');
    document.body.classList.remove('offline');
});

window.addEventListener('offline', () => {
    console.log('Sin conexión');
    document.body.classList.add('offline');
});
