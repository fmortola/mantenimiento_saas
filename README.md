# Sistema de Gestión de Servicio Técnico

Sistema web PWA para gestión de servicio técnico con soporte para:
- Administradores
- Técnicos
- Clientes

## Características

### Administrador
- Dashboard con estadísticas en tiempo real
- Gestión de clientes y ubicaciones
- Gestión de técnicos
- Gestión de equipos/inventario
- Creación de órdenes de trabajo
- Programación y edición de mantenimientos
- Gestión de tickets
- Agenda de trabajos programados
- Reportes con exportación a Excel
- Generación de reportes PDF
- Notificaciones push

### Técnico
- Dashboard con trabajos asignados
- Gestión de órdenes de trabajo
- Ejecución de mantenimientos
- Levantamiento de inventario
- Captura de fotos con cámara del celular
- Registro de trabajo realizado
- Notificaciones push

### Cliente
- Portal de autoservicio
- Tour interactivo de ayuda (Intro.js)
- Visualización de ubicaciones y equipos
- Creación de tickets de soporte
- Seguimiento de tickets
- Historial de servicios
- Descarga de reportes PDF
- Notificaciones push

## Requisitos

- Python 3.8+
- MariaDB 10.x
- Navegador moderno con soporte PWA

## Instalación

1. Clonar repositorio:
```bash
git clone https://github.com/fmortola/mantenimeinto2.git
cd mantenimeinto2
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

5. Crear base de datos en MariaDB:
```sql
CREATE DATABASE servicio_tecnico CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'servicio_tecnico'@'%' IDENTIFIED BY 'tu_password';
GRANT ALL PRIVILEGES ON servicio_tecnico.* TO 'servicio_tecnico'@'%';
FLUSH PRIVILEGES;
```

6. Generar claves VAPID para notificaciones push:
```bash
python gen_vapid.py
# Copiar las claves generadas al archivo .env
```

7. Inicializar base de datos:
```bash
python init_db.py
```

8. Generar iconos PWA (opcional):
```bash
python generate_icons.py
```

9. Ejecutar aplicación:
```bash
python run.py
```

La aplicación estará disponible en: http://localhost:5000

## Usuarios de prueba

Después de ejecutar `init_db.py`:

| Rol | Email | Contraseña |
|-----|-------|------------|
| Admin | admin@admin.com | admin123 |
| Técnico | tecnico@demo.com | tecnico123 |
| Cliente | cliente@demo.com | cliente123 |

## Producción con Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Estructura del proyecto

```
mant2/
├── app/
│   ├── models/          # Modelos de base de datos
│   ├── routes/          # Rutas/controladores
│   ├── services/        # Servicios (notificaciones, PDF, Excel)
│   ├── static/          # Archivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/       # Templates Jinja2
│       ├── admin/
│       ├── tecnico/
│       ├── cliente/
│       └── auth/
├── docs/                # Manuales de usuario
│   ├── manual_administrador.md
│   ├── manual_tecnico.md
│   └── manual_cliente.md
├── config.py            # Configuración
├── requirements.txt     # Dependencias
├── run.py              # Punto de entrada
├── init_db.py          # Script inicialización BD
└── gen_vapid.py        # Generador de claves VAPID
```

## PWA (Progressive Web App)

La aplicación es una PWA que puede ser instalada en dispositivos móviles:

1. Abrir la aplicación en el navegador del celular
2. En el menú del navegador, seleccionar "Agregar a pantalla de inicio"
3. La aplicación funcionará como una app nativa

### Notificaciones Push

Las notificaciones push requieren:
1. Conexión HTTPS (o localhost para desarrollo)
2. Aceptar permisos de notificación en el navegador
3. Claves VAPID configuradas en .env (usar `gen_vapid.py`)
4. iOS 16.4+ para soporte en iPhone/iPad

## Reportes y Exportación

El sistema incluye reportes con exportación a Excel:
- Órdenes de Trabajo
- Mantenimientos
- Tickets
- Productividad por Técnico
- Historial por Cliente
- Inventario de Equipos

## Licencia

MIT

## Soporte

Para reportar problemas o solicitar funcionalidades, crear un issue en el repositorio.
