# Manual de Usuario - Administrador

## Introducción

Este manual te guiará en el uso completo del sistema de Servicio Técnico como administrador. Tendrás acceso a todas las funcionalidades: gestión de clientes, técnicos, tickets, órdenes de trabajo, mantenimientos y reportes.

---

## 1. Acceso al Sistema

### 1.1 Iniciar Sesión
1. Abre el navegador y ve a la dirección del sistema
2. Ingresa tu **correo electrónico** y **contraseña** de administrador
3. Presiona **"Iniciar Sesión"**

### 1.2 Activar Notificaciones
1. Toca tu nombre en la esquina superior derecha
2. Selecciona **"Activar Notificaciones"**
3. Acepta el permiso

---

## 2. Panel Principal (Dashboard)

El dashboard muestra un resumen general:
- **Total Clientes**: Clientes activos
- **Total Técnicos**: Técnicos disponibles
- **Total Equipos**: Equipos registrados
- **Tickets Abiertos**: Tickets sin resolver
- **Órdenes Pendientes**: Órdenes en proceso
- **Mantenimientos Activos**: Mantenimientos en curso

También verás:
- Tickets nuevos sin asignar
- Órdenes recientes
- Mantenimientos en progreso

---

## 3. Gestión de Clientes

### 3.1 Ver Clientes
Menú → **Clientes** → Lista de todos los clientes

### 3.2 Crear Cliente
1. Clic en **"Nuevo Cliente"**
2. Completa los datos:
   - Nombre de la empresa
   - RIF/NIT
   - Email y teléfonos
   - Persona de contacto
   - Notas
3. Presiona **"Guardar"**

### 3.3 Agregar Ubicaciones
Cada cliente puede tener múltiples ubicaciones (sucursales, sedes):
1. Entra al cliente
2. Clic en **"Nueva Ubicación"**
3. Completa: nombre, dirección, ciudad, teléfono, contacto
4. Guarda

### 3.4 Crear Usuario para el Cliente
Para que el cliente pueda crear tickets:
1. Entra al cliente
2. Clic en **"Nuevo Usuario"**
3. Ingresa nombre, email y contraseña
4. El cliente podrá iniciar sesión con esos datos

---

## 4. Gestión de Técnicos

### 4.1 Ver Técnicos
Menú → **Técnicos** → Lista de técnicos

### 4.2 Crear Técnico
1. Clic en **"Nuevo Técnico"**
2. Completa: nombre, email, teléfono, contraseña
3. Guarda

### 4.3 Editar/Desactivar Técnico
- Puedes editar datos o cambiar contraseña
- Desactiva técnicos que ya no trabajen (no se eliminan, solo se desactivan)

---

## 5. Gestión de Equipos

### 5.1 Ver Equipos
Menú → **Equipos**

### 5.2 Filtrar Equipos
1. Selecciona un **Cliente**
2. Selecciona una **Ubicación**
3. Verás los equipos de esa ubicación

### 5.3 Agregar Equipo
1. Filtra por ubicación
2. Clic en **"Agregar Equipo"**
3. Completa:
   - Tipo (PC, Laptop, Impresora, etc.)
   - Nombre/Identificación
   - Marca y modelo
   - Número de serie
   - Departamento
   - Condición
4. Guarda

Los técnicos también pueden agregar equipos durante los mantenimientos.

---

## 6. Tickets

Los tickets son solicitudes creadas por los clientes.

### 6.1 Ver Tickets
Menú → **Tickets**

Por defecto muestra tickets **Activos** (no cerrados). Usa los filtros para ver por estado.

### 6.2 Asignar Técnico a un Ticket
1. Abre el ticket
2. Selecciona uno o más técnicos
3. Clic en **"Asignar"**
4. El técnico recibirá una notificación

### 6.3 Cerrar Ticket
Cuando el técnico resuelve un ticket, tú puedes cerrarlo:
1. Abre el ticket resuelto
2. Añade notas de cierre si es necesario
3. Clic en **"Cerrar Ticket"**
4. El cliente será notificado

### 6.4 Estados
- **Abierto**: Creado por cliente, sin asignar
- **Asignado**: Tiene técnico asignado
- **En Progreso**: Técnico trabajando
- **Resuelto**: Técnico terminó
- **Cerrado**: Admin cerró el caso

---

## 7. Órdenes de Trabajo

Las órdenes son trabajos que tú creas para los técnicos.

### 7.1 Ver Órdenes
Menú → **Órdenes de Trabajo**

Por defecto muestra órdenes **Activas**.

### 7.2 Crear Orden de Trabajo
1. Clic en **"Nueva Orden"**
2. Selecciona el tipo de cliente:
   - **Cliente registrado**: Selecciona cliente y ubicación
   - **Cliente rápido**: Para llamadas telefónicas de clientes no registrados (nombre, teléfono, dirección)
3. Completa:
   - Tipo de trabajo
   - Descripción de la solicitud
   - Prioridad
   - Fecha programada
   - Técnico(s) asignado(s)
4. Clic en **"Crear Orden"**

### 7.3 Seguimiento
- Ve el estado de cada orden
- Cuando el técnico finaliza, puedes generar el **PDF** del reporte

### 7.4 Estados
- **Pendiente**: Creada, sin asignar
- **Asignado**: Tiene técnico
- **En Progreso**: Técnico trabajando
- **Completado**: Trabajo terminado
- **Cancelado**: Orden cancelada

---

## 8. Mantenimientos

Los mantenimientos son visitas programadas para revisar equipos.

### 8.1 Ver Mantenimientos
Menú → **Mantenimientos**

### 8.2 Programar Mantenimiento
1. Clic en **"Programar Mantenimiento"**
2. Selecciona cliente y ubicación
3. Completa:
   - Título (ej: "Mantenimiento Trimestral")
   - Tipo (Preventivo, Correctivo, etc.)
   - Fecha programada
   - Descripción/instrucciones
   - Técnico(s) asignado(s)
4. Clic en **"Programar"**

Los equipos de esa ubicación se agregarán automáticamente al mantenimiento.

### 8.3 Editar Mantenimiento
Si necesitas cambiar fecha o técnicos:
1. Abre el mantenimiento
2. Clic en **"Editar Mantenimiento"**
3. Modifica lo necesario
4. Guarda

Los técnicos agregados/removidos serán notificados.

### 8.4 Seguimiento
- Ve el **progreso** (barra de porcentaje)
- Ve qué equipos ya fueron atendidos
- El mantenimiento inicia automáticamente cuando el técnico comienza

### 8.5 Finalizar Mantenimiento
1. Cuando todos los equipos estén completados (o los necesarios)
2. Clic en **"Finalizar Mantenimiento"**
3. Agrega notas de cierre
4. Podrás generar el **PDF** del reporte

---

## 9. Agenda

Menú → **Agenda**

Vista de planificación que muestra:
- Órdenes programadas
- Mantenimientos programados
- Tickets asignados

Agrupados por día, con indicador de carga de trabajo por técnico.

Útil para:
- Ver qué hay programado para los próximos días
- Identificar días con mucha carga
- Planificar nuevas asignaciones

---

## 10. Reportes

Menú → **Reportes**

### 10.1 Reportes Disponibles

**Operativos:**
- **Órdenes de Trabajo**: Filtrar por fecha, cliente, técnico, estado
- **Mantenimientos**: Filtrar por fecha, cliente, estado
- **Tickets**: Filtrar por fecha, cliente, estado

**Gestión:**
- **Productividad por Técnico**: Ver rendimiento de cada técnico
- **Historial por Cliente**: Todo el trabajo realizado para un cliente
- **Inventario de Equipos**: Listado de equipos por cliente/ubicación

### 10.2 Exportar a Excel
Todos los reportes tienen el botón **"Exportar a Excel"** que descarga un archivo .xlsx con los datos filtrados.

---

## 11. Notificaciones

Como administrador recibirás notificaciones cuando:
- Un cliente cree un **nuevo ticket**
- Un técnico **resuelva** un ticket
- Haya eventos importantes en el sistema

---

## 12. Flujo de Trabajo Típico

### Ticket de Cliente:
1. Cliente crea ticket → Recibes notificación
2. Asignas técnico → Técnico recibe notificación
3. Técnico resuelve → Recibes notificación
4. Cierras el ticket → Cliente recibe notificación

### Orden de Trabajo:
1. Recibes llamada de cliente
2. Creas orden de trabajo
3. Asignas técnico → Técnico recibe notificación
4. Técnico completa → Generas PDF

### Mantenimiento:
1. Programas mantenimiento
2. Asignas técnicos → Reciben notificación
3. Técnicos atienden equipos en sitio
4. Finalizas cuando completen → Generas PDF

---

## 13. Consejos

- Revisa el **Dashboard** diariamente para ver pendientes
- Usa la **Agenda** para planificar la semana
- Exporta **reportes** mensualmente para análisis
- Mantén actualizado el **inventario de equipos**
- Asegúrate que todos los técnicos tengan **notificaciones activadas**

---

## 14. Cerrar Sesión

1. Toca tu nombre en la esquina superior derecha
2. Selecciona **"Cerrar Sesión"**

---

## Soporte Técnico del Sistema

Para problemas técnicos con el sistema, contacta al desarrollador.
