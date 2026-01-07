# ServTec SaaS

![Version](https://img.shields.io/badge/version-1.1.3-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-orange.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

Sistema **multi-tenant (SaaS)** para empresas de servicio tecnico. Permite gestionar clientes, tecnicos, equipos, ordenes de trabajo y mantenimientos preventivos.

## Tabla de Contenidos

- [Caracteristicas](#caracteristicas)
- [Tecnologias](#tecnologias)
- [Requisitos](#requisitos)
- [Instalacion](#instalacion)
- [Configuracion](#configuracion)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API](#api)
- [PWA](#pwa-progressive-web-app)
- [Despliegue en Produccion](#despliegue-en-produccion)
- [Changelog](#changelog)
- [Autor](#autor)

## Caracteristicas

### Multi-Tenant (SaaS)
- Multiples empresas en una sola instalacion
- Datos completamente aislados por tenant
- Planes con diferentes limites y caracteristicas
- Panel SuperAdmin para gestionar tenants y planes
- Backup y restauracion de datos por tenant

### Panel de Administrador
- Dashboard con estadisticas en tiempo real
- Gestion de clientes con ubicaciones y equipos
- Gestion de tecnicos
- Tipos de equipo configurables
- Tickets de soporte
- Ordenes de trabajo con seguimiento
- Mantenimientos preventivos y correctivos
- Historial de trabajos por equipo
- Reportes mensuales automaticos
- Exportacion a Excel y PDF

### App de Tecnico (PWA)
- Ordenes asignadas con detalle
- Registro de actividades con tiempo
- Captura de fotos con camara del celular
- Asociar/crear equipos en campo
- Firma digital del cliente
- Notificaciones push
- Funciona offline

### Portal de Cliente
- Creacion de tickets de soporte
- Seguimiento de ordenes
- Calendario de mantenimientos
- Tour guiado interactivo
- Interfaz movil optimizada

### Seguridad
- Autenticacion con Flask-Login
- Proteccion CSRF en todos los formularios
- Passwords hasheados con Werkzeug
- Aislamiento de datos por tenant
- Politica de privacidad obligatoria

## Tecnologias

| Componente | Tecnologia |
|------------|------------|
| Backend | Python 3.8+ / Flask 3.0 |
| Base de datos | MySQL / MariaDB |
| ORM | SQLAlchemy / Flask-Migrate |
| Frontend | Bootstrap 5, Bootstrap Icons |
| PWA | Service Worker, Web Push (VAPID) |
| PDF | ReportLab |
| Excel | OpenPyXL |
| Tours | Intro.js |

## Requisitos

- Python 3.8 o superior
- MySQL 5.7+ o MariaDB 10.3+
- pip (gestor de paquetes Python)

## Instalacion

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/servtec-saas.git
cd servtec-saas

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones (ver seccion Configuracion)

# Inicializar base de datos
python init_saas.py

# Ejecutar en desarrollo
python run.py
```

La aplicacion estara disponible en: http://localhost:5000

## Configuracion

### Variables de Entorno (.env)

```env
# Flask
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura
FLASK_ENV=development

# Base de datos
DATABASE_URL=mysql+pymysql://usuario:password@localhost/servtec_db

# Push Notifications (VAPID)
VAPID_PUBLIC_KEY=tu-clave-publica-vapid
VAPID_PRIVATE_KEY=tu-clave-privada-vapid
VAPID_CLAIMS_EMAIL=tu-email@ejemplo.com

# Uploads
UPLOAD_FOLDER=app/static/images/uploads
MAX_CONTENT_LENGTH=16777216
```

### Generar Claves VAPID

```bash
python gen_vapid.py
```

## Uso

### Credenciales por Defecto

| Rol | Email | Password |
|-----|-------|----------|
| SuperAdmin | admin@servtec.com | admin123 |
| Admin Demo | admin@demo.com | demo123 |
| Tecnico Demo | tecnico@demo.com | demo123 |

> **Importante:** Cambiar las credenciales en produccion

### Planes Disponibles

| Plan | Tecnicos | Clientes | Equipos | Precio/mes |
|------|----------|----------|---------|------------|
| Basico | 2 | 5 | 10 | $5.90 |
| Pro | 5 | 12 | 15 | $12.75 |
| Enterprise | 20 | 30 | 50 | $29.99 |

### Caracteristicas por Plan

| Caracteristica | Basico | Pro | Enterprise |
|----------------|--------|-----|------------|
| Reportes | Si | Si | Si |
| Notificaciones Push | Si | Si | Si |
| Exportacion Excel | No | Si | Si |
| Branding Personalizado | No | Si | Si |
| Acceso API | No | No | Si |
| Cliente ve Ordenes | No | Si | Si |
| Cliente ve Mantenimientos | No | No | Si |

## Estructura del Proyecto

```
servtec-saas/
├── app/
│   ├── __init__.py          # Factory de la aplicacion
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── plan.py          # Planes SaaS
│   │   ├── tenant.py        # Tenants/Empresas
│   │   ├── usuario.py       # Usuarios (todos los roles)
│   │   ├── cliente.py       # Clientes del tenant
│   │   ├── equipo.py        # Equipos
│   │   ├── orden_trabajo.py # Ordenes de trabajo
│   │   ├── ticket.py        # Tickets de soporte
│   │   └── mantenimiento.py # Mantenimientos
│   ├── routes/              # Blueprints/Rutas
│   │   ├── auth.py          # Autenticacion
│   │   ├── superadmin.py    # Panel SuperAdmin
│   │   ├── admin.py         # Panel Admin de Tenant
│   │   ├── tecnico.py       # App de Tecnico
│   │   ├── cliente.py       # Portal de Cliente
│   │   └── api.py           # API REST
│   ├── services/            # Logica de negocio
│   │   ├── pdf_generator.py # Generacion de PDFs
│   │   └── notificaciones.py# Push notifications
│   ├── templates/           # Templates Jinja2
│   │   ├── auth/            # Login, politica privacidad
│   │   ├── admin/           # Panel administrador
│   │   ├── tecnico/         # App tecnico
│   │   ├── cliente/         # Portal cliente
│   │   └── superadmin/      # Panel superadmin
│   ├── static/              # Archivos estaticos
│   │   ├── css/             # Estilos
│   │   ├── js/              # JavaScript y Service Worker
│   │   └── images/          # Iconos y uploads
│   └── utils/               # Utilidades
│       ├── tenant_utils.py  # Helpers multi-tenant
│       └── query_helpers.py # Helpers de consultas
├── config.py                # Configuracion Flask
├── run.py                   # Punto de entrada
├── init_saas.py             # Inicializacion de datos
├── requirements.txt         # Dependencias Python
├── CHANGELOG.md             # Historial de cambios
└── README.md                # Este archivo
```

## API

### Endpoints Disponibles (Plan Enterprise)

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/api/clientes` | Listar clientes |
| GET | `/api/equipos` | Listar equipos |
| GET | `/api/ordenes` | Listar ordenes |
| GET | `/api/tickets` | Listar tickets |
| POST | `/api/notificaciones/push` | Enviar notificacion |

> Todas las rutas requieren autenticacion y pertenencia a un tenant con plan Enterprise.

## PWA (Progressive Web App)

### Instalacion en Dispositivos

1. Abrir la aplicacion en el navegador del celular
2. El sistema mostrara un banner para instalar
3. Aceptar la instalacion
4. La app aparecera en la pantalla de inicio

### Notificaciones Push

Requisitos:
- HTTPS en produccion (localhost funciona en desarrollo)
- Claves VAPID configuradas en `.env`
- iOS 16.4+ para dispositivos Apple

### Service Worker

El Service Worker maneja:
- Cache de recursos estaticos
- Funcionamiento offline
- Notificaciones push
- Actualizaciones automaticas

## Despliegue en Produccion

### Con Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Con Systemd (Linux)

```ini
# /etc/systemd/system/servtec.service
[Unit]
Description=ServTec SaaS
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/servtec
Environment="PATH=/var/www/servtec/venv/bin"
ExecStart=/var/www/servtec/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Con Nginx (Proxy Reverso)

```nginx
server {
    listen 80;
    server_name tudominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/servtec/app/static;
        expires 30d;
    }
}
```

### Variables de Entorno en Produccion

```env
FLASK_ENV=production
SECRET_KEY=clave-muy-segura-generada-aleatoriamente
DATABASE_URL=mysql+pymysql://usuario:password@localhost/servtec_prod
```

## Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para el historial completo de cambios.

### Ultima Version: 1.1.3 (2026-01-07)

- Aceptacion obligatoria de politica de privacidad
- Nuevo logo de la aplicacion
- Backup y eliminacion de tenants
- Historial de trabajos por equipo
- Menu hamburguesa en PWA admin

## Autor

**YoYoSoft - Soluciones Tecnologicas**

- Email: famb@me.com
- Horario de soporte: Lunes a Viernes, 10:00 - 16:00

---

© 2026 YoYoSoft - Todos los derechos reservados
