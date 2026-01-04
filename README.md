# ServTec SaaS - Sistema de Gestión de Servicio Técnico

Sistema **multi-tenant (SaaS)** para empresas de servicio técnico. Permite gestionar clientes, técnicos, equipos, órdenes de trabajo y mantenimientos preventivos.

## Características Principales

### Multi-Tenant (SaaS)
- Múltiples empresas en una sola instalación
- Datos completamente aislados por tenant
- Planes con diferentes límites y características (Básico, Pro, Enterprise)
- Panel SuperAdmin para gestionar tenants y planes
- Plantillas de tipos de equipo por industria (configurables)

### Panel de Administrador
- Dashboard con estadísticas en tiempo real
- Gestión de clientes con ubicaciones y equipos
- Gestión de técnicos
- Tipos de equipo configurables (Cómputo, Línea Blanca, HVAC, Médico, etc.)
- Tickets de soporte
- Órdenes de trabajo con seguimiento
- Mantenimientos preventivos y correctivos
- Agenda/calendario
- Reportes con exportación a Excel y PDF
- Tour guiado de ayuda

### App de Técnico (PWA)
- Órdenes asignadas
- Registro de actividades con tiempo
- Captura de fotos con cámara del celular
- Firma digital del cliente
- Notificaciones push
- Tour guiado de ayuda

### Portal de Cliente
- Creación de tickets de soporte
- Seguimiento de órdenes (según plan)
- Calendario de mantenimientos (según plan)
- Tour guiado interactivo
- Interfaz móvil optimizada

## Tecnologías

- **Backend:** Python 3.8+ / Flask
- **Base de datos:** MySQL / MariaDB
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **PWA:** Service Worker, Web Push Notifications (VAPID)
- **PDF:** ReportLab
- **Excel:** OpenPyXL
- **Tours:** Intro.js

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/fmortola/mantenimiento_saas.git
cd mantenimiento_saas

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Inicializar base de datos y datos de prueba
python init_saas.py

# Ejecutar
python run.py
```

La aplicación estará disponible en: http://localhost:5000

## Credenciales por Defecto

| Rol | Email | Password |
|-----|-------|----------|
| SuperAdmin | fmortola@gmail.com | Bruno2@@1 |
| Admin Demo | admin@demo.com | demoIN5940 |
| Técnico Demo | tecnico@demo.com | demoIN5940 |

## Planes Disponibles

| Plan | Técnicos | Clientes | Equipos | Usr/Cliente | Precio/mes | Precio/año |
|------|----------|----------|---------|-------------|------------|------------|
| Básico | 2 | 5 | 10 | 1 | $5.90 | $64.99 |
| Pro | 5 | 12 | 15 | 3 | $12.75 | $139.99 |
| Enterprise | 20 | 30 | 50 | 5 | $29.99 | $299.99 |

### Características por Plan

| Característica | Básico | Pro | Enterprise |
|----------------|--------|-----|------------|
| Reportes | ✅ | ✅ | ✅ |
| Notificaciones Push | ✅ | ✅ | ✅ |
| Exportación Excel | ❌ | ✅ | ✅ |
| Branding Personalizado | ❌ | ✅ | ✅ |
| Acceso API | ❌ | ❌ | ✅ |
| Cliente ve Órdenes | ❌ | ✅ | ✅ |
| Cliente ve Mantenimientos | ❌ | ❌ | ✅ |

## Estructura del Proyecto

```
mantenimiento_saas/
├── app/
│   ├── models/          # Modelos SQLAlchemy
│   │   ├── plan.py      # Planes SaaS
│   │   ├── tenant.py    # Tenants/Empresas
│   │   ├── usuario.py   # Usuarios (todos los roles)
│   │   ├── cliente.py   # Clientes del tenant
│   │   └── ...
│   ├── routes/          # Blueprints
│   │   ├── superadmin.py # Panel SuperAdmin
│   │   ├── admin.py     # Panel Admin de Tenant
│   │   ├── tecnico.py   # App de Técnico
│   │   ├── cliente.py   # Portal de Cliente
│   │   └── api.py       # API REST
│   ├── services/        # Servicios
│   │   ├── pdf_generator.py
│   │   └── notificaciones.py
│   ├── templates/       # Templates Jinja2
│   ├── static/          # CSS, JS, imágenes
│   └── utils/           # Utilidades
│       ├── tenant_utils.py
│       └── query_helpers.py
├── config.py            # Configuración
├── init_saas.py         # Script de inicialización SaaS
├── run.py               # Punto de entrada
└── requirements.txt     # Dependencias
```

## PWA (Progressive Web App)

La aplicación puede instalarse en dispositivos móviles:

1. Abrir en navegador del celular
2. Menú → "Agregar a pantalla de inicio"
3. Funciona como app nativa

### Notificaciones Push

Requieren:
- HTTPS (o localhost)
- Claves VAPID configuradas
- iOS 16.4+ para iPhone/iPad

## Producción

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Licencia

Proyecto privado.

## Autor

Fernando Mortola
