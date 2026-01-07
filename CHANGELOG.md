# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.1.3] - 2026-01-07

### Agregado
- Aceptacion obligatoria de politica de privacidad en primer login
- Pagina de politica de privacidad con scroll obligatorio
- Campos `acepto_politica` y `fecha_acepto_politica` en modelo Usuario

## [1.1.2] - 2026-01-07

### Cambiado
- Nuevo logo de la aplicacion (iconos PWA actualizados)

## [1.1.1] - 2026-01-07

### Agregado
- **SuperAdmin**: Backup de tenant (descarga JSON con todos los datos)
- **SuperAdmin**: Eliminación de tenant con confirmación por slug
- **Admin**: Historial de trabajos por equipo
- **Técnico**: Asociar/crear equipos desde órdenes de trabajo
- **Técnico**: Ver historial de equipos
- **Admin PWA**: Menú hamburguesa con accesos a crear clientes, técnicos, equipos

### Mejorado
- Menú móvil del admin con accesos directos a creación

## [1.1.0] - 2026-01-06

### Agregado
- Reportes mensuales automáticos para clientes
- Reportes mensuales con detalle completo (fotos y firmas)

## [1.0.4] - 2026-01-05

### Mejorado
- Auto-rotación a landscape al abrir modal de firma
- Permitir rotación de pantalla en PWA para captura de firma

## [1.0.0] - 2026-01-01

### Inicial
- Sistema multi-tenant SaaS para gestión de servicio técnico
- Módulo Admin: gestión de clientes, técnicos, equipos, tickets, órdenes
- Módulo Técnico: ejecución de trabajos, captura de fotos, firmas
- Módulo Cliente: portal de autoservicio, creación de tickets
- PWA instalable con notificaciones push
- Reportes con exportación a Excel
- Generación de PDF
