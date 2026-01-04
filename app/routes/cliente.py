from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.cliente import Cliente
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo
from app.models.ticket import Ticket, TIPOS_TICKET
from app.models.orden_trabajo import OrdenTrabajo
from app.models.mantenimiento import Mantenimiento
from app.services.notificaciones import notificar_admins
from datetime import datetime

cliente_bp = Blueprint('cliente', __name__)

def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_cliente():
            flash('Acceso denegado. Se requieren permisos de cliente.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== DASHBOARD ====================
@cliente_bp.route('/dashboard')
@login_required
@cliente_required
def dashboard():
    cliente = current_user.cliente
    if not cliente:
        flash('Tu usuario no está asociado a un cliente.', 'danger')
        return redirect(url_for('auth.logout'))

    # Estadísticas
    stats = {
        'ubicaciones': cliente.ubicaciones.filter_by(activo=True).count(),
        'equipos': cliente.total_equipos(),
        'tickets_abiertos': cliente.tickets.filter(Ticket.estado.in_(['abierto', 'asignado', 'en_progreso'])).count(),
        'tickets_resueltos': cliente.tickets.filter_by(estado='resuelto').count()
    }

    # Tickets recientes
    tickets_recientes = cliente.tickets.order_by(Ticket.fecha_creacion.desc()).limit(5).all()

    # Mantenimientos próximos o en progreso
    mantenimientos = cliente.mantenimientos.filter(
        Mantenimiento.estado.in_(['programado', 'en_progreso'])
    ).order_by(Mantenimiento.fecha_programada).all()

    return render_template('cliente/dashboard.html',
                           cliente=cliente,
                           stats=stats,
                           tickets_recientes=tickets_recientes,
                           mantenimientos=mantenimientos)

# ==================== UBICACIONES ====================
@cliente_bp.route('/ubicaciones')
@login_required
@cliente_required
def ubicaciones():
    cliente = current_user.cliente
    ubicaciones = cliente.ubicaciones.filter_by(activo=True).all()
    return render_template('cliente/ubicaciones/lista.html', ubicaciones=ubicaciones)

@cliente_bp.route('/ubicaciones/<int:id>')
@login_required
@cliente_required
def ubicacion_ver(id):
    ubicacion = Ubicacion.query.get_or_404(id)
    if ubicacion.cliente_id != current_user.cliente_id:
        flash('No tienes acceso a esta ubicación.', 'danger')
        return redirect(url_for('cliente.ubicaciones'))

    equipos = ubicacion.equipos.filter_by(activo=True).all()
    return render_template('cliente/ubicaciones/ver.html', ubicacion=ubicacion, equipos=equipos)

# ==================== EQUIPOS ====================
@cliente_bp.route('/equipos')
@login_required
@cliente_required
def equipos():
    cliente = current_user.cliente
    equipos = []
    for ubicacion in cliente.ubicaciones.filter_by(activo=True):
        for equipo in ubicacion.equipos.filter_by(activo=True):
            equipos.append(equipo)
    return render_template('cliente/equipos/lista.html', equipos=equipos)

@cliente_bp.route('/equipos/<int:id>')
@login_required
@cliente_required
def equipo_ver(id):
    equipo = Equipo.query.get_or_404(id)
    if equipo.ubicacion.cliente_id != current_user.cliente_id:
        flash('No tienes acceso a este equipo.', 'danger')
        return redirect(url_for('cliente.equipos'))

    # Historial de mantenimientos del equipo
    historial = equipo.mantenimientos_equipo.filter_by(estado='completado').order_by(
        MantenimientoEquipo.fecha_fin.desc()).all() if hasattr(equipo, 'mantenimientos_equipo') else []

    return render_template('cliente/equipos/ver.html', equipo=equipo, historial=historial)

# ==================== TICKETS ====================
@cliente_bp.route('/tickets')
@login_required
@cliente_required
def tickets():
    cliente = current_user.cliente
    estado = request.args.get('estado', 'todos')

    if estado == 'todos':
        tickets = cliente.tickets.order_by(Ticket.fecha_creacion.desc()).all()
    else:
        tickets = cliente.tickets.filter_by(estado=estado).order_by(Ticket.fecha_creacion.desc()).all()

    return render_template('cliente/tickets/lista.html', tickets=tickets, estado_filtro=estado)

@cliente_bp.route('/tickets/nuevo', methods=['GET', 'POST'])
@login_required
@cliente_required
def ticket_nuevo():
    # Verificar que el tenant este activo para crear tickets
    if not current_user.tenant.esta_activo():
        flash('El sistema esta en mantenimiento. Intenta mas tarde o comunicate por telefono.', 'warning')
        return redirect(url_for('cliente.tickets'))

    cliente = current_user.cliente

    if request.method == 'POST':
        ubicacion_id = request.form.get('ubicacion_id')
        equipo_id = request.form.get('equipo_id')

        ticket = Ticket(
            numero=Ticket.generar_numero(),
            asunto=request.form.get('asunto'),
            descripcion=request.form.get('descripcion'),
            tipo=request.form.get('tipo'),
            prioridad=request.form.get('prioridad', 'normal'),
            cliente_id=cliente.id,
            ubicacion_id=ubicacion_id if ubicacion_id else None,
            equipo_id=equipo_id if equipo_id else None,
            creado_por_id=current_user.id,
            tenant_id=current_user.tenant_id
        )

        db.session.add(ticket)
        db.session.commit()

        # Notificar a administradores
        notificar_admins(
            'Nuevo Ticket',
            f'El cliente {cliente.nombre} ha creado el ticket {ticket.numero}: {ticket.asunto}',
            url_for('admin.ticket_ver', id=ticket.id)
        )

        flash('Ticket creado exitosamente. Nos pondremos en contacto pronto.', 'success')
        return redirect(url_for('cliente.ticket_ver', id=ticket.id))

    ubicaciones = cliente.ubicaciones.filter_by(activo=True).all()
    return render_template('cliente/tickets/form.html',
                           ubicaciones=ubicaciones,
                           tipos=TIPOS_TICKET)

@cliente_bp.route('/tickets/<int:id>')
@login_required
@cliente_required
def ticket_ver(id):
    ticket = Ticket.query.get_or_404(id)
    if ticket.cliente_id != current_user.cliente_id:
        flash('No tienes acceso a este ticket.', 'danger')
        return redirect(url_for('cliente.tickets'))

    return render_template('cliente/tickets/ver.html', ticket=ticket)

# ==================== ÓRDENES DE TRABAJO ====================
@cliente_bp.route('/ordenes')
@login_required
@cliente_required
def ordenes():
    # Verificar si el plan permite ver órdenes
    plan = current_user.tenant.plan
    if not plan.cliente_ve_ordenes:
        flash('Tu plan actual no incluye acceso a órdenes de trabajo. Contacta a tu proveedor para actualizar.', 'warning')
        return redirect(url_for('cliente.dashboard'))

    cliente = current_user.cliente
    estado = request.args.get('estado', 'todos')

    query = cliente.ordenes_trabajo.order_by(OrdenTrabajo.fecha_creacion.desc())
    if estado != 'todos':
        query = query.filter_by(estado=estado)

    ordenes = query.all()
    return render_template('cliente/ordenes/lista.html', ordenes=ordenes, estado_filtro=estado)

@cliente_bp.route('/ordenes/<int:id>')
@login_required
@cliente_required
def orden_ver(id):
    # Verificar si el plan permite ver órdenes
    plan = current_user.tenant.plan
    if not plan.cliente_ve_ordenes:
        flash('Tu plan actual no incluye acceso a órdenes de trabajo.', 'warning')
        return redirect(url_for('cliente.dashboard'))

    orden = OrdenTrabajo.query.get_or_404(id)
    if orden.cliente_id != current_user.cliente_id:
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('cliente.ordenes'))

    return render_template('cliente/ordenes/ver.html', orden=orden)

# ==================== MANTENIMIENTOS ====================
@cliente_bp.route('/mantenimientos')
@login_required
@cliente_required
def mantenimientos():
    # Verificar si el plan permite ver mantenimientos
    plan = current_user.tenant.plan
    if not plan.cliente_ve_mantenimientos:
        flash('Tu plan actual no incluye acceso al calendario de mantenimientos. Contacta a tu proveedor para actualizar.', 'warning')
        return redirect(url_for('cliente.dashboard'))

    cliente = current_user.cliente
    estado = request.args.get('estado', 'todos')

    query = cliente.mantenimientos.order_by(Mantenimiento.fecha_programada.desc())
    if estado != 'todos':
        query = query.filter_by(estado=estado)

    mantenimientos = query.all()
    return render_template('cliente/mantenimientos/lista.html', mantenimientos=mantenimientos, estado_filtro=estado)

@cliente_bp.route('/mantenimientos/<int:id>')
@login_required
@cliente_required
def mantenimiento_ver(id):
    # Verificar si el plan permite ver mantenimientos
    plan = current_user.tenant.plan
    if not plan.cliente_ve_mantenimientos:
        flash('Tu plan actual no incluye acceso a mantenimientos.', 'warning')
        return redirect(url_for('cliente.dashboard'))

    mantenimiento = Mantenimiento.query.get_or_404(id)
    if mantenimiento.cliente_id != current_user.cliente_id:
        flash('No tienes acceso a este mantenimiento.', 'danger')
        return redirect(url_for('cliente.mantenimientos'))

    return render_template('cliente/mantenimientos/ver.html', mantenimiento=mantenimiento)

# ==================== HISTORIAL ====================
@cliente_bp.route('/historial')
@login_required
@cliente_required
def historial():
    cliente = current_user.cliente

    # Órdenes de trabajo completadas
    ordenes = cliente.ordenes_trabajo.filter_by(estado='completado').order_by(
        OrdenTrabajo.fecha_fin.desc()).all()

    # Mantenimientos completados
    mantenimientos = cliente.mantenimientos.filter_by(estado='completado').order_by(
        Mantenimiento.fecha_fin.desc()).all()

    return render_template('cliente/historial.html',
                           ordenes=ordenes,
                           mantenimientos=mantenimientos)

# ==================== API AUXILIAR ====================
@cliente_bp.route('/api/ubicaciones/<int:ubicacion_id>/equipos')
@login_required
@cliente_required
def api_equipos_ubicacion(ubicacion_id):
    ubicacion = Ubicacion.query.get_or_404(ubicacion_id)
    if ubicacion.cliente_id != current_user.cliente_id:
        return jsonify([])

    equipos = ubicacion.equipos.filter_by(activo=True).all()
    return jsonify([{
        'id': e.id,
        'nombre': e.nombre or f'{e.tipo} - {e.marca}',
        'tipo': e.tipo,
        'departamento': e.departamento
    } for e in equipos])
