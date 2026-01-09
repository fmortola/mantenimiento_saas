# Contexto del Proyecto - ServTec SaaS

> Archivo para poner en contexto a Claude en futuras sesiones.
> Ultima actualizacion: 2026-01-08 | Version: 1.1.4

## Descripcion General

**ServTec SaaS** es un sistema multi-tenant para gestion de servicio tecnico. Permite a empresas gestionar clientes, tecnicos, equipos, ordenes de trabajo, tickets y mantenimientos preventivos.

**URL Produccion:** https://m.servitech.com.ec

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Backend | Python 3.10 / Flask 3.0 |
| Base de datos | MySQL / MariaDB |
| ORM | SQLAlchemy + Flask-Migrate |
| Frontend | Bootstrap 5 + Jinja2 |
| PWA | Service Worker + VAPID Push |
| PDF | ReportLab |
| Excel | OpenPyXL |
| Apps Nativas | PWA Wrapper (PWABuilder) |

## Apps en Tiendas

### Android (Google Play)
- **Package ID:** `ec.com.servitech.app`
- **Estado:** En pruebas internas (funcionando)
- **Pendiente:** 20 testers x 14 dias para produccion
- **Console:** https://play.google.com/console

### iOS (App Store)
- **Bundle ID:** `ec.com.servitech.app`
- **Estado:** Enviado a revision de Apple (2026-01-08)
- **Connect:** https://appstoreconnect.apple.com

### Archivos de las apps
```
builds/
├── android/
│   ├── app-release.aab      # Paquete para Play Store
│   ├── signing.keystore     # CLAVE DE FIRMA (no perder!)
│   ├── assetlinks.json      # Copia del que esta en el servidor
│   ├── feature-graphic.png  # Imagen 1024x500 para Play Store
│   └── screenshots/         # Capturas para las tiendas
└── ios/
    └── src/
        └── ServTec.xcworkspace  # Proyecto Xcode
```

## Estructura de Carpetas

```
mant2_saas/
├── app/
│   ├── __init__.py          # App factory, before_request para politica
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── usuario.py       # Usuario con acepto_politica
│   │   ├── tenant.py        # Tenants/empresas
│   │   ├── cliente.py       # Clientes del tenant
│   │   ├── equipo.py        # Equipos
│   │   ├── orden_trabajo.py # Ordenes + fotos + actividades
│   │   ├── ticket.py        # Tickets de soporte
│   │   └── mantenimiento.py # Mantenimientos preventivos
│   ├── routes/
│   │   ├── auth.py          # Login, logout, politicas, assetlinks
│   │   ├── superadmin.py    # Gestion de tenants, planes, backup
│   │   ├── admin.py         # Panel del admin del tenant
│   │   ├── tecnico.py       # App movil del tecnico
│   │   ├── cliente.py       # Portal del cliente
│   │   └── api.py           # API REST
│   ├── templates/
│   │   ├── base.html        # Template base con navbar, modales, SW
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── aceptar_politica.html    # Politica obligatoria (login)
│   │   │   ├── politica_publica.html    # Politica publica (tiendas)
│   │   │   └── solicitar_eliminacion.html # Eliminar cuenta (tiendas)
│   │   ├── admin/           # base_admin.html + subcarpetas
│   │   ├── tecnico/         # Vista movil del tecnico
│   │   ├── cliente/         # Portal cliente
│   │   └── superadmin/      # Panel superadmin
│   ├── static/
│   │   ├── css/style.css    # Estilos custom + mobile menu
│   │   ├── js/
│   │   │   ├── app.js       # JS principal
│   │   │   └── sw.js        # Service Worker (VERSION importante!)
│   │   ├── images/
│   │   │   ├── icon-*.png   # Iconos PWA (72 a 512)
│   │   │   └── screenshots/ # Capturas para manifest
│   │   ├── .well-known/
│   │   │   └── assetlinks.json  # Digital Asset Links (Android)
│   │   └── manifest.json    # PWA manifest mejorado
│   ├── services/
│   │   ├── pdf_generator.py
│   │   └── notificaciones.py
│   └── utils/
│       ├── tenant_utils.py  # get_current_tenant_id()
│       └── query_helpers.py
├── builds/                  # Apps compiladas (NO en git)
├── config.py                # Configuracion Flask + SITE_URL
├── run.py                   # Punto de entrada
├── requirements.txt
├── CHANGELOG.md             # Historial de versiones
├── CONTEXT.md               # Este archivo
└── README.md                # Documentacion
```

## Rutas Publicas (sin autenticacion)

| Ruta | Proposito |
|------|-----------|
| `/politica-privacidad` | Politica de privacidad (Google Play / App Store) |
| `/eliminar-cuenta` | Solicitar eliminacion de cuenta (requerido por tiendas) |
| `/.well-known/assetlinks.json` | Digital Asset Links para Android |
| `/manifest.json` | PWA manifest |
| `/sw.js` | Service Worker |

## Roles de Usuario

| Rol | Descripcion | Acceso |
|-----|-------------|--------|
| superadmin | Administrador de la plataforma | /superadmin/* |
| admin | Administrador del tenant | /admin/* |
| tecnico | Tecnico de campo | /tecnico/* |
| cliente | Cliente del tenant | /cliente/* |

## Arquitectura Multi-Tenant

- Cada tenant tiene su propio conjunto de datos aislado
- `tenant_id` en todas las tablas principales
- Usuarios pertenecen a un tenant (excepto superadmin)
- Planes limitan: tecnicos, clientes, equipos, features

## Versionado

**Archivos a modificar cuando cambia la version:**
1. `app/static/js/sw.js` → `const VERSION = 'x.x.x'`
2. `app/templates/base.html` → `let appVersion = 'x.x.x'`
3. `app/templates/base.html` → Badge en modal "Acerca de"
4. `CHANGELOG.md` → Nueva entrada
5. `README.md` → Badge de version (opcional)

## Funcionalidades por Version

### v1.1.4 (actual)
- Pagina publica de politica de privacidad
- Pagina para solicitar eliminacion de cuenta
- Digital Asset Links para Android
- Manifest mejorado (screenshots, shortcuts)
- Configuracion SITE_URL en config.py
- App Android en Google Play (pruebas)
- App iOS enviada a App Store

### v1.1.3
- Politica de privacidad obligatoria en primer login
- Campos `acepto_politica` y `fecha_acepto_politica` en Usuario
- `before_request` en `__init__.py` verifica aceptacion

### v1.1.2
- Nuevo logo de la app (iconos PWA regenerados desde logo.png)

### v1.1.1
- Backup de tenant (JSON)
- Eliminar tenant con confirmacion
- Historial de trabajos por equipo
- Tecnico puede asociar/crear equipos en ordenes
- Menu hamburguesa en PWA admin

### v1.1.0
- Reportes mensuales automaticos

## PWA y Service Worker

- El SW usa versionado para cache busting
- `skipWaiting()` fuerza actualizacion inmediata
- Notificaciones push con VAPID
- Banner de instalacion para iOS/Android/Desktop
- Manifest incluye shortcuts y related_applications

## Base de Datos

### Agregar columnas a tablas existentes:
```sql
-- Ejemplo para politica de privacidad (ya aplicado)
ALTER TABLE usuario ADD COLUMN acepto_politica BOOLEAN DEFAULT FALSE;
ALTER TABLE usuario ADD COLUMN fecha_acepto_politica DATETIME NULL;
```

Las columnas nuevas en los modelos se crean automaticamente en instalaciones nuevas (`db.create_all()`), pero para bases existentes hay que ejecutar ALTER TABLE.

## Servidor de Produccion

- **URL:** https://m.servitech.com.ec
- **IP interna:** 10.5.1.115:3300
- **Despliegue:** FileZilla (manual)
- **Servidor:** Gunicorn
- **SSL:** Si (requerido para PWA y push)
- Despues de subir archivos Python: reiniciar Gunicorn

## Archivos Importantes

| Archivo | Proposito |
|---------|-----------|
| `app/__init__.py` | Factory, blueprints, before_request |
| `app/routes/auth.py` | Login, politicas, assetlinks |
| `app/templates/base.html` | Template base, navbar, SW, modales |
| `app/static/js/sw.js` | Service Worker (VERSION!) |
| `app/static/manifest.json` | PWA manifest con shortcuts |
| `app/static/.well-known/assetlinks.json` | Android App Links |
| `config.py` | SITE_URL y configuracion |
| `builds/android/signing.keystore` | Clave firma Android (NO perder!) |

## Google Play - Proceso de Publicacion

1. ✅ Crear cuenta desarrollador ($25 unico)
2. ✅ Generar AAB con PWABuilder
3. ✅ Configurar assetlinks.json
4. ✅ Completar declaraciones (10)
5. ✅ Configurar ficha de tienda
6. ✅ Subir a pruebas internas
7. ⏳ Conseguir 20 testers por 14 dias
8. ⏳ Solicitar produccion

## App Store - Proceso de Publicacion

1. ✅ Cuenta Apple Developer ($99/año)
2. ✅ Generar proyecto con PWABuilder
3. ✅ Compilar en Xcode
4. ✅ Configurar App Store Connect
5. ✅ Enviar a revision
6. ⏳ Esperar aprobacion (24-48 hrs)

## Contacto / Autor

**YoYoSoft - Soluciones Tecnologicas**
- Email: famb@me.com
- Horario: Lunes a Viernes, 10:00 - 16:00

## Para Retomar Trabajo

1. Leer este archivo para contexto
2. Ver `CHANGELOG.md` para cambios recientes
3. Ver `git log --oneline -10` para commits recientes
4. La version actual esta en `sw.js` linea 3
5. Estado de apps: Google Play Console / App Store Connect
