# Contexto del Proyecto - ServTec SaaS

> Archivo para poner en contexto a Claude en futuras sesiones.
> Ultima actualizacion: 2026-01-07 | Version: 1.1.3

## Descripcion General

**ServTec SaaS** es un sistema multi-tenant para gestion de servicio tecnico. Permite a empresas gestionar clientes, tecnicos, equipos, ordenes de trabajo, tickets y mantenimientos preventivos.

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
│   │   ├── auth.py          # Login, logout, aceptar_politica
│   │   ├── superadmin.py    # Gestion de tenants, planes, backup
│   │   ├── admin.py         # Panel del admin del tenant
│   │   ├── tecnico.py       # App movil del tecnico
│   │   ├── cliente.py       # Portal del cliente
│   │   └── api.py           # API REST
│   ├── templates/
│   │   ├── base.html        # Template base con navbar, modales, SW
│   │   ├── auth/            # login.html, aceptar_politica.html
│   │   ├── admin/           # base_admin.html + subcarpetas
│   │   ├── tecnico/         # Vista movil del tecnico
│   │   ├── cliente/         # Portal cliente
│   │   └── superadmin/      # Panel superadmin
│   ├── static/
│   │   ├── css/style.css    # Estilos custom + mobile menu
│   │   ├── js/
│   │   │   ├── app.js       # JS principal
│   │   │   └── sw.js        # Service Worker (VERSION importante!)
│   │   ├── images/          # Iconos PWA (icon-72 a icon-512)
│   │   └── manifest.json    # PWA manifest
│   ├── services/
│   │   ├── pdf_generator.py
│   │   └── notificaciones.py
│   └── utils/
│       ├── tenant_utils.py  # get_current_tenant_id()
│       └── query_helpers.py
├── config.py                # Configuracion Flask
├── run.py                   # Punto de entrada
├── requirements.txt
├── CHANGELOG.md             # Historial de versiones
└── README.md                # Documentacion
```

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

## Funcionalidades Recientes (v1.1.x)

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

## Base de Datos

### Agregar columnas a tablas existentes:
```sql
-- Ejemplo para politica de privacidad (ya aplicado)
ALTER TABLE usuario ADD COLUMN acepto_politica BOOLEAN DEFAULT FALSE;
ALTER TABLE usuario ADD COLUMN fecha_acepto_politica DATETIME NULL;
```

Las columnas nuevas en los modelos se crean automaticamente en instalaciones nuevas (`db.create_all()`), pero para bases existentes hay que ejecutar ALTER TABLE.

## Servidor de Produccion

- IP: 10.5.1.115:3300
- Despliegue: FileZilla (manual)
- Servidor: Gunicorn
- Despues de subir archivos Python: reiniciar Gunicorn

## Archivos Importantes

| Archivo | Proposito |
|---------|-----------|
| `app/__init__.py` | Factory, blueprints, before_request |
| `app/routes/auth.py` | Login, politica privacidad |
| `app/templates/base.html` | Template base, navbar, SW, modales |
| `app/static/js/sw.js` | Service Worker (VERSION!) |
| `app/templates/admin/base_admin.html` | Base admin con menu hamburguesa |

## Contacto / Autor

**YoYoSoft - Soluciones Tecnologicas**
- Email: famb@me.com
- Horario: Lunes a Viernes, 10:00 - 16:00

## Para Retomar Trabajo

1. Leer este archivo para contexto
2. Ver `CHANGELOG.md` para cambios recientes
3. Ver `git log --oneline -10` para commits recientes
4. La version actual esta en `sw.js` linea 3
